from django.urls import path
from . import views

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
    
    # Invoices
    path('<int:order_id>/invoice/', views.InvoiceView.as_view(), name='order-invoice'),
    path('<int:order_id>/invoice/pdf/', views.generate_invoice_pdf, name='generate-invoice-pdf'),
    
    # Refunds
    path('refund-requests/', views.RefundRequestListView.as_view(), name='refund-request-list'),
    path('refund-requests/<int:pk>/', views.RefundRequestDetailView.as_view(), name='refund-request-detail'),
]
