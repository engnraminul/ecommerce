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
    images = serializers.SerializerMethodField()
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
            'created_at', 'updated_at', 'variant_count', 'variants', 'images', 'image_url'
        ]
    
    def get_images(self, obj):
        """Get all images for this product"""
        images = obj.images.all()
        return ProductImageDashboardSerializer(images, many=True).data
    
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
    images = serializers.SerializerMethodField()
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
            'created_at', 'updated_at', 'variant_count', 'variants', 'images', 'image_url'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_images(self, obj):
        """Get all images for this product"""
        images = obj.images.all()
        return ProductImageDashboardSerializer(images, many=True).data
    
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
    # Add optional fields for media library support
    image_url_input = serializers.CharField(required=False, write_only=True)
    filename = serializers.CharField(required=False, write_only=True)
    uploaded_image = serializers.ImageField(required=False, write_only=True)
    
    # Add read-only field for the image_url property
    image_url = serializers.ReadOnlyField()
    
    # Add computed field for consistent image access
    image_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt_text', 'is_primary', 'created_at', 'image_url', 'image_url_input', 'filename', 'uploaded_image', 'image_display']
        read_only_fields = ['created_at', 'image_url']
        extra_kwargs = {
            'image': {'required': False}  # Make image optional since we'll set it programmatically
        }
    
    def get_image_display(self, obj):
        """Return the proper image URL for display"""
        return obj.image_url
    
    def validate(self, data):
        # Only require image source when creating a new image
        if not self.instance:  # Creating new image
            if not data.get('uploaded_image') and not data.get('image_url_input'):
                raise serializers.ValidationError("Either 'uploaded_image' file or 'image_url_input' must be provided.")
        
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
    
    def create(self, validated_data):
        # Handle different image sources
        image_url_input = validated_data.pop('image_url_input', None)
        filename = validated_data.pop('filename', None)
        uploaded_image = validated_data.pop('uploaded_image', None)
        
        if image_url_input:
            # Media library image - store the URL directly
            validated_data['image'] = image_url_input
        elif uploaded_image:
            # File upload - save the file and store the path
            from django.core.files.storage import default_storage
            import uuid
            import os
            
            # Generate unique filename
            file_extension = os.path.splitext(uploaded_image.name)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = f"products/{unique_filename}"
            
            # Save the file
            saved_path = default_storage.save(file_path, uploaded_image)
            validated_data['image'] = f"/media/{saved_path}"
        
        return super().create(validated_data)

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
                  'tax_amount', 'curier_id', 'curier_status', 'curier_charge', 'curier_date']
    
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


class StockManagementSerializer(serializers.ModelSerializer):
    """
    Serializer for intelligent stock management of products and variants.
    If product has variants, work with variant stock/cost, else use product stock/cost.
    """
    category_name = serializers.ReadOnlyField(source='category.name')
    variant_count = serializers.SerializerMethodField()
    has_variants = serializers.SerializerMethodField()
    effective_stock_quantity = serializers.SerializerMethodField()
    effective_cost_price = serializers.SerializerMethodField()
    total_variant_stock = serializers.SerializerMethodField()
    total_variant_value = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    stock_management_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category_name', 'stock_quantity', 
            'low_stock_threshold', 'track_inventory', 'cost_price', 'price',
            'variant_count', 'has_variants', 'effective_stock_quantity', 
            'effective_cost_price', 'total_variant_stock', 'total_variant_value',
            'is_low_stock', 'stock_status', 'stock_value', 'variants', 
            'stock_management_type', 'is_active'
        ]
        read_only_fields = ['id', 'name', 'sku', 'category_name', 'variant_count', 
                           'has_variants', 'effective_stock_quantity', 'effective_cost_price',
                           'total_variant_stock', 'total_variant_value', 'is_low_stock', 
                           'stock_status', 'stock_value', 'variants', 'stock_management_type']
    
    def get_variant_count(self, obj):
        return obj.variants.filter(is_active=True).count()
    
    def get_has_variants(self, obj):
        """Check if product has active variants"""
        return obj.variants.filter(is_active=True).exists()
    
    def get_effective_stock_quantity(self, obj):
        """
        Return appropriate stock quantity:
        - If has variants: sum of all variant stock
        - If no variants: product stock
        """
        if self.get_has_variants(obj):
            return sum(variant.stock_quantity for variant in obj.variants.filter(is_active=True))
        return obj.stock_quantity
    
    def get_effective_cost_price(self, obj):
        """
        Return appropriate cost price:
        - If has variants: weighted average cost price of variants
        - If no variants: product cost price
        """
        if self.get_has_variants(obj):
            variants = obj.variants.filter(is_active=True)
            total_cost = 0
            total_quantity = 0
            
            for variant in variants:
                variant_cost = variant.effective_cost_price
                if variant_cost and variant.stock_quantity > 0:
                    total_cost += variant_cost * variant.stock_quantity
                    total_quantity += variant.stock_quantity
            
            if total_quantity > 0:
                return total_cost / total_quantity
            
            # Fallback to average cost price if no stock
            costs = [v.effective_cost_price for v in variants if v.effective_cost_price]
            return sum(costs) / len(costs) if costs else 0
        
        return obj.cost_price or 0
    
    def get_total_variant_stock(self, obj):
        """Total stock across all variants"""
        return sum(variant.stock_quantity for variant in obj.variants.filter(is_active=True))
    
    def get_total_variant_value(self, obj):
        """Total stock value across all variants"""
        total_value = 0
        for variant in obj.variants.filter(is_active=True):
            cost_price = variant.effective_cost_price
            if cost_price:
                total_value += variant.stock_quantity * cost_price
        return float(total_value)
    
    def get_is_low_stock(self, obj):
        """
        Check if stock is low:
        - If has variants: check if any variant is low stock
        - If no variants: check product stock
        """
        if self.get_has_variants(obj):
            return any(
                variant.stock_quantity <= obj.low_stock_threshold 
                for variant in obj.variants.filter(is_active=True)
            )
        return obj.stock_quantity <= obj.low_stock_threshold
    
    def get_stock_status(self, obj):
        """
        Get stock status based on effective stock management:
        - If has variants: based on variant stock levels
        - If no variants: based on product stock
        """
        if not obj.track_inventory:
            return 'not_tracked'
        
        if self.get_has_variants(obj):
            variants = obj.variants.filter(is_active=True)
            if not variants.exists():
                return 'no_variants'
            
            total_stock = sum(v.stock_quantity for v in variants)
            if total_stock == 0:
                return 'out_of_stock'
            elif any(v.stock_quantity <= obj.low_stock_threshold for v in variants):
                return 'low_stock'
            else:
                return 'in_stock'
        else:
            if obj.stock_quantity == 0:
                return 'out_of_stock'
            elif obj.stock_quantity <= obj.low_stock_threshold:
                return 'low_stock'
            else:
                return 'in_stock'
    
    def get_stock_value(self, obj):
        """
        Calculate stock value based on cost price:
        - If has variants: sum of (variant_stock × variant_cost_price)
        - If no variants: product_stock × product_cost_price
        """
        if self.get_has_variants(obj):
            return self.get_total_variant_value(obj)
        
        cost_price = obj.cost_price
        if cost_price:
            return float(obj.stock_quantity * cost_price)
        return 0
    
    def get_stock_management_type(self, obj):
        """Indicate whether stock is managed at product or variant level"""
        return 'variant' if self.get_has_variants(obj) else 'product'
    
    def get_variants(self, obj):
        """Return variant data only if product has variants"""
        if self.get_has_variants(obj):
            return StockVariantManagementSerializer(
                obj.variants.filter(is_active=True), 
                many=True
            ).data
        return []


class StockVariantManagementSerializer(serializers.ModelSerializer):
    """Serializer for stock management of product variants"""
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    low_stock_threshold = serializers.ReadOnlyField(source='product.low_stock_threshold')
    is_low_stock = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()
    effective_cost_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'product_name', 'product_sku', 'stock_quantity',
            'low_stock_threshold', 'is_low_stock', 'stock_status', 'stock_value',
            'cost_price', 'effective_cost_price', 'price', 'size', 'color', 
            'material', 'is_active', 'in_stock'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'low_stock_threshold',
                           'is_low_stock', 'stock_status', 'stock_value', 'effective_cost_price']
    
    def get_is_low_stock(self, obj):
        return obj.stock_quantity <= obj.product.low_stock_threshold
    
    def get_stock_status(self, obj):
        if obj.stock_quantity == 0:
            return 'out_of_stock'
        elif self.get_is_low_stock(obj):
            return 'low_stock'
        else:
            return 'in_stock'
    
    def get_stock_value(self, obj):
        cost_price = obj.effective_cost_price
        if cost_price:
            return float(obj.stock_quantity * cost_price)
        return 0