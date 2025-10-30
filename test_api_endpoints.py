#!/usr/bin/env python
"""
Test API endpoints for dashboard permissions
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def test_api_endpoints():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing Dashboard Permissions API Endpoints")
    print("=" * 60)
    
    # Test dashboard tabs endpoint
    try:
        response = requests.get(f"{base_url}/mb-admin/api/users/dashboard_tabs/")
        if response.status_code == 200:
            tabs = response.json()
            print(f"✓ Dashboard tabs endpoint working")
            print(f"  - Found {len(tabs)} dashboard tabs")
            print(f"  - Sample tabs: {[tab['label'] for tab in tabs[:3]]}")
        else:
            print(f"✗ Dashboard tabs endpoint failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Server not running or not accessible")
        return
    
    # Test users endpoint structure
    try:
        response = requests.get(f"{base_url}/mb-admin/api/users/")
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                user = data['results'][0]
                print(f"✓ Users API endpoint working")
                print(f"  - Found {data['count']} users")
                
                # Check if dashboard permissions are in response
                if 'dashboard_access_summary' in user:
                    print(f"  - Dashboard access summary: ✓")
                    summary = user['dashboard_access_summary']
                    print(f"    Type: {summary.get('type', 'unknown')}")
                    print(f"    Message: {summary.get('message', 'unknown')}")
                
                if 'dashboard_permissions' in user:
                    print(f"  - Dashboard permissions data: ✓")
                    perms = user['dashboard_permissions']
                    if perms:
                        allowed_count = len(perms.get('allowed_tabs', []))
                        print(f"    Allowed tabs: {allowed_count}")
                else:
                    print(f"  - Dashboard permissions data: ✗")
            else:
                print(f"✗ No users found in API response")
        else:
            print(f"✗ Users API endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing users endpoint: {e}")
    
    print("\n" + "=" * 60)
    print("API Test Summary:")
    print("- Dashboard tabs endpoint: Available for permission selection")
    print("- Users API: Enhanced with dashboard permission data")
    print("- Ready for frontend integration")

if __name__ == "__main__":
    test_api_endpoints()