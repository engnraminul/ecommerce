from django.urls import path
from . import views
from . import auth_views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', auth_views.register, name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset
    path('forgot-password/', auth_views.forgot_password, name='forgot_password'),
    path('reset-password/<uuid:token>/', auth_views.reset_password, name='reset_password'),
    
    # Email Activation
    path('activate/<uuid:token>/', auth_views.activate_account, name='activate_account'),
    path('resend-activation/', auth_views.resend_activation, name='resend_activation'),
    
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
