from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone

from pages.models import (
    PageCategory, PageTemplate, Page, PageRevision,
    PageMedia, PageAnalytics
)
from pages.serializers import (
    PageCategorySerializer, PageTemplateSerializer, PageListSerializer,
    PageDetailSerializer, PageCreateUpdateSerializer, PageRevisionSerializer,
    PageMediaSerializer, PageAnalyticsSerializer
)


class PageDashboardViewSet(viewsets.ModelViewSet):
    """Dashboard ViewSet for managing pages"""
    queryset = Page.objects.select_related('category', 'template', 'author', 'last_modified_by').prefetch_related('media', 'comments')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'is_featured', 'show_in_menu', 'allow_comments', 'require_login', 'author']
    search_fields = ['title', 'content', 'meta_title', 'meta_description']
    ordering_fields = ['title', 'created_at', 'updated_at', 'publish_date', 'view_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PageListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PageCreateUpdateSerializer
        return PageDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by author for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(author=self.request.user)
            
        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get page statistics for dashboard"""
        queryset = self.get_queryset()
        
        stats = {
            'total_pages': queryset.count(),
            'published_pages': queryset.filter(status='published').count(),
            'draft_pages': queryset.filter(status='draft').count(),
            'archived_pages': queryset.filter(status='archived').count(),
            'featured_pages': queryset.filter(is_featured=True).count(),
            'total_views': queryset.aggregate(total=Count('view_count'))['total'] or 0,
            'recent_pages': PageListSerializer(
                queryset.order_by('-created_at')[:5],
                many=True
            ).data,
            'popular_pages': PageListSerializer(
                queryset.filter(status='published').order_by('-view_count')[:5],
                many=True
            ).data,
        }
        
        # Add time-based statistics
        today = timezone.now().date()
        week_ago = today - timezone.timedelta(days=7)
        month_ago = today - timezone.timedelta(days=30)
        
        stats.update({
            'pages_created_today': queryset.filter(created_at__date=today).count(),
            'pages_created_this_week': queryset.filter(created_at__date__gte=week_ago).count(),
            'pages_created_this_month': queryset.filter(created_at__date__gte=month_ago).count(),
        })
        
        return Response(stats)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a page"""
        original = self.get_object()
        
        # Create duplicate with modified title and slug
        duplicate_data = {
            'title': f"{original.title} (Copy)",
            'slug': f"{original.slug}-copy-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            'category_id': original.category.id if original.category else None,
            'template_id': original.template.id if original.template else None,
            'content': original.content,
            'excerpt': original.excerpt,
            'meta_title': original.meta_title,
            'meta_description': original.meta_description,
            'meta_keywords': original.meta_keywords,
            'status': 'draft',
            'is_featured': False,
            'show_in_menu': False,
            'allow_comments': original.allow_comments,
            'require_login': original.require_login,
        }
        
        serializer = PageCreateUpdateSerializer(data=duplicate_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def quick_publish(self, request, pk=None):
        """Quickly publish/unpublish a page"""
        page = self.get_object()
        
        if page.status == 'published':
            page.status = 'draft'
            message = 'Page unpublished successfully'
        else:
            page.status = 'published'
            page.publish_date = timezone.now()
            message = 'Page published successfully'
        
        page.last_modified_by = request.user
        page.save()
        
        return Response({
            'detail': message,
            'status': page.status,
            'publish_date': page.publish_date
        })

    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """Toggle featured status of a page"""
        page = self.get_object()
        page.is_featured = not page.is_featured
        page.last_modified_by = request.user
        page.save()
        
        return Response({
            'detail': f'Page {"featured" if page.is_featured else "unfeatured"} successfully',
            'is_featured': page.is_featured
        })

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on multiple pages"""
        page_ids = request.data.get('page_ids', [])
        action_type = request.data.get('action')
        
        if not page_ids:
            return Response({'error': 'No pages selected'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(id__in=page_ids)
        
        if action_type == 'publish':
            updated = queryset.update(status='published', publish_date=timezone.now())
            message = f'{updated} pages published successfully'
        elif action_type == 'unpublish':
            updated = queryset.update(status='draft')
            message = f'{updated} pages unpublished successfully'
        elif action_type == 'archive':
            updated = queryset.update(status='archived')
            message = f'{updated} pages archived successfully'
        elif action_type == 'feature':
            updated = queryset.update(is_featured=True)
            message = f'{updated} pages featured successfully'
        elif action_type == 'unfeature':
            updated = queryset.update(is_featured=False)
            message = f'{updated} pages unfeatured successfully'
        elif action_type == 'delete':
            count = queryset.count()
            queryset.delete()
            message = f'{count} pages deleted successfully'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'detail': message})


class PageCategoryDashboardViewSet(viewsets.ModelViewSet):
    """Dashboard ViewSet for managing page categories"""
    queryset = PageCategory.objects.annotate(pages_count=Count('pages'))
    serializer_class = PageCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'pages_count']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get category statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_categories': queryset.count(),
            'active_categories': queryset.filter(is_active=True).count(),
            'inactive_categories': queryset.filter(is_active=False).count(),
            'categories_with_pages': queryset.filter(pages_count__gt=0).count(),
            'empty_categories': queryset.filter(pages_count=0).count(),
        }
        
        return Response(stats)


class PageTemplateDashboardViewSet(viewsets.ModelViewSet):
    """Dashboard ViewSet for managing page templates"""
    queryset = PageTemplate.objects.all()
    serializer_class = PageTemplateSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class PageMediaDashboardViewSet(viewsets.ModelViewSet):
    """Dashboard ViewSet for managing page media"""
    queryset = PageMedia.objects.select_related('page', 'uploaded_by')
    serializer_class = PageMediaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['media_type', 'is_featured', 'page']
    search_fields = ['title', 'alt_text', 'caption']
    ordering_fields = ['title', 'created_at', 'order']
    ordering = ['order', 'created_at']

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by user's pages for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(page__author=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class PageAnalyticsDashboardViewSet(viewsets.ReadOnlyModelViewSet):
    """Dashboard ViewSet for viewing page analytics"""
    queryset = PageAnalytics.objects.select_related('page')
    serializer_class = PageAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['page', 'date']
    ordering_fields = ['date', 'views', 'unique_views']
    ordering = ['-date']

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by user's pages for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(page__author=self.request.user)
            
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get analytics summary"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Aggregate data
        total_views = sum(analytics.views for analytics in queryset)
        total_unique_views = sum(analytics.unique_views for analytics in queryset)
        avg_bounce_rate = queryset.aggregate(avg_bounce=Count('bounce_rate'))['avg_bounce'] or 0
        
        # Top performing pages
        page_performance = {}
        for analytics in queryset:
            page_id = analytics.page.id
            if page_id not in page_performance:
                page_performance[page_id] = {
                    'page': analytics.page.title,
                    'views': 0,
                    'unique_views': 0
                }
            page_performance[page_id]['views'] += analytics.views
            page_performance[page_id]['unique_views'] += analytics.unique_views
        
        top_pages = sorted(
            page_performance.values(),
            key=lambda x: x['views'],
            reverse=True
        )[:10]
        
        return Response({
            'total_views': total_views,
            'total_unique_views': total_unique_views,
            'average_bounce_rate': avg_bounce_rate,
            'top_pages': top_pages,
            'date_range': {
                'from': date_from,
                'to': date_to
            }
        })