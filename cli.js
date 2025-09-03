#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * API Tester MCP Server
 * A Model Context Protocol server for API testing with OpenAPI/Swagger and Postman collection support
 */

function showHelp() {
  console.log(`
API Tester MCP Server v${require('./package.json').version}

USAGE:
  npx @kirti676/api-tester-mcp [options]
  api-tester-mcp [options]

OPTIONS:
  --help              Show this help message
  --version           Show version information
  --config <path>     Path to configuration file
  --port <port>       Port to listen on (default: stdio)
  --host <host>       Host to bind to (default: localhost)
  --verbose           Enable verbose logging

EXAMPLES:
  # Run via npx (recommended)
  npx @kirti676/api-tester-mcp

  # Run with custom config
  npx @kirti676/api-tester-mcp --config ./api-config.json

  # Run on specific port
  npx @kirti676/api-tester-mcp --port 3000

For more information, visit: https://github.com/kirti676/api_tester_mcp
`);
}

function showVersion() {
  const pkg = require('./package.json');
  console.log(`${pkg.name} v${pkg.version}`);
}

async function checkPythonInstallation() {
  return new Promise((resolve) => {
    const child = spawn('python', ['--version'], { stdio: 'pipe' });
    child.on('close', (code) => {
      resolve(code === 0);
    });
    child.on('error', () => {
      resolve(false);
    });
  });
}

async function checkPythonDependencies() {
  return new Promise((resolve) => {
    const child = spawn('python', ['-c', 'import fastmcp; import pydantic; import requests'], { stdio: 'pipe' });
    child.on('close', (code) => {
      resolve(code === 0);
    });
    child.on('error', () => {
      resolve(false);
    });
  });
}

async function installPythonDependencies() {
  console.log('Installing Python dependencies...');
  const packageDir = __dirname;
  
  return new Promise((resolve, reject) => {
    const child = spawn('python', ['-m', 'pip', 'install', '-e', '.'], {
      stdio: 'inherit',
      cwd: packageDir
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        console.log('✓ Python dependencies installed successfully');
        resolve();
      } else {
        reject(new Error(`Failed to install Python dependencies (exit code: ${code})`));
      }
    });
    
    child.on('error', (err) => {
      reject(new Error(`Failed to install Python dependencies: ${err.message}`));
    });
  });
}

async function main() {
  const args = process.argv.slice(2);
  
  // Handle help
  if (args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }
  
  // Handle version
  if (args.includes('--version') || args.includes('-v')) {
    showVersion();
    return;
  }
  
  // Check Python installation
  const hasPython = await checkPythonInstallation();
  if (!hasPython) {
    console.error('❌ Python 3.8+ is required but not found in PATH.');
    console.error('\nPlease install Python 3.8 or higher:');
    console.error('  - Windows: https://python.org/downloads/');
    console.error('  - macOS: brew install python3');
    console.error('  - Linux: apt-get install python3 python3-pip');
    process.exit(1);
  }
  
  // Check Python dependencies
  const hasDependencies = await checkPythonDependencies();
  if (!hasDependencies) {
    console.log('⚠️  Python dependencies not found. Installing...');
    try {
      await installPythonDependencies();
    } catch (error) {
      console.error('❌ Failed to install Python dependencies:', error.message);
      console.error('\nPlease try manually installing:');
      console.error('  pip install -e .');
      process.exit(1);
    }
  }
  
  // Start the Python MCP server
  const packageDir = __dirname;
  const serverArgs = ['-m', 'api_tester_mcp.server', ...args];
  
  const child = spawn('python', serverArgs, {
    stdio: 'inherit',
    cwd: packageDir,
    env: {
      ...process.env,
      PYTHONPATH: packageDir
    }
  });
  
  child.on('exit', (code) => {
    process.exit(code || 0);
  });
  
  child.on('error', (err) => {
    console.error('❌ Failed to start API Tester MCP server:', err.message);
    console.error('\nTroubleshooting:');
    console.error('  1. Ensure Python 3.8+ is installed');
    console.error('  2. Try: pip install -e .');
    console.error('  3. Check that all dependencies are installed');
    process.exit(1);
  });
  
  // Handle process termination
  process.on('SIGINT', () => {
    child.kill('SIGINT');
  });
  
  process.on('SIGTERM', () => {
    child.kill('SIGTERM');
  });
}

// Run the CLI
main().catch((error) => {
  console.error('❌ Unexpected error:', error.message);
  process.exit(1);
});
