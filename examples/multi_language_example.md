# Multi-Language Test Generation Example

This example demonstrates how to generate API tests in different programming languages and frameworks using the API Tester MCP server.

## Prerequisites

- API Tester MCP server running
- MCP client (Claude Desktop, VS Code, etc.)

## Step 1: Check Supported Languages

First, let's see what language/framework combinations are supported:

```javascript
const languages = await mcp.call("get_supported_languages");
console.log(languages.supported_combinations);
```

**Expected Output:**
```json
{
  "success": true,
  "supported_combinations": [
    {
      "language": "typescript",
      "framework": "playwright",
      "description": "TypeScript with Playwright for robust E2E testing"
    },
    {
      "language": "javascript",
      "framework": "jest",
      "description": "JavaScript with Jest for unit and API testing"
    },
    {
      "language": "python",
      "framework": "pytest",
      "description": "Python with pytest for comprehensive testing"
    }
  ]
}
```

## Step 2: Ingest API Specification with Language Preference

```javascript
// Ingest OpenAPI spec with TypeScript/Playwright preference
await mcp.call("ingest_spec", {
  spec_type: "openapi",
  file_path: "./examples/petstore_openapi.json",
  preferred_language: "typescript",
  preferred_framework: "playwright"
});
```

## Step 3: Generate Test Cases in Different Languages

### TypeScript + Playwright

```javascript
await mcp.call("generate_test_cases", {
  language: "typescript",
  framework: "playwright"
});
```

**Generated TypeScript Code:**
```typescript
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://petstore.swagger.io/v2';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';

test('Get all pets - Positive test', async ({ request }) => {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };

  const response = await request.get('/pets', {
    headers,
    timeout: 30000
  });

  expect([200, 201, 202, 204]).toContain(response.status());
  
  const contentType = response.headers()['content-type'] || '';
  expect(contentType).toContain('json');
});
```

### JavaScript + Jest

```javascript
await mcp.call("generate_test_cases", {
  language: "javascript",
  framework: "jest"
});
```

**Generated JavaScript Code:**
```javascript
const axios = require('axios');

const BASE_URL = process.env.BASE_URL || 'https://petstore.swagger.io/v2';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';

describe('API Test Suite', () => {
  test('Get all pets - Positive test', async () => {
    const config = {
      method: 'get',
      url: `${BASE_URL}/pets`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${AUTH_TOKEN}`,
      },
      timeout: 30000,
    };

    const startTime = Date.now();
    const response = await axios(config);
    const responseTime = Date.now() - startTime;

    expect([200, 201, 202, 204]).toContain(response.status);
    expect(responseTime).toBeLessThan(5000);
  });
});
```

### Python + pytest

```javascript
await mcp.call("generate_test_cases", {
  language: "python",
  framework: "pytest"
});
```

**Generated Python Code:**
```python
import pytest
import requests
import time

BASE_URL = "https://petstore.swagger.io/v2"
AUTH_TOKEN = ""

class TestAPIEndpoints:
    def test_get_all_pets_positive(self):
        """Get all pets - Positive test"""
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {AUTH_TOKEN}',
        }
        
        start_time = time.time()
        response = requests.get(
            url=f'{BASE_URL}/pets',
            headers=headers,
            timeout=30
        )
        response_time = (time.time() - start_time) * 1000
        
        assert response.status_code in [200, 201, 202, 204], f"Expected status in [200, 201, 202, 204], got {response.status_code}"
        assert response_time < 5000, f"Response time {response_time}ms exceeded limit 5000ms"
        
        content_type = response.headers.get('content-type', '')
        assert 'json' in content_type, f"Content-type '{content_type}' does not contain 'json'"
```

## Step 4: Generate Complete Project Files

### TypeScript/Playwright Project

```javascript
await mcp.call("generate_project_files", {
  language: "typescript",
  framework: "playwright",
  project_name: "petstore-playwright-tests",
  include_examples: true
});
```

**Generated Files:**
```
petstore-playwright-tests/
├── package.json
├── playwright.config.ts
├── tests/
│   └── api.spec.ts
└── README.md
```

**package.json:**
```json
{
  "name": "petstore-playwright-tests",
  "version": "1.0.0",
  "description": "Generated API tests using Playwright",
  "scripts": {
    "test": "npx playwright test",
    "test:headed": "npx playwright test --headed",
    "test:debug": "npx playwright test --debug"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "typescript": "^5.0.0"
  }
}
```

### Python/pytest Project

```javascript
await mcp.call("generate_project_files", {
  language: "python",
  framework: "pytest",
  project_name: "petstore-pytest-tests",
  include_examples: true
});
```

**Generated Files:**
```
petstore-pytest-tests/
├── requirements.txt
├── pytest.ini
├── tests/
│   └── test_api.py
└── README.md
```

**requirements.txt:**
```
pytest>=7.0.0
requests>=2.28.0
pytest-html>=3.0.0
```

## Step 5: Running the Generated Tests

### TypeScript/Playwright

```bash
cd output/generated_projects/petstore-playwright-tests
npm install
npx playwright install
export BASE_URL=https://petstore.swagger.io/v2
export AUTH_TOKEN=your-token
npm test
```

### Python/pytest

```bash
cd output/generated_projects/petstore-pytest-tests
pip install -r requirements.txt
export BASE_URL=https://petstore.swagger.io/v2
export AUTH_TOKEN=your-token
pytest tests/ -v --html=report.html
```

### JavaScript/Jest

```bash
cd output/generated_projects/petstore-jest-tests
npm install
export BASE_URL=https://petstore.swagger.io/v2
export AUTH_TOKEN=your-token
npm test
```

## Language-Specific Benefits

### TypeScript + Playwright
- **Type Safety**: Full TypeScript support with autocomplete
- **Browser Integration**: Can test both API and UI in same framework
- **Parallel Execution**: Built-in parallel test execution
- **Rich Reporting**: Detailed HTML reports with screenshots

### JavaScript + Jest
- **Fast Execution**: Optimized for speed with parallel execution
- **Mocking**: Powerful mocking capabilities for isolation
- **Watch Mode**: Automatic re-running of tests during development
- **Snapshot Testing**: Easy regression testing

### Python + pytest
- **Fixtures**: Powerful setup/teardown with dependency injection
- **Parametrization**: Easy data-driven testing
- **Plugin Ecosystem**: Extensive plugin support
- **Data Analysis**: Easy integration with pandas, numpy for response analysis

## Best Practices

1. **Environment Variables**: Always use environment variables for sensitive data
2. **Project Structure**: Keep generated projects separate for different purposes
3. **Version Control**: Add generated projects to version control for team sharing
4. **CI/CD Integration**: Use generated tests in your continuous integration pipeline
5. **Regular Updates**: Regenerate tests when API specifications change

## Troubleshooting

### Common Issues

1. **Unsupported Language Combination**
   ```javascript
   // Error: Unsupported language/framework combination
   // Solution: Check supported combinations first
   const languages = await mcp.call("get_supported_languages");
   ```

2. **Missing Dependencies**
   ```bash
   # TypeScript projects
   npm install
   
   # Python projects  
   pip install -r requirements.txt
   ```

3. **Environment Variables Not Set**
   ```bash
   # Set required environment variables
   export BASE_URL=your-api-base-url
   export AUTH_TOKEN=your-auth-token
   ```

## Next Steps

- Explore different language/framework combinations
- Customize generated test code for your specific needs
- Integrate generated tests into your CI/CD pipeline
- Use load testing capabilities for performance validation
- Generate comprehensive test reports with the HTML reporting feature