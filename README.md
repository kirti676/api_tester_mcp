# API Tester MCP Server

[![npm (scoped)](https://img.shields.io/npm/v/@kirti676/api-tester-mcp.svg)](https://img.shields.io/npm/v/@kirti676/api-tester-mcp.svg)
[![npm downloads](https://img.shields.io/npm/dt/@kirti676/api-tester-mcp.svg)](https://www.npmjs.com/package/@kirti676/api-tester-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Model Context Protocol (MCP) server for QA/SDET engineers that provides API testing capabilities with Swagger/OpenAPI and Postman collection support.

> 🎉 **Now available on NPM!** Install with `npx @kirti676/api-tester-mcp@latest`

## 🆕 What's New

- ✅ **Enhanced Progress Tracking** - Real-time progress with completion percentages and ETA
- ✅ **Visual Progress Bars** - ASCII progress bars with milestone notifications
- ✅ **Performance Metrics** - Throughput calculations and execution summaries
- ✅ **Published on NPM** - Install instantly with NPX
- ✅ **VS Code Integration** - One-click installation buttons  
- ✅ **Simplified Setup** - No manual Python installation required
- ✅ **Cross-Platform** - Works on Windows, macOS, and Linux
- ✅ **Auto-Updates** - Always get the latest version with `@latest`

## 🚀 Getting Started

### 📦 Installation

The API Tester MCP server can be used directly with npx without any installation:

```bash
npx @kirti676/api-tester-mcp@latest
```

**⚡ Quick Install:**

[![Install in VS Code](https://img.shields.io/badge/Install%20in-VS%20Code-blue?style=for-the-badge&logo=visual-studio-code)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%7B%22name%22%3A%22api-tester%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22%40kirti676%2Fapi-tester-mcp%40latest%22%5D%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/Install%20in-VS%20Code%20Insiders-blue?style=for-the-badge&logo=visual-studio-code)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%7B%22name%22%3A%22API-tester%22%2C%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22%40kirti676%2Fapi-tester-mcp%40latest%22%5D%7D)

### 🤖 Claude Desktop

Follow the MCP install [guide](https://modelcontextprotocol.io/quickstart/user), use the standard config below:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "npx",
      "args": ["@kirti676/api-tester-mcp@latest"]
    }
  }
}
```

### 🔗 Other MCP Clients

The standard configuration works with most MCP clients:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "npx",
      "args": ["@kirti676/api-tester-mcp@latest"]
    }
  }
}
```

**🖥️ Supported Clients:**
- 🤖 [Claude Desktop](https://claude.ai/desktop)
- 💻 [VS Code](https://code.visualstudio.com/) with MCP extension
- ⚡ [Cursor](https://cursor.sh/)
- 🌊 [Windsurf](https://codeium.com/windsurf)
- 🪿 [Goose](https://github.com/Codium-ai/goose)
- 🔧 Any other MCP-compatible client

### 🐍 Python Installation (Alternative)

```bash
pip install api-tester-mcp
```

### 💻 From Source

```bash
git clone https://github.com/kirti676/api_tester_mcp.git
cd api_tester_mcp
npm install
```

## ⚡ Quick Start

Try the API Tester MCP server immediately:

```bash
# Run the server
npx @kirti676/api-tester-mcp@latest

# Check version
npx @kirti676/api-tester-mcp@latest --version

# Get help
npx @kirti676/api-tester-mcp@latest --help
```

For MCP clients like Claude Desktop, use this configuration:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "npx",
      "args": ["@kirti676/api-tester-mcp@latest"]
    }
  }
}
```

## ✨ Features

- **📥 Input Support**: Swagger/OpenAPI documents and Postman collections
- **🔄 Test Generation**: Automatic API and Load test scenario generation
- **🌐 Multi-Language Support**: Generate tests in TypeScript/Playwright, JavaScript/Jest, Python/pytest, and more
- **⚡ Test Execution**: Run generated tests with detailed reporting
- **🔐 Smart Auth Detection**: Automatic environment variable analysis and setup guidance
- **🔐 Authentication**: Bearer token and API key support via `set_env_vars`
- **📊 HTML Reports**: Beautiful, accessible reports via MCP resources
- **📈 Real-time Progress**: Live updates with progress bars and completion percentages
- **⏱️ ETA Calculations**: Estimated time to completion for all operations
- **🎯 Milestone Tracking**: Special notifications at key progress milestones (25%, 50%, 75%, etc.)
- **📊 Performance Metrics**: Throughput calculations and execution summaries
- **✅ Schema Validation**: Request body generation from schema examples
- **🎯 Assertions**: Per-endpoint status code assertions (2xx, 4xx, 5xx)
- **📦 Project Generation**: Complete project scaffolding with dependencies and configuration

## 🌐 Multi-Language Test Generation

The API Tester MCP now supports generating test code in multiple programming languages and testing frameworks:

### 🔧 Supported Language/Framework Combinations

| Language   | Framework  | Description                                    | Use Case                    |
|------------|------------|------------------------------------------------|-----------------------------|
| 📘 TypeScript | 🎭 Playwright | Modern E2E testing with excellent API support | 🏢 Enterprise web applications |
| 📘 TypeScript | 🚀 Supertest  | Express.js focused API testing                | 🟢 Node.js backend services    |
| 📙 JavaScript | 🃏 Jest       | Popular testing framework with good ecosystem | 🔧 General API testing         |
| 📙 JavaScript | 🌲 Cypress    | E2E testing with great developer experience   | 🌐 Full-stack applications     |
| 🐍 Python     | 🧪 pytest     | Comprehensive testing with fixtures & plugins | 📊 Data-heavy APIs & ML services |
| 🐍 Python     | 📡 requests   | Simple HTTP testing for quick validation      | ⚡ Rapid prototyping & scripts |

### 🎯 Language Selection Workflow

```javascript
// 1. Get available languages and frameworks
const languages = await mcp.call("get_supported_languages");

// 2. Choose your preferred combination
await mcp.call("ingest_spec", {
  spec_type: "openapi",
  file_path: "./path/to/your/api-spec.json",
  preferred_language: "typescript",    // python, typescript, javascript
  preferred_framework: "playwright"     // varies by language
});

// 3. Generate test cases with code
await mcp.call("generate_test_cases", {
  language: "typescript",
  framework: "playwright"
});

// 4. Get complete project setup
await mcp.call("generate_project_files", {
  language: "typescript",
  framework: "playwright",
  project_name: "my-api-tests",
  include_examples: true
});
```

### 📁 Generated Project Structure

The `generate_project_files` tool creates a complete, ready-to-run project:

**📘 TypeScript + Playwright:**
```
my-api-tests/
├── 📦 package.json          # Dependencies & scripts
├── ⚙️ playwright.config.ts  # Playwright configuration
├── 📂 tests/
│   └── 🧪 api.spec.ts      # Generated test code
└── 📖 README.md            # Setup instructions
```

**🐍 Python + pytest:**
```
my-api-tests/
├── 📋 requirements.txt     # Python dependencies
├── ⚙️ pytest.ini         # pytest configuration
├── 📂 tests/
│   └── 🧪 test_api.py    # Generated test code
└── 📖 README.md          # Setup instructions
```

**📙 JavaScript + Jest:**
```
my-api-tests/
├── 📦 package.json       # Dependencies & scripts
├── ⚙️ jest.config.js     # Jest configuration
├── 📂 tests/
│   └── 🧪 api.test.js   # Generated test code
└── 📖 README.md         # Setup instructions
```

### 🎯 Framework-Specific Features

- **🎭 Playwright**: Browser automation, parallel execution, detailed reporting
- **🃏 Jest**: Snapshot testing, mocking, watch mode for development
- **🧪 pytest**: Fixtures, parametrized tests, extensive plugin ecosystem
- **🌲 Cypress**: Interactive debugging, time-travel debugging, real browser testing
- **🚀 Supertest**: Express.js integration, middleware testing
- **📡 requests**: Simple API calls, session management, authentication helpers

## 📈 Progress Tracking

The API Tester MCP includes comprehensive progress tracking for all operations:

### 📊 Visual Progress Indicators
```
🎯 API Test Execution: [██████████░░░░░░░░░░] 50.0% (5/10) | ETA: 2.5s - GET /api/users ✅
```

### 🔥 Features:
- **📊 Progress Bars**: ASCII progress bars with filled/empty indicators
- **📈 Completion Percentages**: Real-time percentage completion
- **⏰ ETA Calculations**: Estimated time to completion based on current performance
- **🎯 Milestone Notifications**: Special highlighting at key progress points
- **⚡ Performance Metrics**: Throughput and timing statistics
- **📋 Operation Context**: Detailed information about current step being executed

### ✅ Available for:
- 🎬 Scenario generation
- 🧪 Test case generation  
- 🚀 API test execution
- ⚡ Load test execution
- 🔄 All long-running operations

## 🛠️ MCP Tools

The server provides 11 comprehensive MCP tools with detailed parameter specifications:

### 1. 📥 **`ingest_spec`** - Load API Specifications
Load Swagger/OpenAPI or Postman collections with language/framework preferences
```javascript
{
  "spec_type": "openapi",           // openapi, swagger, postman (optional, auto-detected)
  "file_path": "./api-spec.json",   // Path to JSON or YAML specification file (required)
  "preferred_language": "python",   // python, typescript, javascript (optional, default: python)
  "preferred_framework": "requests" // pytest, requests, playwright, jest, cypress, supertest (optional, default: requests)
}
```

### 2. 🔧 **`set_env_vars`** - Configure Authentication & Environment
Set environment variables with automatic validation and guidance
```javascript
{
  "variables": {},                  // Dictionary of custom environment variables (optional)
  "baseUrl": null,                 // API base URL (optional)
  "auth_bearer": null,             // Bearer/JWT token (optional)
  "auth_apikey": null,             // API key (optional)
  "auth_basic": null,              // Base64 encoded credentials (optional)
  "auth_username": null,           // Username for basic auth (optional)
  "auth_password": null            // Password for basic auth (optional)
}
```

### 3. 🎬 **`generate_scenarios`** - Create Test Scenarios
Generate test scenarios from ingested specifications
```javascript
{
  "include_negative_tests": true,   // Generate failure scenarios (default: true)
  "include_edge_cases": true        // Generate boundary conditions (default: true)
}
```

### 4. 🧪 **`generate_test_cases`** - Convert to Executable Tests
Convert scenarios to executable test cases in preferred language/framework
```javascript
{
  "scenario_ids": null              // Array of scenario IDs or null for all (optional)
}
```

### 5. 🚀 **`run_api_tests`** - Execute API Tests
Execute API tests with detailed results and reporting
```javascript
{
  "test_case_ids": null,           // Array of test case IDs or null for all (optional)
  "max_concurrent": 10             // Number of concurrent requests 1-50 (default: 10)
}
```

### 6. ⚡ **`run_load_tests`** - Execute Performance Tests
Execute load/performance tests with configurable parameters
```javascript
{
  "test_case_ids": null,           // Array of test case IDs or null for all (optional)
  "duration": 60,                  // Test duration in seconds (default: 60)
  "users": 10,                     // Number of concurrent virtual users (default: 10)
  "ramp_up": 10                    // Ramp up time in seconds (default: 10)
}
```

### 7. 🌐 **`get_supported_languages`** - List Language/Framework Options
Get list of supported programming languages and testing frameworks
```javascript
// No parameters required
{}
```

### 8. 📦 **`generate_project_files`** - Generate Complete Projects
Generate complete project structure with dependencies and configuration
```javascript
{
  "project_name": null,            // Project folder name (optional, auto-generated if null)
  "include_examples": true         // Include example test files (default: true)
}
```

### 9. 📁 **`get_workspace_info`** - Workspace Information
Get information about workspace directory and file generation locations
```javascript
// No parameters required
{}
```

### 10. 🔍 **`debug_file_system`** - File System Diagnostics
Get comprehensive workspace information and file system diagnostics
```javascript
// No parameters required
{}
```

### 11. 📊 **`get_session_status`** - Session Status & Progress
Retrieve current session information with progress details
```javascript
// No parameters required
{}
```

## 📚 MCP Resources

- **`file://reports`** - List all available test reports
- **`file://reports/{report_id}`** - Access individual HTML test reports

## 💡 MCP Prompts

- **`create_api_test_plan`** - Generate comprehensive API test plans
- **`analyze_test_failures`** - Analyze test failures and provide recommendations

## 🔍 Smart Environment Variable Analysis

The API Tester MCP now automatically analyzes your API specifications to detect required environment variables and provides helpful setup guidance:

### 🎯 Automatic Detection
- **🔐 Authentication Schemes**: Bearer tokens, API keys, Basic auth, OAuth2
- **🌐 Base URLs**: Extracted from specification servers/hosts
- **🔗 Template Variables**: Postman collection variables like `{{baseUrl}}`, `{{authToken}}`
- **📍 Path Parameters**: Dynamic values in paths like `/users/{userId}`

### 💡 Smart Suggestions
```javascript
// 1. Ingest specification - automatic analysis included
const result = await mcp.call("ingest_spec", {
  spec_type: "openapi",
  file_path: "./api-specification.json"
});

// Check the setup message for immediate guidance
console.log(result.setup_message);
// "⚠️ 2 required environment variable(s) detected..."

// 2. Get detailed setup instructions
const suggestions = await mcp.call("get_env_var_suggestions");
console.log(suggestions.setup_instructions);
// Provides copy-paste ready configuration examples
```

## 🎯 Default Parameter Keys

All MCP tools now provide helpful default parameter keys to guide users on what values they can set:

### 🔧 Environment Variables (`set_env_vars`)
**🔑 ALL PARAMETERS ARE OPTIONAL** - Provide only what you need:
```javascript
// Option 1: Just the base URL
await mcp.call("set_env_vars", {
  baseUrl: "https://api.example.com/v1"
});

// Option 2: Just authentication
await mcp.call("set_env_vars", {
  auth_bearer: "your-jwt-token-here"
});

// Option 3: Multiple parameters
await mcp.call("set_env_vars", {
  baseUrl: "https://api.example.com/v1",
  auth_bearer: "your-jwt-token",
  auth_apikey: "your-api-key"
});

// Option 4: Using variables dict for custom values
await mcp.call("set_env_vars", {
  variables: {
    "baseUrl": "https://api.example.com/v1",
    "custom_header": "custom-value"
  }
});
```

### 🌐 Language & Framework Selection
Default values help you understand available options:
```javascript
// Ingest with defaults shown
await mcp.call("ingest_spec", {
  spec_type: "openapi",        // openapi, swagger, postman
  file_path: "./api-spec.json", // Path to JSON or YAML specification file
  preferred_language: "python", // python, typescript, javascript
  preferred_framework: "requests" // pytest, requests, playwright, jest, cypress, supertest
});

// Project generation with defaults
await mcp.call("generate_project_files", {
  language: "python",          // python, typescript, javascript
  framework: "requests",       // Framework matching the language
  project_name: "api-tests",   // Project folder name
  include_examples: true       // Include example test files
});
```

### ⚡ Test Execution Parameters
Clear defaults for performance tuning:
```javascript
// API tests with concurrency control
await mcp.call("run_api_tests", {
  test_case_ids: null,        // ["test_1", "test_2"] or null for all
  max_concurrent: 10          // Number of concurrent requests (1-50)
});

// Load tests with performance parameters  
await mcp.call("run_load_tests", {
  test_case_ids: null,        // ["test_1", "test_2"] or null for all
  duration: 60,               // Test duration in seconds
  users: 10,                  // Number of concurrent virtual users
  ramp_up: 10                 // Ramp up time in seconds
});
```

## 🔧 Configuration Example

```javascript
// NEW: Check supported languages and frameworks
const languages = await mcp.call("get_supported_languages");
console.log(languages.supported_combinations);

// Ingest specification with language preferences
await mcp.call("ingest_spec", {
  spec_type: "openapi",
  file_path: "./openapi-specification.json",
  preferred_language: "typescript",
  preferred_framework: "playwright"
});

// Set environment variables for authentication
await mcp.call("set_env_vars", {
  variables: {
    "baseUrl": "https://api.example.com",
    "auth_bearer": "your-bearer-token",
    "auth_apikey": "your-api-key"
  }
});

// Generate test scenarios
await mcp.call("generate_scenarios", {
  include_negative_tests: true,
  include_edge_cases: true
});

// Generate test cases in TypeScript/Playwright
await mcp.call("generate_test_cases", {
  language: "typescript",
  framework: "playwright"
});

// Generate complete project files
await mcp.call("generate_project_files", {
  language: "typescript",
  framework: "playwright",
  project_name: "my-api-tests",
  include_examples: true
});

// Run API tests (still works with existing execution engine)
await mcp.call("run_api_tests", {
  max_concurrent: 5
});
```

## 🚀 Complete Workflow Example

Here's a complete example of testing the Petstore API:

```bash
# 1. Start the MCP server
npx @kirti676/api-tester-mcp@latest
```

Then in your MCP client (like Claude Desktop):

```javascript
// 1. Load the Petstore OpenAPI spec
await mcp.call("ingest_spec", {
  spec_type: "openapi",
  file_path: "./examples/petstore_openapi.json"
});

// 2. Set environment variables
await mcp.call("set_env_vars", {
  pairs: {
    "baseUrl": "https://petstore.swagger.io/v2",
    "auth_apikey": "special-key"
  }
});

// 3. Generate test cases
const tests = await mcp.call("get_generated_tests");

// 4. Run API tests
const result = await mcp.call("run_api_tests");

// 5. View results in HTML report
const reports = await mcp.call("list_resources", {
  uri: "file://reports"
});
```

## 📖 Usage Examples

### 🔄 Basic API Testing Workflow

1. **📥 Ingest API Specification**
   ```json
   {
     "tool": "ingest_spec",
     "params": {
       "spec_type": "openapi",
       "content": "{ ... your OpenAPI spec ... }"
     }
   }
   ```

2. **🔐 Configure Authentication**
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

3. **🚀 Generate and Run Tests**
   ```json
   {
     "tool": "generate_scenarios",
     "params": {
       "include_negative_tests": true
     }
   }
   ```

4. **📊 View Results**
   - 📄 Access HTML reports via MCP resources
   - 📈 Get session status and statistics

### ⚡ Load Testing

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

- **✅ Positive Tests**: Valid requests with expected 2xx responses
- **❌ Negative Tests**: Invalid authentication (401), wrong methods (405)
- **🎯 Edge Cases**: Large payloads, boundary conditions
- **🏗️ Schema-based Bodies**: Automatic request body generation from OpenAPI schemas
- **🔍 Comprehensive Assertions**: Status codes, response times, content validation

## 📊 HTML Reports

Generated reports include:
- 📈 Test execution summary with pass/fail statistics
- ⏱️ Detailed test results with timing information
- 🔍 Assertion breakdowns and error details
- 👁️ Response previews and debugging information
- 📱 Mobile-friendly responsive design

## 🔒 Authentication Support

- **🎫 Bearer Tokens**: `auth_bearer` environment variable
- **🔑 API Keys**: `auth_apikey` environment variable (sent as X-API-Key header)
- **👤 Basic Auth**: `auth_basic` environment variable

## 🔧 Requirements

- **🐍 Python**: 3.8 or higher
- **🟢 Node.js**: 14 or higher (for npm installation)

## 📦 Dependencies

### 🐍 Python Dependencies
- 🚀 fastmcp>=0.2.0
- 📊 pydantic>=2.0.0
- 🌐 requests>=2.28.0
- ✅ jsonschema>=4.0.0
- 📝 pyyaml>=6.0
- 🎨 jinja2>=3.1.0
- 📁 aiofiles>=23.0.0
- ⚡ aiohttp>=3.8.0
- 🎭 faker>=19.0.0

### 🟢 Node.js Dependencies  
- ✨ None (self-contained package)

## 🔧 Troubleshooting

### ❗ Common Issues

**📦 NPX Command Not Working**
```bash
# If npx command fails, try:
npm install -g @kirti676/api-tester-mcp@latest

# Or run directly:
node ./node_modules/@kirti676/api-tester-mcp/cli.js
```

**🐍 Python Not Found**
```bash
# Make sure Python 3.8+ is installed and in PATH
python --version

# Install Python dependencies manually if needed:
pip install fastmcp>=0.2.0 pydantic>=2.0.0 requests>=2.28.0
```

**🔗 MCP Client Connection Issues**
- ✅ Ensure the MCP server is running on stdio transport (default)
- 🔄 Check that your MCP client supports the latest MCP protocol version
- 📝 Verify the configuration JSON syntax is correct

### 🆘 Getting Help

1. 📖 Check the [Examples](examples/) directory for working configurations
2. 🔍 Run with `--verbose` flag for detailed logging
3. 🐛 Report issues on [GitHub Issues](https://github.com/kirti676/api_tester_mcp/issues)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Issues & Support

- **NPM Package**: [@kirti676/api-tester-mcp](https://www.npmjs.com/package/@kirti676/api-tester-mcp)
- **Report bugs**: [GitHub Issues](https://github.com/kirti676/api_tester_mcp/issues)

## 📈 Roadmap

- ✅ **Multi-Language Test Generation** - TypeScript/Playwright, JavaScript/Jest, Python/pytest support ✨ **NEW!**
- ✅ **Complete Project Generation** - Full project scaffolding with dependencies and configuration ✨ **NEW!**
- [ ] GraphQL API support
- [ ] Additional authentication methods (OAuth2, JWT)
- [ ] Go/Golang test generation (with testify/ginkgo)
- [ ] C#/.NET test generation (with NUnit/xUnit)
- [ ] Performance monitoring and alerting
- [ ] Integration with CI/CD pipelines (GitHub Actions, Jenkins)
- [ ] Advanced test data generation from examples and schemas
- [ ] API contract testing with Pact support
- [ ] Mock server generation for development

## 📄 Copyright & Usage

**© 2025 kirti676. All rights reserved.**

This repository and its contents are protected by copyright law. For permission to reuse, reference, or redistribute any part of this project, please contact the owner at [kirti676@outlook.com](mailto:kirti676@outlook.com).

**✅ Allowed without permission:**
- Personal learning and experimentation
- Contributing back to this repository via Pull Requests

**❓ Requires permission:**
- Commercial use or integration
- Redistribution in modified form
- Publishing derived works

For licensing inquiries, collaboration opportunities, or permission requests, reach out to [kirti676@outlook.com](mailto:kirti676@outlook.com).

---

<div align="center">

[![⭐ Star this repo](https://img.shields.io/github/stars/kirti676/api_tester_mcp?style=social)](https://github.com/kirti676/api_tester_mcp)
[![🍴 Fork this repo](https://img.shields.io/github/forks/kirti676/api_tester_mcp?style=social)](https://github.com/kirti676/api_tester_mcp/fork)
[![👀 Watch this repo](https://img.shields.io/github/watchers/kirti676/api_tester_mcp?style=social)](https://github.com/kirti676/api_tester_mcp/subscription)
[![💬 Discussions](https://img.shields.io/github/discussions/kirti676/api_tester_mcp?style=social)](https://github.com/kirti676/api_tester_mcp/discussions)

**🚀 Built with ❤️ for QA/SDET engineers worldwide 🌍**

</div>