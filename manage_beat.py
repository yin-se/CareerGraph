#!/usr/bin/env python
"""
Safe Celery Beat starter that checks database readiness
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careergraph.settings')
    django.setup()
    
    try:
        # Test database connection
        from django.db import connection
        connection.ensure_connection()
        
        # Check if django_celery_beat tables exist
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.count()
        
        print("✅ Database ready, starting Celery Beat...")
        execute_from_command_line(['manage.py', 'celery', 'beat', '--loglevel=info'])
        
    except Exception as e:
        print(f"❌ Database not ready for Celery Beat: {e}")
        print("Run migrations first: python manage.py migrate")
        sys.exit(1)