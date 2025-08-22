from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Product, Wishlist

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wishlist_api(request):
    """
    API endpoint to get user's wishlist items
    Returns JSON with the wishlist items
    """
    try:
        # Get all wishlist items for the current user
        wishlist_items_db = Wishlist.objects.filter(user=request.user).select_related('product')
        
        # Format response data
        wishlist_items = []
        for item in wishlist_items_db:
            # Get the primary image if available
            primary_image_url = None
            product_images = item.product.images.filter(is_primary=True).first()
            if product_images:
                primary_image_url = product_images.image.url
            
            wishlist_items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_price': str(item.product.price),
                'product_image': primary_image_url,
                'added_at': item.created_at.isoformat(),
            })
        
        # Return formatted data
        return Response({
            'count': len(wishlist_items),
            'wishlist_count': len(wishlist_items),  # Include both formats for compatibility
            'items': wishlist_items
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=500)
