from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
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
        'wishlist_items': user.wishlist_items.count() if hasattr(user, 'wishlist_items') else 0,
        'addresses_count': user.addresses.count(),
    }
    
    return Response(stats)


# API endpoints for profile page
@login_required
@require_http_methods(['POST'])
def update_profile_picture(request):
    """API endpoint to update user profile picture"""
    if 'profile_picture' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No image provided'})
    
    try:
        # Get the uploaded image
        image = request.FILES['profile_picture']
        
        # Update user profile picture
        request.user.profile_picture = image
        request.user.save()
        
        # Return success response with new image URL
        return JsonResponse({
            'success': True,
            'image_url': request.user.profile_picture.url
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['GET', 'POST'])
def address_api_list_create(request):
    """API endpoint to list and create addresses"""
    if request.method == 'GET':
        addresses = Address.objects.filter(user=request.user)
        addresses_data = []
        
        for address in addresses:
            addresses_data.append({
                'id': address.id,
                'type': address.address_type,
                'line1': address.address_line_1,
                'line2': address.address_line_2,
                'city': address.city,
                'state': address.state,
                'postal_code': address.postal_code,
                'country': address.country,
                'is_default': address.is_default
            })
            
        return JsonResponse({'success': True, 'addresses': addresses_data})
    
    elif request.method == 'POST':
        try:
            # Extract address data
            address_type = request.POST.get('address_type')
            is_default = request.POST.get('is_default') == 'on'
            
            # Create new address
            address = Address(
                user=request.user,
                address_type=address_type,
                address_line_1=request.POST.get('address_line_1'),
                address_line_2=request.POST.get('address_line_2', ''),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                postal_code=request.POST.get('postal_code'),
                country=request.POST.get('country'),
                is_default=is_default
            )
            
            # If it's default, reset other addresses of same type
            if is_default:
                Address.objects.filter(
                    user=request.user, 
                    address_type=address_type, 
                    is_default=True
                ).update(is_default=False)
                
            address.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['GET', 'PUT', 'DELETE'])
def address_api_detail(request, address_id):
    """API endpoint to get, update, or delete an address"""
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)
    
    if request.method == 'GET':
        # Return address details
        address_data = {
            'id': address.id,
            'type': address.address_type,
            'line1': address.address_line_1,
            'line2': address.address_line_2,
            'city': address.city,
            'state': address.state,
            'postal_code': address.postal_code,
            'country': address.country,
            'is_default': address.is_default
        }
        return JsonResponse(address_data)
    
    elif request.method == 'PUT':
        try:
            # Extract address data
            address_type = request.POST.get('address_type')
            is_default = request.POST.get('is_default') == 'on'
            
            # Update address fields
            address.address_type = address_type
            address.address_line_1 = request.POST.get('address_line_1')
            address.address_line_2 = request.POST.get('address_line_2', '')
            address.city = request.POST.get('city')
            address.state = request.POST.get('state')
            address.postal_code = request.POST.get('postal_code')
            address.country = request.POST.get('country')
            
            # Handle default address
            if is_default and not address.is_default:
                # Reset other default addresses
                Address.objects.filter(
                    user=request.user, 
                    address_type=address_type, 
                    is_default=True
                ).update(is_default=False)
                address.is_default = True
            elif not is_default and address.is_default:
                # Don't allow removing default status if it's the only address
                if Address.objects.filter(user=request.user, address_type=address_type).count() == 1:
                    address.is_default = True
                else:
                    address.is_default = False
            
            address.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    elif request.method == 'DELETE':
        # Don't allow deletion if it's the only address of this type
        if address.is_default:
            return JsonResponse({
                'success': False, 
                'error': 'Cannot delete default address. Set another address as default first.'
            }, status=400)
        
        address.delete()
        return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def set_default_address(request, address_id):
    """API endpoint to set an address as default"""
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)
    
    # Reset default for other addresses of same type
    Address.objects.filter(
        user=request.user, 
        address_type=address.address_type, 
        is_default=True
    ).update(is_default=False)
    
    # Set as default
    address.is_default = True
    address.save()
    
    return JsonResponse({'success': True})
