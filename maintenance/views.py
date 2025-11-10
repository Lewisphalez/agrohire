import json
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.utils import timezone

from equipment.models import Equipment
from .models import MaintenancePrediction, MaintenanceAlert, MaintenanceRecord

from .rag_pipeline import build_equipment_context, generate_gemini_answer


@login_required
def maintenance_hub(request):
    """
    Displays equipment list, active alerts, and predictive stats
    in the main maintenance dashboard.
    """
    equipment_list = Equipment.objects.all().order_by("name")
    
    active_alerts = MaintenanceAlert.objects.exclude(status="dismissed").order_by("-created_at")
    
    predictions = MaintenancePrediction.objects.filter(is_active=True).select_related("equipment")
    
    risk_counts = predictions.aggregate(
        critical=Count('id', filter=Q(risk_level='critical')),
        high=Count('id', filter=Q(risk_level='high')),
        medium=Count('id', filter=Q(risk_level='medium')),
        low=Count('id', filter=Q(risk_level='low')),
    )
    
    chart_data = {
        "labels": ["Critical", "High", "Medium", "Low"],
        "values": [risk_counts['critical'], risk_counts['high'], risk_counts['medium'], risk_counts['low']],
        "colors": ["#dc3545", "#ffc107", "#0dcaf0", "#198754"],
    }
    
    context = {
        "equipment_list": equipment_list,
        "active_alerts": active_alerts[:5],
        "critical_alerts_count": active_alerts.filter(alert_type='critical').count(),
        "risk_counts": risk_counts,
        "chart_data": chart_data,
        "last_updated": timezone.now(),
        "maintenance_history": MaintenanceRecord.objects.order_by("-scheduled_date")[:5],
        "upcoming_maintenance": MaintenanceRecord.objects.filter(status='scheduled').order_by("scheduled_date")[:5],
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
**Role:** You are a helpful and knowledgeable AI maintenance assistant for AgroHire.

**Task:** Answer the user's question based *only* on the context provided below. Format your response using Markdown for a clear, line-by-line presentation.

**Context:**
---
{context_text}
---

**User Question:** "{user_question}"

**Response Format (Each item on a new line):**

**Summary:** [Provide a brief, one-sentence summary of the answer here]

*   **Risk Level:** [e.g., Medium]
*   **Recommended Action:** [e.g., Schedule standard service]
*   **Due Date:** [e.g., Within 30 days]

**🧠 Reasoning:**
[Briefly explain the reasons for your recommendation, referencing specific data from the context.]

**🔧 Next Step:**
[Provide a clear, actionable next step.]

---

**Your Answer:**
"""

        # 3️⃣ Send to Gemini API
        gemini_response = generate_gemini_answer(full_prompt)

        # 4️⃣ Return answer to frontend
        return JsonResponse({"ok": True, "answer": gemini_response})

    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error: {str(e)}"})
