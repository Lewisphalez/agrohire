import json
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg

from equipment.models import Equipment
from .models import MaintenancePrediction, MaintenanceAlert, MaintenanceRecord
from .rag_pipeline import build_equipment_context, generate_gemini_answer  # ✅ RAG pipeline


# =============================================================================
# 🧠 MAIN MAINTENANCE HUB VIEW
# =============================================================================
@login_required
def maintenance_hub(request):
    """
    Displays equipment list, active alerts, and predictive stats
    in the main maintenance dashboard.
    """
    # ✅ Get all equipment
    equipment_list = Equipment.objects.all().order_by("name")

    # ✅ Recent active alerts (exclude dismissed)
    alerts = (
        MaintenanceAlert.objects.exclude(status="dismissed")
        .order_by("-created_at")[:5]
    )

    # ✅ Active maintenance predictions
    predictions = (
        MaintenancePrediction.objects.filter(is_active=True)
        .select_related("equipment")
    )

    # ✅ Average failure probability (fix from aggregate_avg -> aggregate)
    avg_failure_prob = (
        predictions.aggregate(avg_prob=Avg("predicted_failure_probability"))["avg_prob"] or 0
    )
    avg_failure_prob = round(avg_failure_prob, 2)

    # ✅ Recent maintenance records (for display)
    recent_records = MaintenanceRecord.objects.order_by("-scheduled_date")[:10]

    # ✅ Build context safely — everything iterable
    context = {
        "equipment_list": equipment_list,
        "alerts": alerts,
        "predictions": predictions,
        "recent_records": recent_records,
        "total_equipment": equipment_list.count(),
        "active_alerts_count": alerts.count(),
        "avg_failure_prob": avg_failure_prob,
    }

    return render(request, "maintenance/hub.html", context)


# =============================================================================
# ⚠️ ALERT MANAGEMENT (AJAX)
# =============================================================================
@require_POST
@csrf_exempt
def acknowledge_alert_ajax(request, alert_id):
    """
    Acknowledge a maintenance alert via AJAX.
    """
    try:
        alert = get_object_or_404(MaintenanceAlert, id=alert_id)
        alert.acknowledge(request.user)
        return JsonResponse({"ok": True, "message": "Alert acknowledged."})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


@require_POST
@csrf_exempt
def dismiss_alert_ajax(request, alert_id):
    """
    Dismiss a maintenance alert via AJAX.
    """
    try:
        alert = get_object_or_404(MaintenanceAlert, id=alert_id)
        alert.dismiss()
        return JsonResponse({"ok": True, "message": "Alert dismissed."})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


# =============================================================================
# 🔄 FETCH ALERTS (FOR LIVE REFRESH)
# =============================================================================
@login_required
def alerts_json(request):
    """
    Return latest active alerts as JSON for real-time frontend updates.
    """
    alerts = (
        MaintenanceAlert.objects.exclude(status="dismissed")
        .order_by("-created_at")[:5]
    )

    data = [
        {
            "id": a.id,
            "title": a.title,
            "type": a.get_alert_type_display(),
            "status": a.get_status_display(),
            "message": a.message,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for a in alerts
    ]

    return JsonResponse({"ok": True, "alerts": data})


# =============================================================================
# ⚙️ FETCH EQUIPMENT DETAILS (FOR CHARTS / DASHBOARD)
# =============================================================================
@login_required
def equipment_detail_json(request, equipment_id):
    """
    Returns prediction and maintenance data for one equipment.
    Used in charts and analytics sections.
    """
    try:
        equipment = Equipment.objects.get(id=equipment_id)
        prediction = MaintenancePrediction.objects.filter(
            equipment=equipment, is_active=True
        ).first()
        records = MaintenanceRecord.objects.filter(
            equipment=equipment
        ).order_by("-scheduled_date")[:5]

        data = {
            "equipment": equipment.name,
            "model": getattr(equipment, "model", ""),
            "condition": getattr(equipment, "condition", "N/A"),
            "prediction": {
                "failure_prob": getattr(prediction, "predicted_failure_probability", 0),
                "risk_level": getattr(prediction, "risk_level", "Low"),
                "days_until_maintenance": getattr(prediction, "days_until_maintenance", 0),
                "predicted_date": (
                    prediction.predicted_maintenance_date.strftime("%Y-%m-%d")
                    if prediction and prediction.predicted_maintenance_date
                    else None
                ),
            },
            "records": [
                {
                    "type": r.get_maintenance_type_display(),
                    "date": r.scheduled_date.strftime("%Y-%m-%d"),
                    "cost": r.total_cost,
                    "status": r.get_status_display(),
                }
                for r in records
            ],
        }

        return JsonResponse({"ok": True, "data": data})

    except Equipment.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Equipment not found."})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


# =============================================================================
# 🤖 GEMINI AI ASSISTANT (RAG PIPELINE)
# =============================================================================
@csrf_exempt
@require_POST
def ask_gemini(request, equipment_id):
    """
    Handles user queries from the AI Assistant section.
    Uses RAG (Retrieval-Augmented Generation) with Gemini.
    """
    try:
        body = json.loads(request.body)
        user_question = body.get("question", "").strip()

        if not user_question:
            return JsonResponse({"ok": False, "error": "No question provided."})

        # 1️⃣ Build context for the selected equipment
        context_text = build_equipment_context(equipment_id)

        # 2️⃣ Combine context + user question
        full_prompt = f"""
**Role:** You are a helpful and knowledgeable AI maintenance assistant for AgroHire, a smart farm management system. Your goal is to provide clear, concise, and actionable advice to users based on the equipment data provided.

**Task:** Answer the user's question based *only* on the context provided below.

**Context:**
---
{context_text}
---

**User Question:** "{user_question}"

**Response Guidelines:**
1.  **Analyze the Context:** Carefully review all the provided data: equipment details, predictions, maintenance history, and usage logs.
2.  **Direct Answer:** Provide a direct and clear answer to the user's question.
3.  **Explain Your Reasoning:** Briefly explain *why* you are giving this answer, referencing specific data points from the context (e.g., "based on the high error count in recent usage logs...").
4.  **Actionable Recommendation:** If applicable, provide a clear, actionable recommendation (e.g., "It is recommended to schedule a diagnostic check-up within the next 7 days.").
5.  **Use Markdown:** Format your response using Markdown for readability (e.g., use bullet points, bold text).
6.  **If Unsure:** If the context does not contain enough information to answer the question, state that clearly. Do not guess or provide information not present in the context.

---
**Your Answer:**
"""

        # 3️⃣ Send to Gemini API
        gemini_response = generate_gemini_answer(full_prompt)

        # 4️⃣ Return answer to frontend
        return JsonResponse({"ok": True, "answer": gemini_response})

    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error: {str(e)}"})
