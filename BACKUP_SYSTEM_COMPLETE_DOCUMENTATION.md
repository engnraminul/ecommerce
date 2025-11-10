# Django Backup System - Complete Documentation

## Overview

This is a comprehensive, professional-grade backup and restore system for Django applications. It provides safe, reliable backup and restore operations with integrity verification, foreign key handling, and a user-friendly web interface.

## Features

### Core Functionality
- **Multiple Backup Types**: Full, database-only, and media-only backups
- **Safe Operations**: Foreign key-aware backup/restore with dependency resolution
- **Data Integrity**: SHA-256 checksum verification for all backup files
- **Compression**: Optional gzip compression to reduce storage space
- **Progress Monitoring**: Real-time progress tracking for long-running operations
- **Background Processing**: Non-blocking backup/restore operations
- **Metadata Tracking**: Comprehensive information about each backup

### Safety Features
- **Pre-Restore Backup**: Automatically create backup before restore operations
- **Dry Run Mode**: Test restore operations without making changes
- **Rollback Support**: Ability to revert failed restore operations
- **Integrity Verification**: Verify backup files before and after operations
- **Transaction Safety**: Database operations wrapped in transactions

### User Interface
- **Web Dashboard**: Modern, responsive web interface
- **REST API**: Complete API for programmatic access
- **Django Admin**: Admin interface for backup management
- **Management Commands**: Command-line tools for automation

### Automation & Scheduling
- **Backup Scheduling**: Automated backup creation with cron-like scheduling
- **Retention Policies**: Automatic cleanup of old backups
- **Email Notifications**: Alerts for backup success/failure
- **Monitoring**: Detailed logging and progress tracking

## Installation & Setup

### 1. App Installation

The backup app is already installed in your Django project. The following components are included:

```
backups/
├── __init__.py
├── apps.py                  # App configuration
├── models.py               # Database models
├── admin.py               # Django admin interface
├── views.py               # Web and API views
├── serializers.py         # REST API serializers
├── utils.py               # Backup utilities
├── urls.py                # URL routing
├── management/
│   └── commands/
│       ├── create_backup_safe.py    # Backup creation command
│       └── restore_backup_safe.py   # Backup restore command
└── templates/backups/     # Web interface templates
```

### 2. Settings Configuration

The following settings have been added to your `settings.py`:

```python
# Backup System Settings
BACKUP_ROOT = os.path.join(BASE_DIR, 'backups_data')
BACKUP_MEDIA_ROOT = os.path.join(BACKUP_ROOT, 'media')
BACKUP_DATABASE_ROOT = os.path.join(BACKUP_ROOT, 'database')
BACKUP_ARCHIVE_ROOT = os.path.join(BACKUP_ROOT, 'archives')

# Backup retention (days)
BACKUP_RETENTION_DAYS = 30

# Maximum backup file size (bytes) - 10GB default
BACKUP_MAX_FILE_SIZE = 10*1024*1024*1024

# Enable/disable backup compression
BACKUP_USE_COMPRESSION = True

# Backup file permissions (octal)
BACKUP_FILE_PERMISSIONS = 0o600

# Enable backup encryption (requires cryptography package)
BACKUP_USE_ENCRYPTION = False
BACKUP_ENCRYPTION_KEY = None  # Set in .env for production
```

### 3. Directory Structure

Create the backup directories:

```bash
mkdir -p backups_data/{media,database,archives}
```

### 4. Permissions

Ensure proper permissions for backup directories:

```bash
chmod 750 backups_data
chmod 700 backups_data/{media,database,archives}
```

## Usage

### Web Interface

Access the backup system through the web interface:

```
http://your-domain/backups/
```

The web interface provides:
- **Dashboard**: Overview of recent backups and system statistics
- **Create Backup**: Form to create new backups with various options
- **Backup List**: View all backups with filtering and search
- **Backup Details**: Detailed information about individual backups
- **Restore Interface**: Safe restore operations with confirmation

### Management Commands

#### Create Backup

```bash
# Create a full backup (database + media)
python manage.py create_backup_safe --name "Full Backup" --type full

# Create database-only backup
python manage.py create_backup_safe --name "DB Backup" --type database

# Create media-only backup
python manage.py create_backup_safe --name "Media Backup" --type media

# Create backup with compression
python manage.py create_backup_safe --name "Compressed Backup" --compress

# Create backup excluding certain apps
python manage.py create_backup_safe --name "Selective Backup" --exclude-apps auth sessions

# Background backup (non-blocking)
python manage.py create_backup_safe --name "Background Backup" --background
```

#### Restore Backup

```bash
# Restore a backup (with confirmation prompts)
python manage.py restore_backup_safe <backup-id>

# Restore with pre-restore backup (recommended)
python manage.py restore_backup_safe <backup-id> --create-pre-backup

# Dry run (test without making changes)
python manage.py restore_backup_safe <backup-id> --dry-run

# Force restore without confirmations (dangerous)
python manage.py restore_backup_safe <backup-id> --force --no-input

# Selective restore (specific models only)
python manage.py restore_backup_safe <backup-id> --models auth.User products.Product
```

### REST API

#### Authentication

All API endpoints require authentication. Use Django's session authentication or JWT tokens.

#### Endpoints

```bash
# List all backups
GET /backups/api/backups/

# Create new backup
POST /backups/api/backups/
{
    "name": "API Backup",
    "backup_type": "full",
    "description": "Created via API",
    "include_media": true,
    "compress_backup": true
}

# Get backup details
GET /backups/api/backups/{id}/

# Delete backup
DELETE /backups/api/backups/{id}/

# Verify backup integrity
POST /backups/api/backups/{id}/verify/

# Get backup download info
GET /backups/api/backups/{id}/download/

# Monitor backup progress
GET /backups/api/backups/{id}/progress/

# Create restore operation
POST /backups/api/backups/{id}/restore/
{
    "restore_mode": "replace",
    "create_pre_backup": true,
    "verify_before_restore": true,
    "description": "API restore"
}

# Get system statistics
GET /backups/api/statistics/
```

### Python API

```python
from backups.utils import BackupUtilities
from backups.models import Backup

# Create backup programmatically
backup = BackupUtilities.create_backup(
    name="Programmatic Backup",
    backup_type='full',
    include_media=True,
    compress=True,
    description="Created from Python code"
)

# Restore backup
success = BackupUtilities.restore_backup(
    backup_id=backup.id,
    create_pre_backup=True,
    verify_integrity=True
)

# Verify backup integrity
is_valid = BackupUtilities.verify_backup_integrity(backup.id)

# Get backup statistics
stats = BackupUtilities.get_backup_statistics()
```

## Backup Types

### Full Backup
- **Database**: All tables and data with foreign key dependencies
- **Media Files**: Uploaded files, images, and media assets
- **Metadata**: Complete system information and checksums

### Database Backup
- **Structure**: Table schemas and relationships
- **Data**: All records with proper ordering for foreign keys
- **Indexes**: Database indexes and constraints
- **Sequences**: Auto-increment sequences and counters

### Media Backup
- **Files**: All files in `MEDIA_ROOT` directory
- **Structure**: Directory structure preservation
- **Metadata**: File permissions and timestamps
- **Integrity**: Checksum verification for each file

## Safety Features

### Foreign Key Handling
The system automatically handles foreign key relationships:

1. **Dependency Analysis**: Analyzes model relationships
2. **Topological Sorting**: Orders models for safe backup/restore
3. **Constraint Handling**: Temporarily disables constraints during restore
4. **Integrity Verification**: Validates relationships after restore

### Pre-Restore Backup
Before any restore operation, the system can:

1. **Current State Backup**: Create backup of current data
2. **Rollback Capability**: Ability to revert if restore fails
3. **Safety Net**: Prevents data loss during restore operations

### Verification
Multiple verification layers ensure data integrity:

1. **Checksum Verification**: SHA-256 hashes for all files
2. **File Existence**: Verify all backup files exist
3. **Size Validation**: Confirm file sizes match expectations
4. **Database Integrity**: Validate foreign key relationships

## Scheduling & Automation

### Setting Up Automated Backups

1. **Create Backup Schedule** (via web interface or admin):
   - Schedule name and description
   - Backup frequency (daily, weekly, monthly)
   - Backup type and options
   - Retention policy

2. **Cron Job Setup**:
   ```bash
   # Daily backup at 2 AM
   0 2 * * * /path/to/python /path/to/manage.py create_backup_safe --name "Daily Auto Backup" --type full --compress
   
   # Weekly backup on Sunday at 3 AM
   0 3 * * 0 /path/to/python /path/to/manage.py create_backup_safe --name "Weekly Backup" --type full --compress
   
   # Monthly cleanup of old backups
   0 4 1 * * /path/to/python /path/to/manage.py cleanup_old_backups --days 30
   ```

### Monitoring & Alerts

Set up monitoring for backup operations:

1. **Log Monitoring**: Check backup logs for errors
2. **Email Alerts**: Configure email notifications for failures
3. **Disk Space**: Monitor backup storage usage
4. **Backup Verification**: Regularly verify backup integrity

## Security Considerations

### File Permissions
- Backup files are created with restricted permissions (600)
- Backup directories should have limited access
- Database backups contain sensitive information

### Encryption
- Optional backup encryption for sensitive data
- Requires `cryptography` package
- Use strong encryption keys stored securely

### Access Control
- Web interface requires authentication
- API endpoints require proper permissions
- Admin interface follows Django's permission system

### Network Security
- Backup files should not be exposed via web server
- Use HTTPS for web interface access
- Secure backup file transfers if needed

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Fix backup directory permissions
sudo chown -R www-data:www-data backups_data/
sudo chmod -R 750 backups_data/
```

#### 2. Disk Space Issues
```bash
# Check disk usage
df -h
du -sh backups_data/

# Clean up old backups
python manage.py cleanup_old_backups --days 7
```

#### 3. Memory Issues with Large Databases
```python
# Use chunked processing for large tables
BACKUP_CHUNK_SIZE = 1000  # Process records in batches
```

#### 4. Foreign Key Constraint Errors
- Ensure all related models are included in backup
- Check for circular dependencies
- Verify backup was created properly

### Debug Mode

Enable debug logging for backup operations:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'backup_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'backups_debug.log',
        },
    },
    'loggers': {
        'backups': {
            'handlers': ['backup_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Performance Optimization

#### Large Databases
- Use compression to reduce file sizes
- Process data in chunks for memory efficiency
- Schedule backups during low-usage periods

#### Storage Optimization
- Regular cleanup of old backups
- Use external storage for backup archives
- Implement backup rotation policies

## Best Practices

### Backup Strategy
1. **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
2. **Regular Schedule**: Daily incremental, weekly full backups
3. **Test Restores**: Regularly test backup restore procedures
4. **Monitor Storage**: Keep track of backup storage usage

### Security
1. **Encrypt Sensitive Backups**: Use encryption for production data
2. **Secure Storage**: Store backups in secure locations
3. **Access Control**: Limit backup system access
4. **Audit Logs**: Monitor backup operations

### Monitoring
1. **Backup Success**: Monitor backup completion
2. **Storage Usage**: Track disk space consumption
3. **Restore Testing**: Regularly test restore operations
4. **Performance**: Monitor backup/restore performance

## Integration Examples

### Backup with CI/CD
```yaml
# .github/workflows/backup.yml
name: Database Backup
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Create Backup
        run: |
          python manage.py create_backup_safe --name "CI Backup" --type full
```

### Backup with Docker
```dockerfile
# Add backup service to docker-compose.yml
backup:
  build: .
  volumes:
    - ./backups_data:/app/backups_data
  environment:
    - DJANGO_SETTINGS_MODULE=project.settings.production
  command: python manage.py create_backup_safe --name "Docker Backup" --type full
```

### Custom Backup Logic
```python
from backups.models import Backup
from backups.utils import BackupUtilities

def custom_backup_workflow():
    """Custom backup workflow with error handling"""
    try:
        # Create backup
        backup = BackupUtilities.create_backup(
            name="Custom Workflow Backup",
            backup_type='full',
            include_media=True,
            compress=True
        )
        
        # Verify integrity
        if BackupUtilities.verify_backup_integrity(backup.id):
            print(f"Backup {backup.id} created and verified successfully")
            return backup
        else:
            print(f"Backup {backup.id} failed integrity check")
            return None
            
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return None
```

## Support & Maintenance

### Regular Maintenance Tasks
- Clean up old backup files
- Verify backup integrity
- Monitor disk space usage
- Test restore procedures
- Update backup schedules as needed

### Backup System Health Check
```python
def backup_health_check():
    """Perform comprehensive backup system health check"""
    from backups.utils import BackupUtilities
    
    # Check recent backups
    recent_backups = Backup.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Check storage space
    storage_info = BackupUtilities.get_storage_info()
    
    # Check failed backups
    failed_backups = Backup.objects.filter(
        status='failed',
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    return {
        'recent_backups': recent_backups,
        'storage_usage': storage_info,
        'failed_backups': failed_backups,
        'health_status': 'good' if failed_backups == 0 else 'warning'
    }
```

## Conclusion

This backup system provides enterprise-grade backup and restore capabilities for your Django application. It includes comprehensive safety features, multiple interfaces, and extensive customization options to meet various backup requirements.

For additional support or feature requests, consult the system logs, verify configurations, and ensure all dependencies are properly installed.

---

**Important**: Always test backup and restore procedures in a development environment before using in production. Regular testing of restore operations is crucial for ensuring backup reliability.