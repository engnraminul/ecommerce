from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os

User = get_user_model()


class BackupType(models.TextChoices):
    """Backup type choices"""
    DATABASE_ONLY = 'database', 'Database Only'
    MEDIA_ONLY = 'media', 'Media Files Only'
    FULL_BACKUP = 'full', 'Database + Media Files'


class BackupStatus(models.TextChoices):
    """Backup status choices"""
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class RestoreStatus(models.TextChoices):
    """Restore status choices"""
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class BackupRecord(models.Model):
    """Model to track backup records"""
    
    name = models.CharField(max_length=255, help_text="Custom name for the backup")
    backup_type = models.CharField(
        max_length=20,
        choices=BackupType.choices,
        default=BackupType.FULL_BACKUP,
        help_text="Type of backup to create"
    )
    status = models.CharField(
        max_length=20,
        choices=BackupStatus.choices,
        default=BackupStatus.PENDING,
        help_text="Current backup status"
    )
    
    # File paths
    database_file = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to database backup file"
    )
    media_file = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to media backup file"
    )
    
    # Metadata
    file_size = models.BigIntegerField(
        default=0,
        help_text="Total backup size in bytes"
    )
    database_size = models.BigIntegerField(
        default=0,
        help_text="Database backup size in bytes"
    )
    media_size = models.BigIntegerField(
        default=0,
        help_text="Media backup size in bytes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User and logging
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this backup"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the backup"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if backup failed"
    )
    
    # Backup configuration
    compress = models.BooleanField(
        default=True,
        help_text="Whether to compress backup files"
    )
    exclude_logs = models.BooleanField(
        default=True,
        help_text="Exclude log files from media backup"
    )
    
    class Meta:
        db_table = 'backup_records'
        ordering = ['-created_at']
        verbose_name = 'Backup Record'
        verbose_name_plural = 'Backup Records'
        
    def __str__(self):
        return f"{self.name} - {self.get_backup_type_display()} ({self.status})"
    
    @property
    def duration(self):
        """Calculate backup duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_completed(self):
        """Check if backup is completed successfully"""
        return self.status == BackupStatus.COMPLETED
    
    @property
    def formatted_size(self):
        """Return formatted file size"""
        return self._format_bytes(self.file_size)
    
    @property
    def formatted_database_size(self):
        """Return formatted database size"""
        return self._format_bytes(self.database_size)
    
    @property
    def formatted_media_size(self):
        """Return formatted media size"""
        return self._format_bytes(self.media_size)
    
    def _format_bytes(self, bytes_size):
        """Format bytes to human readable format"""
        if bytes_size == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def get_backup_files(self):
        """Get list of backup files"""
        files = []
        if self.database_file and os.path.exists(self.database_file):
            files.append({
                'type': 'database',
                'path': self.database_file,
                'name': os.path.basename(self.database_file),
                'size': os.path.getsize(self.database_file)
            })
        if self.media_file and os.path.exists(self.media_file):
            files.append({
                'type': 'media',
                'path': self.media_file,
                'name': os.path.basename(self.media_file),
                'size': os.path.getsize(self.media_file)
            })
        return files
    
    def delete_backup_files(self):
        """Delete backup files from filesystem"""
        deleted_files = []
        if self.database_file and os.path.exists(self.database_file):
            os.remove(self.database_file)
            deleted_files.append(self.database_file)
        if self.media_file and os.path.exists(self.media_file):
            os.remove(self.media_file)
            deleted_files.append(self.media_file)
        return deleted_files


class RestoreRecord(models.Model):
    """Model to track restore operations"""
    
    name = models.CharField(max_length=255, help_text="Custom name for the restore")
    backup_record = models.ForeignKey(
        BackupRecord,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Associated backup record (if restoring from existing backup)"
    )
    
    # Upload files for external restore
    uploaded_database_file = models.FileField(
        upload_to='restore_uploads/database/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['sql', 'gz'])],
        help_text="Uploaded database file for restore"
    )
    uploaded_media_file = models.FileField(
        upload_to='restore_uploads/media/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['tar', 'gz', 'zip'])],
        help_text="Uploaded media file for restore"
    )
    
    restore_type = models.CharField(
        max_length=20,
        choices=BackupType.choices,
        default=BackupType.FULL_BACKUP,
        help_text="Type of restore to perform"
    )
    status = models.CharField(
        max_length=20,
        choices=RestoreStatus.choices,
        default=RestoreStatus.PENDING,
        help_text="Current restore status"
    )
    
    # Options
    overwrite_existing = models.BooleanField(
        default=False,
        help_text="Overwrite existing data during restore"
    )
    backup_before_restore = models.BooleanField(
        default=True,
        help_text="Create backup before performing restore"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User and logging
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who initiated this restore"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the restore"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if restore failed"
    )
    
    pre_restore_backup = models.ForeignKey(
        BackupRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restored_from',
        help_text="Backup created before this restore"
    )
    
    class Meta:
        db_table = 'restore_records'
        ordering = ['-created_at']
        verbose_name = 'Restore Record'
        verbose_name_plural = 'Restore Records'
        
    def __str__(self):
        return f"{self.name} - {self.get_restore_type_display()} ({self.status})"
    
    @property
    def duration(self):
        """Calculate restore duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_completed(self):
        """Check if restore is completed successfully"""
        return self.status == RestoreStatus.COMPLETED


