"""
Display the architecture CSV contents
"""

import csv
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def display_architecture_csv():
    """Read and display architecture CSV"""
    csv_path = Path("doc/architecture.csv")
    
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return
    
    print(f"\n{'=' * 100}")
    print(f"ARCHITECTURE IMPLEMENTATION STATUS")
    print(f"{'=' * 100}\n")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Display headers
        headers = reader.fieldnames
        print(f"Columns ({len(headers)}): {', '.join(headers)}")
        print()
        
        # Display all rows
        print("Implementation Status:")
        print("-" * 100)
        
        for row in reader:
            status = row.get('Status', '').upper()
            phase = row.get('Phase', '')
            goal = row.get('Goal', '')
            tasks = row.get('Key Tasks', '')
            
            # Create status indicator
            status_indicator = "[COMPLETE]" if status == "COMPLETE" else "[PARTIAL]" if status == "PARTIAL" else "[TODO]"
            
            print(f"\n{status_indicator} {phase}")
            print(f"  Duration: {row.get('Duration', 'N/A')}")
            print(f"  Goal: {goal}")
            print(f"  Status: {status}")
            print(f"  Priority: {row.get('Priority', 'N/A')}")
            print(f"  Tasks: {tasks[:80]}..." if len(tasks) > 80 else f"  Tasks: {tasks}")
            print(f"  Deliverables: {row.get('Deliverables', 'N/A')[:80]}..." if len(row.get('Deliverables', '')) > 80 else f"  Deliverables: {row.get('Deliverables', 'N/A')}")
        
        print(f"\n" + "=" * 100)
        print("SUMMARY")
        print("=" * 100)
        
        # Count statuses
        total_rows = 0
        complete_count = 0
        not_started_count = 0
        not_impl_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_rows += 1
                status = row.get('Status', '').upper()
                if status == "COMPLETE":
                    complete_count += 1
                elif status == "NOT STARTED":
                    not_started_count += 1
                elif status == "NOT IMPLEMENTED":
                    not_impl_count += 1
        
        print(f"Total items: {total_rows}")
        print(f"Completed: {complete_count}")
        print(f"Not started: {not_started_count}")
        print(f"Not implemented: {not_impl_count}")
        print(f"Completion rate: {(complete_count / total_rows * 100):.1f}%")

if __name__ == "__main__":
    display_architecture_csv()