"""
CLI interface for Job Agent
"""

import argparse
import sys
from typing import Optional
from src.job_agent import JobAgent
from src.models.job import Platform
from src.exporters import CSVExporter
from src.utils.logger import get_logger, setup_logger
from src.utils.input_validator import InputValidator
from config import LOG_LEVEL


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI"""
    parser = argparse.ArgumentParser(
        description="Job Agent - Multi-platform job scraping system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape jobs with exact user-provided job role and location
  python -m src.cli.main scrape --keywords "software engineer" --location remote
  
  # Show suggestions for job roles and locations
  python -m src.cli.main suggest
  
  # Scrape specific platforms with exact job role and location
  python -m src.cli.main scrape --platforms naukri remoteok --keywords "data scientist" --location bengaluru
  
  # Export filtered results to CSV
  python -m src.cli.main scrape --keywords "Python developer" --location remote --output jobs.csv
  
  # Show statistics for exported file
  python -m src.cli.main stats --file jobs.csv
  
  # List all exported files
  python -m src.cli.main list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape jobs from platforms')
    scrape_parser.add_argument('--platforms', nargs='+', choices=['naukri', 'remoteok'],
                              help='Platforms to scrape (default: naukri and remoteok)')
    scrape_parser.add_argument('--keywords', default='software engineer',
                              help='Exact job role to search for (e.g., "software engineer", "data scientist")')
    scrape_parser.add_argument('--location', default='remote',
                              help='Exact location to search in (e.g., "remote", "bengaluru", "mumbai")')
    scrape_parser.add_argument('--max-jobs', type=int, default=50,
                              help='Maximum jobs per platform')
    scrape_parser.add_argument('--output', help='Output CSV file')
    scrape_parser.add_argument('--no-normalize', action='store_true',
                              help='Skip data normalization')
    scrape_parser.add_argument('--no-deduplicate', action='store_true',
                              help='Skip deduplication')
    scrape_parser.add_argument('--no-validate', action='store_true',
                              help='Skip validation')
    scrape_parser.add_argument('--filter-titles', nargs='+',
                              help='Filter by job titles')
    scrape_parser.add_argument('--filter-locations', nargs='+',
                              help='Filter by locations')
    scrape_parser.add_argument('--parallel', action='store_true', default=True,
                              help='Scrape platforms in parallel')
    scrape_parser.add_argument('--sequential', dest='parallel', action='store_false',
                              help='Scrape platforms sequentially')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export operations')
    export_parser.add_argument('--file', required=True, help='CSV file to operate on')
    export_parser.add_argument('--by-platform', action='store_true',
                             help='Export jobs grouped by platform')
    export_parser.add_argument('--output', help='Output filename')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--file', help='CSV file to analyze')
    stats_parser.add_argument('--platforms', action='store_true',
                             help='Show platform breakdown')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List exported files')
    list_parser.add_argument('--details', action='store_true',
                            help='Show detailed information')
    
    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Filter jobs')
    filter_parser.add_argument('--file', required=True, help='Input CSV file')
    filter_parser.add_argument('--output', required=True, help='Output CSV file')
    filter_parser.add_argument('--titles', nargs='+', help='Filter by job titles')
    filter_parser.add_argument('--locations', nargs='+', help='Filter by locations')
    filter_parser.add_argument('--companies', nargs='+', help='Filter by companies')
    filter_parser.add_argument('--days', type=int, help='Filter jobs posted within N days')
    
    # Suggestions command
    suggestions_parser = subparsers.add_parser('suggest', help='Show suggestions for job roles and locations')
    suggestions_parser.add_argument('--type', choices=['roles', 'locations', 'both'], default='both',
                                   help='Type of suggestions to show')
    suggestions_parser.add_argument('--limit', type=int, default=10,
                                   help='Maximum number of suggestions to show')
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress non-error logging')
    
    return parser


def handle_scrape(args) -> int:
    """Handle scrape command with exact user input validation"""
    logger = get_logger("cli")
    
    # Initialize input validator
    input_validator = InputValidator()
    
    # Validate user input
    logger.info("Validating user input...")
    is_valid, normalized_inputs, errors = input_validator.validate_user_input(args.keywords, args.location)
    
    if not is_valid:
        logger.error("Input validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        print("\nERROR Input validation failed:")
        for error in errors:
            print(f"  - {error}")
        print("\nTIP Suggestions:")
        print(f"  Common job roles: {', '.join(input_validator.get_common_job_roles()[:5])}")
        print(f"  Common locations: {', '.join(input_validator.get_common_locations()[:5])}")
        return 1
    
    # Use normalized inputs
    normalized_job_role = normalized_inputs['job_role']
    normalized_location = normalized_inputs['location']
    
    logger.info(f"Validated input: {input_validator.format_input_summary(normalized_job_role, normalized_location)}")
    print(f"\nTARGET Searching for: {input_validator.format_input_summary(normalized_job_role, normalized_location)}")
    
    # Parse platforms
    platforms = None
    if args.platforms:
        platform_map = {
            'naukri': Platform.NAUKRI,
            'remoteok': Platform.REMOTEOK
        }
        platforms = [platform_map[p] for p in args.platforms]
        logger.info(f"Target platforms: {', '.join(args.platforms)}")
    else:
        logger.info("Target platforms: naukri, remoteok (default)")
    
    # Build filter configuration
    filter_config = {}
    if args.filter_titles:
        filter_config['job_titles'] = args.filter_titles
    if args.filter_locations:
        filter_config['locations'] = args.filter_locations
    
    # Initialize job agent
    agent = JobAgent()
    
    try:
        # Run pipeline with validated inputs (skip re-validation since already done at CLI level)
        logger.info("Starting job scraping pipeline...")
        jobs = agent.run_full_pipeline(
            keywords=normalized_job_role,
            location=normalized_location,
            max_jobs_per_platform=args.max_jobs,
            output_file=args.output,
            filter_config=filter_config if filter_config else None,
            skip_input_validation=True  # Skip validation since already done above
        )
        
        if not jobs:
            logger.warning("No jobs were found/processed")
            print("\nWARNING No jobs were found with the specified criteria.")
            print("TIP Try:")
            print("  - Using a more general job role")
            print("  - Trying a different location")
            print("  - Checking if the platforms are accessible")
            return 1
        
        # Print summary
        print(f"\nSUCCESS Successfully scraped and processed {len(jobs)} jobs")
        if args.output:
            print(f"SUCCESS Results exported to: {args.output}")
        
        # Print platform breakdown
        if agent.run_statistics.get('platform_stats'):
            print(f"\n📊 Platform Breakdown:")
            for platform, stats in agent.run_statistics['platform_stats'].items():
                print(f"  {platform.title()}: {stats.get('jobs_scraped', 0)} jobs")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        print(f"\nERROR Error during scraping: {e}")
        return 1


def handle_export(args) -> int:
    """Handle export command"""
    logger = get_logger("cli")
    
    exporter = CSVExporter()
    
    if args.by_platform:
        # Export by platform from existing file
        from src.utils.csv_utils import read_jobs_from_csv
        
        try:
            jobs = read_jobs_from_csv(args.file)
            exported_files = exporter.export_by_platform(jobs)
            
            print(f"SUCCESS Exported {len(exported_files)} platform-specific files:")
            for filepath in exported_files:
                print(f"  - {filepath}")
            
            return 0
        except Exception as e:
            logger.error(f"Error during export: {e}")
            return 1
    else:
        logger.error("Export operation not specified")
        return 1


def handle_stats(args) -> int:
    """Handle stats command"""
    logger = get_logger("cli")
    
    if args.file:
        # Show statistics for specific file
        exporter = CSVExporter()
        stats = exporter.get_export_statistics(args.file)
        
        if 'error' in stats:
            print(f"Error: {stats['error']}")
            return 1
        
        print(f"\nStatistics for {args.file}:")
        print(f"  Total jobs: {stats.get('total_jobs', 0)}")
        print(f"  File size: {stats.get('file_size', 0)} bytes")
        print(f"  Last modified: {stats.get('last_modified', 'Unknown')}")
        
        if args.platforms and 'platforms' in stats:
            print("\nPlatform breakdown:")
            for platform, count in stats['platforms'].items():
                print(f"  {platform}: {count}")
        
        return 0
    else:
        print("Error: Please specify a file with --file")
        return 1


def handle_list(args) -> int:
    """Handle list command"""
    logger = get_logger("cli")
    
    exporter = CSVExporter()
    exports = exporter.list_exports()
    
    if not exports:
        print("No export files found")
        return 0
    
    print(f"\nFound {len(exports)} export file(s):\n")
    
    for export in exports:
        print(f"File: {export['filename']}")
        print(f"  Size: {export['size']} bytes")
        print(f"  Jobs: {export['job_count']}")
        print(f"  Modified: {export['modified']}")
        
        if args.details:
            stats = exporter.get_export_statistics(export['filename'])
            if 'metadata' in stats:
                metadata = stats['metadata']
                print(f"  Export time: {metadata.get('export_time', 'Unknown')}")
                if 'platforms' in metadata:
                    print(f"  Platforms: {', '.join(metadata['platforms'].keys())}")
        
        print()
    
    return 0


def handle_suggestions(args) -> int:
    """Handle suggestions command"""
    logger = get_logger("cli")
    
    input_validator = InputValidator()
    
    print("\nTIP Input Suggestions:")
    print("=" * 40)
    
    if args.type in ['roles', 'both']:
        print("\nCommon Job Roles:")
        roles = input_validator.get_common_job_roles()[:args.limit]
        for i, role in enumerate(roles, 1):
            print(f"  {i}. {role}")
    
    if args.type in ['locations', 'both']:
        print("\nCommon Locations:")
        locations = input_validator.get_common_locations()[:args.limit]
        for i, location in enumerate(locations, 1):
            print(f"  {i}. {location}")
    
    print("\n" + "=" * 40)
    print("TIP Usage: python -m src.cli.main scrape --keywords \"software engineer\" --location remote")
    
    return 0


def handle_filter(args) -> int:
    """Handle filter command"""
    logger = get_logger("cli")
    
    from ..utils.csv_utils import read_jobs_from_csv
    from src.models.job import Job
    
    try:
        jobs = read_jobs_from_csv(args.file)
        
        if not jobs:
            print("No jobs found in input file")
            return 1
        
        print(f"Loaded {len(jobs)} jobs from {args.file}")
        
        # Apply filters
        from src.processors import JobFilter
        
        filter_obj = JobFilter()
        
        filter_config = {}
        if args.titles:
            filter_config['job_titles'] = args.titles
        if args.locations:
            filter_config['locations'] = args.locations
        if args.companies:
            filter_config['companies'] = args.companies
        if args.days:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=args.days)
            filter_config['posted_after'] = cutoff_date
        
        filtered_jobs = filter_obj.filter_jobs(jobs, **filter_config)
        
        print(f"Filtered to {len(filtered_jobs)} jobs")
        
        # Export filtered jobs
        exporter = CSVExporter()
        output_file = exporter.export_jobs(filtered_jobs, args.output)
        
        print(f"SUCCESS Filtered jobs exported to: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during filtering: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "ERROR" if args.quiet else LOG_LEVEL
    setup_logger(level=log_level)
    logger = get_logger("cli")
    
    if not args.command:
        parser.print_help()
        return 1
    
    logger.info(f"Running command: {args.command}")
    
    # Route to appropriate handler
    handlers = {
        'scrape': handle_scrape,
        'export': handle_export,
        'stats': handle_stats,
        'list': handle_list,
        'filter': handle_filter,
        'suggest': handle_suggestions,
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())