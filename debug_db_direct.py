#!/usr/bin/env python
import os
import django
import sys
import sqlite3

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def check_database():
    print("=== CHECKING DATABASE DIRECTLY ===\n")
    
    # Connect to SQLite database directly
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_productimage';")
        table_exists = cursor.fetchone()
        print(f"products_productimage table exists: {table_exists is not None}")
        
        if table_exists:
            # Check table structure
            cursor.execute("PRAGMA table_info(products_productimage);")
            columns = cursor.fetchall()
            print(f"\nTable structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM products_productimage;")
            count = cursor.fetchone()[0]
            print(f"\nTotal rows in products_productimage: {count}")
            
            # Check for any data
            cursor.execute("SELECT * FROM products_productimage LIMIT 5;")
            rows = cursor.fetchall()
            print(f"\nFirst 5 rows:")
            for row in rows:
                print(f"  - {row}")
            
            # Check AUTO_INCREMENT value
            cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='products_productimage';")
            seq = cursor.fetchone()
            print(f"\nNext ID would be: {seq[0] + 1 if seq else 1}")
            
            # Try to see what IDs exist
            cursor.execute("SELECT id FROM products_productimage ORDER BY id;")
            ids = cursor.fetchall()
            print(f"Existing IDs: {[row[0] for row in ids]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_database()