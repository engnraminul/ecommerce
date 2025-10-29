from django.contrib import admin
from .models import Contact, ContactSetting, ContactActivity


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'subject', 'status', 'priority', 'submitted_at', 'assigned_to']
    list_filter = ['status', 'priority', 'submitted_at', 'assigned_to']
    search_fields = ['name', 'email', 'phone', 'subject', 'message']
    ordering = ['-submitted_at']
    readonly_fields = ['submitted_at', 'updated_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'subject', 'message', 'attachment')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to', 'admin_notes')
        }),
        ('Tracking Information', {
            'fields': ('ip_address', 'user_agent', 'submitted_at', 'updated_at', 'replied_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to')


@admin.register(ContactSetting)
class ContactSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'description', 'created_at', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContactActivity)
class ContactActivityAdmin(admin.ModelAdmin):
    list_display = ['contact', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['contact__name', 'contact__email', 'user__username', 'action']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'ip_address', 'user_agent']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contact', 'user')
