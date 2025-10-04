"""
Professional Stock Activity Service
Handles all stock movements with comprehensive tracking and audit trail
"""
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from typing import Union, Optional, Dict, Any, List
import uuid

from .models import StockActivity, StockActivityBatch
from products.models import Product, ProductVariant


class StockActivityService:
    """
    Professional service for managing stock activities with full audit trail
    """
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    def create_stock_activity(
        item: Union[Product, ProductVariant],
        activity_type: str,
        quantity_changed: int,
        reason: str,
        user,
        request=None,
        unit_cost: Optional[Decimal] = None,
        reference_number: str = "",
        notes: str = "",
        activity_date: Optional[timezone.datetime] = None,
        batch: Optional[StockActivityBatch] = None,
        status: str = 'completed'
    ) -> StockActivity:
        """
        Create a comprehensive stock activity record
        
        Args:
            item: Product or ProductVariant instance
            activity_type: Type of activity ('stock_in', 'stock_out', etc.)
            quantity_changed: Positive for increases, negative for decreases
            reason: Reason for the stock activity
            user: User performing the activity
            request: HTTP request object for IP/user agent tracking
            unit_cost: Cost per unit (optional)
            reference_number: Reference number (PO, invoice, etc.)
            notes: Additional notes
            activity_date: When the activity occurred (defaults to now)
            batch: Batch operation this activity belongs to
            status: Activity status
        
        Returns:
            StockActivity instance
        """
        
        # Get current stock before change
        quantity_before = item.stock_quantity
        
        # Apply the stock change
        with transaction.atomic():
            item.stock_quantity += quantity_changed
            item.save()
            
            quantity_after = item.stock_quantity
            
            # Create activity record
            activity = StockActivity.objects.create(
                activity_type=activity_type,
                status=status,
                content_type=ContentType.objects.get_for_model(item),
                object_id=item.pk,
                quantity_before=quantity_before,
                quantity_changed=quantity_changed,
                quantity_after=quantity_after,
                unit_cost=unit_cost,
                total_cost=unit_cost * abs(quantity_changed) if unit_cost else None,
                reason=reason,
                reference_number=reference_number,
                notes=notes,
                created_by=user,
                activity_date=activity_date or timezone.now(),
                batch=batch,
                ip_address=StockActivityService.get_client_ip(request) if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
            )
            
            return activity
    
    @staticmethod
    def stock_in(
        item: Union[Product, ProductVariant],
        quantity: int,
        reason: str,
        user,
        request=None,
        unit_cost: Optional[Decimal] = None,
        reference_number: str = "",
        notes: str = "",
        activity_date: Optional[timezone.datetime] = None
    ) -> StockActivity:
        """
        Record stock incoming activity
        """
        return StockActivityService.create_stock_activity(
            item=item,
            activity_type='stock_in',
            quantity_changed=abs(quantity),  # Ensure positive
            reason=reason,
            user=user,
            request=request,
            unit_cost=unit_cost,
            reference_number=reference_number,
            notes=notes,
            activity_date=activity_date
        )
    
    @staticmethod
    def stock_out(
        item: Union[Product, ProductVariant],
        quantity: int,
        reason: str,
        user,
        request=None,
        reference_number: str = "",
        notes: str = "",
        activity_date: Optional[timezone.datetime] = None
    ) -> StockActivity:
        """
        Record stock outgoing activity
        """
        # Check if sufficient stock is available
        if item.stock_quantity < quantity:
            raise ValueError(f"Insufficient stock. Available: {item.stock_quantity}, Requested: {quantity}")
        
        return StockActivityService.create_stock_activity(
            item=item,
            activity_type='stock_out',
            quantity_changed=-abs(quantity),  # Ensure negative
            reason=reason,
            user=user,
            request=request,
            reference_number=reference_number,
            notes=notes,
            activity_date=activity_date
        )
    
    @staticmethod
    def create_batch_operation(
        batch_type: str,
        description: str,
        user,
        batch_number: Optional[str] = None
    ) -> StockActivityBatch:
        """
        Create a batch operation for multiple stock activities
        """
        if not batch_number:
            batch_number = f"{batch_type.upper()}-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        batch = StockActivityBatch.objects.create(
            batch_type=batch_type,
            batch_number=batch_number,
            description=description,
            created_by=user
        )
        
        return batch
    
    @staticmethod
    def bulk_stock_adjustment(
        adjustments: List[Dict[str, Any]],
        user,
        request=None,
        batch_description: str = "Bulk Stock Adjustment"
    ) -> Dict[str, Any]:
        """
        Perform bulk stock adjustments with comprehensive tracking
        
        Args:
            adjustments: List of adjustment dictionaries with keys:
                - item: Product or ProductVariant instance
                - activity_type: 'stock_in' or 'stock_out'
                - quantity: Amount to adjust
                - reason: Reason for adjustment
                - unit_cost: Optional unit cost
                - reference_number: Optional reference
                - notes: Optional notes
            user: User performing the bulk operation
            request: HTTP request object
            batch_description: Description for the batch operation
        
        Returns:
            Dictionary with results summary
        """
        
        # Create batch operation
        batch = StockActivityService.create_batch_operation(
            batch_type='bulk_adjustment',
            description=batch_description,
            user=user
        )
        
        results = {
            'batch': batch,
            'successful_activities': [],
            'failed_activities': [],
            'total_processed': 0,
            'successful_count': 0,
            'failed_count': 0
        }
        
        for adjustment in adjustments:
            try:
                item = adjustment['item']
                activity_type = adjustment['activity_type']
                quantity = adjustment['quantity']
                reason = adjustment['reason']
                
                # Create the appropriate activity
                if activity_type == 'stock_in':
                    activity = StockActivityService.stock_in(
                        item=item,
                        quantity=quantity,
                        reason=reason,
                        user=user,
                        request=request,
                        unit_cost=adjustment.get('unit_cost'),
                        reference_number=adjustment.get('reference_number', ''),
                        notes=adjustment.get('notes', ''),
                        activity_date=adjustment.get('activity_date')
                    )
                elif activity_type == 'stock_out':
                    activity = StockActivityService.stock_out(
                        item=item,
                        quantity=quantity,
                        reason=reason,
                        user=user,
                        request=request,
                        reference_number=adjustment.get('reference_number', ''),
                        notes=adjustment.get('notes', ''),
                        activity_date=adjustment.get('activity_date')
                    )
                else:
                    raise ValueError(f"Invalid activity type: {activity_type}")
                
                # Link to batch
                activity.batch = batch
                activity.save()
                
                results['successful_activities'].append(activity)
                results['successful_count'] += 1
                
            except Exception as e:
                results['failed_activities'].append({
                    'item': adjustment.get('item'),
                    'error': str(e),
                    'adjustment': adjustment
                })
                results['failed_count'] += 1
            
            results['total_processed'] += 1
        
        # Update batch statistics
        batch.total_activities = results['total_processed']
        batch.completed_activities = results['successful_count']
        batch.failed_activities = results['failed_count']
        batch.is_completed = True
        batch.completed_at = timezone.now()
        batch.save()
        
        return results
    
    @staticmethod
    def get_item_stock_history(
        item: Union[Product, ProductVariant],
        limit: Optional[int] = None,
        activity_type: Optional[str] = None
    ) -> List[StockActivity]:
        """
        Get stock activity history for a specific item
        """
        content_type = ContentType.objects.get_for_model(item)
        queryset = StockActivity.objects.filter(
            content_type=content_type,
            object_id=item.pk
        ).select_related('created_by', 'batch')
        
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def get_user_activity_summary(
        user,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict[str, Any]:
        """
        Get activity summary for a specific user
        """
        queryset = StockActivity.objects.filter(created_by=user)
        
        if start_date:
            queryset = queryset.filter(activity_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(activity_date__lte=end_date)
        
        activities = list(queryset.select_related('batch'))
        
        summary = {
            'total_activities': len(activities),
            'stock_in_count': len([a for a in activities if a.activity_type == 'stock_in']),
            'stock_out_count': len([a for a in activities if a.activity_type == 'stock_out']),
            'total_items_added': sum(a.quantity_changed for a in activities if a.quantity_changed > 0),
            'total_items_removed': sum(abs(a.quantity_changed) for a in activities if a.quantity_changed < 0),
            'total_value_added': sum(a.total_cost for a in activities if a.total_cost and a.quantity_changed > 0),
            'activities': activities
        }
        
        return summary