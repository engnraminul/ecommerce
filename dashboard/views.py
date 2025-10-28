from django.shortcuts import render
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import JsonResponse
from decimal import Decimal
from django.db import transaction

from .models import DashboardSetting, AdminActivity, Expense
from .serializers import (
    DashboardSettingSerializer, AdminActivitySerializer, UserDashboardSerializer,
    CategoryDashboardSerializer, ProductDashboardSerializer, ProductDetailSerializer, ProductVariantDashboardSerializer,
    ProductImageDashboardSerializer, OrderDashboardSerializer, OrderItemDashboardSerializer, DashboardStatisticsSerializer,
    ShippingAddressDashboardSerializer, ExpenseDashboardSerializer
)
from products.models import Product, ProductVariant, ProductImage, Category
from orders.models import Order, OrderItem
from incomplete_orders.models import IncompleteOrder, IncompleteOrderItem, IncompleteShippingAddress
from users.models import User
from settings.models import CheckoutCustomization, SiteSettings

# Helper functions for stock management
def restock_order_items(order):
    """Restore stock for all items in an order"""
    try:
        for item in order.items.all():
            if item.variant:
                # Restore stock to variant
                item.variant.stock_quantity += item.quantity
                item.variant.save()
                print(f"Restocked {item.quantity} units to variant {item.variant.sku}")
            elif hasattr(item.product, 'stock_quantity'):
                # Restore stock to product
                item.product.stock_quantity += item.quantity
                item.product.save()
                print(f"Restocked {item.quantity} units to product {item.product.sku}")
    except Exception as e:
        print(f"Error restocking order {order.order_number}: {str(e)}")

def reduce_order_stock(order):
    """Reduce stock for all items in an order"""
    try:
        for item in order.items.all():
            if item.variant:
                # Reduce stock from variant
                if item.variant.stock_quantity >= item.quantity:
                    item.variant.stock_quantity -= item.quantity
                    item.variant.save()
                    print(f"Reduced {item.quantity} units from variant {item.variant.sku}")
                else:
                    print(f"Warning: Insufficient stock for variant {item.variant.sku}")
            elif hasattr(item.product, 'stock_quantity'):
                # Reduce stock from product
                if item.product.stock_quantity >= item.quantity:
                    item.product.stock_quantity -= item.quantity
                    item.product.save()
                    print(f"Reduced {item.quantity} units from product {item.product.sku}")
                else:
                    print(f"Warning: Insufficient stock for product {item.product.sku}")
    except Exception as e:
        print(f"Error reducing stock for order {order.order_number}: {str(e)}")

def should_restock_status(status):
    """Check if a status change should trigger restocking"""
    return status.lower() in ['cancelled', 'returned', 'partially_returned']

def should_reduce_stock_status(status):
    """Check if a status change should trigger stock reduction"""
    return status.lower() in ['pending', 'confirmed', 'processing', 'shipped', 'delivered']

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
    queryset = Category.objects.all().select_related('parent').order_by('name')
    serializer_class = CategoryDashboardSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Handle parent__isnull filter for root categories
        parent_isnull = self.request.query_params.get('parent__isnull')
        if parent_isnull and parent_isnull.lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset
    
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
    
    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """Get all variants for a specific product"""
        product = self.get_object()
        variants = ProductVariant.objects.filter(product=product, is_active=True)
        serializer = ProductVariantDashboardSerializer(variants, many=True)
        return Response(serializer.data)

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
    
    @action(detail=True, methods=['post'])
    def remove_image(self, request, pk=None):
        """Remove the variant image"""
        variant = self.get_object()
        
        if variant.image:
            # Delete the image file
            variant.image.delete(save=False)
            variant.image = None
            variant.save(update_fields=['image'])
            
            try:
                self.log_activity('removed_image', variant)
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'Variant image removed successfully'
            })
        else:
            return Response({
                'success': False,
                'message': 'Variant has no image to remove'
            }, status=400)
    
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
        # The serializer now handles both file uploads and media library URLs
        # No special processing needed here
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


