from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db import transaction
from .models import User, UserProfile, Address
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserUpdateSerializer, ChangePasswordSerializer, AddressSerializer,
    UserProfileSerializer
)


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        # Log received data for debugging
        print("Received registration data:", request.data)
        print("Content-Type:", request.content_type)
        
        # Make a copy of the request data to ensure we can modify it
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Ensure password_confirm is present if password is present
        if 'password' in data and 'password_confirm' not in data:
            data['password_confirm'] = data['password']
            print("Added missing password_confirm field in view")
        
        # Print data keys for debugging
        print("Data keys after processing:", data.keys())
        
        serializer = self.get_serializer(data=data)
        
        if not serializer.is_valid():
            # Log validation errors for debugging
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """User login view"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        login(request, user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful'
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer


class ChangePasswordView(generics.GenericAPIView):
    """Change password view"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        })


class AddressListCreateView(generics.ListCreateAPIView):
    """List and create user addresses"""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete user addresses"""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class ProfileUpdateView(generics.UpdateAPIView):
    """Update user profile preferences"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout_view(request):
    """Logout view (for token blacklisting if needed)"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout successful'})
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats_view(request):
    """Get user statistics (orders, reviews, etc.)"""
    user = request.user
    
    # Get user statistics
    from orders.models import Order
    from products.models import Review
    
    stats = {
        'total_orders': Order.objects.filter(user=user).count(),
        'completed_orders': Order.objects.filter(user=user, status='delivered').count(),
        'pending_orders': Order.objects.filter(user=user, status__in=['pending', 'confirmed', 'processing', 'shipped']).count(),
        'total_reviews': Review.objects.filter(user=user, is_approved=True).count(),
        'wishlist_items': user.wishlist_items.count(),
        'addresses_count': user.addresses.count(),
    }
    
    return Response(stats)
