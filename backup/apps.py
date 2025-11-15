from django.apps import AppConfig


class BackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backup'
    verbose_name = 'Backup Management'
    
    def ready(self):
        import backup.signals  # Import signals when app is ready