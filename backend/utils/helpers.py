"""
Helper utilities for common operations.
"""

from typing import Any, Dict, List
from datetime import datetime, date
import json
import hashlib
from loguru import logger


def parse_json_markdown(text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from markdown text.
    """
    try:
        # Try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON block
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find anything between the first { and the last }
        # This handles conversational text before/after the JSON
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                content = text[start_idx:end_idx + 1]
                return json.loads(content)
            except json.JSONDecodeError:
                pass
        
        # Log failure and return empty
        logger.error(f"Failed to parse JSON. Raw response start: {text[:200]}...")
        return {}


def serialize_datetime(obj: Any) -> str:
    """
    Serialize datetime objects to ISO format strings.
    
    Args:
        obj: Object to serialize
    
    Returns:
        ISO format string
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def safe_json_dumps(data: Any) -> str:
    """
    Safely serialize data to JSON string.
    
    Args:
        data: Data to serialize
    
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, default=serialize_datetime)
    except Exception as e:
        logger.error(f"Error serializing to JSON: {str(e)}")
        return "{}"


def safe_json_loads(json_str: str) -> Any:
    """
    Safely deserialize JSON string.
    
    Args:
        json_str: JSON string
    
    Returns:
        Deserialized data or empty dict on error
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error deserializing JSON: {str(e)}")
        return {}


def generate_hash(content: str) -> str:
    """
    Generate SHA-256 hash of content.
    
    Args:
        content: Content to hash
    
    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(content.encode()).hexdigest()


def paginate_results(
    items: List[Any],
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Paginated results with metadata
    """
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        "items": items[start_idx:end_idx],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage safely.
    
    Args:
        part: Part value
        total: Total value
    
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def format_time_duration(seconds: float) -> str:
    """
    Format time duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address
    
    Returns:
        True if email format is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input."""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    dangerous_chars = ['<', '>', '"', "'", '&']
    for char in dangerous_chars:
        text = text.replace(char, '')
    return text


def sanitize_jailbreak(text: str) -> str:
    """
    Neutralize keywords that trigger Azure jailbreak/safety filters
    by inserting zero-width spaces into them.
    """
    if not text:
        return ""
    
    keywords = [
        "system prompt", "ignore previous", "you are now", "acting as",
        "strictly follow", "forget everything", "bypass", "root access",
        "instruction extraction", "ignore all instructions"
    ]
    import re
    for kw in keywords:
        # Breakdown into char + zero-width-space + rest
        replacement = f"{kw[0]}\u200b{kw[1:]}"
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        text = pattern.sub(replacement, text)
    return text


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
    
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def get_error_response(
    message: str,
    detail: Any = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        detail: Optional error details
        status_code: HTTP status code
    
    Returns:
        Error response dictionary
    """
    response = {
        "error": True,
        "message": message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if detail:
        response["detail"] = detail
    
    return response


def get_success_response(
    message: str,
    data: Any = None
) -> Dict[str, Any]:
    """
    Create standardized success response.
    
    Args:
        message: Success message
        data: Optional response data
    
    Returns:
        Success response dictionary
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response
