from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from backup.models import BackupSchedule, BackupRecord, BackupType
from backup.services import BackupService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run scheduled backups'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run all active schedules regardless of timing',
        )
        parser.add_argument(
            '--schedule-id',
            type=int,
            help='Run specific schedule by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be executed without actually running backups',
        )
    
    def handle(self, *args, **options):
        """Execute scheduled backups"""
        now = timezone.now()
        
        if options['schedule_id']:
            # Run specific schedule
            try:
                schedule = BackupSchedule.objects.get(id=options['schedule_id'])
                self.run_schedule(schedule, options['dry_run'])
            except BackupSchedule.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Schedule with ID {options['schedule_id']} not found")
                )
                return
        else:
            # Run due schedules
            schedules = self.get_due_schedules(now, options['force'])
            
            if not schedules:
                self.stdout.write("No schedules due for execution")
                return
            
            self.stdout.write(f"Found {len(schedules)} schedule(s) due for execution")
            
            for schedule in schedules:
                self.run_schedule(schedule, options['dry_run'])
    
    def get_due_schedules(self, now, force=False):
        """Get schedules that are due for execution"""
        schedules = BackupSchedule.objects.filter(is_active=True)
        
        if force:
            return schedules
        
        due_schedules = []
        
        for schedule in schedules:
            if self.is_schedule_due(schedule, now):
                due_schedules.append(schedule)
        
        return due_schedules
    
    def is_schedule_due(self, schedule, now):
        """Check if a schedule is due for execution"""
        # If never run, check if it's time based on schedule
        if not schedule.last_run:
            return self.is_time_match(schedule, now)
        
        # Calculate next run time based on schedule type
        next_run = self.calculate_next_run(schedule)
        
        return now >= next_run
    
    def is_time_match(self, schedule, now):
        """Check if current time matches schedule time"""
        if now.hour != schedule.hour or now.minute != schedule.minute:
            return False
        
        if schedule.schedule_type == 'daily':
            return True
        elif schedule.schedule_type == 'weekly':
            return now.weekday() == schedule.day_of_week
        elif schedule.schedule_type == 'monthly':
            return now.day == schedule.day_of_month
        
        return False
    
    def calculate_next_run(self, schedule):
        """Calculate next run time for a schedule"""
        last_run = schedule.last_run
        
        if schedule.schedule_type == 'daily':
            next_run = last_run + timedelta(days=1)
        elif schedule.schedule_type == 'weekly':
            next_run = last_run + timedelta(weeks=1)
        elif schedule.schedule_type == 'monthly':
            # Add approximately one month
            next_run = last_run + timedelta(days=30)
        else:
            next_run = last_run + timedelta(days=1)  # Default to daily
        
        # Set the correct time
        next_run = next_run.replace(
            hour=schedule.hour,
            minute=schedule.minute,
            second=0,
            microsecond=0
        )
        
        return next_run
    
    def run_schedule(self, schedule, dry_run=False):
        """Execute a backup schedule"""
        self.stdout.write(f"Processing schedule: {schedule.name}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would create {schedule.get_backup_type_display()} backup")
            )
            return
        
        try:
            # Create backup record
            backup_name = f"Scheduled_{schedule.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_record = BackupRecord.objects.create(
                name=backup_name,
                backup_type=schedule.backup_type,
                compress=schedule.compress,
                exclude_logs=schedule.exclude_logs,
                description=f"Scheduled backup from: {schedule.name}"
            )
            
            # Execute backup
            backup_service = BackupService()
            success = backup_service.create_backup(backup_record)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Backup completed successfully: {backup_record.name}")
                )
                
                # Update schedule
                schedule.last_run = timezone.now()
                schedule.next_run = self.calculate_next_run(schedule)
                schedule.save()
                
                # Cleanup old backups if retention is set
                if schedule.retention_days > 0:
                    self.cleanup_old_scheduled_backups(schedule)
                
            else:
                self.stdout.write(
                    self.style.ERROR(f"Backup failed: {backup_record.name}")
                )
        
        except Exception as e:
            logger.error(f"Error running scheduled backup {schedule.name}: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Error running schedule {schedule.name}: {str(e)}")
            )
    
    def cleanup_old_scheduled_backups(self, schedule):
        """Clean up old backups for a specific schedule"""
        cutoff_date = timezone.now() - timedelta(days=schedule.retention_days)
        
        old_backups = BackupRecord.objects.filter(
            name__startswith=f"Scheduled_{schedule.name}_",
            created_at__lt=cutoff_date,
            status='completed'
        )
        
        deleted_count = 0
        for backup in old_backups:
            try:
                backup.delete_backup_files()
                backup.delete()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete old backup {backup.name}: {str(e)}")
        
        if deleted_count > 0:
            self.stdout.write(f"Cleaned up {deleted_count} old backups for schedule: {schedule.name}")