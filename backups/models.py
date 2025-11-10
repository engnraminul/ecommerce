from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.conf import settings
import os
import uuid
import json

User = get_user_model()


class Backup(models.Model):
    """Main backup model for tracking backup operations"""
    
    BACKUP_TYPE_CHOICES = [
        ('full', 'Full Backup (Database + Media)'),
        ('database', 'Database Only'),
        ('media', 'Media Files Only'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Descriptive name for this backup")
    description = models.TextField(blank=True, null=True, help_text="Optional description or notes")
    
    # Backup configuration
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES, default='full')
    include_media = models.BooleanField(default=True, help_text="Include media files in backup")
    include_staticfiles = models.BooleanField(default=False, help_text="Include static files in backup")
    compress_backup = models.BooleanField(default=True, help_text="Compress backup files")
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    current_operation = models.CharField(max_length=200, blank=True, help_text="Current backup operation")
    
    # File information
    backup_path = models.CharField(max_length=500, blank=True, help_text="Path to backup file/directory")
    backup_size = models.BigIntegerField(default=0, help_text="Total backup size in bytes")
    compressed_size = models.BigIntegerField(default=0, help_text="Compressed backup size in bytes")
    
    # Metadata
    database_name = models.CharField(max_length=100, blank=True)
    django_version = models.CharField(max_length=50, blank=True)
    python_version = models.CharField(max_length=50, blank=True)
    
    # Statistics
    total_files = models.IntegerField(default=0, help_text="Total number of files in backup")
    total_tables = models.IntegerField(default=0, help_text="Total number of database tables")
    total_records = models.BigIntegerField(default=0, help_text="Total number of database records")
    
    # Foreign key constraints handling
    preserve_foreign_keys = models.BooleanField(default=True, help_text="Preserve foreign key relationships")
    backup_order = models.JSONField(default=list, help_text="Order of model backup for foreign key safety")
    
    # Timing information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # User and system info
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_backups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if backup failed")
    warnings = models.JSONField(default=list, help_text="List of warnings during backup")
    
    # Restoration info
    is_restorable = models.BooleanField(default=True, help_text="Whether this backup can be restored")
    restore_notes = models.TextField(blank=True, help_text="Notes about restoration process")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['backup_type', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.get_backup_type_display()}) - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-generate name if not provided
        if not self.name:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            self.name = f"Backup_{self.get_backup_type_display()}_{timestamp}"
        
        # Calculate duration if completed
        if self.status == 'completed' and self.started_at and self.completed_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        super().save(*args, **kwargs)
    
    @property
    def formatted_size(self):
        """Return human-readable backup size"""
        return self._format_bytes(self.backup_size)
    
    @property
    def formatted_compressed_size(self):
        """Return human-readable compressed size"""
        return self._format_bytes(self.compressed_size)
    
    @property
    def compression_ratio(self):
        """Calculate compression ratio as percentage"""
        if self.backup_size and self.compressed_size:
            return round((1 - self.compressed_size / self.backup_size) * 100, 1)
        return 0
    
    @property
    def duration_formatted(self):
        """Return formatted duration"""
        if self.duration_seconds:
            hours, remainder = divmod(self.duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "0s"
    
    @property
    def can_restore(self):
        """Check if backup can be restored"""
        return (self.status == 'completed' and 
                self.is_restorable and 
                self.backup_path and 
                os.path.exists(self.backup_path))
    
    def _format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        if not bytes_value:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def get_backup_files(self):
        """Get all files associated with this backup"""
        return self.backup_files.all().order_by('file_type', 'filename')
    
    def mark_as_started(self):
        """Mark backup as started"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def mark_as_completed(self):
        """Mark backup as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()
    
    def mark_as_failed(self, error_message=None):
        """Mark backup as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()


class BackupFile(models.Model):
    """Individual files within a backup"""
    
    FILE_TYPE_CHOICES = [
        ('database', 'Database Dump'),
        ('media', 'Media File'),
        ('static', 'Static File'),
        ('fixture', 'Django Fixture'),
        ('config', 'Configuration File'),
        ('log', 'Log File'),
    ]
    
    backup = models.ForeignKey(Backup, on_delete=models.CASCADE, related_name='backup_files')
    
    # File information
    filename = models.CharField(max_length=255)
    original_path = models.CharField(max_length=500, help_text="Original file path")
    backup_path = models.CharField(max_length=500, help_text="Path in backup")
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    
    # File metadata
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA-256 checksum")
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Database specific fields
    model_name = models.CharField(max_length=100, blank=True, help_text="Django model name for database files")
    app_label = models.CharField(max_length=100, blank=True, help_text="Django app label")
    record_count = models.IntegerField(default=0, help_text="Number of records for database dumps")
    
    # Backup metadata
    backed_up_at = models.DateTimeField(auto_now_add=True)
    is_encrypted = models.BooleanField(default=False)
    compression_used = models.BooleanField(default=False)
    
    # Status
    is_verified = models.BooleanField(default=False, help_text="Whether file integrity is verified")
    verification_error = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['backup', 'original_path']
        ordering = ['file_type', 'filename']
        
    def __str__(self):
        return f"{self.filename} ({self.get_file_type_display()})"
    
    @property
    def formatted_size(self):
        """Return human-readable file size"""
        return self._format_bytes(self.file_size)
    
    def _format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        if not bytes_value:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def verify_integrity(self):
        """Verify file integrity using checksum"""
        if not self.checksum or not os.path.exists(self.backup_path):
            return False
        
        import hashlib
        sha256_hash = hashlib.sha256()
        try:
            with open(self.backup_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            calculated_checksum = sha256_hash.hexdigest()
            is_valid = calculated_checksum == self.checksum
            self.is_verified = is_valid
            if not is_valid:
                self.verification_error = f"Checksum mismatch: expected {self.checksum}, got {calculated_checksum}"
            self.save()
            return is_valid
        except Exception as e:
            self.verification_error = str(e)
            self.is_verified = False
            self.save()
            return False


class BackupLog(models.Model):
    """Detailed logging for backup operations"""
    
    LOG_LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    backup = models.ForeignKey(Backup, on_delete=models.CASCADE, related_name='logs')
    
    # Log information
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES)
    message = models.TextField()
    operation = models.CharField(max_length=200, blank=True, help_text="Current operation being logged")
    
    # Context information
    step_number = models.IntegerField(default=0, help_text="Step number in backup process")
    total_steps = models.IntegerField(default=0, help_text="Total steps in backup process")
    
    # Additional data
    extra_data = models.JSONField(default=dict, help_text="Additional contextual data")
    exception_info = models.TextField(blank=True, help_text="Exception traceback if applicable")
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['backup', 'level']),
            models.Index(fields=['backup', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_level_display()}: {self.message[:100]}"


class BackupRestore(models.Model):
    """Track backup restore operations"""
    
    RESTORE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('partial', 'Partially Completed'),
    ]
    
    RESTORE_MODE_CHOICES = [
        ('full', 'Full Restore (Replace All Data)'),
        ('selective', 'Selective Restore'),
        ('merge', 'Merge with Existing Data'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    backup = models.ForeignKey(Backup, on_delete=models.CASCADE, related_name='restore_operations')
    
    # Restore configuration
    restore_mode = models.CharField(max_length=20, choices=RESTORE_MODE_CHOICES, default='full')
    restore_database = models.BooleanField(default=True)
    restore_media = models.BooleanField(default=True)
    restore_staticfiles = models.BooleanField(default=False)
    
    # Selective restore options
    selected_models = models.JSONField(default=list, help_text="List of models to restore")
    exclude_models = models.JSONField(default=list, help_text="List of models to exclude")
    
    # Status and progress
    status = models.CharField(max_length=20, choices=RESTORE_STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    current_operation = models.CharField(max_length=200, blank=True)
    
    # Statistics
    restored_files = models.IntegerField(default=0)
    restored_records = models.BigIntegerField(default=0)
    skipped_files = models.IntegerField(default=0)
    failed_files = models.IntegerField(default=0)
    
    # Backup information
    pre_restore_backup = models.ForeignKey(
        Backup, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pre_restore_for',
        help_text="Backup created before restore operation"
    )
    
    # Timing information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # User and system info
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='initiated_restores')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Results and errors
    error_message = models.TextField(blank=True)
    warnings = models.JSONField(default=list)
    restore_notes = models.TextField(blank=True)
    rollback_available = models.BooleanField(default=False, help_text="Whether rollback is possible")
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Restore of {self.backup.name} - {self.status}"
    
    @property
    def success_rate(self):
        """Calculate success rate of restore operation"""
        total_operations = self.restored_files + self.failed_files
        if total_operations > 0:
            return round((self.restored_files / total_operations) * 100, 1)
        return 0
    
    def mark_as_started(self):
        """Mark restore as started"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def mark_as_completed(self):
        """Mark restore as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.save()
    
    def mark_as_failed(self, error_message=None):
        """Mark restore as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()


class BackupSchedule(models.Model):
    """Automated backup scheduling"""
    
    FREQUENCY_CHOICES = [
        ('manual', 'Manual Only'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Cron'),
    ]
    
    # Schedule information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='manual')
    cron_expression = models.CharField(max_length=100, blank=True, help_text="Custom cron expression")
    
    # Backup configuration
    backup_type = models.CharField(max_length=20, choices=Backup.BACKUP_TYPE_CHOICES, default='full')
    include_media = models.BooleanField(default=True)
    include_staticfiles = models.BooleanField(default=False)
    compress_backup = models.BooleanField(default=True)
    
    # Retention policy
    max_backups_to_keep = models.IntegerField(default=10, help_text="Maximum number of backups to keep")
    delete_old_backups = models.BooleanField(default=True, help_text="Automatically delete old backups")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    last_backup = models.ForeignKey(Backup, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_by')
    
    # User and timing
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"
    
    def calculate_next_run(self):
        """Calculate the next run time based on frequency"""
        if self.frequency == 'manual' or not self.is_active:
            self.next_run = None
            return
        
        from datetime import timedelta
        now = timezone.now()
        
        if self.frequency == 'daily':
            self.next_run = now + timedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_run = now + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            self.next_run = now + timedelta(days=30)  # Approximate
        elif self.frequency == 'custom' and self.cron_expression:
            # This would require a cron parser library
            # For now, default to daily
            self.next_run = now + timedelta(days=1)
        
        self.save()


class BackupSettings(models.Model):
    """Global backup system settings"""
    
    # Storage settings
    backup_root_path = models.CharField(
        max_length=500, 
        default='backups_storage',
        help_text="Root directory for storing backups"
    )
    max_backup_size = models.BigIntegerField(
        default=10 * 1024 * 1024 * 1024,  # 10GB
        help_text="Maximum backup size in bytes"
    )
    
    # Retention settings
    default_retention_days = models.IntegerField(
        default=30,
        help_text="Default retention period in days"
    )
    auto_cleanup_enabled = models.BooleanField(
        default=True,
        help_text="Automatically cleanup old backups"
    )
    
    # Performance settings
    chunk_size = models.IntegerField(
        default=1024 * 1024,  # 1MB
        help_text="File processing chunk size in bytes"
    )
    max_concurrent_operations = models.IntegerField(
        default=3,
        help_text="Maximum concurrent backup/restore operations"
    )
    
    # Security settings
    encrypt_backups = models.BooleanField(
        default=False,
        help_text="Encrypt backup files"
    )
    encryption_key = models.CharField(
        max_length=500,
        blank=True,
        help_text="Encryption key (base64 encoded)"
    )
    
    # Notification settings
    email_notifications = models.BooleanField(
        default=True,
        help_text="Send email notifications for backup events"
    )
    notification_emails = models.TextField(
        blank=True,
        help_text="Comma-separated list of email addresses"
    )
    
    # Advanced settings
    verify_backup_integrity = models.BooleanField(
        default=True,
        help_text="Verify backup file integrity using checksums"
    )
    create_pre_restore_backup = models.BooleanField(
        default=True,
        help_text="Create backup before restore operations"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Backup Settings"
        verbose_name_plural = "Backup Settings"
        
    def __str__(self):
        return "Backup System Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        if not self.pk and BackupSettings.objects.exists():
            raise ValueError("Only one BackupSettings instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create backup settings instance"""
        settings, created = cls.objects.get_or_create(defaults={
            'backup_root_path': 'backups_storage',
            'max_backup_size': 10 * 1024 * 1024 * 1024,  # 10GB
            'default_retention_days': 30,
        })
        return settings