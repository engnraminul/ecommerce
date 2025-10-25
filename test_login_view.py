#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from frontend.views import user_login

def test_login_scenarios():
    """Test various login scenarios"""
    
    factory = RequestFactory()
    
    def create_request(email, password):
        """Helper to create a test request"""
        request = factory.post('/login/', {
            'email': email,
            'password': password,
            'remember_me': ''
        })
        
        # Add session middleware
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        # Add messages framework
        setattr(request, '_messages', FallbackStorage(request))
        
        # Set user to anonymous
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        
        return request
    
    # Test 1: Unverified user with correct password
    print("=== Test 1: Unverified user with correct password ===")
    try:
        request = create_request('phonekobra@gmail.com', 'sathi3065')
        response = user_login(request)
        
        print(f'Response status code: {response.status_code}')
        
        # Check messages
        messages = list(request._messages)
        print(f'Number of messages: {len(messages)}')
        for message in messages:
            print(f'Message: "{message.message}" (Level: {message.level})')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: Wrong password
    print("=== Test 2: Wrong password ===")
    try:
        request = create_request('phonekobra@gmail.com', 'wrongpassword')
        response = user_login(request)
        
        print(f'Response status code: {response.status_code}')
        
        # Check messages
        messages = list(request._messages)
        print(f'Number of messages: {len(messages)}')
        for message in messages:
            print(f'Message: "{message.message}" (Level: {message.level})')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Non-existent user
    print("=== Test 3: Non-existent user ===")
    try:
        request = create_request('nonexistent@example.com', 'anypassword')
        response = user_login(request)
        
        print(f'Response status code: {response.status_code}')
        
        # Check messages
        messages = list(request._messages)
        print(f'Number of messages: {len(messages)}')
        for message in messages:
            print(f'Message: "{message.message}" (Level: {message.level})')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_scenarios()