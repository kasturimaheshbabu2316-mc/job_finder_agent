"""
Input validation and preprocessing for exact user input
"""

from typing import Tuple, Optional, List
import re
from ..utils.logger import get_logger


class InputValidator:
    """
    Validates and preprocesses exact user input for job role and location
    """
    
    def __init__(self):
        self.logger = get_logger("input_validator")
        
        # Common job role variations for normalization
        self.job_role_mappings = {
            'sw engineer': 'software engineer',
            'sw eng': 'software engineer',
            'swe': 'software engineer',
            'dev': 'developer',
            'web dev': 'web developer',
            'full stack': 'full stack developer',
            'fullstack': 'full stack developer',
            'ml engineer': 'machine learning engineer',
            'ml eng': 'machine learning engineer',
            'data science': 'data scientist',
            'data sci': 'data scientist',
        }
        
        # Common location variations for normalization
        self.location_mappings = {
            'blr': 'bengaluru',
            'bangalore': 'bengaluru',
            'blore': 'bengaluru',
            'mum': 'mumbai',
            'bombay': 'mumbai',
            'ny': 'new york',
            'nyc': 'new york',
            'sf': 'san francisco',
            'wfh': 'remote',
            'work from home': 'remote',
        }
        
        # Valid job role patterns
        self.valid_job_role_patterns = [
            r'.*engineer.*',
            r'.*developer.*',
            r'.*scientist.*',
            r'.*analyst.*',
            r'.*manager.*',
            r'.*architect.*',
            r'.*designer.*',
            r'.*consultant.*',
            r'.*specialist.*',
            r'.*coordinator.*',
        ]
    
    def validate_job_role(self, job_role: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate and normalize exact job role input
        
        Args:
            job_role: Raw job role input from user
        
        Returns:
            Tuple of (is_valid, normalized_role, error_message)
        """
        if not job_role or not job_role.strip():
            return False, "", "Job role cannot be empty"
        
        # Clean the input
        job_role = job_role.strip().lower()
        
        # Normalize common variations
        for variation, standard in self.job_role_mappings.items():
            if variation == job_role:
                job_role = standard
                break
        
        # Check if it matches a valid job role pattern
        is_valid_pattern = any(
            re.match(pattern, job_role, re.IGNORECASE) 
            for pattern in self.valid_job_role_patterns
        )
        
        if not is_valid_pattern:
            # If it doesn't match patterns, still accept it but warn
            self.logger.warning(f"Job role '{job_role}' doesn't match common patterns, accepting anyway")
        
        # Capitalize properly
        normalized_role = ' '.join(word.capitalize() for word in job_role.split())
        
        return True, normalized_role, None
    
    def validate_location(self, location: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate and normalize exact location input
        
        Args:
            location: Raw location input from user
        
        Returns:
            Tuple of (is_valid, normalized_location, error_message)
        """
        if not location or not location.strip():
            return False, "", "Location cannot be empty"
        
        # Clean the input
        location = location.strip().lower()
        
        # Normalize common variations
        for variation, standard in self.location_mappings.items():
            if variation == location:
                location = standard
                break
        
        # Capitalize properly
        normalized_location = location.title()
        
        return True, normalized_location, None
    
    def validate_user_input(self, job_role: str, location: str) -> Tuple[bool, dict, List[str]]:
        """
        Validate both job role and location inputs together
        
        Args:
            job_role: Raw job role input from user
            location: Raw location input from user
        
        Returns:
            Tuple of (is_valid, normalized_inputs, error_messages)
        """
        errors = []
        normalized_inputs = {}
        
        # Validate job role
        is_valid_role, normalized_role, role_error = self.validate_job_role(job_role)
        if not is_valid_role:
            errors.append(role_error)
        else:
            normalized_inputs['job_role'] = normalized_role
        
        # Validate location
        is_valid_location, normalized_location, location_error = self.validate_location(location)
        if not is_valid_location:
            errors.append(location_error)
        else:
            normalized_inputs['location'] = normalized_location
        
        is_valid = len(errors) == 0
        
        return is_valid, normalized_inputs, errors
    
    def get_common_job_roles(self) -> List[str]:
        """Get list of common job roles for suggestions"""
        return [
            "software engineer",
            "data scientist",
            "machine learning engineer",
            "frontend developer",
            "backend developer",
            "full stack developer",
            "devops engineer",
            "product manager",
            "ux designer",
            "qa engineer",
        ]
    
    def get_common_locations(self) -> List[str]:
        """Get list of common locations for suggestions"""
        return [
            "remote",
            "bengaluru",
            "mumbai",
            "delhi",
            "pune",
            "hyderabad",
            "chennai",
            "new york",
            "san francisco",
            "london",
        ]
    
    def suggest_job_role_corrections(self, job_role: str) -> List[str]:
        """
        Suggest corrections for potentially misspelled job roles
        
        Args:
            job_role: Raw job role input
        
        Returns:
            List of suggested corrections
        """
        suggestions = []
        job_role_lower = job_role.lower().strip()
        
        for common_role in self.get_common_job_roles():
            # Simple similarity check
            if job_role_lower in common_role or common_role in job_role_lower:
                if common_role != job_role_lower:
                    suggestions.append(common_role)
        
        return suggestions
    
    def format_input_summary(self, job_role: str, location: str) -> str:
        """
        Format a summary of the user input for logging/display
        
        Args:
            job_role: Job role input
            location: Location input
        
        Returns:
            Formatted summary string
        """
        return f"Job Role: '{job_role}' | Location: '{location}'"