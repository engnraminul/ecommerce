from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'incomplete-orders', views.IncompleteOrderViewSet)
router.register(r'incomplete-order-items', views.IncompleteOrderItemViewSet)
router.register(r'incomplete-order-history', views.IncompleteOrderHistoryViewSet)
router.register(r'recovery-emails', views.RecoveryEmailLogViewSet)
router.register(r'analytics', views.IncompleteOrderAnalyticsViewSet)

app_name = 'incomplete_orders'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
]