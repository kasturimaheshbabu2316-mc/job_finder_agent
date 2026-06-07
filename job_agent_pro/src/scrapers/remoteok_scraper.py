"""
RemoteOK job scraper using public API
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from .base_scraper import BaseScraper
from ..models.job import Job, Platform, JobType
from ..utils.text_utils import clean_text, extract_skills, normalize_location, normalize_job_title, extract_salary_range, remove_html_tags
from ..utils.date_utils import parse_date_string


class RemoteOKScraper(BaseScraper):
    """
    Scraper for RemoteOK job listings using their public API
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize RemoteOK scraper
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(Platform.REMOTEOK, config)
        
        self.api_url = self.config.get('api_url', 'https://remoteok.com/api')
        
        # Session for API requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Job-Agent/1.0',
            'Accept': 'application/json',
        })
    
    def _validate_platform_config(self) -> List[str]:
        """Validate RemoteOK-specific configuration"""
        errors = []
        
        if not self.api_url:
            errors.append("REMOTEOK_API_URL is required")
        
        return errors
    
    def fetch_jobs(self, 
                   tags: str = '',
                   search: str = '',
                   max_jobs: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch job listings from RemoteOK API
        
        Args:
            tags: Comma-separated tags to filter by
            search: Search query string
            max_jobs: Maximum number of jobs to fetch
        
        Returns:
            List of raw job data dictionaries
        """
        jobs = []
        
        try:
            # Build API URL
            url = self.api_url
            
            if tags:
                url += f"?tags={tags}"
            if search:
                separator = '&' if tags else '?'
                url += f"{separator}search={search}"
            
            self.logger.info(f"Fetching RemoteOK jobs from {url}")
            
            response = self.retry_on_failure(
                lambda: self.session.get(url, timeout=self.timeout)
            )
            
            if not response or response.status_code != 200:
                self.logger.error(f"Failed to fetch jobs: Status {response.status_code if response else 'No response'}")
                return jobs
            
            # Parse JSON response
            api_data = response.json()
            
            # RemoteOK API returns an array where first element is metadata
            # Jobs start from index 1
            if isinstance(api_data, list) and len(api_data) > 1:
                raw_jobs = api_data[1:]  # Skip metadata
            else:
                self.logger.warning("Unexpected API response format")
                return jobs
            
            self.logger.info(f"Fetched {len(raw_jobs)} jobs from RemoteOK API")
            
            # Filter and limit jobs
            for raw_job in raw_jobs:
                if len(jobs) >= max_jobs:
                    break
                
                # Skip if job is not legal or is archived
                if raw_job.get('legal') == False or raw_job.get('archived', False):
                    continue
                
                jobs.append(raw_job)
            
            self.logger.info(f"Filtered to {len(jobs)} valid jobs")
            
        except Exception as e:
            self.logger.error(f"Error fetching RemoteOK jobs: {e}")
        
        return jobs[:max_jobs]
    
    def parse_job(self, raw_job_data: Dict[str, Any]) -> Job:
        """
        Parse raw RemoteOK job data into standardized Job object
        
        Args:
            raw_job_data: Raw job data from RemoteOK API
        
        Returns:
            Standardized Job object
        """
        # Normalize job title
        job_title = normalize_job_title(raw_job_data.get('position', ''))
        
        # Normalize company name
        company_name = clean_text(raw_job_data.get('company', ''))
        
        # Normalize location (RemoteOK jobs are typically remote)
        location = raw_job_data.get('location', 'Remote')
        if not location or location.lower() == 'anywhere':
            location = 'Remote'
        else:
            location = normalize_location(location)
        
        # Extract salary range
        salary_text = raw_job_data.get('salary', '')
        salary_range = extract_salary_range(salary_text) if salary_text else salary_text
        
        # Parse posted date (RemoteOK uses epoch timestamp)
        epoch_time = raw_job_data.get('epoch')
        posted_date = None
        if epoch_time:
            try:
                posted_date = datetime.fromtimestamp(epoch_time)
            except (ValueError, TypeError):
                pass
        
        # Extract skills from tags
        tags = raw_job_data.get('tags', [])
        skills = tags if tags else []
        
        # Get job description (remove HTML tags)
        description = raw_job_data.get('description', '')
        if description:
            description = remove_html_tags(description)
        
        # Extract additional skills from description if needed
        if not skills and description:
            skills = extract_skills(description)
        
        # Determine job type
        job_type = self._determine_job_type(raw_job_data)
        
        # Construct job URL
        job_url = raw_job_data.get('url', '')
        if job_url and not job_url.startswith('http'):
            job_url = f"https://remoteok.com{job_url}"
        
        # Extract additional fields
        experience_level = raw_job_data.get('experience', '')
        industry = tags[0] if tags and len(tags) > 0 else None
        
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
            raw_job_data: Raw job data from RemoteOK
        
        Returns:
            JobType enum or None
        """
        # RemoteOK specific job type indicators
        job_type_str = raw_job_data.get('type', '').lower()
        
        if 'contract' in job_type_str:
            return JobType.CONTRACT
        elif 'part-time' in job_type_str:
            return JobType.PART_TIME
        elif 'internship' in job_type_str or 'intern' in job_type_str:
            return JobType.INTERNSHIP
        elif 'freelance' in job_type_str:
            return JobType.FREELANCE
        elif 'remote' in job_type_str:
            return JobType.REMOTE
        else:
            # Check tags for job type indicators
            tags = raw_job_data.get('tags', [])
            for tag in tags:
                tag_lower = tag.lower()
                if 'contract' in tag_lower:
                    return JobType.CONTRACT
                elif 'part-time' in tag_lower or 'part time' in tag_lower:
                    return JobType.PART_TIME
                elif 'intern' in tag_lower:
                    return JobType.INTERNSHIP
                elif 'freelance' in tag_lower:
                    return JobType.FREELANCE
            
            return JobType.FULL_TIME  # Default assumption
    
    def __del__(self):
        """Cleanup session on deletion"""
        if hasattr(self, 'session'):
            self.session.close()