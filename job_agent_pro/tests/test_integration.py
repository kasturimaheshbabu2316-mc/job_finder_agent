"""
Integration tests for the complete job agent pipeline
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from src.job_agent import JobAgent
from src.models.job import Job, JobType, Platform
from src.processors import JobNormalizer, JobDeduplicator, JobFilter, JobValidator
from src.exporters import CSVExporter
from src.utils.csv_utils import read_jobs_from_csv, write_jobs_to_csv


@pytest.fixture
def sample_job_data():
    """Create sample job data for integration testing"""
    return [
        Job(
            job_title="Software Engineer",
            company_name="Tech Corp",
            job_description="Develop and maintain software applications using Python and React",
            location="Remote",
            job_url="https://example.com/job/1",
            platform_source=Platform.NAUKRI,
            job_type=JobType.FULL_TIME,
            skills=["Python", "React", "AWS"]
        ),
        Job(
            job_title="Data Scientist",
            company_name="Data Corp",
            job_description="Analyze large datasets and build machine learning models",
            location="Bengaluru",
            job_url="https://example.com/job/2",
            platform_source=Platform.REMOTEOK,
            job_type=JobType.CONTRACT,
            skills=["Python", "Machine Learning", "SQL"]
        ),
        Job(
            job_title="Software Engineer",  # Duplicate title/company
            company_name="Tech Corp",       # Duplicate company
            job_description="Different job description for similar role",
            location="Mumbai",
            job_url="https://example.com/job/3",
            platform_source=Platform.LINKEDIN,
            job_type=JobType.FULL_TIME,
            skills=["Java", "Spring"]
        ),
        Job(
            job_title="Frontend Developer",
            company_name="Web Solutions",
            job_description="Build user interfaces with modern JavaScript frameworks",
            location="Remote",
            job_url="https://example.com/job/4",
            platform_source=Platform.NAUKRI,
            job_type=JobType.REMOTE,
            skills=["JavaScript", "React", "CSS"]
        ),
        Job(
            job_title="Backend Developer",
            company_name="Server Systems",
            job_description="Design and implement server-side logic and APIs",
            location="Pune",
            job_url="https://example.com/job/5",
            platform_source=Platform.REMOTEOK,
            job_type=JobType.FULL_TIME,
            skills=["Python", "Django", "PostgreSQL"]
        )
    ]


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_complete_pipeline(sample_job_data, temp_output_dir):
    """Test the complete data processing pipeline"""
    # Initialize processors
    normalizer = JobNormalizer()
    deduplicator = JobDeduplicator()
    validator = JobValidator()
    
    # Step 1: Normalize
    normalized_jobs = normalizer.normalize_jobs(sample_job_data)
    assert len(normalized_jobs) == len(sample_job_data)
    
    # Step 2: Deduplicate
    deduplicated_jobs = deduplicator.deduplicate_jobs(normalized_jobs, strategy='hybrid')
    assert len(deduplicated_jobs) <= len(normalized_jobs)
    
    # Step 3: Validate
    validation_results = validator.validate_jobs(deduplicated_jobs)
    assert validation_results['statistics']['total_validated'] == len(deduplicated_jobs)
    
    # Step 4: Filter
    job_filter = JobFilter()
    filtered_jobs = job_filter.filter_jobs(
        validation_results['valid_jobs'],
        job_titles=["Software Engineer", "Data Scientist"]
    )
    assert len(filtered_jobs) <= len(validation_results['valid_jobs'])
    
    print(f"Pipeline complete: {len(sample_job_data)} -> {len(filtered_jobs)} jobs")


def test_csv_export_import_cycle(sample_job_data, temp_output_dir):
    """Test exporting and importing jobs from CSV"""
    # Export jobs
    output_file = os.path.join(temp_output_dir, "test_jobs.csv")
    written_count = write_jobs_to_csv(sample_job_data, output_file)
    
    assert written_count == len(sample_job_data)
    assert os.path.exists(output_file)
    
    # Import jobs
    imported_jobs = read_jobs_from_csv(output_file)
    
    assert len(imported_jobs) == len(sample_job_data)
    
    # Verify data integrity
    for original, imported in zip(sample_job_data, imported_jobs):
        assert original.job_title == imported.job_title
        assert original.company_name == imported.company_name
        assert original.location == imported.location


def test_advanced_csv_exporter(sample_job_data, temp_output_dir):
    """Test advanced CSV exporter features"""
    exporter = CSVExporter(output_dir=temp_output_dir)
    
    # Export with backup and metadata
    output_file = exporter.export_jobs(
        sample_job_data,
        filename="advanced_test.csv",
        create_backup=False,
        include_metadata=True
    )
    
    assert os.path.exists(output_file)
    
    # Check for metadata file
    metadata_file = output_file.replace('.csv', '.json')
    assert os.path.exists(metadata_file)
    
    # Get statistics
    stats = exporter.get_export_statistics("advanced_test.csv")
    assert stats['job_count'] == len(sample_job_data)
    assert 'metadata' in stats


def test_filter_and_export_workflow(sample_job_data, temp_output_dir):
    """Test filtering and then exporting results"""
    # Initialize components
    job_filter = JobFilter()
    exporter = CSVExporter(output_dir=temp_output_dir)
    
    # Filter jobs
    filtered_jobs = job_filter.filter_jobs(
        sample_job_data,
        locations=["Remote"],
        job_types=[JobType.FULL_TIME]
    )
    
    # Export filtered results
    output_file = exporter.export_jobs(filtered_jobs, filename="filtered_jobs.csv")
    
    assert os.path.exists(output_file)
    
    # Verify exported data
    imported_jobs = read_jobs_from_csv(output_file)
    assert len(imported_jobs) == len(filtered_jobs)


def test_job_agent_initialization():
    """Test JobAgent initialization"""
    agent = JobAgent()
    
    assert agent is not None
    assert agent.normalizer is not None
    assert agent.deduplicator is not None
    assert agent.filter is not None
    assert agent.validator is not None


def test_job_agent_statistics():
    """Test JobAgent statistics tracking"""
    agent = JobAgent()
    
    # Manually add some jobs to test statistics
    from datetime import datetime
    sample_jobs = [
        Job(
            job_title="Test Engineer",
            company_name="Test Corp",
            job_description="Test description",
            location="Remote",
            job_url="https://test.com/job/1",
            platform_source=Platform.NAUKRI
        )
    ]
    
    agent.all_jobs = sample_jobs
    agent.processed_jobs = sample_jobs
    
    stats = agent.get_statistics()
    
    assert 'total_jobs_scraped' in stats
    assert 'total_jobs_processed' in stats


def test_multi_platform_processing(sample_job_data):
    """Test processing jobs from multiple platforms"""
    # Filter by platforms
    job_filter = JobFilter()
    
    naukri_jobs = job_filter.filter_jobs(sample_job_data, platforms=[Platform.NAUKRI])
    remoteok_jobs = job_filter.filter_jobs(sample_job_data, platforms=[Platform.REMOTEOK])
    
    assert len(naukri_jobs) >= 0
    assert len(remoteok_jobs) >= 0
    assert len(naukri_jobs) + len(remoteok_jobs) <= len(sample_job_data)


def test_data_quality_assessment(sample_job_data):
    """Test data quality assessment across all jobs"""
    validator = JobValidator()
    
    quality_metrics = validator.validate_data_quality(sample_job_data)
    
    assert quality_metrics['total_jobs'] == len(sample_job_data)
    assert quality_metrics['data_quality_score'] >= 0
    assert quality_metrics['data_quality_score'] <= 100
    assert 'quality_rating' in quality_metrics


def test_export_by_platform(sample_job_data, temp_output_dir):
    """Test exporting jobs grouped by platform"""
    exporter = CSVExporter(output_dir=temp_output_dir)
    
    exported_files = exporter.export_by_platform(sample_job_data, create_separate_files=True)
    
    assert len(exported_files) > 0
    
    # Verify each exported file
    for file_path in exported_files:
        assert os.path.exists(file_path)
        imported_jobs = read_jobs_from_csv(file_path)
        assert len(imported_jobs) > 0


def test_complex_filtering_scenario(sample_job_data):
    """Test complex filtering with multiple criteria"""
    job_filter = JobFilter()
    
    # Complex filter: Remote full-time software engineering roles
    filtered_jobs = job_filter.filter_jobs(
        sample_job_data,
        job_titles=["Software Engineer"],
        locations=["Remote"],
        job_types=[JobType.FULL_TIME],
        platforms=[Platform.NAUKRI]
    )
    
    # Verify all criteria are met
    for job in filtered_jobs:
        assert "software engineer" in job.job_title.lower()
        assert "remote" in job.location.lower()
        assert job.job_type == JobType.FULL_TIME
        assert job.platform_source == Platform.NAUKRI


def test_error_handling_in_pipeline(sample_job_data, temp_output_dir):
    """Test error handling in the pipeline"""
    # Create a job with missing required fields
    invalid_job = Job(
        job_title="",  # Invalid: empty required field
        company_name="Test Corp",
        job_description="Test",
        location="Remote",
        job_url="https://test.com/job/invalid",
        platform_source=Platform.NAUKRI
    )
    
    # Add invalid job to the dataset
    jobs_with_invalid = sample_job_data + [invalid_job]
    
    # Run validation
    validator = JobValidator()
    validation_results = validator.validate_jobs(jobs_with_invalid)
    
    # Should separate valid and invalid jobs
    assert len(validation_results['valid_jobs']) < len(jobs_with_invalid)
    assert len(validation_results['invalid_jobs']) > 0
    
    # Invalid jobs should have errors
    invalid_jobs_with_errors = validator.get_invalid_jobs(jobs_with_invalid)
    assert len(invalid_jobs_with_errors) > 0
    assert len(invalid_jobs_with_errors[0][1]) > 0  # Should have errors


def test_sorting_functionality(sample_job_data):
    """Test sorting functionality"""
    from src.processors.filter import JobSorter
    from datetime import datetime, timedelta
    
    # Add posted dates for sorting
    now = datetime.now()
    sample_job_data[0].posted_date = now - timedelta(days=5)
    sample_job_data[1].posted_date = now - timedelta(days=2)
    sample_job_data[2].posted_date = now - timedelta(days=10)
    
    # Sort by posted date (newest first)
    sorted_jobs = JobSorter.sort_by_posted_date(sample_jobs, reverse=True)
    
    # Verify sorting order
    for i in range(len(sorted_jobs) - 1):
        if sorted_jobs[i].posted_date and sorted_jobs[i + 1].posted_date:
            assert sorted_jobs[i].posted_date >= sorted_jobs[i + 1].posted_date


def test_data_integrity_through_pipeline(sample_job_data, temp_output_dir):
    """Test that data remains consistent through the entire pipeline"""
    # Create pipeline components
    normalizer = JobNormalizer()
    deduplicator = JobDeduplicator()
    validator = JobValidator()
    exporter = CSVExporter(output_dir=temp_output_dir)
    
    # Track original data
    original_titles = {job.job_title for job in sample_job_data}
    original_companies = {job.company_name for job in sample_job_data}
    
    # Process through pipeline
    step1 = normalizer.normalize_jobs(sample_job_data)
    step2 = deduplicator.deduplicate_jobs(step1, strategy='content_based')
    step3_jobs = validator.validate_jobs(step2)['valid_jobs']
    
    # Export
    output_file = exporter.export_jobs(step3_jobs, filename="integrity_test.csv")
    
    # Import back
    final_jobs = read_jobs_from_csv(output_file)
    
    # Verify data integrity (some jobs may be removed by deduplication)
    final_titles = {job.job_title for job in final_jobs}
    final_companies = {job.company_name for job in final_jobs}
    
    # Final should be subset of original (due to deduplication)
    assert final_titles.issubset(original_titles)
    assert final_companies.issubset(original_companies)