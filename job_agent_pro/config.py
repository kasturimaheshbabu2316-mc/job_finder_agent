"""
Centralized configuration management for Job Agent
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.absolute()
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "data")
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Naukri Configuration
NAUKRI_BASE_URL = os.getenv("NAUKRI_BASE_URL", "https://www.naukri.com")
NAUKRI_SEARCH_URL = os.getenv("NAUKRI_SEARCH_URL", "https://www.naukri.com/jobapi/v7/search")

# RemoteOK Configuration
REMOTEOK_API_URL = os.getenv("REMOTEOK_API_URL", "https://remoteok.com/api")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/job_agent.log")

# Scraping Settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "2.0"))

# Job Filtering Settings
DEFAULT_JOB_TITLES = os.getenv("DEFAULT_JOB_TITLES", "Software Engineer,Data Scientist,DevOps Engineer").split(",")
DEFAULT_LOCATIONS = os.getenv("DEFAULT_LOCATIONS", "Remote,Bengaluru,Mumbai").split(",")
DEFAULT_JOB_TYPES = os.getenv("DEFAULT_JOB_TYPES", "Full-time,Contract").split(",")

# Scheduling Configuration
ENABLE_SCHEDULING = os.getenv("ENABLE_SCHEDULING", "false").lower() == "true"
SCHEDULE_INTERVAL = os.getenv("SCHEDULE_INTERVAL", "daily")  # daily, weekly, hourly
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")  # HH:MM format

# Platform-specific settings
PLATFORM_CONFIGS = {
    "naukri": {
        "enabled": True,
        "base_url": NAUKRI_BASE_URL,
        "search_url": NAUKRI_SEARCH_URL,
        "rate_limit": RATE_LIMIT_DELAY,
        "timeout": REQUEST_TIMEOUT,
    },
    "remoteok": {
        "enabled": True,
        "api_url": REMOTEOK_API_URL,
        "rate_limit": RATE_LIMIT_DELAY,
        "timeout": REQUEST_TIMEOUT,
    }
}

# Data field mappings for normalization
FIELD_MAPPINGS = {
    "job_title": ["title", "job_title", "position", "role"],
    "company_name": ["company", "company_name", "organization", "employer"],
    "job_description": ["description", "job_description", "details", "summary"],
    "location": ["location", "city", "place", "region"],
    "salary_range": ["salary", "salary_range", "pay", "compensation"],
    "job_type": ["job_type", "employment_type", "type", "employment"],
    "posted_date": ["posted_date", "date", "posted", "published"],
    "job_url": ["url", "job_url", "link", "apply_url"],
    "platform_source": ["source", "platform", "site"]
}

def get_config() -> dict:
    """Get all configuration as a dictionary"""
    return {
        "naukri": {
            "base_url": NAUKRI_BASE_URL,
            "search_url": NAUKRI_SEARCH_URL,
        },
        "remoteok": {
            "api_url": REMOTEOK_API_URL,
        },
        "scraping": {
            "timeout": REQUEST_TIMEOUT,
            "max_retries": MAX_RETRIES,
            "rate_limit_delay": RATE_LIMIT_DELAY,
        },
        "logging": {
            "level": LOG_LEVEL,
            "file": LOG_FILE,
        },
        "paths": {
            "base_dir": BASE_DIR,
            "data_dir": DATA_DIR,
            "output_dir": OUTPUT_DIR,
            "logs_dir": LOGS_DIR,
            "config_dir": CONFIG_DIR,
        }
    }

def validate_config() -> tuple[bool, List[str]]:
    """Validate required configuration settings"""
    errors = []
    
    # No required configuration for current implementation
    # Naukri and RemoteOK don't require API keys
    
    return len(errors) == 0, errors
