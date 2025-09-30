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
from products.models import Product, ProductVariant, ProductImage, Category
from incomplete_orders.models import IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress
from decimal import Decimal
import uuid

User = get_user_model()

def create_test_data():
    print("🔧 Creating test data for edit functionality testing...")
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    print(f"✅ Test user: {user.username}")
    
    # Create or get category
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={'description': 'Test category for incomplete orders'}
    )
    print(f"✅ Test category: {category.name}")
    
    # Create test products
    products_data = [
        {
            'name': 'Test Laptop',
            'sku': 'LAPTOP001',
            'price': Decimal('999.99'),
            'description': 'High-performance laptop for testing',
            'stock_quantity': 10
        },
        {
            'name': 'Test Phone',
            'sku': 'PHONE001', 
            'price': Decimal('599.99'),
            'description': 'Smartphone for testing',
            'stock_quantity': 15
        },
        {
            'name': 'Test Headphones',
            'sku': 'HEADPHONES001',
            'price': Decimal('199.99'),
            'description': 'Premium headphones for testing',
            'stock_quantity': 20
        }
    ]
    
    products = []
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            sku=product_data['sku'],
            defaults={
                'name': product_data['name'],
                'price': product_data['price'],
                'description': product_data['description'],
                'stock_quantity': product_data['stock_quantity'],
                'category': category,
                'is_active': True
            }
        )
        products.append(product)
        print(f"✅ Test product: {product.name} (${product.price})")
        
        # Create variants for some products
        if 'Laptop' in product.name:
            variants_data = [
                {'name': '16GB RAM', 'price': Decimal('999.99'), 'sku': 'LAPTOP001-16GB'},
                {'name': '32GB RAM', 'price': Decimal('1299.99'), 'sku': 'LAPTOP001-32GB'}
            ]
            for variant_data in variants_data:
                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    sku=variant_data['sku'],
                    defaults={
                        'name': variant_data['name'],
                        'price': variant_data['price'],
                        'stock_quantity': 5
                    }
                )
                if created:
                    print(f"  ➤ Variant: {variant.name} (${variant.price})")
    
    # Create test incomplete orders
    incomplete_orders = []
    for i in range(3):
        incomplete_order = IncompleteOrder.objects.create(
            incomplete_order_id=f'INC_{uuid.uuid4().hex[:8].upper()}',
            user=user if i % 2 == 0 else None,  # Mix of user and guest orders
            is_guest_order=i % 2 == 1,
            guest_email=f'guest{i}@example.com' if i % 2 == 1 else '',
            status='pending',
            customer_email=user.email if i % 2 == 0 else f'guest{i}@example.com',
            customer_phone=f'+1234567890{i}',
            subtotal=Decimal('0'),
            total_amount=Decimal('0')
        )
        
        # Create shipping address
        shipping_address = IncompleteShippingAddress.objects.create(
            incomplete_order=incomplete_order,
            first_name=f'John{i}',
            last_name=f'Doe{i}',
            address_line_1=f'{123 + i} Test Street',
            address_line_2=f'Apt {i + 1}' if i % 2 == 0 else '',
            city='Test City',
            state='Test State',
            postal_code=f'1234{i}',
            country='Test Country',
            phone=f'+1234567890{i}',
            email=user.email if i % 2 == 0 else f'guest{i}@example.com'
        )
        
        # Add items to incomplete order
        total_amount = Decimal('0')
        for j, product in enumerate(products[:2]):  # Add first 2 products to each order
            quantity = j + 1
            unit_price = product.price
            
            item = IncompleteOrderItem.objects.create(
                incomplete_order=incomplete_order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                variant_name='Default',
                quantity=quantity,
                unit_price=unit_price
            )
            total_amount += quantity * unit_price
        
        # Update order total
        incomplete_order.subtotal = total_amount
        incomplete_order.total_amount = total_amount
        incomplete_order.save()
        
        incomplete_orders.append(incomplete_order)
        print(f"✅ Incomplete order: {incomplete_order.incomplete_order_id} (${incomplete_order.total_amount})")
        print(f"  ➤ Customer: {shipping_address.first_name} {shipping_address.last_name}")
        print(f"  ➤ Items: {incomplete_order.items.count()}")
    
    print(f"\n🎉 Test data created successfully!")
    print(f"📊 Summary:")
    print(f"  - Products: {Product.objects.count()}")
    print(f"  - Product Variants: {ProductVariant.objects.count()}")
    print(f"  - Incomplete Orders: {IncompleteOrder.objects.count()}")
    print(f"  - Total Items: {IncompleteOrderItem.objects.count()}")
    
    print(f"\n🧪 Ready to test:")
    print(f"  1. Open http://127.0.0.1:8000/mb-admin/incomplete-orders/")
    print(f"  2. Click on any incomplete order to view details")
    print(f"  3. Test editing shipping address (should show existing data)")
    print(f"  4. Test editing order items (quantity, price)")
    print(f"  5. Test adding new items (search and add products)")
    print(f"  6. Test removing items")

if __name__ == '__main__':
    create_test_data()