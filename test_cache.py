# Simple cache test for development
from django.core.cache import cache

print("Testing Django Cache System...")

# Test cache set and get
cache.set('dev_test', 'Database cache working!', 60)
result = cache.get('dev_test')

if result:
    print(f"✅ Cache Working: {result}")
    cache.delete('dev_test')
    print("✅ Cache cleared successfully")
else:
    print("❌ Cache not working")

print("Cache test completed!")