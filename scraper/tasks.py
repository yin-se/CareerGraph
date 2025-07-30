import logging
import hashlib
from datetime import datetime
from typing import Dict, List
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from core.models import (
    LinkedInProfile, University, Company, Major, Degree,
    Education, Experience, CareerPath, PathNode, PathConnection
)
from .models import ScrapingJob, ScrapingTarget, ScrapingResult, ScrapingError
from .linkedin_scraper import EthicalLinkedInScraper, clean_profile_data, validate_profile_data


logger = logging.getLogger(__name__)


@shared_task(bind=True)
def scrape_linkedin_profiles(self, job_id: int):
    """
    Main task for scraping LinkedIn profiles
    """
    try:
        job = ScrapingJob.objects.get(id=job_id)
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        
        logger.info(f"Starting scraping job {job_id}: {job.name}")
        
        with EthicalLinkedInScraper() as scraper:
            for target in job.targets.all():
                try:
                    scrape_target_profiles.delay(job_id, target.id)
                except Exception as e:
                    logger.error(f"Error scheduling target {target.id}: {e}")
                    ScrapingError.objects.create(
                        job=job,
                        target=target,
                        error_type='scheduling_error',
                        error_message=str(e)
                    )
        
        # Update job status after all targets are scheduled
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Completed scraping job {job_id}")
        
    except ScrapingJob.DoesNotExist:
        logger.error(f"Scraping job {job_id} not found")
    except Exception as e:
        logger.error(f"Error in scraping job {job_id}: {e}")
        try:
            job = ScrapingJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
        except:
            pass


@shared_task(bind=True)
def scrape_target_profiles(self, job_id: int, target_id: int):
    """
    Scrape profiles for a specific target
    """
    try:
        job = ScrapingJob.objects.get(id=job_id)
        target = ScrapingTarget.objects.get(id=target_id)
        
        logger.info(f"Scraping target {target_id}: {target.query}")
        
        with EthicalLinkedInScraper() as scraper:
            if target.type == 'profile_url':
                profile_urls = [target.query]
            else:
                # Search for profiles based on target type
                profile_urls = scraper.search_public_profiles(
                    target.query, 
                    max_results=target.max_profiles
                )
            
            scraped_count = 0
            for url in profile_urls:
                try:
                    # Check if we already scraped this profile
                    if ScrapingResult.objects.filter(job=job, linkedin_url=url).exists():
                        continue
                    
                    profile_data = scraper.scrape_public_profile(url)
                    if profile_data:
                        # Store raw scraping result
                        result = ScrapingResult.objects.create(
                            job=job,
                            target=target,
                            linkedin_url=url,
                            profile_data=profile_data
                        )
                        
                        # Process the profile data asynchronously
                        process_scraped_profile.delay(result.id)
                        
                        scraped_count += 1
                        job.profiles_scraped += 1
                        job.save()
                        
                    else:
                        job.profiles_failed += 1
                        job.save()
                        
                except Exception as e:
                    logger.error(f"Error scraping profile {url}: {e}")
                    ScrapingError.objects.create(
                        job=job,
                        target=target,
                        url=url,
                        error_type='profile_scraping_error',
                        error_message=str(e)
                    )
                    job.profiles_failed += 1
                    job.save()
            
            target.scraped_count = scraped_count
            target.save()
        
        logger.info(f"Completed target {target_id}: {scraped_count} profiles scraped")
        
    except Exception as e:
        logger.error(f"Error scraping target {target_id}: {e}")


@shared_task(bind=True)
def process_scraped_profile(self, result_id: int):
    """
    Process a scraped profile and save it to the main database
    """
    try:
        result = ScrapingResult.objects.get(id=result_id)
        raw_data = result.profile_data
        
        # Clean and validate the data
        cleaned_data = clean_profile_data(raw_data)
        if not validate_profile_data(cleaned_data):
            logger.warning(f"Invalid profile data for result {result_id}")
            result.processing_status = 'invalid'
            result.save()
            return
        
        # Extract LinkedIn ID from URL
        linkedin_id = extract_linkedin_id(result.linkedin_url)
        if not linkedin_id:
            logger.warning(f"Could not extract LinkedIn ID from {result.linkedin_url}")
            result.processing_status = 'invalid'
            result.save()
            return
        
        with transaction.atomic():
            # Create or update LinkedIn profile
            profile, created = LinkedInProfile.objects.get_or_create(
                linkedin_id=linkedin_id,
                defaults={
                    'linkedin_url': result.linkedin_url,
                    'full_name': cleaned_data.get('full_name', ''),
                    'headline': cleaned_data.get('headline', ''),
                    'location': cleaned_data.get('location', ''),
                }
            )
            
            if not created:
                # Update existing profile
                profile.full_name = cleaned_data.get('full_name', profile.full_name)
                profile.headline = cleaned_data.get('headline', profile.headline)
                profile.location = cleaned_data.get('location', profile.location)
                profile.scraped_at = timezone.now()
                profile.save()
            
            # Process education data
            if 'education' in cleaned_data:
                process_education_data(profile, cleaned_data['education'])
            
            # Process experience data
            if 'experience' in cleaned_data:
                process_experience_data(profile, cleaned_data['experience'])
            
            # Generate career path
            generate_career_path.delay(profile.id)
        
        result.processing_status = 'processed'
        result.linkedin_id = linkedin_id
        result.save()
        
        logger.info(f"Processed profile {linkedin_id}")
        
    except ScrapingResult.DoesNotExist:
        logger.error(f"Scraping result {result_id} not found")
    except Exception as e:
        logger.error(f"Error processing result {result_id}: {e}")
        try:
            result = ScrapingResult.objects.get(id=result_id)
            result.processing_status = 'error'
            result.save()
        except:
            pass


