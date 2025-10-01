#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Product, ProductVariant
from decimal import Decimal

User = get_user_model()

def test_order_editing_stock_management():
    print("🔧 Testing Order Editing with Stock Management...")
    
    # Get the first few orders
    orders = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).order_by('-created_at')[:3]
    
    if not orders:
        print("❌ No editable orders found")
        return
    
    for order in orders:
        print(f"\n📋 Order: {order.order_number}")
        print(f"  ➤ Status: {order.status}")
        print(f"  ➤ Total: ${order.total_amount}")
        print(f"  ➤ Items: {order.items.count()}")
        
        # Show order items and current stock
        for item in order.items.all():
            product_stock = item.variant.stock_quantity if item.variant else item.product.stock_quantity
            print(f"    • {item.product_name} x{item.quantity} @ ${item.unit_price}")
            print(f"      Current Stock: {product_stock}")
    
    # Get some available products for testing add functionality
    print(f"\n🛍 Available Products for Adding:")
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0)[:5]
    for product in products:
        print(f"  • {product.name} (Stock: {product.stock_quantity}) - ${product.price}")
        if product.variants.exists():
            for variant in product.variants.all()[:2]:
                print(f"    ➤ {variant.name} (Stock: {variant.stock_quantity}) - ${variant.price}")
    
    print(f"\n🎯 Order Edit Testing Instructions:")
    print(f"1. Open http://127.0.0.1:8000/mb-admin/orders/")
    print(f"2. Click on any order to view details")
    print(f"3. Click 'Edit Order' button to enable editing mode")
    print(f"4. Test the following features:")
    print(f"   📝 Edit item quantities (stock will adjust automatically)")
    print(f"   📝 Change item prices")
    print(f"   ➕ Add new items (stock will be deducted)")
    print(f"   🗑️ Remove items (stock will be restored)")
    print(f"   💾 Save changes to persist all modifications")
    print(f"5. Verify stock changes in the product details")
    
    # Show stock management example
    test_order = orders.first()
    if test_order and test_order.items.exists():
        test_item = test_order.items.first()
        current_stock = test_item.variant.stock_quantity if test_item.variant else test_item.product.stock_quantity
        
        print(f"\n📊 Stock Management Example:")
        print(f"Order: {test_order.order_number}")
        print(f"Item: {test_item.product_name} (Quantity: {test_item.quantity})")
        print(f"Current Stock: {current_stock}")
        print(f"")
        print(f"✅ If you increase quantity by 2:")
        print(f"   Stock will decrease by 2 → New stock: {current_stock - 2}")
        print(f"")
        print(f"✅ If you decrease quantity by 1:")
        print(f"   Stock will increase by 1 → New stock: {current_stock + 1}")
        print(f"")
        print(f"✅ If you remove the item:")
        print(f"   Stock will increase by {test_item.quantity} → New stock: {current_stock + test_item.quantity}")
    
    print(f"\n🔒 Edit Restrictions:")
    print(f"• Orders with status 'delivered', 'returned', or 'cancelled' cannot be edited")
    print(f"• Stock availability is checked before allowing quantity increases")
    print(f"• All stock changes are applied immediately upon saving")
    
    print(f"\n🎉 Order editing with professional stock management is ready for testing!")

if __name__ == '__main__':
    test_order_editing_stock_management()