from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'backups', views.BackupViewSet)
router.register(r'schedules', views.BackupScheduleViewSet)
router.register(r'restore-logs', views.RestoreLogViewSet)

app_name = 'backups'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/system-info/', views.backup_system_info, name='system_info'),
    
    # Dashboard views
    path('dashboard/', views.backup_dashboard, name='dashboard'),
]