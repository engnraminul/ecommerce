from django.core.management.base import BaseCommand
from backup.models import BackupRecord, BackupType
from backup.services import BackupService
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a backup manually via command line'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Name for the backup',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['database', 'media', 'full'],
            default='full',
            help='Type of backup to create (default: full)',
        )
        parser.add_argument(
            '--description',
            type=str,
            help='Optional description for the backup',
        )
        parser.add_argument(
            '--no-compress',
            action='store_true',
            help='Disable compression',
        )
        parser.add_argument(
            '--include-logs',
            action='store_true',
            help='Include log files in media backup',
        )
    
    def handle(self, *args, **options):
        """Create a manual backup"""
        backup_name = options['name']
        backup_type = options['type']
        description = options.get('description', f'Manual backup created via command line')
        
        self.stdout.write(f"Creating {backup_type} backup: {backup_name}")
        
        try:
            # Create backup record
            backup_record = BackupRecord.objects.create(
                name=backup_name,
                backup_type=backup_type,
                description=description,
                compress=not options['no_compress'],
                exclude_logs=not options['include_logs']
            )
            
            # Execute backup
            backup_service = BackupService()
            success = backup_service.create_backup(backup_record)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Backup completed successfully!")
                )
                self.stdout.write(f"Backup ID: {backup_record.id}")
                self.stdout.write(f"Total Size: {backup_record.formatted_size}")
                if backup_record.database_file:
                    self.stdout.write(f"Database: {backup_record.formatted_database_size}")
                if backup_record.media_file:
                    self.stdout.write(f"Media: {backup_record.formatted_media_size}")
                self.stdout.write(f"Duration: {backup_record.duration}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"Backup failed: {backup_record.error_message}")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating backup: {str(e)}")
            )