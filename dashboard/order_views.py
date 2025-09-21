from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db import transaction

from orders.models import Order, OrderItem
from products.models import ProductVariant
from .serializers import OrderItemDashboardSerializer

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_order_items(request, order_id):
    """
    Explicit view function for getting order items
    """
    try:
        order = get_object_or_404(Order, id=order_id)
        print(f"Fetching items for order ID: {order.id}, Order Number: {order.order_number}")
        
        # Use select_related to optimize query
        items = OrderItem.objects.filter(order=order).select_related('product', 'variant')
        
        # Log the items for debugging
        print(f"Found {items.count()} items for order {order.order_number}")
        for item in items:
            print(f"Item ID: {item.id}, Product: {item.product_name}, Quantity: {item.quantity}, Price: {item.unit_price}")
        
        # Serialize the data
        serializer = OrderItemDashboardSerializer(items, many=True)
        serialized_data = serializer.data
        
        # Log the serialized data for debugging
        print(f"Serialized data: {serialized_data}")
        
        return Response(serialized_data)
    except Exception as e:
        print(f"Error in get_order_items view: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)  # Using 500 status code for internal errors

@api_view(['POST'])
@permission_classes([IsAdminUser])
@transaction.atomic
def restock_order_items(request, order_id):
    """
    Restocks inventory for order items when order status is changed to:
    - returned: All items are restocked
    - partially_returned: Only specified items are restocked (or all if restock_all=True)
    - cancelled: All items are restocked
    """
    try:
        order = get_object_or_404(Order, id=order_id)
        status_type = request.data.get('status_type')
        restock_all = request.data.get('restock_all', False)
        
        # Log for debugging
        print(f"Restocking items for order {order.order_number}, status: {status_type}, restock_all: {restock_all}")
        
        # Get items to restock
        items_to_restock = OrderItem.objects.filter(order=order).select_related('variant')
        
        # Maintain count of restocked items for reporting
        restocked_count = 0
        items_info = []
        
        # Process each item
        for item in items_to_restock:
            if not item.variant:
                print(f"Skipping item {item.id} - no variant associated")
                continue
                
            # Get variant and update stock
            variant = item.variant
            
            # Log before update
            print(f"Variant {variant.id} - current stock: {variant.stock_quantity}, adding: {item.quantity}")
            
            # Update stock
            variant.stock_quantity = variant.stock_quantity + item.quantity
            variant.save(update_fields=['stock_quantity'])
            
            # Log after update
            print(f"Updated variant {variant.id} stock to {variant.stock_quantity}")
            
            # Track restocked items
            restocked_count += 1
            items_info.append({
                'variant_id': variant.id,
                'variant_name': f"{variant.product.name} - {variant.color_name or ''} {variant.size or ''}".strip(),
                'quantity_restored': item.quantity,
                'new_stock_level': variant.stock_quantity
            })
        
        # Prepare response
        response_data = {
            'success': True,
            'order_id': order_id,
            'order_number': order.order_number,
            'status_type': status_type,
            'items_restocked': restocked_count,
            'items': items_info
        }
        
        return Response(response_data)
    
    except Exception as e:
        # Roll back transaction on error
        print(f"Error in restock_order_items view: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)