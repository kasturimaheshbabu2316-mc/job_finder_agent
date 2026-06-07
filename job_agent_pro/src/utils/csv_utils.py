"""
CSV utility functions for reading and writing job data
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.job import Job


def write_jobs_to_csv(jobs: List[Job], filepath: str, mode: str = 'w') -> int:
    """
    Write jobs to CSV file
    
    Args:
        jobs: List of Job objects to write
        filepath: Path to CSV file
        mode: File mode ('w' for write, 'a' for append)
    
    Returns:
        Number of jobs written
    """
    if not jobs:
        return 0
    
    filepath_path = Path(filepath)
    filepath_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get CSV headers from first job
    headers = list(jobs[0].to_csv_row().keys())
    
    written_count = 0
    with open(filepath, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        
        # Write header only in write mode or if file is empty
        if mode == 'w' or (mode == 'a' and filepath_path.stat().st_size == 0):
            writer.writeheader()
        
        for job in jobs:
            try:
                writer.writerow(job.to_csv_row())
                written_count += 1
            except Exception as e:
                print(f"Error writing job {job.job_url}: {e}")
    
    return written_count


def read_jobs_from_csv(filepath: str) -> List[Job]:
    """
    Read jobs from CSV file
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        List of Job objects
    """
    jobs = []
    filepath_path = Path(filepath)
    
    if not filepath_path.exists():
        return jobs
    
    with open(filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            try:
                # Convert CSV row back to Job object
                job_dict = {
                    'job_title': row.get('Job Title', ''),
                    'company_name': row.get('Company Name', ''),
                    'job_description': row.get('Job Description', ''),
                    'location': row.get('Location', ''),
                    'salary_range': row.get('Salary Range') or None,
                    'job_type': row.get('Job Type') or None,
                    'posted_date': row.get('Posted Date') or None,
                    'job_url': row.get('Job URL', ''),
                    'platform_source': row.get('Platform', 'unknown'),
                    'skills': row.get('Skills', '').split(',') if row.get('Skills') else None,
                    'experience_level': row.get('Experience Level') or None,
                    'industry': row.get('Industry') or None,
                    'company_size': row.get('Company Size') or None,
                }
                jobs.append(Job.from_dict(job_dict))
            except Exception as e:
                print(f"Error reading row: {e}")
    
    return jobs


def append_jobs_to_csv(jobs: List[Job], filepath: str) -> int:
    """
    Append jobs to existing CSV file
    
    Args:
        jobs: List of Job objects to append
        filepath: Path to CSV file
    
    Returns:
        Number of jobs appended
    """
    return write_jobs_to_csv(jobs, filepath, mode='a')


def backup_csv_file(filepath: str, backup_dir: str = None) -> Optional[str]:
    """
    Create backup of CSV file
    
    Args:
        filepath: Path to CSV file to backup
        backup_dir: Directory to store backup (default: same as original)
    
    Returns:
        Path to backup file or None if backup failed
    """
    filepath_path = Path(filepath)
    
    if not filepath_path.exists():
        return None
    
    if backup_dir:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
    else:
        backup_path = filepath_path.parent
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{filepath_path.stem}_{timestamp}.csv"
    backup_filepath = backup_path / backup_filename
    
    try:
        import shutil
        shutil.copy2(filepath, backup_filepath)
        return str(backup_filepath)
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None


def get_csv_statistics(filepath: str) -> Dict[str, Any]:
    """
    Get statistics about CSV file
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        Dictionary with statistics
    """
    filepath_path = Path(filepath)
    
    if not filepath_path.exists():
        return {
            'exists': False,
            'total_jobs': 0,
            'platforms': {},
            'file_size': 0,
        }
    
    jobs = read_jobs_from_csv(filepath)
    
    platform_counts = {}
    for job in jobs:
        platform = job.platform_source.value
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    return {
        'exists': True,
        'total_jobs': len(jobs),
        'platforms': platform_counts,
        'file_size': filepath_path.stat().st_size,
        'last_modified': datetime.fromtimestamp(filepath_path.stat().st_mtime).isoformat(),
    }
