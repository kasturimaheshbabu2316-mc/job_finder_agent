"""
Data normalization pipeline for job data
"""

from typing import List, Dict, Any, Optional
from ..models.job import Job
from ..utils.text_utils import clean_text, normalize_location, normalize_job_title, extract_salary_range
from ..utils.date_utils import normalize_posted_date
from ..utils.logger import get_logger


class JobNormalizer:
    """
    Normalizes job data from different platforms to ensure consistency
    """
    
    def __init__(self):
        self.logger = get_logger("normalizer")
        
        # Location mappings for standardization
        self.location_mappings = {
            'nyc': 'New York',
            'new york city': 'New York',
            'san francisco bay area': 'San Francisco',
            'sf': 'San Francisco',
            'bangalore': 'Bengaluru',
            'bengaluru': 'Bengaluru',
            'remote - worldwide': 'Remote',
            'remote - us': 'Remote',
            'work from home': 'Remote',
            'wfh': 'Remote',
        }
        
        # Job title mappings for standardization
        self.job_title_mappings = {
            'sr.': 'Senior',
            'sr': 'Senior',
            'jr.': 'Junior',
            'jr': 'Junior',
            'mgr.': 'Manager',
            'mgr': 'Manager',
            'dev': 'Developer',
            'eng': 'Engineer',
            'swe': 'Software Engineer',
            'data scientist': 'Data Scientist',
            'ml engineer': 'Machine Learning Engineer',
            'backend engineer': 'Backend Developer',
            'frontend engineer': 'Frontend Developer',
            'full stack engineer': 'Full Stack Developer',
        }
    
    def normalize_job(self, job: Job) -> Job:
        """
        Normalize a single job object
        
        Args:
            job: Job object to normalize
        
        Returns:
            Normalized Job object
        """
        try:
            # Normalize job title
            job.job_title = self._normalize_job_title(job.job_title)
            
            # Normalize company name
            job.company_name = self._normalize_company_name(job.company_name)
            
            # Normalize location
            job.location = self._normalize_location(job.location)
            
            # Normalize salary range
            if job.salary_range:
                job.salary_range = self._normalize_salary_range(job.salary_range)
            
            # Normalize posted date
            job.posted_date = normalize_posted_date(job.posted_date)
            
            # Normalize skills
            if job.skills:
                job.skills = self._normalize_skills(job.skills)
            
            # Normalize experience level
            if job.experience_level:
                job.experience_level = self._normalize_experience_level(job.experience_level)
            
            # Normalize industry
            if job.industry:
                job.industry = self._normalize_industry(job.industry)
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error normalizing job: {e}")
            return job
    
    def normalize_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Normalize a list of job objects
        
        Args:
            jobs: List of Job objects to normalize
        
        Returns:
            List of normalized Job objects
        """
        normalized_jobs = []
        
        for job in jobs:
            normalized_job = self.normalize_job(job)
            normalized_jobs.append(normalized_job)
        
        self.logger.info(f"Normalized {len(normalized_jobs)} jobs")
        return normalized_jobs
    
    def _normalize_job_title(self, title: str) -> str:
        """
        Normalize job title to standard format
        
        Args:
            title: Job title string
        
        Returns:
            Normalized job title
        """
        if not title:
            return ""
        
        # Use the text utility function
        return normalize_job_title(title)
    
    def _normalize_company_name(self, company_name: str) -> str:
        """
        Normalize company name to standard format
        
        Args:
            company_name: Company name string
        
        Returns:
            Normalized company name
        """
        if not company_name:
            return ""
        
        # Clean and trim
        company_name = clean_text(company_name)
        
        # Remove common suffixes/prefixes
        company_name = company_name.replace('Inc.', '').replace('Inc', '')
        company_name = company_name.replace('Ltd.', '').replace('Ltd', '')
        company_name = company_name.replace('LLC', '').replace('LLC.', '')
        company_name = company_name.replace('Pvt.', '').replace('Pvt', '')
        company_name = company_name.replace('Private Limited', '').replace(' Pvt Ltd', '')
        
        # Clean up extra spaces
        company_name = ' '.join(company_name.split())
        
        return company_name.strip()
    
    def _normalize_location(self, location: str) -> str:
        """
        Normalize location to standard format
        
        Args:
            location: Location string
        
        Returns:
            Normalized location
        """
        if not location:
            return ""
        
        # Use the text utility function
        return normalize_location(location)
    
    def _normalize_salary_range(self, salary: str) -> str:
        """
        Normalize salary range to standard format
        
        Args:
            salary: Salary string
        
        Returns:
            Normalized salary range
        """
        if not salary:
            return ""
        
        # Use the text utility function
        salary_range = extract_salary_range(salary)
        
        if salary_range:
            return salary_range
        
        # If no pattern match, return original
        return salary.strip()
    
    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """
        Normalize skills list
        
        Args:
            skills: List of skill strings
        
        Returns:
            Normalized list of skills
        """
        if not skills:
            return []
        
        normalized_skills = []
        
        for skill in skills:
            if skill:
                # Clean skill name
                skill = clean_text(skill)
                # Capitalize properly
                skill = skill.title()
                if skill:
                    normalized_skills.append(skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in normalized_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)
        
        return unique_skills
    
    def _normalize_experience_level(self, experience: str) -> str:
        """
        Normalize experience level to standard format
        
        Args:
            experience: Experience level string
        
        Returns:
            Normalized experience level
        """
        if not experience:
            return ""
        
        experience = experience.lower().strip()
        
        # Common experience level mappings
        exp_mappings = {
            'entry level': 'Entry Level',
            'junior': 'Junior',
            'mid level': 'Mid Level',
            'mid-level': 'Mid Level',
            'mid': 'Mid Level',
            'senior': 'Senior',
            'lead': 'Lead',
            'principal': 'Principal',
            'director': 'Director',
            'executive': 'Executive',
            'intern': 'Intern',
            'internship': 'Internship',
        }
        
        for key, value in exp_mappings.items():
            if key in experience:
                return value
        
        # If no match, capitalize and return
        return experience.title()
    
    def _normalize_industry(self, industry: str) -> str:
        """
        Normalize industry to standard format
        
        Args:
            industry: Industry string
        
        Returns:
            Normalized industry
        """
        if not industry:
            return ""
        
        industry = clean_text(industry)
        
        # Capitalize properly
        return industry.title()
    
    def get_normalization_stats(self, before_jobs: List[Job], after_jobs: List[Job]) -> Dict[str, Any]:
        """
        Get statistics about normalization process
        
        Args:
            before_jobs: Jobs before normalization
            after_jobs: Jobs after normalization
        
        Returns:
            Dictionary with normalization statistics
        """
        return {
            'total_jobs': len(before_jobs),
            'normalized_jobs': len(after_jobs),
            'title_changes': self._count_field_changes(before_jobs, after_jobs, 'job_title'),
            'company_changes': self._count_field_changes(before_jobs, after_jobs, 'company_name'),
            'location_changes': self._count_field_changes(before_jobs, after_jobs, 'location'),
        }
    
    def _count_field_changes(self, before: List[Job], after: List[Job], field: str) -> int:
        """Count how many jobs had a specific field changed during normalization"""
        changes = 0
        for before_job, after_job in zip(before, after):
            if getattr(before_job, field) != getattr(after_job, field):
                changes += 1
        return changes