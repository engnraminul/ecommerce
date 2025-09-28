#!/usr/bin/env python
"""
Debug script to test the statistics API endpoint directly
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from dashboard.views import DashboardStatisticsView

User = get_user_model()

def test_statistics_view():
    """Test the statistics view directly without HTTP requests"""
    
    print("🔍 Testing DashboardStatisticsView directly...")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Create a test user (staff user)
    try:
        user = User.objects.filter(is_staff=True).first()
        if not user:
            print("❌ No staff user found. Creating a test staff user...")
            user = User.objects.create_user(
                username='test_admin',
                email='test@example.com',
                password='testpass',
                is_staff=True
            )
            print("✅ Test staff user created")
    except Exception as e:
        print(f"❌ Error with user setup: {e}")
        return
    
    # Test different periods
    test_periods = [
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('last_month', 'Last Month'),
        ('year', 'This Year'),
        ('custom', 'Custom Range')
    ]
    
    view = DashboardStatisticsView()
    
    for period, description in test_periods:
        print(f"\n📊 Testing {description} ({period})...")
        
        try:
            # Create a fake GET request
            if period == 'custom':
                request = factory.get('/api/statistics/', {
                    'period': period,
                    'date_from': '2025-09-01',
                    'date_to': '2025-09-28'
                })
            else:
                request = factory.get('/api/statistics/', {'period': period})
            
            # Add the user to the request
            request.user = user
            
            # Call the view
            response = view.get(request)
            
            if response.status_code == 200:
                data = response.data
                print(f"✅ {description}: Success")
                print(f"   📈 Total Sales: ${data.get('total_sales', 0)}")
                print(f"   🛍️  Orders Count: {data.get('orders_count', 0)}")
                print(f"   💰 Total Revenue: ${data.get('total_revenue', 0)}")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                if hasattr(response, 'data'):
                    print(f"   Error: {response.data}")
                    
        except Exception as e:
            print(f"❌ {description}: Exception - {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")

def test_imports():
    """Test if all required imports work"""
    
    print("🔍 Testing imports...")
    
    try:
        from django.utils import timezone
        from datetime import timedelta, datetime
        from django.db.models import Sum, Count, Q, F
        from orders.models import Order
        from dashboard.models import Expense
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Statistics Debug Test")
    print("=" * 50)
    
    # Test imports first
    if test_imports():
        # Test the view
        test_statistics_view()
    
    print("\n🎉 Debug test complete!")