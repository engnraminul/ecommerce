from django.apps import AppConfig


class BackupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backups'
    verbose_name = 'Backup Management'
    
    def ready(self):
        try:
            import backups.signals  # noqa F401
        except ImportError:
            pass
