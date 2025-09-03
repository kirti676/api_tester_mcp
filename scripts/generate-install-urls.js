#!/usr/bin/env node

/**
 * Generate VS Code MCP installation URLs for API Tester MCP
 * Usage: node scripts/generate-install-urls.js
 */

const config = {
    name: "api-tester",
    command: "npx", 
    args: ["@kirti676/api-tester-mcp@latest"]
};

const encodedConfig = encodeURIComponent(JSON.stringify(config));

console.log('VS Code Installation URLs for API Tester MCP\n');
console.log('='.repeat(50));

console.log('\n📋 Configuration Object:');
console.log(JSON.stringify(config, null, 2));

console.log('\n🔗 VS Code Installation URLs:');
console.log('\nVS Code:');
console.log(`vscode:mcp/install?${encodedConfig}`);

console.log('\nVS Code Insiders:');
console.log(`vscode-insiders:mcp/install?${encodedConfig}`);

console.log('\n🌐 Web URLs (for GitHub README):');
console.log('\nVS Code:');
console.log(`https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F${encodedConfig.replace(/:/g, '%3A').replace(/\?/g, '%3F')}`);

console.log('\nVS Code Insiders:');
console.log(`https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F${encodedConfig.replace(/:/g, '%3A').replace(/\?/g, '%3F')}`);

console.log('\n📝 Markdown Badges:');
console.log('\nVS Code:');
console.log(`[![Install in VS Code](https://img.shields.io/badge/Install%20in-VS%20Code-blue?style=for-the-badge&logo=visual-studio-code)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F${encodedConfig.replace(/:/g, '%3A').replace(/\?/g, '%3F')})`);

console.log('\nVS Code Insiders:');
console.log(`[![Install in VS Code Insiders](https://img.shields.io/badge/Install%20in-VS%20Code%20Insiders-blue?style=for-the-badge&logo=visual-studio-code)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F${encodedConfig.replace(/:/g, '%3A').replace(/\?/g, '%3F')})`);

console.log('\n✅ URLs generated successfully!');