def extract_linkedin_id(linkedin_url: str) -> str:
    """Extract LinkedIn ID from profile URL"""
    try:
        if '/in/' in linkedin_url:
            return linkedin_url.split('/in/')[1].split('/')[0].split('?')[0]
    except:
        pass
    return ''


def process_education_data(profile: LinkedInProfile, education_data: List[Dict]):
    """Process and save education data"""
    for edu_item in education_data:
        try:
            university_name = edu_item.get('university', '').strip()
            if not university_name:
                continue
            
            # Get or create university
            university, _ = University.objects.get_or_create(
                name=university_name,
                defaults={'country': '', 'city': ''}
            )
            
            # Process degree information
            degree = None
            degree_text = edu_item.get('degree', '').strip()
            if degree_text:
                degree_type = classify_degree_type(degree_text)
                degree, _ = Degree.objects.get_or_create(
                    name=degree_text,
                    defaults={'type': degree_type}
                )
            
            # Extract years
            start_year, end_year = parse_education_years(edu_item.get('years', ''))
            
            # Create education record
            Education.objects.get_or_create(
                profile=profile,
                university=university,
                degree=degree,
                defaults={
                    'start_year': start_year,
                    'end_year': end_year,
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing education item: {e}")


def process_experience_data(profile: LinkedInProfile, experience_data: List[Dict]):
    """Process and save experience data"""
    for exp_item in experience_data:
        try:
            company_name = exp_item.get('company', '').strip()
            title = exp_item.get('title', '').strip()
            
            if not company_name or not title:
                continue
            
            # Get or create company
            company, _ = Company.objects.get_or_create(
                name=company_name,
                defaults={'industry': '', 'size': ''}
            )
            
            # Parse duration
            start_date, end_date, is_current = parse_experience_duration(
                exp_item.get('duration', '')
            )
            
            # Create experience record
            Experience.objects.get_or_create(
                profile=profile,
                company=company,
                title=title,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_current': is_current,
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing experience item: {e}")


def classify_degree_type(degree_text: str) -> str:
    """Classify degree type from text"""
    degree_lower = degree_text.lower()
    
    if any(term in degree_lower for term in ['bachelor', 'bs', 'ba', 'bsc']):
        return 'bachelor'
    elif any(term in degree_lower for term in ['master', 'ms', 'ma', 'msc']):
        return 'master'
    elif any(term in degree_lower for term in ['phd', 'ph.d', 'doctorate']):
        return 'phd'
    elif 'mba' in degree_lower:
        return 'mba'
    elif any(term in degree_lower for term in ['certificate', 'cert']):
        return 'certificate'
    elif any(term in degree_lower for term in ['diploma']):
        return 'diploma'
    else:
        return 'bachelor'  # Default assumption


def parse_education_years(years_text: str) -> tuple:
    """Parse education years from text"""
    try:
        if '–' in years_text or '-' in years_text:
            parts = years_text.replace('–', '-').split('-')
            start_year = int(parts[0].strip()) if parts[0].strip().isdigit() else None
            end_year = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else None
            return start_year, end_year
        elif years_text.strip().isdigit():
            year = int(years_text.strip())
            return year, year
    except:
        pass
    return None, None


def parse_experience_duration(duration_text: str) -> tuple:
    """Parse experience duration from text"""
    try:
        # This is a simplified parser - in production, use more sophisticated parsing
        is_current = 'present' in duration_text.lower() or 'current' in duration_text.lower()
        
        # Extract dates (simplified)
        import re
        date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b'
        dates = re.findall(date_pattern, duration_text)
        
        start_date = None
        end_date = None
        
        if dates:
            # Convert first date to start_date
            start_month, start_year = dates[0]
            start_date = datetime.strptime(f"{start_month} {start_year}", "%b %Y").date()
            
            if len(dates) > 1 and not is_current:
                end_month, end_year = dates[1]
                end_date = datetime.strptime(f"{end_month} {end_year}", "%b %Y").date()
        
        return start_date, end_date, is_current
    except:
        return None, None, False


@shared_task(bind=True)
def generate_career_path(self, profile_id: int):
    """
    Generate career path representation for a profile
    """
    try:
        profile = LinkedInProfile.objects.get(id=profile_id)
        
        # Get education and experience data
        educations = profile.educations.all().order_by('start_year', 'end_year')
        experiences = profile.experiences.all().order_by('start_date')
        
        # Build path sequences
        university_sequence = []
        company_sequence = []
        title_sequence = []
        
        for edu in educations:
            university_sequence.append({
                'university': edu.university.name,
                'degree': edu.degree.name if edu.degree else '',
                'major': edu.major.name if edu.major else '',
                'years': f"{edu.start_year or ''}-{edu.end_year or ''}"
            })
        
        for exp in experiences:
            company_sequence.append({
                'company': exp.company.name,
                'title': exp.title,
                'start_date': exp.start_date.isoformat() if exp.start_date else '',
                'end_date': exp.end_date.isoformat() if exp.end_date else '',
                'is_current': exp.is_current
            })
            title_sequence.append(exp.title)
        
        # Generate path hash for deduplication
        path_string = json.dumps({
            'universities': university_sequence,
            'companies': company_sequence,
            'titles': title_sequence
        }, sort_keys=True)
        path_hash = hashlib.sha256(path_string.encode()).hexdigest()
        
        # Create or update career path
        career_path, created = CareerPath.objects.get_or_create(
            profile=profile,
            defaults={
                'path_hash': path_hash,
                'university_sequence': university_sequence,
                'company_sequence': company_sequence,
                'title_sequence': title_sequence,
            }
        )
        
        if not created:
            career_path.path_hash = path_hash
            career_path.university_sequence = university_sequence
            career_path.company_sequence = company_sequence
            career_path.title_sequence = title_sequence
            career_path.save()
        
        # Update graph nodes and connections
        update_career_graph.delay(profile_id)
        
        logger.info(f"Generated career path for profile {profile_id}")
        
    except LinkedInProfile.DoesNotExist:
        logger.error(f"Profile {profile_id} not found")
    except Exception as e:
        logger.error(f"Error generating career path for profile {profile_id}: {e}")


@shared_task(bind=True)
def update_career_graph(self, profile_id: int):
    """
    Update the career graph nodes and connections based on a profile
    """
    try:
        profile = LinkedInProfile.objects.get(id=profile_id)
        career_path = CareerPath.objects.get(profile=profile)
        
        # Create nodes for universities, companies, and titles
        nodes = []
        
        # University nodes
        for edu_item in career_path.university_sequence:
            if edu_item['university']:
                node, _ = PathNode.objects.get_or_create(
                    type='university',
                    value=edu_item['university']
                )
                nodes.append(node)
        
        # Company nodes
        for comp_item in career_path.company_sequence:
            if comp_item['company']:
                node, _ = PathNode.objects.get_or_create(
                    type='company',
                    value=comp_item['company']
                )
                nodes.append(node)
        
        # Title nodes
        for title in career_path.title_sequence:
            if title:
                node, _ = PathNode.objects.get_or_create(
                    type='title',
                    value=title
                )
                nodes.append(node)
        
        # Create connections between consecutive nodes
        for i in range(len(nodes) - 1):
            from_node = nodes[i]
            to_node = nodes[i + 1]
            
            connection, created = PathConnection.objects.get_or_create(
                from_node=from_node,
                to_node=to_node,
                defaults={'weight': 1}
            )
            
            if not created:
                connection.weight += 1
                connection.save()
            
            # Add profile to connection
            connection.profiles.add(profile)
        
        # Update node profile counts
        for node in nodes:
            node.profiles_count = PathConnection.objects.filter(
                from_node=node
            ).values('profiles').distinct().count()
            node.save()
        
        logger.info(f"Updated career graph for profile {profile_id}")
        
    except (LinkedInProfile.DoesNotExist, CareerPath.DoesNotExist):
        logger.error(f"Profile or career path not found for {profile_id}")
    except Exception as e:
        logger.error(f"Error updating career graph for profile {profile_id}: {e}")


@shared_task(bind=True)
def weekly_scraping_job(self):
    """
    Weekly scheduled task to scrape LinkedIn profiles
    This task runs every Sunday
    """
    try:
        logger.info("Starting weekly LinkedIn scraping job")
        
        # Create a new scraping job
        job = ScrapingJob.objects.create(
            name=f"Weekly Scraping - {timezone.now().strftime('%Y-%m-%d')}",
            status='pending'
        )
        
        # Add targets based on popular universities and companies
        # This would be configured based on your specific requirements
        popular_universities = [
            "Stanford University",
            "Harvard University", 
            "MIT",
            "UC Berkeley",
            "Carnegie Mellon"
        ]
        
        for university in popular_universities:
            ScrapingTarget.objects.create(
                job=job,
                type='university',
                query=f"{university} alumni",
                max_profiles=100
            )
        
        # Start the scraping job
        scrape_linkedin_profiles.delay(job.id)
        
        logger.info(f"Started weekly scraping job {job.id}")
        
    except Exception as e:
        logger.error(f"Error in weekly scraping job: {e}")


# Import json for path hash generation
import json