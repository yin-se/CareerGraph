import time
import random
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from django.conf import settings


logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for LinkedIn scraping with ethical guidelines"""
    min_delay: float = 2.0  # Minimum delay between requests
    max_delay: float = 5.0  # Maximum delay between requests
    request_timeout: int = 30  # Request timeout in seconds
    max_retries: int = 3  # Maximum retry attempts
    respect_robots_txt: bool = True  # Always respect robots.txt
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # Rate limiting - be respectful to LinkedIn's servers
    requests_per_minute: int = 10  # Conservative rate limit
    profiles_per_session: int = 50  # Limit profiles per scraping session
    
    # Ethical constraints
    max_depth: int = 2  # Limit connection depth
    require_consent: bool = True  # Only scrape public profiles
    data_retention_days: int = 365  # Data retention policy


class EthicalLinkedInScraper:
    """
    Ethical LinkedIn scraper that respects robots.txt, rate limits,
    and only scrapes publicly available information.
    
    IMPORTANT: This scraper is designed for defensive security research
    and career path analysis only. It respects LinkedIn's terms of service
    and ethical scraping guidelines.
    """
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.session = requests.Session()
        self.driver = None
        self.last_request_time = 0
        self.request_count = 0
        self.session_start_time = time.time()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def _init_driver(self):
        """Initialize Selenium WebDriver with ethical settings"""
        if self.driver:
            return
            
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={self.config.user_agent}')
        
        # Disable images and CSS for faster loading and reduced bandwidth
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Only for basic scraping
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.config.request_timeout)
        
    def _respect_rate_limit(self):
        """Implement respectful rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        min_interval = 60 / self.config.requests_per_minute
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # Add random jitter to avoid detection
        jitter = random.uniform(self.config.min_delay, self.config.max_delay)
        time.sleep(jitter)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
    def _check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed according to robots.txt"""
        if not self.config.respect_robots_txt:
            return True
            
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                # Simple robots.txt parsing - in production, use robotparser
                robots_content = response.text.lower()
                if 'disallow: /' in robots_content and '*' in robots_content:
                    logger.warning(f"Robots.txt disallows scraping for {url}")
                    return False
                    
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            
        return True
        
    def _is_public_profile(self, profile_url: str) -> bool:
        """
        Check if a LinkedIn profile is publicly accessible
        without requiring authentication
        """
        try:
            self._respect_rate_limit()
            response = self.session.get(profile_url, timeout=self.config.request_timeout)
            
            # Check if we're redirected to login page
            if 'login' in response.url or 'authwall' in response.url:
                return False
                
            # Check for public profile indicators
            soup = BeautifulSoup(response.content, 'html.parser')
            return bool(soup.find('meta', {'name': 'description'}))
            
        except Exception as e:
            logger.error(f"Error checking profile accessibility: {e}")
            return False
            
    def scrape_public_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Scrape publicly available information from a LinkedIn profile
        """
        if not self._check_robots_txt(profile_url):
            logger.warning(f"Robots.txt disallows scraping {profile_url}")
            return None
            
        if not self._is_public_profile(profile_url):
            logger.info(f"Profile not publicly accessible: {profile_url}")
            return None
            
        try:
            self._respect_rate_limit()
            
            # Check session limits
            if self.request_count >= self.config.profiles_per_session:
                logger.warning("Session profile limit reached")
                return None
                
            self._init_driver()
            self.driver.get(profile_url)
            
            # Wait for basic content to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Extract basic public information only
            profile_data = self._extract_public_data()
            profile_data['scraped_url'] = profile_url
            profile_data['scraped_at'] = time.time()
            
            return profile_data
            
        except TimeoutException:
            logger.error(f"Timeout loading profile: {profile_url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            return None
            
    def _extract_public_data(self) -> Dict:
        """
        Extract only publicly available information from the current page
        """
        data = {}
        
        try:
            # Name and headline - only if publicly visible
            name_element = self.driver.find_element(By.CSS_SELECTOR, "h1")
            if name_element:
                data['full_name'] = name_element.text.strip()
                
            headline_element = self.driver.find_element(By.CSS_SELECTOR, ".text-body-medium")
            if headline_element:
                data['headline'] = headline_element.text.strip()
                
            # Location - if publicly visible
            location_elements = self.driver.find_elements(By.CSS_SELECTOR, ".text-body-small")
            for element in location_elements:
                text = element.text.strip()
                if any(indicator in text.lower() for indicator in ['area', 'region', 'location']):
                    data['location'] = text
                    break
                    
            # Public education information
            education_data = self._extract_public_education()
            if education_data:
                data['education'] = education_data
                
            # Public experience information
            experience_data = self._extract_public_experience()
            if experience_data:
                data['experience'] = experience_data
                
        except NoSuchElementException:
            logger.debug("Some profile elements not found - may be private")
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            
        return data
        
    def _extract_public_education(self) -> List[Dict]:
        """Extract publicly visible education information"""
        education_list = []
        
        try:
            # Look for education section
            education_sections = self.driver.find_elements(
                By.CSS_SELECTOR, "[data-field='education'] li, .education li"
            )
            
            for section in education_sections[:5]:  # Limit to prevent overloading
                edu_data = {}
                
                # School name
                school_element = section.find_element(By.CSS_SELECTOR, "h3, .school-name")
                if school_element:
                    edu_data['university'] = school_element.text.strip()
                    
                # Degree
                degree_element = section.find_element(By.CSS_SELECTOR, ".degree")
                if degree_element:
                    edu_data['degree'] = degree_element.text.strip()
                    
                # Years
                time_element = section.find_element(By.CSS_SELECTOR, ".date-range")
                if time_element:
                    edu_data['years'] = time_element.text.strip()
                    
                if edu_data:
                    education_list.append(edu_data)
                    
        except Exception as e:
            logger.debug(f"Could not extract education data: {e}")
            
        return education_list
        
    def _extract_public_experience(self) -> List[Dict]:
        """Extract publicly visible experience information"""
        experience_list = []
        
        try:
            # Look for experience section
            experience_sections = self.driver.find_elements(
                By.CSS_SELECTOR, "[data-field='experience'] li, .experience li"
            )
            
            for section in experience_sections[:10]:  # Limit to prevent overloading
                exp_data = {}
                
                # Job title
                title_element = section.find_element(By.CSS_SELECTOR, "h3, .job-title")
                if title_element:
                    exp_data['title'] = title_element.text.strip()
                    
                # Company
                company_element = section.find_element(By.CSS_SELECTOR, ".company-name")
                if company_element:
                    exp_data['company'] = company_element.text.strip()
                    
                # Duration
                duration_element = section.find_element(By.CSS_SELECTOR, ".date-range")
                if duration_element:
                    exp_data['duration'] = duration_element.text.strip()
                    
                if exp_data:
                    experience_list.append(exp_data)
                    
        except Exception as e:
            logger.debug(f"Could not extract experience data: {e}")
            
        return experience_list
        
    def search_public_profiles(self, query: str, max_results: int = 50) -> List[str]:
        """
        Search for public LinkedIn profiles using Google search
        (more ethical than direct LinkedIn search)
        """
        profile_urls = []
        
        try:
            # Use Google search with site:linkedin.com/in
            search_query = f"site:linkedin.com/in {query}"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            self._respect_rate_limit()
            response = self.session.get(search_url)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract LinkedIn profile URLs from search results
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'linkedin.com/in/' in href and '/url?q=' in href:
                    # Extract actual URL from Google redirect
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    if 'linkedin.com/in/' in actual_url:
                        profile_urls.append(actual_url)
                        
                if len(profile_urls) >= max_results:
                    break
                    
        except Exception as e:
            logger.error(f"Error searching profiles: {e}")
            
        return profile_urls[:max_results]
        
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Utility functions for data processing
def clean_profile_data(raw_data: Dict) -> Dict:
    """Clean and standardize scraped profile data"""
    cleaned = {}
    
    if 'full_name' in raw_data:
        cleaned['full_name'] = raw_data['full_name'].strip()
        
    if 'headline' in raw_data:
        cleaned['headline'] = raw_data['headline'].strip()
        
    if 'location' in raw_data:
        cleaned['location'] = raw_data['location'].strip()
        
    # Process education data
    if 'education' in raw_data:
        cleaned['education'] = []
        for edu in raw_data['education']:
            if 'university' in edu:
                cleaned['education'].append({
                    'university': edu['university'].strip(),
                    'degree': edu.get('degree', '').strip(),
                    'years': edu.get('years', '').strip(),
                })
                
    # Process experience data
    if 'experience' in raw_data:
        cleaned['experience'] = []
        for exp in raw_data['experience']:
            if 'title' in exp and 'company' in exp:
                cleaned['experience'].append({
                    'title': exp['title'].strip(),
                    'company': exp['company'].strip(),
                    'duration': exp.get('duration', '').strip(),
                })
                
    return cleaned


def validate_profile_data(data: Dict) -> bool:
    """Validate that profile data meets minimum requirements"""
    required_fields = ['full_name']
    
    for field in required_fields:
        if field not in data or not data[field].strip():
            return False
            
    # Ensure we have either education or experience data
    has_education = 'education' in data and len(data['education']) > 0
    has_experience = 'experience' in data and len(data['experience']) > 0
    
    return has_education or has_experience