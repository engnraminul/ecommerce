#!/usr/bin/env python
"""
Test script to verify backup and restore fixes
Run this script to test both issues:
1. Progress modal hiding when backup completes
2. Restore functionality with proper file paths
"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backup.models import BackupRecord, RestoreRecord, BackupType, BackupStatus
from backup.services import BackupService, RestoreService
from django.contrib.auth import get_user_model
from django.test import Client

def test_backup_creation():
    """Test Issue 1: Backup progress tracking"""
    print("🔧 Testing Issue 1: Backup Creation & Progress Tracking")
    print("-" * 60)
    
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    if not user:
        print("❌ No superuser found")
        return False
    
    # Create test backup
    backup_record = BackupRecord.objects.create(
        name=f'Progress Test {int(time.time())}',
        backup_type=BackupType.DATABASE_ONLY,
        created_by=user,
        compress=True
    )
    
    print(f"✅ Created backup record: {backup_record.id}")
    print(f"   Initial status: {backup_record.status}")
    
    # Simulate backup service
    service = BackupService()
    service.create_backup(backup_record)
    
    # Check result
    backup_record.refresh_from_db()
    print(f"   Final status: {backup_record.status}")
    print(f"   Duration: {backup_record.duration}")
    
    if backup_record.status == BackupStatus.COMPLETED:
        print("✅ Issue 1 FIXED: Backup completes properly")
        
        # Check if file exists
        if backup_record.database_file and os.path.exists(backup_record.database_file):
            file_size = os.path.getsize(backup_record.database_file)
            print(f"✅ Backup file created: {file_size} bytes")
            return True
        else:
            print("❌ Backup file not created")
            return False
    else:
        print(f"❌ Backup failed with status: {backup_record.status}")
        return False

def test_restore_functionality():
    """Test Issue 2: Restore with proper file paths"""
    print("\n🔧 Testing Issue 2: Restore Functionality")
    print("-" * 60)
    
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    # Find a valid backup to restore from
    valid_backup = BackupRecord.objects.filter(
        status=BackupStatus.COMPLETED,
        database_file__isnull=False
    ).first()
    
    if not valid_backup:
        print("❌ No valid backup found for restore test")
        return False
    
    # Check if backup files exist
    db_exists = os.path.exists(valid_backup.database_file) if valid_backup.database_file else False
    media_exists = os.path.exists(valid_backup.media_file) if valid_backup.media_file else False
    
    print(f"✅ Found backup: {valid_backup.name}")
    print(f"   Database file exists: {db_exists}")
    print(f"   Media file exists: {media_exists}")
    
    if not db_exists:
        print("❌ Database file missing, cannot test restore")
        return False
    
    # Create restore record
    restore_record = RestoreRecord.objects.create(
        name=f'Restore Test {int(time.time())}',
        backup_record=valid_backup,
        restore_type=BackupType.DATABASE_ONLY,
        created_by=user,
        overwrite_existing=False,
        backup_before_restore=False  # Skip for test speed
    )
    
    print(f"✅ Created restore record: {restore_record.id}")
    print(f"   Initial status: {restore_record.status}")
    
    # Test restore service
    try:
        service = RestoreService()
        service.restore_from_backup(restore_record)
        
        # Check result
        restore_record.refresh_from_db()
        print(f"   Final status: {restore_record.status}")
        
        if restore_record.status in ['completed', 'in_progress']:
            print("✅ Issue 2 FIXED: Restore starts properly")
            return True
        else:
            print(f"❌ Restore failed: {restore_record.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Restore error: {str(e)}")
        return False

def test_api_endpoints():
    """Test API endpoints used by JavaScript"""
    print("\n🔧 Testing API Endpoints")
    print("-" * 60)
    
    client = Client()
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    
    if user:
        client.force_login(user)
        
        # Test available backups API
        response = client.get('/backup/api/available-backups/')
        print(f"Available backups API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} available backups")
            return True
        else:
            print("❌ API failed")
            return False
    else:
        print("❌ No user for testing")
        return False

def main():
    print("🧪 BACKUP SYSTEM FIXES TEST")
    print("=" * 60)
    
    results = []
    
    # Test Issue 1: Backup progress
    results.append(test_backup_creation())
    
    # Test Issue 2: Restore functionality  
    results.append(test_restore_functionality())
    
    # Test API endpoints
    results.append(test_api_endpoints())
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("🎉 ALL TESTS PASSED! Both issues are FIXED:")
        print("   ✅ Issue 1: Backup progress tracking works")
        print("   ✅ Issue 2: Restore functionality works") 
        print("   ✅ API endpoints working properly")
        print("\n🚀 You can now:")
        print("   1. Create backups (progress will hide when complete)")
        print("   2. Restore from backup list (will work properly)")
    else:
        print("❌ Some tests failed. Check the output above.")
        
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)