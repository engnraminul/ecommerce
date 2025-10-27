"""
Test IP address capture in real order creation scenario
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import RequestFactory
from orders.utils import get_client_ip, get_external_ip
from orders.models import Order

def test_real_ip_capture():
    """Test that IP capture works with real external IP"""
    print("🧪 Testing Real IP Address Capture")
    print("=" * 50)
    
    # Use your known real external IP (avoiding potentially slow external call)
    real_ip = "202.1.28.11"  # Your real IP from ifconfig.co
    print(f"🎯 Testing with your real external IP: {real_ip}")
    
    # Simulate a request with your real IP
    factory = RequestFactory()
    request = factory.post('/api/orders/')
    
    # Simulate different scenarios where your real IP would be captured
    scenarios = [
        {
            'name': 'Direct connection',
            'headers': {'REMOTE_ADDR': real_ip}
        },
        {
            'name': 'Behind Cloudflare',
            'headers': {
                'HTTP_CF_CONNECTING_IP': real_ip,
                'REMOTE_ADDR': '104.16.0.1'  # Cloudflare IP
            }
        },
        {
            'name': 'Behind Nginx proxy',
            'headers': {
                'HTTP_X_REAL_IP': real_ip,
                'REMOTE_ADDR': '192.168.1.1'
            }
        },
        {
            'name': 'Through load balancer',
            'headers': {
                'HTTP_X_FORWARDED_FOR': f'{real_ip}, 10.0.0.1',
                'REMOTE_ADDR': '10.0.0.1'
            }
        }
    ]
    
    print(f"\n🔍 Testing IP detection scenarios:")
    
    for scenario in scenarios:
        # Set up request headers
        for header, value in scenario['headers'].items():
            request.META[header] = value
        
        # Test IP detection
        detected_ip = get_client_ip(request)
        
        # Check if we got the real IP
        success = detected_ip == real_ip
        status = "✅" if success else "❌"
        
        print(f"  {status} {scenario['name']}: {detected_ip}")
        
        # Clear headers for next test
        request.META.clear()
    
    print(f"\n🎯 For fraud detection, you want to capture: {real_ip}")
    print("   This IP can help you:")
    print("   • Identify customers from same location")
    print("   • Detect VPN/Proxy usage")
    print("   • Track geographic patterns")
    print("   • Spot suspicious rapid orders")

def check_existing_orders():
    """Check if existing orders have IP addresses"""
    print(f"\n📊 Checking Existing Orders")
    print("-" * 30)
    
    total_orders = Order.objects.count()
    orders_with_ip = Order.objects.filter(customer_ip__isnull=False).count()
    orders_without_ip = total_orders - orders_with_ip
    
    print(f"Total orders: {total_orders}")
    print(f"Orders with IP: {orders_with_ip}")
    print(f"Orders without IP: {orders_without_ip}")
    
    if orders_with_ip > 0:
        print(f"\n🔍 Recent orders with IP addresses:")
        recent_orders = Order.objects.filter(
            customer_ip__isnull=False
        ).order_by('-created_at')[:5]
        
        for order in recent_orders:
            print(f"  • Order {order.order_number}: {order.customer_ip} ({order.created_at.strftime('%Y-%m-%d')})")
    
    if orders_without_ip > 0:
        print(f"\n⚠️  {orders_without_ip} orders don't have IP addresses (placed before this feature)")

if __name__ == "__main__":
    test_real_ip_capture()
    check_existing_orders()
    
    print(f"\n🚀 Next Steps for Fraud Detection:")
    print("1. Place a test order to verify IP capture works")
    print("2. Run: python manage.py detect_fraud --days 7")
    print("3. Monitor orders from same IP addresses")
    print("4. Check orders with foreign IP addresses")
    print("5. Set up alerts for high-risk patterns")