from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.core.management import call_command
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.apps import apps
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from io import StringIO
import threading
import json
import logging
import os
import shutil

from .models import (
    Backup, BackupFile, BackupLog, BackupRestore, 
    BackupSchedule, BackupSettings
)
from .serializers import (
    BackupSerializer, BackupListSerializer, BackupCreateSerializer,
    BackupRestoreSerializer, BackupRestoreCreateSerializer,
    BackupScheduleSerializer, BackupSettingsSerializer,
    BackupStatsSerializer, ModelInfoSerializer
)
from .utils import backup_utils
from .full_backup_utils import FullBackupUtilities

logger = logging.getLogger(__name__)


class IsStaffUser(permissions.BasePermission):
    """Custom permission for staff users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class BackupViewSet(viewsets.ModelViewSet):
    """ViewSet for backup management"""
    queryset = Backup.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'backup_type', 'include_media', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'backup_size', 'duration_seconds']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BackupListSerializer
        elif self.action == 'create':
            return BackupCreateSerializer
        return BackupSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new backup and start the backup process"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        backup_data = serializer.validated_data
        
        # Start backup process in background thread
        def run_backup():
            try:
                kwargs = {
                    'type': backup_data.get('backup_type', 'full'),
                    'quiet': True
                }
                
                if backup_data.get('name'):
                    kwargs['name'] = backup_data['name']
                if backup_data.get('description'):
                    kwargs['description'] = backup_data['description']
                if not backup_data.get('include_media', True):
                    kwargs['no_media'] = True
                if not backup_data.get('compress_backup', True):
                    kwargs['no_compress'] = True
                if backup_data.get('include_staticfiles', False):
                    kwargs['include_static'] = True
                
                call_command('create_backup_safe', **kwargs)
                
            except Exception as e:
                logger.error(f"Backup creation failed: {str(e)}")
        
        thread = threading.Thread(target=run_backup)
        thread.daemon = True
        thread.start()
        
        return Response({
            'message': 'Backup creation started successfully',
            'status': 'started'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Start restore operation for a backup"""
        backup = self.get_object()
        
        if not backup.can_restore:
            return Response(
                {'error': 'Backup cannot be restored'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create restore instance
        restore_data = {
            'backup': backup.id,
            'restore_mode': request.data.get('restore_mode', 'full'),
            'restore_database': request.data.get('restore_database', True),
            'restore_media': request.data.get('restore_media', True),
            'selected_models': request.data.get('selected_models', []),
            'exclude_models': request.data.get('exclude_models', []),
        }
        
        serializer = BackupRestoreCreateSerializer(data=restore_data, context={'request': request})
        
        if serializer.is_valid():
            restore = serializer.save()
            
            # Start restore process in background
            def run_restore():
                import time
                try:
                    # Mark as started
                    restore.mark_as_started()
                    restore.current_operation = "Preparing restore..."
                    restore.save()
                    
                    # Execute real restore process (quick mode for speed)
                    args = [str(backup.id)]
                    kwargs = {
                        'force': True,  # Skip confirmation
                        'quiet': True,
                        'no_verify': True,  # Skip verification to avoid failures
                        'no_pre_backup': True,  # Skip pre-backup for now
                        'quick': True  # Use quick restore mode for speed
                    }
                    
                    # Handle backup type restrictions
                    if backup.backup_type == 'database':
                        kwargs['no_media'] = True  # Database-only backups can't restore media
                    elif backup.backup_type == 'media':
                        kwargs['no_database'] = True  # Media-only backups can't restore database
                    
                    # Apply user preferences and restore options
                    if restore.restore_mode:
                        kwargs['mode'] = restore.restore_mode
                    if not restore.restore_database:
                        kwargs['no_database'] = True
                    if not restore.restore_media:
                        kwargs['no_media'] = True
                    if restore.selected_models:
                        kwargs['models'] = ','.join(restore.selected_models)
                    if restore.exclude_models:
                        kwargs['exclude_models'] = ','.join(restore.exclude_models)
                    
                    # Set initial progress
                    restore.current_operation = "Starting restore process..."
                    restore.progress_percentage = 10
                    restore.save()
                    
                    # Call the real restore command
                    call_command('restore_backup_safe', *args, **kwargs)
                    
                    # Mark as completed if successful
                    restore.mark_as_completed()
                
                except Exception as e:
                    restore.mark_as_failed(str(e))
                    logger.error(f"Restore {restore.id} failed: {str(e)}")
            
            thread = threading.Thread(target=run_restore)
            thread.daemon = True
            thread.start()
            
            # Return response with restore ID for frontend monitoring
            response_data = BackupRestoreSerializer(restore).data
            response_data['success'] = True
            response_data['restore_id'] = str(restore.id)
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify backup integrity"""
        backup = self.get_object()
        
        try:
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
                # Mark all files as verified
                backup.backup_files.update(is_verified=True)
                
                return Response({
                    'success': True,
                    'message': f'Backup verification passed: {verify_results["verified_files"]} files verified',
                    'verified_files': verify_results['verified_files']
                })
            else:
                return Response({
                    'success': False,
                    'message': f'Backup verification failed: {verify_results["failed_files"]} files failed',
                    'errors': verify_results['errors']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Verification failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download backup file"""
        from django.http import FileResponse, Http404
        from django.utils.encoding import smart_str
        import os
        
        backup = self.get_object()
        
        if not backup.backup_path or not os.path.exists(backup.backup_path):
            return Response(
                {'error': 'Backup file is not available for download'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Determine filename
            if backup.compress_backup:
                filename = f"{backup.name}_{backup.created_at.strftime('%Y%m%d_%H%M%S')}.tar.gz"
            else:
                filename = f"{backup.name}_{backup.created_at.strftime('%Y%m%d_%H%M%S')}.zip"
            
            # Open and return the file
            file_handle = open(backup.backup_path, 'rb')
            response = FileResponse(
                file_handle, 
                as_attachment=True, 
                filename=smart_str(filename)
            )
            response['Content-Length'] = backup.backup_size or os.path.getsize(backup.backup_path)
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Download failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def delete_backup(self, request, pk=None):
        """Delete backup and associated files"""
        backup = self.get_object()
        
        try:
            # Delete physical backup files
            if backup.backup_path and os.path.exists(backup.backup_path):
                if os.path.isfile(backup.backup_path):
                    os.remove(backup.backup_path)
                elif os.path.isdir(backup.backup_path):
                    shutil.rmtree(backup.backup_path)
            
            # Delete associated backup files from database
            backup.backup_files.all().delete()
            backup.logs.all().delete()
            
            # Delete the backup record
            backup_name = backup.name
            backup.delete()
            
            return Response({
                'success': True,
                'message': f'Backup "{backup_name}" deleted successfully'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Delete failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get backup system statistics"""
        stats = {
            'total_backups': Backup.objects.count(),
            'completed_backups': Backup.objects.filter(status='completed').count(),
            'failed_backups': Backup.objects.filter(status='failed').count(),
            'in_progress_backups': Backup.objects.filter(status='in_progress').count(),
        }
        
        # Storage statistics
        total_storage = Backup.objects.filter(status='completed').aggregate(
            total=Sum('backup_size')
        )['total'] or 0
        
        stats['total_storage_used'] = backup_utils._format_bytes(total_storage) if hasattr(backup_utils, '_format_bytes') else f"{total_storage} bytes"
        
        # Record and file statistics
        stats['total_records_backed_up'] = Backup.objects.filter(status='completed').aggregate(
            total=Sum('total_records')
        )['total'] or 0
        
        stats['total_files_backed_up'] = Backup.objects.filter(status='completed').aggregate(
            total=Sum('total_files')
        )['total'] or 0
        
        # Average backup size
        avg_size = Backup.objects.filter(status='completed').aggregate(
            avg=Avg('backup_size')
        )['avg'] or 0
        
        stats['average_backup_size'] = backup_utils._format_bytes(avg_size) if hasattr(backup_utils, '_format_bytes') else f"{avg_size} bytes"
        
        # Last and next backup dates
        last_backup = Backup.objects.filter(status='completed').order_by('-created_at').first()
        stats['last_backup_date'] = last_backup.created_at if last_backup else None
        
        next_schedule = BackupSchedule.objects.filter(
            is_active=True, 
            next_run__isnull=False
        ).order_by('next_run').first()
        stats['next_scheduled_backup'] = next_schedule.next_run if next_schedule else None
        
        serializer = BackupStatsSerializer(data=stats)
        serializer.is_valid()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_full_backup(self, request):
        """Create comprehensive full backup using database dumps"""
        try:
            # Get form data
            name = request.data.get('name', '').strip()
            description = request.data.get('description', '').strip()
            include_media = request.data.get('include_media', True)
            compress = request.data.get('compress', True)
            
            # Create backup instance for tracking
            backup = Backup.objects.create(
                name=name or f"FullBackup_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                description=description,
                backup_type='full',
                include_media=include_media,
                compress_backup=compress,
                created_by=request.user,
                status='pending'
            )
            
            # Start comprehensive backup in background
            def run_full_backup():
                try:
                    backup.mark_as_started()
                    backup.current_operation = "Initializing comprehensive backup..."
                    backup.save()
                    
                    # Use FullBackupUtilities for comprehensive backup
                    full_backup_utils = FullBackupUtilities()
                    
                    results = full_backup_utils.create_comprehensive_backup(
                        backup_name=backup.name,
                        include_media=include_media,
                        compress=compress,
                        backup_instance=backup
                    )
                    
                    if results['success']:
                        # Update backup instance with results
                        backup.backup_path = results['backup_path']
                        backup.backup_size = results['total_size']
                        backup.compressed_size = results['compressed_size']
                        
                        # Update database info
                        db_results = results.get('database_results', {})
                        backup.total_tables = db_results.get('tables_count', 0)
                        backup.total_records = db_results.get('records_count', 0)
                        
                        # Update media info
                        media_results = results.get('media_results', {})
                        backup.total_files = media_results.get('total_files', 0)
                        
                        backup.mark_as_completed()
                        
                        logger.info(f"Comprehensive backup completed successfully: {backup.name}")
                        
                    else:
                        error_msg = '; '.join(results['errors'])
                        backup.mark_as_failed(error_msg)
                        logger.error(f"Comprehensive backup failed: {error_msg}")
                
                except Exception as e:
                    backup.mark_as_failed(str(e))
                    logger.error(f"Comprehensive backup exception: {str(e)}")
            
            # Start backup thread
            backup_thread = threading.Thread(target=run_full_backup)
            backup_thread.daemon = True
            backup_thread.start()
            
            return Response({
                'success': True,
                'message': 'Comprehensive backup started',
                'backup_id': str(backup.id),
                'status': backup.status
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to start comprehensive backup: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def restore_full_backup(self, request, pk=None):
        """Restore from comprehensive full backup using database dumps"""
        backup = self.get_object()
        
        try:
            restore_database = request.data.get('restore_database', True)
            restore_media = request.data.get('restore_media', True)
            create_pre_backup = request.data.get('create_pre_backup', True)
            
            # Create restore tracking instance
            restore_instance = BackupRestore.objects.create(
                backup=backup,
                restore_database=restore_database,
                restore_media=restore_media,
                status='pending'
            )
            
            # Start comprehensive restore in background
            def run_full_restore():
                try:
                    restore_instance.mark_as_started()
                    restore_instance.current_operation = "Starting comprehensive restore..."
                    restore_instance.save()
                    
                    # Create pre-restore backup if requested
                    if create_pre_backup:
                        restore_instance.current_operation = "Creating pre-restore backup..."
                        restore_instance.save()
                        
                        full_backup_utils = FullBackupUtilities()
                        pre_backup_name = f"PreRestore_{backup.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        pre_backup_results = full_backup_utils.create_comprehensive_backup(
                            backup_name=pre_backup_name,
                            include_media=restore_media,
                            compress=True
                        )
                        
                        if pre_backup_results['success']:
                            # Find the created backup instance
                            pre_backup_instance = Backup.objects.filter(name=pre_backup_name).first()
                            restore_instance.pre_restore_backup = pre_backup_instance
                            restore_instance.save()
                    
                    # Use FullBackupUtilities for comprehensive restore
                    full_backup_utils = FullBackupUtilities()
                    
                    results = full_backup_utils.restore_comprehensive_backup(
                        backup_path=backup.backup_path,
                        restore_database=restore_database,
                        restore_media=restore_media,
                        backup_instance=restore_instance
                    )
                    
                    if results['success']:
                        # Update restore instance with results
                        restore_instance.restored_records = results['database_results'].get('restored_records', 0)
                        restore_instance.restored_files = results['media_results'].get('restored_files', 0)
                        restore_instance.mark_as_completed()
                        
                        logger.info(f"Comprehensive restore completed successfully: {backup.name}")
                        
                    else:
                        error_msg = '; '.join(results['errors'])
                        restore_instance.mark_as_failed(error_msg)
                        logger.error(f"Comprehensive restore failed: {error_msg}")
                
                except Exception as e:
                    restore_instance.mark_as_failed(str(e))
                    logger.error(f"Comprehensive restore exception: {str(e)}")
            
            # Start restore thread
            restore_thread = threading.Thread(target=run_full_restore)
            restore_thread.daemon = True
            restore_thread.start()
            
            return Response({
                'success': True,
                'message': 'Comprehensive restore started',
                'restore_id': str(restore_instance.id),
                'status': restore_instance.status
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to start comprehensive restore: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """Clean up old backups"""
        retention_days = request.data.get('retention_days', 30)
        
        try:
            cleanup_results = backup_utils.cleanup_old_backups(retention_days)
            
            if cleanup_results['success']:
                return Response({
                    'success': True,
                    'message': f'Cleanup completed: {cleanup_results["deleted_backups"]} backups deleted',
                    'deleted_backups': cleanup_results['deleted_backups'],
                    'freed_space': cleanup_results['freed_space']
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Cleanup failed',
                    'errors': cleanup_results['errors']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Cleanup failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BackupRestoreViewSet(viewsets.ModelViewSet):
    """ViewSet for backup restore operations"""
    queryset = BackupRestore.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'restore_mode', 'backup__backup_type']
    search_fields = ['backup__name']
    ordering_fields = ['created_at', 'completed_at', 'duration_seconds']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BackupRestoreCreateSerializer
        return BackupRestoreSerializer
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get restore operation status and progress"""
        restore = self.get_object()
        
        # Calculate progress percentage
        progress_percentage = 0
        if restore.status == 'completed':
            progress_percentage = 100
        elif restore.status == 'in_progress':
            # Estimate progress based on duration (this is a simple heuristic)
            if restore.created_at:
                elapsed = (timezone.now() - restore.created_at).total_seconds()
                # Assume restore takes roughly as long as backup (rough estimate)
                estimated_total = max(300, elapsed * 2)  # At least 5 minutes
                progress_percentage = min(95, (elapsed / estimated_total) * 100)
        
        return Response({
            'status': restore.status,
            'status_display': restore.get_status_display(),
            'progress_percentage': progress_percentage,
            'current_operation': getattr(restore, 'current_operation', ''),
            'error_message': restore.error_message if restore.status == 'failed' else None,
            'created_at': restore.created_at,
            'completed_at': restore.completed_at,
        })


class BackupScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for backup schedules"""
    queryset = BackupSchedule.objects.all()
    serializer_class = BackupScheduleSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['frequency', 'backup_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'next_run']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Manually trigger a scheduled backup"""
        schedule = self.get_object()
        
        # Create backup based on schedule configuration
        backup_data = {
            'name': f"{schedule.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            'description': f"Manual run of scheduled backup: {schedule.name}",
            'backup_type': schedule.backup_type,
            'include_media': schedule.include_media,
            'include_staticfiles': schedule.include_staticfiles,
            'compress_backup': schedule.compress_backup,
        }
        
        serializer = BackupCreateSerializer(data=backup_data, context={'request': request})
        
        if serializer.is_valid():
            backup = serializer.save()
            
            # Update schedule
            schedule.last_run = timezone.now()
            schedule.last_backup = backup
            schedule.calculate_next_run()
            
            # Start backup process
            def run_backup():
                try:
                    call_command(
                        'create_backup_safe',
                        name=backup.name,
                        description=backup.description,
                        type=backup.backup_type,
                        compress=backup.compress_backup,
                        quiet=True
                    )
                except Exception as e:
                    backup.mark_as_failed(str(e))
            
            thread = threading.Thread(target=run_backup)
            thread.daemon = True
            thread.start()
            
            return Response(BackupSerializer(backup).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BackupSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for backup settings (singleton)"""
    queryset = BackupSettings.objects.all()
    serializer_class = BackupSettingsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request, *args, **kwargs):
        """Return settings instance or create default"""
        settings_instance = BackupSettings.get_settings()
        serializer = self.get_serializer(settings_instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Prevent creation if settings already exist"""
        if BackupSettings.objects.exists():
            return Response(
                {'error': 'Settings already exist. Use PUT to update.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffUser])
def model_info(request):
    """Get information about available Django models for selective backup/restore"""
    model_data = []
    dependencies = backup_utils.get_model_dependencies()
    
    for model in apps.get_models():
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        
        try:
            record_count = model.objects.count()
        except:
            record_count = 0
        
        model_info = {
            'app_label': model._meta.app_label,
            'model_name': model._meta.model_name,
            'verbose_name': str(model._meta.verbose_name),
            'full_name': model_key,
            'record_count': record_count,
            'dependencies': dependencies.get(model_key, [])
        }
        
        model_data.append(model_info)
    
    # Sort by app label, then model name
    model_data.sort(key=lambda x: (x['app_label'], x['model_name']))
    
    serializer = ModelInfoSerializer(data=model_data, many=True)
    serializer.is_valid()
    return Response(serializer.data)


# Template-based views for web interface

@staff_member_required
def backup_dashboard(request):
    """Main backup dashboard view"""
    # Get recent backups
    recent_backups = Backup.objects.order_by('-created_at')[:10]
    
    # Get statistics
    stats = {
        'total_backups': Backup.objects.count(),
        'completed_backups': Backup.objects.filter(status='completed').count(),
        'failed_backups': Backup.objects.filter(status='failed').count(),
        'in_progress_backups': Backup.objects.filter(status='in_progress').count(),
    }
    
    # Get active schedules
    active_schedules = BackupSchedule.objects.filter(is_active=True)
    
    context = {
        'recent_backups': recent_backups,
        'stats': stats,
        'active_schedules': active_schedules,
    }
    
    return render(request, 'backups/dashboard.html', context)


@staff_member_required
def backup_list(request):
    """List all backups"""
    backups = Backup.objects.order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    if status_filter:
        backups = backups.filter(status=status_filter)
    
    if type_filter:
        backups = backups.filter(backup_type=type_filter)
    
    context = {
        'backups': backups,
        'status_choices': Backup.STATUS_CHOICES,
        'type_choices': Backup.BACKUP_TYPE_CHOICES,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    
    return render(request, 'backups/backup_list.html', context)


@staff_member_required
def backup_detail(request, backup_id):
    """Show backup details"""
    backup = get_object_or_404(Backup, id=backup_id)
    backup_files = backup.backup_files.order_by('file_type', 'filename')
    logs = backup.logs.order_by('-created_at')[:50]  # Recent logs
    
    context = {
        'backup': backup,
        'backup_files': backup_files,
        'logs': logs,
    }
    
    return render(request, 'backups/backup_detail.html', context)


@staff_member_required
def create_backup(request):
    """Create new backup form"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            backup_type = request.POST.get('backup_type', 'full')
            include_media = request.POST.get('include_media') == 'on'
            compress = request.POST.get('compress') == 'on'
            
            # Create backup instance first for progress tracking
            backup = Backup.objects.create(
                name=name or None,  # Let model generate name if empty
                description=description,
                backup_type=backup_type,
                include_media=include_media,
                compress_backup=compress,
                created_by=request.user,
                status='pending'
            )
            
            # Start backup in background - pass the backup ID to update existing record
            def run_backup():
                try:
                    # Mark as started
                    backup.status = 'in_progress'
                    backup.current_operation = 'Initializing backup...'
                    backup.progress_percentage = 0
                    backup.started_at = timezone.now()
                    backup.save()
                    
                    # Use backup_utils directly instead of command to avoid duplicate creation
                    from backups.utils import backup_utils
                    import tempfile
                    import os
                    
                    # Create temporary working directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        backup_dir = os.path.join(temp_dir, f"backup_{backup.id}")
                        os.makedirs(backup_dir)
                        
                        backup.current_operation = "Creating backup files..."
                        backup.progress_percentage = 20
                        backup.save()
                        
                        success = True
                        total_files = 0
                        total_size = 0
                        
                        # Database backup
                        if backup.backup_type in ['full', 'database']:
                            backup.current_operation = "Backing up database..."
                            backup.progress_percentage = 40
                            backup.save()
                            
                            db_results = backup_utils.create_database_backup(backup_dir, backup)
                            if db_results['success']:
                                total_files += len(db_results['files'])
                                total_size += sum(f['file_size'] for f in db_results['files'])
                                backup.total_tables = db_results['total_tables']
                                backup.total_records = db_results['total_records']
                            else:
                                success = False
                        
                        # Media backup
                        if success and backup.backup_type in ['full', 'media'] and backup.include_media:
                            backup.current_operation = "Backing up media files..."
                            backup.progress_percentage = 60
                            backup.save()
                            
                            media_results = backup_utils.create_media_backup(backup_dir, backup)
                            if media_results['success']:
                                total_files += media_results['total_files']
                                total_size += media_results['total_size']
                            else:
                                success = False
                        
                        backup.total_files = total_files
                        backup.backup_size = total_size
                        
                        # Always set a backup path first (copy uncompressed)
                        output_dir = getattr(settings, 'BACKUP_ROOT', backup_utils.backup_root)
                        os.makedirs(output_dir, exist_ok=True)
                        permanent_dir = os.path.join(output_dir, f"backup_{backup.id}")
                        
                        # Copy backup files to permanent location
                        import shutil
                        if os.path.exists(permanent_dir):
                            shutil.rmtree(permanent_dir)
                        shutil.copytree(backup_dir, permanent_dir)
                        backup.backup_path = permanent_dir
                        
                        # Compress if requested
                        if success and compress:
                            backup.current_operation = "Compressing backup..."
                            backup.progress_percentage = 80
                            backup.save()
                            
                            timestamp = backup.created_at.strftime('%Y%m%d_%H%M%S')
                            archive_name = f"{backup.name}_{timestamp}.tar.gz"
                            archive_path = os.path.join(output_dir, archive_name)
                            
                            compress_results = backup_utils.compress_backup(backup_dir, archive_path, backup)
                            if compress_results['success']:
                                backup.backup_path = archive_path  # Use compressed version
                                backup.compressed_size = compress_results['compressed_size']
                                # Remove uncompressed directory to save space
                                if os.path.exists(permanent_dir):
                                    shutil.rmtree(permanent_dir)
                            else:
                                # Compression failed, keep uncompressed version
                                logger.warning(f"Compression failed for backup {backup.id}, keeping uncompressed version")
                        
                        if success:
                            backup.current_operation = "Finalizing backup..."
                            backup.progress_percentage = 95
                            backup.save()
                            
                            backup.mark_as_completed()
                        else:
                            backup.mark_as_failed("Backup process failed")
                
                except Exception as e:
                    backup.mark_as_failed(str(e))
                    logger.error(f"Backup creation failed: {str(e)}")
            
            thread = threading.Thread(target=run_backup)
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                'success': True,
                'message': 'Backup creation started',
                'backup_id': str(backup.id)
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to start backup: {str(e)}'
            }, status=400)
    
    context = {
        'backup_types': Backup.BACKUP_TYPE_CHOICES,
    }
    
    return render(request, 'backups/create_backup.html', context)


@staff_member_required
def restore_backup(request, backup_id):
    """Restore backup form"""
    backup = get_object_or_404(Backup, id=backup_id)
    
    if not backup.can_restore:
        return JsonResponse({
            'success': False,
            'message': 'Backup cannot be restored'
        }, status=400)
    
    if request.method == 'POST':
        try:
            # Get form data
            restore_database = request.POST.get('restore_database') == 'on'
            restore_media = request.POST.get('restore_media') == 'on'
            create_pre_backup = request.POST.get('create_pre_backup') == 'on'
            
            # Create restore instance
            restore = BackupRestore.objects.create(
                backup=backup,
                restore_database=restore_database,
                restore_media=restore_media,
                initiated_by=request.user
            )
            
            # Start restore in background
            def run_restore():
                import time
                try:
                    # Mark as started
                    restore.mark_as_started()
                    restore.current_operation = "Preparing restore..."
                    restore.save()
                    
                    # Execute real restore process (quick mode for speed)
                    args = [str(backup.id)]
                    kwargs = {
                        'force': True,
                        'quiet': True,
                        'no_verify': True,  # Skip verification to avoid failures
                        'no_pre_backup': True,  # Skip pre-backup for now
                        'quick': True  # Use quick restore mode for speed
                    }
                    
                    # Handle database-only backups
                    if backup.backup_type == 'database':
                        kwargs['no_media'] = True  # Database-only backups can't restore media
                    elif backup.backup_type == 'media':
                        kwargs['no_database'] = True  # Media-only backups can't restore database
                    
                    # Override with user preferences
                    if not restore_database:
                        kwargs['no_database'] = True
                    if not restore_media:
                        kwargs['no_media'] = True
                    
                    # Set initial progress
                    restore.current_operation = "Starting restore process..."
                    restore.progress_percentage = 10
                    restore.save()
                    
                    # Call the real restore command
                    call_command('restore_backup_safe', *args, **kwargs)
                    
                    # Mark as completed if successful
                    restore.mark_as_completed()
                
                except Exception as e:
                    restore.mark_as_failed(str(e))
            
            thread = threading.Thread(target=run_restore)
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                'success': True,
                'message': 'Backup restoration started',
                'restore_id': str(restore.id)
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to start restoration: {str(e)}'
            }, status=400)
    
    context = {
        'backup': backup,
        'can_restore_database': backup.backup_type in ['full', 'database'],
        'can_restore_media': backup.backup_type in ['full', 'media'] and backup.include_media,
    }
    
    return render(request, 'backups/restore_backup.html', context)


@staff_member_required
@csrf_exempt
def backup_progress(request, backup_id):
    """Get backup progress via AJAX"""
    backup = get_object_or_404(Backup, id=backup_id)
    
    data = {
        'id': str(backup.id),
        'status': backup.status,
        'progress_percentage': backup.progress_percentage,
        'current_operation': backup.current_operation,
        'error_message': backup.error_message,
    }
    
    return JsonResponse(data)