"""
Setup script for Job Agent
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="job-agent",
    version="0.1.0",
    author="Job Agent Developer",
    description="Multi-platform job scraping agent that aggregates job listings from Naukri, RemoteOK, and LinkedIn",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/job-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "pandas>=2.0.0",
        "python-dateutil>=2.8.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.0",
        "lxml>=4.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "job-agent=src.cli.main:main",
        ],
    },
)