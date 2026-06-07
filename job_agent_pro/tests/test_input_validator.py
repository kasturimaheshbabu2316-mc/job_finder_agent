"""
Unit tests for Input Validator
"""

import pytest
from src.utils.input_validator import InputValidator


def test_input_validator_initialization():
    """Test input validator initialization"""
    validator = InputValidator()
    assert validator is not None
    assert len(validator.job_role_mappings) > 0
    assert len(validator.location_mappings) > 0


def test_validate_job_role_valid():
    """Test validation of valid job roles"""
    validator = InputValidator()
    
    # Test valid job role
    is_valid, normalized_role, error = validator.validate_job_role("software engineer")
    assert is_valid is True
    assert normalized_role == "Software Engineer"
    assert error is None
    
    # Test another valid job role
    is_valid, normalized_role, error = validator.validate_job_role("data scientist")
    assert is_valid is True
    assert error is None


def test_validate_job_role_empty():
    """Test validation of empty job role"""
    validator = InputValidator()
    
    is_valid, normalized_role, error = validator.validate_job_role("")
    assert is_valid is False
    assert normalized_role == ""
    assert error is not None
    
    is_valid, normalized_role, error = validator.validate_job_role("   ")
    assert is_valid is False
    assert error is not None


def test_validate_job_role_normalization():
    """Test job role normalization"""
    validator = InputValidator()
    
    # Test common variations
    is_valid, normalized_role, error = validator.validate_job_role("sw engineer")
    assert is_valid is True
    assert normalized_role == "Software Engineer"
    
    is_valid, normalized_role, error = validator.validate_job_role("swe")
    assert is_valid is True
    assert normalized_role == "Software Engineer"


def test_validate_location_valid():
    """Test validation of valid locations"""
    validator = InputValidator()
    
    # Test valid location
    is_valid, normalized_location, error = validator.validate_location("remote")
    assert is_valid is True
    assert normalized_location == "Remote"
    assert error is None
    
    # Test another valid location
    is_valid, normalized_location, error = validator.validate_location("bengaluru")
    assert is_valid is True
    assert error is None


def test_validate_location_empty():
    """Test validation of empty location"""
    validator = InputValidator()
    
    is_valid, normalized_location, error = validator.validate_location("")
    assert is_valid is False
    assert normalized_location == ""
    assert error is not None


def test_validate_location_normalization():
    """Test location normalization"""
    validator = InputValidator()
    
    # Test common variations
    is_valid, normalized_location, error = validator.validate_location("blr")
    assert is_valid is True
    assert normalized_location == "Bengaluru"
    
    is_valid, normalized_location, error = validator.validate_location("bangalore")
    assert is_valid is True
    assert normalized_location == "Bengaluru"
    
    is_valid, normalized_location, error = validator.validate_location("wfh")
    assert is_valid is True
    assert normalized_location == "Remote"


def test_validate_user_input_valid():
    """Test validation of complete user input"""
    validator = InputValidator()
    
    is_valid, normalized_inputs, errors = validator.validate_user_input("software engineer", "remote")
    
    assert is_valid is True
    assert normalized_inputs['job_role'] == "Software Engineer"
    assert normalized_inputs['location'] == "Remote"
    assert len(errors) == 0


def test_validate_user_input_invalid():
    """Test validation of invalid user input"""
    validator = InputValidator()
    
    is_valid, normalized_inputs, errors = validator.validate_user_input("", "")
    
    assert is_valid is False
    assert len(errors) > 0
    assert len(normalized_inputs) == 0


def test_get_common_job_roles():
    """Test getting common job roles"""
    validator = InputValidator()
    
    roles = validator.get_common_job_roles()
    assert len(roles) > 0
    assert "software engineer" in roles
    assert "data scientist" in roles


def test_get_common_locations():
    """Test getting common locations"""
    validator = InputValidator()
    
    locations = validator.get_common_locations()
    assert len(locations) > 0
    assert "remote" in locations
    assert "bengaluru" in locations


def test_suggest_job_role_corrections():
    """Test job role correction suggestions"""
    validator = InputValidator()
    
    # Test with misspelled job role
    suggestions = validator.suggest_job_role_corrections("softwar engineer")
    assert isinstance(suggestions, list)
    
    # Test with correct job role
    suggestions = validator.suggest_job_role_corrections("software engineer")
    assert isinstance(suggestions, list)


def test_format_input_summary():
    """Test input summary formatting"""
    validator = InputValidator()
    
    summary = validator.format_input_summary("software engineer", "remote")
    assert "software engineer" in summary.lower()
    assert "remote" in summary.lower()
    assert "job role" in summary.lower()
    assert "location" in summary.lower()
