from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import User, UserProfile, Address, DashboardPermission


class DashboardPermissionForm(forms.ModelForm):
    """Custom form for dashboard permissions with checkboxes"""
    allowed_tabs = forms.MultipleChoiceField(
        choices=DashboardPermission.DASHBOARD_TABS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select dashboard tabs this user can access"
    )
    
    class Meta:
        model = DashboardPermission
        fields = ['allowed_tabs']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['allowed_tabs'].initial = self.instance.allowed_tabs


class DashboardPermissionInline(admin.StackedInline):
    """Inline for dashboard permissions"""
    model = DashboardPermission
    form = DashboardPermissionForm
    extra = 0
    can_delete = False
    verbose_name = "Dashboard Permissions"
    verbose_name_plural = "Dashboard Permissions"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_email_verified', 'is_staff', 'is_active', 'date_joined', 'dashboard_access_summary')
    list_filter = ('is_staff', 'is_active', 'is_email_verified', 'date_joined', 'country')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    inlines = [DashboardPermissionInline]
    
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
        return super().get_queryset(request).select_related('profile').prefetch_related('dashboard_permissions')
    
    def dashboard_access_summary(self, obj):
        """Show a summary of dashboard access permissions"""
        if obj.is_superuser:
            return format_html('<span style="color: green; font-weight: bold;">🔓 Full Access (Superuser)</span>')
        elif obj.is_staff:
            return format_html('<span style="color: blue; font-weight: bold;">🔓 Full Access (Staff)</span>')
        else:
            try:
                permissions = obj.dashboard_permissions
                if permissions.allowed_tabs:
                    count = len(permissions.allowed_tabs)
                    return format_html('<span style="color: orange;">🔐 Limited Access ({} tabs)</span>', count)
                else:
                    return format_html('<span style="color: red;">🔒 No Access</span>')
            except DashboardPermission.DoesNotExist:
                return format_html('<span style="color: red;">🔒 No Permissions Set</span>')
    
    dashboard_access_summary.short_description = 'Dashboard Access'


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


@admin.register(DashboardPermission)
class DashboardPermissionAdmin(admin.ModelAdmin):
    """Dashboard Permission admin"""
    list_display = ('user', 'user_email', 'user_staff_status', 'tabs_count', 'allowed_tabs_display', 'updated_at')
    list_filter = ('user__is_staff', 'user__is_superuser', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    form = DashboardPermissionForm
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Dashboard Permissions', {
            'fields': ('allowed_tabs',),
            'description': 'Select which dashboard tabs this user can access. Note: Staff and superusers always have full access regardless of these settings.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_staff_status(self, obj):
        if obj.user.is_superuser:
            return format_html('<span style="color: red; font-weight: bold;">Superuser</span>')
        elif obj.user.is_staff:
            return format_html('<span style="color: blue; font-weight: bold;">Staff</span>')
        else:
            return format_html('<span style="color: gray;">Regular User</span>')
    user_staff_status.short_description = 'User Type'
    
    def tabs_count(self, obj):
        return len(obj.allowed_tabs) if obj.allowed_tabs else 0
    tabs_count.short_description = 'Tabs Count'
    
    def allowed_tabs_display(self, obj):
        if not obj.allowed_tabs:
            return format_html('<span style="color: red;">No access</span>')
        
        tab_dict = dict(DashboardPermission.DASHBOARD_TABS)
        tab_names = [tab_dict.get(tab, tab) for tab in obj.allowed_tabs[:3]]  # Show first 3
        display = ', '.join(tab_names)
        
        if len(obj.allowed_tabs) > 3:
            display += f' (+{len(obj.allowed_tabs) - 3} more)'
        
        return format_html('<span style="color: green;">{}</span>', display)
    allowed_tabs_display.short_description = 'Allowed Tabs'
