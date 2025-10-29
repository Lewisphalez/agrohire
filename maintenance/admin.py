from django.contrib import admin
from .models import (
    EquipmentUsageLog, 
    MaintenanceRecord, 
    MaintenancePrediction, 
    MaintenanceAlert
)

# Simple registrations - no fancy customization for now
admin.site.register(EquipmentUsageLog)
admin.site.register(MaintenanceRecord)
admin.site.register(MaintenancePrediction)
admin.site.register(MaintenanceAlert)