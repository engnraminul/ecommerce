#!/usr/bin/env python3
"""
Test script to verify backup API functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backup.models import BackupRecord
from backup.views import available_backups
from django.test import RequestFactory
from users.models import User

def test_available_backups():
    print("🧪 TESTING AVAILABLE BACKUPS API")
    print("=" * 60)
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/backup/api/available-backups/')
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('testuser', 'test@test.com', 'testpass')
    request.user = user
    
    # Call the API
    response = available_backups(request)
    print(f'API Status: {response.status_code}')
    print(f'Number of backups returned: {len(response.data)}')
    
    if response.data:
        print("\n📦 Available backups:")
        for backup in response.data:
            print(f'- {backup["name"]}')
            print(f'  DB: {backup["has_database"]}, Media: {backup["has_media"]}')
            print(f'  Type: {backup["backup_type_display"]}')
            print(f'  Size: {backup["file_size_formatted"]}')
            print()
        
        print("✅ BACKUP API IS WORKING - Valid backups found!")
    else:
        print("❌ No valid backups found")
        
        # Check what backups exist in DB
        print("\n🔍 Checking backup records in database:")
        all_backups = BackupRecord.objects.filter(status='completed').order_by('-created_at')
        for backup in all_backups:
            print(f'- {backup.name} (DB exists: {os.path.exists(backup.database_file) if backup.database_file else False}, Media exists: {os.path.exists(backup.media_file) if backup.media_file else False})')

if __name__ == '__main__':
    test_available_backups()