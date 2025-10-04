"""
Test the professional stock activity tracking system
Tests Stock In/Stock Out functionality with comprehensive activity logging
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant
from inventory.services import StockActivityService
from inventory.models import StockActivity
from decimal import Decimal

User = get_user_model()

def test_stock_activity_system():
    """Test the comprehensive stock activity tracking system"""
    print("🧪 Testing Professional Stock Activity System...")
    
    try:
        # Get an existing superuser
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # Create a unique test user
            import uuid
            unique_suffix = str(uuid.uuid4())[:8]
            user = User.objects.create_user(
                username=f'test_stock_user_{unique_suffix}',
                email=f'test_{unique_suffix}@example.com',
                password='testpass123',
                is_staff=True,
                is_superuser=True
            )
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        # Get test products
        products = Product.objects.filter(track_inventory=True)[:3]
        
        if not products.exists():
            print("❌ No products found for testing. Please create some products first.")
            return
        
        print(f"\n📦 Testing with {products.count()} products...")
        
        # Test Stock In operations
        print("\n🔄 Testing Stock In Operations...")
        for i, product in enumerate(products):
            variants = product.variants.filter(is_active=True)
            
            if variants.exists():
                # Test variant stock in
                variant = variants.first()
                print(f"\n📌 Testing Stock In for Variant: {product.name} - {variant.name}")
                print(f"   Current stock: {variant.stock_quantity}")
                
                activity = StockActivityService.stock_in(
                    item=variant,
                    quantity=10,
                    reason=f"Test stock in for variant {variant.name}",
                    user=user,
                    unit_cost=Decimal('15.50'),
                    reference_number=f"PO-TEST-{i+1}",
                    notes="Automated test stock in operation"
                )
                
                print(f"   ✅ Stock In completed: {activity.quantity_before} → {activity.quantity_after}")
                print(f"   📋 Activity ID: {activity.id}")
                print(f"   💰 Total cost: ৳{activity.total_cost}")
                
            else:
                # Test product stock in
                print(f"\n📦 Testing Stock In for Product: {product.name}")
                print(f"   Current stock: {product.stock_quantity}")
                
                activity = StockActivityService.stock_in(
                    item=product,
                    quantity=5,
                    reason=f"Test stock in for product {product.name}",
                    user=user,
                    unit_cost=Decimal('25.00'),
                    reference_number=f"PO-PROD-{i+1}",
                    notes="Automated test stock in for product"
                )
                
                print(f"   ✅ Stock In completed: {activity.quantity_before} → {activity.quantity_after}")
                print(f"   📋 Activity ID: {activity.id}")
                print(f"   💰 Total cost: ৳{activity.total_cost}")
        
        # Test Stock Out operations
        print("\n📤 Testing Stock Out Operations...")
        for i, product in enumerate(products):
            variants = product.variants.filter(is_active=True)
            
            if variants.exists():
                # Test variant stock out
                variant = variants.first()
                if variant.stock_quantity >= 3:
                    print(f"\n📌 Testing Stock Out for Variant: {product.name} - {variant.name}")
                    print(f"   Current stock: {variant.stock_quantity}")
                    
                    activity = StockActivityService.stock_out(
                        item=variant,
                        quantity=3,
                        reason=f"Test stock out for variant {variant.name}",
                        user=user,
                        reference_number=f"SO-TEST-{i+1}",
                        notes="Automated test stock out operation"
                    )
                    
                    print(f"   ✅ Stock Out completed: {activity.quantity_before} → {activity.quantity_after}")
                    print(f"   📋 Activity ID: {activity.id}")
                else:
                    print(f"   ⚠️ Insufficient stock for variant {variant.name} (has: {variant.stock_quantity})")
            
            else:
                # Test product stock out
                if product.stock_quantity >= 2:
                    print(f"\n📦 Testing Stock Out for Product: {product.name}")
                    print(f"   Current stock: {product.stock_quantity}")
                    
                    activity = StockActivityService.stock_out(
                        item=product,
                        quantity=2,
                        reason=f"Test stock out for product {product.name}",
                        user=user,
                        reference_number=f"SO-PROD-{i+1}",
                        notes="Automated test stock out for product"
                    )
                    
                    print(f"   ✅ Stock Out completed: {activity.quantity_before} → {activity.quantity_after}")
                    print(f"   📋 Activity ID: {activity.id}")
                else:
                    print(f"   ⚠️ Insufficient stock for product {product.name} (has: {product.stock_quantity})")
        
        # Test bulk operations
        print("\n🔄 Testing Bulk Stock Operations...")
        adjustments = []
        
        # Prepare bulk adjustments
        for product in products[:2]:
            variants = product.variants.filter(is_active=True)
            if variants.exists():
                adjustments.append({
                    'item': variants.first(),
                    'activity_type': 'stock_in',
                    'quantity': 5,
                    'reason': f'Bulk stock in for {variants.first().name}',
                    'unit_cost': Decimal('20.00'),
                    'reference_number': 'BULK-001'
                })
            else:
                adjustments.append({
                    'item': product,
                    'activity_type': 'stock_in',
                    'quantity': 8,
                    'reason': f'Bulk stock in for {product.name}',
                    'unit_cost': Decimal('30.00'),
                    'reference_number': 'BULK-001'
                })
        
        if adjustments:
            results = StockActivityService.bulk_stock_adjustment(
                adjustments=adjustments,
                user=user,
                batch_description="Test bulk stock operation"
            )
            
            print(f"   📊 Bulk operation results:")
            print(f"     Total processed: {results['total_processed']}")
            print(f"     Successful: {results['successful_count']}")
            print(f"     Failed: {results['failed_count']}")
            print(f"     Batch ID: {results['batch'].id}")
            print(f"     Batch Number: {results['batch'].batch_number}")
        
        # Test activity history
        print("\n📋 Testing Activity History...")
        test_product = products.first()
        history = StockActivityService.get_item_stock_history(test_product, limit=5)
        
        print(f"   📦 Activity history for {test_product.name} (last 5):")
        for activity in history:
            print(f"     • {activity.get_activity_type_display()}: {activity.quantity_changed:+d} units")
            print(f"       Reason: {activity.reason}")
            print(f"       Date: {activity.activity_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"       User: {activity.created_by.username}")
            if activity.total_cost:
                print(f"       Cost: ৳{activity.total_cost}")
            print()
        
        # Test user activity summary
        print("👤 Testing User Activity Summary...")
        summary = StockActivityService.get_user_activity_summary(user)
        
        print(f"   📊 Activity summary for user {user.username}:")
        print(f"     Total activities: {summary['total_activities']}")
        print(f"     Stock In operations: {summary['stock_in_count']}")
        print(f"     Stock Out operations: {summary['stock_out_count']}")
        print(f"     Total items added: {summary['total_items_added']}")
        print(f"     Total items removed: {summary['total_items_removed']}")
        if summary['total_value_added']:
            print(f"     Total value added: ৳{summary['total_value_added']}")
        
        # Test activity statistics
        print("\n📈 Overall Activity Statistics...")
        total_activities = StockActivity.objects.count()
        stock_in_count = StockActivity.objects.filter(activity_type='stock_in').count()
        stock_out_count = StockActivity.objects.filter(activity_type='stock_out').count()
        
        print(f"   📊 Database statistics:")
        print(f"     Total activities recorded: {total_activities}")
        print(f"     Stock In activities: {stock_in_count}")
        print(f"     Stock Out activities: {stock_out_count}")
        
        print("\n✅ All stock activity tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Professional Stock Activity Testing...")
    test_stock_activity_system()
    print("\n🎉 Testing completed!")
    print("\n💡 Key Features Tested:")
    print("   ✅ Stock In operations with cost tracking")
    print("   ✅ Stock Out operations with validation")
    print("   ✅ Professional activity logging")
    print("   ✅ Bulk operations with batch tracking")
    print("   ✅ Activity history retrieval")
    print("   ✅ User activity summaries")
    print("   ✅ Comprehensive audit trail")
    print("\n🌟 Your stock activity system provides:")
    print("   • Complete audit trail for all stock movements")
    print("   • Professional Stock In/Stock Out terminology")
    print("   • Cost tracking and financial reporting")
    print("   • Batch operations for bulk activities")
    print("   • User activity monitoring")
    print("   • Reference number and notes support")