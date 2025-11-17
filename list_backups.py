#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backups.models import Backup

print("=== Current Backups ===")
backups = Backup.objects.all().order_by('-created_at')

if not backups:
    print("No backups found.")
else:
    for backup in backups:
        print(f"ID: {backup.id}")
        print(f"Name: \"{backup.name}\"")
        print(f"Type: {backup.backup_type}")
        print(f"Status: {backup.status}")
        print(f"Created: {backup.created_at}")
        print(f"Size: {backup.formatted_size}")
        if backup.database_file:
            print(f"Database file: {backup.database_file}")
        if backup.media_file:
            print(f"Media file: {backup.media_file}")
        print(f"Can restore: {backup.can_restore}")
        print("---")

print(f"\nTotal backups: {backups.count()}")