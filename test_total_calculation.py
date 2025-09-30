#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from incomplete_orders.models import IncompleteOrder, IncompleteOrderItem
from products.models import Product

def test_total_calculation():
    print("🧪 Testing total calculation for incomplete orders...")
    
    # Get the first incomplete order
    incomplete_order = IncompleteOrder.objects.first()
    if not incomplete_order:
        print("❌ No incomplete orders found")
        return
    
    print(f"📋 Testing order: {incomplete_order.incomplete_order_id}")
    
    # Calculate total from items
    items = incomplete_order.items.all()
    calculated_total = sum(item.quantity * item.unit_price for item in items)
    
    print(f"💰 Current order total: ${incomplete_order.total_amount}")
    print(f"🧮 Calculated from items: ${calculated_total}")
    
    # Show all items
    print(f"\n📦 Order items:")
    for item in items:
        item_total = item.quantity * item.unit_price
        print(f"  • {item.product_name} x{item.quantity} @ ${item.unit_price} = ${item_total}")
    
    # Check if totals match
    if abs(float(incomplete_order.total_amount) - float(calculated_total)) < 0.01:
        print(f"\n✅ Totals match! Order calculation is correct.")
    else:
        print(f"\n❌ Totals don't match! Need to fix calculation.")
        
        # Fix the total
        incomplete_order.total_amount = calculated_total
        incomplete_order.save()
        print(f"🔧 Fixed order total to: ${calculated_total}")
    
    # Show available products for testing add functionality
    print(f"\n🛍 Available products for testing:")
    products = Product.objects.filter(is_active=True)[:5]
    for product in products:
        print(f"  • {product.name} (${product.price}) - SKU: {product.sku}")
    
    print(f"\n🎯 Test Instructions:")
    print(f"1. Open the incomplete orders dashboard")
    print(f"2. Click on order {incomplete_order.incomplete_order_id}")
    print(f"3. Click 'Add Item' button")
    print(f"4. Search for any product (e.g., 'Test')")
    print(f"5. Add the product with quantity 1")
    print(f"6. Verify the total updates correctly")
    print(f"7. Try editing item quantities")
    print(f"8. Verify totals update in real-time")

if __name__ == '__main__':
    test_total_calculation()