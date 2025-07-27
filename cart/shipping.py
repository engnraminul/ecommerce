"""
Shipping calculation service
"""
from decimal import Decimal


class ShippingCalculator:
    """Calculate shipping costs based on cart items and location"""
    
    # Default shipping costs
    DEFAULT_COSTS = {
        'standard_dhaka': Decimal('70'),
        'standard_outside': Decimal('120'),
        'express_dhaka': Decimal('150'),
    }
    
    def __init__(self, cart_items, location='dhaka'):
        """
        Initialize shipping calculator
        
        Args:
            cart_items: QuerySet or list of CartItem objects
            location: 'dhaka' or 'outside'
        """
        self.cart_items = cart_items
        self.location = location
    
    def get_available_shipping_options(self):
        """
        Get all available shipping options based on cart products
        
        Returns:
            List of shipping options with costs
        """
        options = []
        
        # Check if any product offers free shipping
        has_free_shipping = any(
            item.product.shipping_type == 'free' 
            for item in self.cart_items
        )
        
        # Check if any product has standard shipping
        has_standard_shipping = any(
            item.product.shipping_type == 'standard' 
            for item in self.cart_items
        )
        
        # Check if any product has express shipping enabled (Dhaka only)
        has_express_shipping = (
            self.location == 'dhaka' and 
            any(item.product.has_express_shipping for item in self.cart_items)
        )
        
        # Add main shipping options (Free takes priority over Standard)
        if has_free_shipping:
            estimated_days = '1-2 days' if self.location == 'dhaka' else '2-4 days'
            options.append({
                'type': 'free',
                'name': 'Free Shipping',
                'cost': Decimal('0'),
                'description': 'Free delivery',
                'estimated_days': estimated_days
            })
        elif has_standard_shipping:
            cost = self._calculate_standard_shipping_cost()
            location_name = 'Dhaka City' if self.location == 'dhaka' else 'Outside Dhaka'
            estimated_days = '1-2 days' if self.location == 'dhaka' else '2-4 days'
            options.append({
                'type': 'standard',
                'name': f'Standard Shipping ({location_name})',
                'cost': cost,
                'description': f'Regular delivery - {cost} ৳',
                'estimated_days': estimated_days
            })
        
        # Add express shipping option if any product has it enabled (Dhaka only)
        if has_express_shipping and self.location == 'dhaka':
            cost = self._calculate_express_shipping_cost()
            options.append({
                'type': 'express',
                'name': 'Express Shipping (Same Day)',
                'cost': cost,
                'description': f'Same day delivery - {cost} ৳',
                'estimated_days': 'Same day'
            })
        
        return options
    
    def _calculate_standard_shipping_cost(self):
        """Calculate standard shipping cost"""
        total_cost = Decimal('0')
        
        for item in self.cart_items:
            if item.product.shipping_type == 'free':
                continue  # Free shipping products don't add to cost
            
            # Get product-specific shipping cost or use default
            if self.location == 'dhaka':
                product_cost = (
                    item.product.custom_shipping_dhaka or 
                    self.DEFAULT_COSTS['standard_dhaka']
                )
            else:
                product_cost = (
                    item.product.custom_shipping_outside or 
                    self.DEFAULT_COSTS['standard_outside']
                )
            
            # For now, we'll use the highest shipping cost among all products
            # You can modify this logic as needed
            if product_cost > total_cost:
                total_cost = product_cost
        
        return total_cost
    
    def _calculate_express_shipping_cost(self):
        """Calculate express shipping cost (Dhaka only)"""
        if self.location != 'dhaka':
            return None
        
        total_cost = Decimal('0')
        
        for item in self.cart_items:
            # Only consider products that have express shipping enabled
            if not item.product.has_express_shipping:
                continue
            
            # Get product-specific express shipping cost or use default
            product_cost = (
                item.product.custom_express_shipping or 
                self.DEFAULT_COSTS['express_dhaka']
            )
            
            # Use the highest express shipping cost among all products
            if product_cost > total_cost:
                total_cost = product_cost
        
        return total_cost
    
    def calculate_shipping_cost(self, shipping_type):
        """
        Calculate shipping cost for a specific shipping type
        
        Args:
            shipping_type: 'free', 'standard', or 'express'
            
        Returns:
            Decimal cost or None if not available
        """
        if shipping_type == 'free':
            return Decimal('0')
        elif shipping_type == 'standard':
            return self._calculate_standard_shipping_cost()
        elif shipping_type == 'express':
            return self._calculate_express_shipping_cost()
        else:
            return None
    
    def get_shipping_summary(self):
        """
        Get shipping summary for the cart
        
        Returns:
            Dict with shipping information
        """
        options = self.get_available_shipping_options()
        
        # Get the default (cheapest) option
        default_option = None
        if options:
            default_option = min(options, key=lambda x: x['cost'])
        
        return {
            'available_options': options,
            'default_option': default_option,
            'location': self.location,
            'total_weight': sum(
                (item.product.weight or Decimal('0')) * item.quantity 
                for item in self.cart_items
            )
        }
