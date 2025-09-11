from rest_framework import serializers
from .models import DashboardSetting, AdminActivity
from products.models import Product, ProductVariant, Category
from orders.models import Order, OrderItem
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
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'category_name', 
                  'base_price', 'is_active', 'created_at', 'updated_at', 'variant_count']
    
    def get_variant_count(self, obj):
        return obj.variants.count()

class ProductVariantDashboardSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'product_name', 'sku', 'name', 'price', 
                 'stock_quantity', 'is_active', 'image']

class OrderDashboardSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_name', 'order_number', 'status', 'total_amount',
                  'payment_status', 'shipping_address', 'created_at', 'updated_at', 'total_items']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Guest User"
    
    def get_total_items(self, obj):
        return obj.items.count()

class OrderItemDashboardSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product_variant', 'product_name', 'variant_name',
                  'quantity', 'price', 'total_price']
    
    def get_product_name(self, obj):
        if obj.product_variant and obj.product_variant.product:
            return obj.product_variant.product.name
        return "Unknown Product"
    
    def get_variant_name(self, obj):
        if obj.product_variant:
            return obj.product_variant.name
        return "Unknown Variant"

class DashboardStatisticsSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    orders_count = serializers.IntegerField()
    products_count = serializers.IntegerField()
    customers_count = serializers.IntegerField()
    recent_orders = OrderDashboardSerializer(many=True)
    popular_products = serializers.ListSerializer(child=serializers.DictField())
    sales_by_period = serializers.ListSerializer(child=serializers.DictField())