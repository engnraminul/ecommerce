from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from .models import Order, OrderItem, ShippingAddress, OrderStatusHistory, Invoice, RefundRequest
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer,
    InvoiceSerializer, RefundRequestSerializer, OrderTrackingSerializer
)


class OrderListView(generics.ListAPIView):
    """List user orders"""
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """Order detail view"""
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__product', 'items__variant', 'shipping_address', 'status_history'
        )


class CreateOrderView(generics.CreateAPIView):
    """Create new order from cart - supports both authenticated users and guests"""
    serializer_class = CreateOrderSerializer
    permission_classes = [permissions.AllowAny]  # Allow guest users
    
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                
                if not serializer.is_valid():
                    return Response({
                        'error': 'Invalid order data',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                order = serializer.save()
                
                # Send order confirmation email (implement as needed)
                # self.send_order_confirmation_email(order)
                
                response_data = {
                    'message': 'Order created successfully',
                    'order': OrderDetailSerializer(order, context={'request': request}).data
                }
                
                print(f"Order created successfully: {order.order_number}")
                print(f"Response data: {response_data}")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(f"Error creating order: {str(e)}")
            return Response({
                'error': f'Failed to create order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_order(request, order_id):
    """Cancel order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_cancel:
        return Response({
            'error': 'Order cannot be cancelled at this stage'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # Restore stock
        for item in order.items.all():
            if item.variant:
                item.variant.stock_quantity += item.quantity
                item.variant.save()
            elif item.product.track_inventory:
                item.product.stock_quantity += item.quantity
                item.product.save()
        
        # Update order status
        old_status = order.status
        order.status = 'cancelled'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status='cancelled',
            notes=f'Cancelled by customer on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        )
    
    return Response({
        'message': 'Order cancelled successfully'
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def track_order(request, order_number):
    """Track order by order number - Public access"""
    try:
        order = Order.objects.select_related(
            'user', 'shipping_address'
        ).prefetch_related(
            'items__product__images',
            'items__variant',
            'status_history'
        ).get(order_number=order_number)
        
        serializer = OrderTrackingSerializer(order)
        return Response(serializer.data)
        
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found. Please verify your order number and try again.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error tracking order: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Unable to retrieve order information. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class InvoiceView(generics.RetrieveAPIView):
    """Get order invoice"""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        order_id = self.kwargs['order_id']
        order = get_object_or_404(Order, id=order_id, user=self.request.user)
        
        # Get or create invoice
        invoice, created = Invoice.objects.get_or_create(
            order=order,
            defaults={
                'billing_name': f"{order.user.first_name} {order.user.last_name}",
                'billing_email': order.customer_email,
                'billing_address': order.shipping_address.full_address if hasattr(order, 'shipping_address') else ''
            }
        )
        
        return invoice


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_invoice_pdf(request, order_id):
    """Generate PDF invoice"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Get or create invoice
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={
            'billing_name': f"{order.user.first_name} {order.user.last_name}",
            'billing_email': order.customer_email,
            'billing_address': order.shipping_address.full_address if hasattr(order, 'shipping_address') else ''
        }
    )
    
    # Generate PDF (implement PDF generation logic)
    # invoice.generate_pdf()
    
    return Response({
        'message': 'Invoice PDF generated successfully',
        'invoice_url': request.build_absolute_uri(invoice.invoice_file.url) if invoice.invoice_file else None
    })


class RefundRequestListView(generics.ListCreateAPIView):
    """List and create refund requests"""
    serializer_class = RefundRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RefundRequest.objects.filter(user=self.request.user).order_by('-created_at')


class RefundRequestDetailView(generics.RetrieveAPIView):
    """Refund request detail view"""
    serializer_class = RefundRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RefundRequest.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_stats(request):
    """Get user order statistics"""
    user = request.user
    
    # Calculate statistics
    orders = Order.objects.filter(user=user)
    
    stats = {
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status__in=['pending', 'confirmed', 'processing']).count(),
        'shipped_orders': orders.filter(status='shipped').count(),
        'delivered_orders': orders.filter(status='delivered').count(),
        'cancelled_orders': orders.filter(status='cancelled').count(),
        'total_spent': sum(order.total_amount for order in orders.filter(status__in=['delivered', 'shipped'])),
        'average_order_value': orders.filter(status__in=['delivered', 'shipped']).aggregate(
            avg_value=Avg('total_amount')
        )['avg_value'] or 0,
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recent_orders(request):
    """Get user's recent orders"""
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    serializer = OrderListSerializer(recent_orders, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reorder(request, order_id):
    """Reorder items from a previous order"""
    original_order = get_object_or_404(Order, id=order_id, user=request.user)
    
    from cart.models import Cart, CartItem
    
    # Get or create cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    added_items = []
    unavailable_items = []
    
    for order_item in original_order.items.all():
        product = order_item.product
        variant = order_item.variant
        
        # Check if product is still available
        if not product.is_active:
            unavailable_items.append(f"{product.name} - Product no longer available")
            continue
        
        # Check stock
        if variant:
            if variant.stock_quantity < order_item.quantity:
                if variant.stock_quantity > 0:
                    unavailable_items.append(f"{product.name} ({variant.name}) - Only {variant.stock_quantity} available")
                else:
                    unavailable_items.append(f"{product.name} ({variant.name}) - Out of stock")
                continue
        else:
            if product.track_inventory and product.stock_quantity < order_item.quantity:
                if product.stock_quantity > 0:
                    unavailable_items.append(f"{product.name} - Only {product.stock_quantity} available")
                else:
                    unavailable_items.append(f"{product.name} - Out of stock")
                continue
        
        # Add to cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': order_item.quantity}
        )
        
        if not item_created:
            cart_item.quantity += order_item.quantity
            cart_item.save()
        
        added_items.append(f"{product.name}" + (f" ({variant.name})" if variant else ""))
    
    return Response({
        'message': f'Reorder processed. {len(added_items)} items added to cart.',
        'added_items': added_items,
        'unavailable_items': unavailable_items,
        'cart_total': cart.total_items
    })
