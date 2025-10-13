# API Tester MCP Server

A comprehensive Model Context Protocol (MCP) server for QA/SDET engineers that provides automated API testing capabilities with support for Swagger/OpenAPI specifications and Postman collections.

## 🚀 Features

### Core Capabilities
- **Multi-format Support**: Swagger/OpenAPI (JSON/YAML) and Postman collections
- **Automatic Test Generation**: Creates comprehensive test scenarios and executable test cases
- **Authentication Support**: Bearer tokens, API keys, and basic authentication
- **Load Testing**: Built-in load testing with configurable parameters
- **Beautiful Reports**: HTML reports with detailed statistics and visualizations
- **MCP Integration**: Full MCP protocol support with tools, resources, and prompts

### Test Scenario Generation
- **Positive Tests**: Happy path scenarios with valid inputs
- **Negative Tests**: Authentication failures, invalid methods, missing parameters
- **Edge Cases**: Large payloads, boundary conditions, timeout scenarios
- **Custom Assertions**: Status codes, response times, content validation

### Advanced Features
- **Request Body Generation**: Automatic test data from schema examples
- **Environment Variables**: Support for dynamic configuration
- **Progress Tracking**: Real-time progress notifications
- **Resource Access**: HTML reports accessible as MCP resources
- **Concurrent Testing**: Configurable parallel test execution

## 📋 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Installation
```bash
# Clone or download the project
cd api_tester_mcp

# Install in development mode
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

### Verify Installation
```bash
python -m api_tester_mcp.server --help
```

## 🔧 Configuration

### Claude Desktop Integration
Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "python",
      "args": ["-m", "api_tester_mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/api_tester_mcp"
      }
    }
  }
}
```

### VS Code Integration
If using with VS Code MCP extension, configure similar to Claude Desktop.

## 🛠 Usage

### 1. Ingest API Specification
Start by loading your API specification:

```python
# OpenAPI/Swagger
await ingest_spec({
    "spec_type": "openapi",
    "file_path": "./path/to/openapi-spec.json"
})

# Postman Collection
await ingest_spec({
    "spec_type": "postman", 
    "file_path": "./path/to/postman-collection.json"
})

# GraphQL Schema
await ingest_spec({
    "spec_type": "graphql",
    "file_path": "./path/to/schema.graphql"
})
```

### 2. Configure Environment
Set up authentication and base URLs:

```python
await set_env_vars({
    "variables": {
        "baseUrl": "https://api.example.com",
        "auth_bearer": "your-bearer-token",
        "auth_apikey": "your-api-key"
    }
})
```

### 3. Generate Test Scenarios
Create comprehensive test scenarios:

```python
await generate_scenarios({
    "include_negative_tests": True,
    "include_edge_cases": True
})
```

### 4. Generate Test Cases
Convert scenarios to executable test cases:

```python
await generate_test_cases({
    "scenario_ids": []  # Optional: specific scenarios only
})
```

### 5. Execute Tests
Run API tests:

```python
# API Tests
await run_api_tests({
    "test_case_ids": [],  # Optional: specific test cases
    "max_concurrent": 10
})

# Load Tests
await run_load_tests({
    "duration": 60,
    "users": 10,
    "ramp_up": 10
})
```

## 🎯 MCP Tools

### Core Tools
- `ingest_spec` - Load API specifications
- `set_env_vars` - Configure environment variables
- `generate_scenarios` - Create test scenarios
- `generate_test_cases` - Generate executable tests
- `run_api_tests` - Execute API tests
- `run_load_tests` - Execute load tests
- `get_session_status` - Check current session

### Authentication Variables
- `baseUrl` - API base URL
- `auth_bearer` - Bearer token for Authorization header
- `auth_apikey` - API key for X-API-Key header
- `auth_basic` - Basic auth credentials (base64 encoded)

## 📊 Reports and Resources

### HTML Reports
The server generates beautiful HTML reports with:
- Test execution summary
- Individual test results
- Response time statistics
- Assertion details
- Error information

### MCP Resources
Access reports directly through MCP:
- `file://reports` - List all available reports
- `file://reports/{report_id}` - Access specific report

