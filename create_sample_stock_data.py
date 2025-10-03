#!/usr/bin/env python
"""
Sample stock data creation script for testing the stock management feature
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append('/path/to/your/project')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductVariant, Category
from decimal import Decimal

def create_sample_data():
    """Create sample products and variants for stock testing"""
    
    # Create categories if they don't exist
    electronics_cat, created = Category.objects.get_or_create(
        name="Electronics",
        defaults={
            'description': 'Electronic devices and accessories',
            'is_active': True
        }
    )
    
    clothing_cat, created = Category.objects.get_or_create(
        name="Clothing",
        defaults={
            'description': 'Clothing and apparel',
            'is_active': True
        }
    )
    
    # Create sample products
    products_data = [
        {
            'name': 'Wireless Bluetooth Headphones',
            'sku': 'WBH001',
            'category': electronics_cat,
            'price': Decimal('2500.00'),
            'cost_price': Decimal('1800.00'),
            'stock_quantity': 15,
            'low_stock_threshold': 5,
            'description': 'High quality wireless bluetooth headphones',
            'track_inventory': True,
            'is_active': True
        },
        {
            'name': 'Gaming Mouse',
            'sku': 'GM001',
            'category': electronics_cat,
            'price': Decimal('1200.00'),
            'cost_price': Decimal('800.00'),
            'stock_quantity': 3,  # Low stock
            'low_stock_threshold': 5,
            'description': 'Professional gaming mouse',
            'track_inventory': True,
            'is_active': True
        },
        {
            'name': 'Smartphone Cable',
            'sku': 'SC001',
            'category': electronics_cat,
            'price': Decimal('150.00'),
            'cost_price': Decimal('80.00'),
            'stock_quantity': 0,  # Out of stock
            'low_stock_threshold': 10,
            'description': 'USB-C smartphone charging cable',
            'track_inventory': True,
            'is_active': True
        },
        {
            'name': 'Men\'s T-Shirt',
            'sku': 'MT001',
            'category': clothing_cat,
            'price': Decimal('800.00'),
            'cost_price': Decimal('400.00'),
            'stock_quantity': 50,
            'low_stock_threshold': 10,
            'description': 'Cotton men\'s t-shirt',
            'track_inventory': True,
            'is_active': True
        },
        {
            'name': 'Women\'s Dress',
            'sku': 'WD001',
            'category': clothing_cat,
            'price': Decimal('1500.00'),
            'cost_price': Decimal('900.00'),
            'stock_quantity': 25,
            'low_stock_threshold': 8,
            'description': 'Elegant women\'s dress',
            'track_inventory': True,
            'is_active': True
        }
    ]
    
    created_products = []
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            sku=product_data['sku'],
            defaults=product_data
        )
        created_products.append(product)
        if created:
            print(f"Created product: {product.name}")
        else:
            # Update existing product with new data
            for key, value in product_data.items():
                setattr(product, key, value)
            product.save()
            print(f"Updated product: {product.name}")
    
    # Create variants for t-shirt
    tshirt = Product.objects.get(sku='MT001')
    variants_data = [
        {
            'name': 'Small Red',
            'sku': 'MT001-S-RED',
            'size': 'S',
            'color': 'Red',
            'stock_quantity': 12,
            'is_default': True
        },
        {
            'name': 'Medium Blue',
            'sku': 'MT001-M-BLUE',
            'size': 'M',
            'color': 'Blue',
            'stock_quantity': 18
        },
        {
            'name': 'Large Black',
            'sku': 'MT001-L-BLACK',
            'size': 'L',
            'color': 'Black',
            'stock_quantity': 20
        },
        {
            'name': 'Extra Large White',
            'sku': 'MT001-XL-WHITE',
            'size': 'XL',
            'color': 'White',
            'stock_quantity': 0  # Out of stock variant
        }
    ]
    
    for variant_data in variants_data:
        variant_data['product'] = tshirt
        variant, created = ProductVariant.objects.get_or_create(
            sku=variant_data['sku'],
            defaults=variant_data
        )
        if created:
            print(f"Created variant: {variant.name}")
        else:
            print(f"Variant already exists: {variant.name}")
    
    # Create variants for dress
    dress = Product.objects.get(sku='WD001')
    dress_variants_data = [
        {
            'name': 'Small Pink',
            'sku': 'WD001-S-PINK',
            'size': 'S',
            'color': 'Pink',
            'stock_quantity': 8,
            'is_default': True
        },
        {
            'name': 'Medium Purple',
            'sku': 'WD001-M-PURPLE',
            'size': 'M',
            'color': 'Purple',
            'stock_quantity': 2  # Low stock
        },
        {
            'name': 'Large Navy',
            'sku': 'WD001-L-NAVY',
            'size': 'L',
            'color': 'Navy',
            'stock_quantity': 15
        }
    ]
    
    for variant_data in dress_variants_data:
        variant_data['product'] = dress
        variant, created = ProductVariant.objects.get_or_create(
            sku=variant_data['sku'],
            defaults=variant_data
        )
        if created:
            print(f"Created variant: {variant.name}")
        else:
            print(f"Variant already exists: {variant.name}")
    
    print("\nSample stock data creation completed!")
    print(f"Total products: {Product.objects.count()}")
    print(f"Total variants: {ProductVariant.objects.count()}")
    
    # Print stock summary
    total_products = Product.objects.filter(track_inventory=True).count()
    low_stock = Product.objects.filter(track_inventory=True, stock_quantity__lte=5).count()
    out_of_stock = Product.objects.filter(track_inventory=True, stock_quantity=0).count()
    
    print(f"\nStock Summary:")
    print(f"Total trackable products: {total_products}")
    print(f"Low stock products: {low_stock}")
    print(f"Out of stock products: {out_of_stock}")

if __name__ == '__main__':
    create_sample_data()