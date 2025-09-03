"""Test case generation and execution"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from .models import TestCase, TestScenario, TestResult, ApiEndpoint
from .utils import generate_id, logger, generate_test_data
import re


class TestCaseGenerator:
    """Generate executable test cases from scenarios"""
    
    def __init__(self, base_url: str = "", env_vars: Dict[str, str] = None):
        self.base_url = base_url
        self.env_vars = env_vars or {}
    
    def generate_test_cases(self, scenarios: List[TestScenario]) -> List[TestCase]:
        """Generate test cases from scenarios"""
        test_cases = []
        
        for scenario in scenarios:
            test_case = self._scenario_to_test_case(scenario)
            test_cases.append(test_case)
        
        return test_cases
    
    def _scenario_to_test_case(self, scenario: TestScenario) -> TestCase:
        """Convert a scenario to an executable test case"""
        endpoint = scenario.endpoint
        
        # Build URL
        url = self._build_url(endpoint.path)
        
        # Build headers
        headers = self._build_headers(endpoint)
        
        # Build request body
        body = self._build_request_body(endpoint)
        
        # Determine expected status
        expected_status = self._get_expected_status(scenario)
        
        return TestCase(
            id=generate_id(),
            scenario_id=scenario.id,
            name=scenario.name,
            method=endpoint.method,
            url=url,
            headers=headers,
            body=body,
            expected_status=expected_status,
            assertions=scenario.assertions
        )
    
    def _build_url(self, path: str) -> str:
        """Build full URL from path"""
        base = self.base_url or self.env_vars.get("baseUrl", "")
        
        # Replace path parameters with actual values
        url = f"{base.rstrip('/')}{path}"
        
        # Replace template variables
        for key, value in self.env_vars.items():
            url = url.replace(f"{{{key}}}", value)
            url = url.replace(f"{{{{key}}}}", value)
        
        return url
    
    def _build_headers(self, endpoint: ApiEndpoint) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add authentication headers
        if endpoint.auth_required:
            if "auth_bearer" in self.env_vars:
                headers["Authorization"] = f"Bearer {self.env_vars['auth_bearer']}"
            elif "auth_apikey" in self.env_vars:
                headers["X-API-Key"] = self.env_vars["auth_apikey"]
            elif "auth_basic" in self.env_vars:
                headers["Authorization"] = f"Basic {self.env_vars['auth_basic']}"
        
        return headers
    
    def _build_request_body(self, endpoint: ApiEndpoint) -> Optional[Dict[str, Any]]:
        """Build request body from schema"""
        if not endpoint.request_body or endpoint.method in ["GET", "DELETE"]:
            return None
        
        request_body = endpoint.request_body
        
        if isinstance(request_body, dict):
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            
            if schema:
                return generate_test_data(schema)
        
        return {}
    
    def _get_expected_status(self, scenario: TestScenario) -> int:
        """Get expected status code from scenario"""
        for assertion in scenario.assertions:
            if assertion.get("type") == "status_code":
                value = assertion.get("value")
                if isinstance(value, list) and value:
                    return value[0]
                elif isinstance(value, int):
                    return value
        
        return 200


class TestExecutor:
    """Execute test cases and generate results"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.session = None
    
    async def execute_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Execute test cases and return results"""
        results = []
        
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            self.session = session
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Execute tests concurrently
            tasks = [self._execute_test_case(semaphore, test_case) for test_case in test_cases]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = [r for r in results if isinstance(r, TestResult)]
            
        return valid_results
    
    async def _execute_test_case(self, semaphore: asyncio.Semaphore, test_case: TestCase) -> TestResult:
        """Execute a single test case"""
        async with semaphore:
            start_time = time.time()
            
            try:
                # Prepare request
                kwargs = {
                    "method": test_case.method,
                    "url": test_case.url,
                    "headers": test_case.headers,
                    "timeout": aiohttp.ClientTimeout(total=test_case.timeout)
                }
                
                if test_case.body:
                    kwargs["json"] = test_case.body
                
                # Execute request
                async with self.session.request(**kwargs) as response:
                    execution_time = time.time() - start_time
                    response_body = await response.text()
                    
                    # Create result
                    result = TestResult(
                        test_case_id=test_case.id,
                        status="completed",
                        execution_time=execution_time,
                        response_status=response.status,
                        response_body=response_body,
                        response_headers=dict(response.headers)
                    )
                    
                    # Run assertions
                    self._run_assertions(result, test_case, response, execution_time)
                    
                    return result
                    
            except Exception as e:
                execution_time = time.time() - start_time
                return TestResult(
                    test_case_id=test_case.id,
                    status="failed",
                    execution_time=execution_time,
                    error_message=str(e)
                )
    
    def _run_assertions(self, result: TestResult, test_case: TestCase, response, execution_time: float):
        """Run assertions on test result"""
        for assertion in test_case.assertions:
            assertion_result = self._evaluate_assertion(assertion, response, execution_time)
            
            result.assertion_details.append({
                "assertion": assertion,
                "passed": assertion_result["passed"],
                "message": assertion_result["message"]
            })
            
            if assertion_result["passed"]:
                result.assertions_passed += 1
            else:
                result.assertions_failed += 1
        
        # Set overall status
        if result.assertions_failed > 0:
            result.status = "failed"
        else:
            result.status = "passed"
    
    def _evaluate_assertion(self, assertion: Dict[str, Any], response, execution_time: float) -> Dict[str, Any]:
        """Evaluate a single assertion"""
        assertion_type = assertion.get("type")
        operator = assertion.get("operator")
        expected_value = assertion.get("value")
        
        try:
            if assertion_type == "status_code":
                actual_value = response.status
                return self._compare_values(actual_value, operator, expected_value, "Status code")
            
            elif assertion_type == "response_time":
                actual_value = execution_time * 1000  # Convert to milliseconds
                return self._compare_values(actual_value, operator, expected_value, "Response time")
            
            elif assertion_type == "content_type":
                actual_value = response.headers.get("content-type", "")
                return self._compare_values(actual_value, operator, expected_value, "Content type")
            
            elif assertion_type == "header":
                header_name = assertion.get("header")
                actual_value = response.headers.get(header_name, "")
                return self._compare_values(actual_value, operator, expected_value, f"Header {header_name}")
            
            else:
                return {"passed": False, "message": f"Unknown assertion type: {assertion_type}"}
        
        except Exception as e:
            return {"passed": False, "message": f"Assertion error: {str(e)}"}
    
    def _compare_values(self, actual, operator: str, expected, description: str) -> Dict[str, Any]:
        """Compare actual and expected values using operator"""
        try:
            if operator == "eq":
                passed = actual == expected
            elif operator == "ne":
                passed = actual != expected
            elif operator == "lt":
                passed = actual < expected
            elif operator == "le":
                passed = actual <= expected
            elif operator == "gt":
                passed = actual > expected
            elif operator == "ge":
                passed = actual >= expected
            elif operator == "in":
                passed = actual in expected
            elif operator == "not_in":
                passed = actual not in expected
            elif operator == "contains":
                passed = str(expected).lower() in str(actual).lower()
            elif operator == "not_contains":
                passed = str(expected).lower() not in str(actual).lower()
            elif operator == "regex":
                passed = bool(re.search(expected, str(actual)))
            else:
                return {"passed": False, "message": f"Unknown operator: {operator}"}
            
            message = f"{description}: expected {operator} {expected}, got {actual}"
            return {"passed": passed, "message": message}
        
        except Exception as e:
            return {"passed": False, "message": f"Comparison error: {str(e)}"}


class LoadTestExecutor:
    """Execute load tests"""
    
    def __init__(self, duration: int = 60, users: int = 10, ramp_up: int = 10):
        self.duration = duration
        self.users = users
        self.ramp_up = ramp_up
    
    async def run_load_test(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Run load test with specified parameters"""
        if not test_cases:
            return {"error": "No test cases provided"}
        
        start_time = time.time()
        results = []
        
        # Calculate user spawn rate
        spawn_rate = self.users / self.ramp_up if self.ramp_up > 0 else self.users
        
        try:
            # Create connector with high limits for load testing
            connector = aiohttp.TCPConnector(limit=self.users * 2)
            async with aiohttp.ClientSession(connector=connector) as session:
                
                # Spawn users gradually
                tasks = []
                for user_id in range(self.users):
                    delay = user_id / spawn_rate if spawn_rate > 0 else 0
                    task = asyncio.create_task(
                        self._simulate_user(session, test_cases, user_id, delay, start_time)
                    )
                    tasks.append(task)
                
                # Wait for all users to complete
                user_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Flatten results
                for user_result in user_results:
                    if isinstance(user_result, list):
                        results.extend(user_result)
        
        except Exception as e:
            logger.error(f"Load test failed: {str(e)}")
            return {"error": str(e)}
        
        # Analyze results
        total_time = time.time() - start_time
        return self._analyze_load_test_results(results, total_time)
    
    async def _simulate_user(self, session: aiohttp.ClientSession, test_cases: List[TestCase], 
                           user_id: int, delay: float, start_time: float) -> List[Dict[str, Any]]:
        """Simulate a single user's load test"""
        await asyncio.sleep(delay)
        
        results = []
        end_time = start_time + self.duration
        
        while time.time() < end_time:
            for test_case in test_cases:
                if time.time() >= end_time:
                    break
                
                request_start = time.time()
                try:
                    kwargs = {
                        "method": test_case.method,
                        "url": test_case.url,
                        "headers": test_case.headers,
                        "timeout": aiohttp.ClientTimeout(total=test_case.timeout)
                    }
                    
                    if test_case.body:
                        kwargs["json"] = test_case.body
                    
                    async with session.request(**kwargs) as response:
                        request_time = time.time() - request_start
                        
                        result = {
                            "user_id": user_id,
                            "test_case_id": test_case.id,
                            "status_code": response.status,
                            "response_time": request_time,
                            "success": 200 <= response.status < 400,
                            "timestamp": request_start
                        }
                        results.append(result)
                
                except Exception as e:
                    request_time = time.time() - request_start
                    result = {
                        "user_id": user_id,
                        "test_case_id": test_case.id,
                        "status_code": 0,
                        "response_time": request_time,
                        "success": False,
                        "error": str(e),
                        "timestamp": request_start
                    }
                    results.append(result)
        
        return results
    
    def _analyze_load_test_results(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Analyze load test results"""
        if not results:
            return {"error": "No results to analyze"}
        
        # Basic statistics
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r.get("success", False))
        failed_requests = total_requests - successful_requests
        
        # Response time statistics
        response_times = [r["response_time"] for r in results]
        response_times.sort()
        
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Percentiles
        p50 = response_times[int(len(response_times) * 0.5)]
        p90 = response_times[int(len(response_times) * 0.9)]
        p95 = response_times[int(len(response_times) * 0.95)]
        p99 = response_times[int(len(response_times) * 0.99)]
        
        # Throughput
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        
        # Status code distribution
        status_codes = {}
        for result in results:
            status = result.get("status_code", 0)
            status_codes[status] = status_codes.get(status, 0) + 1
        
        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
                "duration": total_time,
                "requests_per_second": requests_per_second
            },
            "response_times": {
                "average": avg_response_time,
                "minimum": min_response_time,
                "maximum": max_response_time,
                "p50": p50,
                "p90": p90,
                "p95": p95,
                "p99": p99
            },
            "status_codes": status_codes,
            "raw_results": results
        }
