#!/usr/bin/env python
"""
Test script to verify frontend login view behavior
for both unverified users and wrong password scenarios.
"""
import os
import django
from django.test import TestCase, Client
from django.contrib.messages import get_messages
from django.urls import reverse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def test_frontend_login():
    """Test frontend login view with different scenarios"""
    client = Client()
    
    print("=== Testing Frontend Login View ===")
    
    # Test 1: Unverified user
    print("\n--- Test 1: Unverified User ---")
    print("Email: phonekobra@gmail.com")
    print("Password: sathi3065")
    
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'sathi3065'
    }, follow=True)
    
    print(f"Response status: {response.status_code}")
    
    # Get messages from the response
    messages = list(get_messages(response.wsgi_request))
    print(f"Messages: {[str(m) for m in messages]}")
    
    # Check if the correct message is present
    activation_message_found = any('Account is not active' in str(message) for message in messages)
    
    if activation_message_found:
        print("✅ SUCCESS: Found 'Account is not active' message")
    else:
        print("❌ FAIL: 'Account is not active' message not found")
        print("Available messages:", [str(m) for m in messages])
    
    # Test 2: Wrong password
    print("\n--- Test 2: Wrong Password ---")
    print("Email: phonekobra@gmail.com")
    print("Password: wrongpassword")
    
    response = client.post('/login/', {
        'email': 'phonekobra@gmail.com',
        'password': 'wrongpassword'
    }, follow=True)
    
    print(f"Response status: {response.status_code}")
    
    # Get messages from the response
    messages = list(get_messages(response.wsgi_request))
    print(f"Messages: {[str(m) for m in messages]}")
    
    # Check if the correct message is present
    invalid_message_found = any('Invalid email or password' in str(message) for message in messages)
    
    if invalid_message_found:
        print("✅ SUCCESS: Found 'Invalid email or password' message")
    else:
        print("❌ FAIL: 'Invalid email or password' message not found")
        print("Available messages:", [str(m) for m in messages])

if __name__ == '__main__':
    test_frontend_login()