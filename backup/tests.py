from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch, MagicMock
import tempfile
import os

from .models import BackupRecord, BackupSchedule, BackupSettings, BackupType, BackupStatus
from .services import BackupService, RestoreService, BackupCleanupService


class BackupModelTests(TestCase):
    """Test backup models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_backup_record_creation(self):
        """Test creating a backup record"""
        backup = BackupRecord.objects.create(
            name='Test Backup',
            backup_type=BackupType.FULL_BACKUP,
            created_by=self.user
        )
        
        self.assertEqual(backup.name, 'Test Backup')
        self.assertEqual(backup.backup_type, BackupType.FULL_BACKUP)
        self.assertEqual(backup.status, BackupStatus.PENDING)
        self.assertEqual(backup.created_by, self.user)
    
    def test_backup_record_str(self):
        """Test backup record string representation"""
        backup = BackupRecord.objects.create(
            name='Test Backup',
            backup_type=BackupType.DATABASE_ONLY,
            status=BackupStatus.COMPLETED
        )
        
        expected = f"Test Backup - Database Only (completed)"
        self.assertEqual(str(backup), expected)
    
    def test_backup_size_formatting(self):
        """Test backup size formatting"""
        backup = BackupRecord.objects.create(
            name='Test Backup',
            file_size=1024 * 1024,  # 1 MB
        )
        
        self.assertEqual(backup.formatted_size, '1.0 MB')
    
    def test_backup_schedule_creation(self):
        """Test creating a backup schedule"""
        schedule = BackupSchedule.objects.create(
            name='Daily Backup',
            backup_type=BackupType.FULL_BACKUP,
            schedule_type='daily',
            hour=2,
            minute=0,
            created_by=self.user
        )
        
        self.assertEqual(schedule.name, 'Daily Backup')
        self.assertEqual(schedule.schedule_type, 'daily')
        self.assertTrue(schedule.is_active)
    
    def test_backup_settings_singleton(self):
        """Test backup settings singleton behavior"""
        settings1 = BackupSettings.get_settings()
        settings2 = BackupSettings.get_settings()
        
        self.assertEqual(settings1.id, settings2.id)
        self.assertEqual(BackupSettings.objects.count(), 1)


class BackupServiceTests(TestCase):
    """Test backup service functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.backup_service = BackupService()
    
    @patch('backup.services.subprocess.run')
    @patch('backup.services.os.path.getsize')
    def test_database_backup_creation(self, mock_getsize, mock_subprocess):
        """Test database backup creation"""
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_getsize.return_value = 1024
        
        backup_record = BackupRecord.objects.create(
            name='Test DB Backup',
            backup_type=BackupType.DATABASE_ONLY,
            created_by=self.user
        )
        
        with patch('backup.services.open', create=True):
            result = self.backup_service.create_backup(backup_record)
        
        self.assertTrue(result)
        backup_record.refresh_from_db()
        self.assertEqual(backup_record.status, BackupStatus.COMPLETED)
    
    @patch('backup.services.tarfile.open')
    @patch('backup.services.os.walk')
    @patch('backup.services.os.path.getsize')
    def test_media_backup_creation(self, mock_getsize, mock_walk, mock_tarfile):
        """Test media backup creation"""
        mock_getsize.return_value = 2048
        mock_walk.return_value = [
            ('/media', ['subdir'], ['file1.jpg', 'file2.png']),
            ('/media/subdir', [], ['file3.jpg'])
        ]
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar
        
        backup_record = BackupRecord.objects.create(
            name='Test Media Backup',
            backup_type=BackupType.MEDIA_ONLY,
            created_by=self.user
        )
        
        result = self.backup_service.create_backup(backup_record)
        
        self.assertTrue(result)
        backup_record.refresh_from_db()
        self.assertEqual(backup_record.status, BackupStatus.COMPLETED)


