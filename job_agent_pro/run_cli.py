"""
Simple CLI runner that handles the relative import issue
"""

import sys
from pathlib import Path

# Add src to path so it can be imported as a top-level package
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now import as absolute imports from src
from cli.main import main

if __name__ == '__main__':
    sys.exit(main())