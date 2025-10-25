#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from users.models import User

def test_login_behaviors():
    """Test login behaviors using Django test client"""
    
    client = Client()
    
    print("=== Test 1: Unverified user with correct password ===")
    try:
        response = client.post('/login/', {
            'email': 'phonekobra@gmail.com',
            'password': 'sathi3065'
        })
        
        print(f'Response status code: {response.status_code}')
        print(f'Response redirect: {response.url if hasattr(response, "url") else "No redirect"}')
        
        # Check if there are any messages in the response context
        if hasattr(response, 'context') and response.context:
            messages = response.context.get('messages', [])
            if messages:
                for message in messages:
                    print(f'Message: "{message}" (Level: {message.level})')
        
        # Check response content for message
        content = response.content.decode('utf-8')
        if 'Account is not active' in content:
            print('✅ Found expected message: "Account is not active"')
        elif 'Invalid email or password' in content:
            print('❌ Found unexpected message: "Invalid email or password"')
        else:
            print('❓ No specific message found in response')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    print("=== Test 2: Wrong password ===")
    try:
        response = client.post('/login/', {
            'email': 'phonekobra@gmail.com',
            'password': 'wrongpassword'
        })
        
        print(f'Response status code: {response.status_code}')
        
        # Check response content for message
        content = response.content.decode('utf-8')
        if 'Invalid email or password' in content:
            print('✅ Found expected message: "Invalid email or password"')
        elif 'Account is not active' in content:
            print('❌ Found unexpected message: "Account is not active"')
        else:
            print('❓ No specific message found in response')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    print("=== Test 3: Non-existent user ===")
    try:
        response = client.post('/login/', {
            'email': 'nonexistent@example.com',
            'password': 'anypassword'
        })
        
        print(f'Response status code: {response.status_code}')
        
        # Check response content for message
        content = response.content.decode('utf-8')
        if 'Invalid email or password' in content:
            print('✅ Found expected message: "Invalid email or password"')
        else:
            print('❓ No specific message found in response')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_behaviors()