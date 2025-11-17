from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Backup, BackupSchedule, RestoreLog


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'backup_type', 'status_badge', 'formatted_size', 
        'created_by', 'created_at', 'restoration_count', 'backup_actions'
    ]
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['name', 'created_by__email']
    readonly_fields = [
        'status', 'database_file', 'media_file', 'database_size', 
        'media_size', 'total_size', 'file_count', 'completed_at',
        'last_restored_at', 'restoration_count'
    ]
    ordering = ['-created_at']
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'creating': '#17a2b8', 
            'completed': '#28a745',
            'failed': '#dc3545',
            'restoring': '#17a2b8',
            'restored': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def backup_actions(self, obj):
        if obj.can_download:
            download_url = reverse('admin:backup_download', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank">Download</a>',
                download_url
            )
        return '-'
    backup_actions.short_description = 'Actions'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:backup_id>/download/',
                self.admin_site.admin_view(self.download_backup),
                name='backup_download',
            ),
        ]
        return custom_urls + urls
    
    def download_backup(self, request, backup_id):
        from django.shortcuts import get_object_or_404
        from django.http import FileResponse
        import os
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        if backup.database_file and os.path.exists(backup.database_file):
            return FileResponse(
                open(backup.database_file, 'rb'),
                as_attachment=True,
                filename=os.path.basename(backup.database_file)
            )
        elif backup.media_file and os.path.exists(backup.media_file):
            return FileResponse(
                open(backup.media_file, 'rb'),
                as_attachment=True,
                filename=os.path.basename(backup.media_file)
            )


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'backup_type', 'frequency', 'is_active_badge', 
        'next_run', 'last_run', 'retention_days'
    ]
    list_filter = ['backup_type', 'frequency', 'is_active']
    search_fields = ['name']
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">Active</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def next_run(self, obj):
        # This would calculate next run time based on schedule
        return 'Calculated next run'
    next_run.short_description = 'Next Run'


@admin.register(RestoreLog)
class RestoreLogAdmin(admin.ModelAdmin):
    list_display = [
        'backup', 'restore_type', 'restored_by', 'started_at', 
        'success_badge', 'duration'
    ]
    list_filter = ['restore_type', 'success', 'started_at']
    search_fields = ['backup__name', 'restored_by__email']
    readonly_fields = [
        'backup', 'restored_by', 'restore_type', 'started_at', 
        'completed_at', 'success', 'error_message', 
        'validation_passed', 'validation_notes'
    ]
    ordering = ['-started_at']
    
    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">Success</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">Failed</span>'
        )
    success_badge.short_description = 'Result'
    
    def duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration)
        return '-'
    duration.short_description = 'Duration'
