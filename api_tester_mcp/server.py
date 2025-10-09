"""Main MCP server implementation using FastMCP"""

import json
import yaml
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastmcp import FastMCP
from fastmcp.prompts import Prompt
from fastmcp.resources import Resource
from pydantic import BaseModel

from .models import (
    SpecType, TestSession, TestScenario, TestCase, TestResult,
    StatusType, TestLanguage, TestFramework
)
from .parsers import SpecificationParser, ScenarioGenerator, analyze_required_env_vars
from .test_execution import TestCaseGenerator, TestExecutor, LoadTestExecutor
from .reports import ReportGenerator
from .code_generators import get_supported_combinations, generate_package_files
from .utils import (
    generate_id, validate_spec_type, logger, ProgressTracker,
    merge_env_vars, validate_url, extract_error_details
)

# Initialize FastMCP server
mcp = FastMCP("API Tester MCP")

# Global state
current_session: Optional[TestSession] = None
test_results: List[TestResult] = []
load_test_results: Dict[str, Any] = {}
report_generator = ReportGenerator()
ingested_file_directory: Optional[str] = None  # Directory of the ingested API specification file

def set_workspace_directory(file_path: Optional[str] = None) -> str:
    """
    Set the workspace directory based on a file path or reset to default behavior.
    
    Args:
        file_path: Path to a file whose directory should be used as workspace, or None to reset
    
    Returns:
        The selected workspace directory
    """
    global ingested_file_directory
    
    if file_path and os.path.exists(file_path):
        ingested_file_directory = os.path.dirname(os.path.abspath(file_path))
        logger.info(f"Workspace directory set to: {ingested_file_directory}")
    else:
        ingested_file_directory = None
        logger.info("Workspace directory reset to default behavior")
    
    return get_workspace_dir()

def reset_workspace_directory():
    """Reset workspace directory to default behavior (ignore ingested file directory)."""
    global ingested_file_directory
    ingested_file_directory = None
    logger.info("Workspace directory reset to default behavior")

# Get the workspace directory (current working directory where VS Code is running)
def get_workspace_dir() -> str:
    """
    Get the current workspace directory with multiple fallback strategies.
    Prioritizes the directory of the ingested API specification file if available.
    This ensures the function works across different environments and workspace configurations.
    """
    global ingested_file_directory
    
    # Strategy 0: Use the directory of the ingested API specification file (highest priority)
    workspace_candidates = []
    if ingested_file_directory:
        workspace_candidates.append(ingested_file_directory)
        logger.info(f"Prioritizing ingested file directory: {ingested_file_directory}")
    
    # Strategy 1: Environment variables (VS Code and other IDEs set these)
    workspace_candidates.extend([
        os.environ.get('PWD'),
        os.environ.get('WORKSPACE_DIR'),
        os.environ.get('VSCODE_CWD'),
        os.environ.get('INIT_CWD')
    ])
    
    # Strategy 2: Current working directory
    workspace_candidates.append(os.getcwd())
    
    # Strategy 3: Python script directory (if running from a specific location)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up directories to find a potential workspace root
        potential_workspace = script_dir
        for _ in range(3):  # Check up to 3 levels up
            if any(os.path.exists(os.path.join(potential_workspace, indicator)) 
                  for indicator in ['.git', '.vscode', 'package.json', 'requirements.txt', 'pyproject.toml']):
                workspace_candidates.append(potential_workspace)
                break
            potential_workspace = os.path.dirname(potential_workspace)
    except Exception:
        pass
    
    # Select the first valid directory that exists and is writable
    for candidate in workspace_candidates:
        if candidate and os.path.exists(candidate) and os.path.isdir(candidate):
            try:
                # Test if directory is writable
                test_file = os.path.join(candidate, '.mcp_test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info(f"Selected workspace directory: {candidate}")
                return candidate
            except Exception:
                continue
    
    # Final fallback: use current directory even if not writable
    fallback = os.getcwd()
    logger.warning(f"Using fallback workspace directory (may not be writable): {fallback}")
    return fallback

def get_or_create_project_dir() -> str:
    """Get current working directory - always use workspace for generated files"""
    workspace_dir = get_workspace_dir()
    
    # Always use the workspace directory directly
    if os.access(workspace_dir, os.W_OK):
        logger.info(f"Using workspace directory: {workspace_dir}")
        return workspace_dir
    else:
        logger.warning(f"Workspace directory not writable, using anyway: {workspace_dir}")
        return workspace_dir

def ensure_workspace_output_dir(subdir: str) -> str:
    """
    Ensure a specific output subdirectory exists in the workspace.
    Creates the directory structure as needed.
    
    Args:
        subdir: The subdirectory name (e.g., 'scenarios', 'test_cases', 'reports')
    
    Returns:
        Full path to the created subdirectory
    """
    workspace_dir = get_workspace_dir()
    
    # Try different output directory patterns commonly used
    possible_output_dirs = [
        "output",           # Standard output dir
        "generated",        # Alternative name
        "api-test-output",  # Descriptive name
        "mcp-output"        # MCP-specific name
    ]
    
    output_base = None
    
    # Check if any standard output directory already exists
    for output_dir_name in possible_output_dirs:
        potential_output = os.path.join(workspace_dir, output_dir_name)
        if os.path.exists(potential_output) and os.path.isdir(potential_output):
            output_base = potential_output
            logger.info(f"Found existing output directory: {output_base}")
            break
    
    # If no existing output directory found, create the default one
    if output_base is None:
        output_base = os.path.join(workspace_dir, "output")
        logger.info(f"Creating new output directory: {output_base}")
    
    # Create the specific subdirectory
    target_dir = os.path.join(output_base, subdir)
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Created/verified directory: {target_dir}")
        return target_dir
    except Exception as e:
        # Fallback: create directly in workspace if output directory creation fails
        logger.warning(f"Failed to create {target_dir}, falling back to workspace subdirectory: {str(e)}")
        fallback_dir = os.path.join(workspace_dir, f"api-test-{subdir}")
        try:
            os.makedirs(fallback_dir, exist_ok=True)
            logger.info(f"Created fallback directory: {fallback_dir}")
            return fallback_dir
        except Exception as e2:
            # Last resort: use workspace directory directly
            logger.error(f"Failed to create fallback directory, using workspace directly: {str(e2)}")
            return workspace_dir

# Legacy function for compatibility - now dynamically ensures directories
def ensure_output_directories():
    """Create output directories in the current workspace (legacy compatibility)"""
    workspace_dir = get_workspace_dir()
    
    # Use the new dynamic approach for each subdirectory
    subdirs = ["reports", "scenarios", "test_cases", "generated_projects"]
    created_dirs = {}
    
    for subdir in subdirs:
        created_dirs[subdir] = ensure_workspace_output_dir(subdir)
    
    # Return the base output directory (parent of the first created directory)
    first_dir = list(created_dirs.values())[0]
    output_base = os.path.dirname(first_dir)
    
    logger.info(f"Output base directory: {output_base}")
    logger.info(f"Created subdirectories: {created_dirs}")
    
    return output_base

# Utility function to check directory permissions
def check_directory_access(directory_path: str) -> Dict[str, Any]:
    """Check if directory exists and is writable"""
    try:
        # Check if directory exists
        exists = os.path.exists(directory_path)
        
        # Check if we can write to it
        writable = False
        if exists:
            writable = os.access(directory_path, os.W_OK)
        
        # Try to create a test file if writable
        test_file_created = False
        if writable:
            try:
                test_file = os.path.join(directory_path, ".test_write_access")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                test_file_created = True
            except Exception:
                pass
        
        return {
            "exists": exists,
            "writable": writable,
            "test_file_created": test_file_created,
            "path": directory_path,
            "absolute_path": os.path.abspath(directory_path)
        }
    except Exception as e:
        return {
            "exists": False,
            "writable": False,
            "test_file_created": False,
            "path": directory_path,
            "error": str(e)
        }

# Initialize output directories (legacy compatibility)
OUTPUT_BASE_DIR = ensure_output_directories()


# Pydantic models for tool parameters
class IngestSpecParams(BaseModel):
    spec_type: Optional[str] = "openapi"  # openapi, swagger, postman
    file_path: str  # Path to the API specification file (JSON or YAML)
    preferred_language: Optional[str] = "python"  # python, typescript, javascript  
    preferred_framework: Optional[str] = "requests"  # pytest, requests, playwright, jest, cypress, supertest


class SetEnvVarsParams(BaseModel):
    variables: Dict[str, str] = {}
    
    # Optional convenience fields that get merged into variables if provided
    baseUrl: Optional[str] = None
    auth_bearer: Optional[str] = None
    auth_apikey: Optional[str] = None
    auth_basic: Optional[str] = None
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None


class GenerateScenariosParams(BaseModel):
    include_negative_tests: bool = True  # Generate failure scenarios (invalid data, unauthorized access)
    include_edge_cases: bool = True  # Generate boundary and edge case scenarios


class GenerateTestCasesParams(BaseModel):
    scenario_ids: Optional[List[str]] = None


class RunApiTestsParams(BaseModel):
    test_case_ids: Optional[List[str]] = None  # ["test_case_1", "test_case_2"] or None for all
    max_concurrent: int = 10  # Number of concurrent requests (1-50)


class RunLoadTestsParams(BaseModel):
    test_case_ids: Optional[List[str]] = None  # ["test_case_1", "test_case_2"] or None for all
    duration: int = 60  # Test duration in seconds
    users: int = 10  # Number of concurrent virtual users
    ramp_up: int = 10  # Ramp up time in seconds


# MCP Tools
@mcp.tool()
async def ingest_spec(params: IngestSpecParams) -> Dict[str, Any]:
    """
    Ingest an API specification (OpenAPI/Swagger or Postman collection) from a file.
    Automatically analyzes the specification and suggests required environment variables.
    
    Args:
        spec_type: Type of specification ('openapi', 'swagger', or 'postman'). 
                  If not provided, the function will attempt to auto-detect from the file content.
        file_path: Path to the API specification file (JSON or YAML format).
                  Can be absolute or relative path. The file must exist and be readable.
        preferred_language: Preferred programming language for test generation (python, typescript, javascript)
        preferred_framework: Preferred testing framework (pytest, playwright, jest, etc.)
    
    Returns:
        Dictionary with ingestion results, session information, and environment variable analysis.
        Includes the original file path in the 'spec_file_path' field for reference.
        
    Raises:
        Returns error dictionary if file doesn't exist, can't be read, or has invalid format.
    """
    global current_session, ingested_file_directory
    
    try:
        # Log provided parameters
        logger.info(f"Ingesting specification - file_path: {params.file_path}, "
                   f"spec_type: {params.spec_type}, "
                   f"preferred_language: {params.preferred_language}, "
                   f"preferred_framework: {params.preferred_framework}")
        
        # Check if file exists
        if not os.path.exists(params.file_path):
            return {
                "success": False,
                "error": f"Specification file not found: {params.file_path}"
            }
        
        # Read file content
        try:
            with open(params.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f"Successfully read specification file: {params.file_path}")
            
            # Capture the directory of the ingested file to use as workspace directory
            ingested_file_directory = os.path.dirname(os.path.abspath(params.file_path))
            logger.info(f"Set workspace directory to ingested file location: {ingested_file_directory}")
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read specification file {params.file_path}: {str(e)}"
            }
        
        # Use provided spec_type or auto-detect
        spec_type_to_use = params.spec_type or "openapi"
        
        # Auto-detect spec type if needed or validate provided type
        detected_type = validate_spec_type(content)
        if detected_type:
            if params.spec_type and detected_type != params.spec_type.lower():
                logger.warning(f"Detected spec type '{detected_type}' differs from provided '{params.spec_type}', using detected type")
            spec_type_to_use = detected_type
        
        # Validate final spec type
        if spec_type_to_use.lower() not in ['openapi', 'swagger', 'postman']:
            return {
                "success": False,
                "error": f"Unsupported specification type: {spec_type_to_use}. Supported types: openapi, swagger, postman"
            }
        
        # Parse specification
        parser = SpecificationParser()
        spec_type = SpecType(spec_type_to_use.lower())
        endpoints = parser.parse(content, spec_type)
        
        if not endpoints:
            return {
                "success": False,
                "error": "No API endpoints found in the specification"
            }
        
        # Analyze required environment variables
        spec_data = json.loads(content) if content.strip().startswith('{') else yaml.safe_load(content)
        env_analysis = analyze_required_env_vars(spec_data, spec_type, parser.base_url)
        
        # Parse language and framework preferences
        preferred_language = TestLanguage.PYTHON  # default
        if params.preferred_language:
            try:
                preferred_language = TestLanguage(params.preferred_language.lower())
            except ValueError:
                logger.warning(f"Invalid language '{params.preferred_language}', using default: python")
            
        preferred_framework = TestFramework.REQUESTS  # default
        if params.preferred_framework:
            try:
                preferred_framework = TestFramework(params.preferred_framework.lower())
            except ValueError:
                logger.warning(f"Invalid framework '{params.preferred_framework}', using default: requests")

        # Create new session
        session_id = generate_id()
        current_session = TestSession(
            id=session_id,
            spec_type=spec_type,
            spec_content=spec_data,
            created_at=datetime.now().isoformat(),
            preferred_language=preferred_language,
            preferred_framework=preferred_framework
        )
        
        logger.info(f"Created new session {session_id} with {len(endpoints)} endpoints")
        
        # Generate helpful message about environment variables
        env_message = []
        required_vars = env_analysis.get("required_variables", {})
        if required_vars:
            env_message.append(f"⚠️  {len(required_vars)} required environment variable(s) detected:")
            for var_name, var_info in required_vars.items():
                if "detected_value" in var_info:
                    env_message.append(f"   • {var_name}: {var_info['description']} (Suggested: {var_info['detected_value']})")
                else:
                    env_message.append(f"   • {var_name}: {var_info['description']}")
            env_message.append("💡 Use set_env_vars() for configuration with automatic validation and guidance.")
        else:
            env_message.append("✅ No authentication or environment variables required.")
        
        # Add workspace directory information to the setup message
        env_message.append("")
        env_message.append(f"📁 Workspace directory set to API specification file location:")
        env_message.append(f"   {ingested_file_directory}")
        env_message.append("   Generated files (scenarios, test cases, reports) will be saved here.")
        
        return {
            "success": True,
            "session_id": session_id,
            "spec_file_path": params.file_path,
            "workspace_directory": ingested_file_directory,
            "spec_type": spec_type.value,
            "preferred_language": preferred_language.value,
            "preferred_framework": preferred_framework.value,
            "endpoints_count": len(endpoints),
            "endpoints": [
                {
                    "path": ep.path,
                    "method": ep.method,
                    "summary": ep.summary,
                    "auth_required": ep.auth_required
                }
                for ep in endpoints
            ],
            "base_url": parser.base_url,
            "environment_analysis": env_analysis,
            "setup_message": "\n".join(env_message)
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to ingest specification: {error_details}")
        return {
            "success": False,
            "error": f"Failed to parse specification: {error_details['message']}"
        }

@mcp.tool()
async def set_env_vars(params: SetEnvVarsParams) -> Dict[str, Any]:
    """
    Set environment variables for authentication and configuration.
    
    This function automatically analyzes the API specification to provide 
    proper validation and context about required/suggested variables.
    
    Args:
        ALL PARAMETERS ARE OPTIONAL - Provide only the values you need!
        
        Individual convenience fields:
        - baseUrl: API base URL (e.g., "https://api.example.com/v1")
        - auth_bearer: Bearer/JWT token (e.g., "eyJhbG...")
        - auth_apikey: API key (e.g., "your-api-key-here")
        - auth_basic: Base64 encoded credentials (e.g., "dXNlcjpwYXNzd29yZA==")
        - auth_username: Username for basic auth
        - auth_password: Password for basic auth
        
        Alternative approach:
        - variables: Dictionary of any custom environment variables
        
        Examples:
        - Just base URL: {"baseUrl": "https://api.example.com"}
        - Just auth token: {"auth_bearer": "your-token"}
        - Mixed: {"baseUrl": "...", "auth_bearer": "...", "variables": {"custom": "value"}}
    
    Returns:
        Dictionary with operation status and current variables
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification first."
        }
    
    try:
        # Analyze the specification for environment variables
        env_analysis = analyze_required_env_vars(
            current_session.spec_content, 
            current_session.spec_type,
            ""  # base_url will be extracted from spec_content
        )
        
        # Check which variables are already set
        current_vars = current_session.env_vars
        suggested_variables = {}
        
        # Process required variables
        for var_name, var_info in env_analysis.get("required_variables", {}).items():
            is_set = var_name in current_vars
            suggested_variables[var_name] = {
                **var_info,
                "currently_set": is_set,
                "current_value": "***" if is_set and ("auth" in var_name.lower() or "secret" in var_name.lower() or "password" in var_name.lower()) else current_vars.get(var_name, None),
                "priority": "required"
            }
        
        # Process optional variables
        for var_name, var_info in env_analysis.get("optional_variables", {}).items():
            is_set = var_name in current_vars
            suggested_variables[var_name] = {
                **var_info,
                "currently_set": is_set,
                "current_value": "***" if is_set and ("auth" in var_name.lower() or "secret" in var_name.lower() or "password" in var_name.lower()) else current_vars.get(var_name, None),
                "priority": "optional"
            }
        
        # Merge optional individual fields into variables dict
        variables_to_set = dict(params.variables)  # Start with explicit variables dict
        
        # Add individual fields if provided (non-None and non-empty)
        optional_fields = {
            "baseUrl": params.baseUrl,
            "auth_bearer": params.auth_bearer, 
            "auth_apikey": params.auth_apikey,
            "auth_basic": params.auth_basic,
            "auth_username": params.auth_username,
            "auth_password": params.auth_password
        }
        
        for key, value in optional_fields.items():
            if value is not None and value.strip():  # Only add if provided and not empty
                variables_to_set[key] = value
        
        # Auto-populate variables with detected values from suggestions if not provided by user
        for var_name, var_info in suggested_variables.items():
            # Only auto-populate if the variable is not already provided by user and has a detected value
            if var_name not in variables_to_set and "detected_value" in var_info:
                variables_to_set[var_name] = var_info["detected_value"]
                logger.info(f"Auto-populated {var_name} with detected value from specification")
        
        # Check what parameters were provided or auto-populated
        provided_keys = list(variables_to_set.keys())
        if not provided_keys:
            # If no variables to set, return current status with suggestions
            return {
                "success": True,
                "session_id": current_session.id,
                "variables_set": [],
                "message": "No variables provided and no auto-detectable values found",
                "suggested_variables": suggested_variables,
                "env_analysis": env_analysis,
                "current_variables": {k: "***" if "auth" in k.lower() or "password" in k.lower() or "secret" in k.lower() else v 
                                   for k, v in current_session.env_vars.items()}
            }
        
        # Validate variables against suggestions
        validation_warnings = []
        validation_errors = []
        
        for var_name, var_value in variables_to_set.items():
            if var_name in suggested_variables:
                var_info = suggested_variables[var_name]
                # Check if this is a required variable
                if var_info.get("priority") == "required" and not var_value.strip():
                    validation_errors.append(f"Required variable '{var_name}' cannot be empty")
                
                # Validate URL format if it's a baseUrl
                if var_name == "baseUrl" and var_value and not validate_url(var_value):
                    validation_errors.append(f"Invalid base URL format: {var_value}")
            else:
                # Variable not in suggestions - it's a custom variable
                validation_warnings.append(f"Setting custom variable '{var_name}' not detected in API specification")
        
        # Return validation errors if any
        if validation_errors:
            return {
                "success": False,
                "error": "Validation failed: " + "; ".join(validation_errors),
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings,
                "suggested_variables": suggested_variables,
                "env_analysis": env_analysis
            }
        
        # Merge with existing variables
        current_session.env_vars = merge_env_vars(current_session.env_vars, variables_to_set)
        
        # Check if all required variables are now set
        missing_required = []
        for var_name, var_info in suggested_variables.items():
            if (var_info.get("priority") == "required" and 
                var_name not in current_session.env_vars):
                missing_required.append(var_name)
        
        # Prepare result
        result = {
            "success": True,
            "session_id": current_session.id,
            "variables_set": provided_keys,
            "variables_updated": len(provided_keys),
            "validation_warnings": validation_warnings,
            "suggested_variables": suggested_variables,
            "env_analysis": env_analysis,
            "missing_required_variables": missing_required,
            "configuration_complete": len(missing_required) == 0,
            "current_variables": {k: "***" if "auth" in k.lower() or "password" in k.lower() or "secret" in k.lower() else v 
                               for k, v in current_session.env_vars.items()}
        }
        
        # Add helpful message based on configuration status
        if len(missing_required) == 0:
            result["message"] = "✅ All required environment variables are now configured!"
        else:
            result["message"] = f"⚠️ Configuration updated, but {len(missing_required)} required variable(s) still missing: {', '.join(missing_required)}"
        
        return result
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to set environment variables: {error_details}")
        return {
            "success": False,
            "error": f"Failed to set variables: {error_details['message']}"
        }

@mcp.tool()
async def generate_scenarios(params: GenerateScenariosParams) -> Dict[str, Any]:
    """
    Generate test scenarios from the ingested API specification.
    
    NOTE: This function automatically saves the generated scenarios to both the output 
    directory and the current workspace for easy access.
    
    Args:
        include_negative_tests: Whether to include negative test scenarios
        include_edge_cases: Whether to include edge case scenarios
    
    Returns:
        Dictionary with generated scenarios information including file paths
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification first."
        }
    
    try:
        # Parse endpoints from session
        parser = SpecificationParser()
        endpoints = parser.parse(json.dumps(current_session.spec_content), current_session.spec_type)
        
        # Generate scenarios
        generator = ScenarioGenerator()
        progress = ProgressTracker(len(endpoints), "Scenario Generation")
        progress.start()
        
        scenarios = []
        for endpoint in endpoints:
            # Generate positive scenario
            positive_scenario = generator._generate_positive_scenario(endpoint)
            scenarios.append(positive_scenario)
            
            if params.include_negative_tests:
                negative_scenarios = generator._generate_negative_scenarios(endpoint)
                scenarios.extend(negative_scenarios)
            
            if params.include_edge_cases:
                edge_scenarios = generator._generate_edge_case_scenarios(endpoint)
                scenarios.extend(edge_scenarios)
            
            progress.update(f"Generated scenarios for {endpoint.method} {endpoint.path}")
        
        # Save scenarios to session
        current_session.scenarios = scenarios
        
        # Prepare scenarios data for serialization
        scenarios_data = [scenario.model_dump() for scenario in scenarios]
        
        # Dynamically ensure scenarios directory exists in workspace
        scenarios_dir = ensure_workspace_output_dir("scenarios")
        workspace_dir = get_workspace_dir()
        
        # Save scenarios to the dynamically created scenarios directory
        scenarios_file = os.path.join(scenarios_dir, f"scenarios_{current_session.id}.json")
        scenarios_file_created = False
        try:
            with open(scenarios_file, 'w', encoding='utf-8') as f:
                json.dump(scenarios_data, f, indent=2)
            scenarios_file_created = True
            logger.info(f"Successfully saved scenarios to workspace: {scenarios_file}")
        except Exception as e:
            logger.error(f"Failed to save scenarios to {scenarios_file}: {str(e)}")
            scenarios_file = f"ERROR: Could not create {scenarios_file} - {str(e)}"
        
        progress.finish()
        
        return {
            "success": True,
            "session_id": current_session.id,
            "scenarios_count": len(scenarios),
            "scenarios": [
                {
                    "id": scenario.id,
                    "name": scenario.name,
                    "objective": scenario.objective,
                    "endpoint": f"{scenario.endpoint.method} {scenario.endpoint.path}",
                    "steps_count": len(scenario.steps),
                    "assertions_count": len(scenario.assertions)
                }
                for scenario in scenarios
            ],
            "scenarios_file": scenarios_file,
            "workspace_directory": workspace_dir,
            "scenarios_directory": scenarios_dir,
            "file_created": scenarios_file_created,
            "file_path": scenarios_file if scenarios_file_created else "Failed to create",
            "message": f"Scenarios saved to workspace: {scenarios_file}" if scenarios_file_created else f"Failed to create scenarios file"
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to generate scenarios: {error_details}")
        return {
            "success": False,
            "error": f"Failed to generate scenarios: {error_details['message']}",
            "workspace_directory": get_workspace_dir(),
            "session_id": current_session.id if current_session else "No session"
        }

@mcp.tool()
async def generate_test_cases(params: GenerateTestCasesParams) -> Dict[str, Any]:
    """
    Generate executable test cases from scenarios using the language and framework specified in ingest_spec.
    
    NOTE: This function automatically saves the generated test cases to both the output 
    directory and the current workspace for easy access.
    
    Args:
        scenario_ids: Optional list of specific scenario IDs to generate test cases for
    
    Returns:
        Dictionary with generated test cases information including generated code and file paths.
        Uses the preferred_language and preferred_framework from the active session (set during ingest_spec).
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification first."
        }
    
    if not current_session.scenarios:
        return {
            "success": False,
            "error": "No scenarios available. Please generate scenarios first."
        }
    
    try:
        # Filter scenarios if specific IDs provided
        scenarios_to_process = current_session.scenarios
        if params.scenario_ids:
            scenarios_to_process = [
                scenario for scenario in current_session.scenarios
                if scenario.id in params.scenario_ids
            ]
            
            if not scenarios_to_process:
                return {
                    "success": False,
                    "error": "No matching scenarios found for provided IDs"
                }

        # Use session's preferred language and framework (set during ingest_spec)
        language = current_session.preferred_language
        framework = current_session.preferred_framework

        language_str = language.value
        framework_str = framework.value

        # Generate test cases
        base_url = current_session.env_vars.get("baseUrl", "")
        generator = TestCaseGenerator(base_url, current_session.env_vars, language, framework)
        
        progress = ProgressTracker(len(scenarios_to_process), "Test Case Generation")
        progress.start()
        
        test_cases = []
        for scenario in scenarios_to_process:
            test_case = generator._scenario_to_test_case(scenario)
            test_cases.append(test_case)
            progress.update(f"Generated test case for {scenario.name}")
        
        # Save test cases to session
        current_session.test_cases = test_cases
        
        # Prepare test cases data for serialization
        test_cases_data = [test_case.model_dump() for test_case in test_cases]
        
        # Dynamically ensure test_cases directory exists in workspace
        test_cases_dir = ensure_workspace_output_dir("test_cases")
        workspace_dir = get_workspace_dir()
        
        # Save test cases JSON metadata to the dynamically created test_cases directory
        test_cases_file = os.path.join(test_cases_dir, f"test_cases_{current_session.id}.json")
        test_cases_file_created = False
        try:
            with open(test_cases_file, 'w', encoding='utf-8') as f:
                json.dump(test_cases_data, f, indent=2)
            test_cases_file_created = True
            logger.info(f"Successfully saved test cases metadata to workspace: {test_cases_file}")
        except Exception as e:
            logger.error(f"Failed to save test cases to {test_cases_file}: {str(e)}")
            test_cases_file = f"ERROR: Could not create {test_cases_file} - {str(e)}"

        # Also generate and save the actual test code files to workspace
        code_files_created = []
        code_files_failed = []
        try:
            # Generate test code using the test case generator
            session_info = {
                'id': current_session.id,
                'base_url': base_url,
                'auth_token': current_session.env_vars.get('auth_bearer', ''),
            }
            
            test_code = generator.code_generator.generate_test_code(test_cases, session_info)
            
            # Determine appropriate filename based on language/framework
            if language == TestLanguage.PYTHON:
                if framework == TestFramework.PYTEST:
                    code_filename = f"test_api_{current_session.id}.py"
                else:
                    code_filename = f"api_tests_{current_session.id}.py"
            elif language == TestLanguage.TYPESCRIPT:
                if framework == TestFramework.PLAYWRIGHT:
                    code_filename = f"api_tests_{current_session.id}.spec.ts"
                else:
                    code_filename = f"api_tests_{current_session.id}.test.ts"
            elif language == TestLanguage.JAVASCRIPT:
                if framework == TestFramework.CYPRESS:
                    code_filename = f"api_tests_{current_session.id}.cy.js"
                else:
                    code_filename = f"api_tests_{current_session.id}.test.js"
            else:
                code_filename = f"api_tests_{current_session.id}.txt"
            
            # Save the code file to workspace root
            code_file_path = os.path.join(workspace_dir, code_filename)
            with open(code_file_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            code_files_created.append(code_file_path)
            logger.info(f"Successfully saved test code to workspace: {code_file_path}")
            
        except Exception as e:
            error_msg = f"Failed to generate test code file: {str(e)}"
            code_files_failed.append(error_msg)
            logger.error(error_msg)
        
        progress.finish()
        
        return {
            "success": True,
            "session_id": current_session.id,
            "language": language_str,
            "framework": framework_str,
            "test_cases_count": len(test_cases),
            "test_cases": [
                {
                    "id": test_case.id,
                    "scenario_id": test_case.scenario_id,
                    "name": test_case.name,
                    "method": test_case.method,
                    "url": test_case.url,
                    "expected_status": test_case.expected_status,
                    "assertions_count": len(test_case.assertions),
                    "language": test_case.language.value,
                    "framework": test_case.framework.value,
                    "has_generated_code": bool(test_case.generated_code)
                }
                for test_case in test_cases
            ],
            "test_cases_file": test_cases_file,
            "workspace_directory": workspace_dir,
            "test_cases_directory": test_cases_dir,
            "generated_code_available": all(tc.generated_code for tc in test_cases),
            "file_created": test_cases_file_created,
            "file_path": test_cases_file if test_cases_file_created else "Failed to create",
            "code_files_created": code_files_created,
            "code_files_failed": code_files_failed,
            "message": f"Test cases saved to workspace: {test_cases_file}" + 
                      (f" | Code files: {', '.join([os.path.basename(f) for f in code_files_created])}" if code_files_created else "") +
                      (f" | Code file errors: {len(code_files_failed)}" if code_files_failed else "")
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to generate test cases: {error_details}")
        return {
            "success": False,
            "error": f"Failed to generate test cases: {error_details['message']}",
            "workspace_directory": get_workspace_dir(),
            "session_id": current_session.id if current_session else "No session"
        }

@mcp.tool()
async def run_api_tests(params: RunApiTestsParams) -> Dict[str, Any]:
    """
    Execute API tests and generate results.
    
    Args:
        test_case_ids: Optional list of specific test case IDs to run.
                      If not provided, runs all test cases.
        max_concurrent: Maximum number of concurrent requests (default: 10)
    
    Returns:
        Dictionary with test execution results and report information
    """
    global current_session, test_results
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification first."
        }
    
    if not current_session.test_cases:
        return {
            "success": False,
            "error": "No test cases available. Please generate test cases first."
        }
    
    try:
        # Filter test cases if specific IDs provided
        test_cases_to_run = current_session.test_cases
        if params.test_case_ids:
            test_cases_to_run = [
                test_case for test_case in current_session.test_cases
                if test_case.id in params.test_case_ids
            ]
            
            if not test_cases_to_run:
                return {
                    "success": False,
                    "error": "No matching test cases found for provided IDs"
                }
        
        # Execute tests
        current_session.status = StatusType.RUNNING
        executor = TestExecutor(max_concurrent=params.max_concurrent)
        test_results = await executor.execute_tests(test_cases_to_run)
        
        current_session.status = StatusType.COMPLETED
        current_session.completed_at = datetime.now().isoformat()
        
        # Generate HTML report
        html_report = report_generator.generate_api_test_report(test_results, current_session)
        reports_dir = ensure_workspace_output_dir("reports")
        report_file = os.path.join(reports_dir, f"api_test_report_{current_session.id}.html")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Calculate summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.status == "passed")
        failed_tests = sum(1 for r in test_results if r.status == "failed")
        total_time = sum(r.execution_time for r in test_results)
        
        return {
            "success": True,
            "session_id": current_session.id,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time,
                "average_execution_time": total_time / total_tests if total_tests > 0 else 0
            },
            "report_file": report_file,
            "detailed_results": [
                {
                    "test_case_id": result.test_case_id,
                    "status": result.status,
                    "execution_time": result.execution_time,
                    "response_status": result.response_status,
                    "assertions_passed": result.assertions_passed,
                    "assertions_failed": result.assertions_failed,
                    "error_message": result.error_message
                }
                for result in test_results
            ]
        }
        
    except Exception as e:
        current_session.status = StatusType.FAILED
        error_details = extract_error_details(e)
        logger.error(f"Failed to run API tests: {error_details}")
        return {
            "success": False,
            "error": f"Failed to run tests: {error_details['message']}"
        }

@mcp.tool()
async def run_load_tests(params: RunLoadTestsParams) -> Dict[str, Any]:
    """
    Execute load tests with specified parameters.
    
    Args:
        test_case_ids: Optional list of specific test case IDs to use for load testing.
                      If not provided, uses all test cases.
        duration: Duration of load test in seconds (default: 60)
        users: Number of concurrent users (default: 10)
        ramp_up: Ramp up time in seconds (default: 10)
    
    Returns:
        Dictionary with load test results and report information
    """
    global current_session, load_test_results
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification first."
        }
    
    if not current_session.test_cases:
        return {
            "success": False,
            "error": "No test cases available. Please generate test cases first."
        }
    
    try:
        # Filter test cases if specific IDs provided
        test_cases_to_run = current_session.test_cases
        if params.test_case_ids:
            test_cases_to_run = [
                test_case for test_case in current_session.test_cases
                if test_case.id in params.test_case_ids
            ]
            
            if not test_cases_to_run:
                return {
                    "success": False,
                    "error": "No matching test cases found for provided IDs"
                }
        
        # Execute load test
        executor = LoadTestExecutor(
            duration=params.duration,
            users=params.users,
            ramp_up=params.ramp_up
        )
        
        load_test_results = await executor.run_load_test(test_cases_to_run)
        
        if "error" in load_test_results:
            return {
                "success": False,
                "error": load_test_results["error"]
            }
        
        # Generate HTML report
        html_report = report_generator.generate_load_test_report(load_test_results, current_session)
        reports_dir = ensure_workspace_output_dir("reports")
        report_file = os.path.join(reports_dir, f"load_test_report_{current_session.id}.html")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        return {
            "success": True,
            "session_id": current_session.id,
            "load_test_results": load_test_results,
            "report_file": report_file
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to run load tests: {error_details}")
        return {
            "success": False,
            "error": f"Failed to run load tests: {error_details['message']}"
        }

@mcp.tool()
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported programming languages and testing frameworks.
    
    Returns:
        Dictionary with supported language/framework combinations and their descriptions
    """
    try:
        combinations = get_supported_combinations()
        
        return {
            "success": True,
            "supported_combinations": combinations,
            "languages": ["python", "typescript", "javascript"],
            "frameworks": {
                "python": ["pytest", "requests"],
                "typescript": ["playwright", "supertest"],
                "javascript": ["jest", "cypress"]
            },
            "recommendations": {
                "beginners": {"language": "python", "framework": "requests"},
                "comprehensive_testing": {"language": "python", "framework": "pytest"},
                "modern_web_apis": {"language": "typescript", "framework": "playwright"},
                "node_js_apis": {"language": "javascript", "framework": "jest"},
                "e2e_testing": {"language": "typescript", "framework": "playwright"}
            }
        }
    except Exception as e:
        logger.error(f"Failed to get supported languages: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get supported languages: {str(e)}"
        }

class GenerateProjectParams(BaseModel):
    project_name: Optional[str] = None
    include_examples: Optional[bool] = True

@mcp.tool()
async def generate_project_files(params: GenerateProjectParams) -> Dict[str, Any]:
    """
    Generate complete project files using the language and framework specified in ingest_spec.
    Automatically reuses test cases and parameters from the current session if available.
    
    Args:
        project_name: Name for the generated project
        include_examples: Whether to include example test files
    
    Returns:
        Dictionary with generated project files and setup instructions.
        Uses the preferred_language and preferred_framework from the active session (set during ingest_spec).
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification and generate test cases first."
        }
    
    if not current_session.test_cases:
        return {
            "success": False,
            "error": "No test cases available. Please generate test cases first using generate_test_cases()."
        }
    
    try:
        # Use session's preferred language and framework (set during ingest_spec)
        language_enum = current_session.preferred_language
        framework_enum = current_session.preferred_framework
        
        language_str = language_enum.value
        framework_str = framework_enum.value
        project_name = params.project_name or f"api-tests-{current_session.id}"
        include_examples = params.include_examples if params.include_examples is not None else True
        
        # Generate package files (dependency management, configs, etc.)
        package_files = generate_package_files(language_enum, framework_enum)
        
        # Reuse existing test files from project directory (created by generate_test_cases)
        project_dir = get_or_create_project_dir()
        existing_test_files = {}
        reused_files = []
        
        # Look for existing test case files in workspace
        expected_test_filenames = []
        if language_enum == TestLanguage.PYTHON:
            if framework_enum == TestFramework.PYTEST:
                expected_test_filenames = [f"test_api_{current_session.id}.py"]
            else:
                expected_test_filenames = [f"api_tests_{current_session.id}.py"]
        elif language_enum == TestLanguage.TYPESCRIPT:
            if framework_enum == TestFramework.PLAYWRIGHT:
                expected_test_filenames = [f"api_tests_{current_session.id}.spec.ts"]
            else:
                expected_test_filenames = [f"api_tests_{current_session.id}.test.ts"]
        elif language_enum == TestLanguage.JAVASCRIPT:
            if framework_enum == TestFramework.CYPRESS:
                expected_test_filenames = [f"api_tests_{current_session.id}.cy.js"]
            else:
                expected_test_filenames = [f"api_tests_{current_session.id}.test.js"]
        
        # Check for existing test files and reuse them
        for filename in expected_test_filenames:
            file_path = os.path.join(project_dir, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    existing_test_files[filename] = content
                    reused_files.append(file_path)
                    logger.info(f"Reusing existing test file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to read existing test file {file_path}: {str(e)}")
        
        # If no existing test files found, create them
        if not existing_test_files:
            logger.info("No existing test files found, creating new ones")
            try:
                generator = TestCaseGenerator(
                    base_url=current_session.env_vars.get("baseUrl", ""),
                    env_vars=current_session.env_vars,
                    language=language_enum,
                    framework=framework_enum
                )
                
                session_info = {
                    'id': current_session.id,
                    'base_url': current_session.env_vars.get("baseUrl", ""),
                    'auth_token': current_session.env_vars.get('auth_bearer', ''),
                }
                
                code_generator = generator.code_generator
                test_code = code_generator.generate_test_code(current_session.test_cases, session_info)
                
                # Create the test file
                for filename in expected_test_filenames:
                    existing_test_files[filename] = test_code
                    
            except Exception as e:
                logger.warning(f"Failed to generate test files: {str(e)}")
        
        # Create example files for project structure (using subset of test cases)
        example_files = {}
        if include_examples and existing_test_files:
            try:
                # Get the first test file content for project examples
                first_test_file = list(existing_test_files.values())[0]
                
                # Determine project structure file paths based on language/framework
                if language_enum == TestLanguage.PYTHON:
                    if framework_enum == TestFramework.PYTEST:
                        example_files["tests/test_api.py"] = first_test_file
                    else:
                        example_files["test_api.py"] = first_test_file
                elif language_enum == TestLanguage.TYPESCRIPT:
                    if framework_enum == TestFramework.PLAYWRIGHT:
                        example_files["tests/api.spec.ts"] = first_test_file
                    else:
                        example_files["tests/api.test.ts"] = first_test_file
                elif language_enum == TestLanguage.JAVASCRIPT:
                    if framework_enum == TestFramework.CYPRESS:
                        example_files["cypress/e2e/api.cy.js"] = first_test_file
                    else:
                        example_files["tests/api.test.js"] = first_test_file
                        
            except Exception as e:
                logger.warning(f"Failed to create example files: {str(e)}")
        
        # Generate setup instructions
        setup_instructions = _generate_setup_instructions(language_enum, framework_enum, project_name)
        
        # Create project directory structure
        base_dir = get_or_create_project_dir()
        final_project_dir = os.path.join(base_dir, project_name)
        
        try:
            os.makedirs(final_project_dir, exist_ok=True)
            logger.info(f"Created/verified project directory: {final_project_dir}")
        except Exception as e:
            logger.error(f"Failed to create project directory {final_project_dir}: {str(e)}")
        
        # Save files to project directory
        saved_files = []
        project_files_created = []
        project_files_failed = []
        test_files_copied = []
        test_files_created_fresh = []
        
        # Save package files (dependencies, configs) to project directory
        for filename, content in package_files.items():
            file_path = os.path.join(final_project_dir, filename)
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_files.append(file_path)
                project_files_created.append(filename)
                logger.info(f"Created project file: {file_path}")
            except Exception as e:
                project_files_failed.append(f"{filename}: {str(e)}")
                logger.error(f"Failed to create project file {file_path}: {str(e)}")
        
        # Copy or create test files in project directory
        if existing_test_files:
            # Copy existing workspace test files to project directory
            for filename, content in existing_test_files.items():
                # Determine appropriate project path based on language/framework
                if language_enum == TestLanguage.PYTHON:
                    if framework_enum == TestFramework.PYTEST:
                        project_test_path = os.path.join(final_project_dir, "tests", filename)
                    else:
                        project_test_path = os.path.join(final_project_dir, filename)
                elif language_enum == TestLanguage.TYPESCRIPT:
                    if framework_enum == TestFramework.PLAYWRIGHT:
                        project_test_path = os.path.join(final_project_dir, "tests", filename)
                    else:
                        project_test_path = os.path.join(final_project_dir, "tests", filename)
                elif language_enum == TestLanguage.JAVASCRIPT:
                    if framework_enum == TestFramework.CYPRESS:
                        project_test_path = os.path.join(final_project_dir, "cypress", "e2e", filename)
                    else:
                        project_test_path = os.path.join(final_project_dir, "tests", filename)
                
                try:
                    os.makedirs(os.path.dirname(project_test_path), exist_ok=True)
                    with open(project_test_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    saved_files.append(project_test_path)
                    test_files_copied.append(filename)
                    logger.info(f"Copied test file to project: {project_test_path}")
                except Exception as e:
                    project_files_failed.append(f"test file {filename}: {str(e)}")
                    logger.error(f"Failed to copy test file {project_test_path}: {str(e)}")
        else:
            # Create fresh test files directly in project directory
            logger.info("Creating fresh test files directly in project directory")
            try:
                generator = TestCaseGenerator(
                    base_url=current_session.env_vars.get("baseUrl", ""),
                    env_vars=current_session.env_vars,
                    language=language_enum,
                    framework=framework_enum
                )
                
                session_info = {
                    'id': current_session.id,
                    'base_url': current_session.env_vars.get("baseUrl", ""),
                    'auth_token': current_session.env_vars.get('auth_bearer', ''),
                }
                
                code_generator = generator.code_generator
                test_code = code_generator.generate_test_code(current_session.test_cases, session_info)
                
                # Create test files directly in project directory
                for filename in expected_test_filenames:
                    if language_enum == TestLanguage.PYTHON:
                        if framework_enum == TestFramework.PYTEST:
                            project_test_path = os.path.join(final_project_dir, "tests", filename)
                        else:
                            project_test_path = os.path.join(final_project_dir, filename)
                    elif language_enum == TestLanguage.TYPESCRIPT:
                        if framework_enum == TestFramework.PLAYWRIGHT:
                            project_test_path = os.path.join(final_project_dir, "tests", filename)
                        else:
                            project_test_path = os.path.join(final_project_dir, "tests", filename)
                    elif language_enum == TestLanguage.JAVASCRIPT:
                        if framework_enum == TestFramework.CYPRESS:
                            project_test_path = os.path.join(final_project_dir, "cypress", "e2e", filename)
                        else:
                            project_test_path = os.path.join(final_project_dir, "tests", filename)
                    
                    try:
                        os.makedirs(os.path.dirname(project_test_path), exist_ok=True)
                        with open(project_test_path, 'w', encoding='utf-8') as f:
                            f.write(test_code)
                        saved_files.append(project_test_path)
                        test_files_created_fresh.append(filename)
                        existing_test_files[filename] = test_code  # Add to existing for return data
                        logger.info(f"Created fresh test file in project: {project_test_path}")
                    except Exception as e:
                        project_files_failed.append(f"fresh test file {filename}: {str(e)}")
                        logger.error(f"Failed to create fresh test file {project_test_path}: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Failed to generate fresh test files: {str(e)}")
        
        # Save additional example files to project directory if requested
        if include_examples:
            for filename, content in example_files.items():
                # Skip if this file was already created as a test file
                if filename in [os.path.basename(f) for f in saved_files]:
                    continue
                    
                file_path = os.path.join(final_project_dir, filename)
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    saved_files.append(file_path)
                    project_files_created.append(filename)
                    logger.info(f"Created example file: {file_path}")
                except Exception as e:
                    project_files_failed.append(f"example {filename}: {str(e)}")
                    logger.error(f"Failed to create example file {file_path}: {str(e)}")
        
        return {
            "success": True,
            "language": language_str,
            "framework": framework_str,
            "project_name": project_name,
            "session_id": current_session.id,
            "project_directory": final_project_dir,
            "base_directory": base_dir,
            "test_files_found_in_workspace": bool(reused_files),
            "generated_files": {
                "package_files": list(package_files.keys()),
                "example_files": list(example_files.keys()) if example_files else [],
                "test_files_copied": test_files_copied,
                "test_files_created_fresh": test_files_created_fresh,
                "project_files_created": project_files_created,
                "project_files_failed": project_files_failed
            },
            "file_status": {
                "workspace_test_files_found": [os.path.basename(f) for f in reused_files],
                "test_files_copied_to_project": len(test_files_copied),
                "test_files_created_fresh_in_project": len(test_files_created_fresh),
                "project_files_created": len(project_files_created),
                "project_files_failed": len(project_files_failed),
                "total_project_files": len(project_files_created) + len(test_files_copied) + len(test_files_created_fresh)
            },
            "file_contents": {
                **package_files, 
                **example_files,
                **existing_test_files
            },
            "setup_instructions": setup_instructions,
            "saved_files": saved_files,
            "message": f"Project created in {final_project_dir}. " + 
                      (f"Copied {len(test_files_copied)} test files from workspace. " if test_files_copied else "") +
                      (f"Created {len(test_files_created_fresh)} fresh test files. " if test_files_created_fresh else "") +
                      f"Added {len(project_files_created)} project configuration files."
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to generate project files: {error_details}")
        return {
            "success": False,
            "error": f"Failed to generate project files: {error_details['message']}",
            "session_id": current_session.id if current_session else "No session",
            "project_directory": get_or_create_project_dir()
        }

def _generate_setup_instructions(language: TestLanguage, framework: TestFramework, project_name: str) -> List[str]:
    """Generate setup instructions for the selected language/framework"""
    instructions = [
        f"# Setup Instructions for {project_name}",
        "",
        f"## {language.value.title()} + {framework.value.title()} Project Setup",
        ""
    ]
    
    if language == TestLanguage.PYTHON:
        instructions.extend([
            "1. Ensure Python 3.8+ is installed",
            "2. Create a virtual environment:",
            "   ```bash",
            "   python -m venv venv",
            "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
            "   ```",
            "3. Install dependencies:",
            "   ```bash",
            "   pip install -r requirements.txt",
            "   ```"
        ])
        
        if framework == TestFramework.PYTEST:
            instructions.extend([
                "4. Run tests:",
                "   ```bash",
                "   pytest tests/ -v",
                "   pytest tests/ --html=report.html  # Generate HTML report",
                "   ```"
            ])
        else:
            instructions.extend([
                "4. Run tests:",
                "   ```bash",
                "   python test_api.py",
                "   ```"
            ])
            
    elif language in [TestLanguage.TYPESCRIPT, TestLanguage.JAVASCRIPT]:
        instructions.extend([
            "1. Ensure Node.js 16+ is installed",
            "2. Install dependencies:",
            "   ```bash",
            "   npm install",
            "   ```"
        ])
        
        if framework == TestFramework.PLAYWRIGHT:
            instructions.extend([
                "3. Install Playwright browsers:",
                "   ```bash",
                "   npx playwright install",
                "   ```",
                "4. Run tests:",
                "   ```bash",
                "   npm test",
                "   npm run test:headed  # Run with browser UI",
                "   ```"
            ])
        elif framework == TestFramework.JEST:
            instructions.extend([
                "3. Run tests:",
                "   ```bash",
                "   npm test",
                "   npm run test:watch  # Run in watch mode",
                "   ```"
            ])
        elif framework == TestFramework.CYPRESS:
            instructions.extend([
                "3. Run tests:",
                "   ```bash",
                "   npm test  # Headless mode",
                "   npm run test:open  # Interactive mode",
                "   ```"
            ])
        elif framework == TestFramework.SUPERTEST:
            instructions.extend([
                "3. Run tests:",
                "   ```bash",
                "   npm test",
                "   ```"
            ])
    
    instructions.extend([
        "",
        "## Environment Variables",
        "",
        "Set the following environment variables:",
        "- `BASE_URL`: API base URL",
        "- `AUTH_TOKEN`: Authentication token (if required)",
        "",
        "Example:",
        "```bash",
        "export BASE_URL=https://api.example.com",
        "export AUTH_TOKEN=your-token-here",
        "```"
    ])
    
    return instructions

@mcp.tool()
async def get_workspace_info() -> Dict[str, Any]:
    """
    Get information about the current workspace directory and file generation locations.
    
    Returns:
        Dictionary with workspace information including current directory and whether it was
        set from an ingested API specification file.
    """
    global ingested_file_directory
    
    try:
        current_workspace = get_workspace_dir()
        
        workspace_info = {
            "success": True,
            "current_workspace_directory": current_workspace,
            "is_from_ingested_file": ingested_file_directory is not None,
            "ingested_file_directory": ingested_file_directory,
            "output_directories": {
                "reports": ensure_workspace_output_dir("reports"),
                "scenarios": ensure_workspace_output_dir("scenarios"),
                "test_cases": ensure_workspace_output_dir("test_cases"),
                "generated_projects": ensure_workspace_output_dir("generated_projects")
            },
            "directory_access": check_directory_access(current_workspace)
        }
        
        if ingested_file_directory:
            workspace_info["message"] = f"Workspace directory set from ingested API specification file location: {current_workspace}"
        else:
            workspace_info["message"] = f"Using default workspace directory: {current_workspace}"
        
        return workspace_info
        
    except Exception as e:
        logger.error(f"Failed to get workspace info: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get workspace info: {str(e)}"
        }

@mcp.tool()
async def debug_file_system() -> Dict[str, Any]:
    """
    Get comprehensive workspace information and file system diagnostics.
    Shows where files will be saved without creating directories.
    
    Returns:
        Dictionary with workspace information and file system diagnostic details
    """
    try:
        workspace_dir = get_workspace_dir()
        
        # Check for existing output directory patterns WITHOUT creating them
        possible_output_dirs = ["output", "generated", "api-test-output", "mcp-output"]
        existing_output_dir = None
        
        for output_dir_name in possible_output_dirs:
            potential_output = os.path.join(workspace_dir, output_dir_name)
            if os.path.exists(potential_output) and os.path.isdir(potential_output):
                existing_output_dir = potential_output
                break
        
        # Determine where directories would be created (without creating them)
        if existing_output_dir:
            output_base = existing_output_dir
            scenarios_dir = os.path.join(output_base, "scenarios")
            test_cases_dir = os.path.join(output_base, "test_cases") 
            reports_dir = os.path.join(output_base, "reports")
            projects_dir = os.path.join(output_base, "generated_projects")
        else:
            output_base = os.path.join(workspace_dir, "output")  # Default choice
            scenarios_dir = os.path.join(output_base, "scenarios")
            test_cases_dir = os.path.join(output_base, "test_cases")
            reports_dir = os.path.join(output_base, "reports") 
            projects_dir = os.path.join(output_base, "generated_projects")
        
        # Check various directories
        directories_to_check = [
            ("workspace", workspace_dir),
            ("output_base", output_base),
            ("scenarios", scenarios_dir),
            ("test_cases", test_cases_dir),
            ("reports", reports_dir),
            ("generated_projects", projects_dir)
        ]
        
        directory_status = {}
        for dir_name, dir_path in directories_to_check:
            directory_status[dir_name] = check_directory_access(dir_path)
        
        # List files in workspace and output directories
        workspace_files = []
        output_files = []
        
        try:
            if os.path.exists(workspace_dir):
                workspace_files = [f for f in os.listdir(workspace_dir) if f.endswith(('.json', '.py', '.ts', '.js'))]
        except Exception as e:
            workspace_files = [f"Error listing workspace files: {str(e)}"]
        
        try:
            if os.path.exists(output_base):
                for root, dirs, files in os.walk(output_base):
                    for file in files:
                        relative_path = os.path.relpath(os.path.join(root, file), output_base)
                        output_files.append(relative_path)
        except Exception as e:
            output_files = [f"Error listing output files: {str(e)}"]
        
        return {
            "success": True,
            "current_working_directory": os.getcwd(),
            "workspace_directory": workspace_dir,
            "output_base_directory": output_base,
            "file_locations": {
                "scenarios": {
                    "path": scenarios_dir,
                    "description": "JSON files with test scenario definitions",
                    "relative_path": os.path.relpath(scenarios_dir, workspace_dir)
                },
                "test_cases": {
                    "path": test_cases_dir,
                    "description": "JSON metadata for generated test cases",
                    "relative_path": os.path.relpath(test_cases_dir, workspace_dir)
                },
                "reports": {
                    "path": reports_dir, 
                    "description": "HTML test execution reports",
                    "relative_path": os.path.relpath(reports_dir, workspace_dir)
                },
                "generated_projects": {
                    "path": projects_dir,
                    "description": "Complete project structures with dependencies", 
                    "relative_path": os.path.relpath(projects_dir, workspace_dir)
                },
                "test_code_files": {
                    "path": workspace_dir,
                    "description": "Executable test files (Python, TypeScript, JavaScript)",
                    "relative_path": "."
                }
            },
            "directory_access": directory_status,
            "workspace_files": workspace_files[:20],  # Limit to first 20 files
            "output_files": output_files[:20],  # Limit to first 20 files
            "environment_variables": {
                "PWD": os.environ.get('PWD'),
                "WORKSPACE_DIR": os.environ.get('WORKSPACE_DIR'),
                "HOME": os.environ.get('HOME'),
                "USERPROFILE": os.environ.get('USERPROFILE')
            },
            "adaptive_behavior": {
                "existing_output_directory": existing_output_dir,
                "will_use_pattern": os.path.basename(output_base) if existing_output_dir else "output (default)",
                "supported_patterns": possible_output_dirs,
                "fallback_strategy": "Creates api-test-{type} directories if standard output creation fails"
            }
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        return {
            "success": False,
            "error": f"Failed to debug file system: {error_details['message']}",
            "current_working_directory": os.getcwd() if hasattr(os, 'getcwd') else "unknown"
        }

@mcp.tool()
async def get_session_status() -> Dict[str, Any]:
    """
    Get current session status and information with progress details.
    
    Returns:
        Dictionary with current session information including progress
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session"
        }
    
    # Get basic session info
    session_info = {
        "success": True,
        "session_id": current_session.id,
        "status": current_session.status.value,
        "spec_type": current_session.spec_type.value,
        "created_at": current_session.created_at,
        "completed_at": current_session.completed_at,
        "endpoints_count": len(current_session.spec_content.get("paths", {})),
        "scenarios_count": len(current_session.scenarios),
        "test_cases_count": len(current_session.test_cases),
        "env_vars": current_session.env_vars,
        "preferred_language": current_session.preferred_language.value,
        "preferred_framework": current_session.preferred_framework.value
    }
    
    # Add progress information if there's an active operation
    # This would be enhanced with a global progress tracker for the current operation
    if hasattr(current_session, 'current_operation_progress'):
        session_info["current_operation"] = current_session.current_operation_progress
    
    return session_info

# MCP Resources - Make HTML reports accessible
@mcp.resource("file://reports/{report_id}")
async def get_report(report_id: str) -> Resource:
    """
    Provide access to HTML test reports.
    
    Args:
        report_id: The report identifier (filename without extension)
    
    Returns:
        Resource containing the HTML report content
    """
    try:
        report_file = os.path.join(OUTPUT_BASE_DIR, "reports", f"{report_id}.html")
        
        if not os.path.exists(report_file):
            return Resource(
                uri=f"file://reports/{report_id}",
                name=f"Report {report_id}",
                description="Report not found",
                mimeType="text/plain",
                text="Report not found or has been deleted."
            )
        
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Resource(
            uri=f"file://reports/{report_id}",
            name=f"Test Report {report_id}",
            description="HTML test report with detailed results and statistics",
            mimeType="text/html",
            text=content
        )
        
    except Exception as e:
        logger.error(f"Failed to load report {report_id}: {str(e)}")
        return Resource(
            uri=f"file://reports/{report_id}",
            name=f"Report {report_id}",
            description="Error loading report",
            mimeType="text/plain",
            text=f"Error loading report: {str(e)}"
        )

# List available reports
@mcp.resource("file://reports")
async def list_reports() -> Resource:
    """
    List all available test reports.
    
    Returns:
        Resource containing a list of available reports
    """
    try:
        reports_dir = os.path.join(OUTPUT_BASE_DIR, "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            
        html_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
        
        if not html_files:
            content = "No reports available yet. Run some tests to generate reports."
        else:
            report_list = []
            for filename in sorted(html_files, reverse=True):  # Most recent first
                file_path = os.path.join(reports_dir, filename)
                mtime = os.path.getmtime(file_path)
                report_list.append({
                    "filename": filename,
                    "report_id": filename.replace('.html', ''),
                    "modified": datetime.fromtimestamp(mtime).isoformat(),
                    "size": os.path.getsize(file_path)
                })
            
            content = json.dumps(report_list, indent=2)
        
        return Resource(
            uri="file://reports",
            name="Available Reports",
            description="List of all available test reports",
            mimeType="application/json",
            text=content
        )
        
    except Exception as e:
        logger.error(f"Failed to list reports: {str(e)}")
        return Resource(
            uri="file://reports",
            name="Reports Error",
            description="Error listing reports",
            mimeType="text/plain",
            text=f"Error listing reports: {str(e)}"
        )

# MCP Prompts - Provide helpful prompts for common tasks
@mcp.prompt()
async def create_api_test_plan() -> Prompt:
    """
    Generate a comprehensive API test plan template.
    """
    return Prompt(
        name="create_api_test_plan",
        description="Generate a comprehensive API test plan based on best practices",
        arguments=[
            {
                "name": "api_name",
                "description": "Name of the API to test",
                "required": True
            },
            {
                "name": "environment",
                "description": "Testing environment (dev, staging, prod)",
                "required": False
            }
        ],
        messages=[
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": """Please create a comprehensive API test plan for {{api_name}} in {{environment}} environment. Include:

1. Test Objectives and Scope
2. Test Strategy (functional, performance, security)
3. Test Data Requirements
4. Environment Setup
5. Test Scenarios Categories:
   - Positive test cases
   - Negative test cases
   - Edge cases
   - Error handling
6. Performance Testing Criteria
7. Security Testing Considerations
8. Reporting and Documentation
9. Test Automation Strategy
10. Risk Assessment

Format the plan in markdown with clear sections and actionable items."""
                }
            }
        ]
    )

@mcp.prompt()
async def analyze_test_failures() -> Prompt:
    """
    Analyze test failure patterns and suggest improvements.
    """
    return Prompt(
        name="analyze_test_failures",
        description="Analyze test failure patterns and provide recommendations",
        arguments=[
            {
                "name": "failure_data",
                "description": "Test failure data in JSON format",
                "required": True
            }
        ],
        messages=[
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": """Please analyze the following test failure data and provide insights:

{{failure_data}}

Provide:
1. Failure Pattern Analysis
2. Root Cause Assessment
3. Recommendations for fixes
4. Suggestions for preventing similar failures
5. Test improvement opportunities
6. Priority ranking of issues

Format your analysis with clear headings and actionable recommendations."""
                }
            }
        ]
    )

# Main server function
def main():
    """Main function to run the MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Tester MCP Server")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    
    logger.info("Starting API Tester MCP Server")
    
    # Run the server (FastMCP uses stdio transport by default for MCP)
    mcp.run()

if __name__ == "__main__":
    main()
