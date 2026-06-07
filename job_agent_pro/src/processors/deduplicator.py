"""
Deduplication system for job listings
"""

from typing import List, Dict, Any, Set
from difflib import SequenceMatcher
from ..models.job import Job
from ..utils.logger import get_logger


class JobDeduplicator:
    """
    Removes duplicate job listings using various strategies
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize deduplicator
        
        Args:
            similarity_threshold: Threshold for considering jobs as similar (0-1)
        """
        self.logger = get_logger("deduplicator")
        self.similarity_threshold = similarity_threshold
        
        # Statistics
        self.original_count = 0
        self.duplicates_removed = 0
        self.final_count = 0
    
    def deduplicate_jobs(self, jobs: List[Job], strategy: str = 'url_based') -> List[Job]:
        """
        Remove duplicate jobs from the list
        
        Args:
            jobs: List of Job objects to deduplicate
            strategy: Deduplication strategy ('url_based', 'content_based', 'hybrid')
        
        Returns:
            List of deduplicated Job objects
        """
        if not jobs:
            return []
        
        self.original_count = len(jobs)
        self.logger.info(f"Starting deduplication with {self.original_count} jobs using strategy: {strategy}")
        
        if strategy == 'url_based':
            deduplicated_jobs = self._url_based_deduplication(jobs)
        elif strategy == 'content_based':
            deduplicated_jobs = self._content_based_deduplication(jobs)
        elif strategy == 'hybrid':
            deduplicated_jobs = self._hybrid_deduplication(jobs)
        else:
            self.logger.warning(f"Unknown strategy: {strategy}, using url_based")
            deduplicated_jobs = self._url_based_deduplication(jobs)
        
        self.final_count = len(deduplicated_jobs)
        self.duplicates_removed = self.original_count - self.final_count
        
        self.logger.info(f"Deduplication complete: {self.duplicates_removed} duplicates removed, {self.final_count} jobs remain")
        
        return deduplicated_jobs
    
    def _url_based_deduplication(self, jobs: List[Job]) -> List[Job]:
        """
        Deduplicate based on job URLs
        
        Args:
            jobs: List of Job objects
        
        Returns:
            Deduplicated list of Job objects
        """
        seen_urls: Set[str] = set()
        unique_jobs = []
        
        for job in jobs:
            if job.job_url and job.job_url not in seen_urls:
                seen_urls.add(job.job_url)
                unique_jobs.append(job)
            else:
                self.logger.debug(f"Duplicate found by URL: {job.job_url}")
        
        return unique_jobs
    
    def _content_based_deduplication(self, jobs: List[Job]) -> List[Job]:
        """
        Deduplicate based on content similarity (title + company)
        
        Args:
            jobs: List of Job objects
        
        Returns:
            Deduplicated list of Job objects
        """
        unique_jobs = []
        seen_signatures: Set[str] = set()
        
        for job in jobs:
            # Create a signature based on title and company
            signature = self._create_job_signature(job)
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_jobs.append(job)
            else:
                self.logger.debug(f"Duplicate found by content: {job.job_title} at {job.company_name}")
        
        return unique_jobs
    
    def _hybrid_deduplication(self, jobs: List[Job]) -> List[Job]:
        """
        Hybrid approach: first URL-based, then content-based for remaining
        
        Args:
            jobs: List of Job objects
        
        Returns:
            Deduplicated list of Job objects
        """
        # First pass: URL-based deduplication
        url_deduplicated = self._url_based_deduplication(jobs)
        
        # Second pass: Content-based deduplication
        content_deduplicated = self._content_based_deduplication(url_deduplicated)
        
        return content_deduplicated
    
    def _create_job_signature(self, job: Job) -> str:
        """
        Create a unique signature for a job based on its content
        
        Args:
            job: Job object
        
        Returns:
            String signature
        """
        # Normalize title and company for comparison
        title = job.job_title.lower().strip()
        company = job.company_name.lower().strip()
        
        return f"{title}|{company}"
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher
        
        Args:
            str1: First string
            str2: Second string
        
        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def find_similar_jobs(self, job: Job, job_list: List[Job]) -> List[tuple[Job, float]]:
        """
        Find jobs similar to a given job
        
        Args:
            job: Job to compare against
            job_list: List of jobs to search through
        
        Returns:
            List of (similar_job, similarity_score) tuples above threshold
        """
        similar_jobs = []
        
        for other_job in job_list:
            if other_job.job_url == job.job_url:
                continue  # Skip exact URL matches
            
            # Calculate similarity based on title and company
            title_similarity = self._calculate_similarity(job.job_title, other_job.job_title)
            company_similarity = self._calculate_similarity(job.company_name, other_job.company_name)
            
            # Combined similarity (weighted average)
            combined_similarity = (title_similarity * 0.6) + (company_similarity * 0.4)
            
            if combined_similarity >= self.similarity_threshold:
                similar_jobs.append((other_job, combined_similarity))
        
        # Sort by similarity score (descending)
        similar_jobs.sort(key=lambda x: x[1], reverse=True)
        
        return similar_jobs
    
    def merge_duplicate_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Merge duplicate jobs by combining data from multiple sources
        
        Args:
            jobs: List of Job objects that may contain duplicates
        
        Returns:
            List of merged Job objects
        """
        # Group jobs by signature
        job_groups: Dict[str, List[Job]] = {}
        
        for job in jobs:
            signature = self._create_job_signature(job)
            if signature not in job_groups:
                job_groups[signature] = []
            job_groups[signature].append(job)
        
        merged_jobs = []
        
        for signature, group in job_groups.items():
            if len(group) == 1:
                # No duplicates
                merged_jobs.append(group[0])
            else:
                # Merge duplicates
                merged_job = self._merge_job_group(group)
                merged_jobs.append(merged_job)
                self.logger.debug(f"Merged {len(group)} duplicate jobs for: {signature}")
        
        return merged_jobs
    
    def _merge_job_group(self, jobs: List[Job]) -> Job:
        """
        Merge a group of duplicate jobs into a single job
        
        Args:
            jobs: List of duplicate Job objects
        
        Returns:
            Merged Job object
        """
        # Use the first job as base
        base_job = jobs[0]
        
        # Merge skills from all jobs
        all_skills = set()
        for job in jobs:
            if job.skills:
                all_skills.update(job.skills)
        
        # Merge other fields - keep the most complete data
        most_complete_job = max(jobs, key=lambda j: self._completeness_score(j))
        
        # Create merged job
        merged_job = Job(
            job_title=base_job.job_title,
            company_name=base_job.company_name,
            job_description=most_complete_job.job_description,
            location=most_complete_job.location,
            salary_range=most_complete_job.salary_range,
            job_type=most_complete_job.job_type,
            posted_date=most_complete_job.posted_date,
            job_url=base_job.job_url,
            platform_source=most_complete_job.platform_source,
            skills=list(all_skills),
            experience_level=most_complete_job.experience_level,
            industry=most_complete_job.industry,
            company_size=most_complete_job.company_size,
            raw_data=most_complete_job.raw_data,
        )
        
        return merged_job
    
    def _completeness_score(self, job: Job) -> int:
        """
        Calculate a completeness score for a job (higher = more complete)
        
        Args:
            job: Job object
        
        Returns:
            Completeness score
        """
        score = 0
        
        if job.job_title: score += 1
        if job.company_name: score += 1
        if job.job_description and len(job.job_description) > 50: score += 1
        if job.location: score += 1
        if job.salary_range: score += 1
        if job.job_type: score += 1
        if job.posted_date: score += 1
        if job.skills and len(job.skills) > 0: score += 1
        if job.experience_level: score += 1
        if job.industry: score += 1
        
        return score
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get deduplication statistics
        
        Returns:
            Dictionary with deduplication statistics
        """
        return {
            'original_count': self.original_count,
            'duplicates_removed': self.duplicates_removed,
            'final_count': self.final_count,
            'duplicate_rate': self.duplicates_removed / self.original_count if self.original_count > 0 else 0,
        }
    
    def reset_statistics(self):
        """Reset deduplication statistics"""
        self.original_count = 0
        self.duplicates_removed = 0
        self.final_count = 0