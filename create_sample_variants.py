#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductVariant

def create_sample_variants():
    """Create sample variants for existing products"""
    
    # Get the first few products
    products = Product.objects.filter(is_active=True)[:3]
    
    if not products:
        print("No products found. Please create some products first.")
        return
    
    # Sample variant data
    colors = ['Red', 'Blue', 'Black', 'White', 'Green']
    sizes = ['XS', 'S', 'M', 'L', 'XL']
    
    for product in products:
        print(f"Creating variants for: {product.name}")
        
        # Clear existing variants
        ProductVariant.objects.filter(product=product).delete()
        
        # Create variants based on product type
        if 'shirt' in product.name.lower() or 'tshirt' in product.name.lower() or 'top' in product.name.lower():
            # Clothing - create size and color variants
            for color in colors[:3]:  # First 3 colors
                for size in sizes[1:4]:  # S, M, L
                    variant = ProductVariant.objects.create(
                        product=product,
                        name=f"{color} - {size}",
                        size=size,
                        color=color,
                        stock_quantity=10,
                        price=product.price + (2 if size == 'L' else 0),  # L size costs $2 more
                        is_active=True
                    )
                    print(f"  Created variant: {variant.name}")
        
        elif 'shoe' in product.name.lower() or 'sneaker' in product.name.lower():
            # Shoes - create size variants
            shoe_sizes = ['7', '8', '9', '10', '11', '12']
            for size in shoe_sizes[:4]:
                for color in colors[:2]:  # First 2 colors
                    variant = ProductVariant.objects.create(
                        product=product,
                        name=f"{color} - Size {size}",
                        size=size,
                        color=color,
                        stock_quantity=5,
                        price=product.price,
                        is_active=True
                    )
                    print(f"  Created variant: {variant.name}")
        
        else:
            # General products - create color variants
            for color in colors[:4]:
                variant = ProductVariant.objects.create(
                    product=product,
                    name=f"{color}",
                    color=color,
                    stock_quantity=8,
                    price=product.price + (5 if color in ['Red', 'Blue'] else 0),  # Premium colors
                    is_active=True
                )
                print(f"  Created variant: {variant.name}")
        
        print()

if __name__ == '__main__':
    create_sample_variants()
    print("Sample variants created successfully!")
