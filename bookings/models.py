from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import User
from equipment.models import Equipment


class Booking(models.Model):
    """
    Model for equipment booking/rental requests
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    # Basic booking information
    booking_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='bookings')
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    actual_start_date = models.DateTimeField(blank=True, null=True)
    actual_end_date = models.DateTimeField(blank=True, null=True)
    
    # Duration and pricing
    duration_hours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='approved_bookings', 
        blank=True, 
        null=True
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # Location and delivery
    pickup_location = models.TextField(blank=True)
    delivery_location = models.TextField(blank=True)
    requires_delivery = models.BooleanField(default=False)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Special requirements
    special_requirements = models.TextField(blank=True)
    operator_required = models.BooleanField(default=False)
    operator_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notes and communication
    customer_notes = models.TextField(blank=True)
    owner_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.booking_number} - {self.equipment.name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = self.generate_booking_number()
        super().save(*args, **kwargs)
    
    def generate_booking_number(self):
        """Generate unique booking number"""
        import random
        import string
        while True:
            # Format: AGH-YYYYMMDD-XXXX
            date_part = timezone.now().strftime('%Y%m%d')
            random_part = ''.join(random.choices(string.digits, k=4))
            booking_number = f"AGH-{date_part}-{random_part}"
            
            if not Booking.objects.filter(booking_number=booking_number).exists():
                return booking_number
    
    @property
    def is_active(self):
        """Check if booking is currently active"""
        now = timezone.now()
        return (
            self.status in ['confirmed', 'in_progress'] and
            self.start_date <= now <= self.end_date
        )
    
    @property
    def is_overdue(self):
        """Check if booking is overdue"""
        now = timezone.now()
        return self.status == 'in_progress' and now > self.end_date
    
    @property
    def duration_days(self):
        """Calculate duration in days"""
        return (self.end_date - self.start_date).days
    
    @property
    def total_with_fees(self):
        """Calculate total amount including all fees"""
        return self.total_amount + self.delivery_fee + self.operator_fee
    
    def check_availability(self):
        """Check if equipment is available for the requested time period"""
        conflicting_bookings = Booking.objects.filter(
            equipment=self.equipment,
            status__in=['confirmed', 'in_progress'],
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        )
        
        if self.pk:
            conflicting_bookings = conflicting_bookings.exclude(pk=self.pk)
        
        return not conflicting_bookings.exists()
    
    def approve(self, approved_by):
        """Approve the booking"""
        self.status = 'confirmed'
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, reason=""):
        """Reject the booking"""
        self.status = 'rejected'
        self.owner_notes = f"Rejected: {reason}"
        self.save()
    
    def cancel(self, reason=""):
        """Cancel the booking"""
        self.status = 'cancelled'
        self.customer_notes = f"Cancelled: {reason}"
        self.save()
    
    def start_booking(self):
        """Mark booking as started"""
        self.status = 'in_progress'
        self.actual_start_date = timezone.now()
        self.save()
    
    def complete_booking(self):
        """Mark booking as completed"""
        self.status = 'completed'
        self.actual_end_date = timezone.now()
        self.save()


class BookingRequest(models.Model):
    """
    Model for booking requests that need approval
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='request')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Request details
    request_reason = models.TextField(blank=True)
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    # Response details
    response_notes = models.TextField(blank=True)
    responded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='responded_requests', 
        blank=True, 
        null=True
    )
    responded_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Booking Request'
        verbose_name_plural = 'Booking Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request for {self.booking.equipment.name} by {self.requested_by.username}"
    
    def approve(self, approved_by, notes=""):
        """Approve the booking request"""
        self.status = 'approved'
        self.responded_by = approved_by
        self.responded_at = timezone.now()
        self.response_notes = notes
        self.save()
        
        # Approve the associated booking
        self.booking.approve(approved_by)
    
    def reject(self, rejected_by, reason=""):
        """Reject the booking request"""
        self.status = 'rejected'
        self.responded_by = rejected_by
        self.responded_at = timezone.now()
        self.response_notes = reason
        self.save()
        
        # Reject the associated booking
        self.booking.reject(reason)


class BookingSchedule(models.Model):
    """
    Model for managing equipment availability schedules
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    
    # Availability periods
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status
    is_available = models.BooleanField(default=True)
    reason_unavailable = models.CharField(max_length=200, blank=True)
    
    # Special pricing
    special_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['equipment', 'date']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"Schedule for {self.equipment.name} on {self.date}"
    
    @property
    def duration_hours(self):
        """Calculate duration in hours"""
        from datetime import datetime
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return (end - start).total_seconds() / 3600
