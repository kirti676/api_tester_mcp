"""Simple test to validate the core functionality"""

import json
import asyncio
from pathlib import Path

from api_tester_mcp.parsers import SpecificationParser, ScenarioGenerator
from api_tester_mcp.test_execution import TestCaseGenerator, TestExecutor
from api_tester_mcp.reports import ReportGenerator
from api_tester_mcp.models import SpecType, TestSession
from api_tester_mcp.utils import generate_id
from datetime import datetime


async def test_core_functionality():
    """Test the core API testing functionality"""
    
    print("🚀 API Tester MCP - Core Functionality Test")
    print("=" * 50)
    
    # Step 1: Parse OpenAPI specification
    print("\n📋 Step 1: Parsing OpenAPI specification...")
    
    with open("examples/petstore_openapi.json", "r") as f:
        openapi_content = f.read()
    
    parser = SpecificationParser()
    endpoints = parser.parse(openapi_content, SpecType.OPENAPI)
    
    print(f"✅ Parsed {len(endpoints)} endpoints")
    print(f"   Base URL: {parser.base_url}")
    
    for i, endpoint in enumerate(endpoints[:3]):
        auth_status = "🔒" if endpoint.auth_required else "🔓"
        print(f"     {i+1}. {auth_status} {endpoint.method} {endpoint.path} - {endpoint.summary}")
    
    if len(endpoints) > 3:
        print(f"     ... and {len(endpoints) - 3} more")
    
    # Step 2: Generate test scenarios
    print("\n📝 Step 2: Generating test scenarios...")
    
    generator = ScenarioGenerator()
    scenarios = generator.generate_scenarios(endpoints)
    
    print(f"✅ Generated {len(scenarios)} test scenarios")
    
    scenario_types = {}
    for scenario in scenarios:
        if "positive" in scenario.name.lower():
            scenario_types["positive"] = scenario_types.get("positive", 0) + 1
        elif "unauthorized" in scenario.name.lower() or "negative" in scenario.name.lower():
            scenario_types["negative"] = scenario_types.get("negative", 0) + 1
        else:
            scenario_types["edge_case"] = scenario_types.get("edge_case", 0) + 1
    
    print("   Scenario breakdown:")
    for scenario_type, count in scenario_types.items():
        print(f"     {scenario_type.title()}: {count}")
    
    # Save scenarios for inspection
    scenarios_file = "output/scenarios/demo_scenarios.json"
    with open(scenarios_file, 'w') as f:
        scenarios_data = [scenario.model_dump() for scenario in scenarios]
        json.dump(scenarios_data, f, indent=2)
    print(f"   📁 Saved to: {scenarios_file}")
    
    # Step 3: Generate test cases
    print("\n🧪 Step 3: Generating executable test cases...")
    
    env_vars = {
        "baseUrl": "https://petstore.swagger.io/v2",
        "auth_bearer": "demo-token-123"
    }
    
    test_generator = TestCaseGenerator(env_vars.get("baseUrl", ""), env_vars)
    test_cases = test_generator.generate_test_cases(scenarios)
    
    print(f"✅ Generated {len(test_cases)} executable test cases")
    
    # Show sample test cases
    print("\n   Sample test cases:")
    for i, test_case in enumerate(test_cases[:3]):
        print(f"     {i+1}. {test_case.method} {test_case.url}")
        print(f"        Expected status: {test_case.expected_status}")
        print(f"        Assertions: {len(test_case.assertions)}")
        if test_case.body:
            print(f"        Has body: Yes")
    
    if len(test_cases) > 3:
        print(f"     ... and {len(test_cases) - 3} more")
    
    # Save test cases
    test_cases_file = "output/test_cases/demo_test_cases.json"
    with open(test_cases_file, 'w') as f:
        test_cases_data = [test_case.model_dump() for test_case in test_cases]
        json.dump(test_cases_data, f, indent=2)
    print(f"   📁 Saved to: {test_cases_file}")
    
    # Step 4: Generate mock test results for report demo
    print("\n📊 Step 4: Generating demo test report...")
    
    # Create a test session
    session = TestSession(
        id=generate_id(),
        spec_type=SpecType.OPENAPI,
        spec_content=json.loads(openapi_content),
        scenarios=scenarios,
        test_cases=test_cases,
        env_vars=env_vars,
        created_at=datetime.now().isoformat(),
        completed_at=datetime.now().isoformat()
    )
    
    # Generate mock test results
    from api_tester_mcp.models import TestResult
    import random
    
    mock_results = []
    for test_case in test_cases[:5]:  # Demo with first 5 test cases
        # Simulate test results
        success = random.choice([True, True, True, False])  # 75% success rate
        
        result = TestResult(
            test_case_id=test_case.id,
            status="passed" if success else "failed",
            execution_time=random.uniform(0.1, 2.0),
            response_status=200 if success else random.choice([400, 401, 404, 500]),
            response_body='{"message": "Success"}' if success else '{"error": "Test failure"}',
            response_headers={"content-type": "application/json"},
            error_message=None if success else "Simulated test failure for demo",
            assertions_passed=len(test_case.assertions) if success else 0,
            assertions_failed=0 if success else len(test_case.assertions),
            assertion_details=[
                {
                    "assertion": assertion,
                    "passed": success,
                    "message": f"Status code assertion {'passed' if success else 'failed'}"
                }
                for assertion in test_case.assertions
            ]
        )
        mock_results.append(result)
    
    # Generate HTML report
    report_generator = ReportGenerator()
    html_report = report_generator.generate_api_test_report(mock_results, session)
    
    report_file = "output/reports/demo_api_test_report.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    # Calculate stats
    total_tests = len(mock_results)
    passed_tests = sum(1 for r in mock_results if r.status == "passed")
    
    print(f"✅ Generated demo test report")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success rate: {(passed_tests / total_tests * 100):.1f}%")
    print(f"   📁 Report saved to: {report_file}")
    
    # Step 5: Test Postman collection parsing
    print("\n🔄 Step 5: Testing Postman collection support...")
    
    with open("examples/petstore_postman.json", "r") as f:
        postman_content = f.read()
    
    postman_endpoints = parser.parse(postman_content, SpecType.POSTMAN)
    
    print(f"✅ Parsed Postman collection: {len(postman_endpoints)} endpoints")
    for endpoint in postman_endpoints:
        auth_status = "🔒" if endpoint.auth_required else "🔓"
        print(f"     {auth_status} {endpoint.method} {endpoint.path} - {endpoint.summary}")
    
    print("\n🎉 Core functionality test completed successfully!")
    print("\n📁 Generated files:")
    print(f"   📋 {scenarios_file}")
    print(f"   🧪 {test_cases_file}")
    print(f"   📊 {report_file}")
    print("\n💡 You can open the HTML report in your browser to see the detailed results!")


if __name__ == "__main__":
    asyncio.run(test_core_functionality())
