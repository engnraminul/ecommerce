#!/usr/bin/env python3
"""
Test script for filename sanitization
"""

import re
import os

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal and ensure safe filenames"""
    # Extract file extension
    name, ext = os.path.splitext(filename)
    
    # Remove or replace problematic characters
    # Keep only alphanumeric, hyphens, underscores, and spaces
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    
    # Remove multiple consecutive underscores/hyphens
    name = re.sub(r'[-_]{2,}', '_', name)
    
    # Remove leading/trailing underscores/hyphens
    name = name.strip('_-')
    
    # Ensure filename is not empty
    if not name:
        name = 'file'
    
    # Limit filename length
    if len(name) > 50:
        name = name[:50]
    
    return f"{name}{ext.lower()}"

def test_filename_sanitization():
    """Test various problematic filenames"""
    test_cases = [
        "Manob bazar office.jpg",
        "../../etc/passwd",
        "file with spaces.png",
        "file@#$%^&*().doc",
        "normal_filename.txt",
        "file---with___many___separators.pdf",
        "   leading_and_trailing_spaces   .jpg",
        "فائل عربی.png",  # Arabic filename
        "файл кириллица.jpg",  # Cyrillic filename
        "very_long_filename_that_exceeds_normal_limits_and_should_be_truncated_properly.jpg",
        ".hidden_file",
        "no_extension",
        ""
    ]
    
    print("Testing filename sanitization:")
    print("=" * 60)
    
    for original in test_cases:
        sanitized = sanitize_filename(original)
        print(f"Original:  '{original}'")
        print(f"Sanitized: '{sanitized}'")
        print("-" * 40)

if __name__ == "__main__":
    test_filename_sanitization()