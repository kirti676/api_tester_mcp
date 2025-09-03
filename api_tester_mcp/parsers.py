"""Specification parsers for OpenAPI/Swagger and Postman collections"""

import json
import yaml
import re
from typing import Dict, List, Any, Optional
from .models import ApiEndpoint, SpecType, TestScenario
from .utils import generate_id, logger


class SpecificationParser:
    """Base class for specification parsers"""
    
    def __init__(self):
        self.spec_type = None
        self.spec_data = {}
        self.base_url = ""
        self.endpoints = []
    
    def parse(self, content: str, spec_type: SpecType) -> List[ApiEndpoint]:
        """Parse specification content and return endpoints"""
        try:
            # Try JSON first
            try:
                self.spec_data = json.loads(content)
            except json.JSONDecodeError:
                # Try YAML
                self.spec_data = yaml.safe_load(content)
            
            self.spec_type = spec_type
            
            if spec_type in [SpecType.OPENAPI, SpecType.SWAGGER]:
                return self._parse_openapi()
            elif spec_type == SpecType.POSTMAN:
                return self._parse_postman()
            else:
                raise ValueError(f"Unsupported specification type: {spec_type}")
                
        except Exception as e:
            logger.error(f"Failed to parse specification: {str(e)}")
            raise
    
    def _parse_openapi(self) -> List[ApiEndpoint]:
        """Parse OpenAPI/Swagger specification"""
        endpoints = []
        
        # Extract base URL
        if "servers" in self.spec_data and self.spec_data["servers"]:
            self.base_url = self.spec_data["servers"][0].get("url", "")
        elif "host" in self.spec_data:
            scheme = self.spec_data.get("schemes", ["https"])[0]
            base_path = self.spec_data.get("basePath", "")
            self.base_url = f"{scheme}://{self.spec_data['host']}{base_path}"
        
        # Parse paths
        paths = self.spec_data.get("paths", {})
        for path, path_obj in paths.items():
            for method, operation in path_obj.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                    endpoint = self._create_openapi_endpoint(path, method.upper(), operation)
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _create_openapi_endpoint(self, path: str, method: str, operation: Dict[str, Any]) -> ApiEndpoint:
        """Create ApiEndpoint from OpenAPI operation"""
        # Extract parameters
        parameters = []
        if "parameters" in operation:
            parameters.extend(operation["parameters"])
        
        # Extract request body
        request_body = None
        if "requestBody" in operation:
            request_body = operation["requestBody"]
        
        # Extract responses
        responses = operation.get("responses", {})
        
        # Check if auth is required
        auth_required = "security" in operation or "security" in self.spec_data
        
        return ApiEndpoint(
            path=path,
            method=method,
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            tags=operation.get("tags", []),
            auth_required=auth_required
        )
    
    def _parse_postman(self) -> List[ApiEndpoint]:
        """Parse Postman collection"""
        endpoints = []
        
        # Extract base URL from collection variables
        variables = self.spec_data.get("variable", [])
        for var in variables:
            if var.get("key") == "baseUrl":
                self.base_url = var.get("value", "")
                break
        
        # Parse items (requests)
        items = self._flatten_postman_items(self.spec_data.get("item", []))
        
        for item in items:
            if "request" in item:
                endpoint = self._create_postman_endpoint(item)
                endpoints.append(endpoint)
        
        return endpoints
    
    def _flatten_postman_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Flatten nested Postman collection items"""
        flattened = []
        
        for item in items:
            if "item" in item:
                # This is a folder, recurse
                flattened.extend(self._flatten_postman_items(item["item"]))
            else:
                # This is a request
                flattened.append(item)
        
        return flattened
    
    def _create_postman_endpoint(self, item: Dict[str, Any]) -> ApiEndpoint:
        """Create ApiEndpoint from Postman request"""
        request = item["request"]
        
        # Extract method
        method = request.get("method", "GET").upper()
        
        # Extract URL and path
        url = request.get("url", {})
        if isinstance(url, str):
            path = url.replace(self.base_url, "") if self.base_url else url
        else:
            raw_url = url.get("raw", "")
            path = raw_url.replace(self.base_url, "") if self.base_url else raw_url
            if "path" in url:
                path = "/" + "/".join(url["path"])
        
        # Extract parameters
        parameters = []
        if isinstance(url, dict) and "query" in url:
            for param in url["query"]:
                parameters.append({
                    "name": param.get("key", ""),
                    "in": "query",
                    "value": param.get("value", ""),
                    "description": param.get("description", "")
                })
        
        # Extract request body
        request_body = None
        if "body" in request:
            request_body = request["body"]
        
        # Check for auth
        auth_required = "auth" in request or "auth" in self.spec_data
        
        return ApiEndpoint(
            path=path,
            method=method,
            summary=item.get("name", ""),
            description=item.get("description", ""),
            parameters=parameters,
            request_body=request_body,
            responses={},
            tags=[],
            auth_required=auth_required
        )


class ScenarioGenerator:
    """Generate test scenarios from API endpoints"""
    
    def __init__(self):
        self.parser = SpecificationParser()
    
    def generate_scenarios(self, endpoints: List[ApiEndpoint]) -> List[TestScenario]:
        """Generate test scenarios from endpoints"""
        scenarios = []
        
        for endpoint in endpoints:
            # Generate positive test scenario
            positive_scenario = self._generate_positive_scenario(endpoint)
            scenarios.append(positive_scenario)
            
            # Generate negative test scenarios
            negative_scenarios = self._generate_negative_scenarios(endpoint)
            scenarios.extend(negative_scenarios)
            
            # Generate edge case scenarios
            edge_scenarios = self._generate_edge_case_scenarios(endpoint)
            scenarios.extend(edge_scenarios)
        
        return scenarios
    
    def _generate_positive_scenario(self, endpoint: ApiEndpoint) -> TestScenario:
        """Generate positive test scenario"""
        scenario_id = generate_id()
        
        steps = [
            f"1. Send {endpoint.method} request to {endpoint.path}",
            "2. Include required authentication if needed",
            "3. Include valid request parameters and body",
            "4. Verify response status code",
            "5. Verify response body structure"
        ]
        
        pass_criteria = [
            "Response status code is 2xx",
            "Response time is under 5 seconds",
            "Response body matches expected schema"
        ]
        
        fail_criteria = [
            "Response status code is 4xx or 5xx",
            "Response time exceeds 5 seconds",
            "Response body is malformed"
        ]
        
        assertions = [
            {"type": "status_code", "operator": "in", "value": [200, 201, 202, 204]},
            {"type": "response_time", "operator": "lt", "value": 5000},
            {"type": "content_type", "operator": "contains", "value": "json"}
        ]
        
        return TestScenario(
            id=scenario_id,
            name=f"Positive test for {endpoint.method} {endpoint.path}",
            objective=f"Verify that {endpoint.method} {endpoint.path} works correctly with valid input",
            endpoint=endpoint,
            steps=steps,
            expected_outcome="Request succeeds with valid response",
            pass_criteria=pass_criteria,
            fail_criteria=fail_criteria,
            assertions=assertions
        )
    
    def _generate_negative_scenarios(self, endpoint: ApiEndpoint) -> List[TestScenario]:
        """Generate negative test scenarios"""
        scenarios = []
        
        # Unauthorized access test
        if endpoint.auth_required:
            scenario = TestScenario(
                id=generate_id(),
                name=f"Unauthorized access test for {endpoint.method} {endpoint.path}",
                objective="Verify that unauthorized requests are rejected",
                endpoint=endpoint,
                steps=[
                    f"1. Send {endpoint.method} request to {endpoint.path}",
                    "2. Do not include authentication headers",
                    "3. Verify response status code is 401"
                ],
                expected_outcome="Request is rejected with 401 Unauthorized",
                pass_criteria=["Response status code is 401"],
                fail_criteria=["Response status code is not 401"],
                assertions=[
                    {"type": "status_code", "operator": "eq", "value": 401}
                ]
            )
            scenarios.append(scenario)
        
        # Invalid method test
        if endpoint.method != "GET":
            scenario = TestScenario(
                id=generate_id(),
                name=f"Invalid method test for {endpoint.path}",
                objective="Verify that invalid HTTP methods are rejected",
                endpoint=endpoint,
                steps=[
                    f"1. Send INVALID request to {endpoint.path}",
                    "2. Verify response status code is 405"
                ],
                expected_outcome="Request is rejected with 405 Method Not Allowed",
                pass_criteria=["Response status code is 405"],
                fail_criteria=["Response status code is not 405"],
                assertions=[
                    {"type": "status_code", "operator": "eq", "value": 405}
                ]
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_edge_case_scenarios(self, endpoint: ApiEndpoint) -> List[TestScenario]:
        """Generate edge case test scenarios"""
        scenarios = []
        
        # Large payload test (for POST/PUT endpoints)
        if endpoint.method in ["POST", "PUT", "PATCH"] and endpoint.request_body:
            scenario = TestScenario(
                id=generate_id(),
                name=f"Large payload test for {endpoint.method} {endpoint.path}",
                objective="Verify system handles large request payloads gracefully",
                endpoint=endpoint,
                steps=[
                    f"1. Send {endpoint.method} request to {endpoint.path}",
                    "2. Include a very large request body",
                    "3. Verify response status code and time"
                ],
                expected_outcome="Request is handled appropriately (accepted or rejected gracefully)",
                pass_criteria=["Response status code is either 2xx or 413", "Response time is reasonable"],
                fail_criteria=["Server timeout or crash"],
                assertions=[
                    {"type": "status_code", "operator": "in", "value": [200, 201, 413]},
                    {"type": "response_time", "operator": "lt", "value": 30000}
                ]
            )
            scenarios.append(scenario)
        
        return scenarios
