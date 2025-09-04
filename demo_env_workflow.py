#!/usr/bin/env python3
"""
Demonstration script showing the new environment variable analysis in action
This simulates what a user would see when using the MCP tools
"""

import asyncio
import json
import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.abspath('.'))

from api_tester_mcp.parsers import analyze_required_env_vars, SpecificationParser
from api_tester_mcp.models import SpecType, TestSession
from datetime import datetime


async def demo_workflow():
    """Demonstrate the complete workflow with environment variable analysis"""
    
    print("🚀 API Tester MCP - Environment Variable Analysis Demo")
    print("=" * 60)
    
    # Step 1: Ingest OpenAPI specification (simulating the MCP tool)
    print("\n📋 Step 1: Ingesting OpenAPI specification...")
    
    with open("examples/petstore_openapi.json", "r") as f:
        openapi_content = f.read()
    
    # Parse specification
    parser = SpecificationParser()
    spec_type = SpecType.OPENAPI
    endpoints = parser.parse(openapi_content, spec_type)
    
    # Analyze environment variables
    spec_data = json.loads(openapi_content)
    env_analysis = analyze_required_env_vars(spec_data, spec_type, parser.base_url)
    
    # Simulate MCP tool response
    session_id = "demo-session-123"
    
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
    
    ingest_result = {
        "success": True,
        "session_id": session_id,
        "spec_type": spec_type.value,
        "endpoints_count": len(endpoints),
        "base_url": parser.base_url,
        "environment_analysis": env_analysis,
        "setup_message": "\n".join(env_message)
    }
    
    print("✅ Specification ingested successfully!")
    print(f"   Session ID: {ingest_result['session_id']}")
    print(f"   Endpoints: {ingest_result['endpoints_count']}")
    print(f"   Base URL: {ingest_result['base_url']}")
    print(f"\n📝 Setup Message:")
    for line in ingest_result['setup_message'].split('\n'):
        print(f"   {line}")
    
    # Show environment analysis summary
    env_analysis = ingest_result['environment_analysis']
    print(f"\n🔍 Environment Analysis:")
    print(f"   {env_analysis['analysis_summary']}")
    
    # Step 2: Get detailed environment variable suggestions (simulating the MCP tool)
    print("\n📋 Step 2: Getting detailed environment variable suggestions...")
    
    # Simulate current session with no variables set
    current_vars = {}
    suggestions = {}
    
    # Process required variables
    for var_name, var_info in env_analysis.get("required_variables", {}).items():
        is_set = var_name in current_vars
        suggestions[var_name] = {
            **var_info,
            "currently_set": is_set,
            "current_value": current_vars.get(var_name, None),
            "priority": "required"
        }
    
    # Process optional variables
    for var_name, var_info in env_analysis.get("optional_variables", {}).items():
        is_set = var_name in current_vars
        suggestions[var_name] = {
            **var_info,
            "currently_set": is_set,
            "current_value": current_vars.get(var_name, None),
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
    
    suggestions_result = {
        "success": True,
        "session_id": session_id,
        "suggested_variables": suggestions,
        "required_missing_count": len(missing_required),
        "total_suggestions": len(suggestions),
        "setup_instructions": setup_instructions,
        **env_analysis
    }
    
    print("✅ Environment variable suggestions retrieved!")
    print(f"   Required missing: {suggestions_result['required_missing_count']}")
    print(f"   Total suggestions: {suggestions_result['total_suggestions']}")
    
    print(f"\n💡 Setup Instructions:")
    for instruction in suggestions_result['setup_instructions']:
        print(f"   {instruction}")
    
    print(f"\n📋 Variable Details:")
    for var_name, var_info in suggestions_result['suggested_variables'].items():
        status = "✅ SET" if var_info['currently_set'] else "❌ MISSING"
        priority = "🔴 REQUIRED" if var_info['priority'] == 'required' else "🟡 OPTIONAL"
        print(f"   • {var_name} ({priority}) {status}")
        print(f"     Description: {var_info['description']}")
        if not var_info['currently_set'] and 'detected_value' in var_info:
            print(f"     Suggested value: {var_info['detected_value']}")
        print()
    
    # Step 3: Simulate setting environment variables
    print("\n📋 Step 3: Setting environment variables...")
    
    # Simulate the set_env_vars operation
    new_vars = {
        "baseUrl": "https://petstore.swagger.io/v2",
        "auth_bearer": "demo-bearer-token-12345"
    }
    
    print("✅ Environment variables set successfully!")
    print(f"   Variables set: {list(new_vars.keys())}")
    
    # Mask sensitive values for display
    display_vars = {}
    for k, v in new_vars.items():
        if "auth" in k.lower() or "password" in k.lower() or "secret" in k.lower():
            display_vars[k] = "***"
        else:
            display_vars[k] = v
    
    print(f"   Current variables: {json.dumps(display_vars, indent=2)}")
    
    # Step 4: Show updated status after setting variables
    print("\n📋 Step 4: Checking updated environment variable status...")
    
    # Update suggestions with the new variables
    updated_suggestions = {}
    for var_name, var_info in suggestions.items():
        is_set = var_name in new_vars
        updated_suggestions[var_name] = {
            **var_info,
            "currently_set": is_set,
            "current_value": "***" if is_set and ("auth" in var_name.lower()) else new_vars.get(var_name, None),
        }
    
    updated_missing_required = [var for var, info in updated_suggestions.items() if info["priority"] == "required" and not info["currently_set"]]
    
    print("✅ Updated status retrieved!")
    print(f"   Required missing: {len(updated_missing_required)}")
    
    if len(updated_missing_required) == 0:
        print("🎉 All required environment variables are now configured!")
        print("   Ready to generate scenarios and run tests!")
        
        print(f"\n✅ Updated Variable Status:")
        for var_name, var_info in updated_suggestions.items():
            status = "✅ SET" if var_info['currently_set'] else "❌ MISSING"
            priority = "🔴 REQUIRED" if var_info['priority'] == 'required' else "🟡 OPTIONAL"
            print(f"   • {var_name} ({priority}) {status}")
    else:
        print("⚠️  Some required variables are still missing:")
        for var in updated_missing_required:
            print(f"   • {var}")
    
    print("\n🎉 Environment variable analysis demo completed!")
    print("\n📚 Available MCP Tools:")
    print("   • ingest_spec - Ingest API specifications with automatic env var analysis")
    print("   • get_env_var_suggestions - Get detailed setup instructions")
    print("   • set_env_vars - Configure environment variables")
    print("   • generate_scenarios - Generate test scenarios (after env setup)")
    print("   • run_api_tests - Execute API tests")
    
    print("\n🔧 Example MCP Usage:")
    print("   1. await mcp.call('ingest_spec', {'spec_type': 'openapi', 'content': '...'})")
    print("   2. await mcp.call('get_env_var_suggestions')")
    print("   3. await mcp.call('set_env_vars', {'variables': {'baseUrl': '...', 'auth_bearer': '...'}})")
    print("   4. await mcp.call('generate_scenarios', {'include_negative_tests': true})")
    print("   5. await mcp.call('run_api_tests')")


if __name__ == "__main__":
    asyncio.run(demo_workflow())
