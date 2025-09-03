# Manual PyPI Publishing Guide

## Check Workflow Status
1. Visit: https://github.com/kirti676/api_tester_mcp/actions
2. Look for "Publish Package" workflow runs

## If Workflow Failed (Missing PyPI Token)
1. Get PyPI API Token:
   - Go to: https://pypi.org/manage/account/
   - Create new API token for "Entire account"
   - Copy the token (starts with pypi-)

2. Add Token to GitHub:
   - Go to: https://github.com/kirti676/api_tester_mcp/settings/secrets/actions
   - Click "New repository secret"
   - Name: PYPI_API_TOKEN
   - Value: [paste your token]

3. Re-trigger Publishing:
   - Option A: Re-run failed workflow in GitHub Actions
   - Option B: Create new tag: git tag v1.0.1 && git push origin v1.0.1

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
