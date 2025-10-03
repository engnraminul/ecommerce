#!/usr/bin/env python
"""
Create test admin user for stock management testing
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append('/path/to/your/project')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_admin():
    """Create a test admin user"""
    try:
        # Check if admin user already exists
        if User.objects.filter(username='testadmin').exists():
            user = User.objects.get(username='testadmin')
            print(f"Test admin user already exists: {user.username}")
        else:
            # Create admin user
            user = User.objects.create_superuser(
                username='testadmin',
                email='testadmin@example.com',
                password='testadmin123',
                first_name='Test',
                last_name='Admin'
            )
            print(f"Created test admin user: {user.username}")
        
        print(f"Login credentials:")
        print(f"Username: testadmin")
        print(f"Password: testadmin123")
        print(f"URL: http://127.0.0.1:8000/mb-admin/login/")
        
        return user
    except Exception as e:
        print(f"Error creating test admin: {e}")
        return None

if __name__ == '__main__':
    create_test_admin()