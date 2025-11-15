from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'backups', views.BackupRecordViewSet)
router.register(r'restores', views.RestoreRecordViewSet)
router.register(r'schedules', views.BackupScheduleViewSet)
router.register(r'settings', views.BackupSettingsViewSet)

app_name = 'backup'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Additional API endpoints
    path('api/statistics/', views.backup_statistics, name='backup_statistics'),
    path('api/cleanup/', views.cleanup_old_backups, name='cleanup_old_backups'),
    path('api/available-backups/', views.available_backups, name='available_backups'),
    path('api/test-settings/', views.test_backup_settings, name='test_backup_settings'),
    
    # File download endpoints
    path('download/<int:backup_id>/<str:file_type>/', 
         views.download_backup_file, name='download_backup_file'),
    
    # Dashboard views
    path('', views.backup_dashboard, name='dashboard'),
]