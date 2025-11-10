from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Backup, BackupFile, BackupLog, BackupRestore, 
    BackupSchedule, BackupSettings
)


@admin.register(BackupSettings)
class BackupSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'backup_root_path', 'auto_cleanup_enabled', 'encrypt_backups', 'updated_at']
    fieldsets = (
        ('Storage Settings', {
            'fields': ('backup_root_path', 'max_backup_size')
        }),
        ('Retention Settings', {
            'fields': ('default_retention_days', 'auto_cleanup_enabled')
        }),
        ('Performance Settings', {
            'fields': ('chunk_size', 'max_concurrent_operations')
        }),
        ('Security Settings', {
            'fields': ('encrypt_backups', 'encryption_key')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'notification_emails')
        }),
        ('Advanced Settings', {
            'fields': ('verify_backup_integrity', 'create_pre_restore_backup')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not BackupSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


class BackupFileInline(admin.TabularInline):
    model = BackupFile
    extra = 0
    readonly_fields = ['filename', 'file_type', 'file_size', 'checksum', 'is_verified']
    fields = ['filename', 'file_type', 'formatted_size', 'checksum', 'is_verified']
    
    def formatted_size(self, obj):
        return obj.formatted_size
    formatted_size.short_description = 'File Size'


class BackupLogInline(admin.TabularInline):
    model = BackupLog
    extra = 0
    readonly_fields = ['level', 'message', 'operation', 'created_at']
    fields = ['level', 'message', 'operation', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        # Limit to recent logs to avoid performance issues
        return super().get_queryset(request)[:50]


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'backup_type', 'status', 'formatted_size', 
        'duration_formatted', 'created_at', 'action_buttons'
    ]
    list_filter = ['status', 'backup_type', 'created_at', 'include_media', 'compress_backup']
    search_fields = ['name', 'description', 'id']
    readonly_fields = [
        'id', 'status', 'progress_percentage', 'current_operation',
        'backup_path', 'backup_size', 'compressed_size', 'formatted_size', 
        'formatted_compressed_size', 'compression_ratio',
        'total_files', 'total_tables', 'total_records',
        'started_at', 'completed_at', 'duration_seconds', 'duration_formatted',
        'django_version', 'python_version', 'database_name',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'backup_type')
        }),
        ('Configuration', {
            'fields': ('include_media', 'include_staticfiles', 'compress_backup', 'preserve_foreign_keys')
        }),
        ('Status', {
            'fields': ('status', 'progress_percentage', 'current_operation', 'is_restorable')
        }),
        ('File Information', {
            'fields': ('backup_path', 'formatted_size', 'formatted_compressed_size', 'compression_ratio')
        }),
        ('Statistics', {
            'fields': ('total_files', 'total_tables', 'total_records')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_formatted')
        }),
        ('System Information', {
            'fields': ('django_version', 'python_version', 'database_name'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message', 'warnings', 'restore_notes'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BackupFileInline, BackupLogInline]
    actions = ['delete_selected_backups', 'verify_selected_backups']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-backup/', self.admin_site.admin_view(self.create_backup_view), name='backups_backup_create'),
            path('<path:object_id>/restore/', self.admin_site.admin_view(self.restore_backup_view), name='backups_backup_restore'),
            path('<path:object_id>/download/', self.admin_site.admin_view(self.download_backup_view), name='backups_backup_download'),
            path('<path:object_id>/verify/', self.admin_site.admin_view(self.verify_backup_view), name='backups_backup_verify'),
            path('cleanup/', self.admin_site.admin_view(self.cleanup_backups_view), name='backups_backup_cleanup'),
        ]
        return custom_urls + urls
    
    def action_buttons(self, obj):
        """Display action buttons for each backup"""
        if obj.status == 'completed':
            buttons = []
            
            # Restore button
            if obj.can_restore:
                buttons.append(
                    f'<a class="button" href="/admin/backups/backup/{obj.id}/restore/" '
                    f'style="background-color: #28a745; color: white; margin-right: 5px;">Restore</a>'
                )
            
            # Download button
            if obj.backup_path:
                buttons.append(
                    f'<a class="button" href="/admin/backups/backup/{obj.id}/download/" '
                    f'style="background-color: #007bff; color: white; margin-right: 5px;">Download</a>'
                )
            
            # Verify button
            buttons.append(
                f'<a class="button" href="/admin/backups/backup/{obj.id}/verify/" '
                f'style="background-color: #ffc107; color: white;">Verify</a>'
            )
            
            return format_html(''.join(buttons))
        
        return '-'
    action_buttons.short_description = 'Actions'
    
    def create_backup_view(self, request):
        """Custom view for creating backups"""
        if request.method == 'POST':
            try:
                from django.core.management import call_command
                from io import StringIO
                import threading
                
                # Get form data
                name = request.POST.get('name', '')
                description = request.POST.get('description', '')
                backup_type = request.POST.get('backup_type', 'full')
                compress = request.POST.get('compress', 'on') == 'on'
                
                # Start backup in background thread
                def run_backup():
                    try:
                        out = StringIO()
                        call_command(
                            'create_backup_safe',
                            name=name or None,
                            description=description,
                            type=backup_type,
                            compress=compress,
                            no_compress=not compress,
                            stdout=out
                        )
                    except Exception as e:
                        # Log error (in a real implementation, you'd want better error handling)
                        pass
                
                thread = threading.Thread(target=run_backup)
                thread.daemon = True
                thread.start()
                
                messages.success(request, 'Backup creation started in background. Check the backup list for progress.')
                return redirect('/admin/backups/backup/')
            
            except Exception as e:
                messages.error(request, f'Failed to start backup: {str(e)}')
        
        # Render form
        context = {
            'title': 'Create New Backup',
            'backup_types': Backup.BACKUP_TYPE_CHOICES,
        }
        return render(request, 'admin/backups/backup/create_backup.html', context)
    
    def restore_backup_view(self, request, object_id):
        """Custom view for restoring backups"""
        backup = self.get_object(request, object_id)
        
        if request.method == 'POST':
            try:
                from django.core.management import call_command
                from io import StringIO
                import threading
                
                # Get form data
                restore_database = request.POST.get('restore_database', 'on') == 'on'
                restore_media = request.POST.get('restore_media', 'on') == 'on'
                create_pre_backup = request.POST.get('create_pre_backup', 'on') == 'on'
                
                # Start restore in background thread
                def run_restore():
                    try:
                        out = StringIO()
                        args = [str(backup.id)]
                        kwargs = {
                            'stdout': out,
                            'force': True  # Skip confirmation in admin
                        }
                        
                        if not restore_database:
                            kwargs['no_database'] = True
                        if not restore_media:
                            kwargs['no_media'] = True
                        if not create_pre_backup:
                            kwargs['no_pre_backup'] = True
                        
                        call_command('restore_backup_safe', *args, **kwargs)
                    except Exception as e:
                        # Log error
                        pass
                
                thread = threading.Thread(target=run_restore)
                thread.daemon = True
                thread.start()
                
                messages.success(request, 'Backup restoration started in background. Check the restore operations for progress.')
                return redirect('/admin/backups/backuprestore/')
            
            except Exception as e:
                messages.error(request, f'Failed to start restoration: {str(e)}')
        
        context = {
            'title': f'Restore Backup: {backup.name}',
            'backup': backup,
            'can_restore_database': backup.backup_type in ['full', 'database'],
            'can_restore_media': backup.backup_type in ['full', 'media'] and backup.include_media,
        }
        return render(request, 'admin/backups/backup/restore_backup.html', context)
    
    def download_backup_view(self, request, object_id):
        """Download backup file"""
        backup = self.get_object(request, object_id)
        
        if not backup.backup_path or not backup.can_restore:
            messages.error(request, 'Backup file is not available for download.')
            return redirect('/admin/backups/backup/')
        
        # In a real implementation, you'd stream the file
        messages.info(request, f'Backup download would start for: {backup.backup_path}')
        return redirect('/admin/backups/backup/')
    
    def verify_backup_view(self, request, object_id):
        """Verify backup integrity"""
        backup = self.get_object(request, object_id)
        
        try:
            from .utils import backup_utils
            
            # Get backup files for verification
            backup_files = []
            for bf in backup.backup_files.all():
                backup_files.append({
                    'path': bf.backup_path,
                    'checksum': bf.checksum
                })
            
            # Verify integrity
            verify_results = backup_utils.verify_backup_integrity(backup_files)
            
            if verify_results['success']:
                messages.success(request, f'Backup verification passed: {verify_results["verified_files"]} files verified')
                # Mark all files as verified
                backup.backup_files.update(is_verified=True)
            else:
                messages.error(request, f'Backup verification failed: {verify_results["failed_files"]} files failed')
                for error in verify_results['errors']:
                    messages.error(request, error)
        
        except Exception as e:
            messages.error(request, f'Verification failed: {str(e)}')
        
        return redirect('/admin/backups/backup/')
    
    def cleanup_backups_view(self, request):
        """Clean up old backups"""
        if request.method == 'POST':
            try:
                retention_days = int(request.POST.get('retention_days', 30))
                
                from .utils import backup_utils
                cleanup_results = backup_utils.cleanup_old_backups(retention_days)
                
                if cleanup_results['success']:
                    messages.success(
                        request, 
                        f'Cleanup completed: {cleanup_results["deleted_backups"]} backups deleted, '
                        f'{cleanup_results["freed_space"]} bytes freed'
                    )
                else:
                    messages.error(request, 'Cleanup failed')
                    for error in cleanup_results['errors']:
                        messages.error(request, error)
            
            except Exception as e:
                messages.error(request, f'Cleanup failed: {str(e)}')
        
        return redirect('/admin/backups/backup/')
    
    def delete_selected_backups(self, request, queryset):
        """Custom action to delete backups and their files"""
        deleted_count = 0
        
        for backup in queryset:
            try:
                # Delete backup file if it exists
                if backup.backup_path and backup.backup_path.startswith('/'):
                    import os
                    if os.path.exists(backup.backup_path):
                        os.remove(backup.backup_path)
                
                # Delete database record
                backup.delete()
                deleted_count += 1
            
            except Exception as e:
                messages.error(request, f'Failed to delete backup {backup.name}: {str(e)}')
        
        messages.success(request, f'Successfully deleted {deleted_count} backup(s)')
    delete_selected_backups.short_description = "Delete selected backups and files"
    
    def verify_selected_backups(self, request, queryset):
        """Custom action to verify selected backups"""
        verified_count = 0
        failed_count = 0
        
        for backup in queryset.filter(status='completed'):
            try:
                from .utils import backup_utils
                
                backup_files = []
                for bf in backup.backup_files.all():
                    backup_files.append({
                        'path': bf.backup_path,
                        'checksum': bf.checksum
                    })
                
                verify_results = backup_utils.verify_backup_integrity(backup_files)
                
                if verify_results['success']:
                    backup.backup_files.update(is_verified=True)
                    verified_count += 1
                else:
                    failed_count += 1
            
            except Exception:
                failed_count += 1
        
        if verified_count > 0:
            messages.success(request, f'Successfully verified {verified_count} backup(s)')
        if failed_count > 0:
            messages.error(request, f'Failed to verify {failed_count} backup(s)')
    verify_selected_backups.short_description = "Verify selected backups"


@admin.register(BackupRestore)
class BackupRestoreAdmin(admin.ModelAdmin):
    list_display = [
        'backup', 'restore_mode', 'status', 'restored_records', 
        'restored_files', 'success_rate', 'created_at'
    ]
    list_filter = ['status', 'restore_mode', 'restore_database', 'restore_media', 'created_at']
    readonly_fields = [
        'id', 'backup', 'status', 'progress_percentage', 'current_operation',
        'restored_files', 'restored_records', 'skipped_files', 'failed_files',
        'success_rate', 'started_at', 'completed_at', 'duration_seconds',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'backup', 'restore_mode')
        }),
        ('Configuration', {
            'fields': ('restore_database', 'restore_media', 'selected_models', 'exclude_models')
        }),
        ('Status', {
            'fields': ('status', 'progress_percentage', 'current_operation')
        }),
        ('Results', {
            'fields': ('restored_files', 'restored_records', 'skipped_files', 'failed_files', 'success_rate')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Backup Information', {
            'fields': ('pre_restore_backup',),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message', 'warnings', 'restore_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'frequency', 'backup_type', 'is_active', 
        'last_run', 'next_run', 'created_at'
    ]
    list_filter = ['frequency', 'backup_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'frequency', 'cron_expression')
        }),
        ('Backup Configuration', {
            'fields': ('backup_type', 'include_media', 'include_staticfiles', 'compress_backup')
        }),
        ('Retention Policy', {
            'fields': ('max_backups_to_keep', 'delete_old_backups')
        }),
        ('Status', {
            'fields': ('is_active', 'last_run', 'next_run', 'last_backup')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.calculate_next_run()
        super().save_model(request, obj, form, change)


@admin.register(BackupFile)
class BackupFileAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'backup', 'file_type', 'formatted_size', 
        'is_verified', 'backed_up_at'
    ]
    list_filter = ['file_type', 'is_verified', 'backed_up_at', 'backup__backup_type']
    search_fields = ['filename', 'original_path', 'model_name', 'app_label']
    readonly_fields = [
        'backup', 'filename', 'original_path', 'backup_path', 'file_type',
        'file_size', 'formatted_size', 'checksum', 'mime_type',
        'model_name', 'app_label', 'record_count', 'backed_up_at'
    ]


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['backup', 'level', 'message_truncated', 'operation', 'created_at']
    list_filter = ['level', 'created_at', 'backup__backup_type']
    search_fields = ['message', 'operation', 'backup__name']
    readonly_fields = ['backup', 'level', 'message', 'operation', 'extra_data', 'created_at']
    
    def message_truncated(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_truncated.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual log creation


# Customize admin site
admin.site.site_header = "Backup Management"
admin.site.site_title = "Backup Admin"
admin.site.index_title = "Backup System Administration"