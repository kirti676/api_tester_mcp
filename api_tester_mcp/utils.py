"""Utility functions for the API Tester MCP server"""

import uuid
import json
import logging
from typing import Dict, Any, Optional
from faker import Faker
import re


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker for test data generation
fake = Faker()


def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def validate_json(content: str) -> bool:
    """Validate if content is valid JSON"""
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError:
        return False


def validate_spec_type(content: str) -> Optional[str]:
    """Detect and validate specification type"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        try:
            import yaml
            data = yaml.safe_load(content)
        except:
            return None
    
    if not isinstance(data, dict):
        return None
    
    # Check for OpenAPI/Swagger
    if "openapi" in data or "swagger" in data:
        return "openapi"
    
    # Check for Postman collection
    if "info" in data and "item" in data and data.get("info", {}).get("schema"):
        if "postman" in data["info"]["schema"].lower():
            return "postman"
    
    return None


def generate_test_data(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate test data from JSON schema"""
    if not schema or not isinstance(schema, dict):
        return {}
    
    schema_type = schema.get("type", "object")
    
    if schema_type == "object":
        return _generate_object_data(schema)
    elif schema_type == "array":
        return _generate_array_data(schema)
    elif schema_type == "string":
        return _generate_string_data(schema)
    elif schema_type == "integer":
        return _generate_integer_data(schema)
    elif schema_type == "number":
        return _generate_number_data(schema)
    elif schema_type == "boolean":
        return fake.boolean()
    else:
        return {}


def _generate_object_data(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate object data from schema"""
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    result = {}
    
    for prop_name, prop_schema in properties.items():
        if prop_name in required or fake.boolean():
            result[prop_name] = generate_test_data(prop_schema)
    
    # Use example if provided
    if "example" in schema:
        return schema["example"]
    
    return result


def _generate_array_data(schema: Dict[str, Any]) -> list:
    """Generate array data from schema"""
    items_schema = schema.get("items", {})
    min_items = schema.get("minItems", 1)
    max_items = schema.get("maxItems", 3)
    
    count = fake.random_int(min=min_items, max=max_items)
    return [generate_test_data(items_schema) for _ in range(count)]


def _generate_string_data(schema: Dict[str, Any]) -> str:
    """Generate string data from schema"""
    # Use example if provided
    if "example" in schema:
        return schema["example"]
    
    # Use enum if provided
    if "enum" in schema:
        return fake.random_element(schema["enum"])
    
    # Use format-specific generation
    format_type = schema.get("format", "")
    
    if format_type == "email":
        return fake.email()
    elif format_type == "uuid":
        return str(uuid.uuid4())
    elif format_type == "date":
        return fake.date().isoformat()
    elif format_type == "date-time":
        return fake.date_time().isoformat()
    elif format_type == "uri":
        return fake.url()
    elif format_type == "password":
        return fake.password()
    
    # Use pattern if provided
    if "pattern" in schema:
        try:
            from exrex import getone
            return getone(schema["pattern"])
        except:
            pass
    
    # Default string generation
    min_length = schema.get("minLength", 5)
    max_length = schema.get("maxLength", 20)
    
    return fake.text(max_nb_chars=min(max_length, 50))[:max_length]


def _generate_integer_data(schema: Dict[str, Any]) -> int:
    """Generate integer data from schema"""
    # Use example if provided
    if "example" in schema:
        return schema["example"]
    
    minimum = schema.get("minimum", 1)
    maximum = schema.get("maximum", 1000)
    
    return fake.random_int(min=minimum, max=maximum)


def _generate_number_data(schema: Dict[str, Any]) -> float:
    """Generate number data from schema"""
    # Use example if provided
    if "example" in schema:
        return schema["example"]
    
    minimum = schema.get("minimum", 1.0)
    maximum = schema.get("maximum", 1000.0)
    
    return fake.random.uniform(minimum, maximum)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system storage"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized or "untitled"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


class ProgressTracker:
    """Track progress of long-running operations"""
    
    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.start_time = None
        
    def start(self):
        """Start tracking progress"""
        import time
        self.start_time = time.time()
        logger.info(f"Starting {self.operation_name} with {self.total_steps} steps")
    
    def update(self, step_name: str = None):
        """Update progress"""
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        
        message = f"{self.operation_name}: {self.current_step}/{self.total_steps} ({percentage:.1f}%)"
        if step_name:
            message += f" - {step_name}"
        
        logger.info(message)
    
    def finish(self):
        """Finish tracking"""
        if self.start_time:
            import time
            duration = time.time() - self.start_time
            logger.info(f"{self.operation_name} completed in {format_duration(duration)}")


def merge_env_vars(base_vars: Dict[str, str], new_vars: Dict[str, str]) -> Dict[str, str]:
    """Merge environment variables"""
    merged = base_vars.copy()
    merged.update(new_vars)
    return merged


def validate_url(url: str) -> bool:
    """Validate if string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def extract_error_details(error: Exception) -> Dict[str, Any]:
    """Extract detailed error information"""
    return {
        "type": type(error).__name__,
        "message": str(error),
        "module": getattr(error, "__module__", None)
    }
