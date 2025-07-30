from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json


class Command(BaseCommand):
    help = 'Set up weekly LinkedIn scraping schedule'

    def handle(self, *args, **options):
        # Create a crontab schedule for every Sunday at 2 AM
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_week=0,  # Sunday (0=Sunday, 6=Saturday)
            day_of_month='*',
            month_of_year='*',
        )

        # Create the periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name='Weekly LinkedIn Scraping',
            defaults={
                'crontab': schedule,
                'task': 'scraper.tasks.weekly_scraping_job',
                'enabled': True,
                'kwargs': json.dumps({}),
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created weekly scraping schedule')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Weekly scraping schedule already exists')
            )

        # Display the schedule
        self.stdout.write(f'Task: {task.name}')
        self.stdout.write(f'Schedule: Every Sunday at 2:00 AM')
        self.stdout.write(f'Enabled: {task.enabled}')
        self.stdout.write(f'Task function: {task.task}')