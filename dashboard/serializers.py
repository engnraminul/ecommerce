from rest_framework import serializers
from .models import DashboardSetting, AdminActivity, Expense
from products.models import Product, ProductVariant, ProductImage, Category
from orders.models import Order, OrderItem, ShippingAddress
from users.models import User

class DashboardSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardSetting
        fields = '__all__'

class AdminActivitySerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = AdminActivity
        fields = ['id', 'user', 'user_username', 'action', 'model_name', 'object_id', 
                  'object_repr', 'changes', 'ip_address', 'timestamp']
        read_only_fields = fields

class UserDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 
                  'is_active', 'date_joined', 'last_login']

class CategoryDashboardSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.count()

class ProductDashboardSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    variant_count = serializers.SerializerMethodField()
    base_price = serializers.ReadOnlyField(source='price')  # Map 'base_price' to 'price'
    variants = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description', 'category', 'category_name', 
            'sku', 'barcode', 'price', 'base_price', 'compare_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold', 'track_inventory',
            'is_active', 'is_featured', 'is_digital',
            'weight', 'dimensions', 'shipping_type', 'has_express_shipping',
            'custom_shipping_dhaka', 'custom_shipping_outside', 'custom_express_shipping',
            'meta_title', 'meta_description', 'youtube_video_url',
            'created_at', 'updated_at', 'variant_count', 'variants', 'image_url'
        ]
    
    def get_variant_count(self, obj):
        return obj.variants.count()
    
    def get_variants(self, obj):
        variants = obj.variants.all()
        return [{
            'id': variant.id,
            'name': variant.name or 'Default',
            'size': variant.size,
            'color': variant.color,
            'price': float(variant.price) if variant.price else float(obj.price or 0),
            'cost_price': float(variant.cost_price) if variant.cost_price else float(obj.cost_price or 0),
            'stock_quantity': variant.stock_quantity or 0,
            'is_active': variant.is_active,
            'image_url': variant.image.url if variant.image else None
        } for variant in variants]
    
    def get_image_url(self, obj):
        # Try to get the first image from productimage_set
        if hasattr(obj, 'productimage_set') and obj.productimage_set.exists():
            first_image = obj.productimage_set.first()
            if first_image and first_image.image:
                return first_image.image.url
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for creating and updating products"""
    category_name = serializers.ReadOnlyField(source='category.name')
    variant_count = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description', 'category', 'category_name',
            'sku', 'barcode', 'price', 'compare_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold', 'track_inventory',
            'is_active', 'is_featured', 'is_digital',
            'weight', 'dimensions', 'shipping_type', 'has_express_shipping',
            'custom_shipping_dhaka', 'custom_shipping_outside', 'custom_express_shipping',
            'meta_title', 'meta_description', 'youtube_video_url',
            'created_at', 'updated_at', 'variant_count', 'variants', 'image_url'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_variant_count(self, obj):
        return obj.variants.count()
    
    def get_variants(self, obj):
        from orders.models import OrderItem
        from django.db.models import Sum
        
        variants = obj.variants.all()
        variants_data = []
        
        for variant in variants:
            # Calculate sales count for this variant
            sales_count = OrderItem.objects.filter(
                variant=variant,
                order__status__in=['delivered', 'shipped']
            ).aggregate(
                total_sold=Sum('quantity')
            )['total_sold'] or 0
            
            variants_data.append({
                'id': variant.id,
                'name': variant.name or 'Default',
                'size': variant.size,
                'color': variant.color,
                'price': float(variant.price) if variant.price else float(obj.price or 0),
                'cost_price': float(variant.cost_price) if variant.cost_price else float(obj.cost_price or 0),
                'stock_quantity': variant.stock_quantity or 0,
                'sales_count': sales_count,
                'is_active': variant.is_active,
                'image_url': variant.image.url if variant.image else None
            })
        
        return variants_data
    
    def get_image_url(self, obj):
        # Try to get the first image from productimage_set
        if hasattr(obj, 'productimage_set') and obj.productimage_set.exists():
            first_image = obj.productimage_set.first()
            if first_image and first_image.image:
                return first_image.image.url
        return None
    
    def validate_slug(self, value):
        """Ensure slug uniqueness"""
        if self.instance:
            # Editing existing product
            if Product.objects.filter(slug=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A product with this slug already exists.")
        else:
            # Creating new product
            if Product.objects.filter(slug=value).exists():
                raise serializers.ValidationError("A product with this slug already exists.")
        return value
    
    def validate_sku(self, value):
        """Ensure SKU uniqueness"""
        if self.instance:
            # Editing existing product
            if Product.objects.filter(sku=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A product with this SKU already exists.")
        else:
            # Creating new product
            if Product.objects.filter(sku=value).exists():
                raise serializers.ValidationError("A product with this SKU already exists.")
        return value

class ProductVariantDashboardSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    effective_price = serializers.ReadOnlyField()
    effective_compare_price = serializers.ReadOnlyField()
    effective_cost_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'product_name', 'sku', 'name', 'color', 'size', 'material', 
                 'price', 'compare_price', 'cost_price', 'stock_quantity', 'is_active', 'image',
                 'effective_price', 'effective_compare_price', 'effective_cost_price', 
                 'discount_percentage', 'profit_margin']

class ProductImageDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt_text', 'is_primary', 'created_at']
        read_only_fields = ['created_at']
    
    def validate(self, data):
        # Handle primary image logic
        if 'is_primary' in data:
            product = data.get('product') or (self.instance.product if self.instance else None)
            if product:
                if data.get('is_primary', False):
                    # Setting as primary - ensure only one primary image per product
                    if self.instance:
                        # Editing existing image
                        ProductImage.objects.filter(
                            product=product, is_primary=True
                        ).exclude(id=self.instance.id).update(is_primary=False)
                    else:
                        # Creating new image
                        ProductImage.objects.filter(
                            product=product, is_primary=True
                        ).update(is_primary=False)
                # If setting to False, no additional logic needed - just update this image
        return data

class ShippingAddressDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['first_name', 'last_name', 'company', 'address_line_1', 'address_line_2',
                 'city', 'state', 'postal_code', 'country', 'phone', 'email', 'delivery_instructions']

class OrderDashboardSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    shipping_address = ShippingAddressDashboardSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_name', 'user_email', 'order_number', 'status', 'total_amount',
                  'payment_status', 'shipping_address', 'created_at', 'updated_at', 'total_items',
                  'instructions', 'customer_email', 'customer_phone', 'customer_notes', 'shipping_cost', 
                  'tax_amount', 'curier_id', 'curier_status', 'curier_charge']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Guest User"
    
    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return obj.customer_email or obj.guest_email or "N/A"
    
    def get_instructions(self, obj):
        return obj.customer_notes
        
    def get_total_items(self, obj):
        return obj.items.count()

class OrderItemDashboardSerializer(serializers.ModelSerializer):
    """Serializer for order items in the dashboard"""
    variant_sku = serializers.SerializerMethodField()
    variant_display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product_name', 'variant_name', 'variant_sku', 'variant_display_name', 'quantity', 'unit_price']
    
    def get_variant_sku(self, obj):
        """Get the full variant SKU"""
        if obj.variant:
            return obj.variant.sku or f"{obj.product_sku}-{obj.variant.name}"
        return obj.product_sku
    
    def get_variant_display_name(self, obj):
        """Get the full variant display name (SKU or full name)"""
        if obj.variant:
            # If variant has a proper SKU, use it; otherwise use the full variant name
            if obj.variant.sku:
                return obj.variant.sku
            else:
                return obj.variant.name  # This should be "MW02 Black"
        return obj.product_name
        
    def to_representation(self, instance):
        """Override to customize response data"""
        data = super().to_representation(instance)
        # Add calculated field
        data['price'] = str(instance.unit_price)
        data['total_price'] = str(instance.unit_price * instance.quantity)
        return data

class DashboardStatisticsSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    orders_count = serializers.IntegerField()
    total_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    dashboard_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    courier_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_product_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2)
    products_count = serializers.IntegerField()
    customers_count = serializers.IntegerField()
    recent_orders = OrderDashboardSerializer(many=True)
    popular_products = serializers.ListSerializer(child=serializers.DictField())
    sales_by_period = serializers.ListSerializer(child=serializers.DictField())
    sales_by_category = serializers.ListSerializer(child=serializers.DictField())
    orders_by_status = serializers.ListSerializer(child=serializers.DictField())
    analytics = serializers.DictField()
    recommendations = serializers.ListSerializer(child=serializers.DictField())

class ExpenseDashboardSerializer(serializers.ModelSerializer):
    expense_type_display = serializers.CharField(source='get_expense_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'expense_type', 'expense_type_display', 'amount', 'description', 
                 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)