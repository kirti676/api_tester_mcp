# Deployment Guide

This guide explains how to deploy the API Tester MCP Server to npm and PyPI registries.

## Prerequisites

### For npm Publishing
- npm account and access token
- Repository pushed to GitHub

### For PyPI Publishing  
- PyPI account and API token
- Repository pushed to GitHub

## GitHub Secrets Setup

Add these secrets to your GitHub repository:

1. **NPM_TOKEN**: Your npm access token
   - Go to npmjs.com → Access Tokens → Generate New Token
   - Add as repository secret

2. **PYPI_API_TOKEN**: Your PyPI API token
   - Go to pypi.org → Account Settings → API Tokens
   - Add as repository secret

## Manual Publishing

### npm Package
```bash
# Login to npm
npm login

# Publish to npm
npm publish
```

### PyPI Package
```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Automated Publishing (GitHub Actions)

### Publishing Workflow
The `.github/workflows/publish.yml` workflow automatically publishes to both npm and PyPI when:
- A new tag starting with 'v' is pushed
- A release is published
- Manually triggered

### Creating a Release
```bash
# Tag the release
git tag v1.0.0
git push origin v1.0.0

# Or create via GitHub UI
# Go to Releases → Create a new release
```

## Installation After Publishing

### Global Installation
```bash
# npm (recommended)
npm install -g api-tester-mcp

# pip
pip install api-tester-mcp
```

### Direct Usage
```bash
# Without installation
npx api-tester-mcp

# Or with pip
python -m api_tester_mcp.server
```

## Package URLs

Once published, packages will be available at:
- **npm**: https://www.npmjs.com/package/api-tester-mcp
- **PyPI**: https://pypi.org/project/api-tester-mcp/

## Version Updates

1. Update version in both `package.json` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create new tag and release
5. GitHub Actions will automatically publish

## Testing Installation

After publishing, test the installation:

```bash
# Test npm installation
npm install -g api-tester-mcp
api-tester-mcp --help

# Test pip installation  
pip install api-tester-mcp
python -m api_tester_mcp.server --help

# Test npx usage
npx api-tester-mcp --setup
```