class BackupAPITests(TestCase):
    """Test backup API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@test.com'
        )
        self.client.login(username='admin', password='adminpass123')
    
    def test_backup_list_endpoint(self):
        """Test backup list API endpoint"""
        BackupRecord.objects.create(
            name='Test Backup 1',
            backup_type=BackupType.DATABASE_ONLY
        )
        BackupRecord.objects.create(
            name='Test Backup 2',
            backup_type=BackupType.MEDIA_ONLY
        )
        
        response = self.client.get('/backup/api/backups/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data), 2)
    
    def test_backup_creation_endpoint(self):
        """Test backup creation API endpoint"""
        data = {
            'name': 'API Test Backup',
            'backup_type': 'database',
            'description': 'Created via API test'
        }
        
        response = self.client.post('/backup/api/backups/', data)
        self.assertEqual(response.status_code, 201)
        
        # Check if backup was created
        backup = BackupRecord.objects.get(name='API Test Backup')
        self.assertEqual(backup.backup_type, BackupType.DATABASE_ONLY)
    
    def test_backup_statistics_endpoint(self):
        """Test backup statistics API endpoint"""
        # Create some test backups
        BackupRecord.objects.create(
            name='Completed Backup',
            status=BackupStatus.COMPLETED
        )
        BackupRecord.objects.create(
            name='Failed Backup',
            status=BackupStatus.FAILED
        )
        
        response = self.client.get('/backup/api/statistics/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total_backups'], 2)
        self.assertEqual(data['completed_backups'], 1)
        self.assertEqual(data['failed_backups'], 1)


class BackupDashboardTests(TestCase):
    """Test backup dashboard views"""
    
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@test.com'
        )
        self.client.login(username='admin', password='adminpass123')
    
    def test_backup_dashboard_access(self):
        """Test backup dashboard access"""
        response = self.client.get('/backup/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backup Management')
    
    def test_backup_dashboard_non_superuser(self):
        """Test backup dashboard access for non-superuser"""
        regular_user = User.objects.create_user(
            username='regular',
            password='regularpass123'
        )
        self.client.login(username='regular', password='regularpass123')
        
        response = self.client.get('/backup/')
        # Should redirect to login or show permission denied
        self.assertNotEqual(response.status_code, 200)


class BackupCleanupTests(TestCase):
    """Test backup cleanup functionality"""
    
    def setUp(self):
        self.cleanup_service = BackupCleanupService()
        
        # Create old backup records
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=35)
        
        self.old_backup = BackupRecord.objects.create(
            name='Old Backup',
            status=BackupStatus.COMPLETED,
            created_at=old_date
        )
        
        self.recent_backup = BackupRecord.objects.create(
            name='Recent Backup',
            status=BackupStatus.COMPLETED
        )
    
    @patch('backup.services.os.path.exists')
    @patch('backup.services.os.remove')
    def test_cleanup_old_backups(self, mock_remove, mock_exists):
        """Test cleanup of old backups"""
        mock_exists.return_value = True
        
        # Set retention to 30 days
        settings = BackupSettings.get_settings()
        settings.default_retention_days = 30
        settings.auto_cleanup = True
        settings.save()
        
        deleted_count = self.cleanup_service.cleanup_old_backups()
        
        # Should delete 1 old backup
        self.assertEqual(deleted_count, 1)
        
        # Check that old backup is deleted but recent remains
        self.assertFalse(BackupRecord.objects.filter(id=self.old_backup.id).exists())
        self.assertTrue(BackupRecord.objects.filter(id=self.recent_backup.id).exists())


class BackupScheduleTests(TestCase):
    """Test backup scheduling functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_schedule_next_run_calculation(self):
        """Test next run calculation for schedules"""
        from backup.management.commands.run_scheduled_backups import Command
        
        command = Command()
        
        # Create daily schedule
        schedule = BackupSchedule.objects.create(
            name='Daily Test',
            schedule_type='daily',
            hour=2,
            minute=0,
            last_run=timezone.now()
        )
        
        next_run = command.calculate_next_run(schedule)
        
        # Should be approximately 24 hours from last run
        expected_diff = timezone.timedelta(days=1)
        actual_diff = next_run - schedule.last_run
        
        # Allow some tolerance for execution time
        self.assertLessEqual(abs(actual_diff.total_seconds() - expected_diff.total_seconds()), 60)