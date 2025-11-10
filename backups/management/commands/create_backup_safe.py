"""
Django management command for creating comprehensive, safe backups
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from backups.models import Backup, BackupFile, BackupLog, BackupSettings
from backups.utils import backup_utils
import logging


class Command(BaseCommand):
    help = 'Create a comprehensive backup of database and media files with foreign key safety'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            help='Name for the backup (auto-generated if not provided)'
        )
        
        parser.add_argument(
            '--type',
            type=str,
            choices=['full', 'database', 'media'],
            default='full',
            help='Type of backup to create (default: full)'
        )
        
        parser.add_argument(
            '--description',
            type=str,
            help='Description for the backup'
        )
        
        parser.add_argument(
            '--compress',
            action='store_true',
            default=True,
            help='Compress the backup (default: True)'
        )
        
        parser.add_argument(
            '--no-compress',
            action='store_true',
            help='Disable compression'
        )
        
        parser.add_argument(
            '--include-media',
            action='store_true',
            default=True,
            help='Include media files (default: True for full backup)'
        )
        
        parser.add_argument(
            '--no-media',
            action='store_true',
            help='Exclude media files'
        )
        
        parser.add_argument(
            '--include-static',
            action='store_true',
            help='Include static files'
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Custom output directory (uses BACKUP_ROOT if not specified)'
        )
        
        parser.add_argument(
            '--verify',
            action='store_true',
            default=True,
            help='Verify backup integrity (default: True)'
        )
        
        parser.add_argument(
            '--no-verify',
            action='store_true',
            help='Skip backup verification'
        )
        
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Minimize output'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )
    
    def handle(self, *args, **options):
        # Setup logging
        self.setup_logging(options)
        
        # Validate options
        self.validate_options(options)
        
        # Create backup instance
        backup = self.create_backup_instance(options)
        
        try:
            self.log_info(f"Starting backup: {backup.name}")
            
            # Start backup process
            backup.mark_as_started()
            self.log_backup(backup, 'info', "Backup process started")
            
            # Create temporary working directory
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_dir = os.path.join(temp_dir, f"backup_{backup.id}")
                os.makedirs(backup_dir)
                
                # Perform backup based on type
                success = self.perform_backup(backup, backup_dir, options)
                
                if success:
                    # Compress if requested (default is True unless --no-compress is specified)
                    if options.get('compress', True) and not options.get('no_compress', False):
                        success = self.compress_backup(backup, backup_dir, options)
                    
                    # Verify if requested
                    if success and options.get('verify', True) and not options.get('no_verify'):
                        success = self.verify_backup(backup, options)
                    
                    if success:
                        backup.mark_as_completed()
                        self.log_backup(backup, 'info', "Backup completed successfully")
                        self.log_success(f"Backup completed successfully: {backup.backup_path}")
                        self.display_backup_summary(backup)
                    else:
                        backup.mark_as_failed("Verification failed")
                        self.log_backup(backup, 'error', "Backup verification failed")
                        raise CommandError("Backup verification failed")
                else:
                    backup.mark_as_failed("Backup process failed")
                    self.log_backup(backup, 'error', "Backup process failed")
                    raise CommandError("Backup process failed")
        
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            backup.mark_as_failed(error_msg)
            self.log_backup(backup, 'error', error_msg, exception_info=str(e))
            self.log_error(error_msg)
            raise CommandError(error_msg)
    
    def setup_logging(self, options):
        """Setup logging configuration"""
        log_level = logging.WARNING
        if options.get('verbose'):
            log_level = logging.DEBUG
        elif not options.get('quiet'):
            log_level = logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_options(self, options):
        """Validate command options"""
        # Check backup type consistency
        backup_type = options.get('type', 'full')
        
        if backup_type == 'database' and options.get('include_media'):
            self.log_warning("--include-media ignored for database-only backup")
        
        if backup_type == 'media' and not options.get('include_media', True):
            raise CommandError("Cannot exclude media from media-only backup")
        
        # Check output directory
        output_dir = options.get('output_dir')
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                raise CommandError(f"Cannot create output directory {output_dir}: {str(e)}")
    
    def create_backup_instance(self, options):
        """Create and configure backup instance"""
        backup_type = options.get('type', 'full')
        
        # Generate name if not provided
        name = options.get('name')
        if not name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"Backup_{backup_type}_{timestamp}"
        
        # Determine backup configuration
        include_media = (backup_type in ['full', 'media']) and not options.get('no_media')
        if backup_type == 'database':
            include_media = False
        
        compress_backup = options.get('compress', True) and not options.get('no_compress')
        
        # Create backup instance
        backup = Backup.objects.create(
            name=name,
            description=options.get('description', ''),
            backup_type=backup_type,
            include_media=include_media,
            include_staticfiles=options.get('include_static', False),
            compress_backup=compress_backup,
            preserve_foreign_keys=True,
        )
        
        # Set system information
        import django
        import sys
        backup.django_version = django.get_version()
        backup.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        backup.database_name = settings.DATABASES['default']['NAME']
        backup.save()
        
        return backup
    
    def perform_backup(self, backup, backup_dir, options):
        """Perform the actual backup process"""
        success = True
        total_files = 0
        total_size = 0
        
        try:
            # Database backup
            if backup.backup_type in ['full', 'database']:
                self.log_info("Creating database backup...")
                backup.current_operation = "Creating database backup..."
                backup.save()
                
                db_results = backup_utils.create_database_backup(backup_dir, backup)
                
                if db_results['success']:
                    backup.total_tables = db_results['total_tables']
                    backup.total_records = db_results['total_records']
                    
                    # Create BackupFile entries for database files
                    for file_info in db_results['files']:
                        BackupFile.objects.create(
                            backup=backup,
                            filename=os.path.basename(file_info['path']),
                            original_path=file_info['path'],
                            backup_path=file_info['path'],
                            file_type='database' if 'schema' not in file_info['model'] else 'fixture',
                            file_size=file_info['file_size'],
                            checksum=file_info['checksum'],
                            model_name=file_info['model'],
                            record_count=file_info.get('record_count', 0)
                        )
                    
                    total_files += len(db_results['files'])
                    total_size += sum(f['file_size'] for f in db_results['files'])
                    
                    self.log_info(f"Database backup completed: {db_results['total_tables']} tables, {db_results['total_records']} records")
                else:
                    self.log_error("Database backup failed")
                    for error in db_results['errors']:
                        self.log_backup(backup, 'error', error)
                    success = False
            
            # Media backup
            if success and backup.backup_type in ['full', 'media'] and backup.include_media:
                self.log_info("Creating media backup...")
                backup.current_operation = "Creating media backup..."
                backup.save()
                
                media_results = backup_utils.create_media_backup(backup_dir, backup)
                
                if media_results['success']:
                    # Create BackupFile entries for media files
                    for file_info in media_results['files']:
                        BackupFile.objects.create(
                            backup=backup,
                            filename=os.path.basename(file_info['path']),
                            original_path=file_info['original_path'],
                            backup_path=file_info['path'],
                            file_type='media',
                            file_size=file_info['file_size'],
                            checksum=file_info['checksum']
                        )
                    
                    total_files += media_results['total_files']
                    total_size += media_results['total_size']
                    
                    self.log_info(f"Media backup completed: {media_results['total_files']} files")
                else:
                    self.log_error("Media backup failed")
                    for error in media_results['errors']:
                        self.log_backup(backup, 'error', error)
                    success = False
            
            # Update backup statistics
            backup.total_files = total_files
            backup.backup_size = total_size
            
            # Set backup path (will be updated during compression or copying)
            if success and (options.get('no_compress', False) or not options.get('compress', True)):
                # If not compressing, copy to permanent location
                permanent_dir = os.path.join(getattr(settings, 'BACKUP_ROOT', backup_utils.backup_root), f"backup_{backup.id}")
                os.makedirs(os.path.dirname(permanent_dir), exist_ok=True)
                shutil.copytree(backup_dir, permanent_dir)
                backup.backup_path = permanent_dir
                backup.save()
        
        except Exception as e:
            self.log_error(f"Backup process failed: {str(e)}")
            success = False
        
        return success
    
    def compress_backup(self, backup, backup_dir, options):
        """Compress the backup directory"""
        try:
            self.log_info("Compressing backup...")
            
            # Determine output location
            output_dir = options.get('output_dir') or getattr(settings, 'BACKUP_ARCHIVE_ROOT', None) or getattr(settings, 'BACKUP_ROOT', backup_utils.backup_root)
            os.makedirs(output_dir, exist_ok=True)
            
            # Create compressed file path
            timestamp = backup.created_at.strftime('%Y%m%d_%H%M%S')
            archive_name = f"{backup.name}_{timestamp}.tar.gz"
            archive_path = os.path.join(output_dir, archive_name)
            
            # Compress
            compress_results = backup_utils.compress_backup(backup_dir, archive_path, backup)
            
            if compress_results['success']:
                backup.backup_path = archive_path
                backup.compressed_size = compress_results['compressed_size']
                backup.backup_size = compress_results['original_size']
                backup.save()
                
                self.log_info(f"Backup compressed: {backup.formatted_size} -> {backup.formatted_compressed_size} ({backup.compression_ratio}% reduction)")
                return True
            else:
                for error in compress_results['errors']:
                    self.log_backup(backup, 'error', error)
                return False
        
        except Exception as e:
            self.log_error(f"Compression failed: {str(e)}")
            return False
    
    def verify_backup(self, backup, options):
        """Verify backup integrity"""
        try:
            self.log_info("Verifying backup integrity...")
            
            backup.current_operation = "Verifying backup integrity..."
            backup.progress_percentage = 95
            backup.save()
            
            # Get backup files info
            backup_files = []
            for bf in backup.backup_files.all():
                backup_files.append({
                    'path': bf.backup_path,
                    'checksum': bf.checksum
                })
            
            # Verify integrity
            verify_results = backup_utils.verify_backup_integrity(backup_files)
            
            if verify_results['success']:
                self.log_info(f"Backup verification completed: {verify_results['verified_files']} files verified")
                
                # Mark all files as verified
                backup.backup_files.update(is_verified=True)
                return True
            else:
                self.log_error(f"Backup verification failed: {verify_results['failed_files']} files failed")
                for error in verify_results['errors']:
                    self.log_backup(backup, 'error', error)
                return False
        
        except Exception as e:
            self.log_error(f"Verification failed: {str(e)}")
            return False
    
    def display_backup_summary(self, backup):
        """Display backup summary"""
        if not self.quiet:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS("BACKUP COMPLETED SUCCESSFULLY"))
            self.stdout.write("="*60)
            self.stdout.write(f"Backup ID: {backup.id}")
            self.stdout.write(f"Name: {backup.name}")
            self.stdout.write(f"Type: {backup.get_backup_type_display()}")
            self.stdout.write(f"Status: {backup.status}")
            self.stdout.write(f"Duration: {backup.duration_formatted}")
            self.stdout.write(f"Total Files: {backup.total_files:,}")
            if backup.backup_type in ['full', 'database']:
                self.stdout.write(f"Database Tables: {backup.total_tables}")
                self.stdout.write(f"Database Records: {backup.total_records:,}")
            self.stdout.write(f"Original Size: {backup.formatted_size}")
            if backup.compress_backup and backup.compressed_size:
                self.stdout.write(f"Compressed Size: {backup.formatted_compressed_size}")
                self.stdout.write(f"Compression Ratio: {backup.compression_ratio}%")
            self.stdout.write(f"Backup Path: {backup.backup_path}")
            self.stdout.write("="*60)
    
    def log_backup(self, backup, level, message, operation=None, exception_info=None):
        """Log message to backup log"""
        BackupLog.objects.create(
            backup=backup,
            level=level,
            message=message,
            operation=operation or backup.current_operation,
            exception_info=exception_info or ''
        )
    
    def log_info(self, message):
        """Log info message"""
        self.logger.info(message)
        if not getattr(self, 'quiet', False):
            self.stdout.write(self.style.SUCCESS(f"[INFO] {message}"))
    
    def log_warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
        self.stdout.write(self.style.WARNING(f"[WARNING] {message}"))
    
    def log_error(self, message):
        """Log error message"""
        self.logger.error(message)
        self.stdout.write(self.style.ERROR(f"[ERROR] {message}"))
    
    def log_success(self, message):
        """Log success message"""
        self.logger.info(message)
        if not getattr(self, 'quiet', False):
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] {message}"))
    
    @property
    def quiet(self):
        """Check if quiet mode is enabled"""
        return getattr(self, '_quiet', False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = None