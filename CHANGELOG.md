# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-02

### Added
- Initial release of API Tester MCP Server
- FastMCP-based Model Context Protocol server implementation
- Support for OpenAPI/Swagger and Postman collection ingestion
- Automatic test scenario generation (positive, negative, edge cases)
- Test case generation and execution
- Authentication support (Bearer tokens, API keys, Basic auth)
- Request body generation from OpenAPI schemas
- Per-endpoint assertions for various status codes (2xx, 4xx, 5xx)
- HTML report generation with beautiful responsive design
- Load testing capabilities
- Real-time progress tracking
- 7 MCP Tools: ingest_spec, set_env_vars, generate_scenarios, generate_test_cases, run_api_tests, run_load_tests, get_session_status
- 2 MCP Resources: HTML report access and listing
- 2 MCP Prompts: test plan generation and failure analysis
- Comprehensive logging system
- npm package support for easy installation
- GitHub Actions for automated publishing
- Cross-platform support (Windows, macOS, Linux)

### Features
- **Input Support**: Swagger/OpenAPI documents and Postman collections
- **Test Generation**: Automatic API and Load test scenario generation
- **Test Execution**: Run generated tests with detailed reporting
- **Authentication**: Bearer token and API key support via set_env_vars
- **HTML Reports**: Beautiful, accessible reports via MCP resources
- **Real-time Progress**: Live updates during test execution
- **Schema Validation**: Request body generation from schema examples
- **Assertions**: Per-endpoint status code assertions (2xx, 4xx, 5xx)

### Dependencies
- fastmcp>=0.2.0
- pydantic>=2.0.0
- aiohttp>=3.8.0
- jinja2>=3.1.0
- pyyaml>=6.0
- jsonschema>=4.0.0
- faker>=19.0.0
- cross-spawn>=7.0.3 (Node.js)
- which>=4.0.0 (Node.js)

### Installation
```bash
# npm (recommended)
npm install -g api-tester-mcp

# pip
pip install api-tester-mcp

# from source
git clone https://github.com/kirti676/api_tester_mcp.git
```
