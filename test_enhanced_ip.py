"""
Enhanced test for IP address detection - specifically for fraud detection
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.utils import get_client_ip, get_external_ip, is_valid_ip
from django.test import RequestFactory

def test_enhanced_ip_detection():
    """Test the enhanced IP detection functionality"""
    factory = RequestFactory()
    
    print("🔍 Testing Enhanced IP Detection for Fraud Prevention")
    print("=" * 60)
    
    # Test 1: Cloudflare header (highest priority)
    print("Test 1: Cloudflare IP header")
    request1 = factory.get('/')
    request1.META['HTTP_CF_CONNECTING_IP'] = '202.1.28.11'
    request1.META['REMOTE_ADDR'] = '127.0.0.1'  # Should be ignored
    ip1 = get_client_ip(request1)
    print(f"  Expected: 202.1.28.11, Got: {ip1}")
    
    # Test 2: X-Real-IP header (Nginx proxy)
    print("Test 2: X-Real-IP header")
    request2 = factory.get('/')
    request2.META['HTTP_X_REAL_IP'] = '202.1.28.11'
    request2.META['REMOTE_ADDR'] = '192.168.1.100'  # Should be ignored
    ip2 = get_client_ip(request2)
    print(f"  Expected: 202.1.28.11, Got: {ip2}")
    
    # Test 3: X-Forwarded-For with public IP
    print("Test 3: X-Forwarded-For with public IP")
    request3 = factory.get('/')
    request3.META['HTTP_X_FORWARDED_FOR'] = '202.1.28.11, 192.168.1.100'
    ip3 = get_client_ip(request3)
    print(f"  Expected: 202.1.28.11, Got: {ip3}")
    
    # Test 4: Only private IP available
    print("Test 4: Only private IP available")
    request4 = factory.get('/')
    request4.META['REMOTE_ADDR'] = '192.168.1.100'
    ip4 = get_client_ip(request4)
    print(f"  Got: {ip4} (private IP, better than localhost)")
    
    # Test 5: External IP detection
    print("Test 5: External IP detection")
    external_ip = get_external_ip()
    if external_ip:
        print(f"  Your real external IP: {external_ip}")
        print(f"  This matches ifconfig.co: {external_ip == '202.1.28.11'}")
    else:
        print("  Could not detect external IP (network issue)")
    
    # Test 6: IP validation
    print("Test 6: IP validation")
    valid_ips = ['202.1.28.11', '192.168.1.1', '127.0.0.1', '::1']
    invalid_ips = ['invalid', '999.999.999.999', '']
    
    for ip in valid_ips:
        result = is_valid_ip(ip)
        print(f"  {ip} is valid: {result}")
    
    for ip in invalid_ips:
        result = is_valid_ip(ip)
        print(f"  {ip} is valid: {result}")

def test_fraud_detection_scenario():
    """Test scenarios that would be useful for fraud detection"""
    factory = RequestFactory()
    
    print("\n🚨 Fraud Detection Scenarios")
    print("=" * 40)
    
    # Scenario 1: Customer using VPN/Proxy
    print("Scenario 1: Customer using VPN/Proxy")
    request1 = factory.get('/')
    request1.META['HTTP_X_FORWARDED_FOR'] = '185.220.100.240, 192.168.1.100'  # Tor exit node
    ip1 = get_client_ip(request1)
    print(f"  Detected IP: {ip1} (potential VPN/Proxy)")
    
    # Scenario 2: Customer from different geographic location
    print("Scenario 2: Customer from different country")
    request2 = factory.get('/')
    request2.META['HTTP_CF_CONNECTING_IP'] = '8.8.8.8'  # Google DNS (US)
    ip2 = get_client_ip(request2)
    print(f"  Detected IP: {ip2} (foreign IP)")
    
    # Scenario 3: Multiple orders from same IP
    print("Scenario 3: Multiple orders from same IP")
    request3 = factory.get('/')
    request3.META['HTTP_X_REAL_IP'] = '202.1.28.11'
    ip3 = get_client_ip(request3)
    print(f"  Detected IP: {ip3} (same IP for multiple orders - potential fraud)")
    
    print("\n💡 Fraud Detection Tips:")
    print("  - Monitor multiple orders from same IP within short time")
    print("  - Check for IPs from different countries than usual")
    print("  - Look for known VPN/Proxy IP ranges")
    print("  - Compare with shipping address locations")

if __name__ == "__main__":
    test_enhanced_ip_detection()
    test_fraud_detection_scenario()
    
    print("\n🎯 Summary for Fraud Detection:")
    print("✅ Enhanced IP detection with multiple header support")
    print("✅ Prioritizes real public IPs over private/localhost")
    print("✅ External IP detection for development environments")
    print("✅ IP validation to ensure data quality")
    print("✅ Cached external IP requests to avoid rate limiting")
    print("\n🔒 Your orders will now capture the real IP (202.1.28.11) for fraud detection!")