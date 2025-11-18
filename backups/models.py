from django.db import models
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
import os

User = get_user_model()


class Backup(models.Model):
    BACKUP_TYPE_CHOICES = [
        ('database', 'Database Only'),
        ('media', 'Media Files Only'),
        ('full', 'Full Backup (Database + Media)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('creating', 'Creating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('restoring', 'Restoring'),
        ('restored', 'Restored'),
    ]
    
    name = models.CharField(max_length=255, help_text="Backup name/description")
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # File paths
    database_file = models.CharField(max_length=500, blank=True, null=True)
    media_file = models.CharField(max_length=500, blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Size information
    database_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    media_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    total_size = models.BigIntegerField(default=0, help_text="Total size in bytes")
    
    # Additional metadata
    file_count = models.IntegerField(default=0, help_text="Number of files in backup")
    compression_level = models.IntegerField(default=6)
    error_message = models.TextField(blank=True, null=True)
    
    # Restoration tracking
    last_restored_at = models.DateTimeField(blank=True, null=True)
    restoration_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Backup"
        verbose_name_plural = "Backups"
    
    def __str__(self):
        return f"{self.name} ({self.get_backup_type_display()}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_complete(self):
        return self.status == 'completed'
    
    @property
    def can_restore(self):
        return self.status == 'completed' and (self.database_file or self.media_file)
    
    @property
    def can_download(self):
        return self.status == 'completed'
    
    @property
    def formatted_size(self):
        """Return human-readable size format"""
        size = self.total_size
        if size == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def get_download_files(self):
        """Return list of files available for download"""
        files = []
        if self.database_file and os.path.exists(self.database_file):
            files.append({
                'type': 'database',
                'path': self.database_file,
                'name': os.path.basename(self.database_file),
                'size': self.database_size
            })
        if self.media_file and os.path.exists(self.media_file):
            files.append({
                'type': 'media', 
                'path': self.media_file,
                'name': os.path.basename(self.media_file),
                'size': self.media_size
            })
        return files
    
    def delete_backup_files(self):
        """Delete backup files from filesystem"""
        files_deleted = []
        
        if self.database_file and os.path.exists(self.database_file):
            try:
                os.remove(self.database_file)
                files_deleted.append('database')
            except OSError:
                pass
        
        if self.media_file and os.path.exists(self.media_file):
            try:
                os.remove(self.media_file)
                files_deleted.append('media')
            except OSError:
                pass
        
        return files_deleted
    
    def delete(self, *args, **kwargs):
        """Override delete method to remove backup files before deleting record"""
        # Delete backup files from filesystem first
        self.delete_backup_files()
        
        # Then delete the database record
        super().delete(*args, **kwargs)


class BackupSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    name = models.CharField(max_length=255)
    backup_type = models.CharField(max_length=20, choices=Backup.BACKUP_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Schedule settings
    hour = models.IntegerField(default=2, help_text="Hour of the day (0-23)")
    minute = models.IntegerField(default=0, help_text="Minute of the hour (0-59)")
    day_of_week = models.IntegerField(blank=True, null=True, help_text="Day of week for weekly backups (0-6, Monday=0)")
    day_of_month = models.IntegerField(blank=True, null=True, help_text="Day of month for monthly backups (1-31)")
    
    # Retention settings
    retention_days = models.IntegerField(default=30, help_text="Days to keep backups")
    max_backups = models.IntegerField(default=10, help_text="Maximum number of backups to keep")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Backup Schedule"
        verbose_name_plural = "Backup Schedules"
    
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"


class RestoreLog(models.Model):
    backup = models.ForeignKey(Backup, on_delete=models.CASCADE, related_name='restore_logs')
    restored_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    restore_type = models.CharField(max_length=20, choices=Backup.BACKUP_TYPE_CHOICES)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    # Pre-restore validation
    validation_passed = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Restore Log"
        verbose_name_plural = "Restore Logs"
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.backup.name} - {status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
