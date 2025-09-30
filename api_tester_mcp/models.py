"""Configuration and data models for the API Tester MCP server"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class SpecType(str, Enum):
    """Supported specification types"""
    OPENAPI = "openapi"
    SWAGGER = "swagger"
    POSTMAN = "postman"


class StatusType(str, Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestLanguage(str, Enum):
    """Supported test languages"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"


class TestFramework(str, Enum):
    """Supported test frameworks"""
    # Python frameworks
    PYTEST = "pytest"
    REQUESTS = "requests"
    
    # TypeScript/JavaScript frameworks
    PLAYWRIGHT = "playwright"
    JEST = "jest"
    SUPERTEST = "supertest"
    CYPRESS = "cypress"


class ApiEndpoint(BaseModel):
    """API endpoint representation"""
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    auth_required: bool = False


class TestScenario(BaseModel):
    """Test scenario representation"""
    id: str
    name: str
    objective: str
    endpoint: ApiEndpoint
    steps: List[str]
    expected_outcome: str
    pass_criteria: List[str]
    fail_criteria: List[str]
    test_data: Optional[Dict[str, Any]] = None
    assertions: List[Dict[str, Any]] = Field(default_factory=list)


class TestCase(BaseModel):
    """Executable test case"""
    id: str
    scenario_id: str
    name: str
    method: str
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Union[str, Dict[str, Any]]] = None
    expected_status: int = 200
    assertions: List[Dict[str, Any]] = Field(default_factory=list)
    timeout: int = 30
    language: TestLanguage = TestLanguage.PYTHON
    framework: TestFramework = TestFramework.REQUESTS
    generated_code: Optional[str] = None  # Generated test code in selected language/framework


class TestResult(BaseModel):
    """Test execution result"""
    test_case_id: str
    status: str
    execution_time: float
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    response_headers: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_details: List[Dict[str, Any]] = Field(default_factory=list)


class TestSession(BaseModel):
    """Test session information"""
    id: str
    spec_type: SpecType
    spec_content: Dict[str, Any]
    scenarios: List[TestScenario] = Field(default_factory=list)
    test_cases: List[TestCase] = Field(default_factory=list)
    env_vars: Dict[str, str] = Field(default_factory=dict)
    status: StatusType = StatusType.PENDING
    created_at: str
    completed_at: Optional[str] = None
    preferred_language: TestLanguage = TestLanguage.PYTHON
    preferred_framework: TestFramework = TestFramework.REQUESTS
