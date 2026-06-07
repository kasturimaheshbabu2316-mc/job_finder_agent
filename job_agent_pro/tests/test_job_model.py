"""
Unit tests for Job data model
"""

import pytest
from datetime import datetime
from src.models.job import Job, JobType, Platform


def test_job_creation():
    """Test basic job creation"""
    job = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Develop software",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI
    )
    
    assert job.job_title == "Software Engineer"
    assert job.company_name == "Tech Corp"
    assert job.platform_source == Platform.NAUKRI
    assert job.scraped_at is not None


def test_job_validation():
    """Test job field validation"""
    with pytest.raises(ValueError):
        Job(
            job_title="",  # Empty required field
            company_name="Tech Corp",
            job_description="Develop software",
            location="Remote",
            job_url="https://example.com/job/1",
            platform_source=Platform.NAUKRI
        )


def test_job_to_dict():
    """Test job to dictionary conversion"""
    job = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Develop software",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI,
        job_type=JobType.FULL_TIME
    )
    
    job_dict = job.to_dict()
    
    assert job_dict['job_title'] == "Software Engineer"
    assert job_dict['platform_source'] == "naukri"
    assert job_dict['job_type'] == "Full-time"


def test_job_from_dict():
    """Test job creation from dictionary"""
    job_dict = {
        'job_title': 'Data Scientist',
        'company_name': 'Data Corp',
        'job_description': 'Analyze data',
        'location': 'Bengaluru',
        'job_url': 'https://example.com/job/2',
        'platform_source': 'remoteok',
        'job_type': 'contract'
    }
    
    job = Job.from_dict(job_dict)
    
    assert job.job_title == "Data Scientist"
    assert job.platform_source == Platform.REMOTEOK
    assert job.job_type == JobType.CONTRACT


def test_job_equality():
    """Test job equality for deduplication"""
    job1 = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Develop software",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI
    )
    
    job2 = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Different description",
        location="Different Location",
        job_url="https://example.com/job/1",
        platform_source=Platform.REMOTEOK
    )
    
    # Should be equal because same URL, title, company
    assert job1 == job2


def test_job_hash():
    """Test job hashing for set operations"""
    job1 = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Develop software",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI
    )
    
    job2 = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Different description",
        location="Different Location",
        job_url="https://example.com/job/1",
        platform_source=Platform.REMOTEOK
    )
    
    # Should have same hash
    assert hash(job1) == hash(job2)
    
    # Should work in sets
    job_set = {job1, job2}
    assert len(job_set) == 1  # Only one unique job


def test_job_csv_conversion():
    """Test job to CSV row conversion"""
    job = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Develop software applications",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI,
        skills=["Python", "React"],
        salary_range="$80,000 - $120,000"
    )
    
    csv_row = job.to_csv_row()
    
    assert csv_row['Job Title'] == "Software Engineer"
    assert csv_row['Company Name'] == "Tech Corp"
    assert csv_row['Platform'] == "naukri"
    assert csv_row['Skills'] == "Python, React"
    assert csv_row['Salary Range'] == "$80,000 - $120,000"


def test_job_type_normalization():
    """Test automatic job type normalization"""
    job = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="contract position for software development",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI,
        job_type="contract"
    )
    
    # Should normalize to enum
    assert job.job_type == JobType.CONTRACT


def test_optional_fields():
    """Test job with optional fields"""
    job = Job(
        job_title="Software Engineer",
        company_name="Tech Corp",
        job_description="Develop software",
        location="Remote",
        job_url="https://example.com/job/1",
        platform_source=Platform.NAUKRI,
        salary_range=None,
        job_type=None,
        posted_date=None
    )
    
    assert job.salary_range is None
    assert job.job_type is None
    assert job.posted_date is None