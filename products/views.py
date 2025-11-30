from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import serializers as drf_serializers
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers, vary_on_cookie
from .models import Category, Product, ProductImage, Review, ReviewImage, Wishlist
from .serializers import (
    CategorySerializer, 
    ProductListSerializer, 
    ProductDetailSerializer,
    ProductCreateUpdateSerializer, 
    ReviewSerializer,
    ReviewImageSerializer, 
    WishlistSerializer,
    ProductImageSerializer, 
    ProductSearchSerializer
)
from .filters import ProductFilter
from utils.cache_utils import get_cache_manager, cache_view


@method_decorator(cache_page(3600), name='dispatch')  # Cache for 1 hour
@method_decorator(vary_on_headers('Accept-Language'), name='dispatch')
class CategoryListView(generics.ListAPIView):
    """List all active categories"""
    queryset = Category.objects.filter(is_active=True, parent=None).prefetch_related('subcategories')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get categories with caching"""
        cache_manager = get_cache_manager()
        cache_key = cache_manager.get_cache_key('categories')
        cached_categories = cache_manager.get_page_cache(cache_key)
        
        if cached_categories is not None:
            return cached_categories
        
        queryset = super().get_queryset()
        categories = list(queryset)
        cache_manager.set_page_cache(cache_key, categories, 'category_list')
        
        return categories


@method_decorator(cache_page(1800), name='dispatch')  # Cache for 30 minutes
class CategoryDetailView(generics.RetrieveAPIView):
    """Category detail with products"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def retrieve(self, request, *args, **kwargs):
        """Get category with caching"""
        cache_manager = get_cache_manager()
        slug = kwargs.get('slug')
        cache_key = f'category_detail_{slug}'
        
        cached_category = cache_manager.get_page_cache(cache_key)
        if cached_category is not None:
            return Response(cached_category)
        
        response = super().retrieve(request, *args, **kwargs)
        cache_manager.set_page_cache(cache_key, response.data, 'category_list')
        
        return response


class ProductListView(generics.ListAPIView):
    """List products with filtering, searching, and pagination"""
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'reviews')
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'short_description', 'category__name']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category_slug = self.request.query_params.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            # Include subcategory products
            category_ids = [category.id] + list(category.subcategories.filter(is_active=True).values_list('id', flat=True))
            queryset = queryset.filter(category_id__in=category_ids)
        
        # Filter featured products
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filter by stock availability
        if self.request.query_params.get('in_stock') == 'true':
            queryset = queryset.filter(
                Q(track_inventory=False) | Q(track_inventory=True, stock_quantity__gt=0)
            )
        
        # Filter by minimum rating
        min_rating = self.request.query_params.get('rating')
        if min_rating:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=min_rating)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List products with caching for common queries"""
        cache_manager = get_cache_manager()
        
        # Generate cache key based on query parameters
        query_params = dict(request.GET)
        cache_key = f"product_list_{hash(str(sorted(query_params.items())))}"
        
        # Check if it's a simple query that can be cached
        cacheable_params = ['category', 'featured', 'in_stock', 'page']
        is_cacheable = not any(param not in cacheable_params for param in query_params.keys())
        
        if is_cacheable:
            cached_response = cache_manager.get_product_cache(cache_key)
            if cached_response is not None:
                return Response(cached_response)
        
        response = super().list(request, *args, **kwargs)
        
        # Cache the response if it's cacheable
        if is_cacheable and response.status_code == 200:
            timeout = cache_manager.get_timeout('product_list')
            cache_manager.set_product_cache(cache_key, response.data, timeout)
        
        return response


@method_decorator(cache_page(1800), name='dispatch')  # Cache for 30 minutes
class ProductDetailView(generics.RetrieveAPIView):
    """Product detail view"""
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        'images', 'variants', 'reviews__user'
    )
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def retrieve(self, request, *args, **kwargs):
        """Get product with caching"""
        cache_manager = get_cache_manager()
        slug = kwargs.get('slug')
        cache_key = f'product_detail_{slug}'
        
        cached_product = cache_manager.get_product_cache(cache_key)
        if cached_product is not None:
            return Response(cached_product)
        
        response = super().retrieve(request, *args, **kwargs)
        
        if response.status_code == 200:
            timeout = cache_manager.get_timeout('product_detail')
            cache_manager.set_product_cache(cache_key, response.data, timeout)
            
            # Increment view count (don't cache this)
            product = self.get_object()
            Product.objects.filter(id=product.id).update(
                view_count=product.view_count + 1
            )
        
        return response


class ProductCreateView(generics.CreateAPIView):
    """Create product (admin only)"""
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductUpdateView(generics.UpdateAPIView):
    """Update product (admin only)"""
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAdminUser]


class FeaturedProductsView(generics.ListAPIView):
    """List featured products"""
    queryset = Product.objects.filter(is_active=True, is_featured=True).select_related('category').prefetch_related('images')
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]


class RelatedProductsView(generics.ListAPIView):
    """Get products related to a specific product"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        product_id = self.kwargs['pk']
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get related products from same category, excluding current product
        return Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product_id).select_related('category').prefetch_related('images')[:6]


