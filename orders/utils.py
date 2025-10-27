import ipaddress
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def is_private_ip(ip):
    """
    Check if an IP address is private/local
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except ValueError:
        # If IP is invalid, consider it private for safety
        return True

def get_public_ip():
    """
    Get the public IP address using external services with caching
    """
    # Check cache first (cache for 5 minutes to avoid frequent API calls)
    cached_ip = cache.get('public_ip')
    if cached_ip:
        logger.debug(f"Using cached public IP: {cached_ip}")
        return cached_ip
    
    services = [
        'https://ifconfig.co/ip',
        'https://ipinfo.io/ip',
        'https://api.ipify.org',
        'https://checkip.amazonaws.com',
    ]
    
    for service in services:
        try:
            logger.debug(f"Trying to get public IP from: {service}")
            response = requests.get(service, timeout=5, headers={
                'User-Agent': 'Django-Ecommerce/1.0'
            })
            if response.status_code == 200:
                public_ip = response.text.strip()
                # Validate that it's a valid IP address
                try:
                    ipaddress.ip_address(public_ip)
                    # Cache the IP for 5 minutes
                    cache.set('public_ip', public_ip, 300)
                    logger.info(f"Successfully detected public IP: {public_ip}")
                    return public_ip
                except ValueError:
                    logger.warning(f"Invalid IP format received from {service}: {public_ip}")
                    continue
        except requests.Timeout:
            logger.warning(f"Timeout while getting IP from {service}")
            continue
        except requests.RequestException as e:
            logger.warning(f"Request error from {service}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error from {service}: {e}")
            continue
    
    # If all services fail, return None
    logger.error("All public IP services failed")
    return None

def get_client_ip(request):
    """
    Get the real IP address of the client making the request.
    This function handles cases where the request might come through proxies,
    load balancers, or CDNs. If a private/local IP is detected, it will
    attempt to get the public IP address.
    """
    # List of headers to check for IP addresses (in order of preference)
    ip_headers = [
        'HTTP_X_FORWARDED_FOR',  # Standard proxy header
        'HTTP_X_REAL_IP',        # Nginx proxy
        'HTTP_CF_CONNECTING_IP', # Cloudflare
        'HTTP_X_CLUSTER_CLIENT_IP', # Cluster
        'HTTP_CLIENT_IP',        # Proxy
        'REMOTE_ADDR',           # Direct connection
    ]
    
    detected_ip = None
    source = None
    
    # Try to get IP from headers
    for header in ip_headers:
        ip_value = request.META.get(header)
        if ip_value:
            # Handle comma-separated IPs (take the first one)
            if ',' in ip_value:
                ip_value = ip_value.split(',')[0].strip()
            
            # Validate IP format
            try:
                ipaddress.ip_address(ip_value)
                detected_ip = ip_value
                source = header
                logger.debug(f"IP detected from {header}: {ip_value}")
                break
            except ValueError:
                logger.warning(f"Invalid IP format in {header}: {ip_value}")
                continue
    
    # If we have a detected IP, check if it's private/local
    if detected_ip:
        if is_private_ip(detected_ip):
            logger.debug(f"Detected IP {detected_ip} is private, attempting to get public IP")
            public_ip = get_public_ip()
            if public_ip:
                logger.info(f"Using public IP {public_ip} instead of private IP {detected_ip}")
                return public_ip
            else:
                logger.warning(f"Could not get public IP, using private IP {detected_ip}")
                return detected_ip
        else:
            # It's already a public IP
            logger.info(f"Using public IP {detected_ip} from {source}")
            return detected_ip
    
    # If no valid IP was found in headers, get public IP as fallback
    logger.warning("No valid IP found in headers, attempting to get public IP")
    public_ip = get_public_ip()
    if public_ip:
        logger.info(f"Using fallback public IP: {public_ip}")
        return public_ip
    
    # Final fallback to localhost
    logger.error("All IP detection methods failed, using localhost")
    return '127.0.0.1'