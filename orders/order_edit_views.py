from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem, ShippingAddress
from .order_edit_serializers import (
    OrderEditSerializer, OrderItemQuantityUpdateSerializer,
    OrderItemAddSerializer, OrderItemDeleteSerializer, 
    ShippingAddressEditSerializer
)
from products.models import Product, ProductVariant


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_order_for_edit(request, order_id):
    """Get order details for editing"""
    try:
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderEditSerializer(order)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Failed to load order: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
@transaction.atomic
def update_order_item_quantity(request, order_id):
    """Update quantity of an order item with stock management"""
    try:
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderItemQuantityUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id = serializer.validated_data['item_id']
        new_quantity = serializer.validated_data['new_quantity']
        
        # Get the order item
        order_item = get_object_or_404(OrderItem, id=item_id, order=order)
        old_quantity = order_item.quantity
        quantity_difference = new_quantity - old_quantity
        
        # Update stock based on quantity change
        if order_item.variant:
            variant = order_item.variant
            # If quantity increased, reduce stock; if decreased, increase stock
            new_stock = variant.stock_quantity - quantity_difference
            
            if new_stock < 0:
                return Response(
                    {'error': f'Insufficient stock. Available: {variant.stock_quantity + old_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            variant.stock_quantity = new_stock
            variant.save()
        elif hasattr(order_item.product, 'stock_quantity'):
            product = order_item.product
            new_stock = product.stock_quantity - quantity_difference
            
            if new_stock < 0:
                return Response(
                    {'error': f'Insufficient stock. Available: {product.stock_quantity + old_quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            product.stock_quantity = new_stock
            product.save()
        
        # Update order item
        order_item.quantity = new_quantity
        order_item.save()
        
        # Recalculate order totals
        order.calculate_totals()
        
        return Response({
            'success': True,
            'message': 'Order item quantity updated successfully',
            'old_quantity': old_quantity,
            'new_quantity': new_quantity,
            'quantity_difference': quantity_difference,
            'order_total': str(order.total_amount)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to update quantity: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
@transaction.atomic
def add_order_item(request, order_id):
    """Add new item to order with stock management"""
    try:
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderItemAddSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        product = validated_data['product']
        variant = validated_data.get('variant')
        quantity = validated_data['quantity']
        
        # Check if item already exists in order
        existing_item = OrderItem.objects.filter(
            order=order,
            product=product,
            variant=variant
        ).first()
        
        if existing_item:
            # Update existing item quantity
            new_quantity = existing_item.quantity + quantity
            
            # Check stock for the additional quantity
            if variant:
                if variant.stock_quantity < quantity:
                    return Response(
                        {'error': f'Insufficient stock for additional quantity. Available: {variant.stock_quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                variant.stock_quantity -= quantity
                variant.save()
            elif hasattr(product, 'stock_quantity'):
                if product.stock_quantity < quantity:
                    return Response(
                        {'error': f'Insufficient stock for additional quantity. Available: {product.stock_quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                product.stock_quantity -= quantity
                product.save()
            
            existing_item.quantity = new_quantity
            existing_item.save()
            
            message = f'Increased existing item quantity by {quantity}'
            item_id = existing_item.id
        else:
            # Create new order item
            # Reduce stock
            if variant:
                variant.stock_quantity -= quantity
                variant.save()
                unit_price = variant.price if hasattr(variant, 'price') else product.price
            else:
                if hasattr(product, 'stock_quantity'):
                    product.stock_quantity -= quantity
                    product.save()
                unit_price = product.price
            
            # Create the order item
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                unit_price=unit_price
            )
            
            message = 'New item added to order successfully'
            item_id = order_item.id
        
        # Recalculate order totals
        order.calculate_totals()
        
        return Response({
            'success': True,
            'message': message,
            'item_id': item_id,
            'order_total': str(order.total_amount)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to add item: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
@transaction.atomic
def delete_order_item(request, order_id):
    """Delete item from order and restore stock"""
    try:
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderItemDeleteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id = serializer.validated_data['item_id']
        order_item = get_object_or_404(OrderItem, id=item_id, order=order)
        
        # Check if this is the last item in the order
        if order.items.count() <= 1:
            return Response(
                {'error': 'Cannot delete the last item from an order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore stock
        if order_item.variant:
            variant = order_item.variant
            variant.stock_quantity += order_item.quantity
            variant.save()
        elif hasattr(order_item.product, 'stock_quantity'):
            product = order_item.product
            product.stock_quantity += order_item.quantity
            product.save()
        
        # Store item info before deletion
        item_info = {
            'product_name': order_item.product_name,
            'variant_name': order_item.variant_name,
            'quantity': order_item.quantity
        }
        
        # Delete the item
        order_item.delete()
        
        # Recalculate order totals
        order.calculate_totals()
        
        return Response({
            'success': True,
            'message': f'Item "{item_info["product_name"]}" removed from order',
            'deleted_item': item_info,
            'order_total': str(order.total_amount)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to delete item: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
@transaction.atomic
def update_shipping_address(request, order_id):
    """Update order shipping address"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        # Get or create shipping address
        shipping_address, created = ShippingAddress.objects.get_or_create(
            order=order,
            defaults={
                'first_name': '',
                'address_line_1': '',
                'city': '',
                'state': '',
                'postal_code': '',
                'country': 'Bangladesh'
            }
        )
        
        serializer = ShippingAddressEditSerializer(
            shipping_address, 
            data=request.data, 
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid address data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Shipping address updated successfully',
            'address': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to update shipping address: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_available_products(request):
    """Get available products for adding to order"""
    try:
        products = Product.objects.filter(
            is_active=True
        ).prefetch_related('variants')
        
        product_data = []
        for product in products:
            variants = []
            for variant in product.variants.filter(is_active=True):
                variants.append({
                    'id': variant.id,
                    'name': variant.name,
                    'sku': variant.sku,
                    'price': str(variant.price if hasattr(variant, 'price') else product.price),
                    'stock_quantity': variant.stock_quantity,
                    'color_name': getattr(variant, 'color_name', ''),
                    'size': getattr(variant, 'size', ''),
                })
            
            product_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': str(product.price),
                'stock_quantity': getattr(product, 'stock_quantity', 0),
                'variants': variants
            })
        
        return Response({
            'success': True,
            'products': product_data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to load products: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_courier_info(request, order_id):
    """Update courier ID and/or courier date for an order"""
    try:
        print(f"Updating courier info for order {order_id}")
        print(f"Request data: {request.data}")
        
        order = get_object_or_404(Order, id=order_id)
        print(f"Found order: {order.order_number}")
        
        courier_id = request.data.get('courier_id')
        curier_date = request.data.get('curier_date')
        
        print(f"Courier ID: {courier_id}, Courier Date: {curier_date}")
        
        # Update fields if provided
        if 'courier_id' in request.data:
            order.curier_id = courier_id if courier_id else ''
            print(f"Updated curier_id to: {order.curier_id}")
            
        if 'curier_date' in request.data:
            if curier_date:
                # Convert string date to date object if necessary
                from datetime import datetime
                if isinstance(curier_date, str):
                    try:
                        # Parse the date string (expecting YYYY-MM-DD format)
                        parsed_date = datetime.strptime(curier_date, '%Y-%m-%d').date()
                        order.curier_date = parsed_date
                        print(f"Parsed and updated curier_date to: {order.curier_date}")
                    except ValueError as e:
                        print(f"Date parsing error: {e}")
                        return Response(
                            {'error': f'Invalid date format. Expected YYYY-MM-DD, got: {curier_date}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    order.curier_date = curier_date
                    print(f"Updated curier_date to: {order.curier_date}")
            else:
                order.curier_date = None
                print("Set curier_date to None")
        
        order.save()
        print("Order saved successfully")
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': 'Courier information updated successfully',
            'curier_id': order.curier_id,
            'curier_date': order.curier_date.isoformat() if order.curier_date else None
        }
        print(f"Response data: {response_data}")
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Error updating courier info: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response(
            {'error': f'Failed to update courier information: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )