"""
Display the contents of the generated CSV files
"""

import csv
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def display_csv_contents(csv_file_path):
    """Read and display CSV file contents"""
    csv_path = Path(csv_file_path)
    
    if not csv_path.exists():
        print(f"File not found: {csv_file_path}")
        return
    
    print(f"\n{'=' * 80}")
    print(f"CSV File: {csv_path.name}")
    print(f"{'=' * 80}\n")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Display headers
        headers = reader.fieldnames
        print(f"Columns ({len(headers)}): {', '.join(headers)}")
        print()
        
        # Display first few rows
        print("First few rows:")
        print("-" * 80)
        
        for i, row in enumerate(reader):
            if i >= 3:  # Show first 3 rows
                break
            print(f"\nRow {i + 1}:")
            for key, value in row.items():
                # Truncate long values for display
                display_value = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                print(f"  {key:20s}: {display_value}")
        
        # Show total row count
        print(f"\n... (Total rows: {i + 1})")

if __name__ == "__main__":
    # Display the generated CSV files
    data_dir = Path("data")
    
    csv_files = [
        "all_jobs_demo.csv",
        "remote_jobs_demo.csv"
    ]
    
    for csv_file in csv_files:
        csv_path = data_dir / csv_file
        if csv_path.exists():
            display_csv_contents(csv_path)
        else:
            print(f"File not found: {csv_file}")
    
    print(f"\n{'=' * 80}")
    print("CSV Files contain all job fields:")
    print("  - Job Title, Company Name, Job Description, Location")
    print("  - Salary Range, Job Type, Posted Date, Job URL, Platform")
    print("  - Skills, Experience Level, Industry, Company Size, Scraped At")
    print("=" * 80)