"""
Email settings views for dashboard.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import EmailConfiguration, EmailTemplate, EmailLog
from .email_forms import (
    EmailConfigurationForm, EmailTemplateForm, TestEmailForm,
    EmailTemplatePreviewForm, BulkEmailForm
)
from .email_service import email_service


@staff_member_required
def email_settings_index(request):
    """Email settings dashboard index."""
    # Get active configuration
    active_config = EmailConfiguration.get_active_config()
    
    # Get template counts
    active_templates = EmailTemplate.objects.filter(is_active=True).count()
    total_templates = EmailTemplate.objects.count()
    
    # Get recent email logs
    recent_logs = EmailLog.objects.select_related('template', 'user', 'email_config')[:10]
    
    # Get email statistics
    from django.db.models import Count
    today = timezone.now().date()
    
    stats = {
        'total_sent': EmailLog.objects.filter(status='sent').count(),
        'total_failed': EmailLog.objects.filter(status='failed').count(),
        'sent_today': EmailLog.objects.filter(status='sent', created_at__date=today).count(),
        'failed_today': EmailLog.objects.filter(status='failed', created_at__date=today).count(),
    }
    
    context = {
        'active_config': active_config,
        'active_templates': active_templates,
        'total_templates': total_templates,
        'recent_logs': recent_logs,
        'stats': stats,
        'active_page': 'email_settings',  # Add this for navigation
    }
    
    return render(request, 'dashboard/email_settings/index.html', context)


@staff_member_required
def email_configuration_list(request):
    """List all email configurations."""
    configurations = EmailConfiguration.objects.all().order_by('-is_active', '-created_at')
    
    context = {
        'configurations': configurations,
        'active_page': 'email_settings',
    }
    
    return render(request, 'dashboard/email_settings/configuration_list.html', context)


@staff_member_required
def email_configuration_create(request):
    """Create new email configuration."""
    if request.method == 'POST':
        form = EmailConfigurationForm(request.POST)
        if form.is_valid():
            configuration = form.save()
            messages.success(request, f'Email configuration "{configuration.name}" created successfully.')
            return redirect('dashboard:email_configuration_list')
    else:
        form = EmailConfigurationForm()
    
    context = {
        'form': form,
        'title': 'Create Email Configuration',
    }
    
    return render(request, 'dashboard/email_settings/configuration_form.html', context)


@staff_member_required
def email_configuration_edit(request, pk):
    """Edit email configuration."""
    configuration = get_object_or_404(EmailConfiguration, pk=pk)
    
    if request.method == 'POST':
        form = EmailConfigurationForm(request.POST, instance=configuration)
        if form.is_valid():
            configuration = form.save()
            messages.success(request, f'Email configuration "{configuration.name}" updated successfully.')
            return redirect('dashboard:email_configuration_list')
    else:
        form = EmailConfigurationForm(instance=configuration)
    
    context = {
        'form': form,
        'configuration': configuration,
        'title': 'Edit Email Configuration',
    }
    
    return render(request, 'dashboard/email_settings/configuration_form.html', context)


@staff_member_required
def email_configuration_delete(request, pk):
    """Delete email configuration."""
    configuration = get_object_or_404(EmailConfiguration, pk=pk)
    
    if request.method == 'POST':
        name = configuration.name
        configuration.delete()
        messages.success(request, f'Email configuration "{name}" deleted successfully.')
        return redirect('dashboard:email_configuration_list')
    
    context = {
        'configuration': configuration,
    }
    
    return render(request, 'dashboard/email_settings/configuration_delete.html', context)


@staff_member_required
def email_configuration_test(request, pk):
    """Test email configuration."""
    configuration = get_object_or_404(EmailConfiguration, pk=pk)
    
    if request.method == 'POST':
        form = TestEmailForm(request.POST)
        if form.is_valid():
            test_email = form.cleaned_data['test_email']
            
            # Test the configuration
            result = email_service.test_email_configuration(configuration.id, test_email)
            
            if result['success']:
                messages.success(request, f'Test email sent successfully to {test_email}')
            else:
                messages.error(request, f'Failed to send test email: {result["message"]}')
            
            return redirect('dashboard:email_configuration_list')
    else:
        form = TestEmailForm()
    
    context = {
        'form': form,
        'configuration': configuration,
    }
    
    return render(request, 'dashboard/email_settings/configuration_test.html', context)


@staff_member_required
def email_configuration_activate(request, pk):
    """Activate email configuration."""
    if request.method == 'POST':
        configuration = get_object_or_404(EmailConfiguration, pk=pk)
        
        # Deactivate all other configurations
        EmailConfiguration.objects.update(is_active=False)
        
        # Activate this configuration
        configuration.is_active = True
        configuration.save()
        
        messages.success(request, f'Email configuration "{configuration.name}" activated successfully.')
    
    return redirect('dashboard:email_configuration_list')


@staff_member_required
def email_template_list(request):
    """List all email templates."""
    templates = EmailTemplate.objects.all().order_by('template_type', 'name')
    
    context = {
        'templates': templates,
        'active_page': 'email_settings',
    }
    
    return render(request, 'dashboard/email_settings/template_list.html', context)


@staff_member_required
def email_template_create(request):
    """Create new email template."""
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Email template "{template.name}" created successfully.')
            return redirect('dashboard:email_template_list')
    else:
        form = EmailTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create Email Template',
    }
    
    return render(request, 'dashboard/email_settings/template_form.html', context)


@staff_member_required
def email_template_edit(request, pk):
    """Edit email template."""
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Email template "{template.name}" updated successfully.')
            return redirect('dashboard:email_template_list')
    else:
        form = EmailTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': 'Edit Email Template',
    }
    
    return render(request, 'dashboard/email_settings/template_form.html', context)


@staff_member_required
def email_template_delete(request, pk):
    """Delete email template."""
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        name = template.name
        template.delete()
        messages.success(request, f'Email template "{name}" deleted successfully.')
        return redirect('dashboard:email_template_list')
    
    context = {
        'template': template,
    }
    
    return render(request, 'dashboard/email_settings/template_delete.html', context)


@staff_member_required
def email_template_preview(request, pk):
    """Preview email template with sample data."""
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        form = EmailTemplatePreviewForm(request.POST)
        if form.is_valid():
            # Generate preview with sample data
            context = {
                'user_name': form.cleaned_data['user_name'],
                'user_email': form.cleaned_data['user_email'],
                'order_number': form.cleaned_data['order_number'],
                'order_total': form.cleaned_data['order_total'],
                'site_name': 'Your Store',
                'site_url': request.build_absolute_uri('/'),
                'current_year': timezone.now().year,
            }
            
            rendered_subject = template.get_rendered_subject(context)
            rendered_content = template.get_rendered_content(context)
            
            return JsonResponse({
                'subject': rendered_subject,
                'html_content': rendered_content,
                'text_content': strip_tags(rendered_content),
            })
    else:
        form = EmailTemplatePreviewForm(initial={'template_id': template.id})
    
    context = {
        'template': template,
        'form': form,
    }
    
    return render(request, 'dashboard/email_settings/template_preview.html', context)


@staff_member_required
def email_log_list(request):
    """List email logs with filtering and pagination."""
    logs = EmailLog.objects.select_related('template', 'user', 'email_config', 'order').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        logs = logs.filter(status=status_filter)
    
    # Filter by template
    template_filter = request.GET.get('template')
    if template_filter:
        logs = logs.filter(template_id=template_filter)
    
    # Search by email
    search = request.GET.get('search')
    if search:
        logs = logs.filter(
            Q(recipient_email__icontains=search) |
            Q(subject__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    templates = EmailTemplate.objects.all()
    
    context = {
        'page_obj': page_obj,
        'templates': templates,
        'current_status': status_filter,
        'current_template': template_filter,
        'current_search': search,
    }
    
    return render(request, 'dashboard/email_settings/log_list.html', context)


@staff_member_required
def email_log_detail(request, pk):
    """View email log details."""
    log = get_object_or_404(EmailLog, pk=pk)
    
    context = {
        'log': log,
    }
    
    return render(request, 'dashboard/email_settings/log_detail.html', context)


@staff_member_required
def bulk_email(request):
    """Send bulk emails."""
    if request.method == 'POST':
        form = BulkEmailForm(request.POST)
        if form.is_valid():
            # This would implement bulk email sending
            # For now, just show a success message
            messages.success(request, 'Bulk email job queued successfully.')
            return redirect('dashboard:email_log_list')
    else:
        form = BulkEmailForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/email_settings/bulk_email.html', context)


@staff_member_required
def ajax_get_smtp_defaults(request):
    """Get default SMTP settings for a given type via AJAX."""
    smtp_type = request.GET.get('type')
    
    defaults = {
        'gmail': {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_use_tls': True,
            'smtp_use_ssl': False,
        },
        'business': {
            'smtp_host': '',
            'smtp_port': 587,
            'smtp_use_tls': True,
            'smtp_use_ssl': False,
        }
    }
    
    return JsonResponse(defaults.get(smtp_type, {}))


@staff_member_required
def ajax_template_variables(request, pk):
    """Get available variables for a template type via AJAX."""
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    # Define available variables for each template type
    variables = {
        'welcome': ['user_name', 'user_email', 'site_name', 'site_url'],
        'activation': ['user_name', 'user_email', 'activation_url', 'activation_token', 'site_name'],
        'password_reset': ['user_name', 'user_email', 'reset_url', 'reset_token', 'site_name'],
        'order_confirmed': ['user_name', 'order_number', 'order_total', 'order_date', 'site_name'],
        'order_shipped': ['user_name', 'order_number', 'tracking_number', 'carrier', 'site_name'],
        'order_delivered': ['user_name', 'order_number', 'delivery_date', 'site_name'],
        'order_cancelled': ['user_name', 'order_number', 'cancellation_reason', 'site_name'],
    }
    
    return JsonResponse({
        'variables': variables.get(template.template_type, [])
    })