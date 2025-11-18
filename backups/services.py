import os
import subprocess
import zipfile
import shutil
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.db import transaction, connection
from django.utils import timezone
from .models import Backup, RestoreLog
import json

logger = logging.getLogger(__name__)


class BackupService:
    """Service for creating backups of database and media files"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BASE_DIR) / getattr(settings, 'BACKUP_DIRECTORY', 'backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # MySQL settings from Django configuration
        self.db_settings = settings.DATABASES['default']
        self.mysql_path = getattr(settings, 'BACKUP_MYSQL_PATH', 'mysqldump')
        
        # Compression level
        self.compression_level = getattr(settings, 'BACKUP_COMPRESSION_LEVEL', 6)
    
    def create_backup(self, backup_type='full', name=None, user=None):
        """Create a new backup"""
        if not name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"backup_{backup_type}_{timestamp}"
        
        # Create backup record
        backup = Backup.objects.create(
            name=name,
            backup_type=backup_type,
            status='creating',
            created_by=user,
            compression_level=self.compression_level
        )
        
        try:
            if backup_type in ['database', 'full']:
                self._backup_database(backup)
            
            if backup_type in ['media', 'full']:
                self._backup_media(backup)
            
            self._finalize_backup(backup)
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            backup.status = 'failed'
            backup.error_message = str(e)
            backup.save()
            raise
        
        return backup
    
    def _backup_database(self, backup):
        """Create database backup using Django's dumpdata command"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"db_backup_{timestamp}.json"
        filepath = self.backup_dir / filename
        
        try:
            # Use Django's dumpdata command to create a backup
            from django.core.management import call_command
            from io import StringIO
            
            # Capture the output
            output = StringIO()
            
            # Export all data except sessions and admin logs
            call_command(
                'dumpdata',
                '--indent=2',
                '--exclude=sessions',
                '--exclude=admin.logentry',
                '--exclude=contenttypes',
                '--exclude=auth.permission',
                stdout=output
            )
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())
            
            # Compress the JSON file
            compressed_filepath = filepath.with_suffix('.json.gz')
            self._compress_file(filepath, compressed_filepath)
            
            # Remove uncompressed file
            filepath.unlink()
            
            # Update backup record
            backup.database_file = str(compressed_filepath)
            backup.database_size = compressed_filepath.stat().st_size
            backup.save()
            
            logger.info(f"Database backup created: {compressed_filepath}")
            
        except Exception as e:
            # Clean up partial files
            if filepath.exists():
                filepath.unlink()
            if 'compressed_filepath' in locals() and compressed_filepath.exists():
                compressed_filepath.unlink()
            raise Exception(f"Database backup failed: {str(e)}")
    
    def _backup_media(self, backup):
        """Create media files backup"""
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            logger.warning("Media directory does not exist")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"media_backup_{timestamp}.zip"
        filepath = self.backup_dir / filename
        
        try:
            total_size = 0
            file_count = 0
            
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zipf:
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.exists():
                            # Calculate relative path from media root
                            arcname = file_path.relative_to(media_root)
                            zipf.write(file_path, arcname)
                            total_size += file_path.stat().st_size
                            file_count += 1
            
            # Update backup record
            backup.media_file = str(filepath)
            backup.media_size = filepath.stat().st_size
            backup.file_count = file_count
            backup.save()
            
            logger.info(f"Media backup created: {filepath} ({file_count} files, {total_size} bytes)")
            
        except Exception as e:
            # Clean up partial files
            if filepath.exists():
                filepath.unlink()
            raise Exception(f"Media backup failed: {str(e)}")
    
    def _compress_file(self, input_path, output_path):
        """Compress a file using gzip"""
        import gzip
        with open(input_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb', compresslevel=self.compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _finalize_backup(self, backup):
        """Finalize backup by updating total size and status"""
        total_size = (backup.database_size or 0) + (backup.media_size or 0)
        
        backup.total_size = total_size
        backup.status = 'completed'
        backup.completed_at = timezone.now()
        backup.save()
        
        logger.info(f"Backup completed: {backup.name} ({backup.formatted_size})")
    
    def cleanup_old_backups(self, retention_days=None):
        """Clean up old backup files based on retention policy"""
        if retention_days is None:
            retention_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        old_backups = Backup.objects.filter(created_at__lt=cutoff_date)
        
        deleted_count = 0
        for backup in old_backups:
            try:
                # The delete() method now automatically handles file deletion via signals
                backup.delete()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete backup {backup.id}: {str(e)}")
        
        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count


class RestoreService:
    """Service for restoring backups safely"""
    
    def __init__(self):
        self.db_settings = settings.DATABASES['default']
        self.media_root = Path(settings.MEDIA_ROOT)
        self.mysql_path = getattr(settings, 'BACKUP_MYSQL_PATH', 'mysql')
    
    def restore_backup(self, backup, restore_type=None, user=None, validate_only=False):
        """Restore a backup with validation and safety checks"""
        if restore_type is None:
            restore_type = backup.backup_type
        
        # Create restore log
        restore_log = RestoreLog.objects.create(
            backup=backup,
            restored_by=user,
            restore_type=restore_type
        )
        
        try:
            # Pre-restore validation
            validation_result = self._validate_restore(backup, restore_type)
            restore_log.validation_passed = validation_result['valid']
            restore_log.validation_notes = validation_result['notes']
            restore_log.save()
            
            if not validation_result['valid']:
                raise Exception(f"Validation failed: {validation_result['notes']}")
            
            if validate_only:
                return restore_log
            
            # Create pre-restore backup if specified
            if getattr(settings, 'BACKUP_CREATE_PRE_RESTORE_BACKUP', True):
                self._create_pre_restore_backup(user)
            
            # Perform restore
            if restore_type in ['database', 'full'] and backup.database_file:
                self._restore_database(backup, restore_log)
            
            if restore_type in ['media', 'full'] and backup.media_file:
                self._restore_media(backup, restore_log)
            
            # Finalize restore
            restore_log.success = True
            restore_log.completed_at = timezone.now()
            restore_log.save()
            
            # Update backup restoration tracking
            backup.last_restored_at = timezone.now()
            backup.restoration_count += 1
            backup.save()
            
            logger.info(f"Restore completed successfully: {backup.name}")
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            restore_log.success = False
            restore_log.error_message = str(e)
            restore_log.completed_at = timezone.now()
            restore_log.save()
            raise
        
        return restore_log
    
    def _validate_restore(self, backup, restore_type):
        """Validate backup before restore"""
        notes = []
        valid = True
        
        # Check backup status
        if backup.status != 'completed':
            return {'valid': False, 'notes': 'Backup is not completed'}
        
        # Check file existence
        if restore_type in ['database', 'full']:
            if not backup.database_file:
                error_msg = 'Database backup file path not set'
                if backup.backup_type == 'full' and backup.media_file:
                    error_msg += '. This may be an uploaded backup that needs reprocessing.'
                return {'valid': False, 'notes': error_msg}
            elif not os.path.exists(backup.database_file):
                return {'valid': False, 'notes': f'Database backup file not found: {backup.database_file}'}
            notes.append(f"Database file: {backup.database_file} ({backup.database_size} bytes)")
        
        if restore_type in ['media', 'full']:
            if not backup.media_file:
                return {'valid': False, 'notes': 'Media backup file path not set'}
            elif not os.path.exists(backup.media_file):
                return {'valid': False, 'notes': f'Media backup file not found: {backup.media_file}'}
            notes.append(f"Media file: {backup.media_file} ({backup.media_size} bytes)")
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            notes.append("Database connection: OK")
        except Exception as e:
            return {'valid': False, 'notes': f'Database connection failed: {str(e)}'}
        
        # Check media directory
        if restore_type in ['media', 'full']:
            if not self.media_root.parent.exists():
                return {'valid': False, 'notes': 'Media parent directory does not exist'}
            notes.append(f"Media directory: {self.media_root}")
        
        return {'valid': valid, 'notes': '; '.join(notes)}
    
    def _create_pre_restore_backup(self, user):
        """Create a backup before restore for safety"""
        from .services import BackupService
        backup_service = BackupService()
        name = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_service.create_backup(backup_type='full', name=name, user=user)
        logger.info("Pre-restore backup created")
    
    def _restore_database(self, backup, restore_log):
        """Restore database from backup"""
        database_file = Path(backup.database_file)
        
        try:
            # Decompress if needed
            if database_file.suffix == '.gz':
                temp_file = self._decompress_file(database_file)
                json_file = temp_file
            else:
                json_file = database_file
            
            # Use Django's loaddata command to restore
            from django.core.management import call_command
            from django.apps import apps
            from django.db import transaction
            
            # Get models that should be preserved (system/auth data)
            preserve_models = [
                'Session', 'LogEntry', 'Permission', 'ContentType', 'Group',
                'User'  # Be careful with users - might want to preserve admin users
            ]
            
            # Get models that should be cleared (app data)
            app_models_to_clear = []
            for model in apps.get_models():
                model_name = model.__name__
                app_label = model._meta.app_label
                
                # Only clear models from your custom apps, preserve Django system apps and backup system
                if (app_label not in ['auth', 'contenttypes', 'sessions', 'admin', 'django', 'backups'] and 
                    model_name not in preserve_models):
                    app_models_to_clear.append(model)
            
            with transaction.atomic():
                # Clear only application data, not system data
                for model in app_models_to_clear:
                    try:
                        model.objects.all().delete()
                        logger.info(f"Cleared {model.__name__} data")
                    except Exception as e:
                        logger.warning(f"Could not clear {model.__name__}: {e}")
                
                # Load the backup data
                call_command('loaddata', str(json_file), verbosity=2)
                logger.info("Backup data loaded successfully")
            
            # Clean up temporary file if created
            if database_file.suffix == '.gz' and json_file != database_file:
                json_file.unlink()
            
            logger.info("Database restored successfully")
            
        except Exception as e:
            # Clean up temporary file if created and error occurred
            if 'json_file' in locals() and database_file.suffix == '.gz' and json_file != database_file:
                try:
                    json_file.unlink()
                except:
                    pass
            raise Exception(f"Database restore failed: {str(e)}")
    
    def _restore_media(self, backup, restore_log):
        """Restore media files from backup"""
        media_file = Path(backup.media_file)
        
        try:
            # Create backup of existing media directory
            if self.media_root.exists():
                backup_media_dir = self.media_root.parent / f"media_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copytree(self.media_root, backup_media_dir)
                logger.info(f"Existing media backed up to: {backup_media_dir}")
            
            # Clear existing media directory
            if self.media_root.exists():
                shutil.rmtree(self.media_root)
            
            # Create media directory
            self.media_root.mkdir(parents=True, exist_ok=True)
            
            # Extract media backup
            with zipfile.ZipFile(media_file, 'r') as zipf:
                zipf.extractall(self.media_root)
            
            logger.info("Media files restored successfully")
            
        except Exception as e:
            raise Exception(f"Media restore failed: {str(e)}")
    
    def _decompress_file(self, compressed_file):
        """Decompress a gzip file to temporary location"""
        import gzip
        temp_file = Path(tempfile.mktemp(suffix='.json'))
        
        with gzip.open(compressed_file, 'rb') as f_in:
            with open(temp_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return temp_file


class BackupUploadService:
    """Service for handling backup file uploads and validation"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BASE_DIR) / getattr(settings, 'BACKUP_DIRECTORY', 'backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def handle_uploaded_backup(self, uploaded_file, backup_type, name=None, user=None):
        """Process an uploaded backup file and create backup record"""
        if not name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"uploaded_backup_{timestamp}"
        
        # Validate file
        validation_result = self._validate_uploaded_file(uploaded_file, backup_type)
        if not validation_result['valid']:
            raise Exception(f"File validation failed: {validation_result['error']}")
        
        # Save uploaded file
        file_path = self._save_uploaded_file(uploaded_file)
        
        # Create backup record
        backup = Backup.objects.create(
            name=name,
            backup_type=backup_type,
            status='completed',
            created_by=user,
            completed_at=timezone.now()
        )
        
        try:
            # Set file paths based on backup type
            if backup_type == 'database':
                backup.database_file = str(file_path)
                backup.database_size = file_path.stat().st_size
            elif backup_type == 'media':
                backup.media_file = str(file_path)
                backup.media_size = file_path.stat().st_size
            elif backup_type == 'full':
                # For full backups, we need to extract and identify components
                self._process_full_backup_upload(backup, file_path)
            
            backup.total_size = (backup.database_size or 0) + (backup.media_size or 0)
            backup.save()
            
            logger.info(f"Uploaded backup processed: {backup.name}")
            return backup
            
        except Exception as e:
            # Clean up on error
            backup.delete()
            if file_path.exists():
                file_path.unlink()
            raise
    
    def _validate_uploaded_file(self, uploaded_file, backup_type):
        """Validate uploaded backup file"""
        # Check file size
        max_size = getattr(settings, 'BACKUP_MAX_UPLOAD_SIZE', 5 * 1024 * 1024 * 1024)  # 5GB default
        if uploaded_file.size > max_size:
            return {'valid': False, 'error': f'File too large. Maximum size: {max_size} bytes'}
        
        # Check file extension based on backup type
        valid_extensions = {
            'database': ['.sql', '.sql.gz', '.dump', '.json.gz'],
            'media': ['.zip', '.tar.gz', '.tar'],
            'full': ['.zip', '.tar.gz', '.tar']
        }
        
        file_ext = Path(uploaded_file.name).suffix.lower()
        if file_ext not in valid_extensions.get(backup_type, []):
            return {
                'valid': False, 
                'error': f'Invalid file extension for {backup_type} backup. Expected: {valid_extensions.get(backup_type, [])}'
            }
        
        # Additional validation for full backups - check if it's a valid zip
        if backup_type == 'full' and file_ext == '.zip':
            try:
                import zipfile
                with zipfile.ZipFile(uploaded_file, 'r') as zipf:
                    file_list = zipf.namelist()
                    # Check if it contains both database and media components
                    has_db = any('db_backup' in f.lower() or f.lower().endswith(('.sql', '.json.gz', '.dump')) 
                              for f in file_list)
                    has_media = any('media' in f.lower() and f.lower().endswith('.zip') 
                                  for f in file_list)
                    
                    if not (has_db or has_media):
                        return {
                            'valid': False, 
                            'error': 'Full backup zip file must contain database and/or media backup files'
                        }
            except zipfile.BadZipFile:
                return {'valid': False, 'error': 'Uploaded file is not a valid zip archive'}
            except Exception as e:
                logger.warning(f"Could not validate zip contents: {e}")
                # Don't fail validation for other errors, just log them
        
        return {'valid': True, 'error': None}
    
    def _save_uploaded_file(self, uploaded_file):
        """Save uploaded file to backup directory"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"uploaded_{timestamp}_{uploaded_file.name}"
        file_path = self.backup_dir / filename
        
        with open(file_path, 'wb') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        return file_path
    
    def _process_full_backup_upload(self, backup, file_path):
        """Process uploaded full backup (containing both database and media)"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # List all files in the zip
                file_list = zipf.namelist()
                logger.info(f"Processing full backup upload with files: {file_list}")
                
                zipf.extractall(temp_dir)
            
            # Look for database and media files with more flexible patterns
            db_files = []
            media_files = []
            
            # Check all extracted files
            for extracted_file in temp_dir.rglob('*'):
                if extracted_file.is_file():
                    file_name = extracted_file.name.lower()
                    
                    # Database files: .json.gz, .sql, .sql.gz, or files containing 'db_backup'
                    if (file_name.endswith(('.json.gz', '.sql', '.sql.gz', '.dump')) or 
                        'db_backup' in file_name or 'database' in file_name):
                        db_files.append(extracted_file)
                    
                    # Media files: .zip files or files containing 'media'
                    elif (file_name.endswith('.zip') and 'media' in file_name) or 'media_backup' in file_name:
                        media_files.append(extracted_file)
            
            logger.info(f"Found database files: {[f.name for f in db_files]}")
            logger.info(f"Found media files: {[f.name for f in media_files]}")
            
            if db_files:
                # Move the first database file to backup directory
                db_file = self.backup_dir / f"db_uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
                shutil.move(str(db_files[0]), str(db_file))
                backup.database_file = str(db_file)
                backup.database_size = db_file.stat().st_size
                logger.info(f"Processed database file: {backup.database_file}")
            
            if media_files:
                # Move the first media file to backup directory
                media_file = self.backup_dir / f"media_uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                shutil.move(str(media_files[0]), str(media_file))
                backup.media_file = str(media_file)
                backup.media_size = media_file.stat().st_size
                logger.info(f"Processed media file: {backup.media_file}")
            
            # If no separate files found, this might be a different format
            if not db_files and not media_files:
                logger.warning(f"No database or media files found in uploaded backup. Available files: {file_list}")
                # Fallback: treat the entire zip as media for now
                backup.media_file = str(file_path)
                backup.media_size = file_path.stat().st_size
            
        except zipfile.BadZipFile:
            logger.error(f"Invalid zip file uploaded: {file_path}")
            raise Exception("Uploaded file is not a valid zip archive")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)