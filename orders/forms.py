"""
Forms for order processing with phone number validation
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Order, ShippingAddress
from .phone_utils import validate_bangladeshi_phone


class CheckoutForm(forms.Form):
    """Checkout form with phone number validation"""
    
    # Customer Information
    customer_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your-email@example.com'
        })
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01777173040',
            'data-phone-validation': 'true'
        })
    )
    
    # Payment Method
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'})
    )
    
    # Mobile Wallet Fields (conditional)
    bkash_transaction_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter bKash transaction ID'
        })
    )
    
    bkash_sender_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01777173040',
            'data-phone-validation': 'true'
        })
    )
    
    nagad_transaction_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Nagad transaction ID'
        })
    )
    
    nagad_sender_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01777173040',
            'data-phone-validation': 'true'
        })
    )
    
    # Shipping Address
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    address_line_1 = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street Address'
        })
    )
    
    address_line_2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apartment, suite, etc. (optional)'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    state = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State/Division'
        })
    )
    
    postal_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code'
        })
    )
    
    customer_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Order notes (optional)'
        })
    )
    
    def clean_customer_phone(self):
        """Validate customer phone number"""
        phone = self.cleaned_data.get('customer_phone')
        if phone:
            validation_result = validate_bangladeshi_phone(phone)
            if not validation_result['is_valid']:
                raise ValidationError(validation_result['error'])
            return validation_result['normalized']
        return phone
    
    def clean_bkash_sender_number(self):
        """Validate bKash sender phone number"""
        phone = self.cleaned_data.get('bkash_sender_number')
        payment_method = self.cleaned_data.get('payment_method')
        
        if payment_method == 'bkash' and phone:
            validation_result = validate_bangladeshi_phone(phone)
            if not validation_result['is_valid']:
                raise ValidationError(validation_result['error'])
            return validation_result['normalized']
        return phone
    
    def clean_nagad_sender_number(self):
        """Validate Nagad sender phone number"""
        phone = self.cleaned_data.get('nagad_sender_number')
        payment_method = self.cleaned_data.get('payment_method')
        
        if payment_method == 'nagad' and phone:
            validation_result = validate_bangladeshi_phone(phone)
            if not validation_result['is_valid']:
                raise ValidationError(validation_result['error'])
            return validation_result['normalized']
        return phone
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        # Validate required fields for mobile wallet payments
        if payment_method == 'bkash':
            if not cleaned_data.get('bkash_transaction_id'):
                self.add_error('bkash_transaction_id', 'Transaction ID is required for bKash payment')
            if not cleaned_data.get('bkash_sender_number'):
                self.add_error('bkash_sender_number', 'Sender number is required for bKash payment')
        
        elif payment_method == 'nagad':
            if not cleaned_data.get('nagad_transaction_id'):
                self.add_error('nagad_transaction_id', 'Transaction ID is required for Nagad payment')
            if not cleaned_data.get('nagad_sender_number'):
                self.add_error('nagad_sender_number', 'Sender number is required for Nagad payment')
        
        return cleaned_data


class ShippingAddressForm(forms.ModelForm):
    """Shipping address form with phone validation"""
    
    class Meta:
        model = ShippingAddress
        exclude = ['order']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'Bangladesh'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '01777173040',
                'data-phone-validation': 'true'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_phone(self):
        """Validate shipping address phone number"""
        phone = self.cleaned_data.get('phone')
        if phone:
            validation_result = validate_bangladeshi_phone(phone)
            if not validation_result['is_valid']:
                raise ValidationError(validation_result['error'])
            return validation_result['normalized']
        return phone