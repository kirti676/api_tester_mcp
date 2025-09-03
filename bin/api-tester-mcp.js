#!/usr/bin/env node

const { spawn } = require('cross-spawn');
const path = require('path');

// Get the directory where this package is installed
const packageDir = path.dirname(__dirname);

// Execute the Python MCP server as a module
// Pass through all arguments
const args = ['-m', 'api_tester_mcp.server', ...process.argv.slice(2)];

// Spawn Python process
const child = spawn('python', args, {
  stdio: 'inherit',
  cwd: packageDir,
  env: {
    ...process.env,
    PYTHONPATH: packageDir
  }
});

child.on('exit', (code) => {
  process.exit(code);
});

child.on('error', (err) => {
  console.error('Failed to start API Tester MCP server:', err.message);
  console.error('\nPlease ensure Python 3.8+ is installed and available in your PATH.');
  console.error('You may also need to install the Python dependencies:');
  console.error('  pip install -e .');
  process.exit(1);
});
