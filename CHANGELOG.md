# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Changelog

All notable changes to this project will be documented in this file.

## [1.2.1] - 2024-12-09

### Removed
- Redundant documentation files (PUBLISHING.md, IMPLEMENTATION_SUMMARY.md, RELEASE_SUMMARY.md, PUBLISHING_GUIDE.md)
- Demo and test files not needed for production (demo_env_workflow.py, test_core.py, run.py)
- Empty output/ directory

### Fixed
- Jinja2 template syntax for Python docstrings in code generators
- Removed unused logger import from code_generators.py

### Enhanced
- CLI version display now shows multi-language support information
- Repository structure optimized for production distribution and maintainability

## [1.2.0] - 2024-12-09

### 🚀 Major Feature: Multi-Language Test Generation

#### Added
- **Multi-Language Support**: Generate test code in TypeScript, JavaScript, and Python
- **Framework Support**: Support for Playwright, Jest, pytest, Supertest, Cypress, and requests
- **New MCP Tools**:
  - `get_supported_languages`: List all supported language/framework combinations
  - `generate_project_files`: Create complete, ready-to-run test projects
- **Enhanced MCP Tools**:
  - `ingest_spec`: Now accepts `preferred_language` and `preferred_framework` parameters
  - `generate_test_cases`: Enhanced with `language` and `framework` parameters
- **Code Generation Engine**: Comprehensive Jinja2-based templates for each language/framework
- **Project Scaffolding**: Complete project generation with dependencies, configuration, and setup instructions

#### Language/Framework Combinations
- **TypeScript + Playwright**: Enterprise E2E testing with type safety
- **TypeScript + Supertest**: Express.js API testing with TypeScript
- **JavaScript + Jest**: Popular testing framework with extensive ecosystem
- **JavaScript + Cypress**: E2E testing with excellent developer experience
- **Python + pytest**: Comprehensive testing with fixtures and plugins
- **Python + requests**: Simple HTTP testing for rapid validation

#### Generated Project Features
- **Package Configuration**: Automatic package.json, requirements.txt generation
- **Framework Configuration**: Proper config files (playwright.config.ts, pytest.ini, etc.)
- **Example Test Files**: Complete test code with proper imports and setup
- **Setup Instructions**: Detailed setup and run instructions for each project type
- **Environment Variable Support**: Proper handling of BASE_URL, AUTH_TOKEN across all languages

#### Enhanced Data Models
- Added `TestLanguage` enum (Python, TypeScript, JavaScript)
- Added `TestFramework` enum (pytest, requests, Playwright, Jest, Supertest, Cypress)
- Enhanced `TestCase` model with `language`, `framework`, and `generated_code` fields
- Enhanced `TestSession` model with `preferred_language` and `preferred_framework`

#### Documentation
- Updated README with comprehensive multi-language examples
- Added `examples/multi_language_example.md` with detailed usage guide
- Updated roadmap to reflect completed multi-language support
- Enhanced configuration examples with language selection

### 🔧 Technical Improvements
- **Code Generation Templates**: 6 comprehensive Jinja2 templates for different language/framework combinations
- **Package File Generation**: Automatic generation of package.json, requirements.txt, and configuration files
- **Setup Instruction Generation**: Dynamic generation of setup instructions based on selected language/framework
- **Enhanced Error Handling**: Better error messages for unsupported language/framework combinations

### 🎯 Breaking Changes
- `TestCase` model now includes `language` and `framework` fields (default to Python/requests for backward compatibility)
- `TestSession` model now includes language preferences

### 📦 Dependencies
- No new runtime dependencies added
- Maintains backward compatibility with existing installations

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
