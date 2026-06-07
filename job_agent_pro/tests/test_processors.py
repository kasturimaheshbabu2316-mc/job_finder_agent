"""
Unit tests for data processors
"""

import pytest
from datetime import datetime
from src.models.job import Job, JobType, Platform
from src.processors.normalizer import JobNormalizer
from src.processors.deduplicator import JobDeduplicator
from src.processors.filter import JobFilter, JobSorter
from src.processors.validator import JobValidator


@pytest.fixture
def sample_jobs():
    """Create sample jobs for testing"""
    return [
        Job(
            job_title="Software Engineer",
            company_name="Tech Corp",
            job_description="Develop software",
            location="Remote",
            job_url="https://example.com/job/1",
            platform_source=Platform.NAUKRI,
            job_type=JobType.FULL_TIME
        ),
        Job(
            job_title="Data Scientist",
            company_name="Data Corp",
            job_description="Analyze data",
            location="Bengaluru",
            job_url="https://example.com/job/2",
            platform_source=Platform.REMOTEOK,
            job_type=JobType.CONTRACT
        ),
        Job(
            job_title="Software Engineer",  # Duplicate title/company
            company_name="Tech Corp",       # Duplicate company
            job_description="Different description",
            location="Different Location",
            job_url="https://example.com/job/3",  # Different URL
            platform_source=Platform.LINKEDIN,
        )
    ]


def test_normalizer_normalize_job(sample_jobs):
    """Test job normalization"""
    normalizer = JobNormalizer()
    
    job = sample_jobs[0]
    normalized_job = normalizer.normalize_job(job)
    
    assert normalized_job.job_title == job.job_title
    assert normalized_job.location == job.location


def test_normalizer_normalize_jobs(sample_jobs):
    """Test batch job normalization"""
    normalizer = JobNormalizer()
    
    normalized_jobs = normalizer.normalize_jobs(sample_jobs)
    
    assert len(normalized_jobs) == len(sample_jobs)


def test_deduplicator_url_based(sample_jobs):
    """Test URL-based deduplication"""
    deduplicator = JobDeduplicator()
    
    # All jobs have different URLs, so none should be removed
    deduplicated = deduplicator.deduplicate_jobs(sample_jobs, strategy='url_based')
    
    assert len(deduplicated) == len(sample_jobs)


def test_deduplicator_content_based(sample_jobs):
    """Test content-based deduplication"""
    deduplicator = JobDeduplicator()
    
    # Jobs 0 and 2 have same title and company, should be deduplicated
    deduplicated = deduplicator.deduplicate_jobs(sample_jobs, strategy='content_based')
    
    assert len(deduplicated) == 2  # Should remove one duplicate


def test_deduplicator_hybrid(sample_jobs):
    """Test hybrid deduplication"""
    deduplicator = JobDeduplicator()
    
    deduplicated = deduplicator.deduplicate_jobs(sample_jobs, strategy='hybrid')
    
    assert len(deduplicated) <= len(sample_jobs)


def test_deduplicator_statistics(sample_jobs):
    """Test deduplication statistics"""
    deduplicator = JobDeduplicator()
    
    deduplicator.deduplicate_jobs(sample_jobs, strategy='content_based')
    stats = deduplicator.get_statistics()
    
    assert stats['original_count'] == len(sample_jobs)
    assert stats['duplicates_removed'] >= 0
    assert stats['final_count'] <= stats['original_count']


def test_filter_by_job_titles(sample_jobs):
    """Test filtering by job titles"""
    job_filter = JobFilter()
    
    filtered = job_filter.filter_jobs(sample_jobs, job_titles=["Software Engineer"])
    
    assert len(filtered) >= 1
    for job in filtered:
        assert "software engineer" in job.job_title.lower()


def test_filter_by_locations(sample_jobs):
    """Test filtering by locations"""
    job_filter = JobFilter()
    
    filtered = job_filter.filter_jobs(sample_jobs, locations=["Remote"])
    
    assert len(filtered) >= 1
    for job in filtered:
        assert "remote" in job.location.lower()


