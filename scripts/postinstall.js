const { spawn } = require('child_process');
const path = require('path');

// Get the package root directory (one level up from scripts/)
const packageRoot = path.dirname(__dirname);

// Check if we're in a CI environment where we should skip Python setup
function isCI() {
  return !!(
    process.env.CI ||
    process.env.GITHUB_ACTIONS ||
    process.env.CONTINUOUS_INTEGRATION ||
    process.env.BUILD_NUMBER ||
    process.env.RUN_ID
  );
}

// Check if Python is available
async function checkPython() {
  const pythonCommands = ['python', 'python3'];
  
  for (const cmd of pythonCommands) {
    try {
      const result = await new Promise((resolve) => {
        const child = spawn(cmd, ['--version'], { stdio: 'pipe' });
        child.on('close', (code) => resolve(code === 0 ? cmd : null));
        child.on('error', () => resolve(null));
      });
      if (result) return result;
    } catch (err) {
      continue;
    }
  }
  return null;
}

// Install Python dependencies
function installPythonDependencies(pythonCmd) {
  return new Promise((resolve, reject) => {
    console.log('Installing Python dependencies...');
    
    // Install just the dependencies, not the package itself to avoid CLI conflicts
    const child = spawn(pythonCmd, ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
      stdio: 'inherit',
      cwd: packageRoot  // Use package root instead of __dirname
    });
    
    child.on('exit', (code) => {
      if (code === 0) {
        console.log('✅ Python dependencies installed successfully');
        resolve();
      } else {
        reject(new Error(`pip install failed with code ${code}`));
      }
    });
    
    child.on('error', reject);
  });
}

// Main setup function
async function setup() {
  try {
    // Skip setup in CI environments (GitHub Actions, etc.)
    if (isCI()) {
      console.log('🏗️  Running in CI environment - skipping Python dependency installation');
      console.log('✅ NPM package ready for publishing');
      return;
    }
    
    console.log('🔧 Setting up API Tester MCP...');
    
    // Check Python availability
    const pythonCmd = await checkPython();
    if (!pythonCmd) {
      console.log('⚠️  Python 3.8+ not found in PATH');
      console.log('Python dependencies will be installed when needed.');
      console.log('✓ Setup completed (Python will be checked at runtime)');
      return;
    }
    
    console.log(`✅ Found Python: ${pythonCmd}`);
    
    // Install Python dependencies
    await installPythonDependencies(pythonCmd);
    
    console.log('🎉 API Tester MCP setup complete!');
    console.log('\nUsage:');
    console.log('  npx api-tester-mcp [options]');
    console.log('  or use as MCP server in your client configuration');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  }
}

// Run setup if this script is executed directly
if (require.main === module) {
  setup();
}

module.exports = { setup };
