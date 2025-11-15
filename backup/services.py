import os
import subprocess
import tarfile
import gzip
import shutil
import logging
from datetime import datetime
from django.conf import settings
from django.db import connection
from django.core.mail import send_mail
from django.utils import timezone
from .models import BackupRecord, BackupSettings, BackupType, BackupStatus

logger = logging.getLogger(__name__)


class BackupService:
    """Service class for handling backup operations"""
    
    def __init__(self):
        self.settings = BackupSettings.get_settings()
        self.backup_dir = self._get_backup_directory()
        
    def _get_backup_directory(self):
        """Get or create backup directory"""
        backup_dir = os.path.join(settings.MEDIA_ROOT, self.settings.backup_directory)
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    def create_backup(self, backup_record):
        """Create backup based on backup record configuration"""
        try:
            backup_record.status = BackupStatus.IN_PROGRESS
            backup_record.started_at = timezone.now()
            backup_record.save()
            
            logger.info(f"Starting backup: {backup_record.name} ({backup_record.backup_type})")
            
            # Create backup based on type
            if backup_record.backup_type == BackupType.DATABASE_ONLY:
                self._create_database_backup(backup_record)
            elif backup_record.backup_type == BackupType.MEDIA_ONLY:
                self._create_media_backup(backup_record)
            elif backup_record.backup_type == BackupType.FULL_BACKUP:
                self._create_database_backup(backup_record)
                self._create_media_backup(backup_record)
            
            # Calculate total size
            backup_record.file_size = backup_record.database_size + backup_record.media_size
            
            backup_record.status = BackupStatus.COMPLETED
            backup_record.completed_at = timezone.now()
            backup_record.save()
            
            logger.info(f"Backup completed: {backup_record.name}")
            
            # Send notification if enabled
            if self.settings.email_notifications:
                self._send_notification(backup_record, success=True)
                
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {backup_record.name} - {str(e)}")
            backup_record.status = BackupStatus.FAILED
            backup_record.error_message = str(e)
            backup_record.save()
            
            # Send failure notification
            if self.settings.email_notifications:
                self._send_notification(backup_record, success=False)
                
            return False
    
    def _create_database_backup(self, backup_record):
        """Create database backup using mysqldump or sqlite3"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"database_{backup_record.name}_{timestamp}.sql"
        
        if backup_record.compress:
            filename += ".gz"
        
        filepath = os.path.join(self.backup_dir, filename)
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')
        
        logger.info(f"Creating database backup: {filename}")
        
        if 'sqlite' in engine:
            # SQLite backup
            self._create_sqlite_backup(backup_record, filepath, db_config)
        elif 'mysql' in engine:
            # MySQL backup
            self._create_mysql_backup(backup_record, filepath, db_config)
        else:
            raise Exception(f"Unsupported database engine: {engine}")
        
        # Update backup record
        backup_record.database_file = filepath
        backup_record.database_size = os.path.getsize(filepath)
        backup_record.save()
        
        logger.info(f"Database backup created: {filename} ({backup_record.formatted_database_size})")
    
    def _create_sqlite_backup(self, backup_record, filepath, db_config):
        """Create SQLite backup using file copy (much faster) or sqlite3 dump"""
        db_path = db_config.get('NAME')
        
        try:
            # Method 1: Fast file copy (recommended for SQLite)
            if backup_record.compress:
                # Copy and compress in chunks for memory efficiency
                chunk_size = 64 * 1024  # 64KB chunks
                with open(db_path, 'rb') as src_file:
                    with gzip.open(filepath, 'wb', compresslevel=6) as gz_file:
                        while True:
                            chunk = src_file.read(chunk_size)
                            if not chunk:
                                break
                            gz_file.write(chunk)
            else:
                # Simple file copy
                shutil.copy2(db_path, filepath.replace('.sql', '.db'))
                # Update filepath to reflect actual file
                backup_record.database_file = filepath.replace('.sql', '.db')
                
        except Exception as e:
            logger.warning(f"Fast copy failed: {e}. Falling back to sqlite3 dump.")
            
            # Fallback: Use sqlite3 .dump command
            cmd = ['sqlite3', str(db_path), '.dump']
            
            if backup_record.compress:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"sqlite3 dump failed: {stderr.decode()}")
                
                # Compress the output
                with gzip.open(filepath, 'wb') as gz_file:
                    gz_file.write(stdout)
            else:
                with open(filepath, 'wb') as f:
                    process = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
    
    def _create_mysql_backup(self, backup_record, filepath, db_config):
        """Create MySQL backup using mysqldump or Python fallback"""
        try:
            # Try mysqldump first (fastest method)
            mysqldump_path = self._find_mysqldump()
            
            # Build mysqldump command with optimizations for speed
            cmd = [
                mysqldump_path,
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', '3306')}",
                f"--user={db_config.get('USER', '')}",
                f"--password={db_config.get('PASSWORD', '')}",
                '--single-transaction',
                '--lock-tables=false',
                '--quick',
                '--compact',
                '--skip-add-locks',
                '--skip-comments',
                '--skip-dump-date',
                '--routines',
                '--triggers',
                db_config.get('NAME', '')
            ]
            
            self._execute_mysql_dump(cmd, filepath, backup_record.compress)
            
        except Exception as e:
            logger.warning(f"mysqldump failed: {e}. Using Python fallback method.")
            self._create_mysql_backup_python(backup_record, filepath, db_config)
    
    def _execute_mysql_dump(self, cmd, filepath, compress):
        """Execute mysqldump command with compression support"""
        if compress:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"mysqldump failed: {stderr.decode()}")
            
            # Compress the output
            with gzip.open(filepath, 'wb', compresslevel=6) as gz_file:
                gz_file.write(stdout)
        else:
            with open(filepath, 'wb') as f:
                process = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
    
    def _create_mysql_backup_python(self, backup_record, filepath, db_config):
        """Fallback MySQL backup using Django's database connection"""
        from django.core.management.color import no_style
        from django.db import connections
        
        # Get database connection
        connection = connections['default']
        
        # Get all table names
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
        
        # Create SQL dump manually
        sql_lines = []
        sql_lines.append("-- MySQL dump created by Django backup system")
        sql_lines.append("SET FOREIGN_KEY_CHECKS=0;")
        
        for table in tables:
            # Get CREATE TABLE statement
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table = cursor.fetchone()[1]
                sql_lines.append(f"DROP TABLE IF EXISTS `{table}`;")
                sql_lines.append(f"{create_table};")
                
                # Get data
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                
                if rows:
                    # Get column names
                    cursor.execute(f"DESCRIBE `{table}`")
                    columns = [row[0] for row in cursor.fetchall()]
                    columns_str = ', '.join([f"`{col}`" for col in columns])
                    
                    sql_lines.append(f"INSERT INTO `{table}` ({columns_str}) VALUES")
                    
                    # Process rows in chunks to avoid memory issues
                    chunk_size = 1000
                    for i in range(0, len(rows), chunk_size):
                        chunk = rows[i:i+chunk_size]
                        values = []
                        for row in chunk:
                            escaped_row = []
                            for val in row:
                                if val is None:
                                    escaped_row.append('NULL')
                                elif isinstance(val, str):
                                    escaped_val = val.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
                                    escaped_row.append(f"'{escaped_val}'")
                                else:
                                    escaped_row.append(str(val))
                            values.append(f"({', '.join(escaped_row)})")
                        
                        sql_lines.append(', '.join(values) + ';')
        
        sql_lines.append("SET FOREIGN_KEY_CHECKS=1;")
        
        # Write to file
        sql_content = '\n'.join(sql_lines).encode('utf-8')
        
        if backup_record.compress:
            with gzip.open(filepath, 'wb', compresslevel=6) as gz_file:
                gz_file.write(sql_content)
        else:
            with open(filepath, 'wb') as f:
                f.write(sql_content)
    
    def _create_media_backup(self, backup_record):
        """Create media files backup using tar.gz"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"media_{backup_record.name}_{timestamp}.tar.gz"
        filepath = os.path.join(self.backup_dir, filename)
        
        logger.info(f"Creating media backup: {filename}")
        
        media_root = settings.MEDIA_ROOT
        
        # Create tar.gz archive
        with tarfile.open(filepath, "w:gz", compresslevel=self.settings.compression_level) as tar:
            for root, dirs, files in os.walk(media_root):
                # Skip backup directory to avoid recursive backup
                if self.backup_dir in root:
                    continue
                
                # Skip log files if configured
                if backup_record.exclude_logs:
                    files = [f for f in files if not f.endswith('.log')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, media_root)
                    tar.add(file_path, arcname=arcname)
        
        # Update backup record
        backup_record.media_file = filepath
        backup_record.media_size = os.path.getsize(filepath)
        backup_record.save()
        
        logger.info(f"Media backup created: {filename} ({backup_record.formatted_media_size})")
    
    def _find_mysqldump(self):
        """Find mysqldump executable on Windows"""
        # Try common MySQL installation paths on Windows
        common_paths = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
            r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            r"C:\Program Files (x86)\MySQL\MySQL Server 8.4\bin\mysqldump.exe",
            r"C:\Program Files (x86)\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
            r"C:\xampp\mysql\bin\mysqldump.exe",
            r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysqldump.exe",
            r"C:\wamp\bin\mysql\mysql5.7.36\bin\mysqldump.exe",
            "mysqldump.exe",  # Try PATH
            "mysqldump"       # Try PATH without .exe
        ]
        
        # Try settings first
        if self.settings.mysql_path and os.path.exists(self.settings.mysql_path):
            return self.settings.mysql_path
        
        # Try common paths
        for path in common_paths:
            try:
                if os.path.exists(path):
                    return path
                # Try running to see if it's in PATH
                if path in ["mysqldump.exe", "mysqldump"]:
                    subprocess.run([path, "--version"], 
                                 capture_output=True, check=True, timeout=5)
                    return path
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise Exception("mysqldump not found. Please install MySQL or set mysql_path in backup settings.")
    
    def _send_notification(self, backup_record, success=True):
        """Send email notification about backup status"""
        if not self.settings.notification_email:
            return
        
        subject = f"Backup {'Completed' if success else 'Failed'}: {backup_record.name}"
        
        if success:
            message = f"""
            Backup completed successfully!
            
            Name: {backup_record.name}
            Type: {backup_record.get_backup_type_display()}
            Size: {backup_record.formatted_size}
            Duration: {backup_record.duration}
            Created: {backup_record.completed_at}
            
            Files:
            """
            for file_info in backup_record.get_backup_files():
                message += f"- {file_info['name']} ({backup_record._format_bytes(file_info['size'])})\n"
        else:
            message = f"""
            Backup failed!
            
            Name: {backup_record.name}
            Type: {backup_record.get_backup_type_display()}
            Error: {backup_record.error_message}
            Time: {timezone.now()}
            """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.settings.notification_email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send notification email: {str(e)}")


class RestoreService:
    """Service class for handling restore operations"""
    
    def __init__(self):
        self.settings = BackupSettings.get_settings()
    
    def restore_from_backup(self, restore_record):
        """Restore from backup record or uploaded files"""
        try:
            from .models import RestoreStatus
            
            restore_record.status = RestoreStatus.IN_PROGRESS
            restore_record.started_at = timezone.now()
            restore_record.save()
            
            logger.info(f"Starting restore: {restore_record.name}")
            
            # Validate restore files exist
            self._validate_restore_files(restore_record)
            
            # Create pre-restore backup if requested
            if restore_record.backup_before_restore:
                self._create_pre_restore_backup(restore_record)
            
            # Perform restore based on type
            if restore_record.restore_type == BackupType.DATABASE_ONLY:
                self._restore_database(restore_record)
            elif restore_record.restore_type == BackupType.MEDIA_ONLY:
                self._restore_media(restore_record)
            elif restore_record.restore_type == BackupType.FULL_BACKUP:
                self._restore_database(restore_record)
                self._restore_media(restore_record)
            
            restore_record.status = RestoreStatus.COMPLETED
            restore_record.completed_at = timezone.now()
            restore_record.save()
            
            logger.info(f"Restore completed: {restore_record.name}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {restore_record.name} - {str(e)}")
            restore_record.status = RestoreStatus.FAILED
            restore_record.error_message = str(e)
            restore_record.save()
            return False
    
    def _create_pre_restore_backup(self, restore_record):
        """Create backup before restore operation"""
        from .models import BackupRecord
        
        backup_name = f"pre_restore_{restore_record.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pre_backup = BackupRecord.objects.create(
            name=backup_name,
            backup_type=BackupType.FULL_BACKUP,
            created_by=restore_record.created_by,
            description=f"Automatic backup before restore: {restore_record.name}"
        )
        
        backup_service = BackupService()
        backup_service.create_backup(pre_backup)
        
        restore_record.pre_restore_backup = pre_backup
        restore_record.save()
    
    def _validate_restore_files(self, restore_record):
        """Validate that required restore files exist before starting restore"""
        restore_type = restore_record.restore_type
        
        # Check database file requirements
        if restore_type in [BackupType.DATABASE_ONLY, BackupType.FULL_BACKUP]:
            if restore_record.backup_record and restore_record.backup_record.database_file:
                db_file = restore_record.backup_record.database_file
                if not os.path.exists(db_file):
                    raise Exception(f"Database backup file not found: {db_file}")
            elif restore_record.uploaded_database_file:
                db_file = restore_record.uploaded_database_file.path
                if not os.path.exists(db_file):
                    raise Exception(f"Uploaded database file not found: {db_file}")
            else:
                raise Exception("No database file available for restore")
        
        # Check media file requirements
        if restore_type in [BackupType.MEDIA_ONLY, BackupType.FULL_BACKUP]:
            if restore_record.backup_record and restore_record.backup_record.media_file:
                media_file = restore_record.backup_record.media_file
                if not os.path.exists(media_file):
                    raise Exception(f"Media backup file not found: {media_file}")
            elif restore_record.uploaded_media_file:
                media_file = restore_record.uploaded_media_file.path
                if not os.path.exists(media_file):
                    raise Exception(f"Uploaded media file not found: {media_file}")
            else:
                # For media restore, if no media file is available, skip rather than fail
                logger.warning(f"No media file available for restore: {restore_record.name}")
    
    def _restore_database(self, restore_record):
        """Restore database from SQL file"""
        # Determine database file source
        if restore_record.backup_record and restore_record.backup_record.database_file:
            db_file = restore_record.backup_record.database_file
        elif restore_record.uploaded_database_file:
            db_file = restore_record.uploaded_database_file.path
        else:
            raise Exception("No database file available for restore")
        
        if not os.path.exists(db_file):
            raise Exception(f"Database file not found: {db_file}")
        
        logger.info(f"Restoring database from: {os.path.basename(db_file)}")
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')
        
        if 'sqlite' in engine:
            self._restore_sqlite_database(db_file, db_config)
        elif 'mysql' in engine:
            self._restore_mysql_database(db_file, db_config)
        else:
            raise Exception(f"Unsupported database engine: {engine}")
        
        logger.info("Database restore completed")
    
    def _restore_sqlite_database(self, db_file, db_config):
        """Restore SQLite database from backup file"""
        db_path = db_config.get('NAME')
        
        try:
            # Method 1: Fast file copy for .db files (fastest)
            if db_file.endswith('.db'):
                if db_file.endswith('.db.gz'):
                    # Decompress and copy
                    with gzip.open(db_file, 'rb') as src:
                        with open(db_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                else:
                    # Direct file copy
                    shutil.copy2(db_file, db_path)
                return
        except Exception as e:
            logger.warning(f"Fast restore failed: {e}. Falling back to SQL restore.")
        
        # Method 2: SQL restore for .sql files
        try:
            # Use sqlite3 command if available
            cmd = ['sqlite3', str(db_path)]
            
            if db_file.endswith('.gz'):
                with gzip.open(db_file, 'rt') as f:
                    process = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, check=True)
            else:
                with open(db_file, 'r') as f:
                    process = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, check=True)
                    
        except Exception as e:
            logger.warning(f"sqlite3 command failed: {e}. Using Python fallback.")
            # Method 3: Python-based restore (most compatible)
            self._restore_sqlite_database_python(db_file, db_config)
    
    def _restore_mysql_database(self, db_file, db_config):
        """Restore MySQL database from SQL file"""
        try:
            # Try mysql command first
            mysql_path = self._find_mysql_client()
            cmd = [
                mysql_path,
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', '3306')}",
                f"--user={db_config.get('USER', '')}",
                f"--password={db_config.get('PASSWORD', '')}",
                db_config.get('NAME', '')
            ]
            
            # Execute restore
            if db_file.endswith('.gz'):
                with gzip.open(db_file, 'rt') as f:
                    process = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, check=True)
            else:
                with open(db_file, 'r') as f:
                    process = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, check=True)
                    
        except Exception as e:
            logger.warning(f"mysql command failed: {e}. Using Python fallback.")
            # Use Python-based restore
            self._restore_mysql_database_python(db_file, db_config)
    
    def _restore_media(self, restore_record):
        """Restore media files from tar.gz archive"""
        # Determine media file source
        if restore_record.backup_record and restore_record.backup_record.media_file:
            media_file = restore_record.backup_record.media_file
        elif restore_record.uploaded_media_file:
            media_file = restore_record.uploaded_media_file.path
        else:
            raise Exception("No media file available for restore")
        
        if not os.path.exists(media_file):
            raise Exception(f"Media file not found: {media_file}")
        
        logger.info(f"Restoring media from: {os.path.basename(media_file)}")
        
        media_root = settings.MEDIA_ROOT
        
        # Create backup of existing media if overwrite is not enabled
        if not restore_record.overwrite_existing:
            backup_dir = f"{media_root}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(media_root, backup_dir)
            os.makedirs(media_root, exist_ok=True)
        
        # Extract media files
        with tarfile.open(media_file, "r:gz") as tar:
            tar.extractall(path=media_root)
        
        logger.info("Media restore completed")
    
    def _find_mysql_client(self):
        """Find mysql client executable on Windows"""
        # Try common MySQL installation paths on Windows
        common_paths = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe", 
            r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
            r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe",
            r"C:\Program Files (x86)\MySQL\MySQL Server 8.4\bin\mysql.exe",
            r"C:\Program Files (x86)\MySQL\MySQL Server 5.7\bin\mysql.exe",
            r"C:\xampp\mysql\bin\mysql.exe",
            r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe",
            r"C:\wamp\bin\mysql\mysql5.7.36\bin\mysql.exe",
            "mysql.exe",  # Try PATH
            "mysql"       # Try PATH without .exe
        ]
        
        # Try common paths
        for path in common_paths:
            try:
                if os.path.exists(path):
                    return path
                # Try running to see if it's in PATH
                if path in ["mysql.exe", "mysql"]:
                    subprocess.run([path, "--version"], 
                                 capture_output=True, check=True, timeout=5)
                    return path
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise Exception("mysql client not found. Please install MySQL client or use Python fallback.")
    
    def _restore_sqlite_database_python(self, db_file, db_config):
        """Pure Python SQLite restore fallback"""
        import sqlite3
        
        # Read SQL content
        if db_file.endswith('.gz'):
            with gzip.open(db_file, 'rt') as f:
                sql_content = f.read()
        else:
            with open(db_file, 'r') as f:
                sql_content = f.read()
        
        # Execute SQL statements
        db_path = db_config.get('NAME')
        conn = sqlite3.connect(db_path)
        try:
            conn.executescript(sql_content)
            conn.commit()
        finally:
            conn.close()
    
    def _restore_mysql_database_python(self, db_file, db_config):
        """Pure Python MySQL restore fallback"""
        from django.db import connections
        
        # Read SQL content
        if db_file.endswith('.gz'):
            with gzip.open(db_file, 'rt', encoding='utf-8') as f:
                sql_content = f.read()
        else:
            with open(db_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
        
        # Execute SQL statements
        connection = connections['default']
        with connection.cursor() as cursor:
            # Split SQL content into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.warning(f"SQL statement failed: {statement[:100]}... Error: {e}")
                        continue


class BackupCleanupService:
    """Service for cleaning up old backups"""
    
    def __init__(self):
        self.settings = BackupSettings.get_settings()
    
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        if not self.settings.auto_cleanup or self.settings.default_retention_days == 0:
            return
        
        from datetime import timedelta
        from .models import BackupRecord
        
        cutoff_date = timezone.now() - timedelta(days=self.settings.default_retention_days)
        old_backups = BackupRecord.objects.filter(
            created_at__lt=cutoff_date,
            status=BackupStatus.COMPLETED
        )
        
        deleted_count = 0
        for backup in old_backups:
            try:
                backup.delete_backup_files()
                backup.delete()
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup.name}")
            except Exception as e:
                logger.error(f"Failed to delete backup {backup.name}: {str(e)}")
        
        logger.info(f"Cleanup completed: {deleted_count} backups deleted")
        return deleted_count