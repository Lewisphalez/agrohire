from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'business_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture')}),
        ('Business info', {'fields': ('business_name', 'business_registration_number')}),
        ('Location', {'fields': ('latitude', 'longitude')}),
        ('Verification', {'fields': ('is_verified', 'verification_document')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_years', 'farm_size', 'farm_type', 'preferred_contact_method')
    list_filter = ('farm_type', 'preferred_contact_method', 'gender')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__username',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'date_of_birth', 'gender')
        }),
        ('Farming Information', {
            'fields': ('experience_years', 'farm_size', 'farm_type')
        }),
        ('Contact Preferences', {
            'fields': ('preferred_contact_method',)
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


# Register the custom User model
admin.site.register(User, UserAdmin)
