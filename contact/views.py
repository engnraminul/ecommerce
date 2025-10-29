from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count

from .models import Contact, ContactSetting, ContactActivity
from .serializers import ContactSerializer, ContactSubmissionSerializer, ContactSettingSerializer
from dashboard.models import BlockList


class IsStaffUser(permissions.BasePermission):
    """Custom permission to match dashboard view requirements"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class ContactDashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contact submissions in dashboard"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'priority', 'assigned_to']
    search_fields = ['name', 'email', 'phone', 'subject', 'message']
    ordering_fields = ['submitted_at', 'updated_at', 'priority', 'status']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        """Enhanced queryset with filtering options"""
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by unread (new status)
        unread_only = self.request.query_params.get('unread_only')
        if unread_only and unread_only.lower() == 'true':
            queryset = queryset.filter(status='new')
        
        # Filter by urgent
        urgent_only = self.request.query_params.get('urgent_only')
        if urgent_only and urgent_only.lower() == 'true':
            two_days_ago = timezone.now() - timedelta(days=2)
            queryset = queryset.filter(
                Q(priority='urgent') |
                Q(status='new', submitted_at__lte=two_days_ago)
            )
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                start_date = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(submitted_at__date__gte=start_date.date())
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                end_date = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(submitted_at__date__lte=end_date.date())
            except ValueError:
                pass
        
        return queryset
    
    def perform_update(self, serializer):
        """Handle contact updates with activity logging"""
        instance = serializer.save()
        try:
            self.log_activity('updated', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
    
    def perform_destroy(self, instance):
        """Handle contact deletion with activity logging"""
        try:
            self.log_activity('deleted', instance)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        instance.delete()
    
    def log_activity(self, action, instance):
        """Log admin activity for contact management"""
        try:
            ContactActivity.objects.create(
                contact=instance,
                user=self.request.user,
                action=action,
                description=f"Contact {action} by {self.request.user.username}",
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Failed to log activity: {str(e)}")
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a contact as read and assign to current user"""
        contact = self.get_object()
        contact.mark_as_read(user=request.user)
        
        try:
            self.log_activity('marked_as_read', contact)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        return Response({
            'success': True,
            'status': contact.status,
            'assigned_to': contact.assigned_to.username if contact.assigned_to else None
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_replied(self, request, pk=None):
        """Mark a contact as replied"""
        contact = self.get_object()
        contact.mark_as_replied(user=request.user)
        
        try:
            self.log_activity('marked_as_replied', contact)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        return Response({
            'success': True,
            'status': contact.status,
            'replied_at': contact.replied_at,
            'assigned_to': contact.assigned_to.username if contact.assigned_to else None
        })
    
    @action(detail=True, methods=['post'])
    def update_priority(self, request, pk=None):
        """Update contact priority"""
        contact = self.get_object()
        new_priority = request.data.get('priority')
        
        if new_priority not in dict(Contact.PRIORITY_CHOICES):
            return Response({'error': 'Invalid priority'}, status=400)
        
        old_priority = contact.priority
        contact.priority = new_priority
        contact.save()
        
        try:
            self.log_activity(f'priority_changed_from_{old_priority}_to_{new_priority}', contact)
        except Exception as e:
            print(f"Error logging activity: {str(e)}")
        
        return Response({
            'success': True,
            'priority': contact.priority,
            'is_urgent': contact.is_urgent
        })
    
    @action(detail=True, methods=['post'])
    def assign_to_user(self, request, pk=None):
        """Assign contact to a specific user"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        contact = self.get_object()
        user_id = request.data.get('user_id')
        
        if user_id:
            try:
                assignee = User.objects.get(id=user_id, is_staff=True)
                contact.assigned_to = assignee
                contact.save()
                
                try:
                    self.log_activity(f'assigned_to_{assignee.username}', contact)
                except Exception as e:
                    print(f"Error logging activity: {str(e)}")
                
                return Response({
                    'success': True,
                    'assigned_to': assignee.username
                })
            except User.DoesNotExist:
                return Response({'error': 'User not found or not staff'}, status=400)
        else:
            # Unassign
            contact.assigned_to = None
            contact.save()
            
            try:
                self.log_activity('unassigned', contact)
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return Response({
                'success': True,
                'assigned_to': None
            })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get contact statistics for dashboard"""
        total_contacts = Contact.objects.count()
        new_contacts = Contact.objects.filter(status='new').count()
        pending_contacts = Contact.objects.filter(status__in=['new', 'read']).count()
        urgent_contacts = Contact.objects.filter(priority='urgent').count()
        
        # Contacts from last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        recent_contacts = Contact.objects.filter(submitted_at__gte=week_ago).count()
        
        return Response({
            'total_contacts': total_contacts,
            'new_contacts': new_contacts,
            'pending_contacts': pending_contacts,
            'urgent_contacts': urgent_contacts,
            'recent_contacts': recent_contacts
        })
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on contacts"""
        contact_ids = request.data.get('contact_ids', [])
        action = request.data.get('action')
        
        if not contact_ids:
            return Response({'error': 'No contact IDs provided'}, status=400)
        
        if not action:
            return Response({'error': 'No action specified'}, status=400)
        
        contacts = Contact.objects.filter(id__in=contact_ids)
        updated_count = 0
        
        try:
            if action == 'mark_as_read':
                for contact in contacts:
                    if contact.status == 'new':
                        contact.mark_as_read()
                        updated_count += 1
                        
            elif action == 'mark_as_spam':
                contacts.update(status='spam')
                updated_count = contacts.count()
                
            elif action == 'delete':
                deleted_count = contacts.count()
                contacts.delete()
                return Response({
                    'success': True,
                    'message': f'Successfully deleted {deleted_count} contact(s)'
                })
                
            elif action in ['low', 'medium', 'high', 'urgent']:
                contacts.update(priority=action)
                updated_count = contacts.count()
                
            elif action in ['new', 'read', 'replied', 'resolved']:
                contacts.update(status=action)
                updated_count = contacts.count()
            
            else:
                return Response({'error': 'Invalid action'}, status=400)
            
            # Log bulk action
            try:
                ContactActivity.objects.create(
                    contact=contacts.first() if contacts.exists() else None,
                    user=request.user,
                    action=f'bulk_{action}',
                    description=f'Bulk {action} applied to {updated_count} contacts',
                    ip_address=self.get_client_ip(),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                print(f"Error logging activity: {str(e)}")
            
            return Response({
                'success': True,
                'message': f'Successfully updated {updated_count} contact(s)'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class ContactPublicViewSet(viewsets.ModelViewSet):
    """Public API for contact form submission"""
    queryset = Contact.objects.none()  # No list/detail access
    serializer_class = ContactSubmissionSerializer
    permission_classes = []  # Public access
    
    def get_queryset(self):
        # Only allow creation, no list/detail access
        return Contact.objects.none()
    
    def list(self, request, *args, **kwargs):
        # Disable list action
        return Response({'error': 'Not allowed'}, status=405)
    
    def retrieve(self, request, *args, **kwargs):
        # Disable retrieve action
        return Response({'error': 'Not allowed'}, status=405)
    
    def update(self, request, *args, **kwargs):
        # Disable update action
        return Response({'error': 'Not allowed'}, status=405)
    
    def partial_update(self, request, *args, **kwargs):
        # Disable partial update action
        return Response({'error': 'Not allowed'}, status=405)
    
    def destroy(self, request, *args, **kwargs):
        # Disable destroy action
        return Response({'error': 'Not allowed'}, status=405)
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        """Create contact submission with validation"""
        # Check for spam/abuse prevention
        ip_address = self.get_client_ip()
        
        # Check if IP is blocked
        if BlockList.is_blocked('ip', ip_address):
            return Response({
                'error': 'Your request could not be processed at this time.'
            }, status=403)
        
        # Validate reCAPTCHA
        recaptcha_response = request.data.get('g-recaptcha-response')
        if not recaptcha_response:
            return Response({
                'error': 'Please complete the reCAPTCHA verification.'
            }, status=400)
        
        # Simple reCAPTCHA validation (you should replace with actual Google verification)
        # For production, verify with Google reCAPTCHA API
        if not self.verify_recaptcha(recaptcha_response):
            return Response({
                'error': 'reCAPTCHA verification failed. Please try again.'
            }, status=400)
        
        # Rate limiting - max 5 submissions per hour from same IP
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_submissions = Contact.objects.filter(
            ip_address=ip_address,
            submitted_at__gte=one_hour_ago
        ).count()
        
        if recent_submissions >= 5:
            return Response({
                'error': 'Too many submissions. Please try again later.'
            }, status=429)
        
        # Process the submission
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            contact = serializer.save()
            
            # TODO: Send notification email to admin
            # send_new_contact_notification(contact)
            
            return Response({
                'success': True,
                'message': 'Your message has been submitted successfully. We will get back to you soon!',
                'contact_id': contact.id
            }, status=201)
            
        except Exception as e:
            return Response({
                'error': 'An error occurred while submitting your message. Please try again.'
            }, status=500)
    
    def verify_recaptcha(self, recaptcha_response):
        """Verify reCAPTCHA response with Google"""
        import requests
        
        # Replace with your actual reCAPTCHA secret key
        secret_key = "6LcxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxA"  # Your secret key here
        
        data = {
            'secret': secret_key,
            'response': recaptcha_response
        }
        
        try:
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result = response.json()
            return result.get('success', False)
        except:
            # If verification fails, allow submission (fallback)
            # In production, you might want to reject on failure
            return True
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


@api_view(['GET'])
def get_contact_settings(request):
    """Get contact page settings from contact settings"""
    try:
        # Get contact settings
        contact_settings = {}
        
        # Try to get contact settings from ContactSetting
        contact_setting = ContactSetting.objects.filter(key='contact_details').first()
        if contact_setting:
            contact_settings = contact_setting.value
        
        # Default contact settings if not found
        default_settings = {
            'business_name': 'Your Business Name',
            'address': '123 Main Street, City, Country',
            'phone': '+1234567890',
            'email': 'contact@yourbusiness.com',
            'business_hours': 'Mon-Fri: 9AM-6PM',
            'social_media': {
                'facebook': '',
                'twitter': '',
                'instagram': '',
                'linkedin': ''
            },
            'map_embed_url': '',
            'additional_info': ''
        }
        
        # Merge with defaults
        final_settings = {**default_settings, **contact_settings}
        
        return Response({
            'success': True,
            'contact_settings': final_settings
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_contact_settings(request):
    """Update contact page settings"""
    try:
        contact_data = request.data.get('contact_settings', {})
        
        # Get or create contact settings
        contact_setting, created = ContactSetting.objects.get_or_create(
            key='contact_details',
            defaults={
                'value': contact_data,
                'description': 'Contact page settings including business information, address, phone, email, and social media links'
            }
        )
        
        if not created:
            contact_setting.value = contact_data
            contact_setting.save()
        
        return Response({
            'success': True,
            'message': 'Contact settings updated successfully'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=500)


def contact_page(request):
    """Professional contact page with database integration."""
    # Get contact settings for display
    contact_settings = {}
    contact_setting = ContactSetting.objects.filter(key='contact_details').first()
    if contact_setting:
        contact_settings = contact_setting.value
    
    # Default contact settings if not found
    default_settings = {
        'business_name': 'Your Business Name',
        'address': '123 Main Street, City, Country',
        'phone': '+1234567890',
        'email': 'contact@yourbusiness.com',
        'business_hours': 'Mon-Fri: 9AM-6PM',
        'social_media': {
            'facebook': '',
            'twitter': '',
            'instagram': '',
            'linkedin': ''
        },
        'map_embed_url': '',
        'additional_info': ''
    }
    
    # Merge with defaults
    final_settings = {**default_settings, **contact_settings}
    
    context = {
        'contact_settings': final_settings,
    }
    
    return render(request, 'contact/contact.html', context)
