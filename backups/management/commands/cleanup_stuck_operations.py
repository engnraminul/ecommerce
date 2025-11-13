from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from backups.models import Backup, BackupRestore
import os


class Command(BaseCommand):
    help = 'Clean up stuck backup and restore operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-timeout',
            type=int,
            default=30,  # 30 minutes default timeout
            help='Backup timeout in minutes (default: 30)'
        )
        parser.add_argument(
            '--restore-timeout',
            type=int,
            default=60,  # 1 hour default timeout for restores
            help='Restore timeout in minutes (default: 60)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even for recent operations'
        )

    def handle(self, *args, **options):
        backup_timeout = options['backup_timeout']
        restore_timeout = options['restore_timeout']
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN - No changes will be made")
            )
        
        now = timezone.now()
        backup_threshold = now - timedelta(minutes=backup_timeout)
        restore_threshold = now - timedelta(minutes=restore_timeout)
        
        # Fix stuck backups
        stuck_backups_query = Backup.objects.filter(status='in_progress')
        
        if not force:
            stuck_backups_query = stuck_backups_query.filter(
                started_at__lt=backup_threshold
            )
        
        stuck_backups = stuck_backups_query
        
        self.stdout.write(f"Found {stuck_backups.count()} stuck backup operations")
        
        fixed_count = 0
        for backup in stuck_backups:
            elapsed = None
            if backup.started_at:
                elapsed = now - backup.started_at
                elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            else:
                elapsed_str = "Unknown"
            
            self.stdout.write(f"  Backup: {backup.name}")
            self.stdout.write(f"    Started: {backup.started_at}")
            self.stdout.write(f"    Elapsed: {elapsed_str}")
            self.stdout.write(f"    Progress: {backup.progress_percentage}%")
            self.stdout.write(f"    Operation: {backup.current_operation}")
            
            if dry_run:
                if backup.backup_path and os.path.exists(backup.backup_path):
                    self.stdout.write("    Would mark as: COMPLETED")
                else:
                    self.stdout.write("    Would mark as: FAILED")
                continue
            
            # Actually fix the backup
            if backup.backup_path and os.path.exists(backup.backup_path):
                backup.status = 'completed'
                backup.progress_percentage = 100
                backup.current_operation = "Backup completed (auto-fixed)"
                backup.completed_at = backup.updated_at or now
                backup.save()
                self.stdout.write(
                    self.style.SUCCESS("    FIXED: Marked as completed")
                )
            else:
                backup.status = 'failed'
                backup.current_operation = "Backup failed (timeout)"
                backup.error_message = f"Backup operation timed out after {backup_timeout} minutes"
                backup.save()
                self.stdout.write(
                    self.style.ERROR("    FIXED: Marked as failed")
                )
            
            fixed_count += 1
        
        # Fix stuck restores
        stuck_restores_query = BackupRestore.objects.filter(status='in_progress')
        
        if not force:
            stuck_restores_query = stuck_restores_query.filter(
                started_at__lt=restore_threshold
            )
        
        stuck_restores = stuck_restores_query
        
        self.stdout.write(f"\nFound {stuck_restores.count()} stuck restore operations")
        
        for restore in stuck_restores:
            elapsed = None
            if restore.started_at:
                elapsed = now - restore.started_at
                elapsed_str = str(elapsed).split('.')[0]
            else:
                elapsed_str = "Unknown"
                
            self.stdout.write(f"  Restore: {restore.backup.name}")
            self.stdout.write(f"    Started: {restore.started_at}")
            self.stdout.write(f"    Elapsed: {elapsed_str}")
            self.stdout.write(f"    Progress: {restore.progress_percentage}%")
            self.stdout.write(f"    Operation: {restore.current_operation}")
            
            if dry_run:
                self.stdout.write("    Would mark as: FAILED")
                continue
                
            restore.status = 'failed'
            restore.current_operation = "Restore failed (timeout)"
            restore.error_message = f"Restore operation timed out after {restore_timeout} minutes"
            restore.save()
            self.stdout.write(
                self.style.ERROR("    FIXED: Marked as failed")
            )
            fixed_count += 1
        
        total = stuck_backups.count() + stuck_restores.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\nWould fix {total} stuck operations")
            )
        elif total > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\nFixed {fixed_count} stuck operations")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("No stuck operations found")
            )
        
        # Show summary
        self.stdout.write("\nCurrent Status Summary:")
        self.stdout.write(f"  Backups - Pending: {Backup.objects.filter(status='pending').count()}")
        self.stdout.write(f"  Backups - In Progress: {Backup.objects.filter(status='in_progress').count()}")
        self.stdout.write(f"  Backups - Completed: {Backup.objects.filter(status='completed').count()}")
        self.stdout.write(f"  Backups - Failed: {Backup.objects.filter(status='failed').count()}")
        
        self.stdout.write(f"  Restores - Pending: {BackupRestore.objects.filter(status='pending').count()}")
        self.stdout.write(f"  Restores - In Progress: {BackupRestore.objects.filter(status='in_progress').count()}")
        self.stdout.write(f"  Restores - Completed: {BackupRestore.objects.filter(status='completed').count()}")
        self.stdout.write(f"  Restores - Failed: {BackupRestore.objects.filter(status='failed').count()}")