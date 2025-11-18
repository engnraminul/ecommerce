"""
Management command to clean up orphaned backup files
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from backups.models import Backup
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Clean up orphaned backup files (files without database records)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            help='Backup directory path (defaults to settings.BACKUP_DIRECTORY)',
        )
    
    def handle(self, *args, **options):
        backup_dir = options.get('backup_dir')
        if not backup_dir:
            backup_dir = Path(settings.BASE_DIR) / getattr(settings, 'BACKUP_DIRECTORY', 'backups_storage')
        else:
            backup_dir = Path(backup_dir)
        
        if not backup_dir.exists():
            self.stdout.write(
                self.style.ERROR(f'Backup directory does not exist: {backup_dir}')
            )
            return
        
        self.stdout.write(f'Scanning backup directory: {backup_dir}')
        
        # Get all backup files from database
        db_files = set()
        for backup in Backup.objects.all():
            if backup.database_file:
                db_files.add(Path(backup.database_file).name)
            if backup.media_file:
                db_files.add(Path(backup.media_file).name)
        
        self.stdout.write(f'Found {len(db_files)} files referenced in database')
        
        # Scan filesystem for backup files
        backup_patterns = [
            'db_backup_*.json.gz',
            'db_backup_*.json',
            'db_uploaded_*.json.gz',
            'media_backup_*.zip',
            'media_uploaded_*.zip',
            'uploaded_*.zip',
        ]
        
        fs_files = set()
        for pattern in backup_patterns:
            fs_files.update(backup_dir.glob(pattern))
        
        self.stdout.write(f'Found {len(fs_files)} backup files on filesystem')
        
        # Find orphaned files
        orphaned_files = []
        for file_path in fs_files:
            if file_path.name not in db_files:
                orphaned_files.append(file_path)
        
        if not orphaned_files:
            self.stdout.write(
                self.style.SUCCESS('No orphaned backup files found')
            )
            return
        
        self.stdout.write(f'Found {len(orphaned_files)} orphaned files:')
        
        total_size = 0
        for file_path in orphaned_files:
            file_size = file_path.stat().st_size
            total_size += file_size
            size_mb = file_size / (1024 * 1024)
            self.stdout.write(f'  - {file_path.name} ({size_mb:.1f} MB)')
        
        total_size_mb = total_size / (1024 * 1024)
        self.stdout.write(f'Total size: {total_size_mb:.1f} MB')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Dry run mode - no files were deleted')
            )
            return
        
        # Confirm deletion
        confirm = input(f'Delete {len(orphaned_files)} orphaned files? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write('Aborted')
            return
        
        # Delete orphaned files
        deleted_count = 0
        for file_path in orphaned_files:
            try:
                file_path.unlink()
                deleted_count += 1
                self.stdout.write(f'Deleted: {file_path.name}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to delete {file_path.name}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} orphaned files')
        )