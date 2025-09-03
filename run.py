#!/usr/bin/env python
"""
API Tester MCP Server Startup Script
Run this script to start the MCP server for API testing.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Start the API Tester MCP server"""
    
    print("🚀 Starting API Tester MCP Server...")
    print("=" * 50)
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "api_tester_mcp").exists():
        print("❌ Error: Please run this script from the api_tester_mcp root directory")
        sys.exit(1)
    
    # Check if the package is installed
    try:
        import api_tester_mcp
        print("✅ Package found and ready")
    except ImportError:
        print("❌ Error: api_tester_mcp package not installed")
        print("   Please run: pip install -e .")
        sys.exit(1)
    
    # Ensure output directories exist
    os.makedirs("output/reports", exist_ok=True)
    os.makedirs("output/scenarios", exist_ok=True)
    os.makedirs("output/test_cases", exist_ok=True)
    print("✅ Output directories ready")
    
    # Parse command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--help"]
    
    if "--demo" in args:
        print("\n🎬 Running demonstration...")
        try:
            subprocess.run([sys.executable, "test_core.py"], check=True)
            print("\n✅ Demo completed successfully!")
            print("📁 Check the 'output' directory for generated files")
            print("🌐 Open output/reports/demo_api_test_report.html in your browser")
        except subprocess.CalledProcessError as e:
            print(f"❌ Demo failed: {e}")
            sys.exit(1)
        return
    
    if "--test" in args:
        print("\n🧪 Running tests...")
        try:
            subprocess.run([sys.executable, "-m", "pytest", "tests/"], check=True)
            print("✅ All tests passed!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed: {e}")
            sys.exit(1)
        return
    
    # Start the MCP server
    print("\n🌐 Starting MCP server...")
    print("   Use Ctrl+C to stop the server")
    print("   Configure your MCP client to connect to this server")
    print("")
    
    try:
        # Start server with default args if none provided
        if args == ["--help"]:
            args = ["--host", "localhost", "--port", "8000"]
        
        cmd = [sys.executable, "-m", "api_tester_mcp.server"] + args
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


def show_help():
    """Show help information"""
    print("""
API Tester MCP Server

Usage:
    python run.py [options]

Options:
    --demo              Run demonstration workflow
    --test              Run test suite
    --help              Show this help
    --host HOST         Server host (default: localhost)
    --port PORT         Server port (default: 8000)
    --log-level LEVEL   Log level (default: INFO)

Examples:
    python run.py --demo                    # Run demonstration
    python run.py --host 0.0.0.0 --port 9000  # Start server on all interfaces
    python run.py --test                    # Run tests

For more information, see DOCUMENTATION.md
""")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
    else:
        main()
