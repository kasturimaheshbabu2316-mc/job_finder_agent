"""
Unit tests for utility functions
"""

import pytest
from datetime import datetime, timedelta
from src.utils.text_utils import (
    clean_text, extract_skills, normalize_location, 
    normalize_job_title, extract_salary_range
)
from src.utils.date_utils import (
    parse_date_string, parse_relative_date, format_date, 
    get_age_from_date, normalize_posted_date
)


def test_clean_text():
    """Test text cleaning"""
    assert clean_text("  Hello  World  ") == "Hello World"
    assert clean_text("Hello\nWorld") == "Hello World"
    assert clean_text("") == ""


def test_extract_skills():
    """Test skill extraction"""
    description = "We are looking for a Python developer with experience in React and AWS"
    skills = extract_skills(description)
    
    assert "Python" in skills
    assert len(skills) >= 1


def test_normalize_location():
    """Test location normalization"""
    assert normalize_location("bangalore") == "Bengaluru"
    assert normalize_location("nyc") == "New York"
    assert normalize_location("wfh") == "Remote"
    assert normalize_location("San Francisco") == "San Francisco"


def test_normalize_job_title():
    """Test job title normalization"""
    assert normalize_job_title("Sr. Software Engineer") == "Senior Software Engineer"
    assert normalize_job_title("Jr. Developer") == "Junior Developer"
    assert normalize_job_title("SWE") == "Software Engineer"


def test_extract_salary_range():
    """Test salary range extraction"""
    assert extract_salary_range("$50,000 - $80,000") is not None
    assert extract_salary_range("50k-80k") is not None
    assert extract_salary_range("No salary info") is None


def test_parse_date_string():
    """Test date string parsing"""
    assert parse_date_string("2023-06-15") == datetime(2023, 6, 15)
    assert parse_date_string("2023/06/15") == datetime(2023, 6, 15)
    assert parse_date_string("invalid date") is None


def test_parse_relative_date():
    """Test relative date parsing"""
    now = datetime.now()
    
    # Test "just now" and "today"
    assert parse_relative_date("just now") is not None
    assert parse_relative_date("today") is not None
    
    # Test "yesterday"
    yesterday = parse_relative_date("yesterday")
    assert yesterday is not None
    assert (now - yesterday).days == 1
    
    # Test "2 days ago"
    two_days_ago = parse_relative_date("2 days ago")
    assert two_days_ago is not None
    assert (now - two_days_ago).days >= 1


def test_format_date():
    """Test date formatting"""
    date = datetime(2023, 6, 15, 14, 30, 0)
    assert format_date(date) == "2023-06-15"
    assert format_date(date, "%Y/%m/%d") == "2023/06/15"


def test_get_age_from_date():
    """Test age calculation from date"""
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    age = get_age_from_date(one_hour_ago)
    assert "hour" in age.lower()
    assert "ago" in age.lower()


def test_normalize_posted_date():
    """Test posted date normalization"""
    # Test with datetime
    date = datetime(2023, 6, 15)
    assert normalize_posted_date(date) == date
    
    # Test with string
    assert normalize_posted_date("2023-06-15") == datetime(2023, 6, 15)
    
    # Test with relative string
    assert normalize_posted_date("2 days ago") is not None
    
    # Test with None
    assert normalize_posted_date(None) is None