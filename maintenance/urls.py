from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Main hub
    path('', views.maintenance_hub, name='hub'),
    

    
    
    path('ask/<int:equipment_id>/', views.ask_gemini, name='ask_gemini'),
    path('ajax/alerts/', views.alerts_json, name='alerts_json'),
    path('ajax/equipment/<int:equipment_id>/', views.equipment_detail_json, name='equipment_detail_json'),
    path('ajax/alert/<int:alert_id>/ack/', views.acknowledge_alert_ajax, name='acknowledge_alert_ajax'),
    path('ajax/alert/<int:alert_id>/dismiss/', views.dismiss_alert_ajax, name='dismiss_alert_ajax'),
    # keep existing non-AJAX endpoints if you want (optional)
    path('alert/<int:alert_id>/acknowledge/', views.acknowledge_alert_ajax, name='acknowledge_alert'),  # can map to ajax
    path('alert/<int:alert_id>/dismiss/', views.dismiss_alert_ajax, name='dismiss_alert'),
]  
