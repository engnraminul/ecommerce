from django.shortcuts import render
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from .models import DashboardSetting, AdminActivity
from .serializers import (
    DashboardSettingSerializer, AdminActivitySerializer, UserDashboardSerializer,
    CategoryDashboardSerializer, ProductDashboardSerializer, ProductVariantDashboardSerializer,
    OrderDashboardSerializer, OrderItemDashboardSerializer, DashboardStatisticsSerializer,
    ShippingAddressDashboardSerializer
)
from products.models import Product, ProductVariant, Category
from orders.models import Order, OrderItem
from users.models import User

class DashboardSettingViewSet(viewsets.ModelViewSet):
    queryset = DashboardSetting.objects.all()
    serializer_class = DashboardSettingSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('created', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_destroy(self, instance):
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        instance.delete()
    
    def log_activity(self, action, instance):
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action=action,
                model_name='DashboardSetting',
                object_id=instance.id,
                object_repr=instance.key,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class AdminActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdminActivity.objects.all()
    serializer_class = AdminActivitySerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'action', 'model_name', 'object_repr']
    ordering_fields = ['timestamp', 'user__username', 'action', 'model_name']
    ordering = ['-timestamp']

class UserDashboardViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'last_login']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('created', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_destroy(self, instance):
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        instance.delete()
    
    def log_activity(self, action, instance):
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action=action,
                model_name='User',
                object_id=instance.id,
                object_repr=instance.username,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class CategoryDashboardViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('created', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_destroy(self, instance):
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        instance.delete()
    
    def log_activity(self, action, instance):
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action=action,
                model_name='Category',
                object_id=instance.id,
                object_repr=instance.name,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class ProductDashboardViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['category', 'is_active', 'is_featured', 'is_digital', 'shipping_type']
    search_fields = ['name', 'description', 'short_description', 'sku', 'barcode']
    ordering_fields = ['name', 'created_at', 'price', 'stock_quantity']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('created', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_destroy(self, instance):
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        instance.delete()
    
    def log_activity(self, action, instance):
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action=action,
                model_name='Product',
                object_id=instance.id,
                object_repr=instance.name,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class ProductVariantDashboardViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['product', 'is_active']
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'price', 'stock_quantity']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('created', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
    def perform_destroy(self, instance):
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        instance.delete()
    
    def log_activity(self, action, instance):
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action=action,
                model_name='ProductVariant',
                object_id=instance.id,
                object_repr=f"{instance.product.name} - {instance.name}",
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class OrderDashboardViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_destroy(self, instance):
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            # Log the error but continue with deletion
            print(f"Error logging activity: {str(e)}")
        
        # Proceed with deletion even if logging fails
        instance.delete()
    
    def log_activity(self, action, instance):
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action=action,
                model_name='Order',
                object_id=instance.id,
                object_repr=instance.order_number,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            from rest_framework import status as http_status
            return Response({'error': 'Status is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        
        # Update order status
        order.status = new_status
        
        # Handle courier charge if provided
        if 'curier_charge' in request.data and request.data['curier_charge'] is not None:
            try:
                order.curier_charge = float(request.data['curier_charge'])
            except (ValueError, TypeError) as e:
                print(f"Error setting courier charge: {e}")
                return Response({'error': 'Invalid courier charge value'}, status=400)
        
        # Handle partially returned amount if applicable
        if new_status == 'partially_returned' and 'partially_ammount' in request.data:
            try:
                if not request.data['partially_ammount']:
                    return Response({'error': 'Refund amount is required for partially returned status'}, status=400)
                order.partially_ammount = float(request.data['partially_ammount'])
            except (ValueError, TypeError) as e:
                print(f"Error setting partially returned amount: {e}")
                return Response({'error': 'Invalid refund amount value'}, status=400)
        
        # Save the order with all updates
        order.save()
        
        # Handle customer notification if requested
        notify_customer = request.data.get('notify_customer', False)
        if notify_customer:
            try:
                # Here you would implement your email notification logic
                # For now, just log that we would send an email
                print(f"Would send status update email to {order.customer_email or order.user.email if order.user else 'No email'}")
                # You could implement a utility function like:
                # from .utils import send_order_status_email
                # send_order_status_email(order, new_status, request.data.get('comment', ''))
            except Exception as e:
                print(f"Error sending notification email: {e}")
        
        try:
            # Include the additional fields in the activity log
            additional_info = {}
            if 'curier_charge' in request.data and request.data['curier_charge']:
                additional_info['courier_charge'] = request.data['curier_charge']
            if 'partially_ammount' in request.data and request.data['partially_ammount']:
                additional_info['partially_refunded'] = request.data['partially_ammount']
                
            activity_details = f"Updated status to {new_status}"
            if additional_info:
                activity_details += f" with {additional_info}"
                
            self.log_activity(activity_details, order)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        return Response({'success': True, 'status': order.status})
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Get all items for a specific order
        """
        try:
            order = self.get_object()
            print(f"Fetching items for order ID: {order.id}, Order Number: {order.order_number}")
            
            # Use select_related to optimize query
            items = OrderItem.objects.filter(order=order).select_related('product', 'variant')
            
            # Log the items for debugging
            print(f"Found {items.count()} items for order {order.order_number}")
            for item in items:
                print(f"Item ID: {item.id}, Product: {item.product_name}, Quantity: {item.quantity}, Price: {item.unit_price}")
            
            # Serialize the data
            serializer = OrderItemDashboardSerializer(items, many=True)
            serialized_data = serializer.data
            
            # Log the serialized data for debugging
            print(f"Serialized data: {serialized_data}")
            
            return Response(serialized_data)
        except Exception as e:
            print(f"Error in items action: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def add_to_curier(self, request, pk=None):
        """Add order to curier service and save the consignment ID"""
        try:
            # Import the utility function here to avoid circular imports
            from settings.utils import send_order_to_curier
            
            order = self.get_object()
            
            # Check if order already has a curier ID
            if order.curier_id:
                return Response({
                    "success": False,
                    "message": f"Order already has a curier ID: {order.curier_id}"
                }, status=400)
            
            # Send order to curier service
            success, result = send_order_to_curier(order)
            
            if success:
                # Check if we got a consignment ID back based on the API documentation
                consignment_id = None
                
                # Try to extract consignment ID from the SteadFast API response
                if isinstance(result, dict):
                    # SteadFast puts the data in a consignment object
                    if 'consignment' in result and isinstance(result['consignment'], dict):
                        consignment_data = result['consignment']
                        # Try consignment_id first (primary identifier)
                        if 'consignment_id' in consignment_data:
                            consignment_id = consignment_data['consignment_id']
                        # Try tracking_code as backup
                        elif 'tracking_code' in consignment_data:
                            consignment_id = consignment_data['tracking_code']
                    # Log the entire result for debugging
                    print(f"SteadFast API response: {result}")
                
                # Save consignment ID to order if found
                if consignment_id:
                    order.curier_id = consignment_id
                    order.curier_status = 'submitted'
                    # Change order status to shipped
                    order.status = 'shipped'
                    order.save()
                    
                    # Log the action
                    try:
                        self.log_activity('added_to_curier', order)
                    except Exception as e:
                        print(f"Error logging activity: {str(e)}")
                    
                    return Response({
                        "success": True,
                        "message": "Order successfully added to curier service",
                        "curier_id": consignment_id,
                        "response": result
                    })
                else:
                    return Response({
                        "success": True,
                        "message": "Order submitted to curier service, but no consignment ID was returned",
                        "response": result
                    })
            else:
                # Return error from curier service
                return Response({
                    "success": False,
                    "message": "Failed to add order to curier service",
                    "error": result.get("error", "Unknown error")
                }, status=400)
        
        except Exception as e:
            print(f"Error adding order to curier: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                "success": False,
                "message": f"Error adding order to curier: {str(e)}"
            }, status=500)

class DashboardStatisticsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get query parameters for date filtering
        period = request.query_params.get('period', 'week')
        
        # Define time periods
        now = timezone.now()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:  # default to week
            start_date = now - timedelta(days=7)
        
        # Get statistics data
        total_sales = Order.objects.filter(
            created_at__gte=start_date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        orders_count = Order.objects.filter(created_at__gte=start_date).count()
        products_count = Product.objects.filter(is_active=True).count()
        customers_count = User.objects.filter(is_active=True).count()
        
        # Get recent orders
        recent_orders = Order.objects.filter(
            created_at__gte=start_date
        ).order_by('-created_at')[:5]
        
        # Get popular products based on order items
        popular_products = list(OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).values('product_variant__product__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5])
        
        # Sales by period (daily for week, weekly for month, monthly for year)
        sales_by_period = []
        if period == 'week':
            # Daily sales for the past week
            for i in range(7):
                day = now - timedelta(days=i)
                day_sales = Order.objects.filter(
                    created_at__date=day.date()
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                sales_by_period.append({
                    'date': day.date().strftime('%Y-%m-%d'),
                    'sales': day_sales
                })
        elif period == 'month':
            # Weekly sales for the past month
            for i in range(4):
                week_start = now - timedelta(days=(i+1)*7)
                week_end = now - timedelta(days=i*7)
                week_sales = Order.objects.filter(
                    created_at__gte=week_start,
                    created_at__lt=week_end
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                sales_by_period.append({
                    'week': f'Week {i+1}',
                    'sales': week_sales
                })
        elif period == 'year':
            # Monthly sales for the past year
            for i in range(12):
                month = now.month - i
                year = now.year
                if month <= 0:
                    month += 12
                    year -= 1
                month_sales = Order.objects.filter(
                    created_at__month=month,
                    created_at__year=year
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                sales_by_period.append({
                    'month': month,
                    'year': year,
                    'sales': month_sales
                })
        
        # Prepare the response data
        data = {
            'total_sales': total_sales,
            'orders_count': orders_count,
            'products_count': products_count,
            'customers_count': customers_count,
            'recent_orders': OrderDashboardSerializer(recent_orders, many=True).data,
            'popular_products': popular_products,
            'sales_by_period': sales_by_period
        }
        
        serializer = DashboardStatisticsSerializer(data)
        return Response(serializer.data)

# Frontend views for dashboard SPA
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from orders.models import Order, OrderItem

def is_admin(user):
    return user.is_staff

def dashboard_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid login credentials or insufficient permissions.')
    
    return render(request, 'dashboard/login.html')

@login_required
def dashboard_logout(request):
    logout(request)
    return redirect('dashboard:login')

@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    # Get some basic statistics for the dashboard home
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_users = User.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    context = {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'active_page': 'home'
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_products(request):
    context = {
        'active_page': 'products'
    }
    return render(request, 'dashboard/products.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_orders(request):
    context = {
        'active_page': 'orders'
    }
    return render(request, 'dashboard/orders.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_users(request):
    context = {
        'active_page': 'users'
    }
    return render(request, 'dashboard/users.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_statistics(request):
    context = {
        'active_page': 'statistics'
    }
    return render(request, 'dashboard/statistics.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_settings(request):
    settings = DashboardSetting.objects.all()
    context = {
        'settings': settings,
        'active_page': 'settings'
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_profile(request):
    context = {
        'active_page': 'profile'
    }
    return render(request, 'dashboard/profile.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_accounts(request):
    context = {
        'active_page': 'accounts'
    }
    return render(request, 'dashboard/accounts.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_api_docs(request):
    context = {
        'active_page': 'api_docs'
    }
    return render(request, 'dashboard/api_docs.html', context)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_order_items(request, order_id):
    """
    Explicit view function for getting order items, bypassing the ViewSet action
    to fix the 404 issue
    """
    try:
        order = get_object_or_404(Order, id=order_id)
        print(f"Fetching items for order ID: {order.id}, Order Number: {order.order_number}")
        
        # Use select_related to optimize query
        items = OrderItem.objects.filter(order=order).select_related('product', 'variant')
        
        # Log the items for debugging
        print(f"Found {items.count()} items for order {order.order_number}")
        for item in items:
            print(f"Item ID: {item.id}, Product: {item.product_name}, Quantity: {item.quantity}, Price: {item.unit_price}")
        
        # Serialize the data
        serializer = OrderItemDashboardSerializer(items, many=True)
        serialized_data = serializer.data
        
        # Log the serialized data for debugging
        print(f"Serialized data: {serialized_data}")
        
        return Response(serialized_data)
    except Exception as e:
        print(f"Error in get_order_items view: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=400)
