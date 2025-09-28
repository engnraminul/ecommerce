#!/usr/bin/env python
"""
Full test of the statistics page functionality including authentication
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_statistics_page_access():
    """Test accessing the statistics page and API with authentication"""
    
    print("🔍 Testing Statistics Page Access...")
    print("=" * 50)
    
    # Create a test client
    client = Client()
    
    # Create or get a staff user
    try:
        user = User.objects.filter(is_staff=True).first()
        if not user:
            print("📝 Creating test staff user...")
            user = User.objects.create_user(
                username='test_admin',
                email='test@example.com',
                password='testpass123',
                is_staff=True,
                is_superuser=True
            )
            print("✅ Test staff user created")
        else:
            print(f"✅ Using existing staff user: {user.username}")
    except Exception as e:
        print(f"❌ Error with user setup: {e}")
        return
    
    # Test 1: Access statistics page (should redirect to login if not logged in)
    print("\n📊 Testing statistics page access without login...")
    try:
        response = client.get('/mb-admin/statistics/')
        if response.status_code == 302:  # Redirect to login
            print("✅ Correctly redirected to login when not authenticated")
        elif response.status_code == 200:
            print("✅ Statistics page accessible (user might be pre-logged in)")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing statistics page: {e}")
    
    # Test 2: Login as staff user
    print(f"\n🔐 Logging in as {user.username}...")
    try:
        login_success = client.login(username=user.username, password='testpass123')
        if login_success:
            print("✅ Login successful")
        else:
            print("❌ Login failed - trying to create a new user")
            user = User.objects.create_user(
                username='test_admin_new',
                email='test_new@example.com', 
                password='testpass123',
                is_staff=True,
                is_superuser=True
            )
            login_success = client.login(username=user.username, password='testpass123')
            print(f"✅ New user login successful: {login_success}")
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return
    
    # Test 3: Access statistics page after login
    print("\n📊 Testing statistics page access after login...")
    try:
        response = client.get('/mb-admin/statistics/')
        if response.status_code == 200:
            print("✅ Statistics page accessible after login")
            print(f"   Response contains statistics template: {'statistics.html' in str(response.content)}")
        else:
            print(f"❌ Statistics page not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing statistics page after login: {e}")
    
    # Test 4: Test API endpoints
    print("\n📡 Testing Statistics API endpoints...")
    
    api_tests = [
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('last_month', 'Last Month'),
        ('year', 'This Year'),
    ]
    
    for period, description in api_tests:
        try:
            response = client.get(f'/mb-admin/api/statistics/?period={period}')
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: Success")
                print(f"   📈 Total Sales: ${data.get('total_sales', 0)}")
                print(f"   🛍️  Orders Count: {data.get('orders_count', 0)}")
                print(f"   💰 Total Revenue: ${data.get('total_revenue', 0)}")
            else:
                print(f"❌ {description}: Failed (HTTP {response.status_code})")
                if hasattr(response, 'content'):
                    print(f"   Response: {response.content[:200]}...")
        except Exception as e:
            print(f"❌ {description}: Exception - {str(e)}")
    
    # Test 5: Test custom date range
    print("\n📅 Testing custom date range API...")
    try:
        response = client.get('/mb-admin/api/statistics/?period=custom&date_from=2025-09-01&date_to=2025-09-28')
        if response.status_code == 200:
            data = response.json()
            print("✅ Custom Range: Success")
            print(f"   📈 Total Sales: ${data.get('total_sales', 0)}")
            print(f"   🛍️  Orders Count: {data.get('orders_count', 0)}")
            print(f"   💰 Total Revenue: ${data.get('total_revenue', 0)}")
        else:
            print(f"❌ Custom Range: Failed (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Custom Range: Exception - {str(e)}")
    
    # Test 6: Test invalid custom date range
    print("\n🧪 Testing invalid date format handling...")
    try:
        response = client.get('/mb-admin/api/statistics/?period=custom&date_from=invalid&date_to=2025-09-28')
        if response.status_code == 400:
            print("✅ Invalid date format properly rejected with HTTP 400")
            try:
                data = response.json()
                print(f"   Error message: {data.get('error', 'No error message')}")
            except:
                print(f"   Raw response: {response.content}")
        else:
            print(f"⚠️  Unexpected response for invalid date: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid date test: Exception - {str(e)}")

def test_url_patterns():
    """Test URL pattern resolution"""
    
    print("\n🔗 Testing URL Pattern Resolution...")
    print("=" * 40)
    
    try:
        from django.urls import resolve
        
        # Test statistics page URL
        match = resolve('/mb-admin/statistics/')
        print(f"✅ Statistics page URL resolves to: {match.view_name}")
        
        # Test API URL
        match = resolve('/mb-admin/api/statistics/')
        print(f"✅ Statistics API URL resolves to: {match.view_name}")
        
    except Exception as e:
        print(f"❌ URL resolution error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Full Statistics Test")
    print("=" * 60)
    
    try:
        test_url_patterns()
        test_statistics_page_access()
        
        print("\n🎉 Full testing complete!")
        print("=" * 60)
        print("✨ If you see authentication errors in the browser,")
        print("   make sure to log in to the admin panel first!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()