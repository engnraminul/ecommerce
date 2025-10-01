from django.urls import path
from . import views
from . import api
from . import order_edit_views

app_name = 'orders'

urlpatterns = [
    # Orders
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.CreateOrderView.as_view(), name='create-order'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel-order'),
    path('<str:order_number>/track/', views.track_order, name='track-order'),
    
    # Order management
    path('recent/', views.recent_orders, name='recent-orders'),
    path('stats/', views.order_stats, name='order-stats'),
    path('<int:order_id>/reorder/', views.reorder, name='reorder'),
    
    # Order editing (admin only)
    path('edit/<int:order_id>/', order_edit_views.get_order_for_edit, name='get-order-for-edit'),
    path('edit/<int:order_id>/update-quantity/', order_edit_views.update_order_item_quantity, name='update-order-item-quantity'),
    path('edit/<int:order_id>/add-item/', order_edit_views.add_order_item, name='add-order-item'),
    path('edit/<int:order_id>/delete-item/', order_edit_views.delete_order_item, name='delete-order-item'),
    path('edit/<int:order_id>/update-address/', order_edit_views.update_shipping_address, name='update-shipping-address'),
    path('edit/<int:order_id>/courier-info/', order_edit_views.update_courier_info, name='update-courier-info'),
    path('edit/available-products/', order_edit_views.get_available_products, name='get-available-products'),
    
    # Invoices
    path('<int:order_id>/invoice/', views.InvoiceView.as_view(), name='order-invoice'),
    path('<int:order_id>/invoice/pdf/', views.generate_invoice_pdf, name='generate-invoice-pdf'),
    
    # Refunds
    path('refund-requests/', views.RefundRequestListView.as_view(), name='refund-request-list'),
    path('refund-requests/<int:pk>/', views.RefundRequestDetailView.as_view(), name='refund-request-detail'),
    
    # API endpoints
    path('api/recent/', api.recent_orders, name='api-recent-orders'),
    path('api/orders/<int:order_id>/', api.order_detail_api, name='api-order-detail'),
]
