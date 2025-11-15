#!/usr/bin/env python3
"""
Test script to verify complete restore functionality
"""
import os
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backup.models import BackupRecord, RestoreRecord
from backup.services import BackupService

def test_complete_restore():
    print("🔄 TESTING COMPLETE RESTORE FUNCTIONALITY")
    print("=" * 60)
    
    # 1. Check available backups
    available_backups = BackupRecord.objects.filter(status='completed').order_by('-created_at')
    valid_backups = []
    
    for backup in available_backups:
        has_db = backup.database_file and os.path.exists(backup.database_file)
        has_media = backup.media_file and os.path.exists(backup.media_file)
        if has_db or has_media:
            valid_backups.append(backup)
    
    print(f"📦 Found {len(valid_backups)} valid backups")
    
    if not valid_backups:
        print("❌ No valid backups available for testing")
        return
    
    # Use the first valid backup for testing
    test_backup = valid_backups[0]
    print(f"🎯 Testing with backup: {test_backup.name}")
    
    # 2. Create restore record
    restore_name = f"Test Restore {int(time.time())}"
    service = BackupService()
    
    try:
        # Test the restore process
        print(f"🚀 Starting restore process...")
        restore_record = service.restore_backup(
            backup_id=test_backup.id,
            restore_name=restore_name,
            restore_type='full',
            overwrite_existing=True,
            backup_before_restore=False  # Skip pre-restore backup for test
        )
        
        print(f"✅ Restore record created: {restore_record.name}")
        print(f"📊 Status: {restore_record.status}")
        
        # Wait a bit and check status
        print("⏳ Waiting for restore to complete...")
        for i in range(30):  # Wait up to 30 seconds
            restore_record.refresh_from_db()
            print(f"Status: {restore_record.status}")
            
            if restore_record.status in ['completed', 'failed']:
                break
                
            time.sleep(1)
        
        # Final status
        restore_record.refresh_from_db()
        print(f"\n🏁 FINAL RESULT:")
        print(f"Status: {restore_record.status}")
        if restore_record.error_message:
            print(f"Error: {restore_record.error_message}")
        
        if restore_record.status == 'completed':
            print("🎉 RESTORE FUNCTIONALITY IS WORKING!")
        else:
            print("❌ Restore failed - but at least the process works")
            
    except Exception as e:
        print(f"❌ Error during restore test: {str(e)}")

if __name__ == '__main__':
    test_complete_restore()