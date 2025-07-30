from django.core.management.base import BaseCommand
from scraper.models import ScrapingJob, ScrapingTarget
from scraper.tasks import scrape_linkedin_profiles


class Command(BaseCommand):
    help = 'Manually run a LinkedIn scraping job'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, help='Name for the scraping job')
        parser.add_argument('--university', type=str, help='University to search for alumni')
        parser.add_argument('--company', type=str, help='Company to search for employees')
        parser.add_argument('--keyword', type=str, help='Keyword search query')
        parser.add_argument('--max-profiles', type=int, default=50, help='Maximum profiles to scrape')

    def handle(self, *args, **options):
        name = options.get('name') or f"Manual Scraping - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create scraping job
        job = ScrapingJob.objects.create(
            name=name,
            status='pending'
        )
        
        # Add targets based on provided options
        if options.get('university'):
            ScrapingTarget.objects.create(
                job=job,
                type='university',
                query=f"{options['university']} alumni",
                max_profiles=options['max_profiles']
            )
            
        if options.get('company'):
            ScrapingTarget.objects.create(
                job=job,
                type='company',
                query=f"{options['company']} employees",
                max_profiles=options['max_profiles']
            )
            
        if options.get('keyword'):
            ScrapingTarget.objects.create(
                job=job,
                type='keyword',
                query=options['keyword'],
                max_profiles=options['max_profiles']
            )
        
        # If no specific targets provided, add some default ones
        if not any([options.get('university'), options.get('company'), options.get('keyword')]):
            default_universities = ['Stanford University', 'Harvard University', 'MIT']
            for university in default_universities:
                ScrapingTarget.objects.create(
                    job=job,
                    type='university',
                    query=f"{university} alumni",
                    max_profiles=20
                )
        
        # Start the scraping job
        scrape_linkedin_profiles.delay(job.id)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully started scraping job: {job.name} (ID: {job.id})')
        )
        self.stdout.write(f'Targets: {job.targets.count()}')
        
        # Show targets
        for target in job.targets.all():
            self.stdout.write(f'  - {target.get_type_display()}: {target.query} (max: {target.max_profiles})')


# Add missing import
from django.utils import timezone