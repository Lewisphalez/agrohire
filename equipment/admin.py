from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EquipmentType, Equipment, EquipmentImage, EquipmentReview


class EquipmentImageInline(admin.TabularInline):
    model = EquipmentImage
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'order')


class EquipmentReviewInline(admin.TabularInline):
    model = EquipmentReview
    extra = 0
    readonly_fields = ('user', 'equipment', 'rating', 'comment', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_daily_rate', 'base_hourly_rate', 'equipment_count')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'icon')
        }),
        ('Default Pricing', {
            'fields': ('base_daily_rate', 'base_hourly_rate')
        }),
        ('Maintenance Settings', {
            'fields': ('maintenance_interval_hours', 'maintenance_interval_days')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def equipment_count(self, obj):
        return obj.equipment.count()
    equipment_count.short_description = 'Equipment Count'


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'owner', 'condition', 'status', 'daily_rate', 'is_available', 'location_display')
    list_filter = ('equipment_type', 'condition', 'status', 'fuel_type', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'model', 'owner__username', 'owner__business_name', 'city')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'total_hours')
    
    inlines = [EquipmentImageInline, EquipmentReviewInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'equipment_type', 'owner', 'description', 'specifications', 'features')
        }),
        ('Physical Details', {
            'fields': ('model', 'year_manufactured', 'condition', 'status', 'main_image')
        }),
        ('Location', {
            'fields': ('city', 'country')
        }),
        ('Pricing', {
            'fields': ('daily_rate', 'hourly_rate', 'weekly_rate', 'monthly_rate')
        }),
        ('Operational Details', {
            'fields': ('fuel_type', 'fuel_consumption', 'capacity')
        }),
        ('Maintenance', {
            'fields': ('total_hours', 'last_maintenance_date', 'next_maintenance_date')
        }),
        ('Documentation', {
            'fields': ('insurance_expiry', 'registration_number')
        }),
        ('Availability Settings', {
            'fields': ('is_active', 'minimum_booking_hours', 'maximum_booking_days')
        }),
    )
    
    def location_display(self, obj):
        if obj.city and obj.country:
            return f"{obj.city}, {obj.country}"
        elif obj.city:
            return obj.city
        elif obj.country:
            return obj.country
        return "Not specified"
    location_display.short_description = 'Location'
    
    def is_available(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green;">✓ Available</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Available</span>')
    is_available.short_description = 'Availability'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('equipment_type', 'owner')


@admin.register(EquipmentImage)
class EquipmentImageAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'image_preview', 'caption', 'is_primary', 'order')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('equipment__name', 'caption')
    ordering = ('equipment__name', 'order')
    
    fieldsets = (
        ('Image Information', {
            'fields': ('equipment', 'image', 'caption', 'is_primary', 'order')
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(EquipmentReview)
class EquipmentReviewAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'rating', 'average_rating', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('equipment__name', 'user__username', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('equipment', 'user', 'booking', 'rating', 'comment', 'equipment_condition', 'operator_skill', 'value_for_money', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('equipment', 'user', 'booking', 'rating', 'comment')
        }),
        ('Detailed Ratings', {
            'fields': ('equipment_condition', 'operator_skill', 'value_for_money')
        }),
        ('Status', {
            'fields': ('is_verified',)
        }),
    )
    
    def average_rating(self, obj):
        return f"{obj.average_rating:.1f}/5"
    average_rating.short_description = 'Average Rating'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('equipment', 'user')
