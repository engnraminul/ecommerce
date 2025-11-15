from rest_framework import serializers
from .models import BackupRecord, RestoreRecord, BackupSchedule, BackupSettings


class BackupRecordSerializer(serializers.ModelSerializer):
    """Serializer for backup records"""
    
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_size = serializers.CharField(read_only=True)
    formatted_database_size = serializers.CharField(read_only=True)
    formatted_media_size = serializers.CharField(read_only=True)
    duration = serializers.DurationField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    backup_files = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupRecord
        fields = [
            'id', 'name', 'backup_type', 'backup_type_display', 'status', 'status_display',
            'database_file', 'media_file', 'file_size', 'database_size', 'media_size',
            'formatted_size', 'formatted_database_size', 'formatted_media_size',
            'created_at', 'started_at', 'completed_at', 'duration', 'is_completed',
            'created_by', 'created_by_username', 'description', 'error_message',
            'compress', 'exclude_logs', 'backup_files'
        ]
        read_only_fields = [
            'id', 'status', 'database_file', 'media_file', 'file_size',
            'database_size', 'media_size', 'started_at', 'completed_at',
            'created_by', 'error_message'
        ]
    
    def get_backup_files(self, obj):
        """Get backup files information"""
        return obj.get_backup_files()


class RestoreRecordSerializer(serializers.ModelSerializer):
    """Serializer for restore records"""
    
    restore_type_display = serializers.CharField(source='get_restore_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.DurationField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    backup_record_name = serializers.CharField(source='backup_record.name', read_only=True)
    pre_restore_backup_name = serializers.CharField(source='pre_restore_backup.name', read_only=True)
    
    class Meta:
        model = RestoreRecord
        fields = [
            'id', 'name', 'backup_record', 'backup_record_name',
            'uploaded_database_file', 'uploaded_media_file',
            'restore_type', 'restore_type_display', 'status', 'status_display',
            'overwrite_existing', 'backup_before_restore',
            'created_at', 'started_at', 'completed_at', 'duration', 'is_completed',
            'created_by', 'created_by_username', 'description', 'error_message',
            'pre_restore_backup', 'pre_restore_backup_name'
        ]
        read_only_fields = [
            'id', 'status', 'started_at', 'completed_at',
            'created_by', 'error_message', 'pre_restore_backup'
        ]


class BackupScheduleSerializer(serializers.ModelSerializer):
    """Serializer for backup schedules"""
    
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    schedule_type_display = serializers.CharField(source='get_schedule_type_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BackupSchedule
        fields = [
            'id', 'name', 'backup_type', 'backup_type_display',
            'schedule_type', 'schedule_type_display',
            'hour', 'minute', 'day_of_week', 'day_of_month',
            'is_active', 'compress', 'exclude_logs', 'retention_days',
            'created_at', 'updated_at', 'created_by', 'created_by_username',
            'last_run', 'next_run'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'last_run', 'next_run'
        ]
    
    def validate(self, data):
        """Validate schedule configuration"""
        schedule_type = data.get('schedule_type')
        
        if schedule_type == 'weekly' and data.get('day_of_week') is None:
            raise serializers.ValidationError(
                "day_of_week is required for weekly schedules"
            )
        
        if schedule_type == 'monthly' and data.get('day_of_month') is None:
            raise serializers.ValidationError(
                "day_of_month is required for monthly schedules"
            )
        
        # Validate hour and minute ranges
        hour = data.get('hour', 0)
        minute = data.get('minute', 0)
        
        if not (0 <= hour <= 23):
            raise serializers.ValidationError("Hour must be between 0 and 23")
        
        if not (0 <= minute <= 59):
            raise serializers.ValidationError("Minute must be between 0 and 59")
        
        # Validate day_of_week
        day_of_week = data.get('day_of_week')
        if day_of_week is not None and not (0 <= day_of_week <= 6):
            raise serializers.ValidationError("day_of_week must be between 0 and 6")
        
        # Validate day_of_month
        day_of_month = data.get('day_of_month')
        if day_of_month is not None and not (1 <= day_of_month <= 31):
            raise serializers.ValidationError("day_of_month must be between 1 and 31")
        
        return data


class BackupSettingsSerializer(serializers.ModelSerializer):
    """Serializer for backup settings"""
    
    class Meta:
        model = BackupSettings
        fields = [
            'id', 'backup_directory', 'max_backup_size',
            'mysql_path', 'mysql_host', 'mysql_port', 'mysql_user', 'mysql_password', 'mysql_database',
            'compression_level', 'default_retention_days', 'auto_cleanup',
            'email_notifications', 'notification_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'mysql_password': {'write_only': True}  # Hide password in responses
        }
    
    def validate_compression_level(self, value):
        """Validate compression level"""
        if not (1 <= value <= 9):
            raise serializers.ValidationError("Compression level must be between 1 and 9")
        return value
    
    def validate_mysql_port(self, value):
        """Validate MySQL port"""
        if not (1 <= value <= 65535):
            raise serializers.ValidationError("Port must be between 1 and 65535")
        return value
    
    def validate_max_backup_size(self, value):
        """Validate max backup size"""
        if value < 0:
            raise serializers.ValidationError("Max backup size cannot be negative")
        return value
    
    def validate_default_retention_days(self, value):
        """Validate retention days"""
        if value < 0:
            raise serializers.ValidationError("Retention days cannot be negative")
        return value


class BackupFileUploadSerializer(serializers.Serializer):
    """Serializer for backup file uploads"""
    
    name = serializers.CharField(max_length=255)
    restore_type = serializers.ChoiceField(
        choices=[('database', 'Database Only'), ('media', 'Media Files Only'), ('full', 'Database + Media Files')]
    )
    database_file = serializers.FileField(required=False, allow_null=True)
    media_file = serializers.FileField(required=False, allow_null=True)
    overwrite_existing = serializers.BooleanField(default=False)
    backup_before_restore = serializers.BooleanField(default=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate upload data"""
        restore_type = data.get('restore_type')
        database_file = data.get('database_file')
        media_file = data.get('media_file')
        
        if restore_type == 'database' and not database_file:
            raise serializers.ValidationError(
                "Database file is required for database restore"
            )
        
        if restore_type == 'media' and not media_file:
            raise serializers.ValidationError(
                "Media file is required for media restore"
            )
        
        if restore_type == 'full' and not (database_file or media_file):
            raise serializers.ValidationError(
                "At least one file is required for full restore"
            )
        
        return data


class BackupStatisticsSerializer(serializers.Serializer):
    """Serializer for backup statistics"""
    
    total_backups = serializers.IntegerField()
    completed_backups = serializers.IntegerField()
    failed_backups = serializers.IntegerField()
    in_progress_backups = serializers.IntegerField()
    success_rate = serializers.FloatField()
    backup_types = serializers.DictField()
    recent_backups = serializers.IntegerField()
    total_size = serializers.IntegerField()
    total_size_formatted = serializers.CharField()