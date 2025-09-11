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
    OrderDashboardSerializer, OrderItemDashboardSerializer, DashboardStatisticsSerializer
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
        self.log_activity('created', instance)
        
    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_activity('updated', instance)
        
    def perform_destroy(self, instance):
        self.log_activity('deleted', instance)
        instance.delete()
    
    def log_activity(self, action, instance):
        AdminActivity.objects.create(
            user=self.request.user,
            action=action,
            model_name='DashboardSetting',
            object_id=instance.id,
            object_repr=instance.key,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
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
        self.log_activity('created', instance)
        
    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_activity('updated', instance)
        
    def perform_destroy(self, instance):
        self.log_activity('deleted', instance)
        instance.delete()
    
    def log_activity(self, action, instance):
        AdminActivity.objects.create(
            user=self.request.user,
            action=action,
            model_name='User',
            object_id=instance.id,
            object_repr=instance.username,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
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
        self.log_activity('created', instance)
        
    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_activity('updated', instance)
        
    def perform_destroy(self, instance):
        self.log_activity('deleted', instance)
        instance.delete()
    
    def log_activity(self, action, instance):
        AdminActivity.objects.create(
            user=self.request.user,
            action=action,
            model_name='Category',
            object_id=instance.id,
            object_repr=instance.name,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

class ProductDashboardViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'base_price']
    
    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_activity('created', instance)
        
    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_activity('updated', instance)
        
    def perform_destroy(self, instance):
        self.log_activity('deleted', instance)
        instance.delete()
    
    def log_activity(self, action, instance):
        AdminActivity.objects.create(
            user=self.request.user,
            action=action,
            model_name='Product',
            object_id=instance.id,
            object_repr=instance.name,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
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
        self.log_activity('created', instance)
        
    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_activity('updated', instance)
        
    def perform_destroy(self, instance):
        self.log_activity('deleted', instance)
        instance.delete()
    
    def log_activity(self, action, instance):
        AdminActivity.objects.create(
            user=self.request.user,
            action=action,
            model_name='ProductVariant',
            object_id=instance.id,
            object_repr=f"{instance.product.name} - {instance.name}",
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
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
        self.log_activity('updated', instance)
    
    def perform_destroy(self, instance):
        self.log_activity('deleted', instance)
        instance.delete()
    
    def log_activity(self, action, instance):
        AdminActivity.objects.create(
            user=self.request.user,
            action=action,
            model_name='Order',
            object_id=instance.id,
            object_repr=instance.order_number,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        status = request.data.get('status')
        
        if not status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = status
        order.save()
        
        self.log_activity('updated status', order)
        
        return Response({'success': True, 'status': order.status})

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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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
