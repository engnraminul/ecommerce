#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backups.models import Backup, RestoreLog
from backups.services import RestoreService

print("=== Testing Restore Process ===")

# Get the first backup
backup = Backup.objects.first()
if not backup:
    print("No backups found!")
    exit(1)

print(f"Testing restore for backup: {backup.name} (ID: {backup.id})")
print(f"Backup type: {backup.backup_type}")
print(f"Status: {backup.status}")
print(f"Can restore: {backup.can_restore}")

try:
    restore_service = RestoreService()
    
    print("\n=== Starting Validation ===")
    restore_log = restore_service.restore_backup(
        backup=backup,
        restore_type='database',  # Safer to test with database only
        user=None,
        validate_only=True  # Just validate first
    )
    
    print(f"Validation result:")
    print(f"  ID: {restore_log.id}")
    print(f"  Success: {restore_log.success}")
    print(f"  Validation passed: {restore_log.validation_passed}")
    print(f"  Validation notes: {restore_log.validation_notes}")
    print(f"  Error message: {restore_log.error_message}")
    
    # If validation passes, try actual restore
    if restore_log.validation_passed:
        print("\n=== Starting Actual Restore ===")
        restore_log2 = restore_service.restore_backup(
            backup=backup,
            restore_type='database',
            user=None,
            validate_only=False
        )
        
        print(f"Restore result:")
        print(f"  ID: {restore_log2.id}")
        print(f"  Success: {restore_log2.success}")
        print(f"  Error message: {restore_log2.error_message}")
        print(f"  Completed at: {restore_log2.completed_at}")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()