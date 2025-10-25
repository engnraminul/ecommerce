#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

import json
from django.test import Client

def test_api_login():
    """Test API login with unverified user"""
    
    client = Client()
    
    print("=== Testing API Login with Unverified User ===")
    print("Email: phonekobra@gmail.com")
    print("Password: sathi3065")
    print()
    
    # Test the API login endpoint
    response = client.post('/api/v1/users/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'sathi3065'
    }, content_type='application/json')
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
        
        if 'Account is not active' in str(response_data):
            print("✅ SUCCESS: Found 'Account is not active' message in API response")
        elif 'Invalid email or password' in str(response_data):
            print("❌ ISSUE: Found 'Invalid email or password' in API response")
        else:
            print("❓ Other response received")
            
    except Exception as e:
        print(f"Could not parse JSON response: {e}")
        print(f"Raw response content: {response.content.decode()}")
    
    print()
    
    # Test with wrong password
    print("=== Testing API Login with Wrong Password ===")
    print("Email: phonekobra@gmail.com")
    print("Password: wrongpassword")
    print()
    
    response = client.post('/api/v1/users/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'wrongpassword'
    }, content_type='application/json')
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
        
        if 'Invalid email or password' in str(response_data):
            print("✅ SUCCESS: Found 'Invalid email or password' for wrong password")
        else:
            print("❓ Unexpected response for wrong password")
            
    except Exception as e:
        print(f"Could not parse JSON response: {e}")

if __name__ == '__main__':
    test_api_login()