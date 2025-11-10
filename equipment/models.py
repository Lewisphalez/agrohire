from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class EquipmentType(models.Model):
    """
    Model for categorizing different types of agricultural equipment
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('tractor', 'Tractor'),
            ('harvester', 'Harvester'),
            ('planter', 'Planter'),
            ('irrigation', 'Irrigation'),
            ('sprayer', 'Sprayer'),
            ('tillage', 'Tillage'),
            ('transport', 'Transport'),
            ('other', 'Other'),
        ]
    )
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    
    # Default pricing
    base_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Maintenance requirements
    maintenance_interval_hours = models.PositiveIntegerField(default=100, help_text="Hours between maintenance")
    maintenance_interval_days = models.PositiveIntegerField(default=30, help_text="Days between maintenance")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Equipment Type'
        verbose_name_plural = 'Equipment Types'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Equipment(models.Model):
    """
    Model for individual equipment items available for hire
    """
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.CASCADE, related_name='equipment')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_equipment')
    
    # Description and details
    description = models.TextField()
    specifications = models.JSONField(default=dict, blank=True, help_text="Technical specifications as JSON")
    features = models.JSONField(default=list, blank=True, help_text="List of features as JSON")
    
    # Physical characteristics
    model = models.CharField(max_length=100, blank=True)
    year_manufactured = models.PositiveIntegerField(blank=True, null=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Location
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Kenya')
    
    # Pricing
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    weekly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Operational details
    fuel_type = models.CharField(
        max_length=20,
        choices=[
            ('diesel', 'Diesel'),
            ('petrol', 'Petrol'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('other', 'Other'),
        ],
        blank=True
    )
    fuel_consumption = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Liters per hour")
    capacity = models.CharField(max_length=100, blank=True, help_text="Equipment capacity (e.g., HP, tons, etc.)")
    
    # Maintenance and usage
    total_hours = models.PositiveIntegerField(default=0, help_text="Total operating hours")
    total_kilometers = models.PositiveIntegerField(default=0, help_text="Total kilometers covered by this equipment")
    last_maintenance_date = models.DateField(blank=True, null=True)
    next_maintenance_date = models.DateField(blank=True, null=True)
    
    # Insurance and documentation
    insurance_expiry = models.DateField(blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True)
    
    # Images and media
    main_image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)
    
    # Availability settings
    is_active = models.BooleanField(default=True)
    minimum_booking_hours = models.PositiveIntegerField(default=1)
    maximum_booking_days = models.PositiveIntegerField(default=30)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.owner.get_full_name_or_business()}"
    
    @property
    def is_available(self):
        return self.status == 'available' and self.is_active
    
    @property
    def needs_maintenance(self):
        if not self.last_maintenance_date or not self.next_maintenance_date:
            return False
        from django.utils import timezone
        return timezone.now().date() >= self.next_maintenance_date
    
    def calculate_rate(self, duration_hours):
        """Calculate rate based on duration"""
        if duration_hours <= 8:  # Daily rate
            return self.get_current_price('daily')
        elif duration_hours <= 168:  # Weekly rate
            return self.get_current_price('weekly')
        else:  # Monthly rate
            return self.get_current_price('monthly')

    @property
    def active_seasonal_rule(self):
        from pricing.models import SeasonalPricing
        from django.utils import timezone
        today = timezone.now().date()
        return SeasonalPricing.objects.filter(
            equipment_type=self.equipment_type,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).first()

    def get_current_price(self, rate_type='daily'):
        """Calculates the current price including seasonal adjustments."""
        rule = self.active_seasonal_rule
        if not rule:
            if rate_type == 'hourly':
                return self.hourly_rate
            elif rate_type == 'weekly':
                return self.weekly_rate or self.daily_rate * 7
            elif rate_type == 'monthly':
                return self.monthly_rate or self.daily_rate * 30
            return self.daily_rate

        if rate_type == 'hourly':
            base_price = rule.fixed_hourly_rate or self.hourly_rate
            return base_price * rule.hourly_multiplier
        elif rate_type == 'daily':
            base_price = rule.fixed_daily_rate or self.daily_rate
            return base_price * rule.daily_multiplier
        elif rate_type == 'weekly':
            base_price = self.weekly_rate or self.daily_rate * 7
            return base_price * rule.daily_multiplier
        elif rate_type == 'monthly':
            base_price = self.monthly_rate or self.daily_rate * 30
            return base_price * rule.daily_multiplier
        
        return self.daily_rate


class EquipmentImage(models.Model):
    """
    Model for storing multiple images for equipment
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='equipment_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.equipment.name}"


class EquipmentReview(models.Model):
    """
    Model for equipment reviews and ratings
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_reviews')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='review', blank=True, null=True)
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField()
    
    # Review categories
    equipment_condition = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    operator_skill = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    value_for_money = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['equipment', 'user', 'booking']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.equipment.name}"
    
    @property
    def average_rating(self):
        """Calculate average of all rating categories"""
        ratings = [self.rating]
        if self.equipment_condition:
            ratings.append(self.equipment_condition)
        if self.operator_skill:
            ratings.append(self.operator_skill)
        if self.value_for_money:
            ratings.append(self.value_for_money)
        return sum(ratings) / len(ratings)
