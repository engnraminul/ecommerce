from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from backup.models import BackupRecord, BackupStatus
from backup.services import BackupCleanupService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old backup files based on retention settings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Override retention days (default: use settings)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even if auto_cleanup is disabled',
        )
    
    def handle(self, *args, **options):
        """Clean up old backups"""
        cleanup_service = BackupCleanupService()
        
        # Check if cleanup is enabled or forced
        if not cleanup_service.settings.auto_cleanup and not options['force']:
            self.stdout.write("Auto cleanup is disabled. Use --force to override.")
            return
        
        # Determine retention period
        retention_days = options['days'] or cleanup_service.settings.default_retention_days
        
        if retention_days <= 0:
            self.stdout.write("Retention days is 0 (keep forever). Nothing to clean up.")
            return
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Find old backups
        old_backups = BackupRecord.objects.filter(
            created_at__lt=cutoff_date,
            status=BackupStatus.COMPLETED
        ).order_by('created_at')
        
        if not old_backups.exists():
            self.stdout.write("No old backups found for cleanup.")
            return
        
        self.stdout.write(f"Found {old_backups.count()} backups older than {retention_days} days")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN - No files will be deleted"))
            for backup in old_backups:
                self.stdout.write(f"Would delete: {backup.name} (Created: {backup.created_at})")
            return
        
        # Perform cleanup
        deleted_count = 0
        total_size_freed = 0
        
        for backup in old_backups:
            try:
                size = backup.file_size
                deleted_files = backup.delete_backup_files()
                backup.delete()
                
                deleted_count += 1
                total_size_freed += size
                
                self.stdout.write(f"Deleted: {backup.name}")
                
                if deleted_files:
                    for file_path in deleted_files:
                        logger.info(f"Deleted backup file: {file_path}")
                        
            except Exception as e:
                logger.error(f"Failed to delete backup {backup.name}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"Failed to delete {backup.name}: {str(e)}")
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup completed: {deleted_count} backups deleted, "
                f"{self.format_bytes(total_size_freed)} freed"
            )
        )
    
    def format_bytes(self, bytes_size):
        """Format bytes to human readable format"""
        if bytes_size == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"