"""
Phone number utilities for Bangladesh phone numbers
"""
import re

def normalize_bangladeshi_phone(phone):
    """
    Normalize a Bangladeshi phone number to the standard format: 01XXXXXXXXX
    
    Handles various input formats:
    - +8801777173040
    - 8801777173040  
    - 01777173040
    - 01777-173040
    - 01777 173040
    - (+88) 01777173040
    - +88 01777-173040
    - (+880) 1777-173040
    - 0177-7173040
    - +880-1777-173040
    
    Returns: Normalized phone number (01XXXXXXXXX) or original if invalid
    """
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if digits.startswith('880'):
        # Remove country code 880 and add 0 prefix
        digits = '0' + digits[3:]
    elif digits.startswith('88'):
        # Remove country code 88 and add 0 prefix  
        digits = '0' + digits[2:]
    elif not digits.startswith('0'):
        # Add 0 prefix if not present
        digits = '0' + digits
    
    # Validate Bangladesh mobile number format
    if len(digits) >= 11 and digits.startswith('01'):
        # Limit to 11 digits for Bangladesh mobile numbers
        return digits[:11]
    
    # Return original if doesn't match expected format
    return phone

def validate_bangladeshi_phone(phone):
    """
    Validate a Bangladeshi phone number
    
    Returns: dict with 'is_valid', 'normalized', and 'error' keys
    """
    if not phone:
        return {
            'is_valid': False,
            'normalized': '',
            'error': 'Phone number is required'
        }
    
    normalized = normalize_bangladeshi_phone(phone)
    
    # Check if normalized phone has at least 11 digits
    if len(normalized) < 11:
        return {
            'is_valid': False,
            'normalized': normalized,
            'error': 'Phone number must be at least 11 digits'
        }
    
    # Check if it's a valid Bangladesh number (starts with 01)
    if not normalized.startswith('01'):
        return {
            'is_valid': False,
            'normalized': normalized,
            'error': 'Please enter a valid Bangladesh phone number'
        }
    
    return {
        'is_valid': True,
        'normalized': normalized,
        'error': None
    }