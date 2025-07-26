import django_filters
from django.db.models import Q
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """Product filter set"""
    
    # Price range filters
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Category filter
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    
    # Stock filter
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    # Featured filter
    featured = django_filters.BooleanFilter(field_name='is_featured')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Product
        fields = ['category', 'is_featured', 'is_digital']
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock"""
        if value:
            return queryset.filter(
                Q(track_inventory=False) | 
                Q(track_inventory=True, stock_quantity__gt=0)
            )
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search filter for product name, description, and category"""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(short_description__icontains=value) |
                Q(category__name__icontains=value)
            )
        return queryset
