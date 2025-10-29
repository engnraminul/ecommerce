from rest_framework import serializers
from .models import Contact, ContactSetting, ContactActivity
from django.contrib.auth import get_user_model

User = get_user_model()


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model with dashboard management features"""
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')
    days_since_submission = serializers.ReadOnlyField()
    is_urgent = serializers.ReadOnlyField()
    attachment_url = serializers.ReadOnlyField(source='get_attachment_url')
    attachment_name = serializers.ReadOnlyField(source='get_attachment_name')
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone', 'email', 'subject', 'message', 'attachment',
            'attachment_url', 'attachment_name', 'status', 'priority', 'ip_address', 
            'user_agent', 'admin_notes', 'assigned_to', 'assigned_to_username',
            'submitted_at', 'updated_at', 'replied_at', 'days_since_submission',
            'is_urgent'
        ]
        read_only_fields = ['submitted_at', 'ip_address', 'user_agent']
    
    def validate_attachment(self, value):
        """Validate file attachment"""
        if value:
            # Check file size (10MB limit)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 10MB.")
            
            # Check file type (optional - you can add more restrictions)
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf', 'text/plain', 
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "File type not allowed. Please upload images, PDF, or document files."
                )
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number"""
        import re
        if value:
            # Remove any formatting characters
            clean_phone = re.sub(r'[^\d+\-\(\)\s]', '', value)
            if len(re.sub(r'[^\d]', '', clean_phone)) < 10:
                raise serializers.ValidationError(
                    'Please enter a valid phone number with at least 10 digits.'
                )
        return value


class ContactSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for public contact form submission"""
    attachment = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = Contact
        fields = ['name', 'phone', 'email', 'subject', 'message', 'attachment']
    
    def validate_attachment(self, value):
        """Validate file attachment for public submission"""
        if value:
            # Check file size (10MB limit)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 10MB.")
        return value
    
    def create(self, validated_data):
        """Create contact with IP and user agent tracking"""
        request = self.context.get('request')
        if request:
            # Add IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                validated_data['ip_address'] = x_forwarded_for.split(',')[0]
            else:
                validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
            
            # Add user agent
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return super().create(validated_data)


class ContactSettingSerializer(serializers.ModelSerializer):
    """Serializer for contact page settings"""
    
    class Meta:
        model = ContactSetting
        fields = '__all__'


class ContactActivitySerializer(serializers.ModelSerializer):
    """Serializer for contact activities"""
    user_username = serializers.ReadOnlyField(source='user.username')
    contact_name = serializers.ReadOnlyField(source='contact.name')
    
    class Meta:
        model = ContactActivity
        fields = [
            'id', 'contact', 'contact_name', 'user', 'user_username', 
            'action', 'description', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['timestamp', 'ip_address', 'user_agent']