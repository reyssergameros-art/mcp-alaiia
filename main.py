#!/usr/bin/env python3
"""
MCP-ALAIIA Server using FastMCP
"""

import sys
from pathlib import Path

# Simple path setup
sys.path.insert(0, str(Path(__file__).parent))

from src.presentation.mcp_server import AlaiiaMCPServer


def main():
    """Main entry point for the MCP server"""
    try:
        server = AlaiiaMCPServer()
        mcp_app = server.get_mcp_app()
        
        print("# MCP-ALAIIA: API Testing Automation Tools")
        print("=" * 60)
        print("Server ready to analyze APIs and generate test artifacts")
        print("\nAvailable tools:")
        print("   * swagger_analysis    - Analyze Swagger/OpenAPI specifications")
        print("   * feature_generator   - Generate Karate DSL .feature files")
        print("   * jmeter_generator    - Generate JMeter .jmx test plans")
        print("   * curl_generator      - Generate cURL commands & Postman collections")
        print("   * complete_workflow   - Execute full pipeline")
        print("\nOptimized workflow:")
        print("   swagger_analysis -> feature_generator")
        print("   swagger_analysis -> jmeter_generator")
        print("   swagger_analysis -> curl_generator")
        print("   complete_workflow (all in one)")
        print("=" * 60)
        
        mcp_app.run()
        
    except KeyboardInterrupt:
        print("\n[STOP] Server shutting down...")
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
