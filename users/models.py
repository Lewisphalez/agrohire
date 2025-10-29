from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('equipment_owner', 'Equipment Owner'),
        ('admin', 'Admin'),
    ]
    
    # Basic profile fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='farmer')
    phone_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        blank=True,
        null=True
    )
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Business-specific fields
    business_name = models.CharField(max_length=200, blank=True, null=True)
    business_registration_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Location fields
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Verification fields
    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    @property
    def is_farmer(self):
        return self.role == 'farmer'
    
    @property
    def is_equipment_owner(self):
        return self.role == 'equipment_owner'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def get_full_name_or_business(self):
        """Return business name if available, otherwise full name"""
        if self.business_name:
            return self.business_name
        return self.get_full_name() or self.username


class UserProfile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional personal information
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        blank=True,
        null=True
    )
    
    # Farming/Equipment specific information
    experience_years = models.PositiveIntegerField(default=0)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Farm size in acres")
    farm_type = models.CharField(
        max_length=50,
        choices=[
            ('crop', 'Crop Farming'),
            ('livestock', 'Livestock Farming'),
            ('mixed', 'Mixed Farming'),
            ('horticulture', 'Horticulture'),
            ('other', 'Other'),
        ],
        blank=True,
        null=True
    )
    
    # Contact preferences
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('sms', 'SMS'),
        ],
        default='phone'
    )
    
    # Social media links
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.username}"
