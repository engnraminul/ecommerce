from django.contrib import admin
from .models import DashboardSetting, AdminActivity, EmailConfiguration, EmailTemplate, EmailLog

@admin.register(DashboardSetting)
class DashboardSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'timestamp')
    list_filter = ('action', 'model_name', 'user', 'timestamp')
    search_fields = ('user__username', 'action', 'model_name', 'object_repr')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 
                      'changes', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'smtp_type', 'smtp_host', 'smtp_port', 'is_active', 'is_verified', 'created_at')
    list_filter = ('smtp_type', 'is_active', 'is_verified', 'created_at')
    search_fields = ('name', 'smtp_host', 'from_email')
    readonly_fields = ('created_at', 'updated_at', 'last_test_date', 'test_result')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'smtp_type', 'is_active')
        }),
        ('SMTP Settings', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_use_tls', 'smtp_use_ssl', 
                      'smtp_username', 'smtp_password')
        }),
        ('Sender Information', {
            'fields': ('from_email', 'from_name')
        }),
        ('Test Results', {
            'fields': ('is_verified', 'test_email_sent', 'last_test_date', 'test_result'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Ensure only one active configuration
        if obj.is_active:
            EmailConfiguration.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'send_to_user_email', 
                   'send_to_checkout_email', 'created_at')
    list_filter = ('template_type', 'is_active', 'send_to_user_email', 
                   'send_to_checkout_email', 'created_at')
    search_fields = ('name', 'subject', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'is_active', 'description')
        }),
        ('Email Content', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Send Settings', {
            'fields': ('send_to_user_email', 'send_to_checkout_email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'subject', 'status', 'template', 'created_at', 'sent_at')
    list_filter = ('status', 'template__template_type', 'email_config', 'created_at')
    search_fields = ('recipient_email', 'subject', 'user__email', 'user__username')
    readonly_fields = ('recipient_email', 'sender_email', 'subject', 'template', 'status',
                      'error_message', 'user', 'order', 'email_config', 'created_at', 'sent_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
