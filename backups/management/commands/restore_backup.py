from django.core.management.base import BaseCommand, CommandError
from backups.services import RestoreService
from backups.models import Backup
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Restore a backup by ID or name'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_identifier',
            type=str,
            help='Backup ID or name to restore'
        )
        
        parser.add_argument(
            '--type',
            type=str,
            choices=['database', 'media', 'full'],
            help='Type of restore to perform (defaults to backup type)'
        )
        
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate the backup without restoring'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts'
        )
    
    def handle(self, *args, **options):
        backup_identifier = options['backup_identifier']
        restore_type = options['type']
        validate_only = options['validate_only']
        force = options['force']
        
        # Find backup by ID or name
        backup = None
        
        # Try to find by both ID and name
        # First try by exact name match
        name_matches = Backup.objects.filter(name=backup_identifier)
        
        # If numeric, also try by ID
        id_match = None
        if backup_identifier.isdigit():
            try:
                id_match = Backup.objects.get(id=int(backup_identifier))
            except Backup.DoesNotExist:
                pass
        
        # Combine results
        all_matches = []
        if id_match:
            all_matches.append(id_match)
        for name_match in name_matches:
            if not id_match or name_match.id != id_match.id:
                all_matches.append(name_match)
        
        # If no matches, try partial name match
        if not all_matches:
            partial_matches = Backup.objects.filter(name__icontains=backup_identifier)
            all_matches = list(partial_matches)
        
        if len(all_matches) == 0:
            raise CommandError(f'No backup found matching: {backup_identifier}')
        elif len(all_matches) == 1:
            backup = all_matches[0]
        else:
            # Multiple matches, show options
            self.stdout.write(f'Multiple backups found matching "{backup_identifier}":')
            for i, b in enumerate(all_matches, 1):
                self.stdout.write(f'  {i}. ID: {b.id}, Name: "{b.name}", Created: {b.created_at}, Type: {b.backup_type}')
            
            choice = input('Enter number to select backup (or 0 to cancel): ')
            try:
                choice_idx = int(choice) - 1
                if choice_idx == -1:
                    self.stdout.write('Restore cancelled.')
                    return
                if 0 <= choice_idx < len(all_matches):
                    backup = all_matches[choice_idx]
                else:
                    raise CommandError('Invalid selection.')
            except ValueError:
                raise CommandError('Invalid selection.')
        
        if not backup:
            raise CommandError(f'Backup not found: {backup_identifier}')
        
        self.stdout.write(f'Found backup: {backup.name}')
        self.stdout.write(f'Type: {backup.get_backup_type_display()}')
        self.stdout.write(f'Created: {backup.created_at}')
        self.stdout.write(f'Size: {backup.formatted_size}')
        
        if not backup.can_restore:
            raise CommandError('Backup cannot be restored (not completed or files missing)')
        
        # Determine restore type
        if not restore_type:
            restore_type = backup.backup_type
        
        self.stdout.write(f'Restore type: {restore_type}')
        
        if validate_only:
            self.stdout.write(
                self.style.WARNING('Validation mode - no actual restore will be performed')
            )
        else:
            self.stdout.write(
                self.style.WARNING('WARNING: This will replace your current data!')
            )
        
        # Confirm restore
        if not force and not validate_only:
            confirm = input('Are you sure you want to restore this backup? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Restore cancelled.')
                return
        
        try:
            restore_service = RestoreService()
            
            if validate_only:
                self.stdout.write('Validating backup...')
            else:
                self.stdout.write('Starting restore...')
            
            restore_log = restore_service.restore_backup(
                backup=backup,
                restore_type=restore_type,
                user=None,  # System restore
                validate_only=validate_only
            )
            
            if validate_only:
                if restore_log.validation_passed:
                    self.stdout.write(
                        self.style.SUCCESS('Validation passed!')
                    )
                    self.stdout.write(f'Notes: {restore_log.validation_notes}')
                else:
                    self.stdout.write(
                        self.style.ERROR('Validation failed!')
                    )
                    self.stdout.write(f'Notes: {restore_log.validation_notes}')
            else:
                if restore_log.success:
                    self.stdout.write(
                        self.style.SUCCESS('Restore completed successfully!')
                    )
                    self.stdout.write(f'Restore log ID: {restore_log.id}')
                    
                    # Update backup restoration count
                    backup.refresh_from_db()
                    self.stdout.write(f'This backup has been restored {backup.restoration_count} times')
                else:
                    self.stdout.write(
                        self.style.ERROR('Restore failed!')
                    )
                    if restore_log.error_message:
                        self.stdout.write(f'Error: {restore_log.error_message}')
            
        except Exception as e:
            logger.error(f'Restore operation failed: {str(e)}')
            raise CommandError(f'Restore operation failed: {str(e)}')