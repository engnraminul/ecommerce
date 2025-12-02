# Production Cache Setup Guide

## Redis Installation on Production Server

### For Ubuntu/Debian Server:
```bash
# Update packages
sudo apt update

# Install Redis
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### For CentOS/RHEL Server:
```bash
# Install EPEL repository
sudo yum install epel-release

# Install Redis
sudo yum install redis

# Start Redis service
sudo systemctl start redis
sudo systemctl enable redis

# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### Using Docker (Recommended):
```bash
# Run Redis container
docker run -d --name redis \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:alpine

# Check if running
docker ps | grep redis
```

## Production Settings Configuration

1. Set environment variable: `USE_REDIS=True`
2. Configure Redis URL: `REDIS_URL=redis://localhost:6379`
3. Uncomment cache usage in orders/utils.py
4. Enable cache middleware for better performance

## Security Considerations

- Configure Redis authentication
- Use firewall to restrict Redis port access
- Consider Redis Sentinel for high availability
- Use Redis encryption in transit if needed