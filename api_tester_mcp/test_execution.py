"""Test case generation and execution"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from .models import TestCase, TestScenario, TestResult, ApiEndpoint, TestLanguage, TestFramework
from .utils import generate_id, logger, generate_test_data, ProgressTracker
from .code_generators import CodeGenerator
import re


class TestCaseGenerator:
    """Generate executable test cases from scenarios"""
    
    def __init__(self, base_url: str = "", env_vars: Dict[str, str] = None, 
                 language: TestLanguage = TestLanguage.PYTHON, 
                 framework: TestFramework = TestFramework.REQUESTS):
        self.base_url = base_url
        self.env_vars = env_vars or {}
        self.language = language
        self.framework = framework
        self.code_generator = CodeGenerator(language, framework)
    
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
        
        test_case = TestCase(
            id=generate_id(),
            scenario_id=scenario.id,
            name=scenario.name,
            method=endpoint.method,
            url=url,
            headers=headers,
            body=body,
            expected_status=expected_status,
            assertions=scenario.assertions,
            language=self.language,
            framework=self.framework
        )
        
        # Generate code for this test case
        session_info = {
            'id': 'current_session',
            'base_url': self.base_url,
            'auth_token': self.env_vars.get('auth_bearer', ''),
        }
        test_case.generated_code = self.code_generator.generate_test_code([test_case], session_info)
        
        return test_case
    
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
        self.progress_tracker = None
        self.completed_tests = 0
        self.total_tests = 0
    
    async def execute_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Execute test cases and return results with detailed progress tracking"""
        self.total_tests = len(test_cases)
        self.completed_tests = 0
        
        # Initialize progress tracker
        self.progress_tracker = ProgressTracker(
            total_steps=self.total_tests,
            operation_name="API Test Execution",
            enable_detailed_logging=True
        )
        self.progress_tracker.start()
        
        results = []
        
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            self.session = session
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Execute tests with progress tracking
            logger.info(f"🧪 Executing {self.total_tests} test cases with {self.max_concurrent} concurrent workers")
            
            # Execute tests concurrently
            tasks = [self._execute_test_case_with_progress(semaphore, test_case) for test_case in test_cases]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log any failures
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, TestResult):
                    valid_results.append(result)
                else:
                    logger.error(f"Test case {test_cases[i].id} failed with exception: {result}")
        
        self.progress_tracker.finish()
        
        # Log execution summary
        passed_tests = sum(1 for r in valid_results if r.status == "passed")
        failed_tests = len(valid_results) - passed_tests
        logger.info(f"📊 Test Execution Summary:")
        logger.info(f"   • Total: {len(valid_results)}")
        logger.info(f"   • Passed: {passed_tests} ({passed_tests/len(valid_results)*100:.1f}%)")
        logger.info(f"   • Failed: {failed_tests} ({failed_tests/len(valid_results)*100:.1f}%)")
        
        return valid_results
    
    async def _execute_test_case_with_progress(self, semaphore: asyncio.Semaphore, test_case: TestCase) -> TestResult:
        """Execute a single test case with progress updates"""
        result = await self._execute_test_case(semaphore, test_case)
        
        # Update progress
        self.completed_tests += 1
        step_name = f"{test_case.method} {test_case.url[:50]}{'...' if len(test_case.url) > 50 else ''}"
        if result.status == "passed":
            step_name += " ✅"
        else:
            step_name += " ❌"
            
        self.progress_tracker.update(step_name)
        
        return result
    
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
    """Execute load tests with detailed progress tracking"""
    
    def __init__(self, duration: int = 60, users: int = 10, ramp_up: int = 10):
        self.duration = duration
        self.users = users
        self.ramp_up = ramp_up
        self.progress_tracker = None
        self.start_time = None
        self.total_requests = 0
        self.completed_requests = 0
    
    async def run_load_test(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Run load test with detailed progress tracking"""
        if not test_cases:
            return {"error": "No test cases provided"}
        
        self.start_time = time.time()
        results = []
        
        # Initialize progress tracking
        # Estimate total requests based on duration and test cases
        estimated_requests_per_user = (self.duration // 2) * len(test_cases)  # Conservative estimate
        total_estimated_requests = self.users * estimated_requests_per_user
        
        self.progress_tracker = ProgressTracker(
            total_steps=max(100, total_estimated_requests // 10),  # Use percentage-based tracking
            operation_name=f"Load Test ({self.users} users, {self.duration}s)",
            enable_detailed_logging=True
        )
        self.progress_tracker.start()
        
        # Calculate user spawn rate
        spawn_rate = self.users / self.ramp_up if self.ramp_up > 0 else self.users
        
        logger.info(f"🚀 Starting load test:")
        logger.info(f"   • Users: {self.users}")
        logger.info(f"   • Duration: {self.duration}s")
        logger.info(f"   • Ramp-up: {self.ramp_up}s")
        logger.info(f"   • Test cases: {len(test_cases)}")
        logger.info(f"   • Spawn rate: {spawn_rate:.2f} users/sec")
        
        try:
            # Create connector with high limits for load testing
            connector = aiohttp.TCPConnector(limit=self.users * 2)
            async with aiohttp.ClientSession(connector=connector) as session:
                
                # Spawn users gradually with progress updates
                tasks = []
                for user_id in range(self.users):
                    delay = user_id / spawn_rate if spawn_rate > 0 else 0
                    task = asyncio.create_task(
                        self._simulate_user_with_progress(session, test_cases, user_id, delay)
                    )
                    tasks.append(task)
                    
                    # Update progress for user spawning
                    if user_id % max(1, self.users // 10) == 0:
                        spawn_percentage = (user_id / self.users) * 10  # First 10% of progress for spawning
                        self.progress_tracker.update(f"Spawned {user_id}/{self.users} users", force_log=True)
                
                # Monitor progress during execution
                monitor_task = asyncio.create_task(self._monitor_progress())
                
                # Wait for all users to complete
                user_results, _ = await asyncio.gather(
                    asyncio.gather(*tasks, return_exceptions=True),
                    monitor_task,
                    return_exceptions=True
                )
                
                # Flatten results
                for user_result in user_results:
                    if isinstance(user_result, list):
                        results.extend(user_result)
        
        except Exception as e:
            logger.error(f"Load test failed: {str(e)}")
            return {"error": str(e)}
        
        self.progress_tracker.finish()
        
        # Analyze results
        total_time = time.time() - self.start_time
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
    
    async def _simulate_user_with_progress(self, session: aiohttp.ClientSession, test_cases: List[TestCase], 
                                         user_id: int, delay: float) -> List[Dict[str, Any]]:
        """Simulate a single user's load test with progress tracking"""
        await asyncio.sleep(delay)
        
        results = []
        end_time = self.start_time + self.duration
        request_count = 0
        
        while time.time() < end_time:
            for test_case in test_cases:
                if time.time() >= end_time:
                    break
                
                request_start = time.time()
                request_count += 1
                
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
        
        logger.debug(f"User {user_id} completed {request_count} requests")
        return results
    
    async def _monitor_progress(self):
        """Monitor and report progress during load test execution"""
        monitor_interval = 2  # Update every 2 seconds
        last_update = time.time()
        
        while time.time() < self.start_time + self.duration:
            await asyncio.sleep(monitor_interval)
            
            current_time = time.time()
            elapsed = current_time - self.start_time
            progress_percentage = min(100, (elapsed / self.duration) * 100)
            
            # Calculate effective progress step
            progress_step = int((progress_percentage / 100) * self.progress_tracker.total_steps)
            
            # Only update if we've made meaningful progress
            if progress_step > self.progress_tracker.current_step:
                remaining_time = max(0, self.duration - elapsed)
                step_name = f"Running load test - {progress_percentage:.1f}% complete, {remaining_time:.0f}s remaining"
                
                # Force update to current progress
                while self.progress_tracker.current_step < progress_step:
                    self.progress_tracker.update(step_name, force_log=True)
