from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import os
import json
import threading
from datetime import datetime

from .models import (
    BackupRecord, RestoreRecord, BackupSchedule, BackupSettings,
    BackupType, BackupStatus, RestoreStatus
)
from .services import BackupService, RestoreService, BackupCleanupService
from .serializers import (
    BackupRecordSerializer, RestoreRecordSerializer,
    BackupScheduleSerializer, BackupSettingsSerializer
)


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_superuser)
def backup_dashboard(request):
    """Main backup management dashboard"""
    context = {
        'active_page': 'backup',
        'recent_backups': BackupRecord.objects.all()[:5],
        'recent_restores': RestoreRecord.objects.all()[:5],
        'backup_stats': {
            'total_backups': BackupRecord.objects.count(),
            'completed_backups': BackupRecord.objects.filter(status=BackupStatus.COMPLETED).count(),
            'failed_backups': BackupRecord.objects.filter(status=BackupStatus.FAILED).count(),
            'total_restores': RestoreRecord.objects.count(),
        }
    }
    return render(request, 'backup/dashboard.html', context)


class BackupRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for backup records management"""
    queryset = BackupRecord.objects.all()
    serializer_class = BackupRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by backup type
        type_filter = self.request.query_params.get('type', None)
        if type_filter:
            queryset = queryset.filter(backup_type=type_filter)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        backup_record = serializer.save(created_by=self.request.user)
        
        # Start backup process in background
        def create_backup():
            backup_service = BackupService()
            backup_service.create_backup(backup_record)
        
        backup_thread = threading.Thread(target=create_backup)
        backup_thread.daemon = True
        backup_thread.start()
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Download backup files"""
        backup = self.get_object()
        file_type = request.data.get('file_type', 'database')
        
        if file_type == 'database' and backup.database_file:
            if os.path.exists(backup.database_file):
                return FileResponse(
                    open(backup.database_file, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(backup.database_file)
                )
        elif file_type == 'media' and backup.media_file:
            if os.path.exists(backup.media_file):
                return FileResponse(
                    open(backup.media_file, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(backup.media_file)
                )
        
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'])
    def delete_files(self, request, pk=None):
        """Delete backup files"""
        backup = self.get_object()
        try:
            deleted_files = backup.delete_backup_files()
            return Response({
                'message': 'Backup files deleted successfully',
                'deleted_files': deleted_files
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete backup record and associated files"""
        backup = self.get_object()
        try:
            backup.delete_backup_files()
            backup.delete()
            return Response({'message': 'Backup deleted successfully'})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class RestoreRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for restore records management"""
    queryset = RestoreRecord.objects.all()
    serializer_class = RestoreRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        restore_record = serializer.save(created_by=self.request.user)
        
        # Start restore process in background
        def perform_restore():
            restore_service = RestoreService()
            restore_service.restore_from_backup(restore_record)
        
        restore_thread = threading.Thread(target=perform_restore)
        restore_thread.daemon = True
        restore_thread.start()
    
    @action(detail=False, methods=['post'])
    def upload_and_restore(self, request):
        """Upload backup files and restore"""
        name = request.data.get('name', f'Upload Restore {datetime.now().strftime("%Y%m%d_%H%M%S")}')
        restore_type = request.data.get('restore_type', BackupType.FULL_BACKUP)
        
        restore_record = RestoreRecord.objects.create(
            name=name,
            restore_type=restore_type,
            created_by=request.user,
            uploaded_database_file=request.FILES.get('database_file'),
            uploaded_media_file=request.FILES.get('media_file'),
            overwrite_existing=request.data.get('overwrite_existing', False),
            backup_before_restore=request.data.get('backup_before_restore', True)
        )
        
        # Start restore process
        def perform_restore():
            restore_service = RestoreService()
            restore_service.restore_from_backup(restore_record)
        
        restore_thread = threading.Thread(target=perform_restore)
        restore_thread.daemon = True
        restore_thread.start()
        
        serializer = self.get_serializer(restore_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BackupScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for backup schedule management"""
    queryset = BackupSchedule.objects.all()
    serializer_class = BackupScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle schedule active status"""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save()
        
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)


class BackupSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for backup settings management"""
    queryset = BackupSettings.objects.all()
    serializer_class = BackupSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Always return the singleton settings object"""
        return BackupSettings.get_settings()
    
    def list(self, request):
        """Return single settings object as list"""
        settings_obj = self.get_object()
        serializer = self.get_serializer(settings_obj)
        return Response([serializer.data])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def backup_statistics(request):
    """Get backup statistics"""
    total_backups = BackupRecord.objects.count()
    completed_backups = BackupRecord.objects.filter(status=BackupStatus.COMPLETED).count()
    failed_backups = BackupRecord.objects.filter(status=BackupStatus.FAILED).count()
    in_progress_backups = BackupRecord.objects.filter(status=BackupStatus.IN_PROGRESS).count()
    
    # Backup types distribution
    backup_types = {}
    for choice in BackupType.choices:
        backup_types[choice[1]] = BackupRecord.objects.filter(backup_type=choice[0]).count()
    
    # Recent activity (last 7 days)
    from datetime import timedelta
    last_week = timezone.now() - timedelta(days=7)
    recent_backups = BackupRecord.objects.filter(created_at__gte=last_week).count()
    
    # Calculate total backup size
    total_size = sum(
        backup.file_size for backup in BackupRecord.objects.filter(
            status=BackupStatus.COMPLETED
        )
    )
    
    return Response({
        'total_backups': total_backups,
        'completed_backups': completed_backups,
        'failed_backups': failed_backups,
        'in_progress_backups': in_progress_backups,
        'success_rate': (completed_backups / total_backups * 100) if total_backups > 0 else 0,
        'backup_types': backup_types,
        'recent_backups': recent_backups,
        'total_size': total_size,
        'total_size_formatted': BackupRecord()._format_bytes(total_size),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_old_backups(request):
    """Manually trigger cleanup of old backups"""
    cleanup_service = BackupCleanupService()
    deleted_count = cleanup_service.cleanup_old_backups()
    
    return Response({
        'message': f'Cleanup completed: {deleted_count} backups deleted',
        'deleted_count': deleted_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_backups(request):
    """Get list of available backups for restore"""
    backups = BackupRecord.objects.filter(
        status=BackupStatus.COMPLETED
    ).order_by('-created_at')
    
    backup_list = []
    for backup in backups:
        has_database = bool(backup.database_file and os.path.exists(backup.database_file))
        has_media = bool(backup.media_file and os.path.exists(backup.media_file))
        
        # Only include backups that have at least one valid file
        if has_database or has_media:
            backup_data = {
                'id': backup.id,
                'name': backup.name,
                'backup_type': backup.backup_type,
                'backup_type_display': backup.get_backup_type_display(),
                'created_at': backup.created_at,
                'file_size': backup.file_size,
                'file_size_formatted': backup.formatted_size,
                'has_database': has_database,
                'has_media': has_media,
            }
            backup_list.append(backup_data)
    
    return Response(backup_list)


@login_required
@require_POST
def test_backup_settings(request):
    """Test backup configuration"""
    try:
        settings = BackupSettings.get_settings()
        
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test backup directory
        backup_dir = os.path.join(settings.backup_directory)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        # Test mysqldump availability
        import subprocess
        try:
            subprocess.run([settings.mysql_path, '--version'], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return JsonResponse({
                'success': False,
                'message': 'mysqldump not found or not accessible'
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Backup configuration test successful'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def download_backup_file(request, backup_id, file_type):
    """Download backup file"""
    backup = get_object_or_404(BackupRecord, id=backup_id)
    
    file_path = None
    if file_type == 'database' and backup.database_file:
        file_path = backup.database_file
    elif file_type == 'media' and backup.media_file:
        file_path = backup.media_file
    
    if not file_path or not os.path.exists(file_path):
        raise Http404("File not found")
    
    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(file_path)
    )