def test_filter_by_platforms(sample_jobs):
    """Test filtering by platforms"""
    job_filter = JobFilter()
    
    filtered = job_filter.filter_jobs(sample_jobs, platforms=[Platform.NAUKRI])
    
    assert len(filtered) >= 1
    for job in filtered:
        assert job.platform_source == Platform.NAUKRI


def test_filter_by_skills(sample_jobs):
    """Test filtering by skills"""
    job_filter = JobFilter()
    
    # Add skills to a job
    sample_jobs[0].skills = ["Python", "React"]
    
    filtered = job_filter.filter_jobs(sample_jobs, skills=["Python"])
    
    assert len(filtered) >= 1


def test_filter_statistics(sample_jobs):
    """Test filter statistics"""
    job_filter = JobFilter()
    
    job_filter.filter_jobs(sample_jobs, job_titles=["Software Engineer"])
    stats = job_filter.get_statistics()
    
    assert stats['original_count'] == len(sample_jobs)
    assert stats['filtered_count'] <= stats['original_count']


def test_sorter_by_posted_date(sample_jobs):
    """Test sorting by posted date"""
    # Add posted dates
    now = datetime.now()
    sample_jobs[0].posted_date = now - timedelta(days=5)
    sample_jobs[1].posted_date = now - timedelta(days=2)
    sample_jobs[2].posted_date = now - timedelta(days=10)
    
    sorted_jobs = JobSorter.sort_by_posted_date(sample_jobs)
    
    # Should be sorted newest first
    assert sorted_jobs[0].posted_date >= sorted_jobs[1].posted_date


def test_sorter_by_company(sample_jobs):
    """Test sorting by company name"""
    sorted_jobs = JobSorter.sort_by_company(sample_jobs)
    
    # Check if sorted alphabetically
    for i in range(len(sorted_jobs) - 1):
        assert sorted_jobs[i].company_name.lower() <= sorted_jobs[i + 1].company_name.lower()


def test_validator_valid_job(sample_jobs):
    """Test validation of valid job"""
    validator = JobValidator()
    
    is_valid, errors = validator.validate_job(sample_jobs[0])
    
    assert is_valid is True
    assert len(errors) == 0


def test_validator_invalid_job():
    """Test validation of invalid job"""
    validator = JobValidator()
    
    invalid_job = Job(
        job_title="",  # Empty required field
        company_name="",  # Empty required field
        job_description="",  # Empty required field
        location="",  # Empty required field
        job_url="",  # Empty required field
        platform_source=Platform.NAUKRI
    )
    
    is_valid, errors = validator.validate_job(invalid_job)
    
    assert is_valid is False
    assert len(errors) > 0


def test_validator_validate_jobs(sample_jobs):
    """Test batch job validation"""
    validator = JobValidator()
    
    results = validator.validate_jobs(sample_jobs)
    
    assert 'valid_jobs' in results
    assert 'invalid_jobs' in results
    assert 'statistics' in results
    assert results['statistics']['total_validated'] == len(sample_jobs)


def test_validator_get_valid_jobs(sample_jobs):
    """Test getting only valid jobs"""
    validator = JobValidator()
    
    valid_jobs = validator.get_valid_jobs(sample_jobs)
    
    assert len(valid_jobs) <= len(sample_jobs)


def test_validator_field_completeness(sample_jobs):
    """Test field completeness analysis"""
    validator = JobValidator()
    
    completeness = validator.validate_field_completeness(sample_jobs)
    
    assert 'job_title' in completeness
    assert 'company_name' in completeness
    assert 'job_description' in completeness
    
    for field, stats in completeness.items():
        assert 'filled' in stats
        assert 'missing' in stats
        assert 'percentage' in stats


def test_validator_data_quality(sample_jobs):
    """Test data quality metrics"""
    validator = JobValidator()
    
    quality = validator.validate_data_quality(sample_jobs)
    
    assert 'total_jobs' in quality
    assert 'field_completeness' in quality
    assert 'data_quality_score' in quality
    assert 'quality_rating' in quality


def test_validator_statistics(sample_jobs):
    """Test validator statistics"""
    validator = JobValidator()
    
    validator.validate_jobs(sample_jobs)
    stats = validator.get_statistics()
    
    assert stats['total_validated'] == len(sample_jobs)
    assert stats['total_passed'] >= 0
    assert stats['total_failed'] >= 0