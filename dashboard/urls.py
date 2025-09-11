from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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