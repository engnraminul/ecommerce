#!/usr/bin/env python
"""
Debug script to test the actual API response for backup restore
"""
import os
import sys
import django
import json
import requests
from urllib.parse import urljoin

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from backups.models import Backup

def test_api_response():
    print("=== Testing API Response ===")
    
    # Get the backup with name "1"
    try:
        backup = Backup.objects.get(name="1")
        print(f"Testing with backup: {backup.name} (ID: {backup.id})")
    except Backup.DoesNotExist:
        print("Error: Backup with name '1' not found")
        return
    
    # Create a test client
    client = Client()
    
    # Get a user (assuming we have one)
    User = get_user_model()
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        
        if user:
            client.force_login(user)
            print(f"Logged in as: {user.email}")
        else:
            print("No user found - testing without authentication")
    except Exception as e:
        print(f"User setup error: {e}")
    
    # Test the restore API
    url = f'/backups/api/backups/{backup.id}/restore/'
    
    # Test data
    test_data = {
        'restore_type': '',  # Same as backup
        'validate_only': False
    }
    
    print(f"\nMaking POST request to: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = client.post(
            url, 
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.items())}")
        
        try:
            response_data = response.json()
            print(f"Response JSON:\n{json.dumps(response_data, indent=2)}")
            
            # Check if the expected fields exist
            expected_fields = ['success', 'validation_passed', 'validation_notes', 'error_message']
            print(f"\nField Analysis:")
            for field in expected_fields:
                if field in response_data:
                    print(f"  ✓ {field}: {response_data[field]}")
                else:
                    print(f"  ✗ {field}: MISSING")
                    
        except Exception as json_error:
            print(f"JSON Parse Error: {json_error}")
            print(f"Raw Response: {response.content}")
            
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == '__main__':
    test_api_response()