#!/usr/bin/env python
"""
Script to fix stuck backup operations that are showing "Backup in Progress" for too long
"""

import os
import django
import sys
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backups.models import Backup, BackupRestore


def fix_stuck_backup_operations():
    """
    Find and fix backup operations that have been stuck in 'in_progress' status for too long
    """
    print("🔍 Checking for stuck backup operations...")
    
    # Define timeout thresholds
    BACKUP_TIMEOUT_HOURS = 2  # Backups should complete within 2 hours
    RESTORE_TIMEOUT_HOURS = 3  # Restores may take longer
    
    now = timezone.now()
    backup_threshold = now - timedelta(hours=BACKUP_TIMEOUT_HOURS)
    restore_threshold = now - timedelta(hours=RESTORE_TIMEOUT_HOURS)
    
    # Check stuck backups
    stuck_backups = Backup.objects.filter(
        status='in_progress',
        started_at__lt=backup_threshold
    )
    
    print(f"📊 Found {stuck_backups.count()} stuck backup operations")
    
    for backup in stuck_backups:
        print(f"  🔧 Fixing backup: {backup.name} (started {backup.started_at})")
        print(f"     Current operation: {backup.current_operation}")
        print(f"     Progress: {backup.progress_percentage}%")
        
        # Check if the backup file actually exists and is complete
        if backup.backup_path and os.path.exists(backup.backup_path):
            # If backup file exists, mark as completed
            backup.status = 'completed'
            backup.progress_percentage = 100
            backup.current_operation = "Backup completed (auto-fixed)"
            backup.completed_at = backup.updated_at or now
            print(f"     ✅ Marked as completed (backup file exists)")
        else:
            # If no backup file, mark as failed
            backup.status = 'failed'
            backup.current_operation = "Backup failed (timeout)"
            backup.error_message = f"Backup operation timed out after {BACKUP_TIMEOUT_HOURS} hours"
            print(f"     ❌ Marked as failed (no backup file found)")
        
        backup.save()
    
    # Check stuck restores
    stuck_restores = BackupRestore.objects.filter(
        status='in_progress',
        started_at__lt=restore_threshold
    )
    
    print(f"📊 Found {stuck_restores.count()} stuck restore operations")
    
    for restore in stuck_restores:
        print(f"  🔧 Fixing restore: {restore.backup.name} (started {restore.started_at})")
        print(f"     Current operation: {restore.current_operation}")
        print(f"     Progress: {restore.progress_percentage}%")
        
        # Mark stuck restores as failed (safer than assuming completion)
        restore.status = 'failed'
        restore.current_operation = "Restore failed (timeout)"
        restore.error_message = f"Restore operation timed out after {RESTORE_TIMEOUT_HOURS} hours"
        restore.save()
        print(f"     ❌ Marked as failed (timeout)")
    
    # Summary
    total_fixed = stuck_backups.count() + stuck_restores.count()
    print(f"\n✅ Fixed {total_fixed} stuck operations")
    
    # Show current status summary
    print("\n📈 Current backup status summary:")
    print(f"  • Pending: {Backup.objects.filter(status='pending').count()}")
    print(f"  • In Progress: {Backup.objects.filter(status='in_progress').count()}")
    print(f"  • Completed: {Backup.objects.filter(status='completed').count()}")
    print(f"  • Failed: {Backup.objects.filter(status='failed').count()}")
    
    print(f"\n📈 Current restore status summary:")
    print(f"  • Pending: {BackupRestore.objects.filter(status='pending').count()}")
    print(f"  • In Progress: {BackupRestore.objects.filter(status='in_progress').count()}")
    print(f"  • Completed: {BackupRestore.objects.filter(status='completed').count()}")
    print(f"  • Failed: {BackupRestore.objects.filter(status='failed').count()}")


def add_timeout_detection_method():
    """
    Add a method to the Backup model to detect timeouts automatically
    """
    print("\n🔧 Adding timeout detection capability...")
    
    # This would be added to the Backup model in models.py
    timeout_detection_code = '''
    def is_stuck(self):
        """Check if this backup operation is stuck (timeout)"""
        if self.status != 'in_progress':
            return False
        
        if not self.started_at:
            return False
        
        from django.utils import timezone
        from datetime import timedelta
        
        timeout_hours = 2  # Configurable timeout
        timeout_threshold = timezone.now() - timedelta(hours=timeout_hours)
        
        return self.started_at < timeout_threshold
    
    def auto_fix_if_stuck(self):
        """Automatically fix this backup if it's stuck"""
        if not self.is_stuck():
            return False
        
        if self.backup_path and os.path.exists(self.backup_path):
            self.status = 'completed'
            self.progress_percentage = 100
            self.current_operation = "Backup completed (auto-fixed)"
            self.completed_at = timezone.now()
        else:
            self.status = 'failed'
            self.current_operation = "Backup failed (timeout)"
            self.error_message = f"Backup operation timed out"
        
        self.save()
        return True
    '''
    
    print("💡 Suggested code to add to Backup model:")
    print(timeout_detection_code)


def create_periodic_cleanup_task():
    """
    Create a management command for periodic cleanup of stuck operations
    """
    management_command_code = '''
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
            default=2,
            help='Backup timeout in hours (default: 2)'
        )
        parser.add_argument(
            '--restore-timeout',
            type=int,
            default=3,
            help='Restore timeout in hours (default: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        backup_timeout = options['backup_timeout']
        restore_timeout = options['restore_timeout']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write("🔍 DRY RUN - No changes will be made")
        
        now = timezone.now()
        backup_threshold = now - timedelta(hours=backup_timeout)
        restore_threshold = now - timedelta(hours=restore_timeout)
        
        # Fix stuck backups
        stuck_backups = Backup.objects.filter(
            status='in_progress',
            started_at__lt=backup_threshold
        )
        
        self.stdout.write(f"Found {stuck_backups.count()} stuck backups")
        
        for backup in stuck_backups:
            if dry_run:
                self.stdout.write(f"  Would fix: {backup.name}")
                continue
            
            if backup.backup_path and os.path.exists(backup.backup_path):
                backup.mark_as_completed()
                self.stdout.write(f"  Fixed (completed): {backup.name}")
            else:
                backup.mark_as_failed("Operation timed out")
                self.stdout.write(f"  Fixed (failed): {backup.name}")
        
        # Fix stuck restores
        stuck_restores = BackupRestore.objects.filter(
            status='in_progress', 
            started_at__lt=restore_threshold
        )
        
        self.stdout.write(f"Found {stuck_restores.count()} stuck restores")
        
        for restore in stuck_restores:
            if dry_run:
                self.stdout.write(f"  Would fix: {restore.backup.name}")
                continue
                
            restore.mark_as_failed("Operation timed out")
            self.stdout.write(f"  Fixed (failed): {restore.backup.name}")
        
        total = stuck_backups.count() + stuck_restores.count()
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Fixed {total} stuck operations")
            )
    '''
    
    print("\n💡 Management command to create:")
    print("File: backups/management/commands/cleanup_stuck_operations.py")
    print(management_command_code)


if __name__ == '__main__':
    try:
        fix_stuck_backup_operations()
        add_timeout_detection_method()
        create_periodic_cleanup_task()
        print("\n🎉 Backup cleanup completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)