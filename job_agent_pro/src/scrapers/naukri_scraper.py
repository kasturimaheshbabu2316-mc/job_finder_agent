"""
Naukri job scraper using HTML parsing
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote
import random
from .base_scraper import BaseScraper
from ..models.job import Job, Platform, JobType
from ..utils.text_utils import clean_text, extract_skills, normalize_location, normalize_job_title, extract_salary_range
from ..utils.date_utils import parse_date_string, parse_relative_date


class NaukriScraper(BaseScraper):
    """
    Scraper for Naukri.com job listings using HTML parsing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Naukri scraper
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(Platform.NAUKRI, config)
        
        self.base_url = self.config.get('base_url', 'https://www.naukri.com')
        self.search_url = self.config.get('search_url', 'https://www.naukri.com/jobapi/v7/search')
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def _validate_platform_config(self) -> List[str]:
        """Validate Naukri-specific configuration"""
        errors = []
        
        if not self.base_url:
            errors.append("NAUKRI_BASE_URL is required")
        
        if not self.search_url:
            errors.append("NAUKRI_SEARCH_URL is required")
        
        return errors
    
    def _get_headers(self) -> Dict[str, str]:
        """Get random headers for each request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def fetch_jobs(self, 
                   keywords: str = 'software engineer',
                   location: str = 'bengaluru',
                   experience: str = '',
                   max_jobs: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch job listings from Naukri
        
        Args:
            keywords: Job keywords to search for
            location: Location to search in
            experience: Experience level
            max_jobs: Maximum number of jobs to fetch
        
        Returns:
            List of raw job data dictionaries
        """
        jobs = []
        page = 1
        
        self.logger.info(f"Fetching Naukri jobs with keywords: {keywords}, location: {location}")
        
        while len(jobs) < max_jobs:
            try:
                # Build search URL
                search_params = {
                    'keywords': keywords,
                    'location': location,
                    'experience': experience,
                    'page': page,
                }
                
                url = f"{self.search_url}?" + '&'.join([f"{k}={quote(str(v))}" for k, v in search_params.items()])
                
                self.logger.debug(f"Fetching page {page}: {url}")
                
                response = self.retry_on_failure(
                    lambda: self.session.get(url, headers=self._get_headers(), timeout=self.timeout)
                )
                
                if not response or response.status_code != 200:
                    self.logger.error(f"Failed to fetch page {page}: Status {response.status_code if response else 'No response'}")
                    break
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract job cards
                job_cards = soup.find_all('div', class_='jobTuple')
                
                if not job_cards:
                    self.logger.warning(f"No job cards found on page {page}")
                    break
                
                page_jobs = self._extract_job_cards(job_cards)
                jobs.extend(page_jobs)
                
                self.logger.info(f"Found {len(page_jobs)} jobs on page {page}, total: {len(jobs)}")
                
                # Check if we've reached max jobs or no more pages
                if len(page_jobs) == 0 or len(jobs) >= max_jobs:
                    break
                
                page += 1
                self.handle_rate_limit()
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                break
        
        return jobs[:max_jobs]
    
    def _extract_job_cards(self, job_cards) -> List[Dict[str, Any]]:
        """
        Extract job data from HTML job cards
        
        Args:
            job_cards: BeautifulSoup elements representing job cards
        
        Returns:
            List of job data dictionaries
        """
        jobs = []
        
        for card in job_cards:
            try:
                job_data = {}
                
                # Job title
                title_elem = card.find('a', class_='title')
                job_data['title'] = clean_text(title_elem.text) if title_elem else ''
                
                # Company name
                company_elem = card.find('a', class_='subTitle')
                job_data['company'] = clean_text(company_elem.text) if company_elem else ''
                
                # Location
                location_elem = card.find('li', class_='location')
                job_data['location'] = clean_text(location_elem.text) if location_elem else ''
                
                # Experience
                exp_elem = card.find('li', class_='experience')
                job_data['experience'] = clean_text(exp_elem.text) if exp_elem else ''
                
                # Salary
                salary_elem = card.find('li', class_='salary')
                job_data['salary'] = clean_text(salary_elem.text) if salary_elem else ''
                
                # Posted date
                posted_elem = card.find('span', class_='postedDate')
                job_data['posted_date'] = clean_text(posted_elem.text) if posted_elem else ''
                
                # Job URL
                if title_elem:
                    job_data['url'] = urljoin(self.base_url, title_elem.get('href', ''))
                else:
                    job_data['url'] = ''
                
                # Job description (might need to fetch individual job page)
                desc_elem = card.find('div', class_='job-description')
                job_data['description'] = clean_text(desc_elem.text) if desc_elem else ''
                
                # Skills tags
                skills_elems = card.find_all('li', class_='skill-tag')
                job_data['skills'] = [clean_text(elem.text) for elem in skills_elems] if skills_elems else []
                
                jobs.append(job_data)
                
            except Exception as e:
                self.logger.warning(f"Error extracting job card: {e}")
                continue
        
        return jobs
    
    def parse_job(self, raw_job_data: Dict[str, Any]) -> Job:
        """
        Parse raw Naukri job data into standardized Job object
        
        Args:
            raw_job_data: Raw job data from Naukri
        
        Returns:
            Standardized Job object
        """
        # Normalize job title
        job_title = normalize_job_title(raw_job_data.get('title', ''))
        
        # Normalize company name
        company_name = clean_text(raw_job_data.get('company', ''))
        
        # Normalize location
        location = normalize_location(raw_job_data.get('location', ''))
        
        # Extract salary range
        salary_text = raw_job_data.get('salary', '')
        salary_range = extract_salary_range(salary_text)
        
        # Parse posted date
        posted_date_str = raw_job_data.get('posted_date', '')
        posted_date = parse_relative_date(posted_date_str)
        
        # Extract skills
        skills = raw_job_data.get('skills', [])
        if not skills and raw_job_data.get('description'):
            skills = extract_skills(raw_job_data['description'])
        
        # Determine job type from description or title
        job_type = self._determine_job_type(raw_job_data)
        
        # Create Job object
        return Job(
            job_title=job_title,
            company_name=company_name,
            job_description=raw_job_data.get('description', ''),
            location=location,
            salary_range=salary_range,
            job_type=job_type,
            posted_date=posted_date,
            job_url=raw_job_data.get('url', ''),
            platform_source=self.platform,
            skills=skills,
            experience_level=raw_job_data.get('experience', ''),
            raw_data=raw_job_data,
        )
    
    def _determine_job_type(self, raw_job_data: Dict[str, Any]) -> Optional[JobType]:
        """
        Determine job type from raw job data
        
        Args:
            raw_job_data: Raw job data
        
        Returns:
            JobType enum or None
        """
        title = raw_job_data.get('title', '').lower()
        description = raw_job_data.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Check for job type indicators
        if 'contract' in combined_text:
            return JobType.CONTRACT
        elif 'part-time' in combined_text or 'part time' in combined_text:
            return JobType.PART_TIME
        elif 'internship' in combined_text or 'intern' in combined_text:
            return JobType.INTERNSHIP
        elif 'freelance' in combined_text or 'freelancer' in combined_text:
            return JobType.FREELANCE
        elif 'remote' in combined_text:
            return JobType.REMOTE
        elif 'hybrid' in combined_text:
            return JobType.HYBRID
        else:
            return JobType.FULL_TIME  # Default assumption
    
    def __del__(self):
        """Cleanup session on deletion"""
        if hasattr(self, 'session'):
            self.session.close()