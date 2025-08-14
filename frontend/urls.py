from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'frontend'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('categories/', views.categories, name='categories'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('search/', views.search, name='search'),
    
    # User authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='frontend:home'), name='logout'),
    
    # User dashboard
    path('profile/', views.profile, name='profile'),
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Static pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Order tracking
    path('order-tracking/', views.order_tracking, name='order_tracking'),
]
