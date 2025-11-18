from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Backup, BackupSchedule, RestoreLog
from .serializers import (
    BackupSerializer, BackupListSerializer, CreateBackupSerializer,
    RestoreBackupSerializer, UploadBackupSerializer, BackupScheduleSerializer,
    RestoreLogSerializer, BackupStatsSerializer
)
from .services import BackupService, RestoreService, BackupUploadService

import os
import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing backups"""
    queryset = Backup.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BackupListSerializer
        elif self.action == 'create_backup':
            return CreateBackupSerializer
        elif self.action == 'restore':
            return RestoreBackupSerializer
        elif self.action == 'upload':
            return UploadBackupSerializer
        return BackupSerializer
    
    def get_queryset(self):
        queryset = Backup.objects.all()
        
        # Filter by backup type
        backup_type = self.request.query_params.get('backup_type')
        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy method to provide better logging for backup deletion"""
        backup = self.get_object()
        backup_name = backup.name
        backup_id = backup.id
        
        try:
            # Log the deletion attempt
            logger.info(f"User {request.user} is deleting backup '{backup_name}' (ID: {backup_id})")
            
            # Perform the deletion (files will be automatically deleted via signals)
            self.perform_destroy(backup)
            
            logger.info(f"Successfully deleted backup '{backup_name}' (ID: {backup_id})")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Failed to delete backup '{backup_name}' (ID: {backup_id}): {str(e)}")
            return Response(
                {'error': f'Failed to delete backup: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """Create a new backup"""
        serializer = CreateBackupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                backup_service = BackupService()
                backup = backup_service.create_backup(
                    backup_type=serializer.validated_data['backup_type'],
                    name=serializer.validated_data.get('name'),
                    user=request.user
                )
                
                response_serializer = BackupSerializer(backup)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Backup creation failed: {str(e)}")
                return Response(
                    {'error': f'Backup creation failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a backup"""
        backup = self.get_object()
        
        # Create a modified data dict with backup_id included
        data = request.data.copy()
        data['backup_id'] = backup.id
        
        # Handle empty restore_type (should use backup's type)
        if not data.get('restore_type'):
            data['restore_type'] = backup.backup_type
        
        serializer = RestoreBackupSerializer(data=data)
        
        if serializer.is_valid():
            try:
                restore_service = RestoreService()
                restore_log = restore_service.restore_backup(
                    backup=backup,
                    restore_type=serializer.validated_data.get('restore_type'),
                    user=request.user,
                    validate_only=serializer.validated_data.get('validate_only', False)
                )
                
                response_serializer = RestoreLogSerializer(restore_log)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Restore failed: {str(e)}")
                return Response(
                    {'error': f'Restore failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download backup files"""
        backup = self.get_object()
        
        if not backup.can_download:
            return Response(
                {'error': 'Backup cannot be downloaded'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get file type from query params
        file_type = request.query_params.get('type', 'all')
        
        if file_type == 'database' and backup.database_file:
            return self._serve_file(backup.database_file)
        elif file_type == 'media' and backup.media_file:
            return self._serve_file(backup.media_file)
        elif file_type == 'all':
            # Create a combined download (zip both files)
            return self._serve_combined_backup(backup)
        else:
            return Response(
                {'error': 'Invalid file type or file not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _serve_file(self, file_path):
        """Serve a file for download"""
        if not os.path.exists(file_path):
            return Response(
                {'error': 'File not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
    
    def _serve_combined_backup(self, backup):
        """Create and serve a combined backup file"""
        import tempfile
        import zipfile
        
        # Create temporary zip file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        try:
            with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if backup.database_file and os.path.exists(backup.database_file):
                    zipf.write(backup.database_file, f"database/{os.path.basename(backup.database_file)}")
                
                if backup.media_file and os.path.exists(backup.media_file):
                    zipf.write(backup.media_file, f"media/{os.path.basename(backup.media_file)}")
            
            response = FileResponse(
                open(temp_file.name, 'rb'),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="{backup.name}_complete.zip"'
            
            # Clean up temp file after response (in a real app, you'd want to do this asynchronously)
            # os.unlink(temp_file.name)
            
            return response
            
        except Exception as e:
            os.unlink(temp_file.name)
            return Response(
                {'error': f'Failed to create combined backup: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """Upload and process backup file"""
        serializer = UploadBackupSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                upload_service = BackupUploadService()
                backup = upload_service.handle_uploaded_backup(
                    uploaded_file=serializer.validated_data['file'],
                    backup_type=serializer.validated_data['backup_type'],
                    name=serializer.validated_data.get('name'),
                    user=request.user
                )
                
                response_serializer = BackupSerializer(backup)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Backup upload failed: {str(e)}")
                return Response(
                    {'error': f'Backup upload failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get backup statistics"""
        stats = {
            'total_backups': Backup.objects.count(),
            'completed_backups': Backup.objects.filter(status='completed').count(),
            'failed_backups': Backup.objects.filter(status='failed').count(),
            'total_size': Backup.objects.aggregate(
                total=Sum('total_size')
            )['total'] or 0,
        }
        
        # Format total size
        total_size = stats['total_size']
        if total_size == 0:
            stats['formatted_total_size'] = "0 B"
        else:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if total_size < 1024.0:
                    stats['formatted_total_size'] = f"{total_size:.1f} {unit}"
                    break
                total_size /= 1024.0
        
        # Latest backup
        stats['latest_backup'] = None
        latest = Backup.objects.filter(status='completed').first()
        if latest:
            stats['latest_backup'] = BackupSerializer(latest).data
        
        # Recent backups (last 5)
        recent = Backup.objects.filter(status='completed')[:5]
        stats['recent_backups'] = BackupSerializer(recent, many=True).data
        
        # Backup types count
        stats['backup_types_count'] = dict(
            Backup.objects.values('backup_type').annotate(count=Count('id'))
            .values_list('backup_type', 'count')
        )
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """Clean up old backups"""
        retention_days = request.data.get('retention_days', 30)
        
        try:
            backup_service = BackupService()
            deleted_count = backup_service.cleanup_old_backups(retention_days)
            
            return Response({
                'message': f'Cleaned up {deleted_count} old backups',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return Response(
                {'error': f'Cleanup failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BackupScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing backup schedules"""
    queryset = BackupSchedule.objects.all()
    serializer_class = BackupScheduleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class RestoreLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing restore logs"""
    queryset = RestoreLog.objects.all()
    serializer_class = RestoreLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = RestoreLog.objects.all()
        
        # Filter by backup
        backup_id = self.request.query_params.get('backup_id')
        if backup_id:
            queryset = queryset.filter(backup_id=backup_id)
        
        # Filter by success status
        success = self.request.query_params.get('success')
        if success is not None:
            queryset = queryset.filter(success=success.lower() == 'true')
        
        return queryset.order_by('-started_at')


# Dashboard views for template rendering
@login_required
def backup_dashboard(request):
    """Dashboard view for backup management"""
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access denied. Admin privileges required.")
    
    context = {
        'page_title': 'Backup Management',
        'active_tab': 'backups'
    }
    return render(request, 'backups/dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def backup_system_info(request):
    """Get backup system information and status"""
    try:
        # Check backup directory
        backup_dir = Path(settings.BASE_DIR) / getattr(settings, 'BACKUP_DIRECTORY', 'backups')
        backup_dir_exists = backup_dir.exists()
        backup_dir_writable = backup_dir_exists and os.access(backup_dir, os.W_OK)
        
        # Check MySQL tools
        mysql_available = True
        mysqldump_available = True
        try:
            import subprocess
            subprocess.run(['mysql', '--version'], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            mysql_available = False
        
        try:
            import subprocess
            subprocess.run(['mysqldump', '--version'], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            mysqldump_available = False
        
        # Database connection
        db_connection = True
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_connection = False
        
        # Media directory
        media_dir = Path(settings.MEDIA_ROOT)
        media_dir_exists = media_dir.exists()
        media_dir_size = 0
        if media_dir_exists:
            try:
                media_dir_size = sum(f.stat().st_size for f in media_dir.rglob('*') if f.is_file())
            except Exception:
                pass
        
        info = {
            'backup_directory': {
                'path': str(backup_dir),
                'exists': backup_dir_exists,
                'writable': backup_dir_writable
            },
            'database': {
                'connection': db_connection,
                'mysql_available': mysql_available,
                'mysqldump_available': mysqldump_available,
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME']
            },
            'media': {
                'path': str(media_dir),
                'exists': media_dir_exists,
                'size': media_dir_size
            },
            'settings': {
                'retention_days': getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
                'compression_level': getattr(settings, 'BACKUP_COMPRESSION_LEVEL', 6),
                'auto_cleanup': getattr(settings, 'BACKUP_AUTO_CLEANUP', True)
            }
        }
        
        return Response(info)
        
    except Exception as e:
        logger.error(f"System info check failed: {str(e)}")
        return Response(
            {'error': f'System info check failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
