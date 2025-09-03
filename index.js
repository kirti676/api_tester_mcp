const { setup } = require('./scripts/postinstall');

// Main entry point for the npm package
async function main() {
  console.log('API Tester MCP Server');
  console.log('====================');
  
  // If no arguments provided, show help
  if (process.argv.length === 2) {
    console.log('\nUsage:');
    console.log('  node index.js [options]');
    console.log('  npx api-tester-mcp [options]');
    console.log('\nOptions:');
    console.log('  --setup     Run setup to install Python dependencies');
    console.log('  --help      Show this help message');
    console.log('\nThis package provides an MCP server for API testing.');
    console.log('Configure it in your MCP client to use the testing tools.');
    return;
  }
  
  // Handle setup command
  if (process.argv.includes('--setup')) {
    await setup();
    return;
  }
  
  // Handle help command
  if (process.argv.includes('--help')) {
    console.log('\nAPI Tester MCP Server');
    console.log('A Model Context Protocol server for API testing\n');
    console.log('Features:');
    console.log('- Swagger/OpenAPI and Postman collection support');
    console.log('- Automatic test scenario generation');
    console.log('- API and load testing capabilities');
    console.log('- HTML report generation');
    console.log('- Authentication handling (Bearer tokens, API keys)');
    console.log('\nFor MCP client configuration, use:');
    console.log('  Command: api-tester-mcp');
    console.log('  Arguments: [--host localhost] [--port 8000]');
    return;
  }
  
  // Default: show configuration info
  console.log('\n📋 MCP Client Configuration:');
  console.log('Add this to your MCP client configuration:');
  console.log('\n{');
  console.log('  "mcpServers": {');
  console.log('    "api-tester": {');
  console.log('      "command": "api-tester-mcp",');
  console.log('      "args": ["--host", "localhost", "--port", "8000"]');
  console.log('    }');
  console.log('  }');
  console.log('}');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { main };
