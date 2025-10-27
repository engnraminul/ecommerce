# Simple test for Django shell
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order
from orders.serializers import OrderDetailSerializer  
from dashboard.serializers import OrderDashboardSerializer

print("🔍 Checking Order model for customer_ip field...")
field_names = [field.name for field in Order._meta.get_fields()]
if 'customer_ip' in field_names:
    print("✅ customer_ip field found in Order model")
    customer_ip_field = Order._meta.get_field('customer_ip')
    print(f"  Field type: {type(customer_ip_field).__name__}")
    print(f"  Blank allowed: {customer_ip_field.blank}")
    print(f"  Null allowed: {customer_ip_field.null}")
else:
    print("❌ customer_ip field NOT found in Order model")

print("\n🔍 Checking serializers for customer_ip field...")
order_detail_fields = OrderDetailSerializer.Meta.fields
if 'customer_ip' in order_detail_fields:
    print("✅ customer_ip field found in OrderDetailSerializer")
else:
    print("❌ customer_ip field NOT found in OrderDetailSerializer")

order_dashboard_fields = OrderDashboardSerializer.Meta.fields  
if 'customer_ip' in order_dashboard_fields:
    print("✅ customer_ip field found in OrderDashboardSerializer")
else:
    print("❌ customer_ip field NOT found in OrderDashboardSerializer")

print("\n🎉 Model and serializer verification completed!")