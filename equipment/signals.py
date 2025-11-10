# equipment/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Equipment
from maintenance.rag_pipeline import build_equipment_context, generate_gemini_answer
from maintenance.models import MaintenancePrediction
from django.utils import timezone

@receiver(post_save, sender=Equipment)
def auto_create_prediction(sender, instance, created, **kwargs):
    from maintenance.rag_pipeline import build_equipment_context, generate_gemini_answer
    if not created:
        return
    # Build a simple prompt (or call your trained model instead of Gemini)
    ctx = build_equipment_context(instance.id)
    prompt = f"""
**Role:** You are an expert maintenance prediction AI. Your task is to analyze the context for a new piece of equipment and provide an initial maintenance prediction in JSON format.

**Context:**
---
{ctx}
---

**Instructions:**
1.  Review the provided context, paying attention to the equipment's type, age (year manufactured), and any initial details.
2.  Based on this initial data, generate a baseline maintenance prediction. For new equipment, this should generally be a low-risk prediction.
3.  Your entire response must be a single JSON object enclosed in a Markdown code block (```json ... ```). Do not include any text outside of the code block.

**JSON Output Schema:**
-   `risk_level`: (String) "Low", "Medium", or "High".
-   `probability`: (Float) A numerical probability of failure (e.g., 5.0 for 5%).
-   `days_until_maintenance`: (Integer) Estimated days until the first check-up is needed.
-   `predicted_date`: (String) The predicted date for the first maintenance in "YYYY-MM-DD" format.
-   `recommendations`: (String) A brief recommendation for initial monitoring.

**Example:**
```json
{{
    "risk_level": "Low",
    "probability": 5.0,
    "days_until_maintenance": 180,
    "predicted_date": "{(timezone.now() + timezone.timedelta(days=180)).strftime('%Y-%m-%d')}",
    "recommendations": "Standard initial monitoring recommended. Check fluid levels and tire pressure after the first 50 hours of use."
}}
```

**Your JSON Response:**
"""
    try:
        out = generate_gemini_answer(prompt)
        
        # Clean the output to extract JSON from a Markdown code block
        if out.strip().startswith("```json"):
            out = out.strip().replace("```json", "").replace("```", "")
        
        import json
        parsed = json.loads(out)

        MaintenancePrediction.objects.create(
            equipment=instance,
            risk_level=parsed.get('risk_level', 'Low'),
            predicted_failure_probability=parsed.get('probability', 0),
            days_until_maintenance=parsed.get('days_until_maintenance', 90),
            predicted_maintenance_date=parsed.get('predicted_date') or timezone.now().date(),
            recommended_actions=parsed.get('recommendations', ''),
            confidence_score=parsed.get('confidence', 80),
            is_active=True
        )
    except Exception as e:
        # fallback if Gemini doesn't return valid JSON — create a default low-risk record
        MaintenancePrediction.objects.create(
            equipment=instance,
            risk_level='Low',
            predicted_failure_probability=0.0,
            days_until_maintenance=90,
            predicted_maintenance_date=timezone.now().date(),
            recommended_actions='Auto-generated placeholder; run AI manually.',
            confidence_score=50,
            is_active=True
        )
