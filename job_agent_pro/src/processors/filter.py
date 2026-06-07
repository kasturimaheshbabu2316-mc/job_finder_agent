"""
Job filtering system
"""

from typing import List, Optional, Callable
from datetime import datetime, timedelta
from ..models.job import Job, JobType, Platform
from ..utils.logger import get_logger


class JobFilter:
    """
    Filters job listings based on various criteria
    """
    
    def __init__(self):
        self.logger = get_logger("filter")
        
        # Statistics
        self.original_count = 0
        self.filtered_count = 0
    
    def filter_jobs(self, 
                   jobs: List[Job],
                   job_titles: Optional[List[str]] = None,
                   locations: Optional[List[str]] = None,
                   companies: Optional[List[str]] = None,
                   job_types: Optional[List[JobType]] = None,
                   platforms: Optional[List[Platform]] = None,
                   skills: Optional[List[str]] = None,
                   posted_after: Optional[datetime] = None,
                   posted_before: Optional[datetime] = None,
                   salary_min: Optional[str] = None,
                   custom_filter: Optional[Callable[[Job], bool]] = None) -> List[Job]:
        """
        Filter jobs based on multiple criteria
        
        Args:
            jobs: List of Job objects to filter
            job_titles: List of job titles to include (partial match)
            locations: List of locations to include (exact or partial match)
            companies: List of companies to include (partial match)
            job_types: List of job types to include
            platforms: List of platforms to include
            skills: List of required skills (job must have at least one)
            posted_after: Only include jobs posted after this date
            posted_before: Only include jobs posted before this date
            salary_min: Minimum salary (string comparison)
            custom_filter: Custom filter function
        
        Returns:
            Filtered list of Job objects
        """
        if not jobs:
            return []
        
        self.original_count = len(jobs)
        self.logger.info(f"Starting filtering with {self.original_count} jobs")
        
        filtered_jobs = jobs.copy()
        
        # Apply each filter
        if job_titles:
            filtered_jobs = self._filter_by_job_titles(filtered_jobs, job_titles)
        
        if locations:
            filtered_jobs = self._filter_by_locations(filtered_jobs, locations)
        
        if companies:
            filtered_jobs = self._filter_by_companies(filtered_jobs, companies)
        
        if job_types:
            filtered_jobs = self._filter_by_job_types(filtered_jobs, job_types)
        
        if platforms:
            filtered_jobs = self._filter_by_platforms(filtered_jobs, platforms)
        
        if skills:
            filtered_jobs = self._filter_by_skills(filtered_jobs, skills)
        
        if posted_after:
            filtered_jobs = self._filter_by_posted_date(filtered_jobs, after=posted_after)
        
        if posted_before:
            filtered_jobs = self._filter_by_posted_date(filtered_jobs, before=posted_before)
        
        if salary_min:
            filtered_jobs = self._filter_by_salary(filtered_jobs, min_salary=salary_min)
        
        if custom_filter:
            filtered_jobs = [job for job in filtered_jobs if custom_filter(job)]
        
        self.filtered_count = len(filtered_jobs)
        
        self.logger.info(f"Filtering complete: {self.filtered_count} jobs remaining ({self.original_count - self.filtered_count} filtered out)")
        
        return filtered_jobs
    
    def _filter_by_job_titles(self, jobs: List[Job], job_titles: List[str]) -> List[Job]:
        """Filter jobs by job titles (partial match)"""
        job_titles_lower = [title.lower() for title in job_titles]
        return [job for job in jobs if any(title in job.job_title.lower() for title in job_titles_lower)]
    
    def _filter_by_locations(self, jobs: List[Job], locations: List[str]) -> List[Job]:
        """Filter jobs by locations (exact or partial match)"""
        locations_lower = [loc.lower() for loc in locations]
        return [job for job in jobs if any(loc in job.location.lower() for loc in locations_lower)]
    
    def _filter_by_companies(self, jobs: List[Job], companies: List[str]) -> List[Job]:
        """Filter jobs by companies (partial match)"""
        companies_lower = [comp.lower() for comp in companies]
        return [job for job in jobs if any(comp in job.company_name.lower() for comp in companies_lower)]
    
    def _filter_by_job_types(self, jobs: List[Job], job_types: List[JobType]) -> List[Job]:
        """Filter jobs by job types"""
        return [job for job in jobs if job.job_type in job_types]
    
    def _filter_by_platforms(self, jobs: List[Job], platforms: List[Platform]) -> List[Job]:
        """Filter jobs by platforms"""
        return [job for job in jobs if job.platform_source in platforms]
    
    def _filter_by_skills(self, jobs: List[Job], required_skills: List[str]) -> List[Job]:
        """Filter jobs by required skills (must have at least one)"""
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        filtered_jobs = []
        for job in jobs:
            if job.skills:
                job_skills_lower = [skill.lower() for skill in job.skills]
                if any(skill in job_skills_lower for skill in required_skills_lower):
                    filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _filter_by_posted_date(self, jobs: List[Job], after: Optional[datetime] = None, before: Optional[datetime] = None) -> List[Job]:
        """Filter jobs by posted date range"""
        filtered_jobs = []
        
        for job in jobs:
            if not job.posted_date:
                continue
            
            if after and job.posted_date < after:
                continue
            
            if before and job.posted_date > before:
                continue
            
            filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _filter_by_salary(self, jobs: List[Job], min_salary: str) -> List[Job]:
        """Filter jobs by minimum salary (string comparison)"""
        # This is a simple string-based comparison
        # In production, you'd want to parse salary ranges more carefully
        return [job for job in jobs if job.salary_range and min_salary.lower() in job.salary_range.lower()]
    
    def filter_recent_jobs(self, jobs: List[Job], days: int = 30) -> List[Job]:
        """
        Filter jobs posted within the last N days
        
        Args:
            jobs: List of Job objects
            days: Number of days to look back
        
        Returns:
            List of recent Job objects
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        return self._filter_by_posted_date(jobs, after=cutoff_date)
    
    def filter_by_keywords(self, jobs: List[Job], keywords: List[str], search_in: List[str] = None) -> List[Job]:
        """
        Filter jobs by keywords in specific fields
        
        Args:
            jobs: List of Job objects
            keywords: List of keywords to search for
            search_in: Fields to search in (default: ['job_title', 'job_description'])
        
        Returns:
            Filtered list of Job objects
        """
        if search_in is None:
            search_in = ['job_title', 'job_description']
        
        keywords_lower = [keyword.lower() for keyword in keywords]
        filtered_jobs = []
        
        for job in jobs:
            job_matches = False
            
            for field in search_in:
                field_value = getattr(job, field, '')
                if field_value:
                    field_value_lower = field_value.lower()
                    if any(keyword in field_value_lower for keyword in keywords_lower):
                        job_matches = True
                        break
            
            if job_matches:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get filtering statistics
        
        Returns:
            Dictionary with filtering statistics
        """
        return {
            'original_count': self.original_count,
            'filtered_count': self.filtered_count,
            'removed_count': self.original_count - self.filtered_count,
            'filter_rate': (self.original_count - self.filtered_count) / self.original_count if self.original_count > 0 else 0,
        }
    
    def reset_statistics(self):
        """Reset filtering statistics"""
        self.original_count = 0
        self.filtered_count = 0


class JobSorter:
    """
    Sorts job listings based on various criteria
    """
    
    @staticmethod
    def sort_by_posted_date(jobs: List[Job], reverse: bool = True) -> List[Job]:
        """Sort jobs by posted date"""
        jobs_with_dates = [job for job in jobs if job.posted_date]
        jobs_without_dates = [job for job in jobs if not job.posted_date]
        
        sorted_jobs = sorted(jobs_with_dates, key=lambda j: j.posted_date, reverse=reverse)
        sorted_jobs.extend(jobs_without_dates)
        
        return sorted_jobs
    
    @staticmethod
    def sort_by_company(jobs: List[Job], reverse: bool = False) -> List[Job]:
        """Sort jobs by company name"""
        return sorted(jobs, key=lambda j: j.company_name.lower(), reverse=reverse)
    
    @staticmethod
    def sort_by_title(jobs: List[Job], reverse: bool = False) -> List[Job]:
        """Sort jobs by job title"""
        return sorted(jobs, key=lambda j: j.job_title.lower(), reverse=reverse)
    
    @staticmethod
    def sort_by_location(jobs: List[Job], reverse: bool = False) -> List[Job]:
        """Sort jobs by location"""
        return sorted(jobs, key=lambda j: j.location.lower(), reverse=reverse)
    
    @staticmethod
    def sort_by_relevance(jobs: List[Job], keywords: List[str]) -> List[Job]:
        """
        Sort jobs by relevance to keywords
        
        Args:
            jobs: List of Job objects
            keywords: List of keywords to match against
        
        Returns:
            List of jobs sorted by relevance
        """
        keywords_lower = [keyword.lower() for keyword in keywords]
        
        def relevance_score(job: Job) -> int:
            score = 0
            searchable_text = f"{job.job_title} {job.company_name} {job.job_description}".lower()
            
            for keyword in keywords_lower:
                if keyword in searchable_text:
                    score += 1
                if keyword in job.job_title.lower():
                    score += 2  # Extra weight for title matches
            
            return score
        
        return sorted(jobs, key=relevance_score, reverse=True)