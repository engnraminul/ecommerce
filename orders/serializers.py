from rest_framework import serializers
from .models import Order, OrderItem, ShippingAddress, OrderStatusHistory, Invoice, RefundRequest
from products.serializers import ProductListSerializer, ProductVariantSerializer
from users.serializers import AddressSerializer


class ShippingAddressSerializer(serializers.ModelSerializer):
    """Shipping address serializer"""
    full_name = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    # Make these fields optional since we simplified the checkout form
    city = serializers.CharField(required=False, allow_blank=True, default='Dhaka')
    state = serializers.CharField(required=False, allow_blank=True, default='Dhaka')
    postal_code = serializers.CharField(required=False, allow_blank=True, default='1000')
    country = serializers.CharField(required=False, allow_blank=True, default='Bangladesh')
    
    class Meta:
        model = ShippingAddress
        fields = (
            'first_name', 'last_name', 'full_name', 'company',
            'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'phone', 'email',
            'delivery_instructions', 'full_address'
        )


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = (
            'id', 'product', 'variant', 'product_name', 'variant_name',
            'quantity', 'unit_price', 'total_price'
        )
        read_only_fields = ('id', 'product_name', 'variant_name')


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Order status history serializer"""
    changed_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = (
            'id', 'old_status', 'new_status', 'changed_by', 'notes',
            'tracking_number', 'carrier', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class OrderListSerializer(serializers.ModelSerializer):
    """Order list serializer (for list views)"""
    total_items = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    is_cod_order = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'payment_status',
            'total_amount', 'total_items', 'can_cancel', 'is_cod_order',
            'created_at', 'confirmed_at', 'shipped_at', 'delivered_at'
        )
        read_only_fields = ('id', 'order_number')


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail serializer (for detail views)"""
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    is_cod_order = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'payment_status',
            'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount',
            'coupon_code', 'coupon_discount', 'total_amount', 'total_items',
            'customer_email', 'customer_phone', 'customer_notes',
            'can_cancel', 'is_cod_order', 'items', 'shipping_address',
            'status_history', 'created_at', 'updated_at', 'confirmed_at',
            'shipped_at', 'delivered_at'
        )
        read_only_fields = ('id', 'order_number', 'created_at', 'updated_at')


class CreateOrderSerializer(serializers.Serializer):
    """Create order serializer"""
    shipping_address = ShippingAddressSerializer()
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate_coupon_code(self, value):
        if value:
            from cart.models import Coupon
            from django.utils import timezone
            
            try:
                coupon = Coupon.objects.get(code=value.upper(), is_active=True)
                if timezone.now() < coupon.valid_from or timezone.now() > coupon.valid_until:
                    raise serializers.ValidationError("Coupon is not valid at this time.")
                self.coupon = coupon
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon code.")
        return value.upper() if value else value
    
    def create(self, validated_data):
        from cart.models import Cart, CouponUsage
        from django.utils import timezone
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        user = self.context['request'].user
        shipping_data = validated_data.pop('shipping_address')
        
        logger.info(f"Creating order for user: {user}")
        logger.info(f"Shipping data: {shipping_data}")
        
        # Get user's cart
        try:
            cart = Cart.objects.get(user=user)
            logger.info(f"Found cart with {cart.items.count()} items")
        except Cart.DoesNotExist:
            logger.error("Cart not found for user")
            raise serializers.ValidationError("Cart is empty.")
        
        if not cart.items.exists():
            logger.error("Cart has no items")
            raise serializers.ValidationError("Cart is empty.")
        
        # Calculate totals
        subtotal = cart.subtotal
        shipping_cost = Decimal('0.00')  # Implement shipping calculation logic
        tax_amount = Decimal('0.00')     # Implement tax calculation logic
        discount_amount = Decimal('0.00')
        coupon_discount = Decimal('0.00')
        
        # Apply coupon if provided
        coupon = getattr(self, 'coupon', None)
        if coupon:
            is_valid, message = coupon.is_valid(user, subtotal)
            if is_valid:
                coupon_discount = coupon.calculate_discount(subtotal)
            else:
                raise serializers.ValidationError(f"Coupon error: {message}")
        
        total_amount = subtotal + shipping_cost + tax_amount - discount_amount - coupon_discount
        
        # Create order
        order = Order.objects.create(
            user=user,
            status='pending',
            payment_status='pending',  # Will be set to 'cod_confirmed' for COD
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            coupon_code=coupon.code if coupon else '',
            coupon_discount=coupon_discount,
            total_amount=total_amount,
            customer_email=user.email,
            customer_phone=user.phone,
            customer_notes=validated_data.get('customer_notes', '')
        )
        
        # Create shipping address
        ShippingAddress.objects.create(order=order, **shipping_data)
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )
            
            # Update product stock
            if cart_item.variant:
                cart_item.variant.stock_quantity -= cart_item.quantity
                cart_item.variant.save()
            elif cart_item.product.track_inventory:
                cart_item.product.stock_quantity -= cart_item.quantity
                cart_item.product.save()
        
        # Record coupon usage
        if coupon:
            CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                order_id=order.order_number
            )
            coupon.used_count += 1
            coupon.save()
        
        # For COD orders, mark as confirmed
        order.payment_status = 'cod_confirmed'
        order.status = 'confirmed'
        order.confirmed_at = timezone.now()
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status='pending',
            new_status='confirmed',
            notes='COD order confirmed automatically'
        )
        
        # Clear cart
        cart.clear()
        
        return order


class InvoiceSerializer(serializers.ModelSerializer):
    """Invoice serializer"""
    order = OrderDetailSerializer(read_only=True)
    
    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_number', 'order', 'invoice_date',
            'billing_name', 'billing_email', 'billing_address',
            'invoice_file', 'created_at'
        )
        read_only_fields = ('id', 'invoice_number', 'invoice_date', 'created_at')


class RefundRequestSerializer(serializers.ModelSerializer):
    """Refund request serializer"""
    order = OrderListSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RefundRequest
        fields = (
            'id', 'order', 'order_id', 'refund_amount', 'reason',
            'description', 'status', 'admin_response',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'status', 'admin_response', 'created_at', 'updated_at')
    
    def validate_order_id(self, value):
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=value, user=user)
            if order.status not in ['delivered', 'shipped']:
                raise serializers.ValidationError("Refund can only be requested for delivered or shipped orders.")
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        return value
    
    def validate_refund_amount(self, value):
        order_id = self.initial_data.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if value > order.total_amount:
                    raise serializers.ValidationError("Refund amount cannot exceed order total.")
            except Order.DoesNotExist:
                pass
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderTrackingSerializer(serializers.Serializer):
    """Order tracking information serializer"""
    order_number = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    tracking_info = serializers.SerializerMethodField()
    estimated_delivery = serializers.DateTimeField(read_only=True, required=False)
    
    def get_tracking_info(self, obj):
        latest_history = obj.status_history.filter(
            tracking_number__isnull=False
        ).order_by('-created_at').first()
        
        if latest_history:
            return {
                'tracking_number': latest_history.tracking_number,
                'carrier': latest_history.carrier,
                'updated_at': latest_history.created_at
            }
        return None
