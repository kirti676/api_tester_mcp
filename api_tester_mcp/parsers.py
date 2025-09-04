"""Specification parsers for OpenAPI/Swagger and Postman collections"""

import json
import yaml
import re
from typing import Dict, List, Any, Optional, Set
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


def analyze_required_env_vars(spec_data: Dict[str, Any], spec_type: SpecType, base_url: str = "") -> Dict[str, Any]:
    """
    Analyze API specification to determine required environment variables
    
    Args:
        spec_data: Parsed specification data
        spec_type: Type of specification (OpenAPI, Swagger, Postman)
        base_url: Base URL extracted from spec
    
    Returns:
        Dictionary containing required and optional environment variables with descriptions
    """
    required_vars = {}
    optional_vars = {}
    detected_auth_schemes = set()
    
    try:
        if spec_type in [SpecType.OPENAPI, SpecType.SWAGGER]:
            required_vars, optional_vars, detected_auth_schemes = _analyze_openapi_env_vars(spec_data, base_url)
        elif spec_type == SpecType.POSTMAN:
            required_vars, optional_vars, detected_auth_schemes = _analyze_postman_env_vars(spec_data, base_url)
        
        # Always suggest baseUrl if not already provided
        if base_url and "baseUrl" not in required_vars and "baseUrl" not in optional_vars:
            required_vars["baseUrl"] = {
                "description": f"API base URL (detected: {base_url})",
                "detected_value": base_url,
                "required": True
            }
        elif not base_url:
            required_vars["baseUrl"] = {
                "description": "API base URL (not detected in specification)",
                "required": True
            }
        
        return {
            "required_variables": required_vars,
            "optional_variables": optional_vars,
            "detected_auth_schemes": list(detected_auth_schemes),
            "total_vars_needed": len(required_vars),
            "analysis_summary": _generate_env_analysis_summary(required_vars, optional_vars, detected_auth_schemes)
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze environment variables: {str(e)}")
        return {
            "required_variables": {},
            "optional_variables": {},
            "detected_auth_schemes": [],
            "total_vars_needed": 0,
            "analysis_summary": "Failed to analyze specification for environment variables",
            "error": str(e)
        }


def _analyze_openapi_env_vars(spec_data: Dict[str, Any], base_url: str) -> tuple:
    """Analyze OpenAPI/Swagger specification for environment variables"""
    required_vars = {}
    optional_vars = {}
    detected_auth_schemes = set()
    
    # Check global security requirements
    global_security = spec_data.get("security", [])
    security_schemes = spec_data.get("components", {}).get("securitySchemes", {})
    
    # For older Swagger specs
    if not security_schemes:
        security_schemes = spec_data.get("securityDefinitions", {})
    
    # Analyze security schemes
    auth_required = bool(global_security) or _has_endpoint_security(spec_data)
    
    if auth_required:
        for scheme_name, scheme_def in security_schemes.items():
            scheme_type = scheme_def.get("type", "").lower()
            detected_auth_schemes.add(scheme_type)
            
            if scheme_type == "http":
                scheme_scheme = scheme_def.get("scheme", "").lower()
                if scheme_scheme == "bearer":
                    required_vars["auth_bearer"] = {
                        "description": f"Bearer token for {scheme_name} authentication",
                        "required": True,
                        "auth_scheme": scheme_name
                    }
                elif scheme_scheme == "basic":
                    required_vars["auth_basic"] = {
                        "description": f"Basic authentication credentials (base64 encoded) for {scheme_name}",
                        "required": True,
                        "auth_scheme": scheme_name
                    }
            elif scheme_type == "apikey":
                location = scheme_def.get("in", "header")
                name = scheme_def.get("name", "X-API-Key")
                required_vars["auth_apikey"] = {
                    "description": f"API key for {scheme_name} authentication (sent in {location}: {name})",
                    "required": True,
                    "auth_scheme": scheme_name,
                    "location": location,
                    "parameter_name": name
                }
            elif scheme_type == "oauth2":
                optional_vars["auth_bearer"] = {
                    "description": f"OAuth2 access token for {scheme_name} authentication",
                    "required": False,
                    "auth_scheme": scheme_name
                }
    
    # Check for path parameters that might need environment variables
    paths = spec_data.get("paths", {})
    for path, path_obj in paths.items():
        # Look for templated path parameters
        template_vars = re.findall(r'\{([^}]+)\}', path)
        for var in template_vars:
            if var not in optional_vars and var not in required_vars:
                optional_vars[var] = {
                    "description": f"Path parameter value for '{var}' in {path}",
                    "required": False,
                    "type": "path_parameter"
                }
        
        # Check operation-specific security
        for method, operation in path_obj.items():
            if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                op_security = operation.get("security", [])
                if op_security and not auth_required:
                    # This endpoint has specific auth requirements
                    for sec_req in op_security:
                        for scheme_name in sec_req.keys():
                            if scheme_name in security_schemes:
                                scheme_def = security_schemes[scheme_name]
                                scheme_type = scheme_def.get("type", "").lower()
                                detected_auth_schemes.add(scheme_type)
                                
                                if scheme_type == "http" and scheme_def.get("scheme") == "bearer":
                                    optional_vars["auth_bearer"] = {
                                        "description": f"Bearer token for {scheme_name} authentication (required for some endpoints)",
                                        "required": False,
                                        "auth_scheme": scheme_name
                                    }
                                elif scheme_type == "apikey":
                                    optional_vars["auth_apikey"] = {
                                        "description": f"API key for {scheme_name} authentication (required for some endpoints)",
                                        "required": False,
                                        "auth_scheme": scheme_name
                                    }
    
    return required_vars, optional_vars, detected_auth_schemes


def _analyze_postman_env_vars(spec_data: Dict[str, Any], base_url: str) -> tuple:
    """Analyze Postman collection for environment variables"""
    required_vars = {}
    optional_vars = {}
    detected_auth_schemes = set()
    
    # Check collection-level variables
    variables = spec_data.get("variable", [])
    for var in variables:
        var_key = var.get("key", "")
        var_value = var.get("value", "")
        var_desc = var.get("description", f"Collection variable: {var_key}")
        
        if var_key and not var_value:  # Variable is defined but has no value
            if "baseurl" in var_key.lower() or "url" in var_key.lower():
                if var_key != "baseUrl":  # Don't duplicate if already handled
                    optional_vars[var_key] = {
                        "description": f"Base URL variable: {var_desc}",
                        "required": False,
                        "type": "url"
                    }
            elif "auth" in var_key.lower() or "token" in var_key.lower() or "key" in var_key.lower():
                optional_vars[var_key] = {
                    "description": f"Authentication variable: {var_desc}",
                    "required": False,
                    "type": "auth"
                }
            else:
                optional_vars[var_key] = {
                    "description": var_desc,
                    "required": False,
                    "type": "general"
                }
    
    # Check collection-level auth
    collection_auth = spec_data.get("auth", {})
    if collection_auth:
        auth_type = collection_auth.get("type", "").lower()
        detected_auth_schemes.add(auth_type)
        
        if auth_type == "bearer":
            required_vars["auth_bearer"] = {
                "description": "Bearer token for collection-level authentication",
                "required": True,
                "auth_scheme": "bearer"
            }
        elif auth_type == "apikey":
            required_vars["auth_apikey"] = {
                "description": "API key for collection-level authentication",
                "required": True,
                "auth_scheme": "apikey"
            }
        elif auth_type == "basic":
            required_vars["auth_basic"] = {
                "description": "Basic authentication credentials (base64 encoded)",
                "required": True,
                "auth_scheme": "basic"
            }
    
    # Check request-level auth and variables
    items = _flatten_postman_items_for_analysis(spec_data.get("item", []))
    template_vars = set()
    
    for item in items:
        if "request" in item:
            request = item["request"]
            
            # Check request-level auth
            request_auth = request.get("auth", {})
            if request_auth and not collection_auth:
                auth_type = request_auth.get("type", "").lower()
                detected_auth_schemes.add(auth_type)
                
                if auth_type == "bearer" and "auth_bearer" not in required_vars:
                    optional_vars["auth_bearer"] = {
                        "description": "Bearer token for request-level authentication",
                        "required": False,
                        "auth_scheme": "bearer"
                    }
                elif auth_type == "apikey" and "auth_apikey" not in required_vars:
                    optional_vars["auth_apikey"] = {
                        "description": "API key for request-level authentication",
                        "required": False,
                        "auth_scheme": "apikey"
                    }
            
            # Extract template variables from URL
            url = request.get("url", {})
            if isinstance(url, str):
                url_vars = re.findall(r'\{\{([^}]+)\}\}', url)
                template_vars.update(url_vars)
            elif isinstance(url, dict):
                raw_url = url.get("raw", "")
                url_vars = re.findall(r'\{\{([^}]+)\}\}', raw_url)
                template_vars.update(url_vars)
                
                # Check query parameters
                for query_param in url.get("query", []):
                    param_value = query_param.get("value", "")
                    query_vars = re.findall(r'\{\{([^}]+)\}\}', param_value)
                    template_vars.update(query_vars)
            
            # Check headers for template variables
            for header in request.get("header", []):
                header_value = header.get("value", "")
                header_vars = re.findall(r'\{\{([^}]+)\}\}', header_value)
                template_vars.update(header_vars)
            
            # Check request body for template variables
            body = request.get("body", {})
            if isinstance(body, dict):
                body_raw = body.get("raw", "")
                if body_raw:
                    body_vars = re.findall(r'\{\{([^}]+)\}\}', body_raw)
                    template_vars.update(body_vars)
    
    # Add template variables as optional (unless they're already identified as auth)
    for var in template_vars:
        if var not in required_vars and var not in optional_vars:
            if "auth" in var.lower() or "token" in var.lower() or "key" in var.lower():
                var_type = "auth"
                description = f"Authentication template variable: {var}"
            elif "url" in var.lower():
                var_type = "url"
                description = f"URL template variable: {var}"
            else:
                var_type = "general"
                description = f"Template variable: {var}"
            
            optional_vars[var] = {
                "description": description,
                "required": False,
                "type": var_type
            }
    
    return required_vars, optional_vars, detected_auth_schemes


def _flatten_postman_items_for_analysis(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten nested Postman collection items for analysis"""
    flattened = []
    for item in items:
        if "item" in item:
            flattened.extend(_flatten_postman_items_for_analysis(item["item"]))
        else:
            flattened.append(item)
    return flattened


def _has_endpoint_security(spec_data: Dict[str, Any]) -> bool:
    """Check if any endpoints have security requirements"""
    paths = spec_data.get("paths", {})
    for path_obj in paths.values():
        for method, operation in path_obj.items():
            if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if operation.get("security"):
                    return True
    return False


def _generate_env_analysis_summary(required_vars: Dict, optional_vars: Dict, detected_auth_schemes: Set) -> str:
    """Generate a human-readable summary of the environment variable analysis"""
    summary_parts = []
    
    if required_vars:
        summary_parts.append(f"Found {len(required_vars)} required environment variable(s)")
    
    if optional_vars:
        summary_parts.append(f"Found {len(optional_vars)} optional environment variable(s)")
    
    if detected_auth_schemes:
        auth_list = ", ".join(sorted(detected_auth_schemes))
        summary_parts.append(f"Detected authentication schemes: {auth_list}")
    
    if not required_vars and not optional_vars:
        summary_parts.append("No environment variables required")
    
    return ". ".join(summary_parts) + "."
