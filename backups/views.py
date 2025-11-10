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
    
    def perform_create(self, serializer):
        """Create a new backup and start the backup process"""
        backup = serializer.save(created_by=self.request.user)
        
        # Start backup process in background thread
        def run_backup():
            try:
                call_command(
                    'create_backup_safe',
                    name=backup.name,
                    description=backup.description,
                    type=backup.backup_type,
                    compress=backup.compress_backup,
                    no_compress=not backup.compress_backup,
                    include_media=backup.include_media,
                    no_media=not backup.include_media,
                    include_static=backup.include_staticfiles,
                    quiet=True
                )
            except Exception as e:
                backup.mark_as_failed(str(e))
                logger.error(f"Backup {backup.id} failed: {str(e)}")
        
        thread = threading.Thread(target=run_backup)
        thread.daemon = True
        thread.start()
    
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
                try:
                    args = [str(backup.id)]
                    kwargs = {
                        'force': True,  # Skip confirmation
                        'mode': restore.restore_mode,
                        'quiet': True
                    }
                    
                    if not restore.restore_database:
                        kwargs['no_database'] = True
                    if not restore.restore_media:
                        kwargs['no_media'] = True
                    if restore.selected_models:
                        kwargs['models'] = ','.join(restore.selected_models)
                    if restore.exclude_models:
                        kwargs['exclude_models'] = ','.join(restore.exclude_models)
                    
                    call_command('restore_backup_safe', *args, **kwargs)
                
                except Exception as e:
                    restore.mark_as_failed(str(e))
                    logger.error(f"Restore {restore.id} failed: {str(e)}")
            
            thread = threading.Thread(target=run_restore)
            thread.daemon = True
            thread.start()
            
            return Response(BackupRestoreSerializer(restore).data, status=status.HTTP_201_CREATED)
        
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
        """Get download URL for backup file"""
        backup = self.get_object()
        
        if not backup.backup_path or not backup.can_restore:
            return Response(
                {'error': 'Backup file is not available for download'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # In a real implementation, you'd return a signed URL or stream the file
        return Response({
            'download_url': f'/backup/download/{backup.id}/',
            'filename': f"{backup.name}_{backup.created_at.strftime('%Y%m%d_%H%M%S')}.tar.gz",
            'size': backup.backup_size
        })
    
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
            
            # Create backup instance
            backup = Backup.objects.create(
                name=name or None,  # Let model generate name if empty
                description=description,
                backup_type=backup_type,
                include_media=include_media,
                compress_backup=compress,
                created_by=request.user
            )
            
            # Start backup in background
            def run_backup():
                try:
                    args = []
                    kwargs = {
                        'type': backup_type,
                        'quiet': True
                    }
                    
                    if name:
                        kwargs['name'] = name
                    if description:
                        kwargs['description'] = description
                    if not include_media:
                        kwargs['no_media'] = True
                    if not compress:
                        kwargs['no_compress'] = True
                    
                    call_command('create_backup_safe', **kwargs)
                
                except Exception as e:
                    backup.mark_as_failed(str(e))
            
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
                try:
                    args = [str(backup.id)]
                    kwargs = {
                        'force': True,
                        'quiet': True
                    }
                    
                    if not restore_database:
                        kwargs['no_database'] = True
                    if not restore_media:
                        kwargs['no_media'] = True
                    if not create_pre_backup:
                        kwargs['no_pre_backup'] = True
                    
                    call_command('restore_backup_safe', *args, **kwargs)
                
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