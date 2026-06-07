"""
Main entry point for running the job agent as a module
"""

from .cli.main import main
import sys

if __name__ == '__main__':
    sys.exit(main())
