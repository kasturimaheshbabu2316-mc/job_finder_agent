"""
Text processing utility functions
"""

import re
from typing import List, Optional, Set


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\-\.\,\:\;\!\?\(\)]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_skills(description: str) -> List[str]:
    """
    Extract skills from job description
    
    Args:
        description: Job description text
    
    Returns:
        List of extracted skills
    """
    if not description:
        return []
    
    # Common programming skills/technologies
    skill_patterns = [
        r'Python', r'Java', r'JavaScript', r'TypeScript', r'Go', r'Rust', 
        r'C\+\+', r'C\#', r'PHP', r'Ruby', r'Swift', r'Kotlin',
        r'React', r'Angular', r'Vue', r'Node\.js', r'Django', r'Flask',
        r'Spring', r'.NET', r'Rails', r'Laravel',
        r'SQL', r'MongoDB', r'PostgreSQL', r'MySQL', r'Redis',
        r'Docker', r'Kubernetes', r'AWS', r'Azure', r'GCP',
        r'Git', r'CI/CD', r'Agile', r'Scrum',
        r'Machine Learning', r'Data Science', r'AI', r'Deep Learning',
        r'TensorFlow', r'PyTorch', r'Keras', r'Scikit-learn',
    ]
    
    found_skills: Set[str] = set()
    
    for pattern in skill_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            found_skills.add(pattern)
    
    return list(found_skills)


def normalize_location(location: str) -> str:
    """
    Normalize location strings
    
    Args:
        location: Location string
    
    Returns:
        Normalized location
    """
    if not location:
        return ""
    
    location = location.strip().lower()
    
    # Common location normalizations
    location_mappings = {
        'bangalore': 'Bengaluru',
        'bengaluru': 'Bengaluru',
        'banglore': 'Bengaluru',
        'nyc': 'New York',
        'new york city': 'New York',
        'sf': 'San Francisco',
        'san francisco bay area': 'San Francisco',
        'remote - worldwide': 'Remote',
        'remote - us': 'Remote',
        'work from home': 'Remote',
        'wfh': 'Remote',
    }
    
    for key, value in location_mappings.items():
        if key in location:
            return value
    
    # Capitalize properly
    return location.title()


def normalize_job_title(title: str) -> str:
    """
    Normalize job title strings
    
    Args:
        title: Job title string
    
    Returns:
        Normalized job title
    """
    if not title:
        return ""
    
    title = title.strip()
    
    # Remove common suffixes/prefixes
    title = re.sub(r'^\w+\s*\-\s*', '', title)  # Remove "Senior - "
    title = re.sub(r'\s*\(\s*.*?\s*\)\s*$', '', title)  # Remove "(remote)"
    title = re.sub(r'\s*\|\s*.*', '', title)  # Remove " | Something"
    
    # Standardize common titles
    title_mappings = {
        'sr.': 'Senior',
        'sr': 'Senior',
        'jr.': 'Junior',
        'jr': 'Junior',
        'mgr.': 'Manager',
        'mgr': 'Manager',
        'dev': 'Developer',
        'eng': 'Engineer',
        'swe': 'Software Engineer',
    }
    
    for abbr, full in title_mappings.items():
        title = re.sub(r'\b' + abbr + r'\b', full, title, flags=re.IGNORECASE)
    
    return title.strip()


def extract_salary_range(salary_text: str) -> Optional[str]:
    """
    Extract salary range from text
    
    Args:
        salary_text: Text containing salary information
    
    Returns:
        Normalized salary range string or None
    """
    if not salary_text:
        return None
    
    # Look for patterns like "$50,000 - $80,000", "50k-80k", "50-80k"
    patterns = [
        r'\$?[\d,]+k?\s*[-–to]\s*\$?[\d,]+k?',  # 50k-80k, $50,000 - $80,000
        r'\$?[\d,]+\s*[-–to]\s*\$?[\d,]+',  # 50-80
        r'[\d,]+\s*[-–to]\s*[\d,]+\s*(?:usd|dollars?)?',  # 50-80 USD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, salary_text, re.IGNORECASE)
        if match:
            range_text = match.group()
            # Clean up the matched range
            range_text = re.sub(r'\s+', ' ', range_text)
            return range_text.strip()
    
    return None


def truncate_text(text: str, max_length: int = 500, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text
    
    Args:
        text: Text with HTML tags
    
    Returns:
        Text without HTML tags
    """
    if not text:
        return ""
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
    
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    }
    
    # Split into words and filter
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]
    
    return list(set(keywords))  # Remove duplicates
