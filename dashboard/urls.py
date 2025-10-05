from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import order_views
from . import media_api
from orders import order_edit_views

router = DefaultRouter()
router.register(r'settings', views.DashboardSettingViewSet)
router.register(r'activities', views.AdminActivityViewSet)
router.register(r'users', views.UserDashboardViewSet)
router.register(r'categories', views.CategoryDashboardViewSet)
router.register(r'products', views.ProductDashboardViewSet)
router.register(r'variants', views.ProductVariantDashboardViewSet)
router.register(r'product-images', views.ProductImageDashboardViewSet)
router.register(r'stock', views.StockDashboardViewSet, basename='stock')
router.register(r'stock-variants', views.StockVariantDashboardViewSet, basename='stock-variant')
router.register(r'orders', views.OrderDashboardViewSet)
router.register(r'incomplete-orders', views.IncompleteOrderDashboardViewSet)
router.register(r'expenses', views.ExpenseDashboardViewSet)
router.register(r'checkout-customization', views.CheckoutCustomizationViewSet)
app_name = 'dashboard'

urlpatterns = [
    path('api/', include(router.urls)),
    # Explicit URL patterns for order-related actions
    path('api/orders/<int:order_id>/items/', order_views.get_order_items, name='order_items'),
    path('api/orders/<int:order_id>/restock/', order_views.restock_order_items, name='restock_order_items'),
    
    # Order editing endpoints
    path('api/orders/<int:order_id>/edit/', order_edit_views.get_order_for_edit, name='get_order_for_edit'),
    path('api/orders/<int:order_id>/edit/update-item/', order_edit_views.update_order_item, name='update_order_item'),
    path('api/orders/<int:order_id>/edit/update-quantity/', order_edit_views.update_order_item_quantity, name='update_order_item_quantity'),
    path('api/orders/<int:order_id>/edit/add-item/', order_edit_views.add_order_item, name='add_order_item'),
    path('api/orders/<int:order_id>/edit/delete-item/', order_edit_views.delete_order_item, name='delete_order_item'),
    path('api/orders/<int:order_id>/edit/update-address/', order_edit_views.update_shipping_address, name='update_shipping_address'),
    path('api/orders/<int:order_id>/edit/courier-info/', order_edit_views.update_courier_info, name='update_courier_info'),
    path('api/orders/edit/available-products/', order_edit_views.get_available_products, name='get_available_products'),
    
    # Add an explicit path for add_to_curier that matches the JavaScript URL
    path('api/orders/<int:pk>/add_to_curier/', views.OrderDashboardViewSet.as_view({'post': 'add_to_curier'}), name='order_add_to_curier'),
    path('api/statistics/', views.DashboardStatisticsView.as_view(), name='statistics'),
    path('api/order-status-breakdown/', views.OrderStatusBreakdownView.as_view(), name='order_status_breakdown'),
    path('api/products-performance/', views.ProductPerformanceView.as_view(), name='products_performance'),
    path('api/export-products/', views.export_products_performance, name='export_products'),
    # Fraud check API endpoint
    path('api/fraud-check/', views.fraud_check_api, name='fraud_check_api'),
    
    # Checkout customization public API
    path('api/checkout-customization/', views.get_checkout_customization, name='get_checkout_customization'),
    
    # Media Library API
    path('api/media/', media_api.list_media_files, name='list_media_files'),
    path('api/media/upload/', media_api.upload_media_file, name='upload_media_file'),
    path('api/media/<str:file_id>/delete/', media_api.delete_media_file, name='delete_media_file'),
    
    # Frontend views for the dashboard SPA
    path('', views.dashboard_home, name='home'),
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('products/', views.dashboard_products, name='products'),
    path('stock/', views.dashboard_stock, name='stock'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('incomplete-orders/', views.dashboard_incomplete_orders, name='incomplete_orders'),
    path('users/', views.dashboard_users, name='users'),
    path('expenses/', views.dashboard_expenses, name='expenses'),
    path('statistics/', views.dashboard_statistics, name='statistics'),
    path('settings/', views.dashboard_settings, name='settings'),
    path('profile/', views.dashboard_profile, name='profile'),
    path('accounts/', views.dashboard_accounts, name='accounts'),
    path('api-docs/', views.dashboard_api_docs, name='api_docs'),
]