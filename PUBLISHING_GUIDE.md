# Manual PyPI Publishing Guide

## ✅ PyPI Publishing Status: SUCCESS
Your package is published at: https://pypi.org/project/api-tester-mcp/

## 🔧 NPM Publishing Setup (Optional)

### Step 1: Get NPM Token
1. Go to: https://www.npmjs.com/settings/tokens
2. Click "Generate New Token" → "Automation"
3. Copy the token (keep it secret!)

### Step 2: Add Token to GitHub
1. Go to: https://github.com/kirti676/api_tester_mcp/settings/secrets/actions
2. Click "New repository secret"
3. Name: `NPM_TOKEN`
4. Value: [paste your NPM token]

### Step 3: Re-run or Create New Tag
- Option A: Re-run failed workflow in GitHub Actions
- Option B: Create new tag: `git tag v1.0.2 && git push origin v1.0.2`

## Manual Workflow Trigger
If you need to trigger manually:
1. Go to: https://github.com/kirti676/api_tester_mcp/actions
2. Click "Publish Package" workflow
3. Click "Run workflow" button
4. Select branch and click "Run workflow"

## Verify Publication
Once successful, check:
- PyPI: https://pypi.org/project/api-tester-mcp/
- Install test: pip install api-tester-mcp