class StockDashboardViewSet(viewsets.ModelViewSet):
    """
    Stock management ViewSet for products and variants
    """
    queryset = Product.objects.select_related('category').prefetch_related('variants').filter(track_inventory=True)
    permission_classes = [IsAdminUser]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'stock_quantity', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        from .serializers import StockManagementSerializer
        return StockManagementSerializer
    
    def get_queryset(self):
        """Enhanced queryset with search functionality"""
        queryset = super().get_queryset()
        
        # Search by name or SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(stock_quantity__lte=F('low_stock_threshold'))
        
        # Filter by out of stock
        out_of_stock = self.request.query_params.get('out_of_stock')
        if out_of_stock == 'true':
            queryset = queryset.filter(stock_quantity=0)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """
        Professional stock adjustment with activity tracking
        Uses "Stock In" and "Stock Out" terminology with comprehensive logging
        """
        from inventory.services import StockActivityService
        
        try:
            product = self.get_object()
            action_type = request.data.get('action')  # 'stock_in' or 'stock_out'
            quantity = int(request.data.get('quantity', 0))
            reason = request.data.get('reason', '')
            variant_id = request.data.get('variant_id')  # Optional: specific variant
            unit_cost = request.data.get('unit_cost')
            reference_number = request.data.get('reference_number', '')
            notes = request.data.get('notes', '')
            
            if quantity <= 0:
                return Response({'error': 'Quantity must be positive'}, status=400)
            
            if action_type not in ['stock_in', 'stock_out']:
                return Response({'error': 'Invalid action type. Use "stock_in" or "stock_out"'}, status=400)
            
            # Convert unit_cost to Decimal if provided
            if unit_cost:
                try:
                    unit_cost = Decimal(str(unit_cost))
                except (ValueError, TypeError):
                    unit_cost = None
            
            # Check if product has variants
            active_variants = product.variants.filter(is_active=True)
            
            if active_variants.exists():
                if not variant_id:
                    # Return variant information for user to choose
                    variants_data = []
                    for variant in active_variants:
                        variants_data.append({
                            'id': variant.id,
                            'name': variant.name,
                            'sku': variant.sku,
                            'current_stock': variant.stock_quantity,
                            'cost_price': float(variant.effective_cost_price or 0)
                        })
                    
                    return Response({
                        'has_variants': True,
                        'message': 'This product has variants. Please specify which variant to adjust.',
                        'variants': variants_data
                    }, status=400)
                
                # Adjust specific variant
                try:
                    variant = active_variants.get(id=variant_id)
                    
                    # Use StockActivityService for professional tracking
                    if action_type == 'stock_in':
                        activity = StockActivityService.stock_in(
                            item=variant,
                            quantity=quantity,
                            reason=reason,
                            user=request.user,
                            request=request,
                            unit_cost=unit_cost,
                            reference_number=reference_number,
                            notes=notes
                        )
                        action_display = "increased"
                    else:  # stock_out
                        activity = StockActivityService.stock_out(
                            item=variant,
                            quantity=quantity,
                            reason=reason,
                            user=request.user,
                            request=request,
                            reference_number=reference_number,
                            notes=notes
                        )
                        action_display = "decreased"
                    
                    return Response({
                        'success': True,
                        'variant_adjusted': True,
                        'variant_name': variant.name,
                        'new_stock': variant.stock_quantity,
                        'old_stock': activity.quantity_before,
                        'action': action_type,
                        'action_display': action_display,
                        'quantity': quantity,
                        'activity_id': activity.id,
                        'total_cost': float(activity.total_cost) if activity.total_cost else None
                    })
                    
                except ProductVariant.DoesNotExist:
                    return Response({'error': 'Variant not found'}, status=400)
                except ValueError as e:
                    return Response({'error': str(e)}, status=400)
            
            else:
                # Product has no variants - adjust product stock
                try:
                    if action_type == 'stock_in':
                        activity = StockActivityService.stock_in(
                            item=product,
                            quantity=quantity,
                            reason=reason,
                            user=request.user,
                            request=request,
                            unit_cost=unit_cost,
                            reference_number=reference_number,
                            notes=notes
                        )
                        action_display = "increased"
                    else:  # stock_out
                        activity = StockActivityService.stock_out(
                            item=product,
                            quantity=quantity,
                            reason=reason,
                            user=request.user,
                            request=request,
                            reference_number=reference_number,
                            notes=notes
                        )
                        action_display = "decreased"
                    
                    return Response({
                        'success': True,
                        'variant_adjusted': False,
                        'new_stock': product.stock_quantity,
                        'old_stock': activity.quantity_before,
                        'action': action_type,
                        'action_display': action_display,
                        'quantity': quantity,
                        'activity_id': activity.id,
                        'total_cost': float(activity.total_cost) if activity.total_cost else None
                    })
                
                except ValueError as e:
                    return Response({'error': str(e)}, status=400)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """Get stock summary statistics with intelligent variant handling"""
        try:
            total_products = Product.objects.filter(track_inventory=True).count()
            
            # Calculate statistics considering variants
            low_stock_products = 0
            out_of_stock_products = 0
            total_stock_value = 0
            
            for product in Product.objects.filter(track_inventory=True).prefetch_related('variants'):
                variants = product.variants.filter(is_active=True)
                
                if variants.exists():
                    # Product has variants - check variant stock
                    variant_stocks = [v.stock_quantity for v in variants]
                    total_variant_stock = sum(variant_stocks)
                    
                    # Check if any variant is low stock
                    if any(stock <= product.low_stock_threshold for stock in variant_stocks):
                        low_stock_products += 1
                    
                    # Check if all variants are out of stock
                    if total_variant_stock == 0:
                        out_of_stock_products += 1
                    
                    # Calculate variant stock value
                    for variant in variants:
                        cost_price = variant.effective_cost_price
                        if cost_price:
                            total_stock_value += variant.stock_quantity * cost_price
                else:
                    # Product has no variants - use product stock
                    if product.stock_quantity <= product.low_stock_threshold:
                        low_stock_products += 1
                    
                    if product.stock_quantity == 0:
                        out_of_stock_products += 1
                    
                    # Calculate product stock value
                    if product.cost_price:
                        total_stock_value += product.stock_quantity * product.cost_price
            
            return Response({
                'total_products': total_products,
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products,
                'total_stock_value': float(total_stock_value)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=False, methods=['post'])
    def bulk_adjust(self, request):
        """Bulk stock adjustment for multiple products"""
        try:
            adjustments = request.data.get('adjustments', [])
            if not adjustments:
                return Response({'error': 'No adjustments provided'}, status=400)
            
            results = []
            success_count = 0
            error_count = 0
            
            for adjustment in adjustments:
                try:
                    product_id = adjustment.get('product_id')
                    action = adjustment.get('action')  # 'increase' or 'decrease'
                    quantity = int(adjustment.get('quantity', 0))
                    reason = adjustment.get('reason', 'Bulk adjustment')
                    
                    if quantity <= 0:
                        results.append({
                            'product_id': product_id,
                            'success': False,
                            'error': 'Quantity must be positive'
                        })
                        error_count += 1
                        continue
                    
                    product = Product.objects.get(id=product_id, track_inventory=True)
                    old_stock = product.stock_quantity
                    
                    if action == 'increase':
                        product.stock_quantity += quantity
                    elif action == 'decrease':
                        if product.stock_quantity < quantity:
                            results.append({
                                'product_id': product_id,
                                'success': False,
                                'error': 'Insufficient stock'
                            })
                            error_count += 1
                            continue
                        product.stock_quantity -= quantity
                    else:
                        results.append({
                            'product_id': product_id,
                            'success': False,
                            'error': 'Invalid action type'
                        })
                        error_count += 1
                        continue
                    
                    product.save()
                    
                    # Log the activity
                    try:
                        AdminActivity.objects.create(
                            user=request.user,
                            action=f'bulk_stock_{action}',
                            model_name='Product',
                            object_id=product.id,
                            object_repr=f"{product.name}: {old_stock} → {product.stock_quantity} ({reason})",
                            ip_address=self.get_client_ip(),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                    except Exception as e:
                        print(f"Error logging activity: {str(e)}")
                    
                    results.append({
                        'product_id': product_id,
                        'success': True,
                        'old_stock': old_stock,
                        'new_stock': product.stock_quantity,
                        'action': action,
                        'quantity': quantity
                    })
                    success_count += 1
                    
                except Product.DoesNotExist:
                    results.append({
                        'product_id': product_id,
                        'success': False,
                        'error': 'Product not found'
                    })
                    error_count += 1
                except Exception as e:
                    results.append({
                        'product_id': product_id,
                        'success': False,
                        'error': str(e)
                    })
                    error_count += 1
            
            return Response({
                'success': True,
                'results': results,
                'summary': {
                    'total': len(adjustments),
                    'success': success_count,
                    'errors': error_count
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=False, methods=['get'])
    def low_stock_report(self, request):
        """Get detailed low stock report"""
        try:
            low_stock_products = Product.objects.filter(
                track_inventory=True,
                stock_quantity__lte=F('low_stock_threshold')
            ).select_related('category').order_by('stock_quantity')
            
            serializer = self.get_serializer(low_stock_products, many=True)
            return Response({
                'count': low_stock_products.count(),
                'products': serializer.data
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=False, methods=['get'])
    def export_stock_report(self, request):
        """Export intelligent stock report as CSV"""
        try:
            import csv
            from django.http import HttpResponse
            from io import StringIO
            
            # Create CSV content
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Product Name', 'SKU', 'Category', 'Stock Management Type',
                'Effective Stock', 'Effective Cost Price (৳)', 'Stock Value (৳)', 
                'Low Stock Threshold', 'Stock Status', 'Variants Count'
            ])
            
            # Get products
            products = self.get_queryset().prefetch_related('variants')
            for product in products:
                variants = product.variants.filter(is_active=True)
                
                if variants.exists():
                    # Product has variants
                    total_stock = sum(v.stock_quantity for v in variants)
                    total_value = sum(
                        v.stock_quantity * (v.effective_cost_price or 0) 
                        for v in variants
                    )
                    avg_cost = total_value / total_stock if total_stock > 0 else 0
                    
                    stock_status = 'Out of Stock' if total_stock == 0 else (
                        'Low Stock' if any(v.stock_quantity <= product.low_stock_threshold for v in variants) 
                        else 'In Stock'
                    )
                    
                    writer.writerow([
                        product.name,
                        product.sku or '',
                        product.category.name if product.category else '',
                        'Variant Level',
                        total_stock,
                        round(avg_cost, 2),
                        round(total_value, 2),
                        product.low_stock_threshold,
                        stock_status,
                        variants.count()
                    ])
                    
                    # Add individual variant rows
                    for variant in variants:
                        variant_value = variant.stock_quantity * (variant.effective_cost_price or 0)
                        variant_status = 'Out of Stock' if variant.stock_quantity == 0 else (
                            'Low Stock' if variant.stock_quantity <= product.low_stock_threshold 
                            else 'In Stock'
                        )
                        
                        writer.writerow([
                            f"  └─ {variant.name}",
                            variant.sku or '',
                            '',
                            'Variant',
                            variant.stock_quantity,
                            variant.effective_cost_price or 0,
                            round(variant_value, 2),
                            product.low_stock_threshold,
                            variant_status,
                            ''
                        ])
                else:
                    # Product has no variants
                    stock_status = 'Out of Stock' if product.stock_quantity == 0 else (
                        'Low Stock' if product.stock_quantity <= product.low_stock_threshold 
                        else 'In Stock'
                    )
                    stock_value = product.stock_quantity * (product.cost_price or 0)
                    
                    writer.writerow([
                        product.name,
                        product.sku or '',
                        product.category.name if product.category else '',
                        'Product Level',
                        product.stock_quantity,
                        product.cost_price or 0,
                        round(stock_value, 2),
                        product.low_stock_threshold,
                        stock_status,
                        0
                    ])
            
            # Create response
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="intelligent_stock_report.csv"'
            return response
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['get'])
    def stock_activity_history(self, request, pk=None):
        """Get stock activity history for a product"""
        from inventory.services import StockActivityService
        from inventory.models import StockActivity
        
        try:
            product = self.get_object()
            limit = int(request.query_params.get('limit', 50))
            activity_type = request.query_params.get('activity_type', None)
            
            # Get activities for this product
            activities = StockActivityService.get_item_stock_history(
                item=product,
                limit=limit,
                activity_type=activity_type
            )
            
            # Also get activities for variants
            variant_activities = []
            for variant in product.variants.filter(is_active=True):
                variant_activities.extend(
                    StockActivityService.get_item_stock_history(
                        item=variant,
                        limit=limit,
                        activity_type=activity_type
                    )
                )
            
            # Combine and sort by date
            all_activities = activities + variant_activities
            all_activities.sort(key=lambda x: x.activity_date, reverse=True)
            
            # Format response
            activities_data = []
            for activity in all_activities[:limit]:
                activities_data.append({
                    'id': activity.id,
                    'activity_type': activity.activity_type,
                    'activity_type_display': activity.get_activity_type_display(),
                    'item_type': 'Product' if activity.is_product else 'Variant',
                    'item_name': activity.item_name,
                    'variant_name': activity.variant_name,
                    'quantity_before': activity.quantity_before,
                    'quantity_changed': activity.quantity_changed,
                    'quantity_after': activity.quantity_after,
                    'unit_cost': float(activity.unit_cost) if activity.unit_cost else None,
                    'total_cost': float(activity.total_cost) if activity.total_cost else None,
                    'reason': activity.reason,
                    'reference_number': activity.reference_number,
                    'notes': activity.notes,
                    'created_by': activity.created_by.username,
                    'activity_date': activity.activity_date.isoformat(),
                    'created_at': activity.created_at.isoformat(),
                    'status': activity.status,
                    'batch_number': activity.batch.batch_number if activity.batch else None
                })
            
            return Response({
                'count': len(activities_data),
                'activities': activities_data
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


class StockVariantDashboardViewSet(viewsets.ModelViewSet):
    """
    Stock management ViewSet for product variants
    """
    queryset = ProductVariant.objects.select_related('product').all()
    permission_classes = [IsAdminUser]
    filterset_fields = ['product', 'is_active']
    search_fields = ['name', 'sku', 'product__name']
    ordering_fields = ['name', 'stock_quantity', 'created_at']
    ordering = ['product__name', 'name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        from .serializers import StockVariantManagementSerializer
        return StockVariantManagementSerializer
    
    def get_queryset(self):
        """Enhanced queryset with search functionality"""
        queryset = super().get_queryset()
        
        # Filter by product if specified
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Search by name, SKU, or product name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(product__name__icontains=search)
            )
        
        # Filter by low stock (using product's threshold)
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(stock_quantity__lte=F('product__low_stock_threshold'))
        
        # Filter by out of stock
        out_of_stock = self.request.query_params.get('out_of_stock')
        if out_of_stock == 'true':
            queryset = queryset.filter(stock_quantity=0)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """Professional variant stock adjustment with activity tracking"""
        from inventory.services import StockActivityService
        
        try:
            variant = self.get_object()
            action_type = request.data.get('action')  # 'stock_in' or 'stock_out'
            quantity = int(request.data.get('quantity', 0))
            reason = request.data.get('reason', '')
            unit_cost = request.data.get('unit_cost')
            reference_number = request.data.get('reference_number', '')
            notes = request.data.get('notes', '')
            
            if quantity <= 0:
                return Response({'error': 'Quantity must be positive'}, status=400)
            
            if action_type not in ['stock_in', 'stock_out']:
                return Response({'error': 'Invalid action type. Use "stock_in" or "stock_out"'}, status=400)
            
            # Convert unit_cost to Decimal if provided
            if unit_cost:
                try:
                    unit_cost = Decimal(str(unit_cost))
                except (ValueError, TypeError):
                    unit_cost = None
            
            # Use StockActivityService for professional tracking
            try:
                if action_type == 'stock_in':
                    activity = StockActivityService.stock_in(
                        item=variant,
                        quantity=quantity,
                        reason=reason,
                        user=request.user,
                        request=request,
                        unit_cost=unit_cost,
                        reference_number=reference_number,
                        notes=notes
                    )
                    action_display = "increased"
                else:  # stock_out
                    activity = StockActivityService.stock_out(
                        item=variant,
                        quantity=quantity,
                        reason=reason,
                        user=request.user,
                        request=request,
                        reference_number=reference_number,
                        notes=notes
                    )
                    action_display = "decreased"
                
                return Response({
                    'success': True,
                    'new_stock': variant.stock_quantity,
                    'old_stock': activity.quantity_before,
                    'action': action_type,
                    'action_display': action_display,
                    'quantity': quantity,
                    'activity_id': activity.id,
                    'total_cost': float(activity.total_cost) if activity.total_cost else None
                })
                
            except ValueError as e:
                return Response({'error': str(e)}, status=400)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
            
            variant.save()
            
            # Log the activity
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action=f'variant_stock_{action_type}',
                    model_name='ProductVariant',
                    object_id=variant.id,
                    object_repr=f"{variant.product.name} - {variant.name}: {old_stock} → {variant.stock_quantity} ({reason})",
                    ip_address=self.get_client_ip(),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return Response({
                'success': True,
                'new_stock': variant.stock_quantity,
                'old_stock': old_stock,
                'action': action_type,
                'quantity': quantity
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
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
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_address__first_name', 'shipping_address__last_name', 'shipping_address__phone']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Enhanced queryset with better search and filtering"""
        queryset = Order.objects.select_related(
            'user', 'shipping_address'
        ).prefetch_related('items__product')
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(shipping_address__first_name__icontains=search) |
                Q(shipping_address__last_name__icontains=search) |
                Q(shipping_address__phone__icontains=search) |
                Q(shipping_address__email__icontains=search) |
                Q(customer_phone__icontains=search) |
                Q(guest_email__icontains=search)
            )
        
        # Date filtering
        created_at_gte = self.request.query_params.get('created_at__date__gte')
        created_at_lte = self.request.query_params.get('created_at__date__lte')
        
        if created_at_gte:
            try:
                from datetime import datetime
                start_date = datetime.strptime(created_at_gte, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__gte=start_date.date())
            except ValueError:
                pass  # Ignore invalid date format
        
        if created_at_lte:
            try:
                from datetime import datetime
                end_date = datetime.strptime(created_at_lte, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__lte=end_date.date())
            except ValueError:
                pass  # Ignore invalid date format
        
        # Status filtering
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Courier date filtering
        courier_date_filter = self.request.query_params.get('courier_date')
        if courier_date_filter == 'today':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(curier_date=today)
        elif courier_date_filter:
            try:
                from datetime import datetime
                courier_date = datetime.strptime(courier_date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(curier_date=courier_date)
            except ValueError:
                pass  # Ignore invalid date format
        
        # Count by status feature
        count_by_status = self.request.query_params.get('count_by_status')
        if count_by_status:
            # This is handled in the list method below
            pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Enhanced list method with status counts"""
        # Check if this is a count_by_status request
        count_by_status = request.query_params.get('count_by_status')
        if count_by_status:
            # Return status counts
            from django.db.models import Count
            from django.utils import timezone
            
            # Get all orders and count by status
            status_counts = {}
            total_count = 0
            
            # Count each status
            all_orders = Order.objects.all()
            status_counts = dict(all_orders.values('status').annotate(count=Count('status')).values_list('status', 'count'))
            total_count = all_orders.count()
            
            # Count today's courier orders
            today = timezone.now().date()
            courier_today_count = Order.objects.filter(curier_date=today).count()
            status_counts['courier_today'] = courier_today_count
            
            return Response({
                'status_counts': status_counts,
                'total_count': total_count
            })
        
        # Include shipping address in serialization
        include_shipping = request.query_params.get('include_shipping_address')
        if include_shipping:
            # Override the serializer context to include shipping address
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                # Use enhanced serializer
                orders_data = []
                for order in page:
                    # Get shipping address data
                    shipping_address = None
                    if hasattr(order, 'shipping_address') and order.shipping_address:
                        shipping_address = {
                            'first_name': order.shipping_address.first_name,
                            'last_name': order.shipping_address.last_name,
                            'phone': order.shipping_address.phone,
                            'email': order.shipping_address.email,
                            'address_line_1': order.shipping_address.address_line_1,
                            'address_line_2': order.shipping_address.address_line_2,
                            'city': order.shipping_address.city,
                            'state': order.shipping_address.state,
                            'postal_code': order.shipping_address.postal_code,
                            'country': order.shipping_address.country,
                        }
                    
                    orders_data.append({
                        'id': order.id,
                        'order_number': order.order_number,
                        'created_at': order.created_at.isoformat(),
                        'status': order.status,
                        'payment_status': order.payment_status,
                        'total_amount': str(order.total_amount),
                        'items_count': order.items.count(),
                        'user': {
                            'id': order.user.id if order.user else None,
                            'username': order.user.username if order.user else None,
                            'email': order.user.email if order.user else order.guest_email,
                            'first_name': order.user.first_name if order.user else None,
                            'last_name': order.user.last_name if order.user else None,
                        } if order.user else None,
                        'shipping_address': shipping_address,
                        'customer_phone': order.customer_phone,
                        'guest_email': order.guest_email,
                        'curier_id': order.curier_id,
                        'curier_status': order.curier_status,
                        'curier_date': order.curier_date.isoformat() if order.curier_date else None,
                    })
                
                return self.get_paginated_response(orders_data)
        
        # Default behavior
        return super().list(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_destroy(self, instance):
        try:
            # Restock items before deleting the order
            print(f"Restocking items for order {instance.order_number} before deletion")
            restock_order_items(instance)
            
            self.log_activity('deleted', instance)
        except Exception as e:
            # Log the error but continue with deletion
            print(f"Error logging activity or restocking: {str(e)}")
        
        # Proceed with deletion even if logging/restocking fails
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
    @transaction.atomic
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            from rest_framework import status as http_status
            return Response({'error': 'Status is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        
        # Store the old status for stock management
        old_status = order.status
        
        # Handle stock management based on status change
        if old_status != new_status:
            print(f"Order {order.order_number}: Status changing from {old_status} to {new_status}")
            
            # If changing FROM cancelled TO active status, reduce stock
            if should_restock_status(old_status) and should_reduce_stock_status(new_status):
                print(f"Order {order.order_number}: Changing from {old_status} to {new_status} - reducing stock")
                reduce_order_stock(order)
            
            # If changing TO cancelled FROM active status, restock
            elif should_reduce_stock_status(old_status) and should_restock_status(new_status):
                print(f"Order {order.order_number}: Changing from {old_status} to {new_status} - restocking")
                restock_order_items(order)
        
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
                
            activity_details = f"Updated status from {old_status} to {new_status}"
            if additional_info:
                activity_details += f" with {additional_info}"
                
            self.log_activity(activity_details, order)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        return Response({'success': True, 'status': order.status, 'message': f'Order status updated with stock management'})
    
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
                    # Change order status to ready for shipped
                    order.status = 'ready_for_shipped'
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
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def bulk_action(self, request):
        """Perform bulk actions on multiple orders"""
        print(f"🔄 BULK ACTION CALLED! User: {request.user}, Data: {request.data}")
        print(f"🔄 Request method: {request.method}")
        print(f"🔄 Request headers: {dict(request.headers)}")
        try:
            order_ids = request.data.get('order_ids', [])
            action = request.data.get('action')
            
            print(f"📋 Order IDs: {order_ids}, Action: {action}")
            
            if not order_ids:
                print("❌ No order IDs provided")
                return Response({'error': 'No order IDs provided'}, status=400)
            
            if not action:
                print("❌ No action specified")
                return Response({'error': 'No action specified'}, status=400)
            
            # Get the orders
            orders = Order.objects.filter(id__in=order_ids)
            
            if not orders.exists():
                return Response({'error': 'No orders found with the provided IDs'}, status=404)
            
            updated_count = 0
            
            if action == 'delete':
                # Restock items before deleting orders
                for order in orders:
                    print(f"Restocking items for order {order.order_number} before deletion")
                    restock_order_items(order)
                
                # Delete orders
                deleted_count = orders.count()
                orders.delete()
                return Response({
                    'success': True,
                    'message': f'Successfully deleted {deleted_count} order(s) and restocked items'
                })
            else:
                # Update status
                new_status = request.data.get('new_status', action)
                
                for order in orders:
                    old_status = order.status
                    order.status = new_status
                    
                    # Handle stock management based on status change
                    if old_status != new_status:
                        # If changing FROM cancelled TO active status, reduce stock
                        if should_restock_status(old_status) and should_reduce_stock_status(new_status):
                            print(f"Order {order.order_number}: Changing from {old_status} to {new_status} - reducing stock")
                            reduce_order_stock(order)
                        
                        # If changing TO cancelled FROM active status, restock
                        elif should_reduce_stock_status(old_status) and should_restock_status(new_status):
                            print(f"Order {order.order_number}: Changing from {old_status} to {new_status} - restocking")
                            restock_order_items(order)
                    
                    # Handle special cases for partially returned status
                    if new_status == 'partially_returned':
                        partially_amount = request.data.get('partially_amount')
                        if partially_amount:
                            order.partially_ammount = float(partially_amount)
                    
                    order.save()
                    updated_count += 1
                    
                    # Log activity for each order
                    try:
                        self.log_activity(f'bulk_updated_to_{new_status}', order)
                    except Exception as e:
                        print(f"Error logging activity: {str(e)}")
                
                return Response({
                    'success': True,
                    'message': f'Successfully updated {updated_count} order(s) to {new_status} with stock management'
                })
                
        except Exception as e:
            print(f"❌ Error in bulk action: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=500)

    @action(detail=True, methods=['post'])
    def update_courier_status(self, request, pk=None):
        """Update courier status for an order"""
        try:
            order = self.get_object()
            new_courier_status = request.data.get('curier_status')
            courier_data = request.data.get('courier_data', {})
            
            if not new_courier_status:
                return Response({'error': 'Courier status is required'}, status=400)
            
            # Update courier status
            order.curier_status = new_courier_status
            order.save()
            
            # Log the activity
            try:
                self.log_activity(f'updated_courier_status_to_{new_courier_status}', order)
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return Response({
                'success': True,
                'curier_status': order.curier_status,
                'order_id': order.id
            })
            
        except Exception as e:
            print(f"Error updating courier status: {str(e)}")
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=500)

    @action(detail=True, methods=['post'])
    def check_courier_status(self, request, pk=None):
        """Check courier status using stored API credentials"""
        try:
            import requests
            from settings.models import Curier
            
            order = self.get_object()
            
            if not order.curier_id:
                return Response({'error': 'Order has no courier ID'}, status=400)
            
            # Get SteadFast courier configuration
            steadfast = Curier.objects.filter(name__icontains='steadfast', is_active=True).first()
            if not steadfast:
                return Response({'error': 'SteadFast courier configuration not found'}, status=400)
            
            # Use the status checking endpoint
            status_url = f"https://portal.packzy.com/api/v1/status_by_cid/{order.curier_id}"
            
            # Prepare headers with authentication
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Api-Key': steadfast.api_key,
                'Secret-Key': steadfast.secret_key
            }
            
            print(f"Checking courier status for order {order.order_number} with courier ID: {order.curier_id}")
            print(f"Using URL: {status_url}")
            
            # Make API request
            response = requests.get(status_url, headers=headers, timeout=30)
            
            print(f"API Response Status: {response.status_code}")
            print(f"API Response: {response.text}")
            
            if response.status_code == 200:
                courier_data = response.json()
                
                # Check if delivered
                status = str(courier_data.get('status', '')).lower()
                delivery_status = str(courier_data.get('delivery_status', '')).lower()
                order_status = str(courier_data.get('order_status', '')).lower()
                
                # Combine all status fields for checking
                combined_status = f"{status} {delivery_status} {order_status}".lower()
                
                is_delivered = any(keyword in combined_status for keyword in [
                    'delivered', 'delivery_completed', 'completed', 'success'
                ])
                
                print(f"Status fields: status={status}, delivery_status={delivery_status}, order_status={order_status}")
                print(f"Combined status: {combined_status}")
                print(f"Is delivered: {is_delivered}")
                
                # Update courier status
                order.curier_status = courier_data.get('status', 'unknown')
                
                # Auto-update to delivered if detected
                if is_delivered and order.status == 'shipped':
                    order.status = 'delivered'
                    print(f"Auto-updated order {order.order_number} to delivered")
                
                order.save()
                
                # Log activity
                try:
                    self.log_activity(f'checked_courier_status', order)
                except Exception as e:
                    print(f"Error logging activity: {str(e)}")
                
                return Response({
                    'success': True,
                    'courier_data': courier_data,
                    'is_delivered': is_delivered,
                    'order_status': order.status,
                    'courier_status': order.curier_status
                })
            else:
                error_message = f"API returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', error_message)
                except:
                    error_message = response.text or error_message
                
                return Response({
                    'error': f'Courier API error: {error_message}',
                    'status_code': response.status_code
                }, status=400)
                
        except requests.exceptions.Timeout:
            return Response({'error': 'Courier API timeout'}, status=408)
        except requests.exceptions.RequestException as e:
            return Response({'error': f'Network error: {str(e)}'}, status=500)
        except Exception as e:
            print(f"Error checking courier status: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=500)

class DashboardStatisticsView(APIView):
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
            
            # Define time periods using Dhaka timezone (UTC +6)
            dhaka_tz = timezone.get_fixed_timezone(6 * 60)  # +6 hours in minutes
            now = timezone.now().astimezone(dhaka_tz)
            
            if period == 'custom' and date_from and date_to:
                # Custom date range
                try:
                    start_date = datetime.strptime(date_from, '%Y-%m-%d').replace(tzinfo=dhaka_tz)
                    end_date = datetime.strptime(date_to, '%Y-%m-%d').replace(tzinfo=dhaka_tz) + timedelta(days=1) - timedelta(seconds=1)
                except ValueError:
                    return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
            elif period == 'day':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif period == 'week':
                # This week (Monday to Sunday in Dhaka time)
                days_since_monday = now.weekday()
                start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif period == 'month':
                # This month in Dhaka timezone
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif period == 'last_month':
                # Last month in Dhaka timezone
                first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = first_day_this_month - timedelta(seconds=1)
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == 'year':
                # This year in Dhaka timezone
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            elif period == 'all':
                start_date = None
                end_date = None
            else:  # default to week
                days_since_monday = now.weekday()
                start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now
            
            # Build base query filter
            date_filter = Q()
            if start_date and end_date:
                date_filter = Q(created_at__gte=start_date.astimezone(timezone.timezone.utc), created_at__lte=end_date.astimezone(timezone.timezone.utc))
            elif start_date:
                date_filter = Q(created_at__gte=start_date.astimezone(timezone.timezone.utc))
            
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
            expense_date_filter = Q()
            if start_date and end_date:
                expense_date_filter = Q(created_at__gte=start_date.astimezone(timezone.timezone.utc), created_at__lte=end_date.astimezone(timezone.timezone.utc))
            elif start_date:
                expense_date_filter = Q(created_at__gte=start_date.astimezone(timezone.timezone.utc))
                
            dashboard_expenses = Expense.objects.filter(expense_date_filter).aggregate(total=Sum('amount'))['total'] or 0
            
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
def dashboard_categories(request):
    context = {
        'active_page': 'categories'
    }
    return render(request, 'dashboard/categories.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_media(request):
    context = {
        'active_page': 'media'
    }
    return render(request, 'dashboard/media.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_orders(request):
    context = {
        'active_page': 'orders'
    }
    return render(request, 'dashboard/orders.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_incomplete_orders(request):
    context = {
        'active_page': 'incomplete_orders'
    }
    return render(request, 'dashboard/incomplete_orders.html', context)

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
@login_required
@user_passes_test(is_admin)
def dashboard_settings(request):
    if request.method == 'POST':
        return handle_general_settings_update(request)
    
    settings = DashboardSetting.objects.all()
    site_settings = SiteSettings.get_active_settings()
    
    context = {
        'settings': settings,
        'site_settings': site_settings,
        'active_page': 'settings'
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@user_passes_test(is_admin)
def debug_settings(request):
    """Debug page for testing settings functionality"""
    if request.method == 'POST':
        return handle_general_settings_update(request)
    
    settings = DashboardSetting.objects.all()
    site_settings = SiteSettings.get_active_settings()
    
    context = {
        'settings': settings,
        'site_settings': site_settings,
        'active_page': 'debug_settings'
    }
    return render(request, 'dashboard/debug_settings.html', context)

def test_settings_post(request):
    """Test endpoint for POST requests without authentication"""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': 'Test POST request successful!',
            'data': dict(request.POST.items())
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests allowed'
        })

@login_required
@user_passes_test(is_admin)
def handle_general_settings_update(request):
    """Handle the general settings form submission"""
    try:
        # Get or create site settings instance
        site_settings = SiteSettings.get_active_settings()
        if not site_settings.pk:
            site_settings = SiteSettings()
        
        # Update site identity fields
        site_settings.site_name = request.POST.get('site_name', site_settings.site_name)
        site_settings.site_tagline = request.POST.get('site_tagline', site_settings.site_tagline)
        
        # Handle image paths (text fields instead of file uploads)
        site_logo_path = request.POST.get('site_logo', '').strip()
        if site_logo_path:
            site_settings.site_logo = site_logo_path
            
        site_favicon_path = request.POST.get('site_favicon', '').strip()
        if site_favicon_path:
            site_settings.site_favicon = site_favicon_path
            
        footer_logo_path = request.POST.get('footer_logo', '').strip()
        if footer_logo_path:
            site_settings.footer_logo = footer_logo_path
        
        # Update contact information
        site_settings.contact_phone = request.POST.get('contact_phone', site_settings.contact_phone)
        site_settings.contact_email = request.POST.get('contact_email', site_settings.contact_email)
        site_settings.contact_address = request.POST.get('contact_address', site_settings.contact_address)
        
        # Update footer information
        site_settings.footer_short_text = request.POST.get('footer_short_text', site_settings.footer_short_text)
        site_settings.facebook_link = request.POST.get('facebook_link', site_settings.facebook_link)
        site_settings.youtube_link = request.POST.get('youtube_link', site_settings.youtube_link)
        
        # Update quick links configuration
        site_settings.quick_links_title = request.POST.get('quick_links_title', site_settings.quick_links_title)
        site_settings.customer_service_title = request.POST.get('customer_service_title', site_settings.customer_service_title)
        
        # Update quick links
        site_settings.home_text = request.POST.get('home_text', site_settings.home_text)
        site_settings.home_url = request.POST.get('home_url', site_settings.home_url)
        site_settings.products_text = request.POST.get('products_text', site_settings.products_text)
        site_settings.products_url = request.POST.get('products_url', site_settings.products_url)
        site_settings.categories_text = request.POST.get('categories_text', site_settings.categories_text)
        site_settings.categories_url = request.POST.get('categories_url', site_settings.categories_url)
        site_settings.about_text = request.POST.get('about_text', site_settings.about_text)
        site_settings.about_url = request.POST.get('about_url', site_settings.about_url)
        site_settings.contact_text = request.POST.get('contact_text', site_settings.contact_text)
        site_settings.contact_url = request.POST.get('contact_url', site_settings.contact_url)
        
        # Update customer service links
        site_settings.track_order_text = request.POST.get('track_order_text', site_settings.track_order_text)
        site_settings.track_order_url = request.POST.get('track_order_url', site_settings.track_order_url)
        site_settings.return_policy_text = request.POST.get('return_policy_text', site_settings.return_policy_text)
        site_settings.return_policy_url = request.POST.get('return_policy_url', site_settings.return_policy_url)
        site_settings.shipping_info_text = request.POST.get('shipping_info_text', site_settings.shipping_info_text)
        site_settings.shipping_info_url = request.POST.get('shipping_info_url', site_settings.shipping_info_url)
        site_settings.fraud_checker_text = request.POST.get('fraud_checker_text', site_settings.fraud_checker_text)
        site_settings.fraud_checker_url = request.POST.get('fraud_checker_url', site_settings.fraud_checker_url)
        site_settings.faq_text = request.POST.get('faq_text', site_settings.faq_text)
        site_settings.faq_url = request.POST.get('faq_url', site_settings.faq_url)
        
        # Update footer copyright
        site_settings.copyright_text = request.POST.get('copyright_text', site_settings.copyright_text)
        
        # Update home page features
        site_settings.why_shop_section_title = request.POST.get('why_shop_section_title', site_settings.why_shop_section_title)
        site_settings.feature1_title = request.POST.get('feature1_title', site_settings.feature1_title)
        site_settings.feature1_subtitle = request.POST.get('feature1_subtitle', site_settings.feature1_subtitle)
        site_settings.feature2_title = request.POST.get('feature2_title', site_settings.feature2_title)
        site_settings.feature2_subtitle = request.POST.get('feature2_subtitle', site_settings.feature2_subtitle)
        site_settings.feature3_title = request.POST.get('feature3_title', site_settings.feature3_title)
        site_settings.feature3_subtitle = request.POST.get('feature3_subtitle', site_settings.feature3_subtitle)
        site_settings.feature4_title = request.POST.get('feature4_title', site_settings.feature4_title)
        site_settings.feature4_subtitle = request.POST.get('feature4_subtitle', site_settings.feature4_subtitle)
        
        # Set as active and save
        site_settings.is_active = True
        site_settings.save()
        
        # Deactivate other settings
        SiteSettings.objects.exclude(pk=site_settings.pk).update(is_active=False)
        
        return JsonResponse({
            'success': True, 
            'message': 'Settings updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error updating settings: {str(e)}'
        })


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
def dashboard_pages(request):
    """Pages management dashboard view"""
    context = {
        'active_page': 'pages',
        'page_title': 'Pages Management',
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/mb-admin/'},
            {'name': 'Pages', 'url': '/mb-admin/pages/'},
        ]
    }
    return render(request, 'dashboard/pages.html', context)

@login_required
@user_passes_test(is_admin)
def dashboard_expenses(request):
    context = {
        'active_page': 'expenses'
    }
    return render(request, 'dashboard/expenses.html', context)

@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
def dashboard_stock(request):
    context = {
        'active_page': 'stock'
    }
    return render(request, 'dashboard/stock.html', context)

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


class IncompleteOrderDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing incomplete orders in the dashboard."""
    queryset = IncompleteOrder.objects.all().prefetch_related('items', 'shipping_address', 'history')
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['status', 'is_guest_order', 'recovery_attempts']
    search_fields = ['incomplete_order_id', 'customer_email', 'guest_email', 'user__username']
    ordering_fields = ['created_at', 'total_amount', 'recovery_attempts']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        # Use the incomplete orders serializers
        from incomplete_orders.serializers import IncompleteOrderSerializer
        return IncompleteOrderSerializer
    
    def list(self, request, *args, **kwargs):
        """Enhanced list method with status counts"""
        # Check if this is a count_by_status request
        count_by_status = request.query_params.get('count_by_status')
        if count_by_status:
            from django.db.models import Count
            from django.utils import timezone
            
            # Get all incomplete orders and count by status
            status_counts = {}
            
            # Count each status
            all_orders = IncompleteOrder.objects.all()
            status_counts = dict(all_orders.values('status').annotate(count=Count('status')).values_list('status', 'count'))
            total_count = all_orders.count()
            
            # Count orders by recovery attempts
            recovery_counts = dict(all_orders.values('recovery_attempts').annotate(count=Count('recovery_attempts')).values_list('recovery_attempts', 'count'))
            
            return Response({
                'status_counts': status_counts,
                'recovery_counts': recovery_counts,
                'total_count': total_count
            })
        
        # Include detailed information in serialization
        include_details = request.query_params.get('include_details')
        if include_details:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                orders_data = []
                for order in page:
                    # Get shipping address data
                    shipping_address = None
                    if hasattr(order, 'shipping_address') and order.shipping_address:
                        shipping_address = {
                            'first_name': order.shipping_address.first_name,
                            'last_name': order.shipping_address.last_name,
                            'phone': order.shipping_address.phone,
                            'email': order.shipping_address.email,
                            'address_line_1': order.shipping_address.address_line_1,
                            'address_line_2': order.shipping_address.address_line_2,
                            'city': order.shipping_address.city,
                            'state': order.shipping_address.state,
                            'postal_code': order.shipping_address.postal_code,
                            'country': order.shipping_address.country,
                        }
                    
                    orders_data.append({
                        'id': order.id,
                        'incomplete_order_id': order.incomplete_order_id,
                        'created_at': order.created_at.isoformat(),
                        'status': order.status,
                        'total_amount': str(order.total_amount),
                        'items_count': order.total_items,
                        'user': {
                            'id': order.user.id if order.user else None,
                            'username': order.user.username if order.user else None,
                            'email': order.user.email if order.user else order.guest_email,
                            'first_name': order.user.first_name if order.user else None,
                            'last_name': order.user.last_name if order.user else None,
                        } if order.user else None,
                        'shipping_address': shipping_address,
                        'customer_email': order.customer_email,
                        'customer_phone': order.customer_phone,
                        'guest_email': order.guest_email,
                        'recovery_attempts': order.recovery_attempts,
                        'last_recovery_attempt': order.last_recovery_attempt.isoformat() if order.last_recovery_attempt else None,
                        'abandonment_reason': order.abandonment_reason,
                        'can_convert': order.can_convert,
                        'is_expired': order.is_expired,
                        'days_since_created': order.days_since_created,
                        'expires_at': order.expires_at.isoformat() if order.expires_at else None,
                    })
                
                return self.get_paginated_response(orders_data)
        
        # Default behavior
        return super().list(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def convert_to_order(self, request, pk=None):
        """Convert incomplete order to complete order"""
        incomplete_order = self.get_object()
        
        try:
            if not incomplete_order.can_convert:
                return Response({
                    'success': False,
                    'error': 'This incomplete order cannot be converted'
                }, status=400)
            
            complete_order = incomplete_order.convert_to_order()
            
            return Response({
                'success': True,
                'message': f'Successfully converted to order {complete_order.order_number}',
                'order_id': complete_order.id,
                'order_number': complete_order.order_number
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=True, methods=['post'])
    def send_recovery_email(self, request, pk=None):
        """Send recovery email for incomplete order"""
        incomplete_order = self.get_object()
        
        try:
            from incomplete_orders.services import IncompleteOrderService
            
            email_type = request.data.get('email_type', 'abandoned_cart')
            success = IncompleteOrderService.send_recovery_email(
                incomplete_order=incomplete_order,
                email_type=email_type
            )
            
            if success:
                incomplete_order.increment_recovery_attempt()
                return Response({
                    'success': True,
                    'message': 'Recovery email sent successfully'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to send recovery email'
                }, status=400)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Bulk actions for incomplete orders"""
        order_ids = request.data.get('order_ids', [])
        action = request.data.get('action')
        
        if not order_ids or not action:
            return Response({
                'success': False,
                'error': 'order_ids and action are required'
            }, status=400)
        
        try:
            orders = IncompleteOrder.objects.filter(id__in=order_ids)
            
            if action == 'convert':
                converted_count = 0
                failed_count = 0
                
                for order in orders:
                    try:
                        if order.can_convert:
                            order.convert_to_order()
                            converted_count += 1
                        else:
                            failed_count += 1
                    except:
                        failed_count += 1
                
                return Response({
                    'success': True,
                    'message': f'Converted {converted_count} orders, {failed_count} failed',
                    'converted': converted_count,
                    'failed': failed_count
                })
            
            elif action == 'send_recovery':
                sent_count = 0
                for order in orders:
                    try:
                        from incomplete_orders.services import IncompleteOrderService
                        if IncompleteOrderService.send_recovery_email(order):
                            order.increment_recovery_attempt()
                            sent_count += 1
                    except:
                        pass
                
                return Response({
                    'success': True,
                    'message': f'Sent recovery emails to {sent_count} customers',
                    'sent': sent_count
                })
            
            elif action == 'mark_abandoned':
                updated_count = orders.filter(status__in=['pending', 'payment_pending']).update(status='abandoned')
                
                return Response({
                    'success': True,
                    'message': f'Marked {updated_count} orders as abandoned',
                    'updated': updated_count
                })
            
            elif action == 'delete':
                deleted_count = orders.count()
                orders.delete()
                
                return Response({
                    'success': True,
                    'message': f'Deleted {deleted_count} incomplete orders',
                    'deleted': deleted_count
                })
            
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid action'
                }, status=400)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get items for a specific incomplete order"""
        incomplete_order = self.get_object()
        
        try:
            items = incomplete_order.items.all().select_related('product', 'variant').prefetch_related('product__images')
            items_data = []
            
            for item in items:
                # Get product image (first image from product images)
                product_image = None
                if item.product and item.product.images.exists():
                    first_image = item.product.images.first()
                    if first_image and first_image.image:
                        try:
                            product_image = first_image.image.url
                        except:
                            product_image = None
                
                # Get variant image
                variant_image = None
                if item.variant and item.variant.image:
                    try:
                        variant_image = item.variant.image.url
                    except:
                        variant_image = None
                
                # Use default image if no product or variant image available
                display_image = variant_image or product_image or '/media/default.webp'
                
                items_data.append({
                    'id': item.id,
                    'product_name': item.product_name or (item.product.name if item.product else 'Unknown Product'),
                    'product_sku': item.product_sku or (item.product.sku if item.product else 'N/A'),
                    'variant_name': item.variant_name or (item.variant.name if item.variant else 'Default'),
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price),
                    'product_image': product_image,
                    'variant_image': variant_image,
                    'display_image': display_image,  # Primary image to show in UI
                })
            
            return Response({
                'success': True,
                'items': items_data,
                'total_items': len(items_data),
                'subtotal': str(incomplete_order.subtotal),
                'shipping_cost': str(incomplete_order.shipping_cost),
                'tax_amount': str(incomplete_order.tax_amount),
                'discount_amount': str(incomplete_order.discount_amount),
                'total_amount': str(incomplete_order.total_amount),
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add a new item to an incomplete order"""
        try:
            incomplete_order = self.get_object()
            
            product_id = request.data.get('product_id')
            variant_id = request.data.get('variant_id')
            quantity = int(request.data.get('quantity', 1))
            unit_price = request.data.get('unit_price')
            
            # Validate required fields
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required'
                }, status=400)
            
            # Get product and variant
            from products.models import Product, ProductVariant
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Product not found'
                }, status=404)
            
            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                except ProductVariant.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Product variant not found'
                    }, status=404)
            
            # Use provided price or default to product/variant price
            if unit_price is None:
                if variant and variant.price:
                    unit_price = variant.price
                else:
                    unit_price = product.price
            
            from incomplete_orders.models import IncompleteOrderItem
            from decimal import Decimal
            
            # Check if item already exists in order
            existing_item = IncompleteOrderItem.objects.filter(
                incomplete_order=incomplete_order,
                product=product,
                variant=variant
            ).first()
            
            if existing_item:
                # Update existing item quantity
                existing_item.quantity += quantity
                existing_item.save()
                message = 'Item quantity updated successfully'
            else:
                # Create new item
                IncompleteOrderItem.objects.create(
                    incomplete_order=incomplete_order,
                    product=product,
                    variant=variant,
                    product_name=product.name,
                    product_sku=product.sku,
                    variant_name=variant.name if variant else 'Default',
                    quantity=quantity,
                    unit_price=Decimal(str(unit_price))
                )
                message = 'Item added to order successfully'
            
            # Recalculate order total
            total = sum(item.quantity * item.unit_price for item in incomplete_order.items.all())
            incomplete_order.total_amount = total
            incomplete_order.save()
            
            return Response({
                'success': True,
                'message': message,
                'new_total': float(total)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove an item from an incomplete order"""
        try:
            incomplete_order = self.get_object()
            item_id = request.data.get('item_id')
            
            if not item_id:
                return Response({
                    'success': False,
                    'error': 'Item ID is required'
                }, status=400)
            
            from incomplete_orders.models import IncompleteOrderItem
            
            try:
                item = IncompleteOrderItem.objects.get(
                    id=item_id,
                    incomplete_order=incomplete_order
                )
                item.delete()
                
                # Recalculate order total
                total = sum(item.quantity * item.unit_price for item in incomplete_order.items.all())
                incomplete_order.total_amount = total
                incomplete_order.save()
                
                return Response({
                    'success': True,
                    'message': 'Item removed successfully',
                    'new_total': float(total)
                })
                
            except IncompleteOrderItem.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Item not found'
                }, status=404)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @action(detail=True, methods=['post'])
    def update_shipping(self, request, pk=None):
        """Update shipping address for an incomplete order"""
        try:
            incomplete_order = self.get_object()
            shipping_data = request.data
            
            # Update or create shipping address
            if hasattr(incomplete_order, 'shipping_address') and incomplete_order.shipping_address:
                shipping_address = incomplete_order.shipping_address
                for field, value in shipping_data.items():
                    setattr(shipping_address, field, value)
                shipping_address.save()
            else:
                # Create new shipping address
                from incomplete_orders.models import IncompleteShippingAddress
                shipping_address = IncompleteShippingAddress.objects.create(
                    incomplete_order=incomplete_order,
                    **shipping_data
                )
            
            return Response({
                'success': True,
                'message': 'Shipping address updated successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    @action(detail=True, methods=['post'])
    def update_items(self, request, pk=None):
        """Update items for an incomplete order"""
        try:
            incomplete_order = self.get_object()
            items_data = request.data.get('items', [])
            
            from incomplete_orders.models import IncompleteOrderItem
            from decimal import Decimal
            
            # Update existing items
            for item_data in items_data:
                try:
                    item = IncompleteOrderItem.objects.get(
                        id=item_data['id'],
                        incomplete_order=incomplete_order
                    )
                    item.quantity = int(item_data['quantity'])
                    item.unit_price = Decimal(str(item_data['unit_price']))
                    item.save()
                except IncompleteOrderItem.DoesNotExist:
                    continue
            
            # Calculate new total
            total = sum(item.quantity * item.unit_price for item in incomplete_order.items.all())
            incomplete_order.total_amount = total
            incomplete_order.save()
            
            return Response({
                'success': True,
                'message': 'Items updated successfully',
                'new_total': float(total)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
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
            period = request.GET.get('period', 'all')
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            search = request.GET.get('search', '').strip()
            sort_by = request.GET.get('sort', 'orders')
            sort_order = request.GET.get('order', 'desc')
            
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
                        image_url = first_image.image_url
                elif hasattr(product, 'productimage_set') and product.productimage_set.exists():
                    first_image = product.productimage_set.first()
                    if first_image and first_image.image:
                        image_url = first_image.image_url
                
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


class CheckoutCustomizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing checkout page customization settings"""
    queryset = CheckoutCustomization.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_permissions(self):
        """Override permissions for specific actions"""
        if self.action == 'active_settings':
            # Allow anyone to read active settings for dashboard loading
            return []
        return super().get_permissions()
    
    def get_serializer_class(self):
        # Create inline serializer for checkout customization
        from rest_framework import serializers
        
        class CheckoutCustomizationSerializer(serializers.ModelSerializer):
            class Meta:
                model = CheckoutCustomization
                fields = '__all__'
                
        return CheckoutCustomizationSerializer
    
    def get_queryset(self):
        """Get checkout customization settings, prioritizing active ones"""
        return CheckoutCustomization.objects.all().order_by('-is_active', '-updated_at')
    
    @action(detail=False, methods=['get'])
    def active_settings(self, request):
        """Get the currently active checkout customization settings"""
        try:
            active_settings = CheckoutCustomization.get_active_settings()
            
            if not active_settings.pk:
                # Return default settings if none exist
                return Response({
                    'exists': False,
                    'message': 'No active checkout customization found. Using default settings.',
                    'settings': self.get_serializer(active_settings).data
                })
            
            serializer = self.get_serializer(active_settings)
            return Response({
                'exists': True,
                'settings': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to retrieve active settings: {str(e)}'
            }, status=500)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a specific checkout customization (deactivate others)"""
        try:
            customization = self.get_object()
            
            # Deactivate all other customizations
            CheckoutCustomization.objects.exclude(pk=customization.pk).update(is_active=False)
            
            # Activate this one
            customization.is_active = True
            customization.save()
            
            # Log activity
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action='activated_checkout_customization',
                    model_name='CheckoutCustomization',
                    object_id=customization.id,
                    object_repr=str(customization),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'Checkout customization activated successfully'
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to activate customization: {str(e)}'
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def reset_to_defaults(self, request):
        """Create new customization with default values"""
        try:
            # Deactivate all existing customizations
            CheckoutCustomization.objects.update(is_active=False)
            
            # Create new default customization
            default_customization = CheckoutCustomization.objects.create(is_active=True)
            
            # Log activity
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action='reset_checkout_to_defaults',
                    model_name='CheckoutCustomization',
                    object_id=default_customization.id,
                    object_repr=str(default_customization),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            serializer = self.get_serializer(default_customization)
            return Response({
                'success': True,
                'message': 'Checkout customization reset to defaults',
                'settings': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to reset to defaults: {str(e)}'
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Update multiple fields at once for the active customization"""
        try:
            active_settings = CheckoutCustomization.objects.filter(is_active=True).first()
            
            if not active_settings:
                # Create new active customization if none exists
                active_settings = CheckoutCustomization.objects.create(is_active=True)
            
            # Update fields from request data
            update_data = request.data.copy()
            
            # Remove non-model fields if any
            if 'csrfmiddlewaretoken' in update_data:
                del update_data['csrfmiddlewaretoken']
            
            # Update the settings
            for field, value in update_data.items():
                if hasattr(active_settings, field):
                    setattr(active_settings, field, value)
            
            active_settings.save()
            
            # Log activity
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action='bulk_updated_checkout_customization',
                    model_name='CheckoutCustomization',
                    object_id=active_settings.id,
                    object_repr=str(active_settings),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            serializer = self.get_serializer(active_settings)
            return Response({
                'success': True,
                'message': 'Checkout customization updated successfully',
                'settings': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to update customization: {str(e)}'
            }, status=500)
    
    def perform_create(self, serializer):
        # When creating new customization, optionally deactivate others
        if serializer.validated_data.get('is_active', False):
            CheckoutCustomization.objects.update(is_active=False)
        
        instance = serializer.save()
        
        # Log activity
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='created',
                model_name='CheckoutCustomization',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_update(self, serializer):
        # When updating, ensure only one active customization
        if serializer.validated_data.get('is_active', False):
            CheckoutCustomization.objects.exclude(pk=self.get_object().pk).update(is_active=False)
        
        instance = serializer.save()
        
        # Log activity
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='updated',
                model_name='CheckoutCustomization',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_destroy(self, instance):
        # Log activity before deletion
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='deleted',
                model_name='CheckoutCustomization',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        instance.delete()
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


@api_view(['GET'])
@permission_classes([])  # Allow anonymous access for frontend
def get_checkout_customization(request):
    """Public API endpoint to get active checkout customization for frontend"""
    try:
        active_settings = CheckoutCustomization.get_active_settings()
        
        # Create a simplified serializer for frontend use
        from rest_framework import serializers
        
        class FrontendCheckoutCustomizationSerializer(serializers.ModelSerializer):
            class Meta:
                model = CheckoutCustomization
                exclude = ['id', 'created_at', 'updated_at']  # Exclude metadata fields
        
        serializer = FrontendCheckoutCustomizationSerializer(active_settings)
        return Response({
            'success': True,
            'settings': serializer.data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to retrieve checkout customization: {str(e)}',
            'settings': {}  # Return empty settings as fallback
        }, status=500)


# BlockList Management Views
from .models import BlockList
from .serializers import BlockListSerializer

class BlockListViewSet(viewsets.ModelViewSet):
    """ViewSet for managing block list entries"""
    queryset = BlockList.objects.all()
    serializer_class = BlockListSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['block_type', 'reason', 'is_active']
    search_fields = ['value', 'description']
    ordering_fields = ['created_at', 'updated_at', 'block_count', 'last_triggered']
    ordering = ['-created_at']
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def perform_create(self, serializer):
        """Log creation activity"""
        instance = serializer.save(blocked_by=self.request.user)
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='created',
                model_name='BlockList',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_update(self, serializer):
        """Log update activity"""
        instance = serializer.save()
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='updated',
                model_name='BlockList',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_destroy(self, instance):
        """Log deletion activity"""
        try:
            AdminActivity.objects.create(
                user=self.request.user,
                action='deleted',
                model_name='BlockList',
                object_id=instance.id,
                object_repr=str(instance),
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete block list entries"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            entries = BlockList.objects.filter(id__in=ids)
            deleted_count = 0
            
            for entry in entries:
                try:
                    AdminActivity.objects.create(
                        user=request.user,
                        action='bulk_deleted',
                        model_name='BlockList',
                        object_id=entry.id,
                        object_repr=str(entry),
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception as e:
                    print(f"Error logging bulk delete activity: {str(e)}")
                
                entry.delete()
                deleted_count += 1
            
            return Response({
                'message': f'Successfully deleted {deleted_count} entries',
                'deleted_count': deleted_count
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_toggle_active(self, request):
        """Bulk toggle active status"""
        ids = request.data.get('ids', [])
        is_active = request.data.get('is_active', True)
        
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_count = BlockList.objects.filter(id__in=ids).update(is_active=is_active)
            
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action='bulk_updated',
                    model_name='BlockList',
                    object_repr=f'Bulk toggle active status to {is_active} for {updated_count} entries',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging bulk update activity: {str(e)}")
            
            return Response({
                'message': f'Successfully updated {updated_count} entries',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get block list statistics"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            total_blocks = BlockList.objects.count()
            active_blocks = BlockList.objects.filter(is_active=True).count()
            phone_blocks = BlockList.objects.filter(block_type='phone', is_active=True).count()
            ip_blocks = BlockList.objects.filter(block_type='ip', is_active=True).count()
            
            # Today's blocks
            today = timezone.now().date()
            today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
            today_blocks = BlockList.objects.filter(created_at__gte=today_start).count()
            
            reason_stats = {}
            for choice in BlockList.REASON_CHOICES:
                reason_code = choice[0]
                reason_name = choice[1]
                count = BlockList.objects.filter(reason=reason_code, is_active=True).count()
                if count > 0:
                    reason_stats[reason_name] = count
            
            recent_blocks = BlockList.objects.filter(
                last_triggered__isnull=False
            ).order_by('-last_triggered')[:5]
            
            recent_activity = []
            for block in recent_blocks:
                recent_activity.append({
                    'type': block.get_block_type_display(),
                    'value': block.value,
                    'reason': block.get_reason_display(),
                    'count': block.block_count,
                    'last_triggered': block.last_triggered
                })
            
            return Response({
                'total_blocked': active_blocks,
                'phone_blocked': phone_blocks,
                'ip_blocked': ip_blocks,
                'today_blocked': today_blocks,
                'total_blocks': total_blocks,
                'active_blocks': active_blocks,
                'reason_stats': reason_stats,
                'recent_activity': recent_activity
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_block(self, request):
        """Bulk activate blocking for selected entries"""
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_count = BlockList.objects.filter(id__in=ids).update(is_active=True)
            
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action='bulk_blocked',
                    model_name='BlockList',
                    object_repr=f'Bulk activated blocking for {updated_count} entries',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging bulk block activity: {str(e)}")
            
            return Response({
                'message': f'Successfully activated blocking for {updated_count} entries',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_unblock(self, request):
        """Bulk deactivate blocking for selected entries"""
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_count = BlockList.objects.filter(id__in=ids).update(is_active=False)
            
            try:
                AdminActivity.objects.create(
                    user=request.user,
                    action='bulk_unblocked',
                    model_name='BlockList',
                    object_repr=f'Bulk deactivated blocking for {updated_count} entries',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging bulk unblock activity: {str(e)}")
            
            return Response({
                'message': f'Successfully deactivated blocking for {updated_count} entries',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def check_blocked(request):
    """Check if a phone number or IP address is blocked"""
    block_type = request.data.get('block_type')
    value = request.data.get('value')
    
    if not block_type or not value:
        return Response({'error': 'block_type and value are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        is_blocked = BlockList.is_blocked(block_type, value)
        block_entry = None
        
        if is_blocked:
            block_entry = BlockList.objects.get(block_type=block_type, value=value, is_active=True)
            serializer = BlockListSerializer(block_entry)
            return Response({
                'is_blocked': True,
                'block_entry': serializer.data
            })
        else:
            return Response({'is_blocked': False})
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_member_required
def dashboard_blocklist(request):
    """BlockList management dashboard view"""
    context = {
        'active_page': 'blocklist',
        'page_title': 'Block List Management',
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': '/mb-admin/'},
            {'name': 'Block List', 'url': '/mb-admin/blocklist/'},
        ]
    }
    return render(request, 'dashboard/blocklist.html', context)


@api_view(['GET'])
@permission_classes([IsStaffUser])
def blocklist_dashboard(request):
    """Render the block list dashboard page"""
    return render(request, 'dashboard/blocklist.html')


# Reviews Management Views
@staff_member_required
def reviews_dashboard(request):
    """Professional Reviews Management Dashboard"""
    from products.models import Review, ReviewImage
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    rating_filter = request.GET.get('rating', 'all')
    product_filter = request.GET.get('product', '')
    verified_filter = request.GET.get('verified', 'all')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Base queryset
    reviews = Review.objects.select_related('user', 'product').prefetch_related('images').order_by('-created_at')
    
    # Apply filters
    if status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)
    elif status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    
    if rating_filter != 'all':
        reviews = reviews.filter(rating=int(rating_filter))
    
    if verified_filter == 'verified':
        reviews = reviews.filter(is_verified_purchase=True)
    elif verified_filter == 'unverified':
        reviews = reviews.filter(is_verified_purchase=False)
    
    if product_filter:
        reviews = reviews.filter(product__name__icontains=product_filter)
    
    if search_query:
        reviews = reviews.filter(
            Q(comment__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(guest_name__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    # Pagination - 20 reviews per page
    paginator = Paginator(reviews, 20)
    try:
        reviews_page = paginator.page(page)
    except PageNotAnInteger:
        reviews_page = paginator.page(1)
    except EmptyPage:
        reviews_page = paginator.page(paginator.num_pages)
    
    # Statistics
    total_reviews = Review.objects.count()
    approved_reviews = Review.objects.filter(is_approved=True).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()
    verified_reviews = Review.objects.filter(is_verified_purchase=True).count()
    reviews_with_images = Review.objects.filter(images__isnull=False).distinct().count()
    
    # Average rating
    from django.db.models import Avg
    avg_rating = Review.objects.filter(is_approved=True).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = Review.objects.filter(rating=i, is_approved=True).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_reviews = Review.objects.filter(created_at__gte=thirty_days_ago).count()
    
    context = {
        'reviews': reviews_page,
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'pending_reviews': pending_reviews,
        'verified_reviews': verified_reviews,
        'reviews_with_images': reviews_with_images,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
        'recent_reviews': recent_reviews,
        'status_filter': status_filter,
        'rating_filter': rating_filter,
        'product_filter': product_filter,
        'verified_filter': verified_filter,
        'search_query': search_query,
        'active_page': 'reviews',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': '/mb-admin/'},
            {'name': 'Reviews', 'url': '/mb-admin/reviews/'},
        ]
    }
    return render(request, 'dashboard/reviews.html', context)


@api_view(['POST'])
@permission_classes([IsStaffUser])
def review_bulk_action(request):
    """Handle bulk actions for reviews"""
    from products.models import Review
    
    try:
        action = request.data.get('action')
        review_ids = request.data.get('review_ids', [])
        
        if not action or not review_ids:
            return Response({'error': 'Action and review IDs are required'}, status=400)
        
        reviews = Review.objects.filter(id__in=review_ids)
        
        if action == 'approve':
            reviews.update(is_approved=True)
            message = f'{reviews.count()} reviews approved successfully'
        elif action == 'disapprove':
            reviews.update(is_approved=False)
            message = f'{reviews.count()} reviews disapproved successfully'
        elif action == 'delete':
            count = reviews.count()
            reviews.delete()
            message = f'{count} reviews deleted successfully'
        else:
            return Response({'error': 'Invalid action'}, status=400)
        
        return Response({'message': message})
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsStaffUser])
def review_single_action(request, review_id):
    """Handle single review actions"""
    from products.models import Review
    
    try:
        review = get_object_or_404(Review, id=review_id)
        action = request.data.get('action')
        
        if action == 'approve':
            review.is_approved = True
            review.save()
            message = 'Review approved successfully'
        elif action == 'disapprove':
            review.is_approved = False
            review.save()
            message = 'Review disapproved successfully'
        elif action == 'delete':
            review.delete()
            message = 'Review deleted successfully'
        elif action == 'toggle_verified':
            review.is_verified_purchase = not review.is_verified_purchase
            review.save()
            message = f'Review marked as {"verified" if review.is_verified_purchase else "unverified"}'
        else:
            return Response({'error': 'Invalid action'}, status=400)
        
        return Response({'message': message})
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET', 'POST'])
@permission_classes([IsStaffUser])
def review_edit(request, review_id):
    """Handle review editing"""
    from products.models import Review
    
    try:
        review = get_object_or_404(Review, id=review_id)
        
        if request.method == 'GET':
            # Return review data for editing
            return Response({
                'id': review.id,
                'product_name': review.product.name,
                'reviewer_name': review.user.username if review.user else review.guest_name,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'is_approved': review.is_approved,
                'is_verified_purchase': review.is_verified_purchase,
                'created_at': review.created_at.isoformat(),
            })
        
        elif request.method == 'POST':
            # Update review
            data = request.data
            
            # Validate rating
            rating = data.get('rating')
            if rating and (not isinstance(rating, int) or rating < 1 or rating > 5):
                return Response({'error': 'Rating must be between 1 and 5'}, status=400)
            
            # Update fields
            if 'rating' in data:
                review.rating = data['rating']
            if 'title' in data:
                review.title = data['title']
            if 'comment' in data:
                review.comment = data['comment']
            if 'is_approved' in data:
                review.is_approved = data['is_approved']
            if 'is_verified_purchase' in data:
                review.is_verified_purchase = data['is_verified_purchase']
            
            review.save()
            
            return Response({'message': 'Review updated successfully'})
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsStaffUser])
def review_images(request, review_id):
    """Get images for a review"""
    from products.models import Review, ReviewImage
    
    try:
        review = get_object_or_404(Review, id=review_id)
        images = review.images.all()
        
        images_data = []
        for image in images:
            images_data.append({
                'id': image.id,
                'image_url': image.image_url,
                'caption': image.caption,
                'created_at': image.created_at.isoformat() if hasattr(image, 'created_at') else None
            })
        
        return Response({'images': images_data})
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsStaffUser])
def upload_review_image(request):
    """Upload a new image for a review"""
    from products.models import Review, ReviewImage
    
    try:
        review_id = request.data.get('review_id')
        image_file = request.FILES.get('image')
        caption = request.data.get('caption', '')
        
        if not review_id or not image_file:
            return Response({'error': 'Review ID and image file are required'}, status=400)
        
        review = get_object_or_404(Review, id=review_id)
        
        # Validate file size (5MB limit)
        if image_file.size > 5 * 1024 * 1024:
            return Response({'error': 'Image file too large. Maximum size is 5MB.'}, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type. Only JPG, PNG, GIF, and WebP are allowed.'}, status=400)
        
        # Create review image
        review_image = ReviewImage.objects.create(
            review=review,
            image=image_file,
            caption=caption
        )
        
        return Response({
            'message': 'Image uploaded successfully',
            'image': {
                'id': review_image.id,
                'image_url': review_image.image_url,
                'caption': review_image.caption
            }
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsStaffUser])
def update_image_caption(request, image_id):
    """Update caption for a review image"""
    from products.models import ReviewImage
    
    try:
        image = get_object_or_404(ReviewImage, id=image_id)
        caption = request.data.get('caption', '')
        
        image.caption = caption
        image.save()
        
        return Response({'message': 'Caption updated successfully'})
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsStaffUser])
def delete_review_image(request, image_id):
    """Delete a review image"""
    from products.models import ReviewImage
    
    try:
        image = get_object_or_404(ReviewImage, id=image_id)
        image.delete()
        
        return Response({'message': 'Image deleted successfully'})
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)
