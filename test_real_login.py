#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

import logging
from django.test import Client
from django.contrib.messages import get_messages

# Set up logging to see our debug messages
logging.basicConfig(level=logging.INFO)

def test_real_login_scenarios():
    """Test login scenarios exactly as they happen in the browser"""
    
    client = Client()
    
    print("=== Testing Unverified User Login ===")
    print("Email: phonekobra@gmail.com")
    print("Password: sathi3065")
    print()
    
    # Test the exact form data that would be sent from the browser
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'sathi3065',
        'remember_me': '',  # Unchecked checkbox
        'csrfmiddlewaretoken': client.cookies.get('csrftoken', '').value if 'csrftoken' in client.cookies else '',
    }, follow=False)  # Don't follow redirects
    
    print(f"Response status: {response.status_code}")
    print(f"Response type: {type(response).__name__}")
    
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
    else:
        print("No redirect")
    
    # Check for messages in the response context
    if hasattr(response, 'context') and response.context:
        messages = list(get_messages(response.wsgi_request))
        print(f"Django messages count: {len(messages)}")
        for message in messages:
            print(f"  - {message.tags}: {message}")
    else:
        print("No response context available")
    
    # Check the actual response content
    content = response.content.decode('utf-8')
    
    # Look for error messages in the HTML
    if 'Account is not active' in content:
        print("✅ SUCCESS: Found 'Account is not active' message in response")
    elif 'Invalid email or password' in content:
        print("❌ ISSUE: Found 'Invalid email or password' instead")
    else:
        print("❓ No specific error message found")
        # Search for any error-related content
        if 'alert-error' in content or 'alert-danger' in content:
            print("Found error alert div in HTML")
        
    print("\n" + "="*50 + "\n")
    
    # Test wrong password
    print("=== Testing Wrong Password ===")
    print("Email: phonekobra@gmail.com")
    print("Password: wrongpassword")
    print()
    
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'wrongpassword',
        'remember_me': '',
    })
    
    content = response.content.decode('utf-8')
    
    if 'Invalid email or password' in content:
        print("✅ SUCCESS: Found 'Invalid email or password' message")
    else:
        print("❌ ISSUE: Expected 'Invalid email or password' message not found")

if __name__ == '__main__':
    test_real_login_scenarios()