"""Helper utilities for the browser agent."""

import json
import csv
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize URL.
    
    Args:
        url: URL to normalize
        base_url: Optional base URL for relative URLs
        
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    # Handle relative URLs
    if base_url and not url.startswith(('http://', 'https://')):
        return urljoin(base_url, url)
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    return url


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


def save_to_json(data: Any, filepath: Union[str, Path]) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def load_from_json(filepath: Union[str, Path]) -> Any:
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_to_csv(data: List[Dict[str, Any]], filepath: Union[str, Path]) -> None:
    """
    Save data to CSV file.
    
    Args:
        data: List of dictionaries to save
        filepath: Path to save file
    """
    if not data:
        return
    
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    keys = data[0].keys()
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text.strip()


def extract_numbers(text: str) -> List[float]:
    """
    Extract numbers from text.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of extracted numbers
    """
    if not text:
        return []
    
    # Find all numbers (including decimals)
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            num = float(match)
            numbers.append(num)
        except ValueError:
            continue
    
    return numbers


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime as ISO timestamp.
    
    Args:
        dt: Datetime to format (defaults to current time)
        
    Returns:
        Formatted timestamp
    """
    if dt is None:
        dt = datetime.utcnow()
    
    return dt.isoformat() + 'Z'


def parse_selector(selector: str) -> Dict[str, str]:
    """
    Parse CSS selector into components.
    
    Args:
        selector: CSS selector
        
    Returns:
        Dictionary with selector components
    """
    components = {
        "type": "css",
        "value": selector,
        "tag": None,
        "id": None,
        "classes": [],
        "attributes": {}
    }
    
    # Extract ID
    id_match = re.search(r'#([\w-]+)', selector)
    if id_match:
        components["id"] = id_match.group(1)
    
    # Extract classes
    class_matches = re.findall(r'\.([\w-]+)', selector)
    if class_matches:
        components["classes"] = class_matches
    
    # Extract tag
    tag_match = re.match(r'^([\w]+)', selector)
    if tag_match:
        components["tag"] = tag_match.group(1)
    
    return components


def retry_on_exception(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on exception.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch
    """
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue
            
            raise last_exception
        
        return wrapper
    
    return decorator


def batch_process(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split items into batches.
    
    Args:
        items: List of items to batch
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    batches = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)
    
    return batches


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to get value from
        path: Dot-separated path to value
        default: Default value if not found
        
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current