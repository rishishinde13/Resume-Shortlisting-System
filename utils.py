import re
import os
from typing import Optional, Dict, Any
import tempfile
from datetime import datetime

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it has reasonable length (10-15 digits)
    return 10 <= len(digits_only) <= 15

def format_phone(phone: str) -> str:
    """
    Format phone number consistently
    
    Args:
        phone: Raw phone number
        
    Returns:
        Formatted phone number
    """
    if not phone:
        return ""
    
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format

def clean_filename(filename: str) -> str:
    """
    Clean filename for safe file operations
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    if not filename:
        return "unknown_file"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace unsafe characters
    safe_chars = re.sub(r'[^\w\s\-_\.]', '_', filename)
    
    # Remove multiple spaces/underscores
    cleaned = re.sub(r'[\s_]+', '_', safe_chars)
    
    return cleaned.strip('_')

def save_temp_file(content: bytes, suffix: str = ".pdf") -> str:
    """
    Save content to a temporary file
    
    Args:
        content: File content as bytes
        suffix: File extension
        
    Returns:
        Path to temporary file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        return temp_file.name

def delete_file_safely(file_path: str) -> bool:
    """
    Safely delete a file
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False

def format_date(date_str: str) -> str:
    """
    Format date string consistently
    
    Args:
        date_str: Date string to format
        
    Returns:
        Formatted date string
    """
    try:
        # Try to parse common date formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        return date_str  # Return original if can't parse
    except Exception:
        return date_str

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_numbers(text: str) -> list:
    """
    Extract all numbers from text
    
    Args:
        text: Text to search
        
    Returns:
        List of numbers found
    """
    if not text:
        return []
    
    # Find all number patterns (integers and floats)
    numbers = re.findall(r'\b\d+\.?\d*\b', text)
    
    # Convert to appropriate numeric types
    result = []
    for num in numbers:
        try:
            if '.' in num:
                result.append(float(num))
            else:
                result.append(int(num))
        except ValueError:
            continue
    
    return result

def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill names for consistent storage
    
    Args:
        skill: Raw skill name
        
    Returns:
        Normalized skill name
    """
    if not skill:
        return ""
    
    # Convert to title case
    normalized = skill.strip().title()
    
    # Handle special cases
    special_cases = {
        'Javascript': 'JavaScript',
        'Nodejs': 'Node.js',
        'Reactjs': 'React.js',
        'Vuejs': 'Vue.js',
        'Angularjs': 'Angular.js',
        'Css': 'CSS',
        'Html': 'HTML',
        'Sql': 'SQL',
        'Api': 'API',
        'Rest': 'REST',
        'Json': 'JSON',
        'Xml': 'XML',
        'Aws': 'AWS',
        'Gcp': 'GCP'
    }
    
    return special_cases.get(normalized, normalized)

def calculate_experience_level(years: int) -> str:
    """
    Calculate experience level based on years
    
    Args:
        years: Years of experience
        
    Returns:
        Experience level string
    """
    if years < 0:
        return "Unknown"
    elif years == 0:
        return "Entry Level"
    elif years <= 2:
        return "Junior"
    elif years <= 5:
        return "Mid Level"
    elif years <= 10:
        return "Senior"
    else:
        return "Expert"

def get_file_size_mb(content: bytes) -> float:
    """
    Get file size in MB
    
    Args:
        content: File content as bytes
        
    Returns:
        File size in MB
    """
    return len(content) / (1024 * 1024)

def validate_pdf_size(content: bytes, max_size_mb: float = 10.0) -> bool:
    """
    Validate PDF file size
    
    Args:
        content: PDF content as bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        True if size is valid, False otherwise
    """
    size_mb = get_file_size_mb(content)
    return size_mb <= max_size_mb

def create_candidate_summary(candidate: Dict[str, Any]) -> str:
    """
    Create a summary string for a candidate
    
    Args:
        candidate: Candidate dictionary
        
    Returns:
        Summary string
    """
    name = candidate.get('full_name', 'Unknown')
    experience = candidate.get('experience_years', 0)
    status = candidate.get('status', 'unknown')
    
    exp_level = calculate_experience_level(experience)
    
    return f"{name} - {exp_level} ({experience} years) - Status: {status.title()}"

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent issues
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potential script tags and other dangerous content
    sanitized = re.sub(r'<[^>]*>', '', text)
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    return sanitized.strip()
