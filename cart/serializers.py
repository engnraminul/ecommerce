from rest_framework import serializers
from .models import Cart, CartItem, SavedItem, Coupon
from products.serializers import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer"""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    total_price = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    
    # Flattened fields for easier frontend access
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_image = serializers.SerializerMethodField()
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)
    variant_color = serializers.CharField(source='variant.color', read_only=True)
    variant_size = serializers.CharField(source='variant.size', read_only=True)
    
    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'variant', 'product_id', 'variant_id',
            'quantity', 'unit_price', 'total_price', 'is_available',
            'product_name', 'product_sku', 'product_image',
            'variant_name', 'variant_sku', 'variant_color', 'variant_size',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'unit_price', 'created_at', 'updated_at')
    
    def get_product_image(self, obj):
        """Get product primary image URL"""
        if obj.variant and obj.variant.image_url:
            # For URL-based variant images, use image_url property
            return obj.variant.image_url
        elif obj.product:
            primary_image = obj.product.images.filter(is_primary=True).first()
            if primary_image:
                return primary_image.image_url
            elif obj.product.images.exists():
                return obj.product.images.first().image_url
        return None
    
    def validate_product_id(self, value):
        from products.models import Product
        try:
            product = Product.objects.get(id=value, is_active=True)
            if not product.is_in_stock and product.track_inventory:
                raise serializers.ValidationError("Product is out of stock.")
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value
    
    def validate_variant_id(self, value):
        if value is not None:
            from products.models import ProductVariant
            try:
                variant = ProductVariant.objects.get(id=value, is_active=True)
                if variant.stock_quantity <= 0:
                    raise serializers.ValidationError("Product variant is out of stock.")
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found or inactive.")
        return value
    
    def validate(self, attrs):
        quantity = attrs.get('quantity', 1)
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')
        
        # Check stock availability
        if variant_id:
            from products.models import ProductVariant
            variant = ProductVariant.objects.get(id=variant_id)
            if variant.stock_quantity < quantity:
                raise serializers.ValidationError(f"Only {variant.stock_quantity} items available in stock.")
        else:
            from products.models import Product
            product = Product.objects.get(id=product_id)
            if product.track_inventory and product.stock_quantity < quantity:
                raise serializers.ValidationError(f"Only {product.stock_quantity} items available in stock.")
        
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Cart serializer"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    total_weight = serializers.ReadOnlyField()
    shipping_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = (
            'id', 'items', 'total_items', 'subtotal', 'total_weight',
            'shipping_summary', 'created_at', 'updated_at'
        )
    
    def get_shipping_summary(self, obj):
        """Get shipping options for this cart"""
        from .shipping import ShippingCalculator
        
        # Get location from request context (default to Dhaka)
        request = self.context.get('request')
        location = 'dhaka'
        if request and hasattr(request, 'GET'):
            location = request.GET.get('location', 'dhaka').lower()
        
        if location not in ['dhaka', 'outside']:
            location = 'dhaka'
        
        cart_items = obj.items.select_related('product').all()
        if not cart_items:
            return None
        
        shipping_calculator = ShippingCalculator(cart_items, location)
        return shipping_calculator.get_shipping_summary()
        read_only_fields = ('id', 'created_at', 'updated_at')


class AddToCartSerializer(serializers.Serializer):
    """Add to cart serializer"""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        from products.models import Product
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value
    
    def validate_variant_id(self, value):
        if value is not None:
            from products.models import ProductVariant
            try:
                ProductVariant.objects.get(id=value, is_active=True)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found or inactive.")
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    """Update cart item quantity serializer"""
    quantity = serializers.IntegerField(min_value=1)


class SavedItemSerializer(serializers.ModelSerializer):
    """Saved item serializer"""
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    
    class Meta:
        model = SavedItem
        fields = (
            'id', 'product', 'variant', 'quantity', 'unit_price', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class CouponSerializer(serializers.ModelSerializer):
    """Coupon serializer (for public use)"""
    discount_display = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = Coupon
        fields = (
            'code', 'name', 'description', 'discount_type', 'discount_value',
            'minimum_order_amount', 'valid_from', 'valid_until',
            'discount_display', 'is_expired', 'days_until_expiry'
        )
        read_only_fields = (
            'name', 'description', 'discount_type', 'discount_value', 
            'minimum_order_amount', 'valid_from', 'valid_until'
        )


class ApplyCouponSerializer(serializers.Serializer):
    """Apply coupon serializer"""
    code = serializers.CharField()
    
    def validate_code(self, value):
        try:
            coupon = Coupon.objects.get(code=value.upper())
            self.coupon = coupon
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")
        return value.upper()


class CouponValidationSerializer(serializers.Serializer):
    """Coupon validation response serializer"""
    is_valid = serializers.BooleanField()
    message = serializers.CharField()
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    coupon = CouponSerializer(required=False)


class CartSummarySerializer(serializers.Serializer):
    """Cart summary with totals serializer"""
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax_amount = serializers.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_amount = serializers.DecimalField(max_digits=8, decimal_places=2, default=0)
    coupon_discount = serializers.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    total_items = serializers.IntegerField()
    total_weight = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
