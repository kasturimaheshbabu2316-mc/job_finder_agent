"""
Date processing utility functions
"""

from datetime import datetime, timedelta
from typing import Optional
import re


def parse_date_string(date_string: str) -> Optional[datetime]:
    """
    Parse various date string formats
    
    Args:
        date_string: Date string in various formats
    
    Returns:
        datetime object or None if parsing fails
    """
    if not date_string:
        return None
    
    date_string = date_string.strip()
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%m-%d-%Y',
        '%m/%d/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            continue
    
    # Handle relative dates like "2 days ago", "1 week ago"
    relative_date = parse_relative_date(date_string)
    if relative_date:
        return relative_date
    
    return None


def parse_relative_date(date_string: str) -> Optional[datetime]:
    """
    Parse relative date strings like "2 days ago", "1 week ago"
    
    Args:
        date_string: Relative date string
    
    Returns:
        datetime object or None if parsing fails
    """
    if not date_string:
        return None
    
    now = datetime.now()
    date_string = date_string.lower().strip()
    
    # Pattern for "X time ago" format
    patterns = [
        (r'(\d+)\s*seconds?\s*ago', timedelta(seconds=1)),
        (r'(\d+)\s*minutes?\s*ago', timedelta(minutes=1)),
        (r'(\d+)\s*hours?\s*ago', timedelta(hours=1)),
        (r'(\d+)\s*days?\s*ago', timedelta(days=1)),
        (r'(\d+)\s*weeks?\s*ago', timedelta(weeks=1)),
        (r'(\d+)\s*months?\s*ago', timedelta(days=30)),
        (r'(\d+)\s*years?\s*ago', timedelta(days=365)),
    ]
    
    for pattern, unit_delta in patterns:
        match = re.search(pattern, date_string)
        if match:
            try:
                quantity = int(match.group(1))
                return now - (unit_delta * quantity)
            except (ValueError, IndexError):
                continue
    
    # Handle "just now", "today", "yesterday"
    if 'just now' in date_string or 'today' in date_string:
        return now
    elif 'yesterday' in date_string:
        return now - timedelta(days=1)
    
    return None


def format_date(date: datetime, format_string: str = '%Y-%m-%d') -> str:
    """
    Format datetime object to string
    
    Args:
        date: datetime object
        format_string: Desired format string
    
    Returns:
        Formatted date string
    """
    if not date:
        return ""
    
    return date.strftime(format_string)


def get_age_from_date(date: datetime) -> str:
    """
    Get human-readable age from date (e.g., "2 days ago", "1 week ago")
    
    Args:
        date: datetime object
    
    Returns:
        Human-readable age string
    """
    if not date:
        return ""
    
    now = datetime.now()
    delta = now - date
    
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def is_recent_date(date: datetime, days_threshold: int = 30) -> bool:
    """
    Check if date is within recent threshold
    
    Args:
        date: datetime object
        days_threshold: Number of days to consider recent
    
    Returns:
        True if date is recent, False otherwise
    """
    if not date:
        return False
    
    now = datetime.now()
    delta = now - date
    
    return delta.days <= days_threshold


def normalize_posted_date(date_input) -> Optional[datetime]:
    """
    Normalize various date input types to datetime object
    
    Args:
        date_input: Date as string, datetime object, or None
    
    Returns:
        Normalized datetime object or None
    """
    if date_input is None:
        return None
    
    if isinstance(date_input, datetime):
        return date_input
    
    if isinstance(date_input, str):
        return parse_date_string(date_input)
    
    return None


def get_date_range_days(start_date: datetime, end_date: datetime) -> int:
    """
    Get number of days between two dates
    
    Args:
        start_date: Start datetime
        end_date: End datetime
    
    Returns:
        Number of days between dates
    """
    if not start_date or not end_date:
        return 0
    
    delta = end_date - start_date
    return delta.days
