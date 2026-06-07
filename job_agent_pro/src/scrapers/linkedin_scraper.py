"""
LinkedIn job scraper using Firecrawl
"""

from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote
import json
from .base_scraper import BaseScraper
from ..models.job import Job, Platform, JobType
from ..utils.text_utils import clean_text, extract_skills, normalize_location, normalize_job_title, extract_salary_range, remove_html_tags
from ..utils.date_utils import parse_date_string, parse_relative_date
from config import FIRECRAWL_API_KEY, FIRECRAWL_API_URL


class LinkedInScraper(BaseScraper):
    """
    Scraper for LinkedIn job listings using Firecrawl
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize LinkedIn scraper with Firecrawl
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(Platform.LINKEDIN, config)
        
        self.api_key = self.config.get('api_key', FIRECRAWL_API_KEY)
        self.api_url = self.config.get('api_url', FIRECRAWL_API_URL)
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        
        # LinkedIn base URLs
        self.base_url = 'https://www.linkedin.com'
        self.jobs_url = 'https://www.linkedin.com/jobs/search'
        
        # Firecrawl client (will be initialized if API key is available)
        self.firecrawl_client = None
        self._initialize_firecrawl()
    
    def _initialize_firecrawl(self):
        """Initialize Firecrawl client"""
        if not self.api_key:
            self.logger.warning("Firecrawl API key not provided, LinkedIn scraper will not function")
            return
        
        try:
            # Try to import and initialize Firecrawl
            try:
                from firecrawl import FirecrawlApp
                self.firecrawl_client = FirecrawlApp(api_key=self.api_key)
                self.logger.info("Firecrawl client initialized successfully")
            except ImportError:
                self.logger.error("Firecrawl package not installed. Install with: pip install firecrawl-py")
            except Exception as e:
                self.logger.error(f"Failed to initialize Firecrawl: {e}")
                
        except Exception as e:
            self.logger.error(f"Error initializing Firecrawl: {e}")
    
    def _validate_platform_config(self) -> List[str]:
        """Validate LinkedIn-specific configuration"""
        errors = []
        
        if not self.api_key:
            errors.append("FIRECRAWL_API_KEY is required for LinkedIn scraping")
        
        if not self.username or not self.password:
            errors.append("LINKEDIN_USERNAME and LINKEDIN_PASSWORD are recommended for LinkedIn scraping")
        
        return errors
    
    def fetch_jobs(self, 
                   keywords: str = 'software engineer',
                   location: str = 'remote',
                   max_jobs: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch job listings from LinkedIn using Firecrawl
        
        Args:
            keywords: Job keywords to search for
            location: Location to search in
            max_jobs: Maximum number of jobs to fetch
        
        Returns:
            List of raw job data dictionaries
        """
        if not self.firecrawl_client:
            self.logger.error("Firecrawl client not initialized")
            return []
        
        jobs = []
        
        try:
            # Build LinkedIn job search URL
            search_params = {
                'keywords': keywords,
                'location': location,
                'f_JT': 'F',  # Full-time jobs
            }
            
            url = self.jobs_url + '?' + '&'.join([f"{k}={quote(str(v))}" for k, v in search_params.items()])
            
            self.logger.info(f"Fetching LinkedIn jobs using Firecrawl: {url}")
            
            # Use Firecrawl to scrape the page
            scrape_result = self.firecrawl_client.scrape_url(
                url,
                params={
                    'formats': ['markdown', 'html'],
                }
            )
            
            if not scrape_result or not scrape_result.get('content'):
                self.logger.error("Firecrawl returned no content")
                return jobs
            
            content = scrape_result['content']
            
            # Parse the scraped content to extract job data
            # This is a simplified parser - real implementation would need more sophisticated parsing
            jobs = self._parse_linkedin_response(content, url)
            
            self.logger.info(f"Fetched {len(jobs)} jobs from LinkedIn")
            
        except Exception as e:
            self.logger.error(f"Error fetching LinkedIn jobs: {e}")
        
        return jobs[:max_jobs]
    
    def _parse_linkedin_response(self, content: str, source_url: str) -> List[Dict[str, Any]]:
        """
        Parse LinkedIn response content to extract job data
        
        Args:
            content: Scraped content from Firecrawl
            source_url: Source URL for context
        
        Returns:
            List of job data dictionaries
        """
        jobs = []
        
        try:
            # This is a simplified parser. In a real implementation, you would need to:
            # 1. Parse HTML/JSON-LD structures from the content
            # 2. Extract job cards with proper selectors
            # 3. Handle pagination
            # 4. Extract detailed job information
            
            # For now, we'll create a mock structure that can be enhanced
            # when you have actual Firecrawl response format
            
            # Example: Try to find job listings in the content
            # This would need to be adapted based on actual response format
            
            # Placeholder implementation - in real usage, you'd parse the actual content
            # For demonstration, we'll return empty list since we don't have actual content
            
            self.logger.warning("LinkedIn content parsing needs to be implemented based on actual Firecrawl response format")
            
        except Exception as e:
            self.logger.error(f"Error parsing LinkedIn response: {e}")
        
        return jobs
    
    def parse_job(self, raw_job_data: Dict[str, Any]) -> Job:
        """
        Parse raw LinkedIn job data into standardized Job object
        
        Args:
            raw_job_data: Raw job data from LinkedIn
        
        Returns:
            Standardized Job object
        """
        # Normalize job title
        job_title = normalize_job_title(raw_job_data.get('title', ''))
        
        # Normalize company name
        company_name = clean_text(raw_job_data.get('company', ''))
        
        # Normalize location
        location = raw_job_data.get('location', '')
        if location:
            location = normalize_location(location)
        
        # Extract salary range
        salary_text = raw_job_data.get('salary', '')
        salary_range = extract_salary_range(salary_text) if salary_text else salary_text
        
        # Parse posted date
        posted_date_str = raw_job_data.get('posted_date', '')
        posted_date = parse_relative_date(posted_date_str) or parse_date_string(posted_date_str)
        
        # Extract skills
        skills = raw_job_data.get('skills', [])
        if not skills and raw_job_data.get('description'):
            skills = extract_skills(raw_job_data['description'])
        
        # Clean job description (remove HTML if present)
        description = raw_job_data.get('description', '')
        if description:
            description = remove_html_tags(description)
        
        # Determine job type
        job_type = self._determine_job_type(raw_job_data)
        
        # Construct job URL
        job_url = raw_job_data.get('url', '')
        if job_url and not job_url.startswith('http'):
            job_url = urljoin(self.base_url, job_url)
        
        # Extract additional fields
        experience_level = raw_job_data.get('experience_level', '')
        industry = raw_job_data.get('industry', '')
        
        # Create Job object
        return Job(
            job_title=job_title,
            company_name=company_name,
            job_description=clean_text(description),
            location=location,
            salary_range=salary_range,
            job_type=job_type,
            posted_date=posted_date,
            job_url=job_url,
            platform_source=self.platform,
            skills=skills,
            experience_level=experience_level,
            industry=industry,
            company_size=raw_job_data.get('company_size', ''),
            raw_data=raw_job_data,
        )
    
    def _determine_job_type(self, raw_job_data: Dict[str, Any]) -> Optional[JobType]:
        """
        Determine job type from raw job data
        
        Args:
            raw_job_data: Raw job data from LinkedIn
        
        Returns:
            JobType enum or None
        """
        employment_type = raw_job_data.get('employment_type', '').lower()
        
        if 'contract' in employment_type:
            return JobType.CONTRACT
        elif 'part-time' in employment_type or 'part time' in employment_type:
            return JobType.PART_TIME
        elif 'internship' in employment_type or 'intern' in employment_type:
            return JobType.INTERNSHIP
        elif 'freelance' in employment_type:
            return JobType.FREELANCE
        elif 'remote' in employment_type:
            return JobType.REMOTE
        else:
            # Check description for job type indicators
            description = raw_job_data.get('description', '').lower()
            if 'contract' in description:
                return JobType.CONTRACT
            elif 'part-time' in description or 'part time' in description:
                return JobType.PART_TIME
            elif 'intern' in description:
                return JobType.INTERNSHIP
            elif 'freelance' in description:
                return JobType.FREELANCE
            elif 'remote' in description:
                return JobType.REMOTE
            
            return JobType.FULL_TIME  # Default assumption
    
    def fetch_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed job information from a specific LinkedIn job URL
        
        Args:
            job_url: URL to the specific LinkedIn job posting
        
        Returns:
            Detailed job data dictionary or None
        """
        if not self.firecrawl_client:
            self.logger.error("Firecrawl client not initialized")
            return None
        
        try:
            self.logger.info(f"Fetching job details from: {job_url}")
            
            scrape_result = self.firecrawl_client.scrape_url(
                job_url,
                params={
                    'formats': ['markdown', 'html'],
                }
            )
            
            if scrape_result and scrape_result.get('content'):
                return self._parse_job_details(scrape_result['content'], job_url)
            else:
                self.logger.error("Failed to fetch job details")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching job details: {e}")
            return None
    
    def _parse_job_details(self, content: str, job_url: str) -> Dict[str, Any]:
        """
        Parse detailed job information from scraped content
        
        Args:
            content: Scraped content from Firecrawl
            job_url: Source URL
        
        Returns:
            Detailed job data dictionary
        """
        # This would need to be implemented based on actual Firecrawl response format
        # For now, return a basic structure
        return {
            'url': job_url,
            'description': content,
        }
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'firecrawl_client'):
            self.firecrawl_client = None