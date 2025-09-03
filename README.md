# API Tester MCP Server

[![npm version](https://badge.fury.io/js/@api-tester/mcp.svg)](https://badge.fury.io/js/@api-tester/mcp)
[![PyPI version](https://badge.fury.io/py/api-tester-mcp.svg)](https://badge.fury.io/py/api-tester-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Model Context Protocol (MCP) server for QA/SDET engineers that provides API testing capabilities with Swagger/OpenAPI and Postman collection support.

## 🚀 Getting Started

### Installation

The API Tester MCP server can be used directly with npx without any installation:

```bash
npx @api-tester/mcp@latest
```

**Quick Install:**

[![Install in VS Code](https://img.shields.io/badge/Install%20in-VS%20Code-blue?style=for-the-badge&logo=visual-studio-code)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522api-tester%2522%252C%2522command%2522%253A%2522npx%2522%252C%2522args%2522%253A%255B%2522%2540api-tester%252Fmcp%2540latest%2522%255D%257D) [![Install in VS Code Insiders](https://img.shields.io/badge/Install%20in-VS%20Code%20Insiders-blue?style=for-the-badge&logo=visual-studio-code)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522api-tester%2522%252C%2522command%2522%253A%2522npx%2522%252C%2522args%2522%253A%255B%2522%2540api-tester%252Fmcp%2540latest%2522%255D%257D)

### Claude Desktop

Follow the MCP install [guide](https://modelcontextprotocol.io/quickstart/user), use the standard config below:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "npx",
      "args": ["@api-tester/mcp@latest"]
    }
  }
}
```

### Other MCP Clients

The standard configuration works with most MCP clients:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "npx",
      "args": ["@api-tester/mcp@latest"]
    }
  }
}
```

**Supported Clients:**
- [Claude Desktop](https://claude.ai/desktop)
- [VS Code](https://code.visualstudio.com/) with MCP extension
- [Cursor](https://cursor.sh/)
- [Windsurf](https://codeium.com/windsurf)
- [Goose](https://github.com/Codium-ai/goose)
- Any other MCP-compatible client

### Python Installation (Alternative)

```bash
pip install api-tester-mcp
```

### From Source

```bash
git clone https://github.com/kirti676/api_tester_mcp.git
cd api_tester_mcp
npm install
```

Or for Claude Desktop on Windows:
```json
{
  "mcpServers": {
    "api-tester": {
      "command": "npx",
      "args": ["api-tester-mcp"]
    }
  }
}
```

## ✨ Features

- **📥 Input Support**: Swagger/OpenAPI documents and Postman collections
- **🔄 Test Generation**: Automatic API and Load test scenario generation
- **⚡ Test Execution**: Run generated tests with detailed reporting
- **🔐 Authentication**: Bearer token and API key support via `set_env_vars`
- **📊 HTML Reports**: Beautiful, accessible reports via MCP resources
- **📈 Real-time Progress**: Live updates during test execution
- **✅ Schema Validation**: Request body generation from schema examples
- **🎯 Assertions**: Per-endpoint status code assertions (2xx, 4xx, 5xx)

## 🛠️ MCP Tools

The server provides 7 comprehensive MCP tools:

1. **`ingest_spec`** - Load Swagger/OpenAPI or Postman collections
2. **`set_env_vars`** - Configure authentication and environment variables
3. **`generate_scenarios`** - Create test scenarios from specifications
4. **`generate_test_cases`** - Convert scenarios to executable test cases
5. **`run_api_tests`** - Execute API tests with detailed results
6. **`run_load_tests`** - Execute performance/load tests
7. **`get_session_status`** - Retrieve current session information

## 📚 MCP Resources

- **`file://reports`** - List all available test reports
- **`file://reports/{report_id}`** - Access individual HTML test reports

## 💡 MCP Prompts

- **`create_api_test_plan`** - Generate comprehensive API test plans
- **`analyze_test_failures`** - Analyze test failures and provide recommendations

## 🔧 Configuration Example

```javascript
// Set environment variables for authentication
await mcp.call("set_env_vars", {
  variables: {
    "baseUrl": "https://api.example.com",
    "auth_bearer": "your-bearer-token",
    "auth_apikey": "your-api-key"
  }
});

// Ingest an OpenAPI specification
await mcp.call("ingest_spec", {
  spec_type: "openapi",
  content: openapi_json_string
});

// Generate test scenarios
await mcp.call("generate_scenarios", {
  include_negative_tests: true,
  include_edge_cases: true
});

// Run API tests
await mcp.call("run_api_tests", {
  max_concurrent: 5
});
```

## 📖 Usage Examples

### Basic API Testing Workflow

1. **Ingest API Specification**
   ```json
   {
     "tool": "ingest_spec",
     "params": {
       "spec_type": "openapi",
       "content": "{ ... your OpenAPI spec ... }"
     }
   }
   ```

2. **Configure Authentication**
   ```json
   {
     "tool": "set_env_vars", 
     "params": {
       "variables": {
         "auth_bearer": "your-token",
         "baseUrl": "https://api.example.com"
       }
     }
   }
   ```

3. **Generate and Run Tests**
   ```json
   {
     "tool": "generate_scenarios",
     "params": {
       "include_negative_tests": true
     }
   }
   ```

4. **View Results**
   - Access HTML reports via MCP resources
   - Get session status and statistics

### Load Testing

```json
{
  "tool": "run_load_tests",
  "params": {
    "users": 10,
    "duration": 60,
    "ramp_up": 10
  }
}
```

## 🔍 Test Generation Features

- **Positive Tests**: Valid requests with expected 2xx responses
- **Negative Tests**: Invalid authentication (401), wrong methods (405)
- **Edge Cases**: Large payloads, boundary conditions
- **Schema-based Bodies**: Automatic request body generation from OpenAPI schemas
- **Comprehensive Assertions**: Status codes, response times, content validation

## 📊 HTML Reports

Generated reports include:
- Test execution summary with pass/fail statistics
- Detailed test results with timing information
- Assertion breakdowns and error details
- Response previews and debugging information
- Mobile-friendly responsive design

## 🔒 Authentication Support

- **Bearer Tokens**: `auth_bearer` environment variable
- **API Keys**: `auth_apikey` environment variable (sent as X-API-Key header)
- **Basic Auth**: `auth_basic` environment variable

## 🔧 Requirements

- **Python**: 3.8 or higher
- **Node.js**: 14 or higher (for npm installation)

## 📦 Dependencies

### Python Dependencies
- fastmcp>=0.2.0
- pydantic>=2.0.0
- aiohttp>=3.8.0
- jinja2>=3.1.0
- pyyaml>=6.0
- jsonschema>=4.0.0
- faker>=19.0.0

### Node.js Dependencies  
- cross-spawn>=7.0.3
- which>=4.0.0

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Issues & Support

- Report bugs: [GitHub Issues](https://github.com/kirti676/api_tester_mcp/issues)
- Documentation: [GitHub Wiki](https://github.com/kirti676/api_tester_mcp/wiki)
- Discussions: [GitHub Discussions](https://github.com/kirti676/api_tester_mcp/discussions)
- Interactive install page: [install.html](install.html)

## 📈 Roadmap

- [ ] GraphQL API support
- [ ] Additional authentication methods (OAuth2, JWT)
- [ ] Performance monitoring and alerting
- [ ] Integration with CI/CD pipelines
- [ ] Test data generation from examples
- [ ] API contract testing

---

**Made with ❤️ for QA/SDET engineers**
