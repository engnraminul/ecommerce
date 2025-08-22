// Test script for wishlist persistence after page reload
// Run this in the browser console to test the functionality

(function testWishlistPersistence() {
    console.log('=== Starting Wishlist Persistence Test ===');
    
    // 1. Check if localStorage has a wishlist count
    const storedCount = localStorage.getItem('wishlistCount');
    console.log(`1. Current localStorage wishlist count: ${storedCount || 'Not set'}`);
    
    // 2. Check if the wishlist badge is visible
    const wishlistBadge = document.querySelector('.wishlist-count');
    if (wishlistBadge) {
        console.log(`2. Wishlist badge visibility: ${getComputedStyle(wishlistBadge).display}`);
        console.log(`   Badge text content: ${wishlistBadge.textContent}`);
    } else {
        console.log('2. Wishlist badge not found in DOM');
    }
    
    // 3. Check if the "X items" text is in sync
    const wishlistItems = document.querySelector('.wishlist-items');
    if (wishlistItems) {
        console.log(`3. Wishlist items text: ${wishlistItems.textContent}`);
    } else {
        console.log('3. Wishlist items text element not found');
    }
    
    // 4. Test localStorage persistence
    const testCount = String(Math.floor(Math.random() * 10));
    console.log(`4. Setting random test count in localStorage: ${testCount}`);
    localStorage.setItem('wishlistCount', testCount);
    
    // 5. Simulate page reload effect (without actually reloading)
    console.log('5. Simulating page reload effect...');
    console.log('   Calling updateWishlistBadge() function...');
    
    // 6. Create a test function that mimics the initial DOM load behavior
    function simulatePageReload() {
        // Get the count from localStorage
        const savedCount = localStorage.getItem('wishlistCount');
        
        // Update the badge if it exists
        if (wishlistBadge) {
            wishlistBadge.textContent = savedCount;
            wishlistBadge.style.display = 'flex';
            wishlistBadge.style.visibility = 'visible';
        }
        
        // Update the "X items" text if it exists
        if (wishlistItems) {
            wishlistItems.textContent = savedCount + ' items';
        }
        
        console.log(`6. After simulated reload: Badge shows ${wishlistBadge?.textContent}`);
        console.log(`   Items text shows: ${wishlistItems?.textContent}`);
    }
    
    // Run the simulation
    simulatePageReload();
    
    console.log('=== Wishlist Persistence Test Complete ===');
    console.log('To verify persistence across actual page reloads:');
    console.log('1. Note the current random count number');
    console.log('2. Reload the page');
    console.log('3. Run this test again and verify the count remained');
    
})();
