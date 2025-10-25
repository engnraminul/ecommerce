#!/usr/bin/env python
"""
Simple test to see what actually happens in the browser
"""
import os
import django
from django.test import Client
from django.contrib.messages import get_messages

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def check_login_page():
    """Check what the login page actually contains"""
    client = Client()
    
    print("=== Checking Login Page Content ===")
    
    # Get the login page
    response = client.get('/login/')
    content = response.content.decode('utf-8')
    
    print(f"Login page status: {response.status_code}")
    
    # Check if JavaScript is properly loaded
    if 'app.js' in content:
        print("✅ app.js is loaded in the page")
    else:
        print("⚠️  app.js not found in the page")
    
    # Test login attempt
    print("\n=== Testing Login with Unverified User ===")
    
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com', 
        'password': 'sathi3065'
    })
    
    print(f"Response status: {response.status_code}")
    print(f"Response redirect: {response.get('Location', 'No redirect')}")
    
    # Get messages
    messages = list(get_messages(response.wsgi_request))
    print(f"Messages: {[str(msg) for msg in messages]}")
    
    # Check response content
    content = response.content.decode('utf-8')
    
    # Look for the error message in the actual HTML content
    if 'Account is not active' in content:
        print("✅ SUCCESS: 'Account is not active' found in response HTML")
    elif 'Invalid email or password' in content:
        print("❌ PROBLEM: 'Invalid email or password' found instead")
    else:
        print("⚠️  UNCLEAR: No clear error message found in HTML")
    
    # Check for notification elements
    if 'notification-error' in content:
        print("🔍 Found notification-error class in HTML")
    if 'alert-error' in content:
        print("🔍 Found alert-error class in HTML")
    if 'alert-danger' in content:
        print("🔍 Found alert-danger class in HTML")

if __name__ == '__main__':
    check_login_page()