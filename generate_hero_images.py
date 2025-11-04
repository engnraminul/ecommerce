#!/usr/bin/env python3
"""
Generate placeholder hero images for testing
"""
import os
from PIL import Image, ImageDraw, ImageFont
import sys

def create_placeholder_image(width, height, text, bg_color, text_color, filename):
    """Create a placeholder image with text"""
    try:
        # Create image
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            # Try to load a font - adjust path as needed
            font_size = min(width, height) // 15
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Add dimensions text
        dim_text = f"{width}x{height}"
        dim_bbox = draw.textbbox((0, 0), dim_text, font=font)
        dim_width = dim_bbox[2] - dim_bbox[0]
        
        draw.text((width - dim_width - 20, height - 40), dim_text, fill=text_color, font=font)
        
        # Save image
        img.save(filename, 'JPEG', quality=85)
        print(f"✓ Created: {filename}")
        
    except Exception as e:
        print(f"❌ Error creating {filename}: {e}")

def generate_hero_images():
    """Generate all hero placeholder images"""
    
    # Ensure the hero directory exists
    hero_dir = r'c:\Users\aminu\OneDrive\Desktop\ecommerce\media\hero'
    os.makedirs(hero_dir, exist_ok=True)
    
    # Define image specifications
    images = [
        # Desktop images (1920x600)
        {
            'filename': os.path.join(hero_dir, 'desktop-hero-1.jpg'),
            'width': 1920,
            'height': 600,
            'text': 'Welcome to Our Amazing Store',
            'bg_color': '#930000',
            'text_color': '#ffffff'
        },
        {
            'filename': os.path.join(hero_dir, 'desktop-hero-2.jpg'),
            'width': 1920,
            'height': 600,
            'text': 'Special Winter Collection',
            'bg_color': '#1e3a8a',
            'text_color': '#ffffff'
        },
        {
            'filename': os.path.join(hero_dir, 'desktop-hero-3.jpg'),
            'width': 1920,
            'height': 600,
            'text': 'Free Shipping on Orders Over $50',
            'bg_color': '#059669',
            'text_color': '#ffffff'
        },
        
        # Mobile images (800x600)
        {
            'filename': os.path.join(hero_dir, 'mobile-hero-1.jpg'),
            'width': 800,
            'height': 600,
            'text': 'Welcome to Our\nAmazing Store',
            'bg_color': '#930000',
            'text_color': '#ffffff'
        },
        {
            'filename': os.path.join(hero_dir, 'mobile-hero-2.jpg'),
            'width': 800,
            'height': 600,
            'text': 'Special Winter\nCollection',
            'bg_color': '#1e3a8a',
            'text_color': '#ffffff'
        },
        {
            'filename': os.path.join(hero_dir, 'mobile-hero-3.jpg'),
            'width': 800,
            'height': 600,
            'text': 'Free Shipping\nOver $50',
            'bg_color': '#059669',
            'text_color': '#ffffff'
        }
    ]
    
    print("Generating placeholder hero images...")
    print("=" * 50)
    
    for img_config in images:
        create_placeholder_image(
            img_config['width'],
            img_config['height'],
            img_config['text'],
            img_config['bg_color'],
            img_config['text_color'],
            img_config['filename']
        )
    
    print("=" * 50)
    print(f"✅ Generated {len(images)} placeholder images!")
    print("\nNext steps:")
    print("1. Visit http://127.0.0.1:8000/ to see your hero carousel")
    print("2. Go to Django Admin → Settings → Hero Content to manage slides")
    print("3. Replace placeholder images with your actual hero images")
    print("4. Customize colors, text, and button URLs as needed")

if __name__ == "__main__":
    try:
        generate_hero_images()
    except ImportError:
        print("❌ Pillow library not found!")
        print("Install it with: pip install Pillow")
        print("Or skip image generation and add your own images to media/hero/")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("You can manually add images to media/hero/ folder instead.")