from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import BackupRecord, RestoreRecord, BackupSchedule, BackupSettings


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    """Admin interface for backup records"""
    
    list_display = [
        'name', 'backup_type', 'status', 'formatted_size', 
        'created_at', 'duration_display', 'created_by'
    ]
    list_filter = ['backup_type', 'status', 'created_at', 'compress']
    search_fields = ['name', 'description']
    readonly_fields = [
        'status', 'database_file', 'media_file', 'file_size', 
        'database_size', 'media_size', 'started_at', 'completed_at',
        'error_message', 'duration_display', 'backup_files_display'
    ]
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'backup_type', 'description', 'created_by')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at', 'duration_display', 'error_message')
        }),
        ('Files & Sizes', {
            'fields': ('database_file', 'media_file', 'file_size', 'database_size', 'media_size', 'backup_files_display')
        }),
        ('Options', {
            'fields': ('compress', 'exclude_logs')
        }),
    ]
    
    def duration_display(self, obj):
        """Display backup duration"""
        if obj.duration:
            return str(obj.duration).split('.')[0]  # Remove microseconds
        return '-'
    duration_display.short_description = 'Duration'
    
    def backup_files_display(self, obj):
        """Display backup files with download links"""
        files = obj.get_backup_files()
        if not files:
            return 'No files'
        
        html = '<ul>'
        for file_info in files:
            download_url = reverse(
                'backup:download_backup_file', 
                args=[obj.id, file_info['type']]
            )
            html += f'<li><a href="{download_url}" target="_blank">{file_info["name"]}</a> ({obj._format_bytes(file_info["size"])})</li>'
        html += '</ul>'
        return format_html(html)
    backup_files_display.short_description = 'Backup Files'
    
    def has_add_permission(self, request):
        """Disable adding records through admin (use API instead)"""
        return False


@admin.register(RestoreRecord)
class RestoreRecordAdmin(admin.ModelAdmin):
    """Admin interface for restore records"""
    
    list_display = [
        'name', 'restore_type', 'status', 'created_at', 
        'duration_display', 'created_by'
    ]
    list_filter = ['restore_type', 'status', 'created_at', 'overwrite_existing']
    search_fields = ['name', 'description']
    readonly_fields = [
        'status', 'started_at', 'completed_at', 'error_message',
        'duration_display', 'pre_restore_backup'
    ]
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'restore_type', 'description', 'created_by')
        }),
        ('Source', {
            'fields': ('backup_record', 'uploaded_database_file', 'uploaded_media_file')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at', 'duration_display', 'error_message')
        }),
        ('Options', {
            'fields': ('overwrite_existing', 'backup_before_restore', 'pre_restore_backup')
        }),
    ]
    
    def duration_display(self, obj):
        """Display restore duration"""
        if obj.duration:
            return str(obj.duration).split('.')[0]  # Remove microseconds
        return '-'
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        """Disable adding records through admin (use API instead)"""
        return False


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    """Admin interface for backup schedules"""
    
    list_display = [
        'name', 'backup_type', 'schedule_type', 'is_active',
        'next_run', 'last_run', 'created_by'
    ]
    list_filter = ['backup_type', 'schedule_type', 'is_active', 'compress']
    search_fields = ['name']
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'backup_type', 'created_by')
        }),
        ('Schedule', {
            'fields': ('schedule_type', 'hour', 'minute', 'day_of_week', 'day_of_month', 'is_active')
        }),
        ('Options', {
            'fields': ('compress', 'exclude_logs', 'retention_days')
        }),
        ('Status', {
            'fields': ('last_run', 'next_run')
        }),
    ]
    readonly_fields = ['last_run', 'next_run']
    
    def save_model(self, request, obj, form, change):
        """Set created_by field on save"""
        if not change:  # Only on create
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BackupSettings)
class BackupSettingsAdmin(admin.ModelAdmin):
    """Admin interface for backup settings"""
    
    fieldsets = [
        ('Storage Settings', {
            'fields': ('backup_directory', 'max_backup_size')
        }),
        ('Database Settings', {
            'fields': ('mysql_path', 'mysql_host', 'mysql_port', 'mysql_user', 'mysql_password', 'mysql_database')
        }),
        ('Compression Settings', {
            'fields': ('compression_level',)
        }),
        ('Retention Settings', {
            'fields': ('default_retention_days', 'auto_cleanup')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'notification_email')
        }),
    ]
    
    def has_add_permission(self, request):
        """Only allow one settings instance"""
        return not BackupSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of settings"""
        return False