### Report Features
- 📈 Visual statistics and charts
- 🎨 Responsive design for all devices
- 🔍 Detailed assertion breakdowns
- ⚡ Performance metrics
- 📱 Mobile-friendly interface

## 🧪 Test Scenario Types

### Positive Tests
- Valid request with expected responses
- Successful authentication
- Proper parameter validation
- Schema compliance verification

### Negative Tests
- Unauthorized access attempts
- Invalid HTTP methods
- Missing required parameters
- Malformed request bodies

### Edge Cases
- Large payload handling
- Boundary value testing
- Timeout scenarios
- Rate limiting tests

## 🚀 GraphQL API Testing

### Supported GraphQL Formats
- **Schema Definition Language (SDL)**: Standard GraphQL schema files
- **Introspection Results**: JSON output from GraphQL introspection queries
- **Schema Objects**: Structured schema definitions in JSON/YAML

### GraphQL-Specific Features
- **Query/Mutation Detection**: Automatic identification of GraphQL operations
- **Schema Parsing**: Support for type definitions, interfaces, enums, and unions
- **Authentication Patterns**: Bearer token and API key detection from schema directives
- **Test Generation**: GraphQL-specific test templates for Python, TypeScript, and JavaScript

### Example GraphQL Schema (SDL)
```graphql
type Query {
  user(id: ID!): User
  users(limit: Int = 10): [User!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User
}

type User {
  id: ID!
  name: String!
  email: String!
}

input CreateUserInput {
  name: String!
  email: String!
}
```

### GraphQL Test Configuration
```python
await set_env_vars({
    "graphqlEndpoint": "https://api.example.com/graphql",
    "auth_bearer": "your-jwt-token",
    "graphqlWsEndpoint": "wss://api.example.com/graphql"  # Optional for subscriptions
})
```

## 🚀 Load Testing

### Configuration
```python
{
    "duration": 60,        # Test duration in seconds
    "users": 10,          # Concurrent virtual users
    "ramp_up": 10,        # Ramp-up time in seconds
    "test_case_ids": []   # Specific test cases to use
}
```

### Metrics
- Total requests and success rate
- Response time percentiles (P50, P90, P95, P99)
- Requests per second throughput
- Status code distribution
- Error analysis

## 📁 File Structure

```
api_tester_mcp/
├── api_tester_mcp/          # Main package
│   ├── __init__.py
│   ├── server.py            # FastMCP server implementation
│   ├── models.py            # Data models and schemas
│   ├── parsers.py           # OpenAPI/Postman parsers
│   ├── test_execution.py    # Test execution engine
│   ├── reports.py           # HTML report generation
│   └── utils.py            # Utility functions
├── examples/               # Example specifications
│   ├── petstore_openapi.json
│   ├── petstore_postman.json
│   └── claude_desktop_config.json
├── output/                 # Generated files
│   ├── scenarios/          # Test scenarios (JSON)
│   ├── test_cases/         # Test cases (JSON)
│   └── reports/           # HTML reports
└── tests/                 # Test files
```

## 🔍 Example Workflow

See the complete example in `test_core.py`:

```python
python test_core.py
```

This demonstrates:
1. Loading OpenAPI specification
2. Parsing endpoints and generating scenarios
3. Creating executable test cases
4. Generating mock test results
5. Creating HTML reports
6. Testing Postman collection support

## 🛡 Error Handling

The server provides comprehensive error handling:
- **Specification Validation**: Validates input formats
- **Authentication Errors**: Clear auth failure messages
- **Network Issues**: Timeout and connection error handling
- **Assertion Failures**: Detailed assertion error reporting

## 📈 Performance

- **Concurrent Execution**: Configurable parallel test execution
- **Memory Efficient**: Streaming JSON parsing for large files
- **Progress Tracking**: Real-time progress updates
- **Resource Management**: Automatic cleanup and connection pooling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
1. Check existing documentation
2. Search through examples
3. Create detailed issue reports
4. Include specification samples when relevant

## 🔄 Updates

The server supports:
- Hot reloading of specifications
- Session management
- Multiple concurrent sessions
- Dynamic configuration updates

---

**Made with ❤️ for QA/SDET engineers who want powerful, automated API testing capabilities through the Model Context Protocol.**
