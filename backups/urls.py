from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'backups', views.BackupViewSet)
router.register(r'restores', views.BackupRestoreViewSet)
router.register(r'schedules', views.BackupScheduleViewSet)
router.register(r'settings', views.BackupSettingsViewSet)

app_name = 'backups'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/models/', views.model_info, name='model_info'),
    
    # Web interface
    path('', views.backup_dashboard, name='dashboard'),
    path('backups/', views.backup_list, name='backup_list'),
    path('backups/<uuid:backup_id>/', views.backup_detail, name='backup_detail'),
    path('backups/create/', views.create_backup, name='create_backup'),
    path('backups/<uuid:backup_id>/restore/', views.restore_backup, name='restore_backup'),
    path('backups/<uuid:backup_id>/progress/', views.backup_progress, name='backup_progress'),
]