from django import template

register = template.Library()

@register.filter
def category_icon(category_name):
    """
    Returns an appropriate FontAwesome icon class for a category name
    """
    icon_mapping = {
        'electronics': 'laptop',
        'clothing': 'tshirt', 
        'fashion': 'tshirt',
        'books': 'book',
        'home': 'home',
        'garden': 'leaf',
        'sports': 'dumbbell',
        'fitness': 'dumbbell',
        'kitchen': 'utensils',
        'furniture': 'couch',
        'toys': 'gamepad',
        'automotive': 'car',
        'beauty': 'heart',
        'health': 'plus-circle',
        'jewelry': 'gem',
        'shoes': 'shoe-prints',
        'bags': 'shopping-bag',
        'computers': 'desktop',
        'phones': 'mobile-alt',
        'cameras': 'camera',
        'music': 'music',
        'movies': 'film',
        'games': 'gamepad',
        'outdoor': 'tree',
        'food': 'utensils',
        'pets': 'paw',
        'office': 'briefcase',
        'art': 'palette',
        'crafts': 'hammer',
    }
    
    # Convert category name to lowercase and check for partial matches
    category_lower = category_name.lower()
    
    # First try exact match
    if category_lower in icon_mapping:
        return icon_mapping[category_lower]
    
    # Then try partial matches
    for key, icon in icon_mapping.items():
        if key in category_lower or category_lower in key:
            return icon
    
    # Default icon
    return 'tag'