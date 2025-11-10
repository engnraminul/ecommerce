from django.apps import AppConfig


class BackupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backups'
    verbose_name = 'Backup Management'
    
    def ready(self):
        """Initialize backup configurations when app is ready"""
        from django.conf import settings
        import os
        
        # Ensure backup directories exist
        backup_root = getattr(settings, 'BACKUP_ROOT', os.path.join(settings.BASE_DIR, 'backups_storage'))
        os.makedirs(backup_root, exist_ok=True)
        os.makedirs(os.path.join(backup_root, 'database'), exist_ok=True)
        os.makedirs(os.path.join(backup_root, 'media'), exist_ok=True)
        os.makedirs(os.path.join(backup_root, 'complete'), exist_ok=True)