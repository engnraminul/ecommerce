from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'contacts', views.ContactDashboardViewSet)
router.register(r'contacts-public', views.ContactPublicViewSet, basename='contacts-public')

app_name = 'contact'

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Contact Settings URLs
    path('api/contact-settings/', views.get_contact_settings, name='get_contact_settings'),
    path('api/contact-settings/update/', views.update_contact_settings, name='update_contact_settings'),
    

    
    # Public contact page
    path('', views.contact_page, name='contact_page'),
]