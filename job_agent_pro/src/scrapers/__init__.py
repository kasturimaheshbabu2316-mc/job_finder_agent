"""
Job scrapers for different platforms
"""

from .base_scraper import BaseScraper
from .naukri_scraper import NaukriScraper
from .remoteok_scraper import RemoteOKScraper

__all__ = ['BaseScraper', 'NaukriScraper', 'RemoteOKScraper']
