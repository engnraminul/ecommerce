from rest_framework import serializers
from .models import Order, OrderItem, ShippingAddress, OrderStatusHistory, Invoice, RefundRequest
from products.serializers import ProductListSerializer, ProductVariantSerializer
from users.serializers import AddressSerializer
from .phone_utils import validate_bangladeshi_phone


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
    
    def validate_phone(self, phone):
        """Validate shipping address phone number"""
        if phone:
            validation_result = validate_bangladeshi_phone(phone)
            if not validation_result['is_valid']:
                raise serializers.ValidationError(validation_result['error'])
            return validation_result['normalized']
        return phone


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
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = (
            'id', 'status', 'status_display', 'title', 'description',
            'changed_by', 'is_system_generated', 'tracking_number', 
            'carrier', 'carrier_url', 'location', 'estimated_delivery',
            'is_milestone', 'is_customer_visible', 'created_at'
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
            'customer_email', 'customer_phone', 'customer_ip', 'customer_notes',
            'can_cancel', 'is_cod_order', 'items', 'shipping_address',
            'status_history', 'created_at', 'updated_at', 'confirmed_at',
            'shipped_at', 'delivered_at'
        )
        read_only_fields = ('id', 'order_number', 'created_at', 'updated_at')


class CreateOrderSerializer(serializers.Serializer):
    """Create order serializer - supports both authenticated users and guests"""
    shipping_address = ShippingAddressSerializer()
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    shipping_option = serializers.CharField(required=False, allow_blank=True)
    shipping_location = serializers.CharField(required=False, allow_blank=True)
    
    # Guest order fields
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    
    # Payment method fields
    payment_method = serializers.ChoiceField(
        choices=[('cod', 'Cash on Delivery'), ('bkash', 'bKash'), ('nagad', 'Nagad')],
        default='cod'
    )
    payment_method_display_name = serializers.CharField(required=False, allow_blank=True)
    
    # Mobile wallet payment details
    bkash_transaction_id = serializers.CharField(required=False, allow_blank=True)
    bkash_sender_number = serializers.CharField(required=False, allow_blank=True)
    nagad_transaction_id = serializers.CharField(required=False, allow_blank=True)
    nagad_sender_number = serializers.CharField(required=False, allow_blank=True)
    
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
    
    def validate(self, data):
        """Validate payment method data and phone numbers"""
        payment_method = data.get('payment_method', 'cod')
        
        # Validate phone numbers
        if data.get('guest_phone'):
            phone_validation = validate_bangladeshi_phone(data['guest_phone'])
            if not phone_validation['is_valid']:
                raise serializers.ValidationError({
                    'guest_phone': phone_validation['error']
                })
            data['guest_phone'] = phone_validation['normalized']
        
        # Validate bKash payment data
        if payment_method == 'bkash':
            if not data.get('bkash_transaction_id'):
                raise serializers.ValidationError({
                    'bkash_transaction_id': 'bKash transaction ID is required for bKash payment.'
                })
            if not data.get('bkash_sender_number'):
                raise serializers.ValidationError({
                    'bkash_sender_number': 'Sender mobile number is required for bKash payment.'
                })
            else:
                # Validate bKash sender number
                phone_validation = validate_bangladeshi_phone(data['bkash_sender_number'])
                if not phone_validation['is_valid']:
                    raise serializers.ValidationError({
                        'bkash_sender_number': phone_validation['error']
                    })
                data['bkash_sender_number'] = phone_validation['normalized']
        
        # Validate Nagad payment data
        if payment_method == 'nagad':
            if not data.get('nagad_transaction_id'):
                raise serializers.ValidationError({
                    'nagad_transaction_id': 'Nagad transaction ID is required for Nagad payment.'
                })
            if not data.get('nagad_sender_number'):
                raise serializers.ValidationError({
                    'nagad_sender_number': 'Sender mobile number is required for Nagad payment.'
                })
            else:
                # Validate Nagad sender number
                phone_validation = validate_bangladeshi_phone(data['nagad_sender_number'])
                if not phone_validation['is_valid']:
                    raise serializers.ValidationError({
                        'nagad_sender_number': phone_validation['error']
                    })
                data['nagad_sender_number'] = phone_validation['normalized']
        
        return data
    
    def create(self, validated_data):
        from cart.models import Cart, CouponUsage
        from cart.shipping import ShippingCalculator
        from django.utils import timezone
        from decimal import Decimal
        from .utils import get_client_ip
        import logging
        
        logger = logging.getLogger(__name__)
        request = self.context['request']
        user = request.user if request.user.is_authenticated else None
        shipping_data = validated_data.pop('shipping_address')
        shipping_option = validated_data.get('shipping_option', '')
        shipping_location = validated_data.get('shipping_location', 'dhaka')
        guest_email = validated_data.get('guest_email', '')
        guest_phone = validated_data.get('guest_phone', '')
        
        # Get customer IP address (uses FORCE_PUBLIC_IP_DETECTION setting)
        customer_ip = get_client_ip(request)
        
        logger.info(f"Creating order for user: {user} (guest: {not bool(user)})")
        logger.info(f"Customer IP: {customer_ip}")
        logger.info(f"Shipping data: {shipping_data}")
        logger.info(f"Shipping option: {shipping_option}")
        logger.info(f"Shipping location: {shipping_location}")
        
        # Get cart - either user's cart or session cart for guests
        if user:
            try:
                cart = Cart.objects.get(user=user)
                logger.info(f"Found user cart with {cart.items.count()} items")
            except Cart.DoesNotExist:
                logger.error("Cart not found for authenticated user")
                raise serializers.ValidationError("Cart is empty.")
        else:
            # For guest users, get cart by session
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            
            try:
                cart = Cart.objects.get(session_id=session_id, user=None)
                logger.info(f"Found guest cart with {cart.items.count()} items")
            except Cart.DoesNotExist:
                logger.error("Cart not found for guest user")
                raise serializers.ValidationError("Cart is empty. Please add items to your cart first.")
        
        if not cart.items.exists():
            logger.error("Cart has no items")
            raise serializers.ValidationError("Cart is empty.")
        
        # Get cart items
        cart_items = cart.items.all()
        
        # Calculate shipping cost
        shipping_cost = Decimal('0.00')
        
        if shipping_option and cart_items:
            # Calculate shipping cost based on selected option
            for cart_item in cart_items:
                product = cart_item.product
                item_shipping_options = product.get_available_shipping_options(shipping_location)
                
                # Find the selected shipping option
                selected_option = None
                for option in item_shipping_options:
                    if option['type'] == shipping_option:
                        selected_option = option
                        break
                
                if selected_option:
                    # Add shipping cost (only once for the entire order, not per item)
                    if shipping_cost == 0:  # Only add shipping cost once
                        shipping_cost = Decimal(str(selected_option['cost']))
                    break
        
        logger.info(f"Calculated shipping cost: {shipping_cost}")
        
        # Calculate totals
        subtotal = cart.subtotal
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
        
        # Determine customer email and phone
        if user:
            customer_email = user.email
            customer_phone = getattr(user, 'phone', '') or guest_phone
        else:
            # For guest orders, use provided email/phone or extract from shipping address
            customer_email = guest_email or shipping_data.get('email', '')
            customer_phone = guest_phone or shipping_data.get('phone', '')
        
        # Validate guest order requirements
        if not user and not customer_email:
            raise serializers.ValidationError("Email is required for guest orders.")
        
        # Get payment method data
        payment_method = validated_data.get('payment_method', 'cod')
        payment_method_display_name = validated_data.get('payment_method_display_name', '')
        
        # Set payment status based on payment method
        if payment_method == 'cod':
            payment_status = 'cod_confirmed'
            if not payment_method_display_name:
                payment_method_display_name = 'Cash on Delivery'
        else:
            payment_status = 'pending'  # For mobile wallets, require manual confirmation
            if payment_method == 'bkash' and not payment_method_display_name:
                payment_method_display_name = 'bKash'
            elif payment_method == 'nagad' and not payment_method_display_name:
                payment_method_display_name = 'Nagad'
        
        # Create order
        order = Order.objects.create(
            user=user,
            is_guest_order=not bool(user),
            guest_email=customer_email if not user else '',
            session_id=request.session.session_key if not user else '',
            status='pending',
            payment_status=payment_status,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            coupon=coupon,  # Add coupon foreign key
            coupon_code=coupon.code if coupon else '',
            coupon_discount=coupon_discount,
            total_amount=total_amount,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_ip=customer_ip,
            customer_notes=validated_data.get('customer_notes', ''),
            # Payment method data
            payment_method=payment_method,
            payment_method_display_name=payment_method_display_name,
            bkash_transaction_id=validated_data.get('bkash_transaction_id', ''),
            bkash_sender_number=validated_data.get('bkash_sender_number', ''),
            nagad_transaction_id=validated_data.get('nagad_transaction_id', ''),
            nagad_sender_number=validated_data.get('nagad_sender_number', ''),
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
            usage_data = {
                'coupon': coupon,
                'user': user,
                'order_id': order.order_number
            }
            
            # For guest users, also store email and phone for tracking
            if not user:
                usage_data['guest_email'] = customer_email
                usage_data['guest_phone'] = customer_phone
            
            CouponUsage.objects.create(**usage_data)
            coupon.used_count += 1
            coupon.save()
        
        # For COD orders, mark as confirmed
        order.payment_status = 'cod_confirmed'
        order.status = 'pending'
        order.confirmed_at = timezone.now()
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status='pending',
            new_status='Processing',
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


class OrderTrackingSerializer(serializers.ModelSerializer):
    """Order tracking information serializer"""
    items = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()
    can_cancel = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'created_at', 'status',
            'items', 'status_history', 'can_cancel',
            'subtotal', 'shipping_cost', 'tax_amount',
            'total_amount'
        )
    
    def get_items(self, obj):
        return [{
            'product': {
                'name': item.product.name,
                'image_url': self.get_product_image_url(item.product)
            },
            'variant': {
                'color': item.variant.color if item.variant else None,
                'size': item.variant.size if item.variant else None
            } if item.variant else None,
            'quantity': item.quantity,
            'total_price': float(item.total_price)
        } for item in obj.items.all()]
    
    def get_product_image_url(self, product):
        """Get product image URL safely"""
        if product.images.exists():
            first_image = product.images.first()
            if hasattr(first_image, 'image') and hasattr(first_image.image, 'url'):
                try:
                    return first_image.image.url
                except (ValueError, AttributeError):
                    pass
        return None
    
    def get_status_history(self, obj):
        # Get all visible status history entries
        history_entries = obj.status_history.filter(is_customer_visible=True).order_by('-created_at')
        
        return [{
            'status': entry.status,
            'status_display': entry.get_status_display(),
            'title': entry.title,
            'description': entry.description,
            'tracking_number': entry.tracking_number,
            'carrier': entry.carrier,
            'carrier_url': entry.carrier_url,
            'location': entry.location,
            'estimated_delivery': entry.estimated_delivery,
            'is_milestone': entry.is_milestone,
            'is_system_generated': entry.is_system_generated,
            'changed_by': str(entry.changed_by) if entry.changed_by else 'System',
            'created_at': entry.created_at,
            'is_current': entry == history_entries.first(),
        } for entry in history_entries]
