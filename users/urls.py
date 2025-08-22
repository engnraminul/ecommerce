from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Addresses
    path('addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    
    # API endpoints
    path('api/v1/addresses/', views.address_api_list_create, name='address-api-list-create'),
    path('api/v1/addresses/<int:address_id>/', views.address_api_detail, name='address-api-detail'),
    path('api/v1/addresses/<int:address_id>/set_default/', views.set_default_address, name='set-default-address'),
    path('api/v1/profile-picture/', views.update_profile_picture, name='update-profile-picture'),
    
    # Statistics
    path('stats/', views.user_stats_view, name='user-stats'),
]
