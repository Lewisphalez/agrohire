# equipment/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Equipment
from maintenance.rag_pipeline import build_equipment_context, generate_gemini_answer
from maintenance.models import MaintenancePrediction
from django.utils import timezone

@receiver(post_save, sender=Equipment)
def auto_create_prediction(sender, instance, created, **kwargs):
    if not created:
        return
    # Build a simple prompt (or call your trained model instead of Gemini)
    ctx = build_equipment_context(instance.id)
    prompt = (
        "You are a maintenance prediction assistant. Given the context below, "
        "produce a short prediction in JSON with keys: risk_level, probability, days_until_maintenance, predicted_date, recommendations.\n\n"
        f"CONTEXT:\n{ctx}\n\n"
        "Return JSON only."
    )
    try:
        out = generate_gemini_answer(prompt)
        # Try to parse JSON from Gemini
        import json
        parsed = json.loads(out)
        # create DB record (ensure fields match your MaintenancePrediction model)
        MaintenancePrediction.objects.create(
            equipment=instance,
            predicted_failure_probability=parsed.get('probability', 0),
            days_until_maintenance=parsed.get('days_until_maintenance', 90),
            predicted_maintenance_date=parsed.get('predicted_date') or timezone.now().date(),
            recommended_actions=parsed.get('recommendations', ''),
            confidence_score=parsed.get('confidence', 80),
            is_active=True
        )
    except Exception as e:
        # fallback if Gemini doesn't return JSON — create a default low-risk record
        MaintenancePrediction.objects.create(
            equipment=instance,
            predicted_failure_probability=0.0,
            days_until_maintenance=90,
            predicted_maintenance_date=timezone.now().date(),
            recommended_actions='Auto-generated placeholder; run AI manually.',
            confidence_score=50,
            is_active=True
        )
