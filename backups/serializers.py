from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Backup, BackupSchedule, RestoreLog

User = get_user_model()


class BackupSerializer(serializers.ModelSerializer):
    formatted_size = serializers.ReadOnlyField()
    can_restore = serializers.ReadOnlyField()
    can_download = serializers.ReadOnlyField()
    download_files = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Backup
        fields = [
            'id', 'name', 'backup_type', 'status', 'database_file', 'media_file',
            'created_at', 'completed_at', 'created_by', 'created_by_name',
            'database_size', 'media_size', 'total_size', 'formatted_size',
            'file_count', 'compression_level', 'error_message',
            'last_restored_at', 'restoration_count',
            'can_restore', 'can_download', 'download_files'
        ]
        read_only_fields = [
            'id', 'status', 'database_file', 'media_file', 'created_at', 
            'completed_at', 'database_size', 'media_size', 'total_size',
            'file_count', 'error_message', 'last_restored_at', 'restoration_count'
        ]
    
    def get_download_files(self, obj):
        return obj.get_download_files()
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return "System"


class CreateBackupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    backup_type = serializers.ChoiceField(
        choices=Backup.BACKUP_TYPE_CHOICES,
        default='full'
    )
    
    def validate_name(self, value):
        if value and Backup.objects.filter(name=value).exists():
            raise serializers.ValidationError("Backup with this name already exists.")
        return value


class RestoreBackupSerializer(serializers.Serializer):
    backup_id = serializers.IntegerField()
    restore_type = serializers.ChoiceField(
        choices=Backup.BACKUP_TYPE_CHOICES,
        required=False
    )
    validate_only = serializers.BooleanField(default=False)
    
    def validate_backup_id(self, value):
        try:
            backup = Backup.objects.get(id=value)
            if not backup.can_restore:
                raise serializers.ValidationError("Backup cannot be restored.")
            return value
        except Backup.DoesNotExist:
            raise serializers.ValidationError("Backup not found.")


class UploadBackupSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255, required=False)
    backup_type = serializers.ChoiceField(choices=Backup.BACKUP_TYPE_CHOICES)
    
    def validate_file(self, value):
        # Validate file size
        max_size = 5 * 1024 * 1024 * 1024  # 5GB
        if value.size > max_size:
            raise serializers.ValidationError("File too large. Maximum size is 5GB.")
        
        return value
    
    def validate_name(self, value):
        if value and Backup.objects.filter(name=value).exists():
            raise serializers.ValidationError("Backup with this name already exists.")
        return value


class BackupScheduleSerializer(serializers.ModelSerializer):
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    
    class Meta:
        model = BackupSchedule
        fields = [
            'id', 'name', 'backup_type', 'backup_type_display',
            'frequency', 'frequency_display', 'is_active',
            'hour', 'minute', 'day_of_week', 'day_of_month',
            'retention_days', 'max_backups',
            'created_at', 'updated_at', 'last_run'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_run']
    
    def validate(self, attrs):
        frequency = attrs.get('frequency')
        
        if frequency == 'weekly' and attrs.get('day_of_week') is None:
            raise serializers.ValidationError({
                'day_of_week': 'Required for weekly backups.'
            })
        
        if frequency == 'monthly' and attrs.get('day_of_month') is None:
            raise serializers.ValidationError({
                'day_of_month': 'Required for monthly backups.'
            })
        
        return attrs


class RestoreLogSerializer(serializers.ModelSerializer):
    backup_name = serializers.CharField(source='backup.name', read_only=True)
    restored_by_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = RestoreLog
        fields = [
            'id', 'backup', 'backup_name', 'restored_by', 'restored_by_name',
            'restore_type', 'started_at', 'completed_at', 'duration',
            'success', 'error_message', 'validation_passed', 'validation_notes'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at', 'success', 'error_message',
            'validation_passed', 'validation_notes'
        ]
    
    def get_restored_by_name(self, obj):
        if obj.restored_by:
            return f"{obj.restored_by.first_name} {obj.restored_by.last_name}".strip() or obj.restored_by.email
        return "System"
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration)
        return None


class BackupStatsSerializer(serializers.Serializer):
    total_backups = serializers.IntegerField()
    completed_backups = serializers.IntegerField()
    failed_backups = serializers.IntegerField()
    total_size = serializers.IntegerField()
    formatted_total_size = serializers.CharField()
    latest_backup = BackupSerializer(read_only=True, allow_null=True)
    recent_backups = BackupSerializer(many=True, read_only=True)
    backup_types_count = serializers.DictField()


class BackupListSerializer(serializers.ModelSerializer):
    """Simplified serializer for backup list views"""
    formatted_size = serializers.ReadOnlyField()
    can_restore = serializers.ReadOnlyField()
    can_download = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    status_badge = serializers.SerializerMethodField()
    
    class Meta:
        model = Backup
        fields = [
            'id', 'name', 'backup_type', 'status', 'status_badge',
            'created_at', 'completed_at', 'created_by_name',
            'total_size', 'formatted_size', 'restoration_count',
            'can_restore', 'can_download'
        ]
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return "System"
    
    def get_status_badge(self, obj):
        status_colors = {
            'pending': 'warning',
            'creating': 'info',
            'completed': 'success',
            'failed': 'danger',
            'restoring': 'info',
            'restored': 'secondary'
        }
        return {
            'text': obj.get_status_display(),
            'color': status_colors.get(obj.status, 'secondary')
        }