"""
Forms for pages management.
"""
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Page, PageCategory, PageTemplate


class PageForm(forms.ModelForm):
    """Form for page management with custom CKEditor configuration."""
    
    content = forms.CharField(
        widget=CKEditorUploadingWidget(config_name='pages'),
        required=False,
        help_text="Main page content with rich text editor"
    )
    
    class Meta:
        model = Page
        fields = [
            'title', 'slug', 'category', 'template', 'content', 'excerpt',
            'featured_image', 'featured_image_alt', 'meta_title', 'meta_description',
            'meta_keywords', 'canonical_url', 'status', 'is_featured', 'show_in_menu',
            'menu_order', 'require_login', 'publish_date', 'expiry_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter page title'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'auto-generated-from-title'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description for meta tags and previews'}),
            'featured_image_alt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alt text for featured image'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO title (max 60 characters)', 'maxlength': 60}),
            'meta_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO description (max 160 characters)', 'maxlength': 160}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO keywords, comma separated'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/canonical-url'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'menu_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'publish_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expiry_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_in_menu': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_login': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make slug field read-only if this is an edit form
        if self.instance.pk:
            self.fields['slug'].widget.attrs['readonly'] = True
            self.fields['slug'].help_text = "Slug cannot be changed after page creation"
        
        # Add CSS classes and help text
        self.fields['category'].empty_label = "Select a category (optional)"
        self.fields['template'].empty_label = "Select a template (optional)"
        
        # Set required fields
        self.fields['title'].required = True
        self.fields['content'].required = False

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if not slug:
            # Auto-generate slug from title
            from django.utils.text import slugify
            slug = slugify(self.cleaned_data.get('title', ''))
        
        # Check for uniqueness
        if Page.objects.filter(slug=slug).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(f"A page with slug '{slug}' already exists.")
        
        return slug

    def clean(self):
        cleaned_data = super().clean()
        publish_date = cleaned_data.get('publish_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if publish_date and expiry_date and publish_date >= expiry_date:
            raise forms.ValidationError("Expiry date must be after publish date.")
        
        return cleaned_data


class PageCategoryForm(forms.ModelForm):
    """Form for page category management."""
    
    class Meta:
        model = PageCategory
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PageTemplateForm(forms.ModelForm):
    """Form for page template management."""
    
    class Meta:
        model = PageTemplate
        fields = ['name', 'slug', 'template_type', 'template_file', 'description', 'preview_image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'template_file': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'templates/pages/template.html'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuickPageForm(forms.ModelForm):
    """Simplified form for quick page creation."""
    
    content = forms.CharField(
        widget=CKEditorUploadingWidget(config_name='pages'),
        required=False,
        help_text="Main page content"
    )
    
    class Meta:
        model = Page
        fields = ['title', 'content', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter page title'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }