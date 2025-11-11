"""
Comprehensive Database and Media Backup Management Command
Creates full database dumps and complete media file backups
"""
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from backups.models import Backup, BackupLog
from backups.full_backup_utils import FullBackupUtilities
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create comprehensive backup with full database dump and media files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            help='Name for the backup (default: auto-generated)',
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Description for the backup',
        )
        parser.add_argument(
            '--no-media',
            action='store_false',
            dest='include_media',
            default=True,
            help='Skip media files backup',
        )
        parser.add_argument(
            '--no-compress',
            action='store_false',
            dest='compress',
            default=True,
            help='Skip compression',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Custom output directory',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Run in quiet mode',
        )
    
    def handle(self, *args, **options):
        try:
            # Configure logging
            if not options['quiet']:
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()]
                )
            
            # Generate backup name if not provided
            backup_name = options['name'] or f"FullBackup_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            
            if not options['quiet']:
                self.stdout.write(f"[INFO] Starting comprehensive backup: {backup_name}")
            
            # Create backup instance for tracking
            backup_instance = Backup.objects.create(
                name=backup_name,
                description=options['description'],
                backup_type='full',
                include_media=options['include_media'],
                compress_backup=options['compress'],
                status='pending'
            )
            
            # Log backup start
            BackupLog.objects.create(
                backup=backup_instance,
                level='info',
                message=f"Starting comprehensive backup: {backup_name}",
                operation="backup_start"
            )
            
            # Initialize backup utilities
            if options['output_dir']:
                # Override default backup root if custom directory provided
                original_backup_root = getattr(settings, 'BACKUP_ROOT', None)
                settings.BACKUP_ROOT = options['output_dir']
            
            backup_utils = FullBackupUtilities()
            
            # Create comprehensive backup
            results = backup_utils.create_comprehensive_backup(
                backup_name=backup_name,
                include_media=options['include_media'],
                compress=options['compress'],
                backup_instance=backup_instance
            )
            
            # Restore original backup root if it was overridden
            if options['output_dir'] and original_backup_root:
                settings.BACKUP_ROOT = original_backup_root
            
            if results['success']:
                if not options['quiet']:
                    self.stdout.write(
                        self.style.SUCCESS(f"[SUCCESS] Backup completed successfully: {results['backup_path']}")
                    )
                    
                    # Print detailed results
                    self.print_backup_summary(backup_instance, results)
                
                # Log success
                BackupLog.objects.create(
                    backup=backup_instance,
                    level='info',
                    message=f"Backup completed successfully: {results['backup_path']}",
                    operation="backup_complete",
                    extra_data=results
                )
            else:
                # Log errors
                for error in results['errors']:
                    BackupLog.objects.create(
                        backup=backup_instance,
                        level='error',
                        message=error,
                        operation="backup_error"
                    )
                
                raise CommandError(f"Backup failed: {'; '.join(results['errors'])}")
        
        except Exception as e:
            if 'backup_instance' in locals():
                backup_instance.mark_as_failed(str(e))
                BackupLog.objects.create(
                    backup=backup_instance,
                    level='critical',
                    message=f"Backup failed with exception: {str(e)}",
                    operation="backup_exception",
                    exception_info=str(e)
                )
            
            raise CommandError(f"Backup failed: {str(e)}")
    
    def print_backup_summary(self, backup_instance, results):
        """Print detailed backup summary"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("COMPREHENSIVE BACKUP COMPLETED SUCCESSFULLY")
        self.stdout.write("=" * 60)
        
        # Basic info
        self.stdout.write(f"Backup ID: {backup_instance.id}")
        self.stdout.write(f"Name: {backup_instance.name}")
        self.stdout.write(f"Type: {backup_instance.get_backup_type_display()}")
        self.stdout.write(f"Status: {backup_instance.status}")
        self.stdout.write(f"Duration: {backup_instance.duration_formatted}")
        
        # Database info
        db_results = results.get('database_results', {})
        if db_results:
            self.stdout.write(f"Database Tables: {db_results.get('tables_count', 0):,}")
            self.stdout.write(f"Database Records: {db_results.get('records_count', 0):,}")
            self.stdout.write(f"Database Size: {self._format_bytes(db_results.get('database_size', 0))}")
        
        # Media info
        media_results = results.get('media_results', {})
        if media_results:
            self.stdout.write(f"Media Files: {media_results.get('total_files', 0):,}")
            self.stdout.write(f"Media Size: {self._format_bytes(media_results.get('total_size', 0))}")
        
        # Size info
        self.stdout.write(f"Original Size: {self._format_bytes(results.get('total_size', 0))}")
        if results.get('compressed_size', 0) < results.get('total_size', 0):
            compression_ratio = round((1 - results['compressed_size'] / results['total_size']) * 100, 1)
            self.stdout.write(f"Compressed Size: {self._format_bytes(results.get('compressed_size', 0))}")
            self.stdout.write(f"Compression Ratio: {compression_ratio}%")
        
        self.stdout.write(f"Backup Path: {results['backup_path']}")
        self.stdout.write("=" * 60)
        
        # Warnings
        if results.get('warnings'):
            self.stdout.write("\nWarnings:")
            for warning in results['warnings']:
                self.stdout.write(f"  - {warning}")
    
    def _format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        if not bytes_value:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"