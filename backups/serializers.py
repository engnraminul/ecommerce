from rest_framework import serializers
from .models import (
    Backup, BackupFile, BackupLog, BackupRestore, 
    BackupSchedule, BackupSettings
)


class BackupFileSerializer(serializers.ModelSerializer):
    """Serializer for backup files"""
    formatted_size = serializers.ReadOnlyField()
    
    class Meta:
        model = BackupFile
        fields = [
            'id', 'filename', 'original_path', 'file_type',
            'file_size', 'formatted_size', 'checksum',
            'model_name', 'app_label', 'record_count',
            'is_verified', 'verification_error', 'backed_up_at'
        ]
        read_only_fields = fields


class BackupLogSerializer(serializers.ModelSerializer):
    """Serializer for backup logs"""
    
    class Meta:
        model = BackupLog
        fields = [
            'id', 'level', 'message', 'operation', 'step_number',
            'total_steps', 'extra_data', 'exception_info', 'created_at'
        ]
        read_only_fields = fields


class BackupSerializer(serializers.ModelSerializer):
    """Serializer for backups with nested files and logs"""
    backup_files = BackupFileSerializer(many=True, read_only=True)
    logs = BackupLogSerializer(many=True, read_only=True)
    formatted_size = serializers.ReadOnlyField()
    formatted_compressed_size = serializers.ReadOnlyField()
    duration_formatted = serializers.ReadOnlyField()
    compression_ratio = serializers.ReadOnlyField()
    can_restore = serializers.ReadOnlyField()
    
    class Meta:
        model = Backup
        fields = [
            'id', 'name', 'description', 'backup_type', 'status',
            'include_media', 'include_staticfiles', 'compress_backup',
            'progress_percentage', 'current_operation',
            'backup_path', 'backup_size', 'compressed_size',
            'formatted_size', 'formatted_compressed_size', 'compression_ratio',
            'total_files', 'total_tables', 'total_records',
            'preserve_foreign_keys', 'backup_order',
            'started_at', 'completed_at', 'duration_seconds', 'duration_formatted',
            'django_version', 'python_version', 'database_name',
            'is_restorable', 'can_restore', 'error_message', 'warnings',
            'created_by', 'created_at', 'updated_at',
            'backup_files', 'logs'
        ]
        read_only_fields = [
            'id', 'status', 'progress_percentage', 'current_operation',
            'backup_path', 'backup_size', 'compressed_size',
            'total_files', 'total_tables', 'total_records',
            'backup_order', 'started_at', 'completed_at', 'duration_seconds',
            'django_version', 'python_version', 'database_name',
            'error_message', 'warnings', 'created_at', 'updated_at'
        ]


class BackupListSerializer(serializers.ModelSerializer):
    """Simplified serializer for backup list view"""
    formatted_size = serializers.ReadOnlyField()
    duration_formatted = serializers.ReadOnlyField()
    can_restore = serializers.ReadOnlyField()
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Backup
        fields = [
            'id', 'name', 'description', 'backup_type', 'status',
            'formatted_size', 'duration_formatted', 'total_files',
            'total_records', 'can_restore', 'file_count',
            'created_at', 'updated_at'
        ]
    
    def get_file_count(self, obj):
        return obj.backup_files.count()


class BackupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new backups"""
    
    class Meta:
        model = Backup
        fields = [
            'name', 'description', 'backup_type',
            'include_media', 'include_staticfiles', 'compress_backup'
        ]
    
    def create(self, validated_data):
        # Add user info
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class BackupRestoreSerializer(serializers.ModelSerializer):
    """Serializer for backup restore operations"""
    backup_name = serializers.CharField(source='backup.name', read_only=True)
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = BackupRestore
        fields = [
            'id', 'backup', 'backup_name', 'restore_mode',
            'restore_database', 'restore_media',
            'selected_models', 'exclude_models',
            'status', 'progress_percentage', 'current_operation',
            'restored_files', 'restored_records', 'skipped_files', 'failed_files',
            'success_rate', 'pre_restore_backup',
            'started_at', 'completed_at', 'duration_seconds',
            'error_message', 'warnings', 'restore_notes',
            'rollback_available', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'progress_percentage', 'current_operation',
            'restored_files', 'restored_records', 'skipped_files', 'failed_files',
            'pre_restore_backup', 'started_at', 'completed_at', 'duration_seconds',
            'error_message', 'warnings', 'rollback_available',
            'created_at', 'updated_at'
        ]


class BackupRestoreCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating restore operations"""
    
    class Meta:
        model = BackupRestore
        fields = [
            'backup', 'restore_mode', 'restore_database', 'restore_media',
            'selected_models', 'exclude_models'
        ]
    
    def create(self, validated_data):
        # Add user info
        request = self.context.get('request')
        if request and request.user:
            validated_data['initiated_by'] = request.user
        
        return super().create(validated_data)


class BackupScheduleSerializer(serializers.ModelSerializer):
    """Serializer for backup schedules"""
    last_backup_name = serializers.CharField(source='last_backup.name', read_only=True)
    
    class Meta:
        model = BackupSchedule
        fields = [
            'id', 'name', 'description', 'frequency', 'cron_expression',
            'backup_type', 'include_media', 'include_staticfiles', 'compress_backup',
            'max_backups_to_keep', 'delete_old_backups',
            'is_active', 'last_run', 'next_run', 'last_backup', 'last_backup_name',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_run', 'next_run', 'last_backup', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        # Add user info
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        # Calculate next run
        schedule = super().create(validated_data)
        schedule.calculate_next_run()
        return schedule
    
    def update(self, instance, validated_data):
        schedule = super().update(instance, validated_data)
        schedule.calculate_next_run()
        return schedule


class BackupSettingsSerializer(serializers.ModelSerializer):
    """Serializer for backup settings"""
    
    class Meta:
        model = BackupSettings
        fields = [
            'id', 'backup_root_path', 'max_backup_size',
            'default_retention_days', 'auto_cleanup_enabled',
            'chunk_size', 'max_concurrent_operations',
            'encrypt_backups', 'encryption_key',
            'email_notifications', 'notification_emails',
            'verify_backup_integrity', 'create_pre_restore_backup',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'encryption_key': {'write_only': True}
        }


class BackupStatsSerializer(serializers.Serializer):
    """Serializer for backup statistics"""
    total_backups = serializers.IntegerField()
    completed_backups = serializers.IntegerField()
    failed_backups = serializers.IntegerField()
    in_progress_backups = serializers.IntegerField()
    total_storage_used = serializers.CharField()
    total_records_backed_up = serializers.IntegerField()
    total_files_backed_up = serializers.IntegerField()
    average_backup_size = serializers.CharField()
    last_backup_date = serializers.DateTimeField()
    next_scheduled_backup = serializers.DateTimeField()


class ModelInfoSerializer(serializers.Serializer):
    """Serializer for Django model information"""
    app_label = serializers.CharField()
    model_name = serializers.CharField()
    verbose_name = serializers.CharField()
    full_name = serializers.CharField()
    record_count = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.CharField())