class BackupSchedule(models.Model):
    """Model for scheduled backups"""
    
    class ScheduleType(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        CUSTOM = 'custom', 'Custom'
    
    name = models.CharField(max_length=255, unique=True)
    backup_type = models.CharField(
        max_length=20,
        choices=BackupType.choices,
        default=BackupType.FULL_BACKUP
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=ScheduleType.choices,
        default=ScheduleType.DAILY
    )
    
    # Schedule configuration
    hour = models.PositiveIntegerField(default=2, help_text="Hour of day (0-23)")
    minute = models.PositiveIntegerField(default=0, help_text="Minute (0-59)")
    day_of_week = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Day of week for weekly backup (0=Monday, 6=Sunday)"
    )
    day_of_month = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Day of month for monthly backup (1-31)"
    )
    
    # Options
    is_active = models.BooleanField(default=True)
    compress = models.BooleanField(default=True)
    exclude_logs = models.BooleanField(default=True)
    retention_days = models.PositiveIntegerField(
        default=30,
        help_text="Number of days to keep backups (0 = keep forever)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'backup_schedules'
        ordering = ['name']
        verbose_name = 'Backup Schedule'
        verbose_name_plural = 'Backup Schedules'
        
    def __str__(self):
        return f"{self.name} ({self.get_schedule_type_display()})"


class BackupSettings(models.Model):
    """Global backup settings"""
    
    # Storage settings
    backup_directory = models.CharField(
        max_length=500,
        default='backups/',
        help_text="Directory to store backup files"
    )
    max_backup_size = models.BigIntegerField(
        default=1073741824,  # 1GB
        help_text="Maximum backup file size in bytes"
    )
    
    # Database settings
    mysql_path = models.CharField(
        max_length=500,
        default='mysqldump',
        help_text="Path to mysqldump executable"
    )
    mysql_host = models.CharField(max_length=255, default='localhost')
    mysql_port = models.PositiveIntegerField(default=3306)
    mysql_user = models.CharField(max_length=255, blank=True)
    mysql_password = models.CharField(max_length=255, blank=True)
    mysql_database = models.CharField(max_length=255, blank=True)
    
    # Compression settings
    compression_level = models.PositiveIntegerField(
        default=6,
        help_text="Compression level (1-9, 9 = best compression)"
    )
    
    # Retention settings
    default_retention_days = models.PositiveIntegerField(
        default=30,
        help_text="Default number of days to keep backups"
    )
    auto_cleanup = models.BooleanField(
        default=True,
        help_text="Automatically delete old backups"
    )
    
    # Notification settings
    email_notifications = models.BooleanField(
        default=False,
        help_text="Send email notifications for backup status"
    )
    notification_email = models.EmailField(
        blank=True,
        help_text="Email address for notifications"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'backup_settings'
        verbose_name = 'Backup Settings'
        verbose_name_plural = 'Backup Settings'
        
    def __str__(self):
        return "Backup Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create backup settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings