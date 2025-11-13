#!/usr/bin/env python
"""
Quick fix script for stuck backup operations
Usage: python quick_backup_fix.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backups.models import Backup, BackupRestore
from django.utils import timezone
from datetime import timedelta


def quick_fix():
    """Quick fix for stuck operations with short timeout (5 minutes)"""
    
    print("Quick Fix: Checking for stuck backup operations...")
    
    now = timezone.now()
    timeout_minutes = 5  # Very short timeout for quick fix
    timeout_threshold = now - timedelta(minutes=timeout_minutes)
    
    # Fix stuck backups
    stuck_backups = Backup.objects.filter(
        status='in_progress',
        started_at__lt=timeout_threshold
    )
    
    print(f"Found {stuck_backups.count()} stuck backups (> {timeout_minutes} minutes)")
    
    for backup in stuck_backups:
        print(f"  Fixing: {backup.name}")
        if backup.auto_fix_if_stuck(timeout_minutes):
            print(f"    FIXED: {backup.status}")
    
    # Fix stuck restores  
    stuck_restores = BackupRestore.objects.filter(
        status='in_progress',
        started_at__lt=timeout_threshold
    )
    
    print(f"Found {stuck_restores.count()} stuck restores (> {timeout_minutes} minutes)")
    
    for restore in stuck_restores:
        print(f"  Fixing: {restore.backup.name}")
        if restore.auto_fix_if_stuck(timeout_minutes):
            print(f"    FIXED: {restore.status}")
    
    # Show final status
    total_in_progress = (
        Backup.objects.filter(status='in_progress').count() +
        BackupRestore.objects.filter(status='in_progress').count()
    )
    
    print(f"\nOperations still in progress: {total_in_progress}")
    
    if total_in_progress == 0:
        print("SUCCESS: All operations completed!")
    else:
        print("Note: Some operations are still running (recent or still active)")


if __name__ == '__main__':
    try:
        quick_fix()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)