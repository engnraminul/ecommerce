import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from backup.models import BackupRecord, RestoreRecord, BackupType, RestoreStatus
from backup.services import RestoreService
from django.contrib.auth import get_user_model

# Get a backup to restore from  
backup = BackupRecord.objects.get(id=3)
print(f'Testing restore from backup: {backup.name}')

# Create restore record
User = get_user_model()
user = User.objects.filter(is_superuser=True).first()

restore = RestoreRecord.objects.create(
    name='Test Restore via CLI',
    description='Testing restore performance',
    backup_record=backup,
    restore_type=BackupType.DATABASE_ONLY,
    created_by=user
)

# Run restore
service = RestoreService()
print('Starting restore...')
success = service.restore_from_backup(restore)
print(f'Restore {"completed" if success else "failed"}!')
restore.refresh_from_db()
print(f'Duration: {restore.duration}')
if not success:
    print(f'Error: {restore.error_message}')