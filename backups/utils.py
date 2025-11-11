"""
Utility functions for backup and restore operations
"""
import os
import json
import shutil
import hashlib
import zipfile
import tarfile
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.db import transaction, connection, models
from django.apps import apps
from django.core.files.storage import default_storage
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class BackupUtilities:
    """Comprehensive backup utility functions"""
    
    def __init__(self):
        self.chunk_size = getattr(settings, 'BACKUP_CHUNK_SIZE', 1024 * 1024)  # 1MB default
        self.backup_root = getattr(settings, 'BACKUP_ROOT', os.path.join(settings.BASE_DIR, 'backups_storage'))
        self.ensure_backup_directories()
    
    def ensure_backup_directories(self):
        """Ensure backup directories exist"""
        directories = [
            self.backup_root,
            os.path.join(self.backup_root, 'database'),
            os.path.join(self.backup_root, 'media'),
            os.path.join(self.backup_root, 'complete'),
            os.path.join(self.backup_root, 'temp'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_model_dependencies(self) -> Dict[str, List[str]]:
        """
        Analyze model dependencies for safe backup/restore order
        Returns a mapping of model names to their dependencies
        """
        dependencies = {}
        
        for model in apps.get_models():
            model_key = f"{model._meta.app_label}.{model._meta.model_name}"
            model_deps = []
            
            # Check foreign key relationships
            for field in model._meta.get_fields():
                if isinstance(field, models.ForeignKey):
                    related_model = field.related_model
                    if related_model != model:  # Avoid self-references
                        dep_key = f"{related_model._meta.app_label}.{related_model._meta.model_name}"
                        if dep_key != model_key:
                            model_deps.append(dep_key)
            
            dependencies[model_key] = model_deps
        
        return dependencies
    
    def get_backup_order(self) -> List[str]:
        """
        Calculate the correct order for backing up models
        to preserve foreign key relationships
        """
        dependencies = self.get_model_dependencies()
        ordered = []
        remaining = set(dependencies.keys())
        
        # Simple topological sort
        while remaining:
            # Find models with no unresolved dependencies
            ready = []
            for model in remaining:
                if all(dep in ordered or dep not in remaining for dep in dependencies[model]):
                    ready.append(model)
            
            if not ready:
                # Circular dependency or missing model, add remaining in alphabetical order
                ready = sorted(remaining)
                logger.warning(f"Circular dependencies detected in models: {remaining}")
                break
            
            # Add ready models to ordered list
            for model in ready:
                ordered.append(model)
                remaining.remove(model)
        
        return ordered
    
    def get_restore_order(self) -> List[str]:
        """
        Get the reverse order for restoration
        """
        return list(reversed(self.get_backup_order()))
    
    def create_database_backup(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Create a comprehensive database backup
        """
        results = {
            'success': True,
            'files': [],
            'total_records': 0,
            'total_tables': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            backup_order = self.get_backup_order()
            
            # Update backup instance if provided
            if backup_instance:
                backup_instance.current_operation = "Creating database backup..."
                backup_instance.backup_order = backup_order
                backup_instance.save()
            
            # Create fixtures for each model in dependency order
            for i, model_path in enumerate(backup_order):
                try:
                    app_label, model_name = model_path.split('.')
                    model = apps.get_model(app_label, model_name)
                    
                    if backup_instance:
                        backup_instance.current_operation = f"Backing up {model._meta.verbose_name}..."
                        backup_instance.progress_percentage = int((i / len(backup_order)) * 50)  # 50% for database
                        backup_instance.save()
                    
                    # Create fixture file
                    fixture_file = os.path.join(backup_dir, f"{app_label}_{model_name}.json")
                    
                    # Get all objects for this model
                    queryset = model.objects.all()
                    record_count = queryset.count()
                    
                    if record_count > 0:
                        # Serialize model data
                        with open(fixture_file, 'w', encoding='utf-8') as f:
                            serializers.serialize('json', queryset, stream=f, indent=2)
                        
                        # Calculate file info
                        file_size = os.path.getsize(fixture_file)
                        checksum = self.calculate_checksum(fixture_file)
                        
                        results['files'].append({
                            'path': fixture_file,
                            'model': model_path,
                            'record_count': record_count,
                            'file_size': file_size,
                            'checksum': checksum
                        })
                        
                        results['total_records'] += record_count
                        results['total_tables'] += 1
                    
                except Exception as e:
                    error_msg = f"Error backing up model {model_path}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Create database schema backup
            self.create_schema_backup(backup_dir, results)
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Database backup failed: {str(e)}")
            logger.error(f"Database backup failed: {str(e)}")
        
        return results
    
    def create_schema_backup(self, backup_dir: str, results: Dict[str, Any]):
        """Create a backup of the database schema"""
        try:
            schema_file = os.path.join(backup_dir, 'schema.sql')
            
            # Get database settings
            db_settings = settings.DATABASES['default']
            engine = db_settings['ENGINE']
            
            if 'postgresql' in engine:
                self._backup_postgresql_schema(schema_file, db_settings)
            elif 'mysql' in engine:
                self._backup_mysql_schema(schema_file, db_settings)
            elif 'sqlite' in engine:
                self._backup_sqlite_schema(schema_file, db_settings)
            else:
                results['warnings'].append(f"Schema backup not supported for {engine}")
                return
            
            if os.path.exists(schema_file):
                file_size = os.path.getsize(schema_file)
                checksum = self.calculate_checksum(schema_file)
                
                results['files'].append({
                    'path': schema_file,
                    'model': 'database.schema',
                    'record_count': 0,
                    'file_size': file_size,
                    'checksum': checksum
                })
        
        except Exception as e:
            results['warnings'].append(f"Schema backup failed: {str(e)}")
            logger.warning(f"Schema backup failed: {str(e)}")
    
    def _backup_postgresql_schema(self, schema_file: str, db_settings: Dict[str, Any]):
        """Backup PostgreSQL schema using pg_dump"""
        cmd = [
            'pg_dump',
            '--schema-only',
            '--no-owner',
            '--no-privileges',
            f"--host={db_settings.get('HOST', 'localhost')}",
            f"--port={db_settings.get('PORT', '5432')}",
            f"--username={db_settings['USER']}",
            db_settings['NAME']
        ]
        
        env = os.environ.copy()
        if db_settings.get('PASSWORD'):
            env['PGPASSWORD'] = db_settings['PASSWORD']
        
        with open(schema_file, 'w') as f:
            subprocess.run(cmd, stdout=f, env=env, check=True)
    
    def _backup_mysql_schema(self, schema_file: str, db_settings: Dict[str, Any]):
        """Backup MySQL schema using mysqldump"""
        cmd = [
            'mysqldump',
            '--no-data',
            '--routines',
            '--triggers',
            f"--host={db_settings.get('HOST', 'localhost')}",
            f"--port={db_settings.get('PORT', '3306')}",
            f"--user={db_settings['USER']}"
        ]
        
        if db_settings.get('PASSWORD'):
            cmd.append(f"--password={db_settings['PASSWORD']}")
        
        cmd.append(db_settings['NAME'])
        
        with open(schema_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)
    
    def _backup_sqlite_schema(self, schema_file: str, db_settings: Dict[str, Any]):
        """Backup SQLite schema using .schema command"""
        db_path = db_settings['NAME']
        
        with open(schema_file, 'w') as f:
            subprocess.run([
                'sqlite3', db_path, '.schema'
            ], stdout=f, check=True)
    
    def create_media_backup(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Create a backup of media files
        """
        results = {
            'success': True,
            'files': [],
            'total_files': 0,
            'total_size': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                results['warnings'].append("Media directory does not exist")
                return results
            
            media_backup_dir = os.path.join(backup_dir, 'media')
            os.makedirs(media_backup_dir, exist_ok=True)
            
            # Walk through media directory
            total_files = sum(len(files) for _, _, files in os.walk(media_root))
            processed = 0
            
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    try:
                        source_path = os.path.join(root, file)
                        relative_path = os.path.relpath(source_path, media_root)
                        dest_path = os.path.join(media_backup_dir, relative_path)
                        
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(source_path, dest_path)
                        
                        # Calculate file info
                        file_size = os.path.getsize(dest_path)
                        checksum = self.calculate_checksum(dest_path)
                        
                        results['files'].append({
                            'path': dest_path,
                            'original_path': source_path,
                            'relative_path': relative_path,
                            'file_size': file_size,
                            'checksum': checksum
                        })
                        
                        results['total_files'] += 1
                        results['total_size'] += file_size
                        processed += 1
                        
                        if backup_instance and total_files > 0:
                            progress = 50 + int((processed / total_files) * 40)  # 40% for media (after 50% for database)
                            backup_instance.progress_percentage = min(progress, 90)
                            backup_instance.current_operation = f"Backing up media file: {relative_path}"
                            backup_instance.save()
                    
                    except Exception as e:
                        error_msg = f"Error backing up media file {file}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Media backup failed: {str(e)}")
            logger.error(f"Media backup failed: {str(e)}")
        
        return results
    
    def compress_backup(self, source_dir: str, output_file: str, backup_instance=None) -> Dict[str, Any]:
        """
        Compress backup directory into a single archive
        """
        results = {
            'success': True,
            'compressed_path': output_file,
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0,
            'errors': []
        }
        
        try:
            if backup_instance:
                backup_instance.current_operation = "Compressing backup..."
                backup_instance.save()
            
            # Calculate original size
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    results['original_size'] += os.path.getsize(os.path.join(root, file))
            
            # Create compressed archive
            if output_file.endswith('.zip'):
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, source_dir)
                            zipf.write(file_path, arc_path)
            
            elif output_file.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(output_file, 'w:gz') as tarf:
                    tarf.add(source_dir, arcname=os.path.basename(source_dir))
            
            else:
                raise ValueError(f"Unsupported archive format: {output_file}")
            
            # Calculate compressed size and ratio
            results['compressed_size'] = os.path.getsize(output_file)
            if results['original_size'] > 0:
                results['compression_ratio'] = (1 - results['compressed_size'] / results['original_size']) * 100
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Compression failed: {str(e)}")
            logger.error(f"Compression failed: {str(e)}")
        
        return results
    
    def restore_database(self, backup_dir: str, backup_instance=None, selective_models: List[str] = None) -> Dict[str, Any]:
        """
        Restore database from backup files
        """
        results = {
            'success': True,
            'restored_models': [],
            'restored_records': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            restore_order = self.get_restore_order()
            
            # Filter models if selective restore
            if selective_models:
                restore_order = [model for model in restore_order if model in selective_models]
            
            if backup_instance:
                backup_instance.current_operation = "Preparing database restoration..."
                backup_instance.save()
            
            with transaction.atomic():
                # Disable foreign key checks temporarily for different database engines
                db_engine = settings.DATABASES['default']['ENGINE']
                with connection.cursor() as cursor:
                    if 'postgresql' in db_engine:
                        cursor.execute("SET foreign_key_checks = 0;")
                    elif 'sqlite' in db_engine:
                        cursor.execute("PRAGMA foreign_keys = OFF;")
                
                for i, model_path in enumerate(restore_order):
                    try:
                        app_label, model_name = model_path.split('.')
                        model = apps.get_model(app_label, model_name)
                        
                        fixture_file = os.path.join(backup_dir, f"{app_label}_{model_name}.json")
                        
                        if not os.path.exists(fixture_file):
                            results['warnings'].append(f"Fixture file not found for {model_path}")
                            continue
                        
                        if backup_instance:
                            backup_instance.current_operation = f"Restoring {model._meta.verbose_name}..."
                            backup_instance.progress_percentage = int((i / len(restore_order)) * 80)  # 80% for database restore
                            backup_instance.save()
                        
                        # Clear existing data for this model (with foreign key constraints disabled)
                        if not selective_models:  # Only clear if full restore
                            try:
                                # Fast truncate for better performance
                                table_name = model._meta.db_table
                                with connection.cursor() as cursor:
                                    if 'sqlite' in db_engine:
                                        cursor.execute(f"DELETE FROM {table_name};")
                                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
                                    elif 'postgresql' in db_engine:
                                        cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
                                    else:
                                        # Fallback to regular deletion
                                        deleted_count = model.objects.all().delete()[0]
                                        if deleted_count > 0:
                                            results['warnings'].append(f"Deleted {deleted_count} existing records from {model_path}")
                            except Exception as delete_error:
                                # If truncate fails, try regular deletion
                                try:
                                    deleted_count = model.objects.all().delete()[0]
                                    if deleted_count > 0:
                                        results['warnings'].append(f"Deleted {deleted_count} existing records from {model_path}")
                                except Exception as fallback_error:
                                    results['warnings'].append(f"Could not clear existing records from {model_path}: {str(fallback_error)}")
                        
                        # Load fixture data
                        with open(fixture_file, 'r', encoding='utf-8') as f:
                            fixture_data = json.load(f)
                        
                        # Deserialize and save objects (optimized for speed)
                        objects_to_create = []
                        objects = serializers.deserialize('json', json.dumps(fixture_data))
                        
                        for obj in objects:
                            objects_to_create.append(obj.object)
                        
                        # Use bulk_create for much faster insertion
                        if objects_to_create:
                            try:
                                model.objects.bulk_create(objects_to_create, batch_size=1000, ignore_conflicts=True)
                                restored_count = len(objects_to_create)
                            except Exception as bulk_error:
                                # Fallback to individual saves if bulk fails
                                restored_count = 0
                                for obj_instance in objects_to_create:
                                    try:
                                        obj_instance.save()
                                        restored_count += 1
                                    except Exception as save_error:
                                        results['warnings'].append(f"Could not save {model_path} record: {str(save_error)}")
                        else:
                            restored_count = 0
                        
                        results['restored_models'].append({
                            'model': model_path,
                            'records': restored_count
                        })
                        results['restored_records'] += restored_count
                    
                    except Exception as e:
                        error_msg = f"Error restoring model {model_path}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
                # Re-enable foreign key checks
                with connection.cursor() as cursor:
                    if 'postgresql' in db_engine:
                        cursor.execute("SET foreign_key_checks = 1;")
                    elif 'sqlite' in db_engine:
                        cursor.execute("PRAGMA foreign_keys = ON;")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Database restore failed: {str(e)}")
            logger.error(f"Database restore failed: {str(e)}")
        
        return results
    
    def restore_media(self, backup_dir: str, backup_instance=None) -> Dict[str, Any]:
        """
        Restore media files from backup
        """
        results = {
            'success': True,
            'restored_files': 0,
            'skipped_files': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            media_backup_dir = os.path.join(backup_dir, 'media')
            if not os.path.exists(media_backup_dir):
                results['warnings'].append("No media backup directory found")
                return results
            
            media_root = settings.MEDIA_ROOT
            
            # Count total files for progress
            total_files = sum(len(files) for _, _, files in os.walk(media_backup_dir))
            processed = 0
            
            for root, dirs, files in os.walk(media_backup_dir):
                for file in files:
                    try:
                        source_path = os.path.join(root, file)
                        relative_path = os.path.relpath(source_path, media_backup_dir)
                        dest_path = os.path.join(media_root, relative_path)
                        
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(source_path, dest_path)
                        results['restored_files'] += 1
                        processed += 1
                        
                        if backup_instance and total_files > 0:
                            progress = 80 + int((processed / total_files) * 15)  # 15% for media (after 80% for database)
                            backup_instance.progress_percentage = min(progress, 95)
                            backup_instance.current_operation = f"Restoring media file: {relative_path}"
                            backup_instance.save()
                    
                    except Exception as e:
                        error_msg = f"Error restoring media file {file}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Media restore failed: {str(e)}")
            logger.error(f"Media restore failed: {str(e)}")
        
        return results
    
    def extract_backup(self, archive_path: str, extract_dir: str) -> bool:
        """
        Extract backup archive to directory
        """
        try:
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
            
            elif archive_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(archive_path, 'r:gz') as tarf:
                    tarf.extractall(extract_dir)
            
            else:
                raise ValueError(f"Unsupported archive format: {archive_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to extract backup: {str(e)}")
            return False
    
    def calculate_checksum(self, file_path: str) -> str:
        """
        Calculate SHA-256 checksum of a file
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {str(e)}")
            return ""
    
    def verify_backup_integrity(self, backup_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify integrity of backup files using checksums
        """
        results = {
            'success': True,
            'verified_files': 0,
            'failed_files': 0,
            'errors': []
        }
        
        for file_info in backup_files:
            try:
                file_path = file_info.get('path')
                expected_checksum = file_info.get('checksum')
                
                if not file_path or not expected_checksum:
                    continue
                
                if not os.path.exists(file_path):
                    results['errors'].append(f"File not found: {file_path}")
                    results['failed_files'] += 1
                    continue
                
                actual_checksum = self.calculate_checksum(file_path)
                
                if actual_checksum == expected_checksum:
                    results['verified_files'] += 1
                else:
                    results['errors'].append(f"Checksum mismatch for {file_path}")
                    results['failed_files'] += 1
            
            except Exception as e:
                results['errors'].append(f"Error verifying {file_path}: {str(e)}")
                results['failed_files'] += 1
        
        results['success'] = results['failed_files'] == 0
        return results
    
    def get_directory_size(self, directory: str) -> int:
        """
        Calculate total size of directory in bytes
        """
        total_size = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error calculating directory size for {directory}: {str(e)}")
        
        return total_size
    
    def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old backup files based on retention policy
        """
        from .models import Backup
        
        results = {
            'success': True,
            'deleted_backups': 0,
            'freed_space': 0,
            'errors': []
        }
        
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)
            old_backups = Backup.objects.filter(
                created_at__lt=cutoff_date,
                status='completed'
            )
            
            for backup in old_backups:
                try:
                    if backup.backup_path and os.path.exists(backup.backup_path):
                        file_size = os.path.getsize(backup.backup_path)
                        os.remove(backup.backup_path)
                        results['freed_space'] += file_size
                    
                    backup.delete()
                    results['deleted_backups'] += 1
                
                except Exception as e:
                    results['errors'].append(f"Error deleting backup {backup.id}: {str(e)}")
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Cleanup failed: {str(e)}")
        
        return results


# Global utility instance
backup_utils = BackupUtilities()