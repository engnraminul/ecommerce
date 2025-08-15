from rest_framework import serializers
from django.db.models import Avg
from .models import Category, Product, ProductImage, ProductVariant, Review, ReviewImage, Wishlist


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    product_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'image', 'parent',
            'product_count', 'subcategories', 'is_active',
            'get_absolute_url', 'created_at'
        )
        read_only_fields = ('id', 'product_count', 'subcategories', 'get_absolute_url', 'created_at')
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_subcategories(self, obj):
        subcategories = obj.subcategories.filter(is_active=True)
        return CategorySerializer(subcategories, many=True, context=self.context).data


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'created_at')
        read_only_fields = ('id', 'created_at')


class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer"""
    effective_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = (
            'id', 'name', 'sku', 'size', 'color', 'material',
            'price', 'effective_price', 'stock_quantity', 'is_default', 'is_active'
        )
        read_only_fields = ('id', 'sku', 'effective_price')


class ReviewImageSerializer(serializers.ModelSerializer):
    """Review image serializer"""
    class Meta:
        model = ReviewImage
        fields = ('id', 'image', 'caption', 'created_at')
        read_only_fields = ('id', 'created_at')


class ReviewSerializer(serializers.ModelSerializer):
    """Review serializer with image support for both authenticated and guest users"""
    reviewer_name = serializers.ReadOnlyField()
    images = ReviewImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Upload multiple images for the review"
    )
    
    class Meta:
        model = Review
        fields = (
            'id', 'rating', 'title', 'comment', 'reviewer_name',
            'guest_name', 'guest_email', 'images', 'uploaded_images',
            'is_verified_purchase', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'reviewer_name', 'is_verified_purchase', 'created_at', 'updated_at')
        extra_kwargs = {
            'guest_name': {'required': False, 'allow_blank': True},
            'guest_email': {'required': False, 'allow_blank': True},
            'title': {'required': False, 'allow_blank': True},
        }
    
    def validate(self, attrs):
        """Validate review data"""
        request = self.context.get('request')
        
        # If user is not authenticated, require guest_name
        if not (request and request.user.is_authenticated):
            if not attrs.get('guest_name'):
                raise serializers.ValidationError({
                    'guest_name': 'Name is required for guest reviews.'
                })
        
        # Validate rating
        rating = attrs.get('rating')
        if not rating or rating < 1 or rating > 5:
            raise serializers.ValidationError({
                'rating': 'Rating must be between 1 and 5.'
            })
        
        # Validate comment
        comment = attrs.get('comment', '').strip()
        if not comment:
            raise serializers.ValidationError({
                'comment': 'Comment is required.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create review with images"""
        uploaded_images = validated_data.pop('uploaded_images', [])
        
        # Set user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            # Clear guest fields for authenticated users
            validated_data.pop('guest_name', None)
            validated_data.pop('guest_email', None)
        
        review = super().create(validated_data)
        
        # Create review images
        for image in uploaded_images:
            ReviewImage.objects.create(review=review, image=image)
        
        return review


class ProductListSerializer(serializers.ModelSerializer):
    """Product list serializer (for list views)"""
    category = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'short_description', 'category',
            'price', 'compare_price', 'discount_percentage',
            'primary_image', 'is_featured', 'is_in_stock',
            'average_rating', 'review_count', 'created_at'
        )
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        elif obj.images.exists():
            return self.context['request'].build_absolute_uri(obj.images.first().image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Product detail serializer (for detail views)"""
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    default_variant = ProductVariantSerializer(read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_wishlisted = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'short_description',
            'sku', 'category', 'price', 'compare_price', 'discount_percentage',
            'stock_quantity', 'is_in_stock', 'is_low_stock', 'track_inventory',
            'weight', 'dimensions', 'is_digital', 'is_featured',
            'images', 'variants', 'default_variant', 'reviews', 'average_rating', 'review_count',
            'is_wishlisted', 'meta_title', 'meta_description', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'sku', 'created_at', 'updated_at')
    
    def get_reviews(self, obj):
        # Return only approved reviews with images, latest first
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:10]
        return ReviewSerializer(reviews, many=True, context=self.context).data
    
    def get_is_wishlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Product create/update serializer"""
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = (
            'name', 'description', 'short_description', 'category',
            'price', 'compare_price', 'cost_price', 'stock_quantity',
            'low_stock_threshold', 'track_inventory', 'weight', 'dimensions',
            'is_digital', 'is_active', 'is_featured', 'meta_title', 'meta_description',
            'images'
        )
    
    def validate(self, attrs):
        if attrs.get('compare_price') and attrs.get('price'):
            if attrs['compare_price'] <= attrs['price']:
                raise serializers.ValidationError("Compare price must be higher than the selling price.")
        return attrs


class WishlistSerializer(serializers.ModelSerializer):
    """Wishlist serializer"""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Wishlist
        fields = ('id', 'product', 'product_id', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value


class CategoryProductsSerializer(serializers.ModelSerializer):
    """Serializer for category with its products"""
    products = ProductListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'products')


# Search and Filter serializers
class ProductSearchSerializer(serializers.Serializer):
    """Product search serializer"""
    q = serializers.CharField(required=False, help_text="Search query")
    category = serializers.CharField(required=False, help_text="Category slug")
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    in_stock = serializers.BooleanField(required=False, help_text="Filter by stock availability")
    featured = serializers.BooleanField(required=False, help_text="Filter featured products")
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False, help_text="Minimum rating")
    ordering = serializers.ChoiceField(
        choices=[
            'name', '-name', 'price', '-price', 
            'created_at', '-created_at', 'rating', '-rating'
        ],
        required=False,
        help_text="Ordering field"
    )
