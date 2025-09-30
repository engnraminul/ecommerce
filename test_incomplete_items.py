#!/usr/bin/env python
"""
Quick test script to check incomplete order items API
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from incomplete_orders.models import IncompleteOrder
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from dashboard.views import IncompleteOrderDashboardViewSet

User = get_user_model()

def test_incomplete_order_items():
    print("🔍 Testing Incomplete Order Items API...")
    
    # Get the first incomplete order
    incomplete_orders = IncompleteOrder.objects.all()
    
    if not incomplete_orders.exists():
        print("❌ No incomplete orders found. Please create some incomplete orders first.")
        return
    
    incomplete_order = incomplete_orders.first()
    print(f"✅ Found incomplete order: {incomplete_order.incomplete_order_id}")
    
    # Test the API endpoint
    try:
        # Create a mock request
        factory = RequestFactory()
        request = factory.get(f'/mb-admin/api/incomplete-orders/{incomplete_order.id}/items/')
        
        # Create admin user for authentication
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser('testadmin', 'test@example.com', 'testpass123')
            request.user = admin_user
        except Exception as e:
            print(f"⚠️  Could not create/get admin user: {e}")
            request.user = None
        
        # Test the viewset
        viewset = IncompleteOrderDashboardViewSet()
        viewset.request = request
        viewset.kwargs = {'pk': incomplete_order.id}
        
        # Call the items method
        response = viewset.items(request, pk=incomplete_order.id)
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ API call successful!")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Total items: {data.get('total_items', 0)}")
            print(f"   - Total amount: ${data.get('total_amount', '0.00')}")
            
            items = data.get('items', [])
            if items:
                print(f"📦 Items details:")
                for i, item in enumerate(items[:3], 1):  # Show first 3 items
                    print(f"   {i}. {item.get('product_name', 'Unknown')} (SKU: {item.get('product_sku', 'N/A')})")
                    print(f"      - Variant: {item.get('variant_name', 'Default')}")
                    print(f"      - Quantity: {item.get('quantity', 0)}")
                    print(f"      - Price: ${item.get('unit_price', '0.00')}")
                    print(f"      - Image: {item.get('display_image', 'No image')}")
                    print()
            else:
                print("📦 No items found in this incomplete order")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"   Error: {response.data}")
            
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_incomplete_order_items()