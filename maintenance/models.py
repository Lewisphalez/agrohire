from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date
from equipment.models import Equipment
from bookings.models import Booking
from users.models import User


class EquipmentUsageLog(models.Model):
    """Track equipment usage data for each booking"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='usage_log')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='usage_logs')
    
    # Usage metrics
    hours_used = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    kilometers_covered = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    fuel_consumed = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    
    # Operational conditions
    operating_temperature_avg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    load_factor = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], default=50)
    terrain_type = models.CharField(max_length=20, choices=[('flat', 'Flat'), ('hilly', 'Hilly'), ('rough', 'Rough Terrain'), ('mixed', 'Mixed')], default='flat')
    
    # Performance indicators
    idle_time_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    error_count = models.PositiveIntegerField(default=0)
    operator_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Equipment Usage Log'
        verbose_name_plural = 'Equipment Usage Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Usage log for {self.equipment.name} - Booking {self.booking.booking_number}"
    
    @property
    def fuel_efficiency(self):
        if self.fuel_consumed > 0:
            return float(self.kilometers_covered) / float(self.fuel_consumed)
        return 0


class MaintenanceRecord(models.Model):
    """Track all maintenance activities performed on equipment"""
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('predictive', 'Predictive Maintenance'),
        ('emergency', 'Emergency Repair'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Scheduling
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(blank=True, null=True)
    
    # Work performed
    description = models.TextField()
    work_performed = models.TextField(blank=True)
    parts_replaced = models.JSONField(default=list, blank=True)
    
    # Metrics
    equipment_hours_at_maintenance = models.PositiveIntegerField(default=0)
    kilometers_at_maintenance = models.PositiveIntegerField(default=0)
    
    # Cost tracking
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Personnel
    performed_by = models.CharField(max_length=200)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='approved_maintenance', blank=True, null=True)
    
    # Issues found
    issues_found = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low')
    next_maintenance_due = models.DateField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Maintenance Record'
        verbose_name_plural = 'Maintenance Records'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.get_maintenance_type_display()} - {self.equipment.name}"
    
    def complete_maintenance(self):
        self.status = 'completed'
        self.completed_date = timezone.now()
        self.save()
        self.equipment.status = 'available'
        self.equipment.last_maintenance_date = self.completed_date.date()
        if self.next_maintenance_due:
            self.equipment.next_maintenance_date = self.next_maintenance_due
        self.equipment.save()


class MaintenancePrediction(models.Model):
    """Store AI predictions for equipment maintenance needs"""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_predictions')
    
    # Prediction results
    predicted_failure_probability = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    days_until_maintenance = models.PositiveIntegerField(default=90)
    predicted_maintenance_date = models.DateField()
    
    # Risk assessment
    risk_level = models.CharField(max_length=20, choices=[('low', 'Low Risk'), ('medium', 'Medium Risk'), ('high', 'High Risk'), ('critical', 'Critical Risk')], default='low')
    
    # Components at risk
    components_at_risk = models.JSONField(default=list, blank=True)
    
    # Model information
    model_version = models.CharField(max_length=50, default='v1.0')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], default=80)
    features_used = models.JSONField(default=dict, blank=True)
    recommended_actions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    predicted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Maintenance Prediction'
        verbose_name_plural = 'Maintenance Predictions'
        ordering = ['-predicted_at']
        indexes = [
            models.Index(fields=['equipment', '-predicted_at']),
            models.Index(fields=['risk_level']),
        ]
    
    def __str__(self):
        return f"Prediction for {self.equipment.name} - {self.risk_level}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate risk level
        if self.predicted_failure_probability >= 75:
            self.risk_level = 'critical'
        elif self.predicted_failure_probability >= 50:
            self.risk_level = 'high'
        elif self.predicted_failure_probability >= 25:
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'
        
        super().save(*args, **kwargs)
        
        # Deactivate old predictions
        if self.is_active:
            MaintenancePrediction.objects.filter(equipment=self.equipment).exclude(pk=self.pk).update(is_active=False)


class MaintenanceAlert(models.Model):
    """Track maintenance alerts sent to equipment owners and admins"""
    ALERT_TYPE_CHOICES = [
        ('upcoming', 'Upcoming Maintenance'),
        ('overdue', 'Overdue Maintenance'),
        ('high_risk', 'High Risk Alert'),
        ('critical', 'Critical Alert'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_alerts')
    prediction = models.ForeignKey(MaintenancePrediction, on_delete=models.CASCADE, related_name='alerts', blank=True, null=True)
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    sent_to_owner = models.BooleanField(default=False)
    sent_to_admins = models.BooleanField(default=False)
    
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='acknowledged_alerts', blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Maintenance Alert'
        verbose_name_plural = 'Maintenance Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.equipment.name}"
    
    def acknowledge(self, user):
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, notes=""):
        self.status = 'resolved'
        self.resolution_notes = notes
        self.resolved_at = timezone.now()
        self.save()
    
    def dismiss(self):
        self.status = 'dismissed'
        self.save()