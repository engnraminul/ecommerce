#!/usr/bin/env python
"""
Test script for login error messages with unverified accounts.
"""
import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from users.models import User
from django.contrib.auth import authenticate
from django.test import Client, RequestFactory
from django.contrib.messages import get_messages

def test_login_error_messages():
    """Test login error messages for unverified accounts"""
    print("🔐 Testing Login Error Messages for Unverified Accounts")
    print("=" * 60)
    
    # Clean up any existing test user
    test_email = 'login.test@example.com'
    try:
        User.objects.filter(email=test_email).delete()
        print(f"🧹 Cleaned up existing user: {test_email}")
    except:
        pass
    
    print(f"\n📝 Creating unverified test user...")
    
    # Create unverified user
    try:
        user = User.objects.create_user(
            username='login_test',
            email=test_email,
            password='TestPassword123',
            first_name='Login',
            last_name='Test',
            is_active=True,
            is_email_verified=False
        )
        
        print(f"✅ Unverified user created: {user.email}")
        print(f"   - Is Active: {user.is_active}")
        print(f"   - Email Verified: {user.is_email_verified}")
        print(f"   - Can Login: {user.can_login()}")
        
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return
    
    print(f"\n🧪 Testing authentication backend...")
    
    # Test authentication directly
    auth_result = authenticate(username=test_email, password='TestPassword123')
    print(f"   - Direct authentication result: {auth_result}")
    print(f"   - Expected: None (blocked by custom backend)")
    
    print(f"\n🌐 Testing login view via Django test client...")
    
    # Test login view
    client = Client()
    
    # Attempt login with unverified user
    response = client.post('/login/', {
        'email': test_email,
        'password': 'TestPassword123'
    })
    
    print(f"   - Response status: {response.status_code}")
    print(f"   - Response redirect: {response.get('Location', 'No redirect')}")
    
    # Get messages from the response
    messages = list(get_messages(response.wsgi_request))
    if messages:
        for message in messages:
            print(f"   - Message: '{message}' (level: {message.level_tag})")
    else:
        print(f"   - No messages found")
    
    print(f"\n🧪 Testing with wrong password...")
    
    # Test with wrong password
    response_wrong_pass = client.post('/login/', {
        'email': test_email,
        'password': 'WrongPassword123'
    })
    
    print(f"   - Response status: {response_wrong_pass.status_code}")
    
    # Get messages from wrong password attempt
    messages_wrong = list(get_messages(response_wrong_pass.wsgi_request))
    if messages_wrong:
        for message in messages_wrong:
            print(f"   - Message: '{message}' (level: {message.level_tag})")
    else:
        print(f"   - No messages found")
    
    print(f"\n🧪 Testing with non-existent user...")
    
    # Test with non-existent user
    response_no_user = client.post('/login/', {
        'email': 'nonexistent@example.com',
        'password': 'TestPassword123'
    })
    
    print(f"   - Response status: {response_no_user.status_code}")
    
    # Get messages from non-existent user attempt
    messages_no_user = list(get_messages(response_no_user.wsgi_request))
    if messages_no_user:
        for message in messages_no_user:
            print(f"   - Message: '{message}' (level: {message.level_tag})")
    else:
        print(f"   - No messages found")
    
    print(f"\n🧹 Cleaning up test user...")
    try:
        user.delete()
        print(f"✅ Test user deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting test user: {str(e)}")
    
    print(f"\n🎉 Login Error Message Test Completed!")
    print("\n📋 Expected Messages:")
    print("✅ Unverified user: 'Account is not active, please check your email and activate account'")
    print("✅ Wrong password: 'Invalid email or password. Please try again.'")
    print("✅ Non-existent user: 'Invalid email or password. Please try again.'")

if __name__ == '__main__':
    test_login_error_messages()