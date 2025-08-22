from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderItem


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_orders(request):
    """
    API endpoint to get user's recent orders
    Returns JSON with the recent orders
    """
    try:
        # Get recent orders for the current user
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        # Format response data
        orders_data = []
        for order in orders:
            # Convert order to dict
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.isoformat(),
                'status': order.status,
                'status_display': dict(Order.ORDER_STATUS_CHOICES).get(order.status, order.status),
                'total_amount': str(order.total_amount),
                'items_count': order.items.count(),
            })
        
        # Return formatted data
        return Response({
            'orders': orders_data
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail_api(request, order_id):
    """
    API endpoint to get order details
    Returns JSON with order details
    """
    try:
        # Get the order for the current user
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Get order items
        items = []
        for item in order.items.all():
            # Get the primary image if available
            image_url = None
            if item.product and hasattr(item.product, 'images'):
                product_image = item.product.images.filter(is_primary=True).first()
                if product_image:
                    image_url = product_image.image.url
            
            items.append({
                'id': item.id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'variant_name': item.variant_name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price),
                'image_url': image_url,
            })
        
        # Format shipping address
        shipping_address = None
        if hasattr(order, 'shipping_address'):
            shipping_address = {
                'full_name': order.shipping_address.full_name,
                'address_line_1': order.shipping_address.address_line_1,
                'address_line_2': order.shipping_address.address_line_2,
                'city': order.shipping_address.city,
                'state': order.shipping_address.state,
                'postal_code': order.shipping_address.postal_code,
                'country': order.shipping_address.country,
                'phone': order.shipping_address.phone,
                'email': order.shipping_address.email,
            }
        
        # Format order data
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'created_at': order.created_at.isoformat(),
            'status': order.status,
            'status_display': dict(Order.ORDER_STATUS_CHOICES).get(order.status, order.status),
            'payment_status': order.payment_status,
            'payment_status_display': dict(Order.PAYMENT_STATUS_CHOICES).get(order.payment_status, order.payment_status),
            'subtotal': str(order.subtotal),
            'shipping_cost': str(order.shipping_cost),
            'tax_amount': str(order.tax_amount),
            'discount_amount': str(order.discount_amount),
            'total_amount': str(order.total_amount),
            'coupon_code': order.coupon_code,
            'coupon_discount': str(order.coupon_discount),
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
            'customer_notes': order.customer_notes,
            'is_guest_order': order.is_guest_order,
            'can_cancel': order.can_cancel,
            'items': items,
            'shipping_address': shipping_address,
        }
        
        # Return formatted data
        return Response(order_data)
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)
