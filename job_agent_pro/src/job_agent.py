"""
Main JobAgent controller - orchestrates all components
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import concurrent.futures
from src.models.job import Job, Platform
from src.scrapers import NaukriScraper, RemoteOKScraper
from src.processors import JobNormalizer, JobDeduplicator, JobFilter, JobValidator
from src.utils.logger import get_logger
from src.utils.csv_utils import write_jobs_to_csv, get_csv_statistics
from src.utils.input_validator import InputValidator
from config import PLATFORM_CONFIGS, get_config


class JobAgent:
    """
    Main controller for job scraping and processing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize JobAgent with configuration
        
        Args:
            config: Configuration dictionary (uses default if not provided)
        """
        self.config = config or get_config()
        self.logger = get_logger("job_agent")
        
        # Initialize scrapers
        self.scrapers = self._initialize_scrapers()
        
        # Initialize processors
        self.normalizer = JobNormalizer()
        self.deduplicator = JobDeduplicator()
        self.filter = JobFilter()
        self.validator = JobValidator()
        
        # Initialize input validator for user input processing
        self.input_validator = InputValidator()
        
        # Job storage
        self.all_jobs: List[Job] = []
        self.processed_jobs: List[Job] = []
        
        # Statistics
        self.run_statistics = {
            'start_time': None,
            'end_time': None,
            'total_jobs_scraped': 0,
            'total_jobs_processed': 0,
            'total_jobs_exported': 0,
            'platform_stats': {}
        }
    
    def _initialize_scrapers(self) -> Dict[Platform, Any]:
        """
        Initialize platform scrapers based on configuration
        
        Returns:
            Dictionary of initialized scrapers
        """
        scrapers = {}
        
        # Initialize Naukri scraper
        if PLATFORM_CONFIGS.get('naukri', {}).get('enabled', True):
            naukri_config = PLATFORM_CONFIGS['naukri']
            scrapers[Platform.NAUKRI] = NaukriScraper(naukri_config)
            self.logger.info("Naukri scraper initialized")
        
        # Initialize RemoteOK scraper
        if PLATFORM_CONFIGS.get('remoteok', {}).get('enabled', True):
            remoteok_config = PLATFORM_CONFIGS['remoteok']
            scrapers[Platform.REMOTEOK] = RemoteOKScraper(remoteok_config)
            self.logger.info("RemoteOK scraper initialized")
        
        return scrapers
    
    def scrape_jobs(self,
                   platforms: Optional[List[Platform]] = None,
                   keywords: str = 'software engineer',
                   location: str = 'remote',
                   max_jobs_per_platform: int = 50,
                   parallel: bool = True,
                   skip_input_validation: bool = False) -> List[Job]:
        """
        Scrape jobs from specified platforms based on exact user-provided job role and location

        Args:
            platforms: List of platforms to scrape (None = all enabled)
            keywords: Exact job role/keywords provided by user for targeted search (e.g., "software engineer", "data scientist")
            location: Exact location provided by user for filtering (e.g., "remote", "bengaluru", "mumbai")
            max_jobs_per_platform: Maximum jobs to scrape per platform
            parallel: Whether to scrape platforms in parallel
            skip_input_validation: Whether to skip input validation (use if already validated)

        Returns:
            List of scraped Job objects
        """
        self.run_statistics['start_time'] = datetime.now()
        self.all_jobs = []
        
        # Validate and normalize user input (unless already validated)
        if not skip_input_validation:
            self.logger.info("Validating and normalizing user input...")
            is_valid, normalized_inputs, errors = self.input_validator.validate_user_input(keywords, location)
            
            if not is_valid:
                self.logger.error(f"Input validation failed: {errors}")
                raise ValueError(f"Invalid input: {', '.join(errors)}")
            
            keywords = normalized_inputs['job_role']
            location = normalized_inputs['location']
            self.logger.info(f"Normalized input: {self.input_validator.format_input_summary(keywords, location)}")
        
        platforms_to_scrape = platforms or list(self.scrapers.keys())
        self.logger.info(f"Starting job scrape from {len(platforms_to_scrape)} platforms")
        self.logger.info(f"Job Role: {keywords}, Location: {location}")
        
        if parallel:
            jobs = self._scrape_parallel(platforms_to_scrape, keywords, location, max_jobs_per_platform)
        else:
            jobs = self._scrape_sequential(platforms_to_scrape, keywords, location, max_jobs_per_platform)
        
        self.all_jobs = jobs
        self.run_statistics['total_jobs_scraped'] = len(jobs)
        
        self.logger.info(f"Scraping complete: {len(jobs)} total jobs scraped")
        
        return jobs
    
    def _scrape_sequential(self, platforms: List[Platform], keywords: str, location: str, max_jobs: int) -> List[Job]:
        """Scrape jobs from platforms sequentially"""
        all_jobs = []
        
        for platform in platforms:
            if platform not in self.scrapers:
                self.logger.warning(f"Scraper for {platform.value} not available")
                continue
            
            scraper = self.scrapers[platform]
            
            try:
                # Platform-specific parameters
                scrape_params = self._get_scrape_params(platform, keywords, location)
                scrape_params['max_jobs'] = max_jobs
                
                jobs = scraper.scrape_jobs(**scrape_params)
                all_jobs.extend(jobs)
                
                # Store platform statistics
                self.run_statistics['platform_stats'][platform.value] = scraper.get_statistics()
                
            except Exception as e:
                self.logger.error(f"Error scraping {platform.value}: {e}")
        
        return all_jobs
    
    def _scrape_parallel(self, platforms: List[Platform], keywords: str, location: str, max_jobs: int) -> List[Job]:
        """Scrape jobs from platforms in parallel"""
        all_jobs = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(platforms)) as executor:
            future_to_platform = {}
            
            for platform in platforms:
                if platform not in self.scrapers:
                    self.logger.warning(f"Scraper for {platform.value} not available")
                    continue
                
                scraper = self.scrapers[platform]
                scrape_params = self._get_scrape_params(platform, keywords, location)
                scrape_params['max_jobs'] = max_jobs
                
                future = executor.submit(scraper.scrape_jobs, **scrape_params)
                future_to_platform[future] = platform
            
            for future in concurrent.futures.as_completed(future_to_platform):
                platform = future_to_platform[future]
                scraper = self.scrapers[platform]
                
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    self.run_statistics['platform_stats'][platform.value] = scraper.get_statistics()
                except Exception as e:
                    self.logger.error(f"Error scraping {platform.value}: {e}")
        
        return all_jobs
    
    def _get_scrape_params(self, platform: Platform, keywords: str, location: str) -> Dict[str, Any]:
        """Get platform-specific scrape parameters"""
        params = {
            'keywords': keywords,
            'location': location,
        }
        
        # Platform-specific adjustments
        if platform == Platform.REMOTEOK:
            params.pop('location')  # RemoteOK uses different parameter structure
            params['search'] = keywords
        
        return params
    
    def process_jobs(self, 
                    normalize: bool = True,
                    deduplicate: bool = True,
                    validate: bool = True,
                    filter_config: Optional[Dict[str, Any]] = None) -> List[Job]:
        """
        Process scraped jobs through normalization, deduplication, and filtering
        
        Args:
            normalize: Whether to normalize job data
            deduplicate: Whether to remove duplicates
            validate: Whether to validate job data
            filter_config: Filter configuration dictionary
        
        Returns:
            List of processed Job objects
        """
        if not self.all_jobs:
            self.logger.warning("No jobs to process")
            return []
        
        self.logger.info(f"Processing {len(self.all_jobs)} jobs")
        jobs = self.all_jobs.copy()
        
        # Normalization
        if normalize:
            self.logger.info("Normalizing job data...")
            jobs = self.normalizer.normalize_jobs(jobs)
        
        # Deduplication
        if deduplicate:
            self.logger.info("Removing duplicate jobs...")
            jobs = self.deduplicator.deduplicate_jobs(jobs, strategy='hybrid')
        
        # Filtering
        if filter_config:
            self.logger.info("Filtering jobs...")
            jobs = self.filter.filter_jobs(jobs, **filter_config)
        
        # Validation
        if validate:
            self.logger.info("Validating job data...")
            validation_results = self.validator.validate_jobs(jobs)
            jobs = validation_results['valid_jobs']
            
            # Log validation results
            stats = validation_results['statistics']
            self.logger.info(f"Validation: {stats['total_passed']}/{stats['total_validated']} jobs passed")
        
        self.processed_jobs = jobs
        self.run_statistics['total_jobs_processed'] = len(jobs)
        
        self.logger.info(f"Processing complete: {len(jobs)} jobs remaining")
        
        return jobs
    
    def run_full_pipeline(self,
                         keywords: str = 'software engineer',
                         location: str = 'remote',
                         max_jobs_per_platform: int = 50,
                         output_file: str = None,
                         filter_config: Optional[Dict[str, Any]] = None,
                         skip_input_validation: bool = False) -> List[Job]:
        """
        Run the complete job agent pipeline with exact user-provided job role and location

        Args:
            keywords: Exact job role/keywords provided by user for targeted search (e.g., "software engineer", "data scientist")
            location: Exact location provided by user for filtering (e.g., "remote", "bengaluru", "mumbai")
            max_jobs_per_platform: Maximum jobs to scrape per platform
            output_file: CSV file to export results
            filter_config: Additional filter configuration
            skip_input_validation: Whether to skip input validation (use if already validated at CLI level)

        Returns:
            List of processed Job objects
        """
        self.logger.info("=" * 50)
        self.logger.info("Starting full job agent pipeline")
        self.logger.info("=" * 50)
        
        try:
            # Scrape jobs (skip validation if already done at CLI level)
            jobs = self.scrape_jobs(
                keywords=keywords,
                location=location,
                max_jobs_per_platform=max_jobs_per_platform,
                skip_input_validation=skip_input_validation
            )
            
            if not jobs:
                self.logger.warning("No jobs scraped, stopping pipeline")
                return []
            
            # Process jobs
            processed_jobs = self.process_jobs(filter_config=filter_config)
            
            if not processed_jobs:
                self.logger.warning("No jobs after processing, stopping pipeline")
                return []
            
            # Export if requested
            if output_file:
                self.export_jobs(output_file)
            
            self.run_statistics['end_time'] = datetime.now()
            self._log_final_statistics()
            
            return processed_jobs
            
        except Exception as e:
            self.logger.error(f"Error in pipeline: {e}")
            raise
    
    def export_jobs(self, output_file: str, jobs: Optional[List[Job]] = None) -> int:
        """
        Export jobs to CSV file
        
        Args:
            output_file: Path to output CSV file
            jobs: Jobs to export (default: processed jobs)
        
        Returns:
            Number of jobs exported
        """
        jobs_to_export = jobs or self.processed_jobs
        
        if not jobs_to_export:
            self.logger.warning("No jobs to export")
            return 0
        
        self.logger.info(f"Exporting {len(jobs_to_export)} jobs to {output_file}")
        
        written_count = write_jobs_to_csv(jobs_to_export, output_file, mode='w')
        
        self.run_statistics['total_jobs_exported'] = written_count
        
        self.logger.info(f"Export complete: {written_count} jobs written to {output_file}")
        
        return written_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the job agent run
        
        Returns:
            Dictionary with run statistics
        """
        stats = self.run_statistics.copy()
        
        # Add duration if available
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['duration_seconds'] = duration
            stats['duration_minutes'] = duration / 60
        
        return stats
    
    def _log_final_statistics(self):
        """Log final statistics summary"""
        self.logger.info("=" * 50)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 50)
        
        stats = self.get_statistics()
        
        self.logger.info(f"Total jobs scraped: {stats['total_jobs_scraped']}")
        self.logger.info(f"Total jobs processed: {stats['total_jobs_processed']}")
        self.logger.info(f"Total jobs exported: {stats['total_jobs_exported']}")
        
        if 'duration_seconds' in stats:
            self.logger.info(f"Total duration: {stats['duration_seconds']:.2f}s")
        
        # Platform statistics
        self.logger.info("\nPlatform Statistics:")
        for platform, platform_stats in stats['platform_stats'].items():
            self.logger.info(f"  {platform}:")
            self.logger.info(f"    Jobs scraped: {platform_stats.get('jobs_scraped', 0)}")
            self.logger.info(f"    Errors: {platform_stats.get('errors_encountered', 0)}")
            if platform_stats.get('duration_seconds'):
                self.logger.info(f"    Duration: {platform_stats['duration_seconds']:.2f}s")
        
        self.logger.info("=" * 50)
    
    def reset(self):
        """Reset the job agent state"""
        self.all_jobs = []
        self.processed_jobs = []
        self.run_statistics = {
            'start_time': None,
            'end_time': None,
            'total_jobs_scraped': 0,
            'total_jobs_processed': 0,
            'total_jobs_exported': 0,
            'platform_stats': {}
        }
        
        # Reset scraper statistics
        for scraper in self.scrapers.values():
            scraper.reset_statistics()
        
        # Reset processor statistics
        self.deduplicator.reset_statistics()
        self.filter.reset_statistics()
        self.validator.reset_statistics()
        
        self.logger.info("Job agent state reset")