class ReviewListCreateView(generics.ListCreateAPIView):
    """List and create product reviews"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]  # Allow guest reviews
    
    def get_queryset(self):
        product_id = self.kwargs['product_pk']
        return Review.objects.filter(
            product_id=product_id,
            is_approved=True
        ).select_related('user').prefetch_related('images').order_by('-created_at')
    
    def perform_create(self, serializer):
        product_id = self.kwargs['product_pk']
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # For authenticated users, check if they already reviewed this product
        if self.request.user.is_authenticated:
            if Review.objects.filter(user=self.request.user, product=product).exists():
                raise drf_serializers.ValidationError("You have already reviewed this product.")
            
            # Check if user has purchased this product (optional verification)
            from orders.models import OrderItem
            has_purchased = OrderItem.objects.filter(
                order__user=self.request.user,
                product=product,
                order__status='delivered'
            ).exists()
            
            serializer.save(product=product, is_verified_purchase=has_purchased)
        else:
            # For guest users, save without verified purchase status
            serializer.save(product=product)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete review"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class WishlistView(generics.ListCreateAPIView):
    """List and add items to wishlist"""
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')


class WishlistItemView(generics.DestroyAPIView):
    """Remove item from wishlist"""
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_wishlist(request, product_id):
    """Toggle product in wishlist"""
    # Debug info
    import logging
    logger = logging.getLogger('django')
    logger.info(f"Wishlist toggle request received for product ID: {product_id}")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"Request data: {request.data}")
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    # Get wishlist count for the user
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    logger.info(f"Wishlist count: {wishlist_count}, Item created: {created}")
    
    if not created:
        wishlist_item.delete()
        return Response({
            'message': 'Product removed from wishlist',
            'in_wishlist': False,
            'wishlist_count': wishlist_count - 1  # Subtract 1 since we just deleted it
        })
    else:
        return Response({
            'message': 'Product added to wishlist',
            'in_wishlist': True,
            'wishlist_count': wishlist_count
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_search(request):
    """Advanced product search with filters"""
    serializer = ProductSearchSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    
    # Text search
    search_query = serializer.validated_data.get('q')
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Category filter
    category_slug = serializer.validated_data.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        category_ids = [category.id] + list(category.subcategories.filter(is_active=True).values_list('id', flat=True))
        queryset = queryset.filter(category_id__in=category_ids)
    
    # Price range filter
    min_price = serializer.validated_data.get('min_price')
    max_price = serializer.validated_data.get('max_price')
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)
    
    # Stock filter
    if serializer.validated_data.get('in_stock'):
        queryset = queryset.filter(
            Q(track_inventory=False) | Q(track_inventory=True, stock_quantity__gt=0)
        )
    
    # Featured filter
    if serializer.validated_data.get('featured'):
        queryset = queryset.filter(is_featured=True)
    
    # Rating filter
    min_rating = serializer.validated_data.get('rating')
    if min_rating:
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__gte=min_rating)
    
    # Ordering
    ordering = serializer.validated_data.get('ordering', '-created_at')
    if ordering == 'rating':
        queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif ordering == '-rating':
        queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('avg_rating')
    else:
        queryset = queryset.order_by(ordering)
    
    # Paginate results
    paginator = generics.pagination.PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = ProductListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = ProductListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def category_products(request, category_slug):
    """Get products for a specific category"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    # Include subcategory products
    category_ids = [category.id] + list(category.subcategories.filter(is_active=True).values_list('id', flat=True))
    
    products = Product.objects.filter(
        category_id__in=category_ids,
        is_active=True
    ).select_related('category').prefetch_related('images')
    
    # Apply filters similar to ProductListView
    # ... (implement additional filtering as needed)
    
    # Paginate results
    paginator = generics.pagination.PageNumberPagination()
    page = paginator.paginate_queryset(products, request)
    
    if page is not None:
        serializer = ProductListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = ProductListSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)
