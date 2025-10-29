from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from equipment.models import Equipment, EquipmentType


class PricingRule(models.Model):
    """
    Model for defining pricing rules and policies
    """
    RULE_TYPE_CHOICES = [
        ('seasonal', 'Seasonal'),
        ('demand', 'Demand-based'),
        ('duration', 'Duration-based'),
        ('location', 'Location-based'),
        ('equipment_type', 'Equipment Type'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Applicability
    equipment_type = models.ForeignKey(
        EquipmentType, 
        on_delete=models.CASCADE, 
        related_name='pricing_rules', 
        blank=True, 
        null=True
    )
    equipment = models.ForeignKey(
        Equipment, 
        on_delete=models.CASCADE, 
        related_name='pricing_rules', 
        blank=True, 
        null=True
    )
    
    # Time-based rules
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    # Day of week rules
    days_of_week = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of days (0=Monday, 6=Sunday)"
    )
    
    # Location-based rules
    latitude_min = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    latitude_max = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude_min = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude_max = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Pricing adjustments
    hourly_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00,
        validators=[MinValueValidator(0.01), MaxValueValidator(10.00)]
    )
    daily_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00,
        validators=[MinValueValidator(0.01), MaxValueValidator(10.00)]
    )
    weekly_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00,
        validators=[MinValueValidator(0.01), MaxValueValidator(10.00)]
    )
    monthly_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00,
        validators=[MinValueValidator(0.01), MaxValueValidator(10.00)]
    )
    
    # Fixed rate overrides
    fixed_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fixed_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fixed_weekly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fixed_monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Priority and status
    priority = models.PositiveIntegerField(default=1, help_text="Higher number = higher priority")
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pricing Rule'
        verbose_name_plural = 'Pricing Rules'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def is_applicable(self, equipment, date, time=None, location=None):
        """Check if this pricing rule is applicable"""
        # Check equipment applicability
        if self.equipment and self.equipment != equipment:
            return False
        if self.equipment_type and equipment.equipment_type != self.equipment_type:
            return False
        
        # Check date range
        if self.start_date and date < self.start_date:
            return False
        if self.end_date and date > self.end_date:
            return False
        
        # Check time range
        if time and self.start_time and time < self.start_time:
            return False
        if time and self.end_time and time > self.end_time:
            return False
        
        # Check days of week
        if self.days_of_week and date.weekday() not in self.days_of_week:
            return False
        
        # Check location
        if location and self.latitude_min and location['lat'] < self.latitude_min:
            return False
        if location and self.latitude_max and location['lat'] > self.latitude_max:
            return False
        if location and self.longitude_min and location['lng'] < self.longitude_min:
            return False
        if location and self.longitude_max and location['lng'] > self.longitude_max:
            return False
        
        return True
    
    def calculate_rate(self, equipment, duration_hours, base_rate_type='daily'):
        """Calculate adjusted rate based on this rule"""
        if base_rate_type == 'hourly':
            if self.fixed_hourly_rate:
                return self.fixed_hourly_rate
            return equipment.hourly_rate * self.hourly_multiplier
        elif base_rate_type == 'daily':
            if self.fixed_daily_rate:
                return self.fixed_daily_rate
            return equipment.daily_rate * self.daily_multiplier
        elif base_rate_type == 'weekly':
            if self.fixed_weekly_rate:
                return self.fixed_weekly_rate
            return (equipment.weekly_rate or equipment.daily_rate * 7) * self.weekly_multiplier
        elif base_rate_type == 'monthly':
            if self.fixed_monthly_rate:
                return self.fixed_monthly_rate
            return (equipment.monthly_rate or equipment.daily_rate * 30) * self.monthly_multiplier
        
        return equipment.daily_rate


class SeasonalPricing(models.Model):
    """
    Model for seasonal pricing adjustments
    """
    SEASON_CHOICES = [
        ('planting', 'Planting Season'),
        ('growing', 'Growing Season'),
        ('harvesting', 'Harvesting Season'),
        ('off_season', 'Off Season'),
        ('peak', 'Peak Season'),
        ('low', 'Low Season'),
    ]
    
    name = models.CharField(max_length=200)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES)
    equipment_type = models.ForeignKey(
        EquipmentType, 
        on_delete=models.CASCADE, 
        related_name='seasonal_pricing'
    )
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Pricing adjustments
    hourly_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00,
        validators=[MinValueValidator(0.01), MaxValueValidator(10.00)]
    )
    daily_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.00,
        validators=[MinValueValidator(0.01), MaxValueValidator(10.00)]
    )
    
    # Fixed rates
    fixed_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fixed_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Seasonal Pricing'
        verbose_name_plural = 'Seasonal Pricing'
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.name} - {self.get_season_display()}"
    
    def is_active_for_date(self, date):
        """Check if this seasonal pricing is active for a given date"""
        return self.start_date <= date <= self.end_date


class DemandPricing(models.Model):
    """
    Model for demand-based dynamic pricing
    """
    equipment_type = models.ForeignKey(
        EquipmentType, 
        on_delete=models.CASCADE, 
        related_name='demand_pricing'
    )
    
    # Demand thresholds
    low_demand_threshold = models.PositiveIntegerField(default=0, help_text="Bookings per week")
    high_demand_threshold = models.PositiveIntegerField(default=10, help_text="Bookings per week")
    
    # Pricing adjustments based on demand
    low_demand_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.8,
        validators=[MinValueValidator(0.01), MaxValueValidator(2.00)]
    )
    normal_demand_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.0,
        validators=[MinValueValidator(0.01), MaxValueValidator(2.00)]
    )
    high_demand_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.3,
        validators=[MinValueValidator(0.01), MaxValueValidator(2.00)]
    )
    
    # Time window for demand calculation
    demand_calculation_days = models.PositiveIntegerField(default=7, help_text="Days to look back for demand calculation")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Demand Pricing'
        verbose_name_plural = 'Demand Pricing'
    
    def __str__(self):
        return f"Demand Pricing for {self.equipment_type.name}"
    
    def calculate_demand_level(self, date):
        """Calculate current demand level for the equipment type"""
        from django.utils import timezone
        from datetime import timedelta
        from bookings.models import Booking
        
        start_date = date - timedelta(days=self.demand_calculation_days)
        
        # Count bookings in the time window
        booking_count = Booking.objects.filter(
            equipment__equipment_type=self.equipment_type,
            start_date__gte=start_date,
            start_date__lte=date,
            status__in=['confirmed', 'in_progress']
        ).count()
        
        # Determine demand level
        if booking_count <= self.low_demand_threshold:
            return 'low'
        elif booking_count >= self.high_demand_threshold:
            return 'high'
        else:
            return 'normal'
    
    def get_multiplier(self, demand_level):
        """Get pricing multiplier for demand level"""
        if demand_level == 'low':
            return self.low_demand_multiplier
        elif demand_level == 'high':
            return self.high_demand_multiplier
        else:
            return self.normal_demand_multiplier


class PricingHistory(models.Model):
    """
    Model for tracking pricing changes over time
    """
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='pricing_history')
    pricing_rule = models.ForeignKey(PricingRule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pricing details
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    adjusted_rate = models.DecimalField(max_digits=10, decimal_places=2)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Context
    rate_type = models.CharField(max_length=20, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    
    # Demand context
    demand_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ], blank=True)
    
    # Timestamps
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pricing History'
        verbose_name_plural = 'Pricing History'
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"Pricing for {self.equipment.name} on {self.effective_date}"
