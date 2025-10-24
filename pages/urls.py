from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()
router.register(r'categories', views.PageCategoryViewSet)
router.register(r'templates', views.PageTemplateViewSet)
router.register(r'pages', views.PageViewSet)
router.register(r'media', views.PageMediaViewSet)
router.register(r'revisions', views.PageRevisionViewSet)
router.register(r'analytics', views.PageAnalyticsViewSet)

app_name = 'pages_app'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/search/', views.page_search, name='page_search'),
    path('api/statistics/', views.page_statistics, name='page_statistics'),
    
    # Frontend views
    path('', views.page_list, name='page_list'),
    path('category/<slug:slug>/', views.page_category, name='page_category'),
    path('<slug:slug>/', views.page_detail, name='page_detail'),
]