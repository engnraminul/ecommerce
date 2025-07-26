#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')

# Setup Django
django.setup()

from products.models import Product, ProductVariant

# Color mapping to hex codes
COLOR_HEX_MAP = {
    'Red': '#dc3545',
    'Blue': '#007bff', 
    'Black': '#343a40',
    'White': '#ffffff',
    'Green': '#28a745',
    'Yellow': '#ffc107',
    'Purple': '#6f42c1',
    'Orange': '#fd7e14',
    'Pink': '#e83e8c',
    'Gray': '#6c757d',
    'Navy': '#004085',
    'Maroon': '#721c24'
}

def update_variants():
    """Update existing variants with hex colors and better names"""
    
    variants = ProductVariant.objects.all()
    print(f"Found {variants.count()} variants to update...")
    
    for variant in variants:
        old_name = variant.name
        old_color = variant.color
        
        # Update color to hex if it exists in our mapping
        if variant.color in COLOR_HEX_MAP:
            variant.color = COLOR_HEX_MAP[variant.color]
        
        # Create better variant names
        color_name = old_color  # Keep original color name for display
        size_info = f" - {variant.size}" if variant.size else ""
        material_info = f" ({variant.material})" if variant.material else ""
        
        # Create descriptive name
        if variant.product.name == "Classic Cotton T-Shirt":
            variant.name = f"{color_name} Cotton T-Shirt{size_info}"
        elif variant.product.name == "Modern Office Chair":
            variant.name = f"{color_name} Office Chair{material_info}"
        elif variant.product.name == "AirPods Pro":
            variant.name = f"{color_name} AirPods Pro"
        else:
            variant.name = f"{color_name} {variant.product.name}{size_info}{material_info}"
        
        variant.save()
        print(f"Updated: {old_name} -> {variant.name} (Color: {old_color} -> {variant.color})")
    
    print(f"\nSuccessfully updated {variants.count()} variants!")
    
    # Show updated variants by product
    print("\nUpdated variants by product:")
    for product in Product.objects.filter(variants__isnull=False).distinct():
        print(f"\n{product.name}:")
        for variant in product.variants.all():
            print(f"  - {variant.name} (Color: {variant.color}, Stock: {variant.stock_quantity})")

if __name__ == "__main__":
    update_variants()
