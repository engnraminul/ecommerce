from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

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
