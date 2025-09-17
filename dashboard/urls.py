from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import order_views

router = DefaultRouter()
router.register(r'settings', views.DashboardSettingViewSet)
router.register(r'activities', views.AdminActivityViewSet)
router.register(r'users', views.UserDashboardViewSet)
router.register(r'categories', views.CategoryDashboardViewSet)
router.register(r'products', views.ProductDashboardViewSet)
router.register(r'variants', views.ProductVariantDashboardViewSet)
router.register(r'orders', views.OrderDashboardViewSet)
app_name = 'dashboard'

urlpatterns = [
    path('api/', include(router.urls)),
    # Explicit URL patterns for order-related actions
    path('api/orders/<int:order_id>/items/', order_views.get_order_items, name='order_items'),
    # Add an explicit path for add_to_curier that matches the JavaScript URL
    path('api/orders/<int:pk>/add_to_curier/', views.OrderDashboardViewSet.as_view({'post': 'add_to_curier'}), name='order_add_to_curier'),
    path('api/statistics/', views.DashboardStatisticsView.as_view(), name='statistics'),
    
    # Frontend views for the dashboard SPA
    path('', views.dashboard_home, name='home'),
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('products/', views.dashboard_products, name='products'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('users/', views.dashboard_users, name='users'),
    path('statistics/', views.dashboard_statistics, name='statistics'),
    path('settings/', views.dashboard_settings, name='settings'),
    path('profile/', views.dashboard_profile, name='profile'),
    path('accounts/', views.dashboard_accounts, name='accounts'),
    path('api-docs/', views.dashboard_api_docs, name='api_docs'),
]