#!/usr/bin/env python
import os
import sys
import django
from datetime import timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from products.models import Product, ProductVariant, ProductImage, Category
from orders.models import Order, OrderItem

def test_products_performance():
    """Test the products performance logic to identify the error"""
    try:
        print("Starting products performance test...")
        
        # Get query parameters (simulating the actual request)
        period = 'month'
        date_from = '2025-09-30'
        date_to = '2025-10-24'
        search = ''
        sort_by = 'orders'
        sort_order = 'desc'
        
        print(f"Parameters: period={period}, date_from={date_from}, date_to={date_to}")
        
        # Build date filter for orders
        order_date_filter = Q()
        if date_from:
            try:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                order_date_filter &= Q(created_at__date__gte=from_date)
                print(f"Added from_date filter: {from_date}")
            except ValueError as e:
                print(f"Error parsing from_date: {e}")
                    
        if date_to:
            try:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                order_date_filter &= Q(created_at__date__lte=to_date)
                print(f"Added to_date filter: {to_date}")
            except ValueError as e:
                print(f"Error parsing to_date: {e}")
        
        print(f"Order date filter: {order_date_filter}")
        
        # Get all active products
        products_query = Product.objects.filter(is_active=True)
        print(f"Found {products_query.count()} active products")
        
        # Apply search filter
        if search:
            products_query = products_query.filter(
                Q(name__icontains=search) | 
                Q(category__name__icontains=search)
            )
            print(f"After search filter: {products_query.count()} products")
        
        products_data = []
        
        # Test with just the first 3 products to avoid overwhelming output
        for i, product in enumerate(products_query[:3]):
            print(f"\nProcessing product {i+1}: {product.name} (ID: {product.id})")
            
            try:
                # Get all orders for this product within date range
                product_orders = Order.objects.filter(
                    order_date_filter,
                    items__product=product
                ).distinct()
                
                print(f"  Found {product_orders.count()} orders for this product")
                
                # Count total orders
                orders_count = product_orders.count()
                
                # Calculate delivered quantity
                delivered_orders = product_orders.filter(status__in=['delivered', 'shipped'])
                print(f"  Found {delivered_orders.count()} delivered/shipped orders")
                
                delivered_quantity = OrderItem.objects.filter(
                    order__in=delivered_orders,
                    product=product
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                print(f"  Delivered quantity: {delivered_quantity}")
                
                # Calculate revenue (from delivered and shipped orders + partial returns)
                delivered_shipped_revenue = Order.objects.filter(
                    order_date_filter &
                    Q(status__in=['delivered', 'shipped']) &
                    Q(items__product=product)
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                print(f"  Delivered/shipped revenue: {delivered_shipped_revenue}")
                
                partial_return_revenue = Order.objects.filter(
                    order_date_filter &
                    Q(status='partially_returned') &
                    Q(items__product=product)
                ).aggregate(total=Sum('partially_ammount'))['total'] or 0
                
                print(f"  Partial return revenue: {partial_return_revenue}")
                
                total_revenue = delivered_shipped_revenue + partial_return_revenue
                
                # Get category name
                category_name = product.category.name if product.category else 'Uncategorized'
                
                # Get product image URL
                image_url = None
                if hasattr(product, 'images') and product.images.exists():
                    first_image = product.images.first()
                    if first_image and first_image.image:
                        image_url = first_image.image_url
                elif hasattr(product, 'productimage_set') and product.productimage_set.exists():
                    first_image = product.productimage_set.first()
                    if first_image and first_image.image:
                        image_url = first_image.image_url
                
                product_data = {
                    'id': product.id,
                    'product_name': product.name,
                    'category': category_name,
                    'orders': orders_count,
                    'delivered_quantity': int(delivered_quantity),
                    'revenue': float(total_revenue),
                    'price': float(product.price) if product.price else 0,
                    'cost_price': float(product.cost_price) if product.cost_price else 0,
                    'stock': product.stock_quantity if hasattr(product, 'stock_quantity') else 0,
                    'image_url': image_url
                }
                
                products_data.append(product_data)
                print(f"  Product data created successfully: {product_data}")
                
            except Exception as e:
                print(f"  ERROR processing product {product.name}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        print(f"\nSuccessfully processed {len(products_data)} products")
        print("Test completed successfully!")
        
        return {
            'products': products_data,
            'total_count': len(products_data),
            'filters': {
                'period': period,
                'date_from': date_from,
                'date_to': date_to,
                'search': search,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
        
    except Exception as e:
        print(f"CRITICAL ERROR in test: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    test_products_performance()