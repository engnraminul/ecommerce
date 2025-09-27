from django.shortcuts import render
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import JsonResponse
from decimal import Decimal

from .models import DashboardSetting, AdminActivity, Expense
from .serializers import (
    DashboardSettingSerializer, AdminActivitySerializer, UserDashboardSerializer,
    CategoryDashboardSerializer, ProductDashboardSerializer, ProductDetailSerializer, ProductVariantDashboardSerializer,
    ProductImageDashboardSerializer, OrderDashboardSerializer, OrderItemDashboardSerializer, DashboardStatisticsSerializer,
    ShippingAddressDashboardSerializer, ExpenseDashboardSerializer
)
from products.models import Product, ProductVariant, ProductImage, Category
from orders.models import Order, OrderItem
from users.models import User

class IsStaffUser(permissions.BasePermission):
    """Custom permission to match dashboard view requirements"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

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
    permission_classes = [IsStaffUser]
    filterset_fields = ['category', 'is_active', 'is_featured', 'is_digital', 'shipping_type']
    search_fields = ['name', 'description', 'short_description', 'sku', 'barcode']
    ordering_fields = ['name', 'created_at', 'price', 'stock_quantity']
    
    def get_serializer_class(self):
        """Use detailed serializer for create/update operations"""
        if self.action in ['create', 'update', 'partial_update', 'retrieve']:
            return ProductDetailSerializer
        return ProductDashboardSerializer
    
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

class ProductImageDashboardViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageDashboardSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['product', 'is_primary']
    ordering_fields = ['created_at', 'is_primary']
    ordering = ['-is_primary', 'created_at']
    
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
                model_name='ProductImage',
                object_id=instance.id,
                object_repr=f"Image for {instance.product.name}",
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            # Handle database errors
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')
    
    @action(detail=False, methods=['post'])
    def reorder_images(self, request):
        """Reorder product images based on provided order"""
        try:
            image_ids = request.data.get('image_ids', [])
            product_id = request.data.get('product_id')
            
            if not image_ids or not product_id:
                return Response({'error': 'image_ids and product_id are required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Update the order by updating created_at (since we order by created_at)
            # In a real implementation, you'd add an 'order' field to the model
            from datetime import datetime, timedelta
            base_time = datetime.now()
            
            for i, image_id in enumerate(image_ids):
                try:
                    image = ProductImage.objects.get(id=image_id, product_id=product_id)
                    # Simulate ordering by updating created_at with incremental timestamps
                    image.created_at = base_time + timedelta(seconds=i)
                    image.save(update_fields=['created_at'])
                except ProductImage.DoesNotExist:
                    continue
            
            return Response({'success': True}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Check if user is staff (admin user)
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=403)
        
        try:
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
            elif period == 'all':
                start_date = None
            else:  # default to week
                start_date = now - timedelta(days=7)
            
            # Build base query filter
            date_filter = Q()
            if start_date:
                date_filter = Q(created_at__gte=start_date)
            
            # Calculate Total Sales Amount based on order status
            delivered_shipped_sales = Order.objects.filter(
                date_filter & Q(status__in=['delivered', 'shipped'])
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            partially_returned_sales = Order.objects.filter(
                date_filter & Q(status='partially_returned')
            ).aggregate(total=Sum('partially_ammount'))['total'] or 0
            
            total_sales = delivered_shipped_sales + partially_returned_sales
            
            # Total Orders Count
            orders_count = Order.objects.filter(date_filter).count()
            
            # Calculate Total Expenses
            dashboard_expenses = Expense.objects.filter(
                Q(created_at__gte=start_date) if start_date else Q()
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            courier_expenses = Order.objects.filter(
                date_filter & Q(status__in=['delivered', 'shipped', 'returned', 'partially_returned'])
            ).aggregate(total=Sum('curier_charge'))['total'] or 0
            
            total_expenses = dashboard_expenses + courier_expenses
            
            # Calculate Product Cost (only for delivered and shipped orders)
            delivered_shipped_orders = Order.objects.filter(
                date_filter & Q(status__in=['delivered', 'shipped'])
            )
            
            total_product_cost = Decimal('0')
            for order in delivered_shipped_orders:
                if order.cost_price:
                    # Use stored cost_price if available
                    total_product_cost += order.cost_price
                else:
                    # Calculate from order items if cost_price is not stored
                    for item in order.items.all():
                        if item.variant and item.variant.effective_cost_price:
                            total_product_cost += item.variant.effective_cost_price * item.quantity
                        elif item.product and item.product.cost_price:
                            total_product_cost += item.product.cost_price * item.quantity
            
            # Calculate Total Revenue (Total Sales - (Expenses + Product Cost))
            total_revenue = total_sales - (total_expenses + total_product_cost)
            
            # Calculate profit margin percentage
            profit_margin = 0
            if total_sales > 0:
                profit_margin = (total_revenue / total_sales) * 100
            
            products_count = Product.objects.filter(is_active=True).count()
            customers_count = User.objects.filter(is_active=True).count()
            
            # Calculate orders by status breakdown
            orders_by_status = Order.objects.filter(date_filter).values('status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Normalize status values and consolidate duplicates (e.g., "Pending" and "pending")
            status_consolidation = {}
            for status_data in orders_by_status:
                normalized_status = status_data['status'].lower()
                if normalized_status in status_consolidation:
                    status_consolidation[normalized_status] += status_data['count']
                else:
                    status_consolidation[normalized_status] = status_data['count']
            
            # Convert to list format for frontend
            orders_status_list = [
                {
                    'status': status,
                    'count': count
                }
                for status, count in sorted(status_consolidation.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Prepare response data with simple defaults for now
            data = {
                'total_sales': float(total_sales),
                'orders_count': orders_count,
                'total_expenses': float(total_expenses),
                'dashboard_expenses': float(dashboard_expenses),
                'courier_expenses': float(courier_expenses),
                'total_product_cost': float(total_product_cost),
                'total_revenue': float(total_revenue),
                'profit_margin': round(profit_margin, 2),
                'products_count': products_count,
                'customers_count': customers_count,
                'recent_orders': [],
                'popular_products': [],
                'sales_by_period': [],
                'sales_by_category': [],
                'orders_by_status': orders_status_list,
                'analytics': {},
                'recommendations': []
            }
            
            return Response(data)
            
        except Exception as e:
            print(f"Error in statistics view: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

class OrderStatusBreakdownView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Check if user is staff (admin user)
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=403)
        
        try:
            # Get query parameters for date filtering
            period = request.GET.get('period', 'week')
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            
            # Build date filter based on parameters
            date_filter = Q()
            
            if date_from and date_to:
                # Use custom date range if provided
                from datetime import datetime
                try:
                    start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                    end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                    date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
                except ValueError:
                    return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
            else:
                # Use period-based filtering as fallback
                now = timezone.now()
                if period == 'day':
                    start_date = now - timedelta(days=1)
                elif period == 'month':
                    start_date = now - timedelta(days=30)
                elif period == 'year':
                    start_date = now - timedelta(days=365)
                elif period == 'all':
                    start_date = None
                else:  # default to week
                    start_date = now - timedelta(days=7)
                
                if start_date:
                    date_filter = Q(created_at__gte=start_date)
            
            # Calculate orders by status breakdown
            orders_by_status = Order.objects.filter(date_filter).values('status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Normalize status values and consolidate duplicates
            status_consolidation = {}
            for status_data in orders_by_status:
                normalized_status = status_data['status'].lower()
                if normalized_status in status_consolidation:
                    status_consolidation[normalized_status] += status_data['count']
                else:
                    status_consolidation[normalized_status] = status_data['count']
            
            # Convert to list format for frontend
            orders_status_list = [
                {
                    'status': status,
                    'count': count
                }
                for status, count in sorted(status_consolidation.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Prepare response data
            data = {
                'orders_by_status': orders_status_list,
                'total_orders': sum(status_consolidation.values()),
                'date_range': {
                    'from': date_from,
                    'to': date_to,
                    'period': period
                }
            }
            
            return Response(data)
            
        except Exception as e:
            print(f"Error in order status breakdown view: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

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

@login_required
@user_passes_test(is_admin)
def dashboard_expenses(request):
    context = {
        'active_page': 'expenses'
    }
    return render(request, 'dashboard/expenses.html', context)

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


@api_view(['POST'])
@permission_classes([IsAdminUser])
def fraud_check_api(request):
    """
    API endpoint for fraud checking in dashboard
    """
    try:
        import json
        from fraud_checker.combined_service import CombinedFraudChecker
        
        phone_number = request.data.get('phone_number', '').strip()
        
        if not phone_number:
            return Response({
                'success': False,
                'error': 'Phone number is required'
            }, status=400)
        
        # Initialize combined fraud checker service
        fraud_service = CombinedFraudChecker()
        
        # Perform fraud check across all couriers
        result = fraud_service.check_fraud_all_couriers(phone_number)
        
        return Response(result)
        
    except Exception as e:
        print(f"Dashboard fraud check API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

class ExpenseDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expenses in the dashboard."""
    queryset = Expense.objects.all()
    serializer_class = ExpenseDashboardSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Expense.objects.all()
        
        # Filter by expense type
        expense_type = self.request.query_params.get('expense_type')
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Filter by month and year
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month:
            queryset = queryset.filter(created_at__month=month)
        if year:
            queryset = queryset.filter(created_at__year=year)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # Log admin activity
        expense = serializer.save(created_by=self.request.user)
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='CREATE',
                model_name='Expense',
                object_id=expense.id,
                object_repr=str(expense),
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Could not log admin activity: {e}")
    
    def perform_update(self, serializer):
        # Log admin activity
        old_instance = self.get_object()
        expense = serializer.save()
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='UPDATE',
                model_name='Expense',
                object_id=expense.id,
                object_repr=str(expense),
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Could not log admin activity: {e}")
    
    def perform_destroy(self, instance):
        # Log admin activity
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='DELETE',
                model_name='Expense',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        except Exception as e:
            # Handle database errors, particularly if the AdminActivity table doesn't exist
            print(f"Could not log admin activity: {e}")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get expense statistics for charts and reports."""
        queryset = self.get_queryset()
        
        # Total expenses
        total_expenses = queryset.aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly expenses for the last 12 months
        from django.utils import timezone
        from datetime import datetime, timedelta
        import calendar
        
        now = timezone.now()
        monthly_expenses = []
        
        for i in range(12):
            month_date = now.replace(day=1) - timedelta(days=30*i)
            month_expenses = queryset.filter(
                created_at__year=month_date.year,
                created_at__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_expenses.insert(0, {
                'month': calendar.month_name[month_date.month],
                'year': month_date.year,
                'total': float(month_expenses),
                'date': f"{month_date.year}-{month_date.month:02d}"
            })
        
        # Expenses by type for pie chart
        expense_by_type = []
        expense_types = Expense.EXPENSE_TYPE_CHOICES
        
        for expense_type, display_name in expense_types:
            type_total = queryset.filter(expense_type=expense_type).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            if type_total > 0:
                expense_by_type.append({
                    'type': expense_type,
                    'name': display_name,
                    'total': float(type_total),
                    'percentage': round((float(type_total) / float(total_expenses)) * 100, 2) if total_expenses > 0 else 0
                })
        
        return Response({
            'total_expenses': float(total_expenses),
            'monthly_expenses': monthly_expenses,
            'expense_by_type': expense_by_type,
            'total_count': queryset.count()
        })


class ProductPerformanceView(APIView):
    """
    API endpoint for detailed product performance data with filtering and sorting
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Check if user is staff (admin user)
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=403)
        
        try:
            # Get query parameters
            period = request.query_params.get('period', 'all')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            search = request.query_params.get('search', '').strip()
            sort_by = request.query_params.get('sort', 'orders')
            sort_order = request.query_params.get('order', 'desc')
            
            # Define time periods if no specific dates provided
            now = timezone.now()
            if not date_from and not date_to:
                if period == 'day':
                    start_date = now - timedelta(days=1)
                elif period == 'week':
                    start_date = now - timedelta(days=7)
                elif period == 'month':
                    start_date = now - timedelta(days=30)
                elif period == 'year':
                    start_date = now - timedelta(days=365)
                else:  # 'all'
                    start_date = None
            else:
                start_date = None
            
            # Build date filter for orders
            order_date_filter = Q()
            if date_from:
                try:
                    from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                    order_date_filter &= Q(created_at__date__gte=from_date)
                except ValueError:
                    pass
                    
            if date_to:
                try:
                    to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                    order_date_filter &= Q(created_at__date__lte=to_date)
                except ValueError:
                    pass
                    
            if start_date and not (date_from or date_to):
                order_date_filter = Q(created_at__gte=start_date)
            
            # Get all active products
            products_query = Product.objects.filter(is_active=True)
            
            # Apply search filter
            if search:
                products_query = products_query.filter(
                    Q(name__icontains=search) | 
                    Q(category__name__icontains=search)
                )
            
            products_data = []
            
            for product in products_query:
                # Get all orders for this product within date range
                product_orders = Order.objects.filter(
                    order_date_filter,
                    items__product=product
                ).distinct()
                
                # Count total orders
                orders_count = product_orders.count()
                
                # Calculate delivered quantity
                delivered_orders = product_orders.filter(status__in=['delivered', 'shipped'])
                delivered_quantity = OrderItem.objects.filter(
                    order__in=delivered_orders,
                    product=product
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # Calculate revenue (from delivered and shipped orders + partial returns)
                delivered_shipped_revenue = Order.objects.filter(
                    order_date_filter &
                    Q(status__in=['delivered', 'shipped']) &
                    Q(items__product=product)
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                partial_return_revenue = Order.objects.filter(
                    order_date_filter &
                    Q(status='partially_returned') &
                    Q(items__product=product)
                ).aggregate(total=Sum('partially_ammount'))['total'] or 0
                
                total_revenue = delivered_shipped_revenue + partial_return_revenue
                
                # Get category name
                category_name = product.category.name if product.category else 'Uncategorized'
                
                # Get product image URL
                image_url = None
                if hasattr(product, 'images') and product.images.exists():
                    first_image = product.images.first()
                    if first_image and first_image.image:
                        image_url = first_image.image.url
                elif hasattr(product, 'productimage_set') and product.productimage_set.exists():
                    first_image = product.productimage_set.first()
                    if first_image and first_image.image:
                        image_url = first_image.image.url
                
                product_data = {
                    'id': product.id,
                    'product_name': product.name,
                    'category': category_name,
                    'orders': orders_count,
                    'delivered_quantity': int(delivered_quantity),
                    'revenue': float(total_revenue),
                    'price': float(product.price) if product.price else 0,
                    'cost_price': float(product.cost_price) if product.cost_price else 0,
                    'stock': product.stock_quantity if hasattr(product, 'stock_quantity') else 0,
                    'image_url': image_url
                }
                
                products_data.append(product_data)
            
            # Sort the data
            reverse_sort = sort_order.lower() == 'desc'
            
            if sort_by == 'name':
                products_data.sort(key=lambda x: x['product_name'].lower(), reverse=reverse_sort)
            elif sort_by == 'orders':
                products_data.sort(key=lambda x: x['orders'], reverse=reverse_sort)
            elif sort_by == 'delivered':
                products_data.sort(key=lambda x: x['delivered_quantity'], reverse=reverse_sort)
            elif sort_by == 'revenue':
                products_data.sort(key=lambda x: x['revenue'], reverse=reverse_sort)
            else:
                products_data.sort(key=lambda x: x['orders'], reverse=reverse_sort)
            
            return Response({
                'products': products_data,
                'total_count': len(products_data),
                'filters': {
                    'period': period,
                    'date_from': date_from,
                    'date_to': date_to,
                    'search': search,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to load product performance data',
                'detail': str(e)
            }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_products_performance(request):
    """
    Export product performance data as CSV
    """
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        import csv
        from django.http import HttpResponse
        
        # Get the same data as the API
        view = ProductPerformanceView()
        view.request = request
        response_data = view.get(request).data
        
        if 'error' in response_data:
            return Response(response_data, status=500)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products_performance.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Product Name',
            'Category', 
            'Total Orders',
            'Delivered Quantity',
            'Revenue ($)',
            'Price ($)',
            'Cost Price ($)',
            'Stock'
        ])
        
        # Write data rows
        for product in response_data['products']:
            writer.writerow([
                product['product_name'],
                product['category'],
                product['orders'],
                product['delivered_quantity'],
                f"{product['revenue']:.2f}",
                f"{product['price']:.2f}",
                f"{product['cost_price']:.2f}",
                product['stock']
            ])
        
        return response
        
    except Exception as e:
        return Response({
            'error': 'Failed to export data',
            'detail': str(e)
        }, status=500)
