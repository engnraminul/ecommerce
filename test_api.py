import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# Create test client
client = Client()

# Login as a superuser
User = get_user_model()
user = User.objects.filter(is_superuser=True).first()
if user:
    client.force_login(user)
    
    # Test the API endpoint
    response = client.get('/backup/api/available-backups/')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        import json
        data = response.json()
        print(f'Found {len(data)} backups:')
        for backup in data[:3]:  # Show first 3
            print(f"  - {backup['name']} ({backup['backup_type_display']})")
    else:
        print(f'Error: {response.content.decode()}')
else:
    print('No superuser found')