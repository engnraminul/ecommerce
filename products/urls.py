from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:category_slug>/products/', views.category_products, name='category-products'),
    
    # Products
    path('', views.ProductListView.as_view(), name='product-list'),
    path('search/', views.product_search, name='product-search'),
    path('featured/', views.FeaturedProductsView.as_view(), name='featured-products'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/related/', views.RelatedProductsView.as_view(), name='related-products'),
    
    # Product management (admin)
    path('create/', views.ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    
    # Reviews
    path('<int:product_pk>/reviews/', views.ReviewListCreateView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    
    # Wishlist
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:pk>/', views.WishlistItemView.as_view(), name='wishlist-item'),
    path('<int:product_id>/toggle-wishlist/', views.toggle_wishlist, name='toggle-wishlist'),
]
