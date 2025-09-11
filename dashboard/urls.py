from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', views.dashboard_home, name='home'),
    
    # Order management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Product management
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Product variant management
    path('products/<int:product_id>/variants/', views.variant_list, name='variant_list'),
    path('products/<int:product_id>/variants/create/', views.variant_create, name='variant_create'),
    path('products/variants/<int:pk>/edit/', views.variant_edit, name='variant_edit'),
    path('products/variants/<int:pk>/delete/', views.variant_delete, name='variant_delete'),
]
