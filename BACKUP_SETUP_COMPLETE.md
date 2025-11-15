# Quick Setup Instructions for Backup System

## ✅ Current Status
The backup system has been successfully created and is running with SQLite for development. All migrations have been applied and the server is running.

## 🔄 To Switch Back to MySQL (Optional)

### 1. Install MySQL Client Library
```bash
pip install mysqlclient
```

**If you encounter installation issues on Windows:**
```bash
# Alternative approach - install using conda
conda install mysqlclient

# Or use PyMySQL as alternative
pip install PyMySQL
# Then add this to settings.py:
import pymysql
pymysql.install_as_MySQLdb()
```

### 2. Update Database Settings
In `ecommerce_project/settings.py`, uncomment the MySQL configuration:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'manob_bazar',
        'USER': 'root',
        'PASSWORD': 'aminul3065',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

### 3. Run Migrations on MySQL
```bash
python manage.py migrate
```

## 🚀 Access the Backup System

### 1. Create a Superuser (if not already created)
```bash
python manage.py createsuperuser
```

### 2. Access the Dashboard
- Open your browser and go to: `http://localhost:8000/mb-admin/`
- Login with your superuser credentials
- Click on the **"Backup"** tab in the sidebar

### 3. Alternative Direct Access
- Go directly to: `http://localhost:8000/backup/`

## ⭐ Key Features Available

### ✅ Backup Creation
- **Database Only**: SQLite/MySQL backup
- **Media Only**: Complete media files backup
- **Full Backup**: Database + Media files combined

### ✅ Restore Features
- Restore from existing backups
- Upload external backup files
- Safe restore with pre-backup option

### ✅ Management Features
- Scheduled backups (daily/weekly/monthly)
- Automatic cleanup of old backups
- Download backup files
- Statistics dashboard

### ✅ Command Line Interface
```bash
# Create manual backup
python manage.py create_backup --name "Manual Backup" --type full

# Run scheduled backups
python manage.py run_scheduled_backups

# Cleanup old backups
python manage.py cleanup_old_backups
```

## 🔧 Current Configuration
- **Database**: SQLite (for development)
- **Backup Storage**: `media/backups/`
- **Access**: Superuser only
- **Status**: ✅ Fully functional

## 📁 File Locations
- **Dashboard**: `/backup/` or via dashboard sidebar
- **API Endpoints**: `/backup/api/`
- **Settings**: Configure in the Settings tab
- **Backup Files**: Stored in `media/backups/`

## 🎯 Next Steps
1. Access the backup dashboard
2. Configure backup settings if needed
3. Create your first backup
4. Optionally set up scheduled backups
5. Switch to MySQL when ready (follow instructions above)

---

**✅ The backup system is now ready to use!** All features are working with SQLite, and you can easily switch to MySQL later when needed.