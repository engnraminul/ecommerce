from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from datetime import timedelta

from .models import (
    PageCategory, PageTemplate, Page, PageRevision,
    PageMedia, PageComment, PageAnalytics
)
from .serializers import (
    PageCategorySerializer, PageTemplateSerializer, PageListSerializer,
    PageDetailSerializer, PageCreateUpdateSerializer, PageRevisionSerializer,
    PageMediaSerializer, PageCommentSerializer, PageAnalyticsSerializer,
    PageMenuSerializer, PageSitemapSerializer
)


class PageCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing page categories"""
    queryset = PageCategory.objects.all()
    serializer_class = PageCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class PageTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing page templates"""
    queryset = PageTemplate.objects.all()
    serializer_class = PageTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class PageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing pages"""
    queryset = Page.objects.select_related('category', 'template', 'author', 'last_modified_by').prefetch_related('media', 'comments')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'is_featured', 'show_in_menu', 'allow_comments', 'require_login']
    search_fields = ['title', 'content', 'meta_title', 'meta_description']
    ordering_fields = ['title', 'created_at', 'updated_at', 'publish_date', 'view_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PageListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PageCreateUpdateSerializer
        return PageDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = self.queryset
        
        # Filter by published status for non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                status='published',
                publish_date__lte=timezone.now()
            ).filter(
                Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
            )
        
        # Filter by author for non-admin users
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='published') | Q(author=self.request.user)
            )
            
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check login requirement
        if instance.require_login and not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required to view this page.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Increment view count for published pages
        if instance.is_published:
            instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def duplicate(self, request, pk=None):
        """Duplicate a page"""
        original = self.get_object()
        
        # Create duplicate
        duplicate_data = {
            'title': f"{original.title} (Copy)",
            'slug': f"{original.slug}-copy",
            'category': original.category,
            'template': original.template,
            'content': original.content,
            'excerpt': original.excerpt,
            'meta_title': original.meta_title,
            'meta_description': original.meta_description,
            'meta_keywords': original.meta_keywords,
            'status': 'draft',
            'author': request.user,
        }
        
        serializer = PageCreateUpdateSerializer(data=duplicate_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish(self, request, pk=None):
        """Publish a page"""
        page = self.get_object()
        
        if page.author != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You can only publish your own pages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        page.status = 'published'
        page.publish_date = timezone.now()
        page.save()
        
        return Response({'detail': 'Page published successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unpublish(self, request, pk=None):
        """Unpublish a page"""
        page = self.get_object()
        
        if page.author != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You can only unpublish your own pages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        page.status = 'draft'
        page.save()
        
        return Response({'detail': 'Page unpublished successfully.'})

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured pages"""
        featured_pages = self.get_queryset().filter(is_featured=True)
        serializer = PageListSerializer(featured_pages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def menu_items(self, request):
        """Get pages for menu navigation"""
        menu_pages = self.get_queryset().filter(
            show_in_menu=True,
            status='published'
        ).order_by('menu_order', 'title')
        
        serializer = PageMenuSerializer(menu_pages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sitemap(self, request):
        """Get pages for sitemap"""
        sitemap_pages = self.get_queryset().filter(status='published')
        serializer = PageSitemapSerializer(sitemap_pages, many=True)
        return Response(serializer.data)


class PageMediaViewSet(viewsets.ModelViewSet):
    """ViewSet for managing page media"""
    queryset = PageMedia.objects.select_related('page', 'uploaded_by')
    serializer_class = PageMediaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['media_type', 'is_featured', 'page']
    search_fields = ['title', 'alt_text', 'caption']
    ordering_fields = ['title', 'created_at', 'order']
    ordering = ['order', 'created_at']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class PageCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing page comments"""
    queryset = PageComment.objects.select_related('page', 'author', 'parent')
    serializer_class = PageCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['page', 'is_approved', 'parent']
    search_fields = ['content']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        queryset = self.queryset
        
        # Show only approved comments for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
            
        return queryset

    def perform_create(self, serializer):
        # Auto-approve comments from staff users
        is_approved = self.request.user.is_staff
        serializer.save(author=self.request.user, is_approved=is_approved)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a comment"""
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        return Response({'detail': 'Comment approved successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def unapprove(self, request, pk=None):
        """Unapprove a comment"""
        comment = self.get_object()
        comment.is_approved = False
        comment.save()
        return Response({'detail': 'Comment unapproved successfully.'})


class PageRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing page revisions"""
    queryset = PageRevision.objects.select_related('page', 'created_by')
    serializer_class = PageRevisionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['page']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restore(self, request, pk=None):
        """Restore a page to a specific revision"""
        revision = self.get_object()
        page = revision.page
        
        # Check permission
        if page.author != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You can only restore your own pages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create current revision before restoring
        PageRevision.objects.create(
            page=page,
            title=page.title,
            content=page.content,
            excerpt=page.excerpt,
            meta_title=page.meta_title,
            meta_description=page.meta_description,
            revision_note=f"Auto-saved before restoring to revision {revision.id}",
            created_by=request.user
        )
        
        # Restore page content
        page.title = revision.title
        page.content = revision.content
        page.excerpt = revision.excerpt
        page.meta_title = revision.meta_title
        page.meta_description = revision.meta_description
        page.last_modified_by = request.user
        page.save()
        
        return Response({'detail': 'Page restored successfully.'})


class PageAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing page analytics"""
    queryset = PageAnalytics.objects.select_related('page')
    serializer_class = PageAnalyticsSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['page', 'date']
    ordering_fields = ['date', 'views']
    ordering = ['-date']

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
        
        summary = queryset.aggregate(
            total_views=Count('views'),
            total_unique_views=Count('unique_views'),
            avg_bounce_rate=Avg('bounce_rate')
        )
        
        return Response(summary)


# Frontend views for displaying pages
def page_detail(request, slug):
    """Display a single page"""
    page = get_object_or_404(
        Page.objects.select_related('category', 'template', 'author')
        .prefetch_related('media', 'comments'),
        slug=slug
    )
    
    # Check if page is published
    if not page.is_published and not request.user.is_staff:
        if page.author != request.user:
            raise Http404("Page not found")
    
    # Check login requirement
    if page.require_login and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Increment view count
    if page.is_published:
        page.increment_view_count()
    
    # Get template
    template_name = 'pages/page_detail.html'
    if page.template and page.template.template_file:
        template_name = f'pages/{page.template.template_file}'
    
    context = {
        'page': page,
        'comments': page.comments.filter(parent=None, is_approved=True) if page.allow_comments else None,
        'related_pages': Page.objects.filter(
            category=page.category,
            status='published'
        ).exclude(id=page.id)[:3] if page.category else None,
    }
    
    return TemplateResponse(request, template_name, context)


def page_list(request):
    """Display list of pages"""
    pages = Page.objects.filter(
        status='published',
        publish_date__lte=timezone.now()
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
    ).select_related('category', 'author')
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        pages = pages.filter(category__slug=category_slug)
    
    # Search
    search = request.GET.get('search')
    if search:
        pages = pages.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(excerpt__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(pages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = PageCategory.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search,
    }
    
    return TemplateResponse(request, 'pages/page_list.html', context)


def page_category(request, slug):
    """Display pages in a category"""
    category = get_object_or_404(PageCategory, slug=slug, is_active=True)
    
    pages = Page.objects.filter(
        category=category,
        status='published',
        publish_date__lte=timezone.now()
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
    ).select_related('author')
    
    # Pagination
    paginator = Paginator(pages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return TemplateResponse(request, 'pages/category.html', context)


# API views
@api_view(['GET'])
@permission_classes([AllowAny])
def page_search(request):
    """Search pages API endpoint"""
    query = request.GET.get('q', '')
    
    if not query:
        return Response({'results': []})
    
    pages = Page.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(excerpt__icontains=query),
        status='published'
    ).select_related('category', 'author')[:10]
    
    serializer = PageListSerializer(pages, many=True)
    return Response({'results': serializer.data})


@api_view(['GET'])
@permission_classes([AllowAny])
def page_statistics(request):
    """Get page statistics"""
    stats = {
        'total_pages': Page.objects.filter(status='published').count(),
        'total_categories': PageCategory.objects.filter(is_active=True).count(),
        'total_views': Page.objects.aggregate(total=Count('view_count'))['total'] or 0,
        'recent_pages': PageListSerializer(
            Page.objects.filter(status='published').order_by('-created_at')[:5],
            many=True
        ).data,
        'popular_pages': PageListSerializer(
            Page.objects.filter(status='published').order_by('-view_count')[:5],
            many=True
        ).data,
    }
    
    return Response(stats)
