from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem, ShippingAddress
from products.models import Product, ProductVariant


class OrderItemEditSerializer(serializers.ModelSerializer):
    """Serializer for editing order items"""
    product_id = serializers.IntegerField(write_only=True, required=False)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    product_name = serializers.CharField(read_only=True)
    variant_name = serializers.CharField(read_only=True)
    variant_sku = serializers.CharField(read_only=True, source='variant.sku')
    variant_display_name = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    product_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_id', 'variant_id', 'product_name', 'variant_name', 
            'variant_sku', 'variant_display_name', 'quantity', 'unit_price', 
            'total_price', 'product_stock'
        ]
    
    def get_variant_display_name(self, obj):
        """Get variant display name for stickers and UI"""
        if obj.variant:
            return obj.variant.sku or obj.variant.name or f"{obj.product_name} - {obj.variant_name}"
        return obj.product_name
    
    def get_product_stock(self, obj):
        """Get current stock quantity"""
        if obj.variant:
            return obj.variant.stock_quantity
        return obj.product.stock_quantity if hasattr(obj.product, 'stock_quantity') else 0


class ShippingAddressEditSerializer(serializers.ModelSerializer):
    """Serializer for editing shipping address"""
    
    class Meta:
        model = ShippingAddress
        fields = [
            'first_name', 'last_name', 'company', 'address_line_1', 
            'address_line_2', 'city', 'state', 'postal_code', 
            'country', 'phone', 'email', 'delivery_instructions'
        ]


class OrderEditSerializer(serializers.ModelSerializer):
    """Serializer for editing basic order information"""
    items = OrderItemEditSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressEditSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 
            'customer_email', 'customer_phone', 'customer_notes',
            'shipping_cost', 'tax_amount', 'discount_amount',
            'subtotal', 'total_amount', 'items', 'shipping_address'
        ]


class OrderItemQuantityUpdateSerializer(serializers.Serializer):
    """Serializer for updating order item quantity"""
    item_id = serializers.IntegerField()
    new_quantity = serializers.IntegerField(min_value=1)
    
    def validate_new_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class OrderItemAddSerializer(serializers.Serializer):
    """Serializer for adding new items to order"""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    
    def validate(self, data):
        # Validate product exists
        try:
            product = Product.objects.get(id=data['product_id'])
            data['product'] = product
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        
        # Validate variant if provided
        if data.get('variant_id'):
            try:
                variant = ProductVariant.objects.get(
                    id=data['variant_id'], 
                    product=product
                )
                data['variant'] = variant
                
                # Check stock
                if variant.stock_quantity < data['quantity']:
                    raise serializers.ValidationError(
                        f"Insufficient stock. Available: {variant.stock_quantity}"
                    )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found")
        else:
            # Check product stock if no variant
            if hasattr(product, 'stock_quantity') and product.stock_quantity < data['quantity']:
                raise serializers.ValidationError(
                    f"Insufficient stock. Available: {product.stock_quantity}"
                )
        
        return data


class OrderItemDeleteSerializer(serializers.Serializer):
    """Serializer for deleting order items"""
    item_id = serializers.IntegerField()
    
    def validate_item_id(self, value):
        try:
            item = OrderItem.objects.get(id=value)
            self.item = item
            return value
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError("Order item not found")