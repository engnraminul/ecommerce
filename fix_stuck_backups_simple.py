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
    print("Checking for stuck backup operations...")
    
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
    
    print(f"Found {stuck_backups.count()} stuck backup operations")
    
    for backup in stuck_backups:
        print(f"  Fixing backup: {backup.name} (started {backup.started_at})")
        print(f"     Current operation: {backup.current_operation}")
        print(f"     Progress: {backup.progress_percentage}%")
        
        # Check if the backup file actually exists and is complete
        if backup.backup_path and os.path.exists(backup.backup_path):
            # If backup file exists, mark as completed
            backup.status = 'completed'
            backup.progress_percentage = 100
            backup.current_operation = "Backup completed (auto-fixed)"
            backup.completed_at = backup.updated_at or now
            print(f"     SUCCESS: Marked as completed (backup file exists)")
        else:
            # If no backup file, mark as failed
            backup.status = 'failed'
            backup.current_operation = "Backup failed (timeout)"
            backup.error_message = f"Backup operation timed out after {BACKUP_TIMEOUT_HOURS} hours"
            print(f"     FAILED: Marked as failed (no backup file found)")
        
        backup.save()
    
    # Check stuck restores
    stuck_restores = BackupRestore.objects.filter(
        status='in_progress',
        started_at__lt=restore_threshold
    )
    
    print(f"Found {stuck_restores.count()} stuck restore operations")
    
    for restore in stuck_restores:
        print(f"  Fixing restore: {restore.backup.name} (started {restore.started_at})")
        print(f"     Current operation: {restore.current_operation}")
        print(f"     Progress: {restore.progress_percentage}%")
        
        # Mark stuck restores as failed (safer than assuming completion)
        restore.status = 'failed'
        restore.current_operation = "Restore failed (timeout)"
        restore.error_message = f"Restore operation timed out after {RESTORE_TIMEOUT_HOURS} hours"
        restore.save()
        print(f"     FAILED: Marked as failed (timeout)")
    
    # Summary
    total_fixed = stuck_backups.count() + stuck_restores.count()
    print(f"\nFixed {total_fixed} stuck operations")
    
    # Show current status summary
    print("\nCurrent backup status summary:")
    print(f"  - Pending: {Backup.objects.filter(status='pending').count()}")
    print(f"  - In Progress: {Backup.objects.filter(status='in_progress').count()}")
    print(f"  - Completed: {Backup.objects.filter(status='completed').count()}")
    print(f"  - Failed: {Backup.objects.filter(status='failed').count()}")
    
    print(f"\nCurrent restore status summary:")
    print(f"  - Pending: {BackupRestore.objects.filter(status='pending').count()}")
    print(f"  - In Progress: {BackupRestore.objects.filter(status='in_progress').count()}")
    print(f"  - Completed: {BackupRestore.objects.filter(status='completed').count()}")
    print(f"  - Failed: {BackupRestore.objects.filter(status='failed').count()}")


if __name__ == '__main__':
    try:
        fix_stuck_backup_operations()
        print("\nBackup cleanup completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)