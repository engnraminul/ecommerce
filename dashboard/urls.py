from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import order_views
from . import media_api
from . import email_views
from orders import order_edit_views
from pages import dashboard_views as pages_dashboard_views

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
router.register(r'blocklist', views.BlockListViewSet)

# Pages management router
router.register(r'pages/pages', pages_dashboard_views.PageDashboardViewSet, basename='pages')
router.register(r'pages/categories', pages_dashboard_views.PageCategoryDashboardViewSet, basename='page-categories')
router.register(r'pages/templates', pages_dashboard_views.PageTemplateDashboardViewSet, basename='page-templates')
router.register(r'pages/media', pages_dashboard_views.PageMediaDashboardViewSet, basename='page-media')
router.register(r'pages/analytics', pages_dashboard_views.PageAnalyticsDashboardViewSet, basename='page-analytics')
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
    
    # Product variant nested endpoints
    path('api/products/<int:product_id>/variants/<int:variant_id>/', views.ProductVariantDashboardViewSet.as_view({'get': 'retrieve'}), name='product_variant_detail'),
    
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
    path('api/media/<str:file_id>/edit/', media_api.edit_media_file, name='edit_media_file'),
    path('api/media/<str:file_id>/download/', media_api.download_media_file, name='download_media_file'),
    path('api/media/<str:file_id>/delete/', media_api.delete_media_file, name='delete_media_file'),
    path('api/media/directories/create/', media_api.create_directory, name='create_media_directory'),
    
    # BlockList management API
    path('api/blocklist/bulk-block/', views.BlockListViewSet.as_view({'post': 'bulk_block'}), name='blocklist-bulk-block'),
    path('api/blocklist/bulk-unblock/', views.BlockListViewSet.as_view({'post': 'bulk_unblock'}), name='blocklist-bulk-unblock'),
    path('api/blocklist/statistics/', views.BlockListViewSet.as_view({'get': 'statistics'}), name='blocklist-statistics'),
    
    # Frontend views for the dashboard SPA
    path('', views.dashboard_home, name='home'),
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('products/', views.dashboard_products, name='products'),
    path('categories/', views.dashboard_categories, name='categories'),
    path('media/', views.dashboard_media, name='media'),
    path('stock/', views.dashboard_stock, name='stock'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('incomplete-orders/', views.dashboard_incomplete_orders, name='incomplete_orders'),
    path('users/', views.dashboard_users, name='users'),
    path('expenses/', views.dashboard_expenses, name='expenses'),
    path('statistics/', views.dashboard_statistics, name='statistics'),
    path('settings/', views.dashboard_settings, name='settings'),
    path('settings/debug/', views.debug_settings, name='debug_settings'),
    path('settings/test/', views.test_settings_post, name='test_settings_post'),
    path('profile/', views.dashboard_profile, name='profile'),
    path('accounts/', views.dashboard_accounts, name='accounts'),
    path('api-docs/', views.dashboard_api_docs, name='api_docs'),
    path('pages/', views.dashboard_pages, name='pages'),
    path('blocklist/', views.dashboard_blocklist, name='blocklist'),
    
    # Reviews Management URLs
    path('reviews/', views.reviews_dashboard, name='reviews'),
    path('reviews/bulk-action/', views.review_bulk_action, name='review_bulk_action'),
    path('reviews/<int:review_id>/action/', views.review_single_action, name='review_single_action'),
    
    # Email Settings URLs
    path('email-settings/', email_views.email_settings_index, name='email_settings_index'),
    
    # Email Configuration URLs
    path('email-settings/configuration/', email_views.email_configuration_list, name='email_configuration_list'),
    path('email-settings/configuration/create/', email_views.email_configuration_create, name='email_configuration_create'),
    path('email-settings/configuration/<int:pk>/edit/', email_views.email_configuration_edit, name='email_configuration_edit'),
    path('email-settings/configuration/<int:pk>/delete/', email_views.email_configuration_delete, name='email_configuration_delete'),
    path('email-settings/configuration/<int:pk>/test/', email_views.email_configuration_test, name='email_configuration_test'),
    path('email-settings/configuration/<int:pk>/activate/', email_views.email_configuration_activate, name='email_configuration_activate'),
    
    # Email Template URLs
    path('email-settings/templates/', email_views.email_template_list, name='email_template_list'),
    path('email-settings/templates/create/', email_views.email_template_create, name='email_template_create'),
    path('email-settings/templates/<int:pk>/edit/', email_views.email_template_edit, name='email_template_edit'),
    path('email-settings/templates/<int:pk>/delete/', email_views.email_template_delete, name='email_template_delete'),
    path('email-settings/templates/<int:pk>/preview/', email_views.email_template_preview, name='email_template_preview'),
    
    # Email Log URLs
    path('email-settings/logs/', email_views.email_log_list, name='email_log_list'),
    path('email-settings/logs/<int:pk>/', email_views.email_log_detail, name='email_log_detail'),
    
    # Bulk Email URLs
    path('email-settings/bulk/', email_views.bulk_email, name='bulk_email'),
    
    # AJAX URLs
    path('ajax/smtp-defaults/', email_views.ajax_get_smtp_defaults, name='ajax_smtp_defaults'),
    path('ajax/template-variables/<int:pk>/', email_views.ajax_template_variables, name='ajax_template_variables'),
]