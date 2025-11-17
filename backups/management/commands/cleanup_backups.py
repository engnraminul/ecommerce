from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from backups.services import BackupService
from backups.models import Backup
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old backup files based on retention policy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Number of days to retain backups (default: 30)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation'
        )
    
    def handle(self, *args, **options):
        retention_days = options['retention_days']
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.WARNING(f'Cleaning up backups older than {retention_days} days...')
        )
        
        # Get backups to be deleted
        cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)
        old_backups = Backup.objects.filter(created_at__lt=cutoff_date)
        
        if not old_backups.exists():
            self.stdout.write(
                self.style.SUCCESS('No old backups found to clean up.')
            )
            return
        
        total_size = sum(backup.total_size or 0 for backup in old_backups)
        
        self.stdout.write(f'Found {old_backups.count()} backups to delete:')
        for backup in old_backups:
            self.stdout.write(f'  - {backup.name} ({backup.formatted_size}) - {backup.created_at}')
        
        self.stdout.write(f'Total size to be freed: {self._format_size(total_size)}')
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('Dry run completed. No files were deleted.')
            )
            return
        
        # Confirm deletion
        if not force:
            confirm = input('Are you sure you want to delete these backups? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Cleanup cancelled.')
                return
        
        try:
            backup_service = BackupService()
            deleted_count = backup_service.cleanup_old_backups(retention_days)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {deleted_count} old backups')
            )
            
        except Exception as e:
            logger.error(f'Cleanup failed: {str(e)}')
            raise CommandError(f'Cleanup failed: {str(e)}')
    
    def _format_size(self, size_bytes):
        """Format size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"