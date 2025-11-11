"""
Comprehensive Backup Restore Management Command
Restores full database dumps and complete media file backups
"""
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from backups.models import Backup, BackupRestore, BackupLog
from backups.full_backup_utils import FullBackupUtilities
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Restore comprehensive backup with full database dump and media files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_id',
            type=str,
            help='Backup ID or path to backup file/directory',
        )
        parser.add_argument(
            '--no-database',
            action='store_false',
            dest='restore_database',
            default=True,
            help='Skip database restoration',
        )
        parser.add_argument(
            '--no-media',
            action='store_false',
            dest='restore_media',
            default=True,
            help='Skip media files restoration',
        )
        parser.add_argument(
            '--no-pre-backup',
            action='store_false',
            dest='create_pre_backup',
            default=True,
            help='Skip creating pre-restore backup',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restoration without confirmation',
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
            
            backup_id = options['backup_id']
            
            # Try to find backup by ID first, then treat as file path
            backup_instance = None
            backup_path = None
            
            try:
                # Try to find by UUID
                backup_instance = Backup.objects.get(id=backup_id)
                backup_path = backup_instance.backup_path
                
                if not backup_path or not os.path.exists(backup_path):
                    raise CommandError(f"Backup file not found: {backup_path}")
                    
            except (Backup.DoesNotExist, ValueError):
                # Treat as file path
                backup_path = backup_id
                if not os.path.exists(backup_path):
                    raise CommandError(f"Backup file not found: {backup_path}")
            
            if not options['quiet']:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("RESTORATION PLAN")
                self.stdout.write("=" * 60)
                
                if backup_instance:
                    self.stdout.write(f"Backup ID: {backup_instance.id}")
                    self.stdout.write(f"Backup Name: {backup_instance.name}")
                    self.stdout.write(f"Backup Type: {backup_instance.get_backup_type_display()}")
                    self.stdout.write(f"Created: {backup_instance.created_at}")
                    self.stdout.write(f"Size: {backup_instance.formatted_size}")
                else:
                    self.stdout.write(f"Backup Path: {backup_path}")
                
                restore_items = []
                if options['restore_database']:
                    restore_items.append("Database")
                if options['restore_media']:
                    restore_items.append("Media Files")
                
                self.stdout.write(f"Items to restore: {', '.join(restore_items)}")
                
                safety_measures = []
                if options['create_pre_backup']:
                    safety_measures.append("Pre-restore backup")
                
                if safety_measures:
                    self.stdout.write(f"Safety measures: {', '.join(safety_measures)}")
                
                self.stdout.write("=" * 60)
                
                self.stdout.write("\nWARNING: This operation will modify your database and/or media files!")
            
            # Get confirmation unless forced
            if not options['force']:
                confirmation = input("\nDo you want to proceed with the restoration? (yes/no): ")
                if confirmation.lower() not in ['yes', 'y']:
                    self.stdout.write("Restoration cancelled.")
                    return
            
            if not options['quiet']:
                self.stdout.write(f"[INFO] Starting restoration...")
            
            # Create restore tracking instance
            restore_instance = BackupRestore.objects.create(
                backup=backup_instance,
                restore_database=options['restore_database'],
                restore_media=options['restore_media'],
                status='pending'
            )
            
            # Create pre-restore backup if requested
            pre_backup_instance = None
            if options['create_pre_backup']:
                if not options['quiet']:
                    self.stdout.write("[INFO] Creating pre-restore backup...")
                
                # Create a backup before restoration
                backup_utils = FullBackupUtilities()
                pre_backup_name = f"PreRestore_{backup_instance.name if backup_instance else 'Unknown'}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                
                pre_backup_results = backup_utils.create_comprehensive_backup(
                    backup_name=pre_backup_name,
                    include_media=options['restore_media'],
                    compress=True
                )
                
                if pre_backup_results['success']:
                    # Find the created backup instance
                    pre_backup_instance = Backup.objects.filter(name=pre_backup_name).first()
                    restore_instance.pre_restore_backup = pre_backup_instance
                    restore_instance.save()
                    
                    if not options['quiet']:
                        self.stdout.write(f"[INFO] Pre-restore backup created: {pre_backup_instance.id}")
                else:
                    self.stdout.write(
                        self.style.WARNING("[WARNING] Pre-restore backup failed, but continuing with restoration")
                    )
            
            # Initialize backup utilities
            backup_utils = FullBackupUtilities()
            
            # Perform restoration
            restore_instance.mark_as_started()
            
            results = backup_utils.restore_comprehensive_backup(
                backup_path=backup_path,
                restore_database=options['restore_database'],
                restore_media=options['restore_media'],
                backup_instance=restore_instance
            )
            
            if results['success']:
                if not options['quiet']:
                    self.stdout.write(
                        self.style.SUCCESS("[SUCCESS] Restoration completed successfully!")
                    )
                    
                    # Print detailed results
                    self.print_restore_summary(restore_instance, results)
                
                # Update restore instance
                restore_instance.restored_records = results['database_results'].get('restored_records', 0)
                restore_instance.restored_files = results['media_results'].get('restored_files', 0)
                restore_instance.mark_as_completed()
                
            else:
                # Handle restoration failure
                error_msg = '; '.join(results['errors'])
                restore_instance.mark_as_failed(error_msg)
                
                if pre_backup_instance:
                    self.stdout.write(
                        self.style.ERROR(
                            f"[ERROR] Restoration failed. You can rollback using backup: {pre_backup_instance.id}"
                        )
                    )
                
                raise CommandError(f"Restoration failed: {error_msg}")
        
        except Exception as e:
            if 'restore_instance' in locals():
                restore_instance.mark_as_failed(str(e))
            
            raise CommandError(f"Restoration failed: {str(e)}")
    
    def print_restore_summary(self, restore_instance, results):
        """Print detailed restoration summary"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("RESTORATION COMPLETED SUCCESSFULLY")
        self.stdout.write("=" * 60)
        
        # Basic info
        self.stdout.write(f"Restore ID: {restore_instance.id}")
        if restore_instance.backup:
            self.stdout.write(f"Source Backup: {restore_instance.backup.name}")
        self.stdout.write(f"Duration: {restore_instance.duration_seconds}s")
        
        # Database restoration info
        db_results = results.get('database_results', {})
        if db_results and restore_instance.restore_database:
            self.stdout.write(f"Database Tables Restored: {db_results.get('restored_tables', 0):,}")
            self.stdout.write(f"Database Records Restored: {db_results.get('restored_records', 0):,}")
        
        # Media restoration info
        media_results = results.get('media_results', {})
        if media_results and restore_instance.restore_media:
            self.stdout.write(f"Media Files Restored: {media_results.get('restored_files', 0):,}")
            self.stdout.write(f"Media Size Restored: {self._format_bytes(media_results.get('total_size', 0))}")
        
        # Pre-restore backup info
        if restore_instance.pre_restore_backup:
            self.stdout.write(f"Pre-restore Backup: {restore_instance.pre_restore_backup.id}")
            self.stdout.write("  (Use this backup to rollback if needed)")
        
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