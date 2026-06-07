"""
CSV export system with advanced features
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import csv
import json
from ..models.job import Job
from ..utils.csv_utils import write_jobs_to_csv, read_jobs_from_csv, backup_csv_file, get_csv_statistics
from ..utils.logger import get_logger


class CSVExporter:
    """
    Advanced CSV export system with backup, versioning, and statistics
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize CSV exporter
        
        Args:
            output_dir: Directory for output files (default: data/)
        """
        self.logger = get_logger("csv_exporter")
        self.output_dir = Path(output_dir) if output_dir else Path("data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export statistics
        self.export_count = 0
        self.total_jobs_exported = 0
    
    def export_jobs(self, 
                   jobs: List[Job],
                   filename: str = None,
                   create_backup: bool = True,
                   append_mode: bool = False,
                   include_metadata: bool = True) -> str:
        """
        Export jobs to CSV file with advanced features
        
        Args:
            jobs: List of Job objects to export
            filename: Output filename (default: jobs_YYYYMMDD_HHMMSS.csv)
            create_backup: Whether to backup existing file
            append_mode: Whether to append to existing file
            include_metadata: Whether to include export metadata
        
        Returns:
            Path to exported file
        """
        if not jobs:
            self.logger.warning("No jobs to export")
            return ""
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"jobs_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Backup existing file if requested
        if create_backup and filepath.exists() and not append_mode:
            backup_path = backup_csv_file(str(filepath), backup_dir=str(self.output_dir / "backups"))
            if backup_path:
                self.logger.info(f"Backup created: {backup_path}")
        
        # Export jobs
        mode = 'a' if append_mode else 'w'
        written_count = write_jobs_to_csv(jobs, str(filepath), mode=mode)
        
        # Add metadata file if requested
        if include_metadata:
            self._create_metadata_file(jobs, filepath, written_count)
        
        self.export_count += 1
        self.total_jobs_exported += written_count
        
        self.logger.info(f"Exported {written_count} jobs to {filepath}")
        
        return str(filepath)
    
    def _create_metadata_file(self, jobs: List[Job], csv_filepath: Path, count: int):
        """
        Create metadata file alongside CSV export
        
        Args:
            jobs: List of exported jobs
            csv_filepath: Path to CSV file
            count: Number of jobs exported
        """
        metadata = {
            'export_time': datetime.now().isoformat(),
            'job_count': count,
            'source_file': str(csv_filepath.name),
            'platforms': {},
            'job_types': {},
            'locations': {},
        }
        
        # Calculate statistics
        for job in jobs:
            # Platform statistics
            platform = job.platform_source.value
            metadata['platforms'][platform] = metadata['platforms'].get(platform, 0) + 1
            
            # Job type statistics
            if job.job_type:
                job_type = job.job_type.value
                metadata['job_types'][job_type] = metadata['job_types'].get(job_type, 0) + 1
            
            # Location statistics
            location = job.location
            metadata['locations'][location] = metadata['locations'].get(location, 0) + 1
        
        # Write metadata file
        metadata_path = csv_filepath.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Metadata file created: {metadata_path}")
    
    def export_by_platform(self, jobs: List[Job], create_separate_files: bool = True) -> List[str]:
        """
        Export jobs grouped by platform
        
        Args:
            jobs: List of Job objects to export
            create_separate_files: Whether to create separate files per platform
        
        Returns:
            List of exported file paths
        """
        if not jobs:
            self.logger.warning("No jobs to export")
            return []
        
        if create_separate_files:
            # Export each platform to separate file
            exported_files = []
            platform_jobs: Dict[str, List[Job]] = {}
            
            for job in jobs:
                platform = job.platform_source.value
                if platform not in platform_jobs:
                    platform_jobs[platform] = []
                platform_jobs[platform].append(job)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for platform, platform_job_list in platform_jobs.items():
                filename = f"jobs_{platform}_{timestamp}.csv"
                filepath = self.export_jobs(platform_job_list, filename, create_backup=False)
                if filepath:
                    exported_files.append(filepath)
            
            return exported_files
        else:
            # Export all jobs to single file with platform column
            return [self.export_jobs(jobs)]
    
    def export_filtered_jobs(self, 
                            jobs: List[Job],
                            filter_criteria: Dict[str, Any],
                            filename: str = None) -> str:
        """
        Export jobs that meet specific criteria
        
        Args:
            jobs: List of Job objects
            filter_criteria: Filter criteria (e.g., {'platform': 'naukri', 'location': 'remote'})
            filename: Output filename
        
        Returns:
            Path to exported file
        """
        from ..processors import JobFilter
        
        filter_obj = JobFilter()
        filtered_jobs = filter_obj.filter_jobs(jobs, **filter_criteria)
        
        return self.export_jobs(filtered_jobs, filename)
    
    def append_to_existing(self, jobs: List[Job], filename: str) -> int:
        """
        Append jobs to existing CSV file
        
        Args:
            jobs: List of Job objects to append
            filename: Existing CSV filename
        
        Returns:
            Number of jobs appended
        """
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            self.logger.warning(f"File {filename} does not exist, creating new file")
            return self.export_jobs(jobs, filename)
        
        return self.export_jobs(jobs, filename, append_mode=True, create_backup=True)
    
    def get_export_statistics(self, filename: str) -> Dict[str, Any]:
        """
        Get statistics about an exported file
        
        Args:
            filename: CSV filename
        
        Returns:
            Dictionary with file statistics
        """
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            return {'error': 'File does not exist'}
        
        stats = get_csv_statistics(str(filepath))
        
        # Try to load metadata file if it exists
        metadata_path = filepath.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                stats['metadata'] = json.load(f)
        
        return stats
    
    def list_exports(self) -> List[Dict[str, Any]]:
        """
        List all exported CSV files with basic information
        
        Returns:
            List of file information dictionaries
        """
        exports = []
        
        for csv_file in self.output_dir.glob("*.csv"):
            file_info = {
                'filename': csv_file.name,
                'path': str(csv_file),
                'size': csv_file.stat().st_size,
                'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat(),
            }
            
            # Try to get statistics
            try:
                stats = get_csv_statistics(str(csv_file))
                file_info['job_count'] = stats.get('total_jobs', 0)
            except:
                file_info['job_count'] = 'Unknown'
            
            exports.append(file_info)
        
        # Sort by modification date (newest first)
        exports.sort(key=lambda x: x['modified'], reverse=True)
        
        return exports
    
    def cleanup_old_exports(self, keep_days: int = 30, dry_run: bool = True) -> List[str]:
        """
        Clean up export files older than specified days
        
        Args:
            keep_days: Number of days to keep files
            dry_run: If True, only list files to delete (don't actually delete)
        
        Returns:
            List of files that would be/is deleted
        """
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        files_to_delete = []
        
        for csv_file in self.output_dir.glob("*.csv"):
            if csv_file.stat().st_mtime < cutoff_date:
                files_to_delete.append(str(csv_file))
        
        if dry_run:
            self.logger.info(f"Dry run: Would delete {len(files_to_delete)} files older than {keep_days} days")
        else:
            for file_path in files_to_delete:
                try:
                    Path(file_path).unlink()
                    # Also delete metadata file if it exists
                    metadata_path = Path(file_path).with_suffix('.json')
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    self.logger.info(f"Deleted old export: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error deleting {file_path}: {e}")
        
        return files_to_delete
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get exporter statistics
        
        Returns:
            Dictionary with exporter statistics
        """
        return {
            'export_count': self.export_count,
            'total_jobs_exported': self.total_jobs_exported,
            'output_directory': str(self.output_dir),
        }
    
    def reset_statistics(self):
        """Reset exporter statistics"""
        self.export_count = 0
        self.total_jobs_exported = 0