from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Cart
    path('', views.CartView.as_view(), name='cart'),
    path('add/', views.add_to_cart, name='add-to-cart'),
    path('items/<int:item_id>/update/', views.update_cart_item, name='update-cart-item'),
    path('items/<int:item_id>/remove/', views.remove_from_cart, name='remove-from-cart'),
    path('clear/', views.clear_cart, name='clear-cart'),
    
    # Save for later
    path('items/<int:item_id>/save/', views.save_for_later, name='save-for-later'),
    path('saved-items/', views.SavedItemsView.as_view(), name='saved-items'),
    path('saved-items/<int:saved_item_id>/move-to-cart/', views.move_to_cart, name='move-to-cart'),
    path('saved-items/<int:saved_item_id>/remove/', views.remove_saved_item, name='remove-saved-item'),
    
    # Coupons
    path('apply-coupon/', views.apply_coupon, name='apply-coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove-coupon'),
    
    # Cart summary
    path('summary/', views.cart_summary, name='cart-summary'),
]
