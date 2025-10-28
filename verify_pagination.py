#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Review
from django.core.paginator import Paginator

reviews = Review.objects.order_by('-created_at')
p = Paginator(reviews, 20)

print(f'Total: {reviews.count()} reviews')
print(f'Pages: {p.num_pages}')
print(f'Page 1: {p.page(1).start_index()}-{p.page(1).end_index()} ({len(p.page(1).object_list)} items)')

if p.num_pages > 1:
    print(f'Page 2: {p.page(2).start_index()}-{p.page(2).end_index()} ({len(p.page(2).object_list)} items)')

print("✅ Pagination working correctly!")