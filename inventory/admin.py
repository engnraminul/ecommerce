from django.contrib import admin
from .models import StockActivity, StockActivityBatch


@admin.register(StockActivity)
class StockActivityAdmin(admin.ModelAdmin):
    list_display = [
        'activity_date', 'activity_type', 'item_name', 'quantity_changed', 
        'quantity_after', 'created_by', 'status'
    ]
    list_filter = [
        'activity_type', 'status', 'activity_date', 'created_at', 'content_type'
    ]
    search_fields = ['reason', 'reference_number', 'notes']
    readonly_fields = [
        'created_at', 'updated_at', 'ip_address', 'user_agent'
    ]
    date_hierarchy = 'activity_date'
    
    fieldsets = (
        ('Activity Information', {
            'fields': (
                'activity_type', 'status', 'content_type', 'object_id', 
                'activity_date'
            )
        }),
        ('Stock Details', {
            'fields': (
                'quantity_before', 'quantity_changed', 'quantity_after',
                'unit_cost', 'total_cost'
            )
        }),
        ('Activity Details', {
            'fields': ('reason', 'reference_number', 'notes', 'batch')
        }),
        ('User Information', {
            'fields': ('created_by', 'approved_by')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )


@admin.register(StockActivityBatch)
class StockActivityBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'batch_type', 'total_activities', 
        'completed_activities', 'success_rate', 'created_by', 'is_completed'
    ]
    list_filter = ['batch_type', 'is_completed', 'created_at']
    search_fields = ['batch_number', 'description']
    readonly_fields = [
        'created_at', 'completed_at', 'total_activities', 
        'completed_activities', 'failed_activities'
    ]