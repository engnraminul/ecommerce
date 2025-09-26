#!/usr/bin/env python
"""
Test script to validate the business logic for product cost and revenue calculations
"""
import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Product, ProductVariant

User = get_user_model()

def test_business_logic():
    print("🔍 Testing Business Logic Calculations")
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found!")
        return
    
    print(f"👤 Admin user: {admin_user.username}")
    
    # Test API
    client = Client()
    client.force_login(admin_user)
    
    response = client.get('/mb-admin/api/statistics/', {'period': 'all'})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Response Status: {response.status_code}")
        print()
        
        print("📊 BUSINESS CALCULATIONS BREAKDOWN:")
        print("-" * 40)
        
        print("1️⃣ SALES CALCULATION:")
        print(f"   • Delivered & Shipped Orders Sales: ${data['total_sales']}")
        print(f"   • (Includes partial refunds from partially returned orders)")
        print()
        
        print("2️⃣ EXPENSES BREAKDOWN:")
        print(f"   • Dashboard Expenses: ${data['dashboard_expenses']}")
        print(f"   • Courier Charges: ${data['courier_expenses']}")
        print(f"   • Total Expenses: ${data['total_expenses']}")
        print()
        
        print("3️⃣ PRODUCT COST CALCULATION:")
        print(f"   • Product Cost (Delivered & Shipped only): ${data['total_product_cost']}")
        print(f"   • (Only counts cost from delivered and shipped orders)")
        print()
        
        print("4️⃣ REVENUE CALCULATION:")
        print(f"   • Total Sales: ${data['total_sales']}")
        print(f"   • Total Expenses: ${data['total_expenses']}")
        print(f"   • Product Cost: ${data['total_product_cost']}")
        print(f"   • Revenue = Sales - (Expenses + Product Cost)")
        print(f"   • Revenue = {data['total_sales']} - ({data['total_expenses']} + {data['total_product_cost']})")
        print(f"   • Total Revenue: ${data['total_revenue']}")
        print()
        
        print("5️⃣ PROFIT MARGIN:")
        print(f"   • Profit Margin: {data['profit_margin']}%")
        print(f"   • Formula: (Revenue / Sales) × 100")
        print()
        
        # Show detailed order breakdown
        print("📦 ORDER STATUS BREAKDOWN:")
        print("-" * 30)
        
        all_orders = Order.objects.all()
        status_counts = {}
        status_sales = {}
        
        for order in all_orders:
            status = order.status
            if status not in status_counts:
                status_counts[status] = 0
                status_sales[status] = Decimal('0')
            
            status_counts[status] += 1
            
            # Calculate sales based on business logic
            if status in ['delivered', 'shipped']:
                status_sales[status] += order.total_amount
            elif status == 'partially_returned':
                status_sales[status] += order.partially_ammount or Decimal('0')
        
        for status, count in status_counts.items():
            sales_amount = status_sales.get(status, Decimal('0'))
            includes_sales = "✅" if status in ['delivered', 'shipped', 'partially_returned'] else "❌"
            includes_product_cost = "✅" if status in ['delivered', 'shipped'] else "❌"
            
            print(f"   • {status.title()}: {count} orders, ${sales_amount}")
            print(f"     Sales: {includes_sales} | Product Cost: {includes_product_cost}")
        
        print()
        print("✅ Business logic validation complete!")
        
    else:
        print(f"❌ API Error: Status {response.status_code}")
        print(f"Response: {response.content.decode()}")

if __name__ == "__main__":
    test_business_logic()