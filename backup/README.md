# Backup Management System

A comprehensive backup and restore system for Django ecommerce application with support for database backups, media file backups, and scheduled backups.

## Features

### ✨ Core Features
- **Database Backup**: MySQL database backup using mysqldump
- **Media File Backup**: Complete media directory backup using tar.gz compression
- **Combined Backups**: Full system backup (database + media files)
- **File Upload Restore**: Upload and restore from external backup files
- **Scheduled Backups**: Automated daily, weekly, and monthly backup scheduling
- **Professional Dashboard**: Modern web interface for backup management
- **REST API**: Complete API for programmatic backup operations

### 🛡️ Security & Safety Features
- **Pre-Restore Backup**: Automatically create backup before restore operations
- **File Validation**: Validate backup file integrity before operations
- **User Permissions**: Superuser-only access to backup functions
- **Error Handling**: Comprehensive error logging and user feedback
- **Safe Restore**: Option to overwrite or preserve existing data

### 🔧 Management Features
- **Retention Policies**: Automatic cleanup of old backups
- **Progress Tracking**: Real-time backup/restore progress monitoring  
- **File Management**: Download, delete, and manage backup files
- **Statistics Dashboard**: Backup success rates and storage analytics
- **Email Notifications**: Optional email alerts for backup status

## Installation & Setup

### 1. App Configuration
The backup app is already added to `INSTALLED_APPS` in settings.py:
```python
INSTALLED_APPS = [
    # ... other apps
    'backup.apps.BackupConfig',
]
```

### 2. Database Migration
Run migrations to create backup tables:
```bash
python manage.py makemigrations backup
python manage.py migrate
```

### 3. URL Configuration
Backup URLs are included in the main project:
```python
# In ecommerce_project/urls.py
path('backup/', include('backup.urls')),
```

### 4. Settings Configuration
The following settings are available in `settings.py`:
```python
# Backup System Settings
BACKUP_DIRECTORY = 'backups/'
BACKUP_RETENTION_DAYS = 30
BACKUP_AUTO_CLEANUP = True

# MySQL Backup Settings
BACKUP_MYSQL_PATH = 'mysqldump'
BACKUP_MYSQL_HOST = '127.0.0.1'
BACKUP_MYSQL_PORT = 3306
BACKUP_MYSQL_USER = 'root'
BACKUP_MYSQL_PASSWORD = 'your_password'
BACKUP_MYSQL_DATABASE = 'your_database'

# Backup Compression Settings
BACKUP_COMPRESSION_LEVEL = 6

# Backup Notification Settings
BACKUP_EMAIL_NOTIFICATIONS = False
BACKUP_NOTIFICATION_EMAIL = ''
```

## Usage

### Dashboard Access
Navigate to `/backup/` in your browser to access the backup management dashboard. Only superusers can access this interface.

### Creating Backups

#### Via Web Interface
1. Go to **Dashboard > Backup Management**
2. Click **"Create Backup"**
3. Choose backup type:
   - **Database Only**: MySQL database backup
   - **Media Only**: Media files backup  
   - **Full Backup**: Database + Media files
4. Configure options (compression, exclude logs)
5. Click **"Start Backup"**

#### Via Management Commands
```bash
# Create a manual backup
python manage.py create_backup --name "Manual Backup" --type full

# Create database-only backup
python manage.py create_backup --name "DB Backup" --type database

# Create media-only backup without compression
python manage.py create_backup --name "Media Backup" --type media --no-compress
```

### Restoring from Backups

#### Restore from Existing Backup
1. Go to **Restores** tab
2. Click **"Restore from Backup"**
3. Select backup from list
4. Choose restore type and options
5. Click **"Start Restore"**

#### Upload and Restore
1. Go to **Restores** tab
2. Click **"Upload & Restore"**
3. Upload database (.sql, .sql.gz) and/or media (.tar.gz, .zip) files
4. Configure restore options
5. Click **"Upload & Restore"**

### Scheduling Backups

#### Via Web Interface
1. Go to **Schedules** tab
2. Click **"Create Schedule"**
3. Configure schedule:
   - **Daily**: Runs every day at specified time
   - **Weekly**: Runs on specified day of week
   - **Monthly**: Runs on specified day of month
4. Set retention period and options
5. Click **"Create Schedule"**

#### Via Cron Job
Add to your system crontab:
```bash
# Run scheduled backups every hour
0 * * * * cd /path/to/project && python manage.py run_scheduled_backups

# Daily cleanup of old backups at 3 AM
0 3 * * * cd /path/to/project && python manage.py cleanup_old_backups
```

## API Reference

### Authentication
All API endpoints require authentication. Use session authentication or JWT tokens.

### Endpoints

#### Backups
- `GET /backup/api/backups/` - List all backups
- `POST /backup/api/backups/` - Create new backup
- `GET /backup/api/backups/{id}/` - Get backup details
- `DELETE /backup/api/backups/{id}/` - Delete backup
- `POST /backup/api/backups/{id}/download/` - Download backup file

#### Restores
- `GET /backup/api/restores/` - List all restores
- `POST /backup/api/restores/` - Create new restore
- `POST /backup/api/restores/upload_and_restore/` - Upload and restore

#### Schedules
- `GET /backup/api/schedules/` - List backup schedules
- `POST /backup/api/schedules/` - Create backup schedule
- `PUT /backup/api/schedules/{id}/` - Update schedule
- `POST /backup/api/schedules/{id}/toggle_active/` - Toggle schedule

#### Statistics
- `GET /backup/api/statistics/` - Get backup statistics
- `GET /backup/api/available-backups/` - Get available backups for restore

### Example API Usage

#### Create Backup
```python
import requests

response = requests.post('/backup/api/backups/', {
    'name': 'API Test Backup',
    'backup_type': 'full',
    'description': 'Created via API',
    'compress': True,
    'exclude_logs': True
})
```

#### Upload and Restore
```python
files = {
    'database_file': open('backup.sql.gz', 'rb'),
    'media_file': open('media.tar.gz', 'rb')
}
data = {
    'name': 'API Restore',
    'restore_type': 'full',
    'backup_before_restore': True
}

response = requests.post('/backup/api/restores/upload_and_restore/', 
                        data=data, files=files)
```

## Management Commands

### Create Backup
```bash
python manage.py create_backup --name "Backup Name" --type [database|media|full] [options]

Options:
  --description TEXT     Optional backup description
  --no-compress         Disable compression
  --include-logs        Include log files in media backup
```

### Run Scheduled Backups
```bash
python manage.py run_scheduled_backups [options]

Options:
  --force              Force run all schedules
  --schedule-id ID     Run specific schedule
  --dry-run           Show what would run without executing
```

### Cleanup Old Backups
```bash
python manage.py cleanup_old_backups [options]

Options:
  --days DAYS         Override retention days
  --dry-run          Show what would be deleted
  --force            Force cleanup even if disabled
```

## File Structure

```
backup/
├── __init__.py
├── apps.py
├── models.py          # Backup data models
├── services.py        # Core backup/restore logic
├── views.py           # API views and dashboard
├── urls.py            # URL patterns
├── admin.py           # Django admin interface
├── serializers.py     # API serializers
├── signals.py         # Django signals
├── tests.py           # Unit tests
├── management/
│   └── commands/
│       ├── create_backup.py
│       ├── run_scheduled_backups.py
│       └── cleanup_old_backups.py
├── templates/
│   └── backup/
│       ├── dashboard.html
│       └── modals.html
└── static/
    └── backup/
        └── js/
            └── backup-dashboard.js
```

## Models

### BackupRecord
Stores backup information including files, sizes, status, and metadata.

### RestoreRecord  
Tracks restore operations with source backup or uploaded files.

### BackupSchedule
Defines automated backup schedules with timing and retention settings.

### BackupSettings
Global backup configuration including paths, credentials, and preferences.

## Security Considerations

1. **Access Control**: Only superusers can access backup functions
2. **File Permissions**: Backup files are stored in protected media directory
3. **Database Credentials**: MySQL credentials are stored in Django settings
4. **Pre-Restore Backups**: Automatic backup creation before restore operations
5. **File Validation**: Uploaded files are validated before processing

## Troubleshooting

### Common Issues

#### MySQL Connection Errors
- Verify MySQL credentials in settings
- Check if mysqldump is installed and accessible
- Ensure MySQL server is running

#### Permission Errors
- Check file system permissions for backup directory
- Verify Django has write access to media folder
- Ensure backup user has database privileges

#### Large File Handling
- Increase Django's `FILE_UPLOAD_MAX_MEMORY_SIZE` for large uploads
- Configure web server timeout for long-running operations
- Use appropriate compression levels for balance between size and speed

#### Disk Space Issues
- Monitor backup directory size
- Configure retention policies appropriately
- Set up automatic cleanup schedules

### Logging
Backup operations are logged to Django's logging system. Check logs for detailed error information:
- Backup creation/failure logs
- Restore operation logs  
- Cleanup operation logs
- Schedule execution logs

## Performance Tips

1. **Compression**: Use appropriate compression levels (1-9)
2. **Scheduling**: Run large backups during off-peak hours
3. **Retention**: Set reasonable retention periods to manage disk usage
4. **Exclusions**: Exclude unnecessary files (logs, temp files) from media backups
5. **Monitoring**: Monitor backup sizes and execution times

## Contributing

When contributing to the backup system:

1. Follow Django best practices
2. Add tests for new functionality
3. Update documentation for API changes
4. Consider backward compatibility
5. Test with different backup sizes and types

## License

This backup system is part of the Django ecommerce project and follows the same licensing terms.