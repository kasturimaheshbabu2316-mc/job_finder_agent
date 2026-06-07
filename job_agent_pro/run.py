"""
Standalone CLI runner that handles imports properly
"""

import argparse
import sys
from pathlib import Path

# Add the project root to Python path for proper module resolution
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Now we can import as if we're in the project root
from src.cli.main import main

if __name__ == '__main__':
    sys.exit(main())