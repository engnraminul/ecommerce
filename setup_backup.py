#!/usr/bin/env python
"""
Backup System Setup Script
Run this script to initialize the backup system after installation.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth.models import User
from backup.models import BackupSettings
from django.conf import settings


def setup_backup_system():
    """Initialize the backup system"""
    print("🔧 Setting up Backup Management System...")
    
    # 1. Create backup directory
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    print(f"✅ Created backup directory: {backup_dir}")
    
    # 2. Initialize backup settings
    settings_obj = BackupSettings.get_settings()
    
    # Update with Django settings if available
    if hasattr(settings, 'BACKUP_MYSQL_HOST'):
        settings_obj.mysql_host = settings.BACKUP_MYSQL_HOST
    if hasattr(settings, 'BACKUP_MYSQL_PORT'):
        settings_obj.mysql_port = settings.BACKUP_MYSQL_PORT
    if hasattr(settings, 'BACKUP_MYSQL_USER'):
        settings_obj.mysql_user = settings.BACKUP_MYSQL_USER
    if hasattr(settings, 'BACKUP_MYSQL_PASSWORD'):
        settings_obj.mysql_password = settings.BACKUP_MYSQL_PASSWORD
    if hasattr(settings, 'BACKUP_MYSQL_DATABASE'):
        settings_obj.mysql_database = settings.BACKUP_MYSQL_DATABASE
    
    settings_obj.save()
    print("✅ Initialized backup settings")
    
    # 3. Check mysqldump availability
    import subprocess
    try:
        result = subprocess.run(['mysqldump', '--version'], capture_output=True, text=True, check=True)
        print(f"✅ mysqldump found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Warning: mysqldump not found. Database backups may not work.")
        print("   Please install MySQL client tools or update BACKUP_MYSQL_PATH setting.")
    
    # 4. Test database connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️  Warning: Database connection test failed: {e}")
    
    # 5. Check superuser exists
    if User.objects.filter(is_superuser=True).exists():
        print("✅ Superuser found - can access backup dashboard")
    else:
        print("⚠️  No superuser found. Create one to access backup dashboard:")
        print("   python manage.py createsuperuser")
    
    print("\n🎉 Backup system setup complete!")
    print(f"📁 Backup directory: {backup_dir}")
    print("🌐 Dashboard URL: /backup/")
    print("📚 Documentation: backup/README.md")
    
    # 6. Suggest next steps
    print("\n📋 Next Steps:")
    print("1. Visit /backup/ in your browser (superuser required)")
    print("2. Configure backup settings in the Settings tab")
    print("3. Create your first backup")
    print("4. Set up scheduled backups")
    print("5. Add cron jobs for automated scheduling:")
    print("   0 * * * * cd /path/to/project && python manage.py run_scheduled_backups")
    print("   0 3 * * * cd /path/to/project && python manage.py cleanup_old_backups")


def show_usage():
    """Show usage information"""
    print("Backup Management System Setup")
    print("Usage: python setup_backup.py")
    print("\nThis script will:")
    print("- Create backup directory")
    print("- Initialize backup settings")
    print("- Check system requirements")
    print("- Provide setup instructions")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_usage()
    else:
        try:
            setup_backup_system()
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            print("Please check your Django configuration and try again.")
            sys.exit(1)