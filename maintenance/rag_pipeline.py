# maintenance/rag_pipeline.py
import google.generativeai as genai
from django.conf import settings
from django.utils import timezone
from .models import MaintenancePrediction, MaintenanceRecord, Equipment, EquipmentUsageLog

# =============================================================================
# ⚙️ 1. CONFIGURE GEMINI CLIENT
# =============================================================================
if not getattr(settings, "GEMINI_API_KEY", None):
    raise RuntimeError("⚠️ GEMINI_API_KEY missing in settings or environment!")

# Configure Gemini SDK
genai.configure(api_key=settings.GEMINI_API_KEY)

# =============================================================================
# 🔍 2. DETECT AND SELECT THE BEST AVAILABLE GEMINI MODEL
# =============================================================================
def get_available_model():
    """
    Detects and selects the best available Gemini model dynamically.
    Falls back safely if unavailable.
    """
    try:
        models = [m.name for m in genai.list_models()]
        print("✅ Available Gemini models:", models)

        preferred = [
            "models/gemini-1.5-pro-latest",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-1.0-pro",
            "models/gemini-pro",
        ]
        for candidate in preferred:
            if candidate in models:
                print(f"✅ Using Gemini model: {candidate}")
                return candidate

        print("⚠️ No preferred model found. Defaulting to models/gemini-pro.")
        return "models/gemini-pro"

    except Exception as e:
        print(f"⚠️ Could not list Gemini models: {e}")
        return "models/gemini-1.5-flash-latest"

# Auto-detect once at startup
GEMINI_MODEL = get_available_model()

# =============================================================================
# 🧩 3. BUILD CONTEXT FROM EQUIPMENT DATA (RETRIEVAL STAGE)
# =============================================================================
def build_equipment_context(equipment_id, max_history=5):
    """Fetch and structure equipment data into a readable context."""
    try:
        equip = Equipment.objects.get(id=equipment_id)
    except Equipment.DoesNotExist:
        return "No equipment data available."

    context = [
        f"Equipment Name: {equip.name}",
        f"Type: {getattr(equip, 'equipment_type', 'N/A')}",
        f"Model: {getattr(equip, 'model', 'N/A')}",
        f"Year Manufactured: {getattr(equip, 'year_manufactured', 'N/A')}",
        f"Location: {getattr(equip, 'city', 'N/A')}",
        f"Total Hours: {getattr(equip, 'total_hours', 'N/A')}",
        "",
    ]

    # Maintenance predictions
    pred = MaintenancePrediction.objects.filter(equipment=equip).order_by('-predicted_at').first()
    if pred:
        context += [
            "Latest Maintenance Prediction:",
            f"- Risk Level: {pred.risk_level}",
            f"- Confidence Score: {getattr(pred, 'confidence_score', 'N/A')}",
            f"- Failure Probability: {float(pred.predicted_failure_probability):.2f}%",
            f"- Days Until Maintenance: {getattr(pred, 'days_until_maintenance', 'N/A')}",
            f"- Predicted Maintenance Date: {getattr(pred, 'predicted_maintenance_date', 'N/A')}",
            f"- Recommendations: {pred.recommended_actions or 'None'}",
            "",
        ]

    # Maintenance history
    history = MaintenanceRecord.objects.filter(equipment=equip).order_by('-scheduled_date')[:max_history]
    context.append("Recent Maintenance Records:")
    if history.exists():
        for r in history:
            context.append(
                f"- {r.scheduled_date}: {r.get_maintenance_type_display()} "
                f"({r.get_status_display()}) - Cost: {r.total_cost}"
            )
    else:
        context.append("- None found.")
    context.append("")

    # Usage logs
    logs = EquipmentUsageLog.objects.filter(equipment=equip).order_by('-created_at')[:max_history]
    context.append("Recent Usage Logs:")
    if logs.exists():
        for l in logs:
            context.append(
                f"- {l.created_at.date()}: Hours={l.hours_used}, KM={l.kilometers_covered}, "
                f"Fuel={l.fuel_consumed}, Errors={l.error_count}"
            )
    else:
        context.append("- None found.")
    context.append("")

    context.append(f"Context gathered at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(context)

# =============================================================================
# 🤖 4. GENERATE GEMINI ANSWER (GENERATION STAGE)
# =============================================================================
def generate_gemini_answer(prompt_text, model_name=None, temperature=0.2, max_output_tokens=512):
    """
    Send prompt to Gemini and return a response.
    Includes model auto-fallback and better error handling.
    """
    model_name = model_name or GEMINI_MODEL

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt_text,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
        )
        return getattr(response, "text", str(response)).strip()

    except Exception as e:
        error_message = str(e)
        print(f"⚠️ Gemini API error: {error_message}")

        # Fallback if model not found or unsupported
        if "404" in error_message or "not found" in error_message:
            fallback_model = "models/gemini-pro" if "pro" in model_name else "models/gemini-pro"
            print(f"🔁 Retrying with fallback model: {fallback_model}")
            try:
                fallback = genai.GenerativeModel(fallback_model)
                response = fallback.generate_content(prompt_text)
                return getattr(response, "text", str(response)).strip()
            except Exception as inner:
                return f"Gemini fallback also failed: {inner}"

        return f"Error contacting Gemini API: {error_message}"
