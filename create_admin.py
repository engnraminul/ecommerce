#!/usr/bin/env python
"""
Create or update admin user for testing statistics functionality
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from getpass import getpass

User = get_user_model()

def create_admin_user():
    """Create or update an admin user"""
    
    print("👤 Admin User Setup for Statistics Testing")
    print("=" * 50)
    
    # Check if any superuser exists
    existing_superuser = User.objects.filter(is_superuser=True).first()
    
    if existing_superuser:
        print(f"✅ Found existing superuser: {existing_superuser.username}")
        print(f"   Email: {existing_superuser.email}")
        print(f"   Is staff: {existing_superuser.is_staff}")
        print(f"   Is active: {existing_superuser.is_active}")
        
        choice = input("\nDo you want to create a new admin user? (y/n): ").lower().strip()
        if choice != 'y':
            print("📋 Using existing admin user for testing.")
            print("\n🌐 To test the statistics page:")
            print(f"   1. Go to: http://127.0.0.1:8000/mb-admin/login/")
            print(f"   2. Login with username: {existing_superuser.username}")
            print(f"   3. Then go to: http://127.0.0.1:8000/mb-admin/statistics/")
            return existing_superuser
    
    # Create new admin user
    print("\n📝 Creating new admin user...")
    
    while True:
        username = input("Enter username: ").strip()
        if username and not User.objects.filter(username=username).exists():
            break
        print("❌ Username already exists or is empty. Try another.")
    
    while True:
        email = input("Enter email: ").strip()
        if email:
            break
        print("❌ Email cannot be empty.")
    
    while True:
        password = getpass("Enter password: ").strip()
        password_confirm = getpass("Confirm password: ").strip()
        
        if password and password == password_confirm:
            break
        elif password != password_confirm:
            print("❌ Passwords don't match. Try again.")
        else:
            print("❌ Password cannot be empty.")
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Is superuser: {user.is_superuser}")
        print(f"   Is staff: {user.is_staff}")
        
        print("\n🌐 To test the statistics page:")
        print(f"   1. Go to: http://127.0.0.1:8000/mb-admin/login/")
        print(f"   2. Login with your new credentials")
        print(f"   3. Then go to: http://127.0.0.1:8000/mb-admin/statistics/")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None

def test_admin_login():
    """Test admin login URL"""
    
    print("\n🔐 Testing Admin Login Access...")
    
    try:
        from django.test import Client
        client = Client()
        
        response = client.get('/mb-admin/login/')
        if response.status_code == 200:
            print("✅ Admin login page is accessible")
        else:
            print(f"❌ Admin login page returned: {response.status_code}")
            
        # Test if statistics page redirects to login
        response = client.get('/mb-admin/statistics/')
        if response.status_code == 302:
            print("✅ Statistics page correctly redirects to login when not authenticated")
            redirect_url = response.get('Location', '')
            if 'login' in redirect_url:
                print("✅ Redirect URL contains login, which is correct")
        else:
            print(f"⚠️  Statistics page returned unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")

if __name__ == "__main__":
    print("🚀 Starting Admin User Setup")
    print()
    
    try:
        user = create_admin_user()
        
        if user:
            test_admin_login()
            
            print("\n" + "=" * 60)
            print("🎯 NEXT STEPS TO TEST THE STATISTICS FILTER:")
            print("=" * 60)
            print("1. Make sure the Django server is running:")
            print("   python manage.py runserver")
            print()
            print("2. Open your browser and go to:")
            print("   http://127.0.0.1:8000/mb-admin/login/")
            print()
            print(f"3. Login with your admin credentials")
            print()
            print("4. Navigate to the statistics page:")
            print("   http://127.0.0.1:8000/mb-admin/statistics/")
            print()
            print("5. Test the new dropdown filter with options:")
            print("   • This Week")
            print("   • This Month") 
            print("   • Last Month")
            print("   • This Year")
            print("   • Custom Range")
            print()
            print("6. Check browser console (F12) for any JavaScript errors")
            print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()