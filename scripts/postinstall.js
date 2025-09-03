const { spawn } = require('cross-spawn');
const which = require('which');
const path = require('path');
const fs = require('fs');

// Get the package root directory (one level up from scripts/)
const packageRoot = path.dirname(__dirname);

// Check if Python is available
async function checkPython() {
  try {
    await which('python');
    return 'python';
  } catch (err) {
    try {
      await which('python3');
      return 'python3';
    } catch (err) {
      return null;
    }
  }
}

// Install Python dependencies
function installPythonDependencies(pythonCmd) {
  return new Promise((resolve, reject) => {
    console.log('Installing Python dependencies...');
    
    const child = spawn(pythonCmd, ['-m', 'pip', 'install', '-e', '.'], {
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
    console.log('🔧 Setting up API Tester MCP...');
    
    // Check Python availability
    const pythonCmd = await checkPython();
    if (!pythonCmd) {
      console.error('❌ Python 3.8+ is required but not found in PATH');
      console.error('Please install Python and try again.');
      process.exit(1);
    }
    
    console.log(`✅ Found Python: ${pythonCmd}`);
    
    // Install Python dependencies
    await installPythonDependencies(pythonCmd);
    
    // Create output directories
    const outputDirs = ['output', 'output/reports', 'output/scenarios', 'output/test_cases'];
    for (const dir of outputDirs) {
      const dirPath = path.join(packageRoot, dir);
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`📁 Created directory: ${dir}`);
      }
    }
    
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
