# Installation Guide

## Quick Install Options

### Option 1: npm (Recommended)
```bash
# Global installation
npm install -g api-tester-mcp

# Direct usage
npx api-tester-mcp --setup
```

### Option 2: pip
```bash
pip install api-tester-mcp
```

### Option 3: From Source
```bash
git clone https://github.com/kirti676/api_tester_mcp.git
cd api_tester_mcp
npm install  # or pip install -e .
```

## MCP Client Setup

### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "api-tester": {
      "command": "api-tester-mcp"
    }
  }
}
```

### Other MCP Clients
The server is compatible with any MCP client. Use:
- Command: `api-tester-mcp`
- Protocol: stdio
- Port: Optional (for HTTP mode)

## Verification

Test the installation:
```bash
api-tester-mcp --help
npx api-tester-mcp --help
python -m api_tester_mcp.server --help
```

## Troubleshooting

### Python not found
- Install Python 3.8+
- Ensure it's in your PATH

### Permission issues
- Use `sudo` on macOS/Linux if needed
- Run as Administrator on Windows

### npm issues
- Update npm: `npm install -g npm@latest`
- Clear cache: `npm cache clean --force`
