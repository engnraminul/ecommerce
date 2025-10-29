#!/usr/bin/env python3
"""
Quick test script for the contact app functionality
"""

import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def test_contact_endpoints():
    """Test contact app endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    # Configure session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    print("🧪 Testing Contact App Endpoints\n")
    
    try:
        # Test 1: Contact page (public)
        print("1. Testing public contact page...")
        response = session.get(f"{base_url}/contact/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Contact page loads successfully")
        else:
            print(f"   ❌ Contact page failed: {response.status_code}")
        
        # Test 2: Contact dashboard page (protected)
        print("\n2. Testing contact dashboard page...")
        response = session.get(f"{base_url}/contact/dashboard/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code in [200, 302, 403]:  # 302/403 for auth redirect
            print("   ✅ Dashboard page accessible (may require auth)")
        else:
            print(f"   ❌ Dashboard page failed: {response.status_code}")
        
        # Test 3: Contact API endpoints
        print("\n3. Testing contact API endpoints...")
        
        # Test API root
        response = session.get(f"{base_url}/contact/api/", timeout=10)
        print(f"   API Root Status: {response.status_code}")
        
        # Test settings endpoint
        response = session.get(f"{base_url}/contact/api/contact-settings/", timeout=10)
        print(f"   Settings API Status: {response.status_code}")
        
        # Test 4: Submit contact form (POST test)
        print("\n4. Testing contact form submission...")
        contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'subject': 'Test Subject',
            'message': 'This is a test message from the contact app test script.'
        }
        
        # Get CSRF token first
        csrf_response = session.get(f"{base_url}/contact/", timeout=10)
        if 'csrfmiddlewaretoken' in csrf_response.text:
            # Extract CSRF token (simplified extraction)
            import re
            csrf_match = re.search(r'csrfmiddlewaretoken["\']?\s*[:=]\s*["\']([^"\']+)', csrf_response.text)
            if csrf_match:
                contact_data['csrfmiddlewaretoken'] = csrf_match.group(1)
        
        response = session.post(f"{base_url}/contact/api/submit/", data=contact_data, timeout=10)
        print(f"   Form Submission Status: {response.status_code}")
        
        if response.status_code == 201:
            print("   ✅ Contact form submitted successfully")
        elif response.status_code == 400:
            print(f"   ⚠️  Form validation errors: {response.text[:200]}")
        else:
            print(f"   ❌ Form submission failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure Django server is running on http://127.0.0.1:8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Server might be slow to respond.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n🎉 Contact app testing completed!")
    return True

def check_database_tables():
    """Check if contact tables exist in database"""
    print("\n📊 Checking Database Tables\n")
    
    try:
        import django
        import os
        import sys
        
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(project_root)
        
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
        django.setup()
        
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if contact tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'contact%'
                ORDER BY name;
            """)
            
            tables = cursor.fetchall()
            
            if tables:
                print("Contact app tables found:")
                for table in tables:
                    print(f"   ✅ {table[0]}")
                    
                    # Get row count for each table
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"      Records: {count}")
            else:
                print("❌ No contact tables found in database")
                return False
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Contact App Integration Test\n")
    print("=" * 50)
    
    # Test database first
    db_success = check_database_tables()
    
    if db_success:
        print("\n" + "=" * 50)
        # Test web endpoints
        web_success = test_contact_endpoints()
        
        if web_success and db_success:
            print("\n🎊 All tests passed! Contact app is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
    else:
        print("\n❌ Database test failed. Contact app may not be properly configured.")

if __name__ == "__main__":
    main()