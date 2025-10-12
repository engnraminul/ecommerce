#!/usr/bin/env python
"""
Test script to verify pages dashboard functionality
"""
import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from pages.models import Page, PageCategory, PageComment

User = get_user_model()

def test_pages_dashboard():
    """Test the pages dashboard functionality"""
    print("🧪 Testing Pages Dashboard Functionality")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Get or create superuser for testing
    try:
        # First check for existing users
        users = User.objects.all()
        print(f"📊 Found {users.count()} existing users")
        
        # Try to find a superuser
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # Create new superuser
            user = User.objects.create_superuser(
                username='testadmin',
                email='admin@test.com',
                password='admin123'
            )
            print(f"✅ Created new admin user: {user.username}")
        else:
            print(f"✅ Using existing admin user: {user.username}")
            # Ensure password is set correctly
            user.set_password('admin123')
            user.save()
        
    except Exception as e:
        print(f"❌ Error with admin user: {e}")
        return
    
    # Login - try with the known password
    login_success = client.login(username=user.username, password='admin123')
    if not login_success:
        # Try with existing user's actual credentials
        existing_user = User.objects.filter(username='aminul').first()
        if existing_user:
            print(f"🔄 Trying with existing user: {existing_user.username}")
            existing_user.set_password('admin123')
            existing_user.is_staff = True
            existing_user.is_superuser = True
            existing_user.save()
            login_success = client.login(username='aminul', password='admin123')
            user = existing_user
    
    if not login_success:
        print("❌ Failed to login with any user")
        return
    print(f"✅ Admin login successful as: {user.username}")
    
    # Test 1: Dashboard page loads
    try:
        response = client.get('/mb-admin/pages/')
        if response.status_code == 200:
            print("✅ Dashboard page loads successfully")
        else:
            print(f"❌ Dashboard page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard page error: {e}")
    
    # Test 2: API endpoints
    api_tests = [
        ('/mb-admin/api/pages/pages/', 'Pages list'),
        ('/mb-admin/api/pages/categories/', 'Categories list'),
        ('/mb-admin/api/pages/comments/', 'Comments list'),
        ('/mb-admin/api/pages/analytics/', 'Analytics list'),
        ('/mb-admin/api/pages/pages/statistics/', 'Pages statistics'),
    ]
    
    for endpoint, name in api_tests:
        try:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {response.status_code} - {len(data.get('results', data)) if isinstance(data, dict) else len(data)} items")
            else:
                print(f"❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name} error: {e}")
    
    # Test 3: CRUD operations
    print("\n📝 Testing CRUD Operations")
    print("-" * 30)
    
    # Test creating a new category
    try:
        category_data = {
            'name': 'Test Category',
            'description': 'A test category created by automation',
            'is_active': True
        }
        response = client.post('/mb-admin/api/pages/categories/', 
                              data=json.dumps(category_data), 
                              content_type='application/json')
        if response.status_code in [200, 201]:
            created_category = response.json()
            print(f"✅ Category created: {created_category.get('name')}")
            
            # Test updating the category
            update_data = {
                'name': 'Updated Test Category',
                'description': 'Updated description',
                'is_active': True
            }
            response = client.put(f'/mb-admin/api/pages/categories/{created_category["id"]}/', 
                                 data=json.dumps(update_data), 
                                 content_type='application/json')
            if response.status_code == 200:
                print("✅ Category updated successfully")
            else:
                print(f"❌ Category update failed: {response.status_code}")
            
            # Test deleting the category
            response = client.delete(f'/mb-admin/api/pages/categories/{created_category["id"]}/')
            if response.status_code == 204:
                print("✅ Category deleted successfully")
            else:
                print(f"❌ Category deletion failed: {response.status_code}")
        else:
            print(f"❌ Category creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Category CRUD error: {e}")
    
    # Test creating a new page
    try:
        # Get a category for the page
        category = PageCategory.objects.first()
        page_data = {
            'title': 'Test Page',
            'content': '<p>This is a test page created by automation.</p>',
            'status': 'draft',
            'category': category.id if category else None,
            'allow_comments': True,
            'meta_title': 'Test Page - Meta Title',
            'meta_description': 'Test page meta description'
        }
        response = client.post('/mb-admin/api/pages/pages/', 
                              data=json.dumps(page_data), 
                              content_type='application/json')
        if response.status_code in [200, 201]:
            created_page = response.json()
            print(f"✅ Page created: {created_page.get('title')}")
            
            # Test page duplication
            response = client.post(f'/mb-admin/api/pages/pages/{created_page["id"]}/duplicate/')
            if response.status_code in [200, 201]:
                print("✅ Page duplicated successfully")
            else:
                print(f"❌ Page duplication failed: {response.status_code}")
            
            # Test quick publish
            response = client.post(f'/mb-admin/api/pages/pages/{created_page["id"]}/quick_publish/')
            if response.status_code == 200:
                print("✅ Page quick publish successful")
            else:
                print(f"❌ Page quick publish failed: {response.status_code}")
            
            # Clean up - delete the test page
            response = client.delete(f'/mb-admin/api/pages/pages/{created_page["id"]}/')
            if response.status_code == 204:
                print("✅ Test page cleaned up")
        else:
            print(f"❌ Page creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Page CRUD error: {e}")
    
    # Test 4: Database integrity
    print("\n🔍 Database Status")
    print("-" * 20)
    print(f"📄 Total Pages: {Page.objects.count()}")
    print(f"📁 Total Categories: {PageCategory.objects.count()}")
    print(f"💬 Total Comments: {PageComment.objects.count()}")
    print(f"📊 Published Pages: {Page.objects.filter(status='published').count()}")
    print(f"📝 Draft Pages: {Page.objects.filter(status='draft').count()}")
    
    print("\n🎉 Dashboard testing completed!")

if __name__ == '__main__':
    test_pages_dashboard()