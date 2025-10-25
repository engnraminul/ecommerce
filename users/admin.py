from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_email_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_email_verified', 'date_joined', 'country')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Email Verification', {
            'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': (
                'phone', 'date_of_birth', 'profile_picture',
                'address_line_1', 'address_line_2', 'city', 
                'state', 'postal_code', 'country'
            )
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'phone')
        }),
    )
    
    readonly_fields = ('email_verification_token', 'email_verification_sent_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile admin"""
    list_display = ('user', 'newsletter_subscription', 'email_notifications', 'preferred_currency', 'created_at')
    list_filter = ('newsletter_subscription', 'email_notifications', 'sms_notifications', 'preferred_currency')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Address admin"""
    list_display = ('user', 'address_type', 'city', 'state', 'country', 'is_default')
    list_filter = ('address_type', 'is_default', 'country', 'state')
    search_fields = ('user__username', 'user__email', 'city', 'address_line_1')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User & Type', {
            'fields': ('user', 'address_type', 'is_default')
        }),
        ('Address Details', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        
    )
