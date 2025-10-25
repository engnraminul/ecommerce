#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from users.models import User
from django.contrib.auth import authenticate

def test_login_flow():
    """Test the complete login flow"""
    try:
        user = User.objects.get(email='phonekobra@gmail.com')
        print(f'=== User Information ===')
        print(f'User found: {user.email}')
        print(f'is_email_verified: {user.is_email_verified}')
        print(f'is_active: {user.is_active}')
        print(f'username: {user.username}')
        print()
        
        print(f'=== Testing Login Flow ===')
        
        # Test 1: Check if user exists
        print(f'1. User exists: ✓')
        
        # Test 2: Test password validation
        password_valid = user.check_password('sathi3065')
        print(f'2. Password "sathi3065" is valid: {"✓" if password_valid else "✗"}')
        
        # Test 3: Check email verification status
        email_verified = user.is_email_verified
        print(f'3. Email verified: {"✓" if email_verified else "✗"}')
        
        # Test 4: Test authentication with custom backend
        auth_user = authenticate(username='phonekobra@gmail.com', password='sathi3065')
        auth_success = auth_user is not None
        print(f'4. Authentication result: {"✓" if auth_success else "✗"}')
        
        print()
        print(f'=== Expected Login Behavior ===')
        if not password_valid:
            print('❌ Should show: "Invalid email or password"')
        elif not email_verified:
            print('❌ Should show: "Account is not active, please check your email and activate account"')
        elif auth_success:
            print('✅ Should log in successfully')
        else:
            print('❌ Should show: "Authentication error"')
            
        # Test with wrong password
        print()
        print(f'=== Testing Wrong Password ===')
        wrong_password_valid = user.check_password('wrongpassword')
        print(f'Wrong password check: {"✓" if wrong_password_valid else "✗"}')
        if not wrong_password_valid:
            print('✅ Should show: "Invalid email or password"')
            
    except User.DoesNotExist:
        print('❌ User not found')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_flow()