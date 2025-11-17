"""
Management command to reprocess uploaded backups that have missing database or media files
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from backups.models import Backup
from backups.services import BackupUploadService
from pathlib import Path
import zipfile
import os


class Command(BaseCommand):
    help = 'Reprocess uploaded backups that have missing database or media file paths'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-id',
            type=int,
            help='Specific backup ID to reprocess',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reprocess all problematic uploaded backups',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting backup reprocessing...'))
        
        # Find backups to process
        if options['backup_id']:
            backups = Backup.objects.filter(id=options['backup_id'])
        elif options['all']:
            # Find full backups missing database or media files
            backups = Backup.objects.filter(
                backup_type='full'
            ).filter(
                models.Q(database_file__isnull=True) | 
                models.Q(media_file__isnull=True) |
                models.Q(database_file='') |
                models.Q(media_file='')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --backup-id or --all')
            )
            return
        
        if not backups.exists():
            self.stdout.write(
                self.style.WARNING('No backups found to process')
            )
            return
        
        self.stdout.write(f'Found {backups.count()} backup(s) to process')
        
        processed = 0
        errors = 0
        
        for backup in backups:
            try:
                self.stdout.write(f'\nProcessing: {backup.name} (ID: {backup.id})')
                
                # Check if we have a file to process
                source_file = backup.database_file or backup.media_file
                if not source_file or not os.path.exists(source_file):
                    self.stdout.write(
                        self.style.ERROR(f'  No valid source file found for backup {backup.id}')
                    )
                    errors += 1
                    continue
                
                # Check if it's a zip file
                if not source_file.endswith('.zip'):
                    self.stdout.write(
                        self.style.WARNING(f'  Backup {backup.id} is not a zip file, skipping')
                    )
                    continue
                
                # Analyze the zip contents
                try:
                    with zipfile.ZipFile(source_file, 'r') as zipf:
                        file_list = zipf.namelist()
                        self.stdout.write(f'  Zip contains: {", ".join(file_list)}')
                        
                        # Check for database and media files
                        db_files = []
                        media_files = []
                        
                        for file_name in file_list:
                            name_lower = file_name.lower()
                            if (name_lower.endswith(('.json.gz', '.sql', '.sql.gz', '.dump')) or 
                                'db_backup' in name_lower or 'database' in name_lower):
                                db_files.append(file_name)
                            elif (name_lower.endswith('.zip') and 'media' in name_lower) or 'media_backup' in name_lower:
                                media_files.append(file_name)
                        
                        self.stdout.write(f'  Database files: {db_files}')
                        self.stdout.write(f'  Media files: {media_files}')
                        
                        if not db_files and not media_files:
                            self.stdout.write(
                                self.style.WARNING(f'  No recognizable backup components found')
                            )
                            continue
                        
                        if not options['dry_run']:
                            # Reprocess the backup
                            service = BackupUploadService()
                            original_db = backup.database_file
                            original_media = backup.media_file
                            
                            service._process_full_backup_upload(backup, Path(source_file))
                            backup.save()
                            
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✅ Reprocessed successfully')
                            )
                            self.stdout.write(f'     Database: {original_db} → {backup.database_file}')
                            self.stdout.write(f'     Media: {original_media} → {backup.media_file}')
                            processed += 1
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✅ Would reprocess (dry run)')
                            )
                            processed += 1
                        
                except zipfile.BadZipFile:
                    self.stdout.write(
                        self.style.ERROR(f'  Invalid zip file: {source_file}')
                    )
                    errors += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing backup {backup.id}: {e}')
                )
                errors += 1
        
        self.stdout.write(f'\n{self.style.SUCCESS("Processing complete:")}')
        self.stdout.write(f'  Processed: {processed}')
        self.stdout.write(f'  Errors: {errors}')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('This was a dry run. Use without --dry-run to apply changes.')
            )