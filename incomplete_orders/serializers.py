from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress,
    IncompleteOrderHistory, RecoveryEmailLog, IncompleteOrderAnalytics
)
from products.serializers import ProductDetailSerializer, ProductVariantSerializer

User = get_user_model()


class IncompleteOrderItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = IncompleteOrderItem
        fields = [
            'id', 'product', 'variant', 'product_name', 'product_sku',
            'variant_name', 'quantity', 'unit_price', 'total_price',
            'added_at', 'updated_at'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'variant_name', 'added_at', 'updated_at']


class IncompleteShippingAddressSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = IncompleteShippingAddress
        fields = [
            'id', 'first_name', 'last_name', 'company', 'address_line_1',
            'address_line_2', 'city', 'state', 'postal_code', 'country',
            'phone', 'email', 'delivery_instructions', 'full_name',
            'full_address', 'is_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class IncompleteOrderHistorySerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = IncompleteOrderHistory
        fields = [
            'id', 'action', 'action_display', 'details', 'user',
            'user_username', 'created_by_system', 'ip_address',
            'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class IncompleteOrderSerializer(serializers.ModelSerializer):
    items = IncompleteOrderItemSerializer(many=True, read_only=True)
    shipping_address = IncompleteShippingAddressSerializer(read_only=True)
    history = IncompleteOrderHistorySerializer(many=True, read_only=True)
    
    # Computed fields
    total_items = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_since_created = serializers.IntegerField(read_only=True)
    can_convert = serializers.BooleanField(read_only=True)
    
    # Display fields
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = IncompleteOrder
        fields = [
            'id', 'incomplete_order_id', 'user', 'user_username', 'is_guest_order',
            'guest_email', 'session_id', 'status', 'status_display',
            'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount',
            'total_amount', 'coupon_code', 'coupon_discount',
            'customer_email', 'customer_phone', 'recovery_attempts',
            'last_recovery_attempt', 'user_agent', 'ip_address',
            'referrer_url', 'customer_notes', 'admin_notes',
            'abandonment_reason', 'created_at', 'updated_at',
            'abandoned_at', 'expires_at', 'converted_order_id',
            'converted_at', 'items', 'shipping_address', 'history',
            'total_items', 'is_expired', 'days_since_created', 'can_convert'
        ]
        read_only_fields = [
            'id', 'incomplete_order_id', 'created_at', 'updated_at',
            'abandoned_at', 'expires_at', 'converted_at', 'converted_order_id'
        ]


class IncompleteOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating incomplete orders"""
    items = IncompleteOrderItemSerializer(many=True)
    shipping_address = IncompleteShippingAddressSerializer(required=False)
    
    class Meta:
        model = IncompleteOrder
        fields = [
            'user', 'is_guest_order', 'guest_email', 'session_id',
            'customer_email', 'customer_phone', 'customer_notes',
            'user_agent', 'ip_address', 'referrer_url', 'items',
            'shipping_address', 'coupon_code'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        shipping_address_data = validated_data.pop('shipping_address', None)
        
        # Create the incomplete order
        incomplete_order = IncompleteOrder.objects.create(**validated_data)
        
        # Create items
        for item_data in items_data:
            IncompleteOrderItem.objects.create(
                incomplete_order=incomplete_order,
                **item_data
            )
        
        # Create shipping address if provided
        if shipping_address_data:
            IncompleteShippingAddress.objects.create(
                incomplete_order=incomplete_order,
                **shipping_address_data
            )
        
        # Calculate totals
        incomplete_order.calculate_totals()
        
        # Log creation
        IncompleteOrderHistory.objects.create(
            incomplete_order=incomplete_order,
            action='created',
            details='Incomplete order created',
            created_by_system=True
        )
        
        return incomplete_order


class IncompleteOrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating incomplete orders"""
    
    class Meta:
        model = IncompleteOrder
        fields = [
            'customer_email', 'customer_phone', 'customer_notes',
            'admin_notes', 'abandonment_reason'
        ]


class RecoveryEmailLogSerializer(serializers.ModelSerializer):
    email_type_display = serializers.CharField(source='get_email_type_display', read_only=True)
    incomplete_order_id = serializers.CharField(source='incomplete_order.incomplete_order_id', read_only=True)
    
    class Meta:
        model = RecoveryEmailLog
        fields = [
            'id', 'incomplete_order', 'incomplete_order_id', 'email_type',
            'email_type_display', 'recipient_email', 'subject', 'sent_at',
            'delivered', 'opened', 'clicked', 'responded', 'response_date',
            'discount_code', 'discount_percentage'
        ]
        read_only_fields = ['id', 'sent_at']


class IncompleteOrderAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncompleteOrderAnalytics
        fields = [
            'id', 'date', 'total_incomplete_orders', 'abandoned_orders',
            'converted_orders', 'expired_orders', 'recovery_emails_sent',
            'recovery_success_count', 'total_lost_revenue', 'recovered_revenue',
            'conversion_rate', 'recovery_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'conversion_rate', 'recovery_rate', 'created_at', 'updated_at']


class ConvertToOrderSerializer(serializers.Serializer):
    """Serializer for converting incomplete order to complete order"""
    incomplete_order_id = serializers.CharField()
    
    def validate_incomplete_order_id(self, value):
        try:
            incomplete_order = IncompleteOrder.objects.get(incomplete_order_id=value)
            if not incomplete_order.can_convert:
                raise serializers.ValidationError("This incomplete order cannot be converted")
            return value
        except IncompleteOrder.DoesNotExist:
            raise serializers.ValidationError("Incomplete order not found")
    
    def save(self):
        incomplete_order = IncompleteOrder.objects.get(
            incomplete_order_id=self.validated_data['incomplete_order_id']
        )
        return incomplete_order.convert_to_order()


class IncompleteOrderStatsSerializer(serializers.Serializer):
    """Serializer for incomplete order statistics"""
    total_incomplete_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    abandoned_orders = serializers.IntegerField()
    payment_failed_orders = serializers.IntegerField()
    converted_orders = serializers.IntegerField()
    expired_orders = serializers.IntegerField()
    total_recovery_attempts = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    abandoned_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    converted_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_days_to_abandon = serializers.DecimalField(max_digits=5, decimal_places=2)