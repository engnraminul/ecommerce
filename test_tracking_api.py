import os
import django
import sys

# Add project root to Python path
sys.path.append('/Users/aminu/OneDrive/Desktop/ecommerce')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order
from orders.serializers import OrderTrackingSerializer

def test_order_tracking():
    print("=== TESTING ORDER TRACKING API ===")
    
    # Test with a known order
    try:
        order = Order.objects.get(order_number='MB1050')
        print(f"Found order: {order.order_number}")
        
        # Test the serializer
        serializer = OrderTrackingSerializer(order)
        data = serializer.data
        print(f"Serializer data: {data}")
        
    except Order.DoesNotExist:
        print("Order MB1050 not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_order_tracking()