"""
Abstract base class for job scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
import logging
from ..models.job import Job, Platform
from ..utils.logger import get_logger


class BaseScraper(ABC):
    """
    Abstract base class for platform-specific job scrapers
    
    All platform scrapers must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, platform: Platform, config: Dict[str, Any] = None):
        """
        Initialize base scraper
        
        Args:
            platform: Platform enum value
            config: Platform-specific configuration
        """
        self.platform = platform
        self.config = config or {}
        self.logger = get_logger(f"scraper.{platform.value}")
        
        # Common settings
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 2.0)
        self.enabled = self.config.get('enabled', True)
        
        # Statistics
        self.jobs_scraped = 0
        self.errors_encountered = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    @abstractmethod
    def fetch_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch raw job data from the platform
        
        Args:
            **kwargs: Platform-specific search parameters
        
        Returns:
            List of raw job data dictionaries
        """
        pass
    
    @abstractmethod
    def parse_job(self, raw_job_data: Dict[str, Any]) -> Job:
        """
        Parse raw job data into standardized Job object
        
        Args:
            raw_job_data: Raw job data from platform
        
        Returns:
            Standardized Job object
        """
        pass
    
    def scrape_jobs(self, **kwargs) -> List[Job]:
        """
        Main scraping method - fetches and parses jobs
        
        Args:
            **kwargs: Search parameters for fetching jobs
        
        Returns:
            List of standardized Job objects
        """
        if not self.enabled:
            self.logger.warning(f"Scraper for {self.platform.value} is disabled")
            return []
        
        self.start_time = datetime.now()
        self.logger.info(f"Starting scraping for {self.platform.value}")
        
        try:
            # Fetch raw job data
            raw_jobs = self.fetch_jobs(**kwargs)
            self.logger.info(f"Fetched {len(raw_jobs)} raw job listings")
            
            # Parse raw jobs into Job objects
            jobs = []
            for raw_job in raw_jobs:
                try:
                    job = self.parse_job(raw_job)
                    jobs.append(job)
                    self.jobs_scraped += 1
                except Exception as e:
                    self.logger.error(f"Error parsing job: {e}")
                    self.errors_encountered += 1
                    continue
                
                # Rate limiting between jobs
                if self.rate_limit_delay > 0:
                    time.sleep(self.rate_limit_delay)
            
            self.logger.info(f"Successfully scraped {len(jobs)} jobs from {self.platform.value}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            self.errors_encountered += 1
            return []
        finally:
            self.end_time = datetime.now()
            self._log_statistics()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scraping statistics
        
        Returns:
            Dictionary with scraping statistics
        """
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'platform': self.platform.value,
            'jobs_scraped': self.jobs_scraped,
            'errors_encountered': self.errors_encountered,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'success_rate': self.jobs_scraped / (self.jobs_scraped + self.errors_encountered) if (self.jobs_scraped + self.errors_encountered) > 0 else 0,
        }
    
    def _log_statistics(self):
        """Log scraping statistics"""
        stats = self.get_statistics()
        self.logger.info(f"Scraping statistics for {self.platform.value}:")
        self.logger.info(f"  Jobs scraped: {stats['jobs_scraped']}")
        self.logger.info(f"  Errors encountered: {stats['errors_encountered']}")
        duration_str = f"{stats['duration_seconds']:.2f}s" if stats['duration_seconds'] else 'N/A'
        self.logger.info(f"  Duration: {duration_str}")
        self.logger.info(f"  Success rate: {stats['success_rate']:.2%}")
    
    def reset_statistics(self):
        """Reset scraping statistics"""
        self.jobs_scraped = 0
        self.errors_encountered = 0
        self.start_time = None
        self.end_time = None
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """
        Validate platform-specific configuration
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if platform is enabled
        if not self.enabled:
            errors.append(f"Scraper for {self.platform.value} is disabled")
        
        # Platform-specific validation should be implemented in subclasses
        platform_errors = self._validate_platform_config()
        errors.extend(platform_errors)
        
        return len(errors) == 0, errors
    
    def _validate_platform_config(self) -> List[str]:
        """
        Platform-specific configuration validation
        
        Subclasses should override this method to add platform-specific validation
        
        Returns:
            List of configuration errors
        """
        return []
    
    def handle_rate_limit(self):
        """Handle rate limiting by sleeping for configured delay"""
        if self.rate_limit_delay > 0:
            self.logger.debug(f"Rate limiting: sleeping for {self.rate_limit_delay} seconds")
            time.sleep(self.rate_limit_delay)
    
    def retry_on_failure(self, func, max_retries: int = None) -> Optional[Any]:
        """
        Retry a function on failure
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries (default: use instance setting)
        
        Returns:
            Function result or None if all retries fail
        """
        retries = max_retries or self.max_retries
        
        for attempt in range(retries):
            try:
                return func()
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"All {retries} attempts failed")
                    return None
        
        return None