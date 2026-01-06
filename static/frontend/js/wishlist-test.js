// Wishlist URL tester
// Run this in your browser console to see which endpoints work

(function() {
    console.log('=== Testing Wishlist Endpoints ===');
    
    // List of potential endpoints to test
    const endpoints = [
        '/api/v1/products/wishlist/',
        '/wishlist/',
        '/api/products/wishlist/',
        '/products/wishlist/',
        '/api/v1/users/wishlist/'
    ];
    
    // Test each endpoint
    endpoints.forEach(endpoint => {
        console.log(`Testing endpoint: ${endpoint}`);
        
        fetch(endpoint, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        })
        .then(response => {
            console.log(`${endpoint} - Status: ${response.status} ${response.statusText}`);
            console.log(`${endpoint} - Content Type: ${response.headers.get('content-type')}`);
            
            if (response.headers.get('content-type')?.includes('application/json')) {
                return response.json().then(data => {
                    console.log(`${endpoint} - JSON data:`, data);
                });
            } else if (response.headers.get('content-type')?.includes('text/html')) {
                console.log(`${endpoint} - Returns HTML (not JSON API endpoint)`);
                return null;
            }
        })
        .catch(error => {
            console.error(`${endpoint} - Error:`, error);
        });
    });
    
    // Also check if the toggle-wishlist endpoint is working properly
    const testProductId = 1; // Use a valid product ID from your database
    
    fetch(`/api/v1/products/${testProductId}/toggle-wishlist/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
        },
        body: JSON.stringify({
            action: 'add'
        }),
        credentials: 'include'
    })
    .then(response => {
        console.log(`Toggle wishlist endpoint - Status: ${response.status} ${response.statusText}`);
        if (response.ok) {
            return response.json();
        }
        return null;
    })
    .then(data => {
        if (data) {
            console.log('Toggle wishlist endpoint - Response:', data);
        }
    })
    .catch(error => {
        console.error('Toggle wishlist endpoint - Error:', error);
    });
    
    console.log('=== Wishlist Endpoint Test Complete ===');
})();
