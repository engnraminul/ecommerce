#!/usr/bin/env python
"""
Test script to simulate browser login and check Django messages
"""
import os
import django
from django.test import Client
from django.contrib.messages import get_messages

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def test_browser_login():
    """Test login behavior as a browser would see it"""
    client = Client()
    
    print("=== Testing Browser Login Behavior ===")
    
    # Test 1: Login with unverified user
    print("\n--- Test 1: Unverified User Login ---")
    print("Email: phonekobra@gmail.com")
    print("Password: sathi3065")
    print("Simulating browser form submission...")
    
    # First get the login page to get CSRF token
    response = client.get('/login/')
    print(f"Login page status: {response.status_code}")
    
    # Submit login form (follow=True to follow redirects)
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'sathi3065'
    }, follow=True)
    
    print(f"Login response status: {response.status_code}")
    print(f"Final URL: {response.request['PATH_INFO']}")
    
    # Get messages from the response context
    messages = list(get_messages(response.wsgi_request))
    print(f"Django messages: {[str(msg) for msg in messages]}")
    
    # Check the actual content of the response
    content = response.content.decode('utf-8')
    
    # Look for specific message text in the HTML
    if 'Account is not active' in content:
        print("✅ SUCCESS: Found 'Account is not active' message in HTML")
    elif 'Invalid email or password' in content:
        print("❌ ISSUE: Found 'Invalid email or password' message in HTML")
    else:
        print("⚠️  UNKNOWN: No recognizable error message found in HTML")
    
    # Look for notification divs
    if 'notification-error' in content:
        print("🔍 Found notification-error in HTML")
    if 'alert-error' in content or 'alert-danger' in content:
        print("🔍 Found alert-error/alert-danger in HTML")
    
    # Test 2: Login with wrong password 
    print("\n--- Test 2: Wrong Password Login ---")
    print("Email: phonekobra@gmail.com")
    print("Password: wrongpassword")
    
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'wrongpassword'
    }, follow=True)
    
    messages = list(get_messages(response.wsgi_request))
    print(f"Django messages: {[str(msg) for msg in messages]}")
    
    content = response.content.decode('utf-8')
    if 'Invalid email or password' in content:
        print("✅ SUCCESS: Found 'Invalid email or password' for wrong password")
    else:
        print("❌ ISSUE: Expected 'Invalid email or password' message not found")

if __name__ == '__main__':
    test_browser_login()