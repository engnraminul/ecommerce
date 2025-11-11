"""
Django management command for safely restoring backups with data integrity protection
"""
import os
import sys
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from backups.models import Backup, BackupRestore, BackupLog, BackupSettings
from backups.utils import backup_utils
import logging


class Command(BaseCommand):
    help = 'Safely restore a backup with optional pre-restore backup and selective restoration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_id',
            type=str,
            help='ID of the backup to restore'
        )
        
        parser.add_argument(
            '--mode',
            type=str,
            choices=['full', 'selective', 'merge'],
            default='full',
            help='Restoration mode (default: full)'
        )
        
        parser.add_argument(
            '--database',
            action='store_true',
            default=True,
            help='Restore database (default: True)'
        )
        
        parser.add_argument(
            '--no-database',
            action='store_true',
            help='Skip database restoration'
        )
        
        parser.add_argument(
            '--media',
            action='store_true',
            default=True,
            help='Restore media files (default: True)'
        )
        
        parser.add_argument(
            '--no-media',
            action='store_true',
            help='Skip media restoration'
        )
        
        parser.add_argument(
            '--models',
            type=str,
            help='Comma-separated list of models to restore (app.model format)'
        )
        
        parser.add_argument(
            '--exclude-models',
            type=str,
            help='Comma-separated list of models to exclude from restoration'
        )
        
        parser.add_argument(
            '--pre-backup',
            action='store_true',
            default=True,
            help='Create backup before restoration (default: True)'
        )
        
        parser.add_argument(
            '--no-pre-backup',
            action='store_true',
            help='Skip pre-restoration backup'
        )
        
        parser.add_argument(
            '--verify-before',
            action='store_true',
            default=True,
            help='Verify backup integrity before restoration (default: True)'
        )
        
        parser.add_argument(
            '--no-verify',
            action='store_true',
            help='Skip backup verification'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restoration without confirmation prompts'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually doing it'
        )
        
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Minimize output'
        )
        
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Quick restore mode (faster but skips some safety checks)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )
    
    def handle(self, *args, **options):
        # Setup logging
        self.setup_logging(options)
        
        # Validate and get backup
        backup = self.get_backup(options['backup_id'])
        
        # Validate options
        self.validate_options(options, backup)
        
        # Show restoration plan
        if not options.get('quiet'):
            self.show_restoration_plan(backup, options)
        
        # Confirm restoration unless forced or dry run
        if not options.get('force') and not options.get('dry_run'):
            if not self.confirm_restoration(backup, options):
                self.stdout.write(self.style.WARNING("Restoration cancelled by user"))
                return
        
        # Dry run mode
        if options.get('dry_run'):
            self.perform_dry_run(backup, options)
            return
        
        # Create restore instance
        restore = self.create_restore_instance(backup, options)
        
        try:
            self.log_info(f"Starting restoration of backup: {backup.name}")
            
            # Start restore process
            restore.mark_as_started()
            self.log_restore(restore, 'info', "Restoration process started")
            
            # Verify backup integrity if requested
            if options.get('verify_before', True) and not options.get('no_verify'):
                if not self.verify_backup_before_restore(backup, restore):
                    raise CommandError("Backup verification failed")
            
            # Create pre-restore backup if requested
            pre_restore_backup = None
            if options.get('pre_backup', True) and not options.get('no_pre_backup'):
                pre_restore_backup = self.create_pre_restore_backup(restore)
                if not pre_restore_backup:
                    raise CommandError("Pre-restore backup failed")
            
            # Extract backup if compressed
            with tempfile.TemporaryDirectory() as temp_dir:
                extract_dir = self.extract_backup(backup, temp_dir)
                
                # Perform restoration
                success = self.perform_restoration(backup, restore, extract_dir, options)
                
                if success:
                    restore.mark_as_completed()
                    self.log_restore(restore, 'info', "Restoration completed successfully")
                    self.log_success(f"Backup restored successfully: {backup.name}")
                    self.display_restore_summary(restore, pre_restore_backup)
                else:
                    restore.mark_as_failed("Restoration process failed")
                    self.log_restore(restore, 'error', "Restoration process failed")
                    raise CommandError("Restoration process failed")
        
        except Exception as e:
            error_msg = f"Restoration failed: {str(e)}"
            restore.mark_as_failed(error_msg)
            self.log_restore(restore, 'error', error_msg, exception_info=str(e))
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
    
    def get_backup(self, backup_id):
        """Get and validate backup instance"""
        try:
            backup = Backup.objects.get(id=backup_id)
            
            if backup.status != 'completed':
                raise CommandError(f"Backup {backup_id} is not in completed state (status: {backup.status})")
            
            if not backup.can_restore:
                raise CommandError(f"Backup {backup_id} cannot be restored")
            
            return backup
        
        except Backup.DoesNotExist:
            raise CommandError(f"Backup with ID {backup_id} not found")
    
    def validate_options(self, options, backup):
        """Validate command options"""
        # Check restoration type consistency
        restore_database = not options.get('no_database', False)
        restore_media = not options.get('no_media', False)
        
        if not restore_database and not restore_media:
            raise CommandError("Must restore at least database or media")
        
        # Validate model selection
        if options.get('models') and options.get('exclude_models'):
            raise CommandError("Cannot specify both --models and --exclude-models")
        
        if options.get('models'):
            models = [m.strip() for m in options['models'].split(',')]
            self.validate_model_names(models)
        
        if options.get('exclude_models'):
            models = [m.strip() for m in options['exclude_models'].split(',')]
            self.validate_model_names(models)
        
        # Check backup content compatibility
        if restore_database and backup.backup_type == 'media':
            raise CommandError("Cannot restore database from media-only backup")
        
        if restore_media and backup.backup_type == 'database':
            raise CommandError("Cannot restore media from database-only backup")
    
    def validate_model_names(self, models):
        """Validate model names format"""
        from django.apps import apps
        
        for model_name in models:
            if '.' not in model_name:
                raise CommandError(f"Invalid model format: {model_name} (use app.model)")
            
            try:
                app_label, model = model_name.split('.', 1)
                apps.get_model(app_label, model)
            except Exception as e:
                raise CommandError(f"Invalid model {model_name}: {str(e)}")
    
    def show_restoration_plan(self, backup, options):
        """Show what will be restored"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.HTTP_INFO("RESTORATION PLAN"))
        self.stdout.write("="*60)
        self.stdout.write(f"Backup ID: {backup.id}")
        self.stdout.write(f"Backup Name: {backup.name}")
        self.stdout.write(f"Backup Type: {backup.get_backup_type_display()}")
        self.stdout.write(f"Created: {backup.created_at}")
        self.stdout.write(f"Size: {backup.formatted_size}")
        
        # Show what will be restored
        restore_items = []
        if not options.get('no_database', False):
            restore_items.append("Database")
        if not options.get('no_media', False) and backup.include_media:
            restore_items.append("Media Files")
        
        self.stdout.write(f"Items to restore: {', '.join(restore_items)}")
        
        # Show model selection if applicable
        if options.get('models'):
            models = [m.strip() for m in options['models'].split(',')]
            self.stdout.write(f"Selected models: {', '.join(models)}")
        elif options.get('exclude_models'):
            models = [m.strip() for m in options['exclude_models'].split(',')]
            self.stdout.write(f"Excluded models: {', '.join(models)}")
        
        # Show safety measures
        safety_measures = []
        if options.get('pre_backup', True) and not options.get('no_pre_backup'):
            safety_measures.append("Pre-restore backup")
        if options.get('verify_before', True) and not options.get('no_verify'):
            safety_measures.append("Integrity verification")
        
        if safety_measures:
            self.stdout.write(f"Safety measures: {', '.join(safety_measures)}")
        
        self.stdout.write("="*60)
    
    def confirm_restoration(self, backup, options):
        """Confirm restoration with user"""
        self.stdout.write(self.style.WARNING("\nWARNING: This operation will modify your database and/or media files!"))
        
        if not options.get('pre_backup', True) or options.get('no_pre_backup'):
            self.stdout.write(self.style.ERROR("No pre-restore backup will be created!"))
        
        response = input("\nDo you want to proceed with the restoration? (yes/no): ")
        return response.lower() in ['yes', 'y']
    
    def perform_dry_run(self, backup, options):
        """Perform a dry run showing what would be restored"""
        self.stdout.write(self.style.HTTP_INFO("\nDRY RUN MODE - No changes will be made"))
        self.stdout.write("="*60)
        
        # Show backup contents
        backup_files = backup.get_backup_files()
        
        database_files = backup_files.filter(file_type__in=['database', 'fixture'])
        media_files = backup_files.filter(file_type='media')
        
        if not options.get('no_database', False) and database_files.exists():
            self.stdout.write(f"\nDatabase files to restore ({database_files.count()}):")
            for bf in database_files:
                self.stdout.write(f"  - {bf.filename} ({bf.formatted_size}, {bf.record_count} records)")
        
        if not options.get('no_media', False) and media_files.exists():
            self.stdout.write(f"\nMedia files to restore ({media_files.count()}):")
            for bf in media_files[:10]:  # Show first 10
                self.stdout.write(f"  - {bf.filename} ({bf.formatted_size})")
            if media_files.count() > 10:
                self.stdout.write(f"  ... and {media_files.count() - 10} more files")
        
        self.stdout.write("\n" + "="*60)
    
    def create_restore_instance(self, backup, options):
        """Create restore tracking instance"""
        restore_mode = options.get('mode', 'full')
        
        # Parse model selection
        selected_models = []
        exclude_models = []
        
        if options.get('models'):
            selected_models = [m.strip() for m in options['models'].split(',')]
        
        if options.get('exclude_models'):
            exclude_models = [m.strip() for m in options['exclude_models'].split(',')]
        
        restore = BackupRestore.objects.create(
            backup=backup,
            restore_mode=restore_mode,
            restore_database=not options.get('no_database', False),
            restore_media=not options.get('no_media', False),
            selected_models=selected_models,
            exclude_models=exclude_models
        )
        
        return restore
    
    def verify_backup_before_restore(self, backup, restore):
        """Verify backup integrity before restoration"""
        try:
            self.log_info("Verifying backup integrity...")
            restore.current_operation = "Verifying backup integrity..."
            restore.save()
            
            # Get backup files for verification
            backup_files = []
            for bf in backup.backup_files.all():
                backup_files.append({
                    'path': bf.backup_path,
                    'checksum': bf.checksum
                })
            
            verify_results = backup_utils.verify_backup_integrity(backup_files)
            
            if verify_results['success']:
                self.log_info(f"Backup verification passed: {verify_results['verified_files']} files verified")
                return True
            else:
                self.log_error(f"Backup verification failed: {verify_results['failed_files']} files failed")
                for error in verify_results['errors']:
                    self.log_restore(restore, 'error', error)
                return False
        
        except Exception as e:
            self.log_error(f"Backup verification failed: {str(e)}")
            return False
    
    def create_pre_restore_backup(self, restore):
        """Create a backup before restoration"""
        try:
            self.log_info("Creating pre-restore backup...")
            restore.current_operation = "Creating pre-restore backup..."
            restore.save()
            
            # Create pre-restore backup using the create_backup_safe command
            from django.core.management import call_command
            from io import StringIO
            
            # Capture output
            out = StringIO()
            
            # Create backup
            call_command(
                'create_backup_safe',
                name=f"PreRestore_{restore.backup.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                description=f"Automatic backup before restoring {restore.backup.name}",
                type='full',
                quiet=True,
                stdout=out
            )
            
            # Get the created backup (latest one)
            pre_backup = Backup.objects.filter(
                name__startswith=f"PreRestore_{restore.backup.name}"
            ).latest('created_at')
            
            restore.pre_restore_backup = pre_backup
            restore.save()
            
            self.log_info(f"Pre-restore backup created: {pre_backup.id}")
            return pre_backup
        
        except Exception as e:
            self.log_error(f"Pre-restore backup failed: {str(e)}")
            return None
    
    def extract_backup(self, backup, temp_dir):
        """Extract backup if it's compressed"""
        if backup.compress_backup and backup.backup_path.endswith(('.zip', '.tar.gz', '.tgz')):
            self.log_info("Extracting compressed backup...")
            
            extract_dir = os.path.join(temp_dir, f"extracted_{backup.id}")
            os.makedirs(extract_dir)
            
            if backup_utils.extract_backup(backup.backup_path, extract_dir):
                # Find the actual backup directory inside extracted content
                contents = os.listdir(extract_dir)
                if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                    return os.path.join(extract_dir, contents[0])
                return extract_dir
            else:
                raise CommandError("Failed to extract backup archive")
        else:
            # Backup is not compressed, use path directly
            return backup.backup_path
    
    def perform_restoration(self, backup, restore, backup_dir, options):
        """Perform the actual restoration"""
        success = True
        
        try:
            # Database restoration
            if restore.restore_database and backup.backup_type in ['full', 'database']:
                self.log_info("Restoring database...")
                restore.current_operation = "Restoring database..."
                restore.save()
                
                # Prepare model list for selective restore
                selective_models = None
                if restore.selected_models:
                    selective_models = restore.selected_models
                elif restore.exclude_models:
                    all_models = backup_utils.get_backup_order()
                    selective_models = [m for m in all_models if m not in restore.exclude_models]
                
                db_results = backup_utils.restore_database(
                    backup_dir, 
                    backup_instance=restore, 
                    selective_models=selective_models
                )
                
                if db_results['success']:
                    restore.restored_records = db_results['restored_records']
                    self.log_info(f"Database restoration completed: {db_results['restored_records']:,} records restored")
                else:
                    self.log_error("Database restoration failed")
                    for error in db_results['errors']:
                        self.log_restore(restore, 'error', error)
                    success = False
            
            # Media restoration
            if success and restore.restore_media and backup.backup_type in ['full', 'media']:
                self.log_info("Restoring media files...")
                restore.current_operation = "Restoring media files..."
                restore.save()
                
                media_results = backup_utils.restore_media(backup_dir, backup_instance=restore)
                
                if media_results['success']:
                    restore.restored_files = media_results['restored_files']
                    restore.skipped_files = media_results['skipped_files']
                    self.log_info(f"Media restoration completed: {media_results['restored_files']} files restored")
                else:
                    self.log_error("Media restoration failed")
                    for error in media_results['errors']:
                        self.log_restore(restore, 'error', error)
                    success = False
        
        except Exception as e:
            self.log_error(f"Restoration process failed: {str(e)}")
            success = False
        
        return success
    
    def display_restore_summary(self, restore, pre_restore_backup=None):
        """Display restoration summary"""
        if not self.quiet:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS("RESTORATION COMPLETED SUCCESSFULLY"))
            self.stdout.write("="*60)
            self.stdout.write(f"Restore ID: {restore.id}")
            self.stdout.write(f"Backup Name: {restore.backup.name}")
            self.stdout.write(f"Restore Mode: {restore.get_restore_mode_display()}")
            self.stdout.write(f"Status: {restore.status}")
            self.stdout.write(f"Duration: {restore.duration_seconds}s")
            
            if restore.restored_records:
                self.stdout.write(f"Database Records Restored: {restore.restored_records:,}")
            if restore.restored_files:
                self.stdout.write(f"Media Files Restored: {restore.restored_files}")
            if restore.skipped_files:
                self.stdout.write(f"Files Skipped: {restore.skipped_files}")
            
            if pre_restore_backup:
                self.stdout.write(f"Pre-restore Backup: {pre_restore_backup.id}")
                self.stdout.write(f"Pre-restore Backup Path: {pre_restore_backup.backup_path}")
            
            self.stdout.write("="*60)
            
            if pre_restore_backup:
                self.stdout.write(self.style.HTTP_INFO(
                    f"\nIMPORTANT: A backup was created before restoration (ID: {pre_restore_backup.id})"
                ))
                self.stdout.write("You can use this backup to rollback if needed:")
                self.stdout.write(f"python manage.py restore_backup_safe {pre_restore_backup.id}")
    
    def log_restore(self, restore, level, message, operation=None, exception_info=None):
        """Log message to restore log"""
        BackupLog.objects.create(
            backup=restore.backup,
            level=level,
            message=f"RESTORE: {message}",
            operation=operation or restore.current_operation,
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