"""
Data validation for job listings
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.job import Job
from ..utils.logger import get_logger


class JobValidator:
    """
    Validates job data quality and completeness
    """
    
    def __init__(self):
        self.logger = get_logger("validator")
        
        # Validation statistics
        self.total_validated = 0
        self.total_passed = 0
        self.total_failed = 0
    
    def validate_job(self, job: Job, strict: bool = False) -> tuple[bool, List[str]]:
        """
        Validate a single job object
        
        Args:
            job: Job object to validate
            strict: If True, enforce stricter validation rules
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate required fields
        if not job.job_title or not job.job_title.strip():
            errors.append("Job title is required")
        
        if not job.company_name or not job.company_name.strip():
            errors.append("Company name is required")
        
        if not job.job_description or not job.job_description.strip():
            errors.append("Job description is required")
        
        if not job.location or not job.location.strip():
            errors.append("Location is required")
        
        if not job.job_url or not job.job_url.strip():
            errors.append("Job URL is required")
        
        # Validate URL format
        if job.job_url:
            if not job.job_url.startswith(('http://', 'https://')):
                errors.append("Job URL must start with http:// or https://")
        
        # Strict validation
        if strict:
            if not job.posted_date:
                errors.append("Posted date is required in strict mode")
            
            if not job.job_type:
                errors.append("Job type is required in strict mode")
            
            if job.job_description and len(job.job_description) < 50:
                errors.append("Job description too short in strict mode (minimum 50 characters)")
        
        # Validate data types
        if job.posted_date and not isinstance(job.posted_date, datetime):
            errors.append("Posted date must be a datetime object")
        
        # Validate logical consistency
        if job.posted_date and job.posted_date > datetime.now():
            errors.append("Posted date cannot be in the future")
        
        return len(errors) == 0, errors
    
    def validate_jobs(self, jobs: List[Job], strict: bool = False) -> Dict[str, Any]:
        """
        Validate a list of job objects
        
        Args:
            jobs: List of Job objects to validate
            strict: If True, enforce stricter validation rules
        
        Returns:
            Dictionary with validation results and statistics
        """
        self.total_validated = len(jobs)
        self.total_passed = 0
        self.total_failed = 0
        
        validation_results = {
            'valid_jobs': [],
            'invalid_jobs': [],
            'errors': {},
            'statistics': {}
        }
        
        for job in jobs:
            is_valid, errors = self.validate_job(job, strict)
            
            if is_valid:
                validation_results['valid_jobs'].append(job)
                self.total_passed += 1
            else:
                validation_results['invalid_jobs'].append(job)
                validation_results['errors'][job.job_url] = errors
                self.total_failed += 1
        
        # Calculate statistics
        validation_results['statistics'] = self.get_statistics()
        
        self.logger.info(f"Validation complete: {self.total_passed}/{self.total_validated} jobs passed ({(self.total_passed/self.total_validated)*100:.1f}%)")
        
        return validation_results
    
    def get_valid_jobs(self, jobs: List[Job], strict: bool = False) -> List[Job]:
        """
        Get only valid jobs from a list
        
        Args:
            jobs: List of Job objects to validate
            strict: If True, enforce stricter validation rules
        
        Returns:
            List of valid Job objects
        """
        validation_results = self.validate_jobs(jobs, strict)
        return validation_results['valid_jobs']
    
    def get_invalid_jobs(self, jobs: List[Job], strict: bool = False) -> List[tuple[Job, List[str]]]:
        """
        Get only invalid jobs with their errors from a list
        
        Args:
            jobs: List of Job objects to validate
            strict: If True, enforce stricter validation rules
        
        Returns:
            List of (invalid_job, errors) tuples
        """
        validation_results = self.validate_jobs(jobs, strict)
        invalid_jobs = []
        
        for job in validation_results['invalid_jobs']:
            errors = validation_results['errors'].get(job.job_url, [])
            invalid_jobs.append((job, errors))
        
        return invalid_jobs
    
    def validate_field_completeness(self, jobs: List[Job]) -> Dict[str, Any]:
        """
        Validate field completeness across all jobs
        
        Args:
            jobs: List of Job objects to analyze
        
        Returns:
            Dictionary with field completeness statistics
        """
        if not jobs:
            return {}
        
        total_jobs = len(jobs)
        
        fields_to_check = {
            'job_title': lambda j: bool(j.job_title and j.job_title.strip()),
            'company_name': lambda j: bool(j.company_name and j.company_name.strip()),
            'job_description': lambda j: bool(j.job_description and j.job_description.strip()),
            'location': lambda j: bool(j.location and j.location.strip()),
            'job_url': lambda j: bool(j.job_url and j.job_url.strip()),
            'salary_range': lambda j: bool(j.salary_range and j.salary_range.strip()),
            'job_type': lambda j: bool(j.job_type),
            'posted_date': lambda j: bool(j.posted_date),
            'skills': lambda j: bool(j.skills and len(j.skills) > 0),
            'experience_level': lambda j: bool(j.experience_level and j.experience_level.strip()),
            'industry': lambda j: bool(j.industry and j.industry.strip()),
        }
        
        completeness_stats = {}
        
        for field_name, check_func in fields_to_check.items():
            filled_count = sum(1 for job in jobs if check_func(job))
            completeness_percent = (filled_count / total_jobs) * 100
            completeness_stats[field_name] = {
                'filled': filled_count,
                'missing': total_jobs - filled_count,
                'percentage': completeness_percent
            }
        
        return completeness_stats
    
    def validate_data_quality(self, jobs: List[Job]) -> Dict[str, Any]:
        """
        Validate overall data quality metrics
        
        Args:
            jobs: List of Job objects to analyze
        
        Returns:
            Dictionary with data quality metrics
        """
        if not jobs:
            return {'error': 'No jobs to analyze'}
        
        quality_metrics = {
            'total_jobs': len(jobs),
            'field_completeness': self.validate_field_completeness(jobs),
            'data_quality_score': 0.0
        }
        
        # Calculate overall data quality score
        completeness_stats = quality_metrics['field_completeness']
        avg_completeness = sum(stats['percentage'] for stats in completeness_stats.values()) / len(completeness_stats)
        
        # Required fields have higher weight
        required_fields = ['job_title', 'company_name', 'job_description', 'location', 'job_url']
        required_completeness = sum(completeness_stats[field]['percentage'] for field in required_fields) / len(required_fields)
        
        # Weighted score (70% required fields, 30% optional fields)
        quality_score = (required_completeness * 0.7) + (avg_completeness * 0.3)
        quality_metrics['data_quality_score'] = quality_score
        
        # Quality rating
        if quality_score >= 90:
            quality_metrics['quality_rating'] = 'Excellent'
        elif quality_score >= 75:
            quality_metrics['quality_rating'] = 'Good'
        elif quality_score >= 60:
            quality_metrics['quality_rating'] = 'Fair'
        else:
            quality_metrics['quality_rating'] = 'Poor'
        
        return quality_metrics
    
    def detect_data_anomalies(self, jobs: List[Job]) -> List[str]:
        """
        Detect potential data anomalies in job listings
        
        Args:
            jobs: List of Job objects to analyze
        
        Returns:
            List of anomaly descriptions
        """
        anomalies = []
        
        if not jobs:
            return anomalies
        
        # Check for unusual job titles
        title_lengths = [len(job.job_title) for job in jobs if job.job_title]
        avg_title_length = sum(title_lengths) / len(title_lengths) if title_lengths else 0
        
        for job in jobs:
            if job.job_title and len(job.job_title) > avg_title_length * 3:
                anomalies.append(f"Unusually long job title: {job.job_title[:50]}...")
            
            if job.job_title and len(job.job_title) < 3:
                anomalies.append(f"Suspiciously short job title: {job.job_title}")
        
        # Check for future dates
        for job in jobs:
            if job.posted_date and job.posted_date > datetime.now():
                anomalies.append(f"Future posted date: {job.posted_date} for {job.job_title}")
        
        # Check for very old dates
        cutoff_date = datetime.now() - timedelta(days=365)
        for job in jobs:
            if job.posted_date and job.posted_date < cutoff_date:
                anomalies.append(f"Old job posting (>1 year): {job.posted_date} for {job.job_title}")
        
        # Check for duplicate URLs
        urls = [job.job_url for job in jobs if job.job_url]
        if len(urls) != len(set(urls)):
            anomalies.append("Duplicate job URLs detected")
        
        return anomalies
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics
        
        Returns:
            Dictionary with validation statistics
        """
        return {
            'total_validated': self.total_validated,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'pass_rate': self.total_passed / self.total_validated if self.total_validated > 0 else 0,
        }
    
    def reset_statistics(self):
        """Reset validation statistics"""
        self.total_validated = 0
        self.total_passed = 0
        self.total_failed = 0