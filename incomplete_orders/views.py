from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from .models import (
    IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress,
    IncompleteOrderHistory, RecoveryEmailLog, IncompleteOrderAnalytics
)
from .serializers import (
    IncompleteOrderSerializer, IncompleteOrderCreateSerializer,
    IncompleteOrderUpdateSerializer, IncompleteOrderItemSerializer,
    IncompleteShippingAddressSerializer, IncompleteOrderHistorySerializer,
    RecoveryEmailLogSerializer, IncompleteOrderAnalyticsSerializer,
    ConvertToOrderSerializer, IncompleteOrderStatsSerializer
)


class IncompleteOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing incomplete orders"""
    queryset = IncompleteOrder.objects.all().prefetch_related('items', 'shipping_address', 'history')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['status', 'is_guest_order', 'recovery_attempts']
    search_fields = ['incomplete_order_id', 'customer_email', 'guest_email', 'user__username']
    ordering_fields = ['created_at', 'updated_at', 'total_amount', 'recovery_attempts']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IncompleteOrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return IncompleteOrderUpdateSerializer
        return IncompleteOrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(session_id=self.request.session.session_key)
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filter by expired status
        expired = self.request.query_params.get('expired')
        if expired == 'true':
            queryset = queryset.filter(expires_at__lt=timezone.now())
        elif expired == 'false':
            queryset = queryset.filter(expires_at__gte=timezone.now())
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def convert_to_order(self, request, pk=None):
        """Convert incomplete order to complete order"""
        incomplete_order = self.get_object()
        
        if not incomplete_order.can_convert:
            return Response(
                {'error': 'This incomplete order cannot be converted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = incomplete_order.convert_to_order()
            return Response({
                'message': 'Successfully converted to order',
                'order_number': order.order_number,
                'order_id': order.id
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_abandoned(self, request, pk=None):
        """Mark incomplete order as abandoned"""
        incomplete_order = self.get_object()
        reason = request.data.get('reason', 'Manually marked as abandoned')
        
        incomplete_order.mark_as_abandoned(reason)
        
        return Response({'message': 'Order marked as abandoned'})
    
    @action(detail=True, methods=['post'])
    def send_recovery_email(self, request, pk=None):
        """Send recovery email for incomplete order"""
        incomplete_order = self.get_object()
        email_type = request.data.get('email_type', 'abandoned_cart')
        
        # Increment recovery attempt
        incomplete_order.increment_recovery_attempt()
        
        # Log the recovery email (actual email sending would be implemented separately)
        RecoveryEmailLog.objects.create(
            incomplete_order=incomplete_order,
            email_type=email_type,
            recipient_email=incomplete_order.customer_email or incomplete_order.guest_email,
            subject=f"Complete your order - {incomplete_order.incomplete_order_id}"
        )
        
        # Log in history
        IncompleteOrderHistory.objects.create(
            incomplete_order=incomplete_order,
            action='recovery_sent',
            details=f'Recovery email sent: {email_type}',
            created_by_system=True
        )
        
        return Response({'message': 'Recovery email sent'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get incomplete order statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        stats = {
            'total_incomplete_orders': queryset.count(),
            'pending_orders': queryset.filter(status='pending').count(),
            'abandoned_orders': queryset.filter(status='abandoned').count(),
            'payment_failed_orders': queryset.filter(status='payment_failed').count(),
            'converted_orders': queryset.filter(status='converted').count(),
            'expired_orders': queryset.filter(expires_at__lt=timezone.now()).count(),
        }
        
        # Recovery attempts
        stats['total_recovery_attempts'] = queryset.aggregate(
            total=Sum('recovery_attempts')
        )['total'] or 0
        
        # Financial stats
        financial_stats = queryset.aggregate(
            total_value=Sum('total_amount'),
            abandoned_value=Sum('total_amount', filter=Q(status='abandoned')),
            converted_value=Sum('total_amount', filter=Q(status='converted'))
        )
        
        stats.update({
            'total_value': financial_stats['total_value'] or 0,
            'abandoned_value': financial_stats['abandoned_value'] or 0,
            'converted_value': financial_stats['converted_value'] or 0,
        })
        
        # Conversion rate
        if stats['total_incomplete_orders'] > 0:
            stats['conversion_rate'] = round(
                (stats['converted_orders'] / stats['total_incomplete_orders']) * 100, 2
            )
        else:
            stats['conversion_rate'] = 0
        
        # Average days to abandon
        abandoned_orders = queryset.filter(status='abandoned', abandoned_at__isnull=False)
        if abandoned_orders.exists():
            avg_days = abandoned_orders.extra(
                select={'days_diff': "EXTRACT(EPOCH FROM (abandoned_at - created_at))/86400"}
            ).aggregate(avg=Avg('days_diff'))['avg']
            stats['average_days_to_abandon'] = round(avg_days or 0, 2)
        else:
            stats['average_days_to_abandon'] = 0
        
        serializer = IncompleteOrderStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired incomplete orders"""
        expired_orders = self.get_queryset().filter(expires_at__lt=timezone.now())
        page = self.paginate_queryset(expired_orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(expired_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def cleanup_expired(self, request):
        """Delete expired incomplete orders"""
        days_to_keep = int(request.data.get('days_to_keep', 90))
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        expired_orders = IncompleteOrder.objects.filter(
            expires_at__lt=cutoff_date
        )
        count = expired_orders.count()
        expired_orders.delete()
        
        return Response({
            'message': f'Deleted {count} expired incomplete orders',
            'deleted_count': count
        })


class IncompleteOrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing incomplete order items"""
    queryset = IncompleteOrderItem.objects.all()
    serializer_class = IncompleteOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by incomplete order
        incomplete_order_id = self.request.query_params.get('incomplete_order')
        if incomplete_order_id:
            queryset = queryset.filter(incomplete_order__incomplete_order_id=incomplete_order_id)
        
        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(incomplete_order__user=self.request.user) | 
                Q(incomplete_order__session_id=self.request.session.session_key)
            )
        
        return queryset


class IncompleteOrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing incomplete order history"""
    queryset = IncompleteOrderHistory.objects.all()
    serializer_class = IncompleteOrderHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['action', 'created_by_system']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by incomplete order
        incomplete_order_id = self.request.query_params.get('incomplete_order')
        if incomplete_order_id:
            queryset = queryset.filter(incomplete_order__incomplete_order_id=incomplete_order_id)
        
        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(incomplete_order__user=self.request.user) | 
                Q(incomplete_order__session_id=self.request.session.session_key)
            )
        
        return queryset


class RecoveryEmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing recovery email logs"""
    queryset = RecoveryEmailLog.objects.all()
    serializer_class = RecoveryEmailLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['email_type', 'delivered', 'opened', 'clicked', 'responded']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Only staff can view all recovery emails
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(incomplete_order__user=self.request.user) | 
                Q(incomplete_order__session_id=self.request.session.session_key)
            )
        
        return queryset


class IncompleteOrderAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing incomplete order analytics"""
    queryset = IncompleteOrderAnalytics.objects.all()
    serializer_class = IncompleteOrderAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['date']
    ordering = ['-date']
    
    def get_permissions(self):
        # Only staff can view analytics
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


# Utility functions for cart integration
def create_incomplete_order_from_cart(request, cart_items, customer_data=None):
    """
    Create an incomplete order from cart items
    This function can be called from cart views when user doesn't complete checkout
    """
    incomplete_order_data = {
        'user': request.user if request.user.is_authenticated else None,
        'is_guest_order': not request.user.is_authenticated,
        'session_id': request.session.session_key,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'ip_address': request.META.get('REMOTE_ADDR'),
        'referrer_url': request.META.get('HTTP_REFERER', ''),
    }
    
    if customer_data:
        incomplete_order_data.update(customer_data)
    
    # Create incomplete order
    incomplete_order = IncompleteOrder.objects.create(**incomplete_order_data)
    
    # Add items
    for cart_item in cart_items:
        IncompleteOrderItem.objects.create(
            incomplete_order=incomplete_order,
            product=cart_item.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price
        )
    
    # Calculate totals
    incomplete_order.calculate_totals()
    
    return incomplete_order


def track_cart_abandonment(request, cart_items, stage='cart'):
    """
    Track when user abandons cart at different stages
    """
    if cart_items:
        incomplete_order = create_incomplete_order_from_cart(request, cart_items)
        
        # Mark as abandoned with reason
        abandonment_reasons = {
            'cart': 'Left cart page',
            'checkout': 'Abandoned at checkout',
            'payment': 'Abandoned at payment',
            'session_timeout': 'Session timeout'
        }
        
        incomplete_order.mark_as_abandoned(abandonment_reasons.get(stage, 'Unknown'))
        
        return incomplete_order
    
    return None


@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def save_checkout_data(request):
    """Save checkout form data to session for abandonment tracking"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # Store checkout data in session
        request.session['checkout_data'] = data
        request.session['checkout_timestamp'] = str(timezone.now())
        
        return JsonResponse({'status': 'saved'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def track_checkout_abandonment(request):
    """Track checkout abandonment and create incomplete order"""
    try:
        from cart.models import Cart
        
        # Get checkout data from session
        checkout_data = request.session.get('checkout_data')
        if not checkout_data:
            return JsonResponse({'status': 'no_data'})
        
        # Get user's cart
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return JsonResponse({'status': 'no_cart'})
        else:
            # Guest user
            session_id = request.session.session_key
            if not session_id:
                return JsonResponse({'status': 'no_session'})
            
            try:
                cart = Cart.objects.get(session_id=session_id, user=None)
            except Cart.DoesNotExist:
                return JsonResponse({'status': 'no_cart'})
        
        # Check if cart has items
        if not cart.items.exists():
            return JsonResponse({'status': 'empty_cart'})
        
        # Check if incomplete order already exists for this cart/session
        if request.user.is_authenticated:
            existing_incomplete = IncompleteOrder.objects.filter(
                user=request.user,
                status='pending'
            ).first()
        else:
            existing_incomplete = IncompleteOrder.objects.filter(
                session_id=session_id,
                user=None,
                status='pending'
            ).first()
        
        # If incomplete order already exists, update it
        if existing_incomplete:
            _update_incomplete_order(existing_incomplete, checkout_data)
            incomplete_order = existing_incomplete
        else:
            # Create new incomplete order
            incomplete_order = _create_incomplete_order(request, cart, checkout_data)
        
        return JsonResponse({
            'status': 'created',
            'incomplete_order_id': incomplete_order.incomplete_order_id
        })
        
    except Exception as e:
        import traceback
        print(f"Error in abandonment tracking: {str(e)}")
        print(traceback.format_exc())
        
        return JsonResponse({'error': str(e)}, status=500)


def _create_incomplete_order(request, cart, checkout_data):
    """Create a new incomplete order from cart and checkout data"""
    # Prepare customer data
    customer_data = {
        'email': checkout_data.get('email', ''),
        'phone': checkout_data.get('phone_number', ''),
        'notes': checkout_data.get('order_instruction', ''),
    }
    
    # Prepare shipping data
    shipping_data = {}
    if checkout_data.get('full_name'):
        name_parts = checkout_data['full_name'].split(' ', 1)
        shipping_data['first_name'] = name_parts[0]
        shipping_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
    
    shipping_data.update({
        'phone': checkout_data.get('phone_number', ''),
        'address_line_1': checkout_data.get('address', ''),
        'city': 'Not specified',
        'postal_code': '',
        'country': 'Bangladesh',
    })
    
    # Create incomplete order
    order_data = {
        'user': request.user if request.user.is_authenticated else None,
        'is_guest_order': not request.user.is_authenticated,
        'session_id': request.session.session_key,
        'customer_email': customer_data['email'],
        'customer_phone': customer_data['phone'],
        'customer_notes': customer_data['notes'],
        'guest_email': customer_data['email'] if not request.user.is_authenticated else '',
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'ip_address': _get_client_ip(request),
        'referrer_url': request.META.get('HTTP_REFERER', ''),
    }
    
    incomplete_order = IncompleteOrder.objects.create(**order_data)
    
    # Add cart items to incomplete order
    for cart_item in cart.items.all():
        IncompleteOrderItem.objects.create(
            incomplete_order=incomplete_order,
            product=cart_item.product,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price
        )
    
    # Add shipping address if we have enough data
    if shipping_data.get('first_name') and shipping_data.get('address_line_1'):
        IncompleteShippingAddress.objects.create(
            incomplete_order=incomplete_order,
            **shipping_data
        )
    
    # Calculate totals
    incomplete_order.calculate_totals()
    
    # Mark as abandoned
    incomplete_order.mark_as_abandoned('checkout_form_abandonment')
    
    return incomplete_order


def _update_incomplete_order(incomplete_order, checkout_data):
    """Update existing incomplete order with new checkout data"""
    # Update customer data
    if checkout_data.get('email'):
        incomplete_order.customer_email = checkout_data['email']
        if not incomplete_order.user:
            incomplete_order.guest_email = checkout_data['email']
    
    if checkout_data.get('phone_number'):
        incomplete_order.customer_phone = checkout_data['phone_number']
    
    if checkout_data.get('order_instruction'):
        incomplete_order.customer_notes = checkout_data['order_instruction']
    
    incomplete_order.save()
    
    # Update shipping address if exists
    if hasattr(incomplete_order, 'shipping_address'):
        shipping_address = incomplete_order.shipping_address
        
        if checkout_data.get('full_name'):
            name_parts = checkout_data['full_name'].split(' ', 1)
            shipping_address.first_name = name_parts[0]
            shipping_address.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if checkout_data.get('phone_number'):
            shipping_address.phone = checkout_data['phone_number']
        
        if checkout_data.get('address'):
            shipping_address.address_line_1 = checkout_data['address']
        
        shipping_address.save()


def _get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '')
