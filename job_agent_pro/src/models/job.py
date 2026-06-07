"""
Job data model with standardized fields
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class JobType(Enum):
    """Enumeration for job types"""
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"
    FREELANCE = "Freelance"
    REMOTE = "Remote"
    HYBRID = "Hybrid"


class Platform(Enum):
    """Enumeration for job platforms"""
    NAUKRI = "naukri"
    REMOTEOK = "remoteok"


@dataclass
class Job:
    """
    Standardized job data model
    
    Attributes:
        job_title: Title of the job position
        company_name: Name of the company offering the job
        job_description: Detailed description of the job
        location: Geographic location of the job
        salary_range: Salary range for the position
        job_type: Type of employment (full-time, part-time, etc.)
        posted_date: Date when the job was posted
        job_url: URL to the original job posting
        platform_source: Platform where the job was found
        raw_data: Original raw data from the platform
        scraped_at: Timestamp when the job was scraped
    """
    
    # Required fields
    job_title: str
    company_name: str
    job_description: str
    location: str
    job_url: str
    platform_source: Platform
    
    # Optional fields with defaults
    salary_range: Optional[str] = None
    job_type: Optional[JobType] = None
    posted_date: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    # Additional metadata
    skills: Optional[list[str]] = None
    experience_level: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    
    def __post_init__(self):
        """Validate job data after initialization"""
        self._validate_required_fields()
        self._normalize_job_type()
        
    def _validate_required_fields(self):
        """Validate that all required fields are present and non-empty"""
        required_fields = {
            'job_title': self.job_title,
            'company_name': self.company_name,
            'job_description': self.job_description,
            'location': self.location,
            'job_url': self.job_url,
        }
        
        missing_fields = [
            field_name for field_name, field_value in required_fields.items()
            if not field_value or (isinstance(field_value, str) and not field_value.strip())
        ]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def _normalize_job_type(self):
        """Normalize job type to enum if provided as string"""
        if self.job_type and isinstance(self.job_type, str):
            try:
                # Try to match string to enum
                self.job_type = JobType(self.job_type.lower())
            except ValueError:
                # If no exact match, try to find partial match
                for job_type in JobType:
                    if job_type.value.lower() in self.job_type.lower():
                        self.job_type = job_type
                        break
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            'job_title': self.job_title,
            'company_name': self.company_name,
            'job_description': self.job_description,
            'location': self.location,
            'salary_range': self.salary_range,
            'job_type': self.job_type.value if self.job_type else None,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'job_url': self.job_url,
            'platform_source': self.platform_source.value,
            'skills': self.skills,
            'experience_level': self.experience_level,
            'industry': self.industry,
            'company_size': self.company_size,
            'scraped_at': self.scraped_at.isoformat(),
        }
    
    def to_csv_row(self) -> Dict[str, str]:
        """Convert job to CSV-compatible dictionary with string values"""
        return {
            'Job Title': self.job_title,
            'Company Name': self.company_name,
            'Job Description': self.job_description,
            'Location': self.location,
            'Salary Range': self.salary_range or '',
            'Job Type': self.job_type.value if self.job_type else '',
            'Posted Date': self.posted_date.strftime('%Y-%m-%d') if self.posted_date else '',
            'Job URL': self.job_url,
            'Platform': self.platform_source.value,
            'Skills': ', '.join(self.skills) if self.skills else '',
            'Experience Level': self.experience_level or '',
            'Industry': self.industry or '',
            'Company Size': self.company_size or '',
            'Scraped At': self.scraped_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job instance from dictionary"""
        # Handle platform source
        platform = Platform(data.get('platform_source', 'unknown'))
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                platform = Platform.NAUKRI  # Default
        
        # Handle job type
        job_type = None
        if data.get('job_type'):
            try:
                job_type = JobType(data['job_type'].lower())
            except ValueError:
                job_type = data['job_type']
        
        # Handle posted date
        posted_date = None
        if data.get('posted_date'):
            if isinstance(data['posted_date'], str):
                try:
                    posted_date = datetime.fromisoformat(data['posted_date'])
                except ValueError:
                    pass
            elif isinstance(data['posted_date'], datetime):
                posted_date = data['posted_date']
        
        return cls(
            job_title=data.get('job_title', ''),
            company_name=data.get('company_name', ''),
            job_description=data.get('job_description', ''),
            location=data.get('location', ''),
            salary_range=data.get('salary_range'),
            job_type=job_type,
            posted_date=posted_date,
            job_url=data.get('job_url', ''),
            platform_source=platform,
            skills=data.get('skills'),
            experience_level=data.get('experience_level'),
            industry=data.get('industry'),
            company_size=data.get('company_size'),
            raw_data=data.get('raw_data'),
        )
    
    def __hash__(self) -> int:
        """Generate hash for deduplication"""
        return hash((self.job_url, self.job_title, self.company_name))
    
    def __eq__(self, other) -> bool:
        """Check equality for deduplication"""
        if not isinstance(other, Job):
            return False
        return (
            self.job_url == other.job_url and
            self.job_title == other.job_title and
            self.company_name == other.company_name
        )
