"""
Comprehensive Full Database and Media Files Backup System
Handles complete database dump and restore with proper foreign key handling
"""
import os
import json
import shutil
import sqlite3
import tarfile
import gzip
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.management import call_command
from django.db import connection, transaction
from django.core.files.storage import default_storage
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class FullBackupUtilities:
    """Complete database and media files backup system"""
    
    def __init__(self):
        self.backup_root = getattr(settings, 'BACKUP_ROOT', os.path.join(settings.BASE_DIR, 'backups_data'))
        self.media_root = settings.MEDIA_ROOT
        self.static_root = getattr(settings, 'STATIC_ROOT', '')
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary backup directories"""
        directories = [
            self.backup_root,
            os.path.join(self.backup_root, 'database'),
            os.path.join(self.backup_root, 'media'),
            os.path.join(self.backup_root, 'static'),
            os.path.join(self.backup_root, 'archives'),
            os.path.join(self.backup_root, 'temp'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def create_full_database_dump(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Create a complete database dump using native database tools
        This preserves all constraints, indexes, and relationships
        """
        results = {
            'success': True,
            'database_file': None,
            'database_size': 0,
            'tables_count': 0,
            'records_count': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            db_settings = settings.DATABASES['default']
            engine = db_settings['ENGINE']
            
            if backup_instance:
                backup_instance.current_operation = "Creating full database dump..."
                backup_instance.save()
            
            if 'sqlite' in engine.lower():
                results = self._create_sqlite_dump(backup_dir, db_settings, backup_instance)
            elif 'postgresql' in engine.lower():
                results = self._create_postgresql_dump(backup_dir, db_settings, backup_instance)
            elif 'mysql' in engine.lower():
                results = self._create_mysql_dump(backup_dir, db_settings, backup_instance)
            else:
                results['success'] = False
                results['errors'].append(f"Unsupported database engine: {engine}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Database dump failed: {str(e)}")
            logger.error(f"Database dump failed: {str(e)}")
        
        return results
    
    def _create_sqlite_dump(self, backup_dir: str, db_settings: Dict, backup_instance=None) -> Dict[str, Any]:
        """Create SQLite database dump"""
        results = {
            'success': True,
            'database_file': None,
            'database_size': 0,
            'tables_count': 0,
            'records_count': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            db_path = db_settings['NAME']
            backup_file = os.path.join(backup_dir, 'database_dump.sql')
            
            if backup_instance:
                backup_instance.current_operation = "Dumping SQLite database..."
                backup_instance.save()
            
            # Create a complete SQL dump
            with sqlite3.connect(db_path) as source_conn:
                with open(backup_file, 'w', encoding='utf-8') as dump_file:
                    # Add SQLite specific commands for full restoration
                    dump_file.write("PRAGMA foreign_keys=OFF;\n")
                    
                    # Dump the entire database (iterdump() already includes BEGIN/COMMIT)
                    for line in source_conn.iterdump():
                        dump_file.write(f"{line}\n")
                    
                    dump_file.write("PRAGMA foreign_keys=ON;\n")
            
            # Get database statistics
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Count tables
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                results['tables_count'] = cursor.fetchone()[0]
                
                # Count total records
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = cursor.fetchall()
                total_records = 0
                
                for table_name, in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    total_records += count
                
                results['records_count'] = total_records
            
            # Get file info
            results['database_file'] = backup_file
            results['database_size'] = os.path.getsize(backup_file)
            
            if backup_instance:
                backup_instance.current_operation = "SQLite dump completed"
                backup_instance.progress_percentage = 30
                backup_instance.save()
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"SQLite dump failed: {str(e)}")
            logger.error(f"SQLite dump failed: {str(e)}")
        
        return results
    
    def _create_postgresql_dump(self, backup_dir: str, db_settings: Dict, backup_instance=None) -> Dict[str, Any]:
        """Create PostgreSQL database dump using pg_dump"""
        results = {
            'success': True,
            'database_file': None,
            'database_size': 0,
            'tables_count': 0,
            'records_count': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            backup_file = os.path.join(backup_dir, 'database_dump.sql')
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                '-f', backup_file,
            ]
            
            # Add connection parameters
            if db_settings.get('HOST'):
                cmd.extend(['-h', db_settings['HOST']])
            if db_settings.get('PORT'):
                cmd.extend(['-p', str(db_settings['PORT'])])
            if db_settings.get('USER'):
                cmd.extend(['-U', db_settings['USER']])
            
            cmd.append(db_settings['NAME'])
            
            # Set password environment variable if provided
            env = os.environ.copy()
            if db_settings.get('PASSWORD'):
                env['PGPASSWORD'] = db_settings['PASSWORD']
            
            if backup_instance:
                backup_instance.current_operation = "Running pg_dump..."
                backup_instance.save()
            
            # Execute pg_dump
            import subprocess
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                results['database_file'] = backup_file
                results['database_size'] = os.path.getsize(backup_file)
                
                # Get database statistics
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    results['tables_count'] = cursor.fetchone()[0]
                    
                    # This is approximate for PostgreSQL
                    cursor.execute("""
                        SELECT SUM(n_tup_ins + n_tup_upd) 
                        FROM pg_stat_user_tables
                    """)
                    result_count = cursor.fetchone()[0]
                    results['records_count'] = result_count or 0
            else:
                results['success'] = False
                results['errors'].append(f"pg_dump failed: {result.stderr}")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"PostgreSQL dump failed: {str(e)}")
        
        return results
    
    def _create_mysql_dump(self, backup_dir: str, db_settings: Dict, backup_instance=None) -> Dict[str, Any]:
        """Create MySQL database dump using mysqldump"""
        results = {
            'success': True,
            'database_file': None,
            'database_size': 0,
            'tables_count': 0,
            'records_count': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            backup_file = os.path.join(backup_dir, 'database_dump.sql')
            
            # Build mysqldump command
            cmd = [
                'mysqldump',
                '--single-transaction',
                '--routines',
                '--triggers',
                '--add-drop-table',
                '--disable-keys',
                '--extended-insert',
                '--result-file=' + backup_file,
            ]
            
            # Add connection parameters
            if db_settings.get('HOST'):
                cmd.extend(['-h', db_settings['HOST']])
            if db_settings.get('PORT'):
                cmd.extend(['-P', str(db_settings['PORT'])])
            if db_settings.get('USER'):
                cmd.extend(['-u', db_settings['USER']])
            if db_settings.get('PASSWORD'):
                cmd.append(f"-p{db_settings['PASSWORD']}")
            
            cmd.append(db_settings['NAME'])
            
            if backup_instance:
                backup_instance.current_operation = "Running mysqldump..."
                backup_instance.save()
            
            # Execute mysqldump
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                results['database_file'] = backup_file
                results['database_size'] = os.path.getsize(backup_file)
                
                # Get database statistics
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_settings['NAME']])
                    results['tables_count'] = cursor.fetchone()[0]
                    
                    # Get approximate record count
                    cursor.execute("""
                        SELECT SUM(table_rows) FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_settings['NAME']])
                    result_count = cursor.fetchone()[0]
                    results['records_count'] = result_count or 0
            else:
                results['success'] = False
                results['errors'].append(f"mysqldump failed: {result.stderr}")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"MySQL dump failed: {str(e)}")
        
        return results
    
    def create_media_backup(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Create complete backup of all media files
        """
        results = {
            'success': True,
            'media_files': [],
            'total_files': 0,
            'total_size': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            media_backup_dir = os.path.join(backup_dir, 'media')
            os.makedirs(media_backup_dir, exist_ok=True)
            
            if backup_instance:
                backup_instance.current_operation = "Backing up media files..."
                backup_instance.save()
            
            if os.path.exists(self.media_root) and os.path.isdir(self.media_root):
                # Copy entire media directory
                for root, dirs, files in os.walk(self.media_root):
                    for file in files:
                        source_path = os.path.join(root, file)
                        relative_path = os.path.relpath(source_path, self.media_root)
                        destination_path = os.path.join(media_backup_dir, relative_path)
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                        
                        try:
                            shutil.copy2(source_path, destination_path)
                            file_size = os.path.getsize(source_path)
                            
                            results['media_files'].append({
                                'source': source_path,
                                'destination': destination_path,
                                'relative_path': relative_path,
                                'size': file_size
                            })
                            
                            results['total_files'] += 1
                            results['total_size'] += file_size
                            
                        except Exception as e:
                            results['errors'].append(f"Failed to copy {source_path}: {str(e)}")
            
            if backup_instance:
                backup_instance.current_operation = f"Media backup completed: {results['total_files']} files"
                backup_instance.progress_percentage = 60
                backup_instance.save()
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Media backup failed: {str(e)}")
            logger.error(f"Media backup failed: {str(e)}")
        
        return results
    
    def restore_full_database(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Restore database from complete dump file
        """
        results = {
            'success': True,
            'restored_tables': 0,
            'restored_records': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            db_settings = settings.DATABASES['default']
            engine = db_settings['ENGINE']
            
            if backup_instance:
                backup_instance.current_operation = "Restoring database from dump..."
                backup_instance.save()
            
            if 'sqlite' in engine.lower():
                results = self._restore_sqlite_dump(backup_dir, db_settings, backup_instance)
            elif 'postgresql' in engine.lower():
                results = self._restore_postgresql_dump(backup_dir, db_settings, backup_instance)
            elif 'mysql' in engine.lower():
                results = self._restore_mysql_dump(backup_dir, db_settings, backup_instance)
            else:
                results['success'] = False
                results['errors'].append(f"Unsupported database engine: {engine}")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Database restore failed: {str(e)}")
            logger.error(f"Database restore failed: {str(e)}")
        
        return results
    
    def _restore_sqlite_dump(self, backup_dir: str, db_settings: Dict, backup_instance=None) -> Dict[str, Any]:
        """Restore SQLite database from dump using Django connection"""
        results = {
            'success': True,
            'restored_tables': 0,
            'restored_records': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            dump_file = os.path.join(backup_dir, 'database_dump.sql')
            
            if not os.path.exists(dump_file):
                results['success'] = False
                results['errors'].append("Database dump file not found")
                return results
            
            if backup_instance:
                backup_instance.current_operation = "Restoring SQLite database..."
                backup_instance.save()
            
            # Read the dump file
            with open(dump_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Use Django's database connection to execute the restore
            from django.db import connection, transaction
            
            # Split the SQL script into individual statements
            statements = []
            current_statement = ""
            
            for line in sql_script.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    current_statement += line + '\n'
                    if line.endswith(';'):
                        statements.append(current_statement.strip())
                        current_statement = ""
            
            # Execute restoration in a transaction
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # First, disable foreign key checks
                    cursor.execute("PRAGMA foreign_keys = OFF;")
                    
                    # Drop all existing tables except system ones
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                    tables = cursor.fetchall()
                    
                    for table_name, in tables:
                        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
                    
                    # Execute each statement from the dump
                    for statement in statements:
                        if statement.strip():
                            try:
                                cursor.execute(statement)
                            except Exception as stmt_error:
                                logger.warning(f"Statement execution warning: {str(stmt_error)}")
                                # Continue with other statements
                    
                    # Re-enable foreign key checks
                    cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Get restoration statistics
            with connection.cursor() as cursor:
                # Count tables
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                results['restored_tables'] = cursor.fetchone()[0]
                
                # Count total records
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = cursor.fetchall()
                total_records = 0
                
                for table_name, in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                        count = cursor.fetchone()[0]
                        total_records += count
                    except:
                        # Skip tables that might have issues
                        pass
                
                results['restored_records'] = total_records
            
            if backup_instance:
                backup_instance.current_operation = "SQLite restore completed"
                backup_instance.progress_percentage = 80
                backup_instance.save()
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"SQLite restore failed: {str(e)}")
            logger.error(f"SQLite restore failed: {str(e)}")
        
        return results
    
    def _restore_postgresql_dump(self, backup_dir: str, db_settings: Dict, backup_instance=None) -> Dict[str, Any]:
        """Restore PostgreSQL database from dump"""
        results = {
            'success': True,
            'restored_tables': 0,
            'restored_records': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            dump_file = os.path.join(backup_dir, 'database_dump.sql')
            
            if not os.path.exists(dump_file):
                results['success'] = False
                results['errors'].append("Database dump file not found")
                return results
            
            # Build psql command
            cmd = [
                'psql',
                '--no-password',
                '-f', dump_file,
            ]
            
            # Add connection parameters
            if db_settings.get('HOST'):
                cmd.extend(['-h', db_settings['HOST']])
            if db_settings.get('PORT'):
                cmd.extend(['-p', str(db_settings['PORT'])])
            if db_settings.get('USER'):
                cmd.extend(['-U', db_settings['USER']])
            
            cmd.append(db_settings['NAME'])
            
            # Set password environment variable if provided
            env = os.environ.copy()
            if db_settings.get('PASSWORD'):
                env['PGPASSWORD'] = db_settings['PASSWORD']
            
            if backup_instance:
                backup_instance.current_operation = "Running psql restore..."
                backup_instance.save()
            
            # Execute psql
            import subprocess
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Get restoration statistics
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    results['restored_tables'] = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT SUM(n_tup_ins + n_tup_upd) 
                        FROM pg_stat_user_tables
                    """)
                    result_count = cursor.fetchone()[0]
                    results['restored_records'] = result_count or 0
            else:
                results['success'] = False
                results['errors'].append(f"psql restore failed: {result.stderr}")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"PostgreSQL restore failed: {str(e)}")
        
        return results
    
    def _restore_mysql_dump(self, backup_dir: str, db_settings: Dict, backup_instance=None) -> Dict[str, Any]:
        """Restore MySQL database from dump"""
        results = {
            'success': True,
            'restored_tables': 0,
            'restored_records': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            dump_file = os.path.join(backup_dir, 'database_dump.sql')
            
            if not os.path.exists(dump_file):
                results['success'] = False
                results['errors'].append("Database dump file not found")
                return results
            
            # Build mysql command
            cmd = ['mysql']
            
            # Add connection parameters
            if db_settings.get('HOST'):
                cmd.extend(['-h', db_settings['HOST']])
            if db_settings.get('PORT'):
                cmd.extend(['-P', str(db_settings['PORT'])])
            if db_settings.get('USER'):
                cmd.extend(['-u', db_settings['USER']])
            if db_settings.get('PASSWORD'):
                cmd.append(f"-p{db_settings['PASSWORD']}")
            
            cmd.append(db_settings['NAME'])
            
            if backup_instance:
                backup_instance.current_operation = "Running mysql restore..."
                backup_instance.save()
            
            # Execute mysql
            import subprocess
            with open(dump_file, 'r') as f:
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Get restoration statistics
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_settings['NAME']])
                    results['restored_tables'] = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT SUM(table_rows) FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_settings['NAME']])
                    result_count = cursor.fetchone()[0]
                    results['restored_records'] = result_count or 0
            else:
                results['success'] = False
                results['errors'].append(f"mysql restore failed: {result.stderr}")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"MySQL restore failed: {str(e)}")
        
        return results
    
    def restore_media_files(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Restore media files from backup
        """
        results = {
            'success': True,
            'restored_files': 0,
            'total_size': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            media_backup_dir = os.path.join(backup_dir, 'media')
            
            if not os.path.exists(media_backup_dir):
                results['warnings'].append("No media files found in backup")
                return results
            
            if backup_instance:
                backup_instance.current_operation = "Restoring media files..."
                backup_instance.save()
            
            # Create media root if it doesn't exist
            os.makedirs(self.media_root, exist_ok=True)
            
            # Copy all files from backup
            for root, dirs, files in os.walk(media_backup_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_path, media_backup_dir)
                    destination_path = os.path.join(self.media_root, relative_path)
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    
                    try:
                        shutil.copy2(source_path, destination_path)
                        file_size = os.path.getsize(source_path)
                        
                        results['restored_files'] += 1
                        results['total_size'] += file_size
                        
                    except Exception as e:
                        results['errors'].append(f"Failed to restore {relative_path}: {str(e)}")
            
            if backup_instance:
                backup_instance.current_operation = f"Media restore completed: {results['restored_files']} files"
                backup_instance.progress_percentage = 90
                backup_instance.save()
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Media restore failed: {str(e)}")
            logger.error(f"Media restore failed: {str(e)}")
        
        return results
    
    def create_comprehensive_backup(self, backup_name: str, include_media: bool = True, 
                                  compress: bool = True, backup_instance=None) -> Dict[str, Any]:
        """
        Create a comprehensive backup including full database dump and all media files
        """
        results = {
            'success': True,
            'backup_path': None,
            'database_results': {},
            'media_results': {},
            'total_size': 0,
            'compressed_size': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Create temporary backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_backup_dir = os.path.join(self.backup_root, 'temp', f"{backup_name}_{timestamp}")
            os.makedirs(temp_backup_dir, exist_ok=True)
            
            if backup_instance:
                backup_instance.current_operation = "Starting comprehensive backup..."
                backup_instance.mark_as_started()
            
            # Create database backup
            db_results = self.create_full_database_dump(temp_backup_dir, backup_instance)
            results['database_results'] = db_results
            
            if not db_results['success']:
                results['success'] = False
                results['errors'].extend(db_results['errors'])
                return results
            
            # Create media backup if requested
            if include_media:
                media_results = self.create_media_backup(temp_backup_dir, backup_instance)
                results['media_results'] = media_results
                
                if not media_results['success']:
                    results['warnings'].extend(media_results['errors'])
            
            # Create backup metadata
            metadata = {
                'backup_name': backup_name,
                'created_at': timezone.now().isoformat(),
                'database_engine': settings.DATABASES['default']['ENGINE'],
                'django_version': getattr(settings, 'VERSION', 'unknown'),
                'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                'include_media': include_media,
                'compressed': compress,
                'database_info': {
                    'tables_count': db_results.get('tables_count', 0),
                    'records_count': db_results.get('records_count', 0),
                    'database_size': db_results.get('database_size', 0),
                },
                'media_info': {
                    'files_count': results['media_results'].get('total_files', 0),
                    'total_size': results['media_results'].get('total_size', 0),
                }
            }
            
            # Save metadata
            metadata_file = os.path.join(temp_backup_dir, 'backup_metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Calculate total size
            for root, dirs, files in os.walk(temp_backup_dir):
                for file in files:
                    results['total_size'] += os.path.getsize(os.path.join(root, file))
            
            # Compress backup if requested
            if compress:
                if backup_instance:
                    backup_instance.current_operation = "Compressing backup..."
                    backup_instance.progress_percentage = 90
                    backup_instance.save()
                
                archive_path = os.path.join(self.backup_root, 'archives', f"{backup_name}_{timestamp}.tar.gz")
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(temp_backup_dir, arcname=os.path.basename(temp_backup_dir))
                
                results['compressed_size'] = os.path.getsize(archive_path)
                results['backup_path'] = archive_path
                
                # Clean up temporary directory
                shutil.rmtree(temp_backup_dir)
            else:
                # Move to permanent location
                final_path = os.path.join(self.backup_root, 'archives', f"{backup_name}_{timestamp}")
                shutil.move(temp_backup_dir, final_path)
                results['backup_path'] = final_path
                results['compressed_size'] = results['total_size']
            
            if backup_instance:
                backup_instance.current_operation = "Backup completed successfully"
                backup_instance.backup_path = results['backup_path']
                backup_instance.backup_size = results['total_size']
                backup_instance.compressed_size = results['compressed_size']
                backup_instance.total_tables = db_results.get('tables_count', 0)
                backup_instance.total_records = db_results.get('records_count', 0)
                backup_instance.total_files = results['media_results'].get('total_files', 0)
                backup_instance.mark_as_completed()
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Comprehensive backup failed: {str(e)}")
            logger.error(f"Comprehensive backup failed: {str(e)}")
            
            if backup_instance:
                backup_instance.mark_as_failed(str(e))
        
        return results
    
    def restore_comprehensive_backup(self, backup_path: str, restore_database: bool = True,
                                   restore_media: bool = True, backup_instance=None) -> Dict[str, Any]:
        """
        Restore from comprehensive backup
        """
        results = {
            'success': True,
            'database_results': {},
            'media_results': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            if backup_instance:
                backup_instance.current_operation = "Starting comprehensive restore..."
                backup_instance.mark_as_started()
            
            # Extract backup if it's compressed
            if backup_path.endswith(('.tar.gz', '.tgz')):
                temp_extract_dir = os.path.join(self.backup_root, 'temp', f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                os.makedirs(temp_extract_dir, exist_ok=True)
                
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(temp_extract_dir)
                
                # Find the actual backup directory
                extracted_dirs = [d for d in os.listdir(temp_extract_dir) if os.path.isdir(os.path.join(temp_extract_dir, d))]
                if extracted_dirs:
                    backup_dir = os.path.join(temp_extract_dir, extracted_dirs[0])
                else:
                    backup_dir = temp_extract_dir
            else:
                backup_dir = backup_path
                temp_extract_dir = None
            
            # Restore database if requested
            if restore_database:
                db_results = self.restore_full_database(backup_dir, backup_instance)
                results['database_results'] = db_results
                
                if not db_results['success']:
                    results['success'] = False
                    results['errors'].extend(db_results['errors'])
            
            # Restore media files if requested
            if restore_media:
                media_results = self.restore_media_files(backup_dir, backup_instance)
                results['media_results'] = media_results
                
                if not media_results['success']:
                    results['warnings'].extend(media_results['errors'])
            
            # Clean up temporary extraction directory
            if temp_extract_dir and os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            
            if backup_instance:
                backup_instance.current_operation = "Restore completed successfully"
                backup_instance.restored_records = results['database_results'].get('restored_records', 0)
                backup_instance.restored_files = results['media_results'].get('restored_files', 0)
                backup_instance.mark_as_completed()
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Comprehensive restore failed: {str(e)}")
            logger.error(f"Comprehensive restore failed: {str(e)}")
            
            if backup_instance:
                backup_instance.mark_as_failed(str(e))
        
        return results