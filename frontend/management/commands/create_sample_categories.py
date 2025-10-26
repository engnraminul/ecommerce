from django.core.management.base import BaseCommand
from products.models import Category

class Command(BaseCommand):
    help = 'Create sample categories with parent-child relationships for testing'

    def handle(self, *args, **options):
        # Create parent categories
        parent_categories = [
            {
                'name': 'Electronics', 
                'description': 'Electronic devices and gadgets',
                'image': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=100&h=100&fit=crop'
            },
            {
                'name': 'Clothing', 
                'description': 'Fashion and apparel',
                'image': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=100&h=100&fit=crop'
            },
            {
                'name': 'Home & Garden', 
                'description': 'Home decor and garden supplies',
                'image': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=100&h=100&fit=crop'
            },
            {
                'name': 'Sports & Fitness', 
                'description': 'Sports equipment and fitness gear',
                'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=100&h=100&fit=crop'
            },
            {
                'name': 'Books & Media', 
                'description': 'Books, movies, and music',
                'image': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=100&h=100&fit=crop'
            },
        ]

        # Create subcategories for each parent with images
        subcategories = {
            'Electronics': [
                {'name': 'Smartphones', 'image': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=80&h=80&fit=crop'},
                {'name': 'Laptops', 'image': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=80&h=80&fit=crop'},
                {'name': 'Cameras', 'image': 'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=80&h=80&fit=crop'},
                {'name': 'Headphones', 'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=80&h=80&fit=crop'},
                {'name': 'Gaming', 'image': 'https://images.unsplash.com/photo-1592840496694-26d035b52b48?w=80&h=80&fit=crop'}
            ],
            'Clothing': [
                {'name': "Men's Fashion", 'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop'},
                {'name': "Women's Fashion", 'image': 'https://images.unsplash.com/photo-1494790108755-2616c85a1a16?w=80&h=80&fit=crop'}, 
                {'name': 'Shoes', 'image': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=80&h=80&fit=crop'},
                {'name': 'Accessories', 'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=80&h=80&fit=crop'},
                {'name': 'Jewelry', 'image': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=80&h=80&fit=crop'}
            ],
            'Home & Garden': [
                {'name': 'Furniture', 'image': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=80&h=80&fit=crop'},
                {'name': 'Kitchen', 'image': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=80&h=80&fit=crop'},
                {'name': 'Bathroom', 'image': 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=80&h=80&fit=crop'},
                {'name': 'Garden Tools', 'image': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=80&h=80&fit=crop'},
                {'name': 'Home Decor', 'image': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=80&h=80&fit=crop'}
            ],
            'Sports & Fitness': [
                {'name': 'Fitness Equipment', 'image': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=80&h=80&fit=crop'},
                {'name': 'Outdoor Sports', 'image': 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=80&h=80&fit=crop'},
                {'name': 'Team Sports', 'image': 'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=80&h=80&fit=crop'},
                {'name': 'Water Sports', 'image': 'https://images.unsplash.com/photo-1530549387789-4c1017266635?w=80&h=80&fit=crop'},
                {'name': 'Winter Sports', 'image': 'https://images.unsplash.com/photo-1551524164-687a55dd1126?w=80&h=80&fit=crop'}
            ],
            'Books & Media': [
                {'name': 'Fiction Books', 'image': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=80&h=80&fit=crop'},
                {'name': 'Non-Fiction Books', 'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop'},
                {'name': 'Movies & TV', 'image': 'https://images.unsplash.com/photo-1489599577372-f5f4c10a9f73?w=80&h=80&fit=crop'},
                {'name': 'Music', 'image': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=80&h=80&fit=crop'},
                {'name': 'Educational', 'image': 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=80&h=80&fit=crop'}
            ]
        }

        created_parents = {}
        
        # Create parent categories
        for parent_data in parent_categories:
            parent, created = Category.objects.get_or_create(
                name=parent_data['name'],
                defaults={
                    'description': parent_data['description'],
                    'is_active': True
                }
            )
            created_parents[parent_data['name']] = parent
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created parent category: {parent.name}')
                )
            else:
                self.stdout.write(f'Parent category already exists: {parent.name}')

        # Create subcategories
        for parent_name, sub_list in subcategories.items():
            parent = created_parents[parent_name]
            
            for sub_data in sub_list:
                subcategory, created = Category.objects.get_or_create(
                    name=sub_data['name'],
                    defaults={
                        'description': f'{sub_data["name"]} in {parent_name}',
                        'parent': parent,
                        'image': sub_data.get('image', ''),
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created subcategory: {subcategory.name} under {parent.name}')
                    )
                else:
                    self.stdout.write(f'Subcategory already exists: {subcategory.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample categories!')
        )