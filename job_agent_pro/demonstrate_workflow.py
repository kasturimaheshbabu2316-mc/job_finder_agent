"""
Demonstration script to show complete job agent workflow and CSV generation
This creates sample job data and exports it to CSV to demonstrate the functionality
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from src.models.job import Job, JobType, Platform
from src.exporters import CSVExporter
from src.processors import JobNormalizer, JobDeduplicator, JobFilter, JobValidator
from src.utils.logger import setup_logger, get_logger

def create_sample_jobs():
    """Create sample job data for demonstration"""
    
    # Current time for realistic posting dates
    now = datetime.now()
    
    sample_jobs = [
        Job(
            job_title="Software Engineer",
            company_name="Tech Corp India",
            job_description="We are looking for a skilled Software Engineer to join our team. You will be responsible for developing and maintaining web applications using Python and React. The ideal candidate should have 3+ years of experience in software development.",
            location="Bengaluru",
            salary_range="₹8,00,000 - ₹15,00,000 per annum",
            job_type=JobType.FULL_TIME,
            posted_date=now - timedelta(days=2),
            job_url="https://www.naukri.com/job-listing/software-engineer-tech-corp-12345",
            platform_source=Platform.NAUKRI,
            skills=["Python", "React", "JavaScript", "AWS", "Docker"],
            experience_level="3-5 years",
            industry="Technology",
            company_size="500-1000 employees"
        ),
        Job(
            job_title="Data Scientist",
            company_name="Analytics Solutions",
            job_description="Join our data science team to work on cutting-edge machine learning projects. You will analyze large datasets, build predictive models, and collaborate with cross-functional teams to drive data-driven decisions.",
            location="Remote",
            salary_range="$80,000 - $120,000 per year",
            job_type=JobType.REMOTE,
            posted_date=now - timedelta(days=1),
            job_url="https://remoteok.com/remote-jobs/data-scientist-analytics-solutions",
            platform_source=Platform.REMOTEOK,
            skills=["Python", "Machine Learning", "SQL", "TensorFlow", "Pandas"],
            experience_level="2-4 years",
            industry="Data Analytics",
            company_size="100-500 employees"
        ),
        Job(
            job_title="Software Engineer",  # Duplicate title/company to test deduplication
            company_name="Tech Corp India",  # Duplicate company
            job_description="Software engineering position with focus on backend development using Java Spring Boot. Work on enterprise applications and microservices architecture.",
            location="Mumbai",
            salary_range="₹10,00,000 - ₹18,00,000 per annum",
            job_type=JobType.FULL_TIME,
            posted_date=now - timedelta(days=5),
            job_url="https://www.naukri.com/job-listing/backend-engineer-tech-corp-67890",
            platform_source=Platform.NAUKRI,
            skills=["Java", "Spring Boot", "Microservices", "MySQL", "Kubernetes"],
            experience_level="4-6 years",
            industry="Technology",
            company_size="500-1000 employees"
        ),
        Job(
            job_title="Frontend Developer",
            company_name="Web Innovators",
            job_description="Looking for an experienced Frontend Developer to build modern, responsive web applications. You will work with React, TypeScript, and modern CSS frameworks to create exceptional user experiences.",
            location="Remote",
            salary_range="$70,000 - $100,000 per year",
            job_type=JobType.REMOTE,
            posted_date=now - timedelta(days=3),
            job_url="https://remoteok.com/remote-jobs/frontend-developer-web-innovators",
            platform_source=Platform.REMOTEOK,
            skills=["React", "TypeScript", "CSS", "JavaScript", "Redux"],
            experience_level="2-4 years",
            industry="Web Development",
            company_size="50-100 employees"
        ),
        Job(
            job_title="DevOps Engineer",
            company_name="Cloud Systems",
            job_description="We need a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. Experience with AWS, Kubernetes, and automation tools is required.",
            location="Pune",
            salary_range="₹12,00,000 - ₹20,00,000 per annum",
            job_type=JobType.FULL_TIME,
            posted_date=now - timedelta(days=4),
            job_url="https://www.naukri.com/job-listing/devops-engineer-cloud-systems-11111",
            platform_source=Platform.NAUKRI,
            skills=["AWS", "Kubernetes", "Docker", "Jenkins", "Ansible"],
            experience_level="3-5 years",
            industry="Cloud Computing",
            company_size="200-500 employees"
        ),
        Job(
            job_title="Machine Learning Engineer",
            company_name="AI Labs",
            job_description="Build and deploy machine learning models at scale. Work on computer vision and natural language processing projects with state-of-the-art techniques.",
            location="Remote",
            salary_range="$90,000 - $140,000 per year",
            job_type=JobType.REMOTE,
            posted_date=now - timedelta(days=1),
            job_url="https://remoteok.com/remote-jobs/ml-engineer-ai-labs",
            platform_source=Platform.REMOTEOK,
            skills=["Python", "TensorFlow", "PyTorch", "Computer Vision", "NLP"],
            experience_level="4-7 years",
            industry="Artificial Intelligence",
            company_size="100-200 employees"
        ),
        Job(
            job_title="Full Stack Developer",
            company_name="Digital Solutions",
            job_description="Full-stack development role working on both frontend and backend. MERN stack experience preferred. Build scalable web applications for enterprise clients.",
            location="Hyderabad",
            salary_range="₹9,00,000 - ₹16,00,000 per annum",
            job_type=JobType.FULL_TIME,
            posted_date=now - timedelta(days=6),
            job_url="https://www.naukri.com/job-listing/full-stack-developer-digital-solutions-22222",
            platform_source=Platform.NAUKRI,
            skills=["MongoDB", "Express.js", "React", "Node.js", "TypeScript"],
            experience_level="3-5 years",
            industry="Software Development",
            company_size="200-400 employees"
        ),
        Job(
            job_title="Python Developer",
            company_name="Script Masters",
            job_description="Python development position focusing on backend APIs and data processing. Experience with Django, Flask, and data libraries like Pandas required.",
            location="Chennai",
            salary_range="₹7,00,000 - ₹12,00,000 per annum",
            job_type=JobType.FULL_TIME,
            posted_date=now - timedelta(days=7),
            job_url="https://www.naukri.com/job-listing/python-developer-script-masters-33333",
            platform_source=Platform.NAUKRI,
            skills=["Python", "Django", "Flask", "SQL", "API Development"],
            experience_level="2-4 years",
            industry="Software Development",
            company_size="100-300 employees"
        )
    ]
    
    return sample_jobs


def demonstrate_complete_workflow():
    """Demonstrate the complete job agent workflow"""
    
    # Setup logging
    setup_logger(level="INFO")
    logger = get_logger("demo")
    
    print("=" * 60)
    print("JOB AGENT DEMONSTRATION")
    print("Complete Workflow Demonstration with CSV Generation")
    print("=" * 60)
    
    # Step 1: Create sample job data
    print("\n[Step 1] Creating sample job data...")
    sample_jobs = create_sample_jobs()
    logger.info(f"Created {len(sample_jobs)} sample jobs from naukri and remoteok")
    print(f"   Created {len(sample_jobs)} sample jobs")
    print(f"   Platforms: naukri ({sum(1 for j in sample_jobs if j.platform_source == Platform.NAUKRI)} jobs)")
    print(f"   Platforms: remoteok ({sum(1 for j in sample_jobs if j.platform_source == Platform.REMOTEOK)} jobs)")
    
    # Step 2: Normalize jobs
    print("\n[Step 2] Normalizing job data...")
    normalizer = JobNormalizer()
    normalized_jobs = normalizer.normalize_jobs(sample_jobs)
    logger.info(f"Normalized {len(normalized_jobs)} jobs")
    print(f"   Normalized {len(normalized_jobs)} jobs")
    
    # Step 3: Remove duplicates
    print("\n[Step 3] Removing duplicate jobs...")
    deduplicator = JobDeduplicator()
    deduplicated_jobs = deduplicator.deduplicate_jobs(normalized_jobs, strategy='hybrid')
    logger.info(f"Removed {len(normalized_jobs) - len(deduplicated_jobs)} duplicates")
    print(f"   Removed {len(normalized_jobs) - len(deduplicated_jobs)} duplicate jobs")
    print(f"   Remaining unique jobs: {len(deduplicated_jobs)}")
    
    # Step 4: Validate jobs
    print("\n[Step 4] Validating job data...")
    validator = JobValidator()
    validation_results = validator.validate_jobs(deduplicated_jobs)
    logger.info(f"Validation: {validation_results['statistics']['total_passed']}/{validation_results['statistics']['total_validated']} jobs passed")
    print(f"   Valid jobs: {validation_results['statistics']['total_passed']}")
    print(f"   Invalid jobs: {validation_results['statistics']['total_failed']}")
    
    # Step 5: Filter jobs (example: only remote jobs)
    print("\n[Step 5] Filtering jobs (remote positions only)...")
    job_filter = JobFilter()
    filtered_jobs = job_filter.filter_jobs(validation_results['valid_jobs'], locations=["remote"])
    logger.info(f"Filtered to {len(filtered_jobs)} remote jobs")
    print(f"   Remote jobs found: {len(filtered_jobs)}")
    
    # Step 6: Export to CSV
    print("\n[Step 6] Exporting jobs to CSV file...")
    exporter = CSVExporter(output_dir="data")
    
    # Export all jobs
    all_jobs_file = exporter.export_jobs(
        validation_results['valid_jobs'],
        filename="all_jobs_demo.csv",
        include_metadata=True
    )
    print(f"   [OK] All jobs exported to: {all_jobs_file}")
    
    # Export filtered jobs
    remote_jobs_file = exporter.export_jobs(
        filtered_jobs,
        filename="remote_jobs_demo.csv",
        include_metadata=True
    )
    print(f"   [OK] Remote jobs exported to: {remote_jobs_file}")
    
    # Step 7: Show export statistics
    print("\n[Step 7] Export statistics...")
    stats_all = exporter.get_export_statistics("all_jobs_demo.csv")
    print(f"   All jobs file:")
    print(f"     Total jobs: {stats_all.get('total_jobs', stats_all.get('job_count', 'N/A'))}")
    print(f"     File size: {stats_all.get('file_size', stats_all.get('size', 'N/A'))} bytes")
    
    if 'metadata' in stats_all:
        metadata = stats_all['metadata']
        print(f"     Export time: {metadata.get('export_time', 'N/A')}")
        platforms = metadata.get('platforms', {})
        if platforms:
            print(f"     Platforms: {', '.join(platforms.keys())}")
    
    # Step 8: Show data quality
    print("\n[Step 8] Data quality assessment...")
    quality = validator.validate_data_quality(validation_results['valid_jobs'])
    print(f"   Data quality score: {quality['data_quality_score']:.1f}/100")
    print(f"   Quality rating: {quality['quality_rating']}")
    
    # Step 9: List all exports
    print("\n[Step 9] Listing all export files...")
    exports = exporter.list_exports()
    print(f"   Total export files: {len(exports)}")
    for export in exports[:3]:  # Show first 3
        print(f"     - {export['filename']} ({export['job_count']} jobs)")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print(f"\n[Generated CSV files]")
    print(f"   1. data/all_jobs_demo.csv - All validated jobs")
    print(f"   2. data/remote_jobs_demo.csv - Filtered remote jobs")
    print(f"\n[INFO] You can open these CSV files to see the complete job data")
    print(f"   including job title, company, description, location, salary, skills, etc.")
    
    return validation_results['valid_jobs']


if __name__ == "__main__":
    try:
        final_jobs = demonstrate_complete_workflow()
        print(f"\n[SUCCESS] Generated {len(final_jobs)} validated job entries in CSV files")
    except Exception as e:
        print(f"\n[ERROR] Error during demonstration: {e}")
        import traceback
        traceback.print_exc()