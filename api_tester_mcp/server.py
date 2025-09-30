"""Main MCP server implementation using FastMCP"""

import asyncio
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

# Ensure output directories exist
os.makedirs("output/reports", exist_ok=True)
os.makedirs("output/scenarios", exist_ok=True)
os.makedirs("output/test_cases", exist_ok=True)


# Pydantic models for tool parameters
class IngestSpecParams(BaseModel):
    spec_type: str
    content: str
    preferred_language: Optional[str] = "python"
    preferred_framework: Optional[str] = "requests"


class SetEnvVarsParams(BaseModel):
    variables: Dict[str, str]


class GenerateScenariosParams(BaseModel):
    include_negative_tests: bool = True
    include_edge_cases: bool = True


class GenerateTestCasesParams(BaseModel):
    scenario_ids: Optional[List[str]] = None
    language: Optional[str] = None
    framework: Optional[str] = None


class RunApiTestsParams(BaseModel):
    test_case_ids: Optional[List[str]] = None
    max_concurrent: int = 10


class RunLoadTestsParams(BaseModel):
    test_case_ids: Optional[List[str]] = None
    duration: int = 60
    users: int = 10
    ramp_up: int = 10


# MCP Tools
@mcp.tool()
async def ingest_spec(params: IngestSpecParams) -> Dict[str, Any]:
    """
    Ingest an API specification (OpenAPI/Swagger or Postman collection).
    Automatically analyzes the specification and suggests required environment variables.
    
    Args:
        spec_type: Type of specification ('openapi', 'swagger', or 'postman')
        content: The specification content as JSON or YAML string
        preferred_language: Preferred programming language for test generation (python, typescript, javascript)
        preferred_framework: Preferred testing framework (pytest, playwright, jest, etc.)
    
    Returns:
        Dictionary with ingestion results, session information, and environment variable analysis
    """
    global current_session
    
    try:
        # Validate spec type
        if params.spec_type.lower() not in ['openapi', 'swagger', 'postman']:
            return {
                "success": False,
                "error": f"Unsupported specification type: {params.spec_type}. Supported types: openapi, swagger, postman"
            }
        
        # Auto-detect spec type if needed
        detected_type = validate_spec_type(params.content)
        if detected_type and detected_type != params.spec_type.lower():
            logger.warning(f"Detected spec type '{detected_type}' differs from provided '{params.spec_type}'")
        
        # Parse specification
        parser = SpecificationParser()
        spec_type = SpecType(params.spec_type.lower())
        endpoints = parser.parse(params.content, spec_type)
        
        if not endpoints:
            return {
                "success": False,
                "error": "No API endpoints found in the specification"
            }
        
        # Analyze required environment variables
        spec_data = json.loads(params.content) if params.content.strip().startswith('{') else yaml.safe_load(params.content)
        env_analysis = analyze_required_env_vars(spec_data, spec_type, parser.base_url)
        
        # Parse language and framework preferences
        try:
            preferred_language = TestLanguage(params.preferred_language.lower())
        except ValueError:
            preferred_language = TestLanguage.PYTHON
            
        try:
            preferred_framework = TestFramework(params.preferred_framework.lower())
        except ValueError:
            preferred_framework = TestFramework.REQUESTS

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
            env_message.append("💡 Use get_env_var_suggestions() for detailed setup instructions.")
        else:
            env_message.append("✅ No authentication or environment variables required.")
        
        return {
            "success": True,
            "session_id": session_id,
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
    
    Args:
        variables: Dictionary of environment variables to set
                  Common variables: baseUrl, auth_bearer, auth_apikey, auth_basic
    
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
        # Validate URLs if present
        if "baseUrl" in params.variables:
            base_url = params.variables["baseUrl"]
            if base_url and not validate_url(base_url):
                return {
                    "success": False,
                    "error": f"Invalid base URL: {base_url}"
                }
        
        # Merge with existing variables
        current_session.env_vars = merge_env_vars(current_session.env_vars, params.variables)
        
        logger.info(f"Updated environment variables for session {current_session.id}")
        
        return {
            "success": True,
            "session_id": current_session.id,
            "variables_set": list(params.variables.keys()),
            "current_variables": {k: "***" if "auth" in k.lower() or "password" in k.lower() or "secret" in k.lower() else v 
                               for k, v in current_session.env_vars.items()}
        }
        
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
    
    Args:
        include_negative_tests: Whether to include negative test scenarios
        include_edge_cases: Whether to include edge case scenarios
    
    Returns:
        Dictionary with generated scenarios information
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
        
        # Save scenarios to file
        scenarios_file = f"output/scenarios/scenarios_{current_session.id}.json"
        with open(scenarios_file, 'w') as f:
            scenarios_data = [scenario.model_dump() for scenario in scenarios]
            json.dump(scenarios_data, f, indent=2)
        
        progress.finish()
        
        logger.info(f"Generated {len(scenarios)} scenarios for session {current_session.id}")
        
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
            "scenarios_file": scenarios_file
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to generate scenarios: {error_details}")
        return {
            "success": False,
            "error": f"Failed to generate scenarios: {error_details['message']}"
        }


@mcp.tool()
async def generate_test_cases(params: GenerateTestCasesParams) -> Dict[str, Any]:
    """
    Generate executable test cases from scenarios in the specified language and framework.
    
    Args:
        scenario_ids: Optional list of specific scenario IDs to generate test cases for.
                     If not provided, generates for all scenarios.
        language: Programming language (python, typescript, javascript). Uses session default if not provided.
        framework: Testing framework (pytest, playwright, jest, etc.). Uses session default if not provided.
    
    Returns:
        Dictionary with generated test cases information including generated code
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
        
        # Parse language and framework if provided, otherwise use session defaults
        language = current_session.preferred_language
        framework = current_session.preferred_framework
        
        if params.language:
            try:
                language = TestLanguage(params.language.lower())
            except ValueError:
                pass
        
        if params.framework:
            try:
                framework = TestFramework(params.framework.lower())
            except ValueError:
                pass

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
        
        # Save test cases to file
        test_cases_file = f"output/test_cases/test_cases_{current_session.id}.json"
        with open(test_cases_file, 'w') as f:
            test_cases_data = [test_case.model_dump() for test_case in test_cases]
            json.dump(test_cases_data, f, indent=2)
        
        progress.finish()
        
        logger.info(f"Generated {len(test_cases)} test cases for session {current_session.id}")
        
        return {
            "success": True,
            "session_id": current_session.id,
            "language": language.value,
            "framework": framework.value,
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
            "generated_code_available": all(tc.generated_code for tc in test_cases)
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to generate test cases: {error_details}")
        return {
            "success": False,
            "error": f"Failed to generate test cases: {error_details['message']}"
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
        
        logger.info(f"Starting execution of {len(test_cases_to_run)} test cases")
        test_results = await executor.execute_tests(test_cases_to_run)
        
        current_session.status = StatusType.COMPLETED
        current_session.completed_at = datetime.now().isoformat()
        
        # Generate HTML report
        html_report = report_generator.generate_api_test_report(test_results, current_session)
        report_file = f"output/reports/api_test_report_{current_session.id}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Calculate summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.status == "passed")
        failed_tests = sum(1 for r in test_results if r.status == "failed")
        total_time = sum(r.execution_time for r in test_results)
        
        logger.info(f"Test execution completed: {passed_tests}/{total_tests} passed")
        
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
        
        logger.info(f"Starting load test: {params.users} users, {params.duration}s duration")
        load_test_results = await executor.run_load_test(test_cases_to_run)
        
        if "error" in load_test_results:
            return {
                "success": False,
                "error": load_test_results["error"]
            }
        
        # Generate HTML report
        html_report = report_generator.generate_load_test_report(load_test_results, current_session)
        report_file = f"output/reports/load_test_report_{current_session.id}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        logger.info(f"Load test completed: {load_test_results['summary']['requests_per_second']:.1f} req/s")
        
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
async def get_env_var_suggestions() -> Dict[str, Any]:
    """
    Get environment variable suggestions based on the ingested API specification.
    
    Returns:
        Dictionary with suggested environment variables and their descriptions
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session. Please ingest a specification first."
        }
    
    try:
        # Re-analyze the specification for environment variables
        env_analysis = analyze_required_env_vars(
            current_session.spec_content, 
            current_session.spec_type,
            ""  # base_url will be extracted from spec_content
        )
        
        # Check which variables are already set
        current_vars = current_session.env_vars
        suggestions = {}
        
        # Process required variables
        for var_name, var_info in env_analysis.get("required_variables", {}).items():
            is_set = var_name in current_vars
            suggestions[var_name] = {
                **var_info,
                "currently_set": is_set,
                "current_value": "***" if is_set and ("auth" in var_name.lower() or "secret" in var_name.lower() or "password" in var_name.lower()) else current_vars.get(var_name, None),
                "priority": "required"
            }
        
        # Process optional variables
        for var_name, var_info in env_analysis.get("optional_variables", {}).items():
            is_set = var_name in current_vars
            suggestions[var_name] = {
                **var_info,
                "currently_set": is_set,
                "current_value": "***" if is_set and ("auth" in var_name.lower() or "secret" in var_name.lower() or "password" in var_name.lower()) else current_vars.get(var_name, None),
                "priority": "optional"
            }
        
        # Generate setup instructions
        missing_required = [var for var, info in suggestions.items() if info["priority"] == "required" and not info["currently_set"]]
        setup_instructions = []
        
        if missing_required:
            setup_instructions.append("⚠️  Required environment variables missing:")
            for var in missing_required:
                var_info = suggestions[var]
                if "detected_value" in var_info:
                    setup_instructions.append(f"   • {var}: {var_info['description']} (Suggested: {var_info['detected_value']})")
                else:
                    setup_instructions.append(f"   • {var}: {var_info['description']}")
            
            setup_instructions.append("\n💡 Use the set_env_vars tool to configure these variables:")
            example_vars = {}
            for var in missing_required:
                if "detected_value" in suggestions[var]:
                    example_vars[var] = suggestions[var]["detected_value"]
                elif var == "auth_bearer":
                    example_vars[var] = "your-bearer-token"
                elif var == "auth_apikey":
                    example_vars[var] = "your-api-key"
                elif var == "auth_basic":
                    example_vars[var] = "base64-encoded-credentials"
                else:
                    example_vars[var] = "your-value"
            
            setup_instructions.append(f"   await set_env_vars({json.dumps({'variables': example_vars}, indent=2)})")
        else:
            setup_instructions.append("✅ All required environment variables are configured!")
        
        return {
            "success": True,
            "session_id": current_session.id,
            "suggested_variables": suggestions,
            "required_missing_count": len(missing_required),
            "total_suggestions": len(suggestions),
            "setup_instructions": setup_instructions,
            **env_analysis  # Include the original analysis
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to get environment variable suggestions: {error_details}")
        return {
            "success": False,
            "error": f"Failed to analyze environment variables: {error_details['message']}"
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
    language: str
    framework: str
    project_name: Optional[str] = "api-tests"
    include_examples: bool = True


@mcp.tool()
async def generate_project_files(params: GenerateProjectParams) -> Dict[str, Any]:
    """
    Generate complete project files for the selected language and framework.
    
    Args:
        language: Programming language (python, typescript, javascript)
        framework: Testing framework (pytest, playwright, jest, etc.)
        project_name: Name for the generated project
        include_examples: Whether to include example test files
    
    Returns:
        Dictionary with generated project files and setup instructions
    """
    global current_session
    
    try:
        # Validate language and framework
        try:
            language_enum = TestLanguage(params.language.lower())
            framework_enum = TestFramework(params.framework.lower())
        except ValueError as e:
            return {
                "success": False,
                "error": f"Unsupported language/framework combination: {params.language}/{params.framework}"
            }
        
        # Generate package files
        package_files = generate_package_files(language_enum, framework_enum)
        
        # Generate example test files if requested and session exists
        example_files = {}
        if params.include_examples and current_session and current_session.test_cases:
            try:
                generator = TestCaseGenerator(
                    base_url=current_session.env_vars.get("baseUrl", ""),
                    env_vars=current_session.env_vars,
                    language=language_enum,
                    framework=framework_enum
                )
                
                # Generate code for existing test cases
                session_info = {
                    'id': current_session.id,
                    'base_url': current_session.env_vars.get("baseUrl", ""),
                    'auth_token': current_session.env_vars.get('auth_bearer', ''),
                }
                
                code_generator = generator.code_generator
                test_code = code_generator.generate_test_code(current_session.test_cases[:5], session_info)
                
                # Determine file extension and path
                if language_enum == TestLanguage.PYTHON:
                    if framework_enum == TestFramework.PYTEST:
                        example_files["tests/test_api.py"] = test_code
                    else:
                        example_files["test_api.py"] = test_code
                elif language_enum == TestLanguage.TYPESCRIPT:
                    if framework_enum == TestFramework.PLAYWRIGHT:
                        example_files["tests/api.spec.ts"] = test_code
                    else:
                        example_files["tests/api.test.ts"] = test_code
                elif language_enum == TestLanguage.JAVASCRIPT:
                    if framework_enum == TestFramework.CYPRESS:
                        example_files["cypress/e2e/api.cy.js"] = test_code
                    else:
                        example_files["tests/api.test.js"] = test_code
                        
            except Exception as e:
                logger.warning(f"Failed to generate example files: {str(e)}")
        
        # Generate setup instructions
        setup_instructions = _generate_setup_instructions(language_enum, framework_enum, params.project_name)
        
        # Save files to output directory if possible
        import os
        project_dir = f"output/generated_projects/{params.project_name}"
        os.makedirs(project_dir, exist_ok=True)
        
        saved_files = []
        all_files = {**package_files, **example_files}
        
        for filename, content in all_files.items():
            file_path = os.path.join(project_dir, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files.append(file_path)
        
        logger.info(f"Generated {params.language}/{params.framework} project: {project_dir}")
        
        return {
            "success": True,
            "language": params.language,
            "framework": params.framework,
            "project_name": params.project_name,
            "project_directory": project_dir,
            "generated_files": {
                "package_files": list(package_files.keys()),
                "example_files": list(example_files.keys()) if example_files else [],
                "all_files": list(all_files.keys())
            },
            "file_contents": all_files,
            "setup_instructions": setup_instructions,
            "saved_files": saved_files
        }
        
    except Exception as e:
        error_details = extract_error_details(e)
        logger.error(f"Failed to generate project files: {error_details}")
        return {
            "success": False,
            "error": f"Failed to generate project files: {error_details['message']}"
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
        "env_vars": current_session.env_vars
    }
    
    # Add progress information if there's an active operation
    # This would be enhanced with a global progress tracker for the current operation
    if hasattr(current_session, 'current_operation_progress'):
        session_info["current_operation"] = current_session.current_operation_progress
    
    return session_info


@mcp.tool()
async def get_operation_progress() -> Dict[str, Any]:
    """
    Get detailed progress information for the current operation.
    
    Returns:
        Dictionary with detailed progress information
    """
    global current_session
    
    if not current_session:
        return {
            "success": False,
            "error": "No active session"
        }
    
    # This would be enhanced with actual progress tracking
    # For now, return basic status
    return {
        "success": True,
        "session_id": current_session.id,
        "status": current_session.status.value,
        "message": "Progress tracking will be available during test execution"
    }


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
        report_file = f"output/reports/{report_id}.html"
        
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
        reports_dir = "output/reports"
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
