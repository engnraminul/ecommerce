from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from orders.models import Order, OrderItem
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