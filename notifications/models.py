from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User


class NotificationTemplate(models.Model):
    """
    Model for notification templates
    """
    TEMPLATE_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    NOTIFICATION_CATEGORY_CHOICES = [
        ('booking', 'Booking'),
        ('payment', 'Payment'),
        ('equipment', 'Equipment'),
        ('maintenance', 'Maintenance'),
        ('system', 'System'),
        ('marketing', 'Marketing'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=NOTIFICATION_CATEGORY_CHOICES)
    
    # Template content
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    sms_body = models.TextField(blank=True, help_text="SMS version of the message")
    
    # Template variables
    variables = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of available template variables"
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='normal'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render_template(self, context_data):
        """Render template with provided context"""
        try:
            rendered_body = self.body
            for key, value in context_data.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_body = rendered_body.replace(placeholder, str(value))
            
            rendered_subject = self.subject
            for key, value in context_data.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_subject = rendered_subject.replace(placeholder, str(value))
            
            return {
                'subject': rendered_subject,
                'body': rendered_body,
                'sms_body': self.sms_body
            }
        except Exception as e:
            return {
                'subject': self.subject,
                'body': self.body,
                'sms_body': self.sms_body,
                'error': str(e)
            }


class Notification(models.Model):
    """
    Model for individual notifications
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Recipient and content
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    sms_message = models.TextField(blank=True)
    
    # Status and delivery
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Delivery details
    delivery_attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    error_message = models.TextField(blank=True)
    
    # External service details
    external_id = models.CharField(max_length=100, blank=True, help_text="ID from external service (email/SMS provider)")
    
    # Related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username}"
    
    def mark_as_sent(self, external_id=None):
        """Mark notification as sent"""
        from django.utils import timezone
        
        self.status = 'sent'
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save()
    
    def mark_as_delivered(self):
        """Mark notification as delivered"""
        from django.utils import timezone
        
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message=""):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.delivery_attempts += 1
        self.save()
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        
        self.read_at = timezone.now()
        self.save()
    
    @property
    def is_read(self):
        return self.read_at is not None
    
    @property
    def can_retry(self):
        return self.status == 'failed' and self.delivery_attempts < self.max_attempts


class NotificationPreference(models.Model):
    """
    Model for user notification preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_notifications = models.BooleanField(default=True)
    email_booking_updates = models.BooleanField(default=True)
    email_payment_updates = models.BooleanField(default=True)
    email_equipment_updates = models.BooleanField(default=True)
    email_maintenance_alerts = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    # SMS preferences
    sms_notifications = models.BooleanField(default=True)
    sms_booking_updates = models.BooleanField(default=True)
    sms_payment_updates = models.BooleanField(default=True)
    sms_urgent_alerts = models.BooleanField(default=True)
    
    # Push notification preferences
    push_notifications = models.BooleanField(default=True)
    push_booking_updates = models.BooleanField(default=True)
    push_payment_updates = models.BooleanField(default=True)
    push_equipment_updates = models.BooleanField(default=True)
    
    # In-app notification preferences
    in_app_notifications = models.BooleanField(default=True)
    
    # Frequency preferences
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='immediate'
    )
    
    # Quiet hours
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def should_send_notification(self, notification_type, category):
        """Check if notification should be sent based on preferences"""
        if notification_type == 'email':
            if not self.email_notifications:
                return False
            if category == 'booking' and not self.email_booking_updates:
                return False
            if category == 'payment' and not self.email_payment_updates:
                return False
            if category == 'equipment' and not self.email_equipment_updates:
                return False
            if category == 'maintenance' and not self.email_maintenance_alerts:
                return False
            if category == 'marketing' and not self.email_marketing:
                return False
        
        elif notification_type == 'sms':
            if not self.sms_notifications:
                return False
            if category == 'booking' and not self.sms_booking_updates:
                return False
            if category == 'payment' and not self.sms_payment_updates:
                return False
        
        elif notification_type == 'push':
            if not self.push_notifications:
                return False
            if category == 'booking' and not self.push_booking_updates:
                return False
            if category == 'payment' and not self.push_payment_updates:
                return False
            if category == 'equipment' and not self.push_equipment_updates:
                return False
        
        elif notification_type == 'in_app':
            if not self.in_app_notifications:
                return False
        
        return True
    
    def is_in_quiet_hours(self):
        """Check if current time is in quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now().time()
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            # Quiet hours span midnight
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class NotificationLog(models.Model):
    """
    Model for logging notification delivery attempts
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_logs')
    attempt_number = models.PositiveIntegerField()
    
    # Delivery details
    status = models.CharField(max_length=20, choices=Notification.STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    external_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"Log for {self.notification} - Attempt {self.attempt_number}"
