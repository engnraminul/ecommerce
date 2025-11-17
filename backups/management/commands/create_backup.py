from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from backups.services import BackupService
from backups.models import Backup
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a backup of the database and/or media files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['database', 'media', 'full'],
            default='full',
            help='Type of backup to create (default: full)'
        )
        
        parser.add_argument(
            '--name',
            type=str,
            help='Custom name for the backup'
        )
        
        parser.add_argument(
            '--no-cleanup',
            action='store_true',
            help='Skip automatic cleanup of old backups'
        )
        
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Number of days to retain backups (default: 30)'
        )
    
    def handle(self, *args, **options):
        backup_type = options['type']
        backup_name = options['name']
        no_cleanup = options['no_cleanup']
        retention_days = options['retention_days']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting {backup_type} backup creation...')
        )
        
        try:
            # Create backup
            backup_service = BackupService()
            backup = backup_service.create_backup(
                backup_type=backup_type,
                name=backup_name,
                user=None  # System backup
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Backup created successfully: {backup.name}')
            )
            self.stdout.write(f'Backup ID: {backup.id}')
            self.stdout.write(f'Size: {backup.formatted_size}')
            self.stdout.write(f'Files: {backup.file_count}')
            
            if backup.database_file:
                self.stdout.write(f'Database file: {backup.database_file}')
            if backup.media_file:
                self.stdout.write(f'Media file: {backup.media_file}')
            
            # Cleanup old backups if requested
            if not no_cleanup:
                self.stdout.write('Cleaning up old backups...')
                deleted_count = backup_service.cleanup_old_backups(retention_days)
                self.stdout.write(
                    self.style.SUCCESS(f'Cleaned up {deleted_count} old backups')
                )
            
        except Exception as e:
            logger.error(f'Backup creation failed: {str(e)}')
            raise CommandError(f'Backup creation failed: {str(e)}')