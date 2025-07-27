console.log('Testing default variant selection...');

// Simulate variant data structure
const testVariantsData = [
    {
        "id": 26,
        "name": "Red Classic T-Shirt - Small",
        "color": "#dc3545",
        "colorName": "Red",
        "size": "S",
        "price": "19.99",
        "stock": 15,
        "isDefault": true
    },
    {
        "id": 27,
        "name": "Red Classic T-Shirt - Medium",
        "color": "#dc3545",
        "colorName": "Red", 
        "size": "M",
        "price": "19.99",
        "stock": 20,
        "isDefault": false
    }
];

// Test finding default variant
const defaultVariant = testVariantsData.find(v => v.isDefault === true);
console.log('Default variant found:', defaultVariant);

if (defaultVariant) {
    console.log('✓ Default variant selection should work');
    console.log('- Color to select:', defaultVariant.color);
    console.log('- Size to select:', defaultVariant.size);
    console.log('- Variant ID:', defaultVariant.id);
} else {
    console.log('✗ No default variant found');
}

// Test the logic for products without sizes
const noSizeVariantsData = [
    {
        "id": 50,
        "name": "Black",
        "color": "#00000",
        "colorName": "Black",
        "size": "",
        "price": "89.99",
        "stock": 20,
        "isDefault": true
    }
];

const defaultNoSize = noSizeVariantsData.find(v => v.isDefault === true);
console.log('Default variant (no size) found:', defaultNoSize);

console.log('Test completed.');
