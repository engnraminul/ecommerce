from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PageCategory, PageTemplate, Page, PageRevision, 
    PageMedia, PageComment, PageAnalytics
)

User = get_user_model()


class PageCategorySerializer(serializers.ModelSerializer):
    pages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PageCategory
        fields = [
            'id', 'name', 'slug', 'description', 'is_active', 
            'pages_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_pages_count(self, obj):
        return obj.pages.filter(status='published').count()


class PageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageTemplate
        fields = [
            'id', 'name', 'slug', 'template_type', 'template_file',
            'description', 'preview_image', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PageMediaSerializer(serializers.ModelSerializer):
    file_size = serializers.ReadOnlyField()
    uploaded_by = AuthorSerializer(read_only=True)
    
    class Meta:
        model = PageMedia
        fields = [
            'id', 'title', 'media_type', 'file', 'alt_text', 'caption',
            'order', 'is_featured', 'file_size', 'uploaded_by', 'created_at'
        ]
        read_only_fields = ['uploaded_by', 'created_at']


class PageCommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = PageComment
        fields = [
            'id', 'content', 'author', 'parent', 'is_approved',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_replies(self, obj):
        if obj.replies.exists():
            return PageCommentSerializer(
                obj.replies.filter(is_approved=True), 
                many=True, 
                context=self.context
            ).data
        return []


class PageRevisionSerializer(serializers.ModelSerializer):
    created_by = AuthorSerializer(read_only=True)
    
    class Meta:
        model = PageRevision
        fields = [
            'id', 'title', 'content', 'excerpt', 'meta_title',
            'meta_description', 'revision_note', 'created_by', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']


class PageListSerializer(serializers.ModelSerializer):
    """Serializer for page list views with limited fields"""
    category = PageCategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    reading_time = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Page
        fields = [
            'id', 'title', 'slug', 'category', 'excerpt', 'featured_image',
            'featured_image_alt', 'status', 'is_featured', 'show_in_menu',
            'menu_order', 'author', 'reading_time', 'is_published', 
            'view_count', 'publish_date', 'created_at', 'updated_at'
        ]


class PageDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed page views"""
    category = PageCategorySerializer(read_only=True)
    template = PageTemplateSerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    last_modified_by = AuthorSerializer(read_only=True)
    media = PageMediaSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    revisions = PageRevisionSerializer(many=True, read_only=True)
    reading_time = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Page
        fields = [
            'id', 'title', 'slug', 'category', 'template', 'content', 'excerpt',
            'featured_image', 'featured_image_alt', 'meta_title', 'meta_description',
            'meta_keywords', 'canonical_url', 'status', 'is_featured', 'show_in_menu',
            'menu_order', 'allow_comments', 'require_login', 'publish_date',
            'expiry_date', 'author', 'last_modified_by', 'view_count', 'share_count',
            'reading_time', 'is_published', 'media', 'comments', 'revisions',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'author', 'last_modified_by', 'view_count', 'share_count',
            'created_at', 'updated_at'
        ]

    def get_comments(self, obj):
        if obj.allow_comments:
            comments = obj.comments.filter(parent=None, is_approved=True)
            return PageCommentSerializer(comments, many=True, context=self.context).data
        return []


class PageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating pages"""
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    template_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Page
        fields = [
            'id', 'title', 'slug', 'category_id', 'template_id', 'content', 'excerpt',
            'featured_image', 'featured_image_alt', 'meta_title', 'meta_description',
            'meta_keywords', 'canonical_url', 'status', 'is_featured', 'show_in_menu',
            'menu_order', 'allow_comments', 'require_login', 'publish_date', 'expiry_date'
        ]
        read_only_fields = ['id']

    def validate_slug(self, value):
        """Validate slug uniqueness"""
        page_id = self.instance.id if self.instance else None
        if Page.objects.filter(slug=value).exclude(id=page_id).exists():
            raise serializers.ValidationError("A page with this slug already exists.")
        return value

    def validate(self, attrs):
        """Validate publish and expiry dates"""
        publish_date = attrs.get('publish_date')
        expiry_date = attrs.get('expiry_date')
        
        if publish_date and expiry_date and publish_date >= expiry_date:
            raise serializers.ValidationError(
                "Expiry date must be after publish date."
            )
        return attrs

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        template_id = validated_data.pop('template_id', None)
        
        if category_id:
            validated_data['category'] = PageCategory.objects.get(id=category_id)
        if template_id:
            validated_data['template'] = PageTemplate.objects.get(id=template_id)
            
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        template_id = validated_data.pop('template_id', None)
        
        if category_id:
            validated_data['category'] = PageCategory.objects.get(id=category_id)
        elif category_id is None:
            validated_data['category'] = None
            
        if template_id:
            validated_data['template'] = PageTemplate.objects.get(id=template_id)
        elif template_id is None:
            validated_data['template'] = None
            
        validated_data['last_modified_by'] = self.context['request'].user
        
        # Create revision before updating
        PageRevision.objects.create(
            page=instance,
            title=instance.title,
            content=instance.content,
            excerpt=instance.excerpt,
            meta_title=instance.meta_title,
            meta_description=instance.meta_description,
            revision_note=f"Auto-saved before update at {instance.updated_at}",
            created_by=self.context['request'].user
        )
        
        return super().update(instance, validated_data)


class PageAnalyticsSerializer(serializers.ModelSerializer):
    page_title = serializers.CharField(source='page.title', read_only=True)
    
    class Meta:
        model = PageAnalytics
        fields = [
            'id', 'page', 'page_title', 'date', 'views', 'unique_views',
            'bounce_rate', 'avg_time_on_page'
        ]


class PageMenuSerializer(serializers.ModelSerializer):
    """Serializer for menu navigation"""
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'menu_order']


class PageSitemapSerializer(serializers.ModelSerializer):
    """Serializer for sitemap generation"""
    class Meta:
        model = Page
        fields = ['slug', 'updated_at', 'publish_date']