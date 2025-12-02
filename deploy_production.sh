#!/bin/bash

# Production Deployment Script for Django Ecommerce

echo "🚀 Starting Production Deployment..."

# 1. Install Redis (Ubuntu/Debian)
echo "📦 Installing Redis..."
sudo apt update
sudo apt install -y redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is running successfully"
else
    echo "❌ Redis installation failed"
    exit 1
fi

# 2. Set environment variables
echo "⚙️ Setting up environment..."
export USE_REDIS=true
export DEBUG=false
export REDIS_URL=redis://localhost:6379

# 3. Install Python dependencies
echo "📚 Installing Python packages..."
pip install -r requirements.txt
pip install redis django-redis

# 4. Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# 5. Create cache tables (backup for fallback)
echo "💾 Creating cache tables..."
python manage.py createcachetable

# 6. Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# 7. Test cache system
echo "🧪 Testing cache system..."
python manage.py shell -c "
from django.core.cache import cache
cache.set('test', 'production_ready', 30)
result = cache.get('test')
if result == 'production_ready':
    print('✅ Cache system is working')
else:
    print('❌ Cache system failed')
"

# 8. Test order system
echo "🛒 Testing order system..."
python manage.py shell -c "
from orders.utils import get_client_ip
from django.test import RequestFactory
rf = RequestFactory()
req = rf.get('/')
ip = get_client_ip(req)
print(f'✅ Order IP detection working: {ip}')
"

echo "🎉 Production deployment completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Configure your web server (Nginx/Apache)"
echo "2. Set up SSL certificates"
echo "3. Configure firewall rules"
echo "4. Set up monitoring and logging"