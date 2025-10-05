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

def fix_database():
    print("=== FIXING DATABASE SEQUENCE ISSUE ===\n")
    
    # Connect to SQLite database directly
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current data
        cursor.execute("SELECT * FROM products_productimage;")
        rows = cursor.fetchall()
        print(f"Current records: {len(rows)}")
        for row in rows:
            print(f"  - ID: {row[0]}, Product: {row[4]}, Image: {row[5]}")
        
        # Delete all records
        cursor.execute("DELETE FROM products_productimage;")
        print("Deleted all records")
        
        # Reset the sequence
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='products_productimage';")
        print("Reset sequence")
        
        conn.commit()
        print("Changes committed")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM products_productimage;")
        count = cursor.fetchone()[0]
        print(f"Records after cleanup: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()