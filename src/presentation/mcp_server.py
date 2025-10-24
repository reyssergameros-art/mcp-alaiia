"""
MCP Server for ALAIIA API Testing Tools using FastMCP.
"""

from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional
import json

from ..mcp_tools import MCPToolsOrchestrator


class SwaggerAnalysisRequest(BaseModel):
    """Request model for Swagger analysis"""
    swagger_url: str
    format: Optional[str] = "detailed"  # "detailed" or "summary"


class FeatureGeneratorRequest(BaseModel):
    """Request model for feature generation"""
    swagger_data: dict
    output_dir: Optional[str] = "./output/features"


class JMeterGeneratorRequest(BaseModel):
    """Request model for JMeter generation"""
    source_data: dict
    source_type: str  # "swagger" or "features"
    output_file: Optional[str] = "./output/test_plan.jmx"


class CompleteWorkflowRequest(BaseModel):
    """Request model for complete workflow"""
    swagger_url: str
    output_dir: Optional[str] = "./output"


class CurlGeneratorRequest(BaseModel):
    """Request model for cURL generation"""
    swagger_data: dict
    output_dir: Optional[str] = "./output"


class CurlToTestsRequest(BaseModel):
    """Request model for cURL to tests conversion"""
    curl_command: str
    output_dir: Optional[str] = "./output"


class DatabaseQueryRequest(BaseModel):
    """Request model for database query execution"""
    query: str
    db_type: str  # postgres, mysql, sqlserver, sqlite
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: Optional[int] = 30
    max_rows: Optional[int] = 1000
    output_format: Optional[str] = "json"  # json, csv, markdown, table
    include_metadata: Optional[bool] = True
    output_file: Optional[str] = None


class QueryValidationRequest(BaseModel):
    """Request model for query validation"""
    query: str
    db_type: str


class ConnectionTestRequest(BaseModel):
    """Request model for database connection test"""
    db_type: str
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class AlaiiaMCPServer:
    """MCP Server for ALAIIA API Testing Tools"""
    
    def __init__(self):
        self.mcp = FastMCP("MCP-ALAIIA")
        self.orchestrator = MCPToolsOrchestrator()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools"""
        
        @self.mcp.tool()
        async def swagger_analysis(request: SwaggerAnalysisRequest) -> str:
            """
            Analyze Swagger/OpenAPI specifications from URL or file path.

            This tool provides comprehensive analysis of Swagger/OpenAPI specifications:
            - API structure and endpoints discovery
            - HTTP methods for each endpoint
            - Request headers (required/optional, types, constraints)
            - Request body structure and validation rules
            - Response definitions with status codes and descriptions
            - Automatic error handling and validation

            Args:
                request: SwaggerAnalysisRequest with swagger_url and format

            Returns:
                Complete analysis report in JSON format
            """
            try:
                result = await self.orchestrator.analyze_swagger_from_url(request.swagger_url)
                
                if result["success"]:
                    return f"""[SUCCESS] Swagger Analysis Completed Successfully!

API Analysis Results:
• Title: {result['data']['title']}
• Version: {result['data']['version']}
• Description: {result['data']['description']}
• Total Endpoints: {result['data']['total_endpoints']}
• Base URLs: {', '.join(result['data']['base_urls'])}

Complete Data (JSON):
{json.dumps(result, indent=2)}
"""
                else:
                    return f"[ERROR] Analysis Failed: {result.get('message', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error analyzing Swagger: {str(e)}"
        
        @self.mcp.tool()
        async def feature_generator(request: FeatureGeneratorRequest) -> str:
            """
            Generate Karate DSL feature files from Swagger analysis.

            This tool creates Karate DSL .feature files for API testing:
            - Automatic scenario generation for each endpoint
            - Request/response validation steps
            - Background configurations
            - Given-When-Then structure
            - Examples and data tables

            Args:
                request: FeatureGeneratorRequest with swagger_data and output_dir

            Returns:
                Feature generation results with file paths
            """
            try:
                result = await self.orchestrator.generate_features_from_swagger(
                    request.swagger_data, 
                    request.output_dir
                )
                
                if result["success"]:
                    data = result["data"]
                    return f"""[SUCCESS] Feature Generation Completed Successfully!

Generation Results:
• Total Features: {len(data['features'])}
• Total Scenarios: {data['total_scenarios']}
• Base URL: {data['base_url']}
• Output Directory: {request.output_dir}

Generated Files:
{chr(10).join(f"• {file}" for file in data.get('saved_files', []))}

Complete Data (JSON):
{json.dumps(result, indent=2)}
"""
                else:
                    return f"[ERROR] Generation Failed: {result.get('message', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error generating features: {str(e)}"
        
        @self.mcp.tool()
        async def jmeter_generator(request: JMeterGeneratorRequest) -> str:
            """
            Generate JMeter test plans from Swagger analysis or feature files.

            This tool creates JMeter .jmx files for performance testing:
            - Thread Groups with configurable parameters
            - HTTP requests for all endpoints
            - Required headers and UUID tracing
            - Request bodies for POST/PUT operations
            - Ready-to-run test plans

            Args:
                request: JMeterGeneratorRequest with source_data, source_type, and output_file

            Returns:
                JMeter generation results with file path
            """
            try:
                if request.source_type == "swagger":
                    result = await self.orchestrator.generate_jmeter_from_swagger(
                        request.source_data, 
                        request.output_file
                    )
                elif request.source_type == "features":
                    result = await self.orchestrator.generate_jmeter_from_features(
                        request.source_data, 
                        request.output_file
                    )
                else:
                    return "[ERROR] Error: source_type must be 'swagger' or 'features'"
                
                if result["success"]:
                    data = result["data"]
                    return f"""[SUCCESS] JMeter Generation Completed Successfully!

Generation Results:
• Test Plan: {data['test_plan_name']}
• Thread Groups: {data['total_thread_groups']}
• Total Requests: {data['total_requests']}
• Output File: {data.get('saved_file', request.output_file)}

Complete Data (JSON):
{json.dumps(result, indent=2)}
"""
                else:
                    return f"[ERROR] Generation Failed: {result.get('message', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error generating JMeter plan: {str(e)}"
        
        @self.mcp.tool()
        async def curl_generator(request: CurlGeneratorRequest) -> str:
            """
            Generate cURL commands and Postman collection from Swagger analysis.

            This tool creates ready-to-use cURL commands and Postman collections:
            - Generates executable cURL commands for each endpoint
            - Includes all headers and request bodies
            - Creates Postman v2.1 collection for import
            - Supports path parameter substitution
            - Exports both .sh script and .json collection

            Args:
                request: CurlGeneratorRequest with swagger_data and output_dir

            Returns:
                cURL generation results with file paths
            """
            try:
                result = await self.orchestrator.generate_curl_from_swagger(
                    request.swagger_data,
                    request.output_dir
                )
                
                if result["success"]:
                    data = result["data"]
                    return f"""[SUCCESS] cURL Generation Completed Successfully!

Generation Results:
• Total Commands: {data['total_commands']}
• Base URL: {data['base_url']}
• Collection Name: {data['collection_name']}

Generated Files:
• cURL Script: {data['curl_file']}
• Postman Collection: {data['postman_file']}

You can:
1. Execute cURL commands: bash {data['curl_file']}
2. Import to Postman: File → Import → {data['postman_file']}

Complete Data (JSON):
{json.dumps(result, indent=2)}
"""
                else:
                    return f"[ERROR] Generation Failed: {result.get('message', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error generating cURL commands: {str(e)}"
        
        @self.mcp.tool()
        async def curl_to_tests(request: CurlToTestsRequest) -> str:
            """
            Generate test artifacts from cURL command.

            Parses a cURL command and generates:
            - Karate DSL .feature files
            - JMeter .jmx test plans
            
            Uses existing generators WITHOUT modification.

            Args:
                request: CurlToTestsRequest with curl_command and output_dir

            Returns:
                Test generation results
            """
            try:
                result = await self.orchestrator.parse_curl_to_tests(
                    request.curl_command,
                    request.output_dir
                )
                
                if result["success"]:
                    data = result["data"]
                    parsed = data['parsed_curl']
                    
                    summary = f"""[SUCCESS] Tests Generated from cURL!

Parsed cURL:
• Method: {parsed['method']}
• Path: {parsed['path']}
• Base URL: {parsed['base_url']}
• Headers: {parsed['headers_count']}
• Has Body: {parsed['has_body']}
"""
                    
                    if data.get('features_generation'):
                        features = data['features_generation']
                        summary += f"""
Features:
• Files: {len(features['features'])}
• Scenarios: {features['total_scenarios']}
"""
                    
                    if data.get('jmeter_generation'):
                        jmeter = data['jmeter_generation']
                        summary += f"""
JMeter:
• Requests: {jmeter['total_requests']}
• File: {jmeter.get('saved_file', 'N/A')}
"""
                    
                    summary += f"""
Output: {request.output_dir}

Complete Data (JSON):
{json.dumps(result, indent=2)}
"""
                    return summary
                else:
                    return f"[ERROR] Failed: {result.get('message', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error: {str(e)}"
        
        @self.mcp.tool()
        async def complete_workflow(request: CompleteWorkflowRequest) -> str:
            """
            Execute complete workflow: Swagger Analysis → Feature Generation → JMeter Generation → cURL Generation.

            This tool executes the full ALAIIA pipeline in one operation:
            1. Analyzes the Swagger/OpenAPI specification
            2. Generates Karate DSL .feature files
            3. Creates JMeter .jmx test plan
            4. Generates cURL commands and Postman collection
            5. Saves all artifacts to the specified output directory

            Args:
                request: CompleteWorkflowRequest with swagger_url and output_dir

            Returns:
                Complete workflow results with all generated artifacts
            """
            try:
                result = await self.orchestrator.complete_workflow(
                    request.swagger_url, 
                    request.output_dir
                )
                
                if result["success"]:
                    data = result["data"]
                    swagger_data = data['swagger_analysis']
                    features_data = data['features_generation']
                    
                    summary = f"""[SUCCESS] Complete Workflow Executed Successfully!

Swagger Analysis:
• API: {swagger_data['title']} v{swagger_data['version']}
• Endpoints Analyzed: {swagger_data['total_endpoints']}

Feature Generation:
• Feature Files: {len(features_data['features'])}
• Total Scenarios: {features_data['total_scenarios']}

JMeter Generation:"""
                    
                    if data.get('jmeter_generation'):
                        jmeter_data = data['jmeter_generation']
                        summary += f"\n• Requests: {jmeter_data['total_requests']}"
                    
                    # Add cURL generation info
                    if data.get('curl_generation'):
                        curl_data = data['curl_generation']
                        summary += f"""

cURL Generation:
• Commands Generated: {curl_data['total_commands']}
• cURL Script: {curl_data['curl_file']}
• Postman Collection: {curl_data['postman_file']}"""
                    
                    summary += f"""

Output Directory: {request.output_dir}

All artifacts generated successfully!
Check the output directory for .feature, .jmx, .sh and .json files.

Complete Data (JSON):
{json.dumps(result, indent=2)}
"""
                    return summary
                else:
                    return f"[ERROR] Workflow Failed: {result.get('message', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error executing workflow: {str(e)}"
        
        @self.mcp.tool()
        async def database_query(request: DatabaseQueryRequest) -> str:
            """
            Execute database query with validation and result formatting.
            
            This tool executes SQL queries against databases with security features:
            - Read-only query validation (SELECT, WITH allowed)
            - Blocks write operations (INSERT, UPDATE, DELETE, DROP, etc.)
            - Query timeout protection
            - Row limit enforcement
            - Multiple output formats (JSON, CSV, Markdown, Table)
            - Optional file export
            
            Args:
                request: DatabaseQueryRequest with query, connection, and formatting options
            
            Returns:
                Query results with metadata or error details
            """
            try:
                result = await self.orchestrator.execute_database_query(
                    query=request.query,
                    db_type=request.db_type,
                    connection_string=request.connection_string,
                    host=request.host,
                    port=request.port,
                    database=request.database,
                    username=request.username,
                    password=request.password,
                    timeout=request.timeout,
                    max_rows=request.max_rows,
                    output_format=request.output_format,
                    include_metadata=request.include_metadata,
                    output_file=request.output_file
                )
                
                if result["success"]:
                    summary_data = result["summary"]
                    
                    response = f"""[SUCCESS] Database Query Executed Successfully!

Query Execution Summary:
• Database Type: {summary_data['database_type']}
• Rows Retrieved: {summary_data['row_count']}
• Columns: {summary_data['column_count']}
• Execution Time: {summary_data['execution_time_seconds']} seconds
• Truncated: {'Yes' if summary_data['truncated'] else 'No'}
• Timestamp: {summary_data['timestamp']}

Query Preview:
{summary_data['query_preview']}
"""
                    
                    # Add validation info if metadata included
                    if request.include_metadata and result.get("validation"):
                        validation = result["validation"]
                        response += f"""
Validation:
• Valid: {validation['is_valid']}
• Read-only: {validation['is_read_only']}
• Operations Detected: {', '.join(validation['detected_operations'])}
"""
                        if validation['warnings']:
                            response += f"• Warnings: {', '.join(validation['warnings'])}\n"
                    
                    # Add output file info if saved
                    if request.output_file and result.get("output_file"):
                        response += f"\n✓ Results saved to: {result['output_file']}\n"
                    
                    # Add formatted results based on output format
                    if request.output_format == "json":
                        response += f"\nResults (JSON):\n{json.dumps(result['result'], indent=2)}\n"
                    else:
                        response += f"\nResults ({request.output_format.upper()}):\n{result['result']}\n"
                    
                    return response
                else:
                    error_msg = result.get('error', 'Unknown error')
                    response = f"[ERROR] Database Query Failed: {error_msg}"
                    
                    # Add validation errors if present
                    if result.get('validation'):
                        validation = result['validation']
                        if validation.get('errors'):
                            response += f"\n\nValidation Errors:\n"
                            for error in validation['errors']:
                                response += f"  • {error}\n"
                    
                    return response
                    
            except Exception as e:
                return f"[ERROR] Error executing database query: {str(e)}"
        
        @self.mcp.tool()
        async def validate_query(request: QueryValidationRequest) -> str:
            """
            Validate database query without executing it.
            
            This tool validates SQL queries for safety:
            - Checks for read-only operations
            - Detects write operations (INSERT, UPDATE, DELETE, etc.)
            - Identifies dangerous patterns
            - Provides warnings and errors
            
            Args:
                request: QueryValidationRequest with query and db_type
            
            Returns:
                Validation results with detailed feedback
            """
            try:
                result = await self.orchestrator.validate_database_query(
                    query=request.query,
                    db_type=request.db_type
                )
                
                if result["success"]:
                    validation = result["validation"]
                    
                    response = f"""[VALIDATION] Query Validation Results:

Status:
• Valid: {validation['is_valid']}
• Read-only: {validation['is_read_only']}
• Operations Detected: {', '.join(validation['detected_operations']) if validation['detected_operations'] else 'None'}
"""
                    
                    if validation['errors']:
                        response += f"\nErrors ({validation['error_count']}):\n"
                        for error in validation['errors']:
                            response += f"  ❌ {error}\n"
                    
                    if validation['warnings']:
                        response += f"\nWarnings ({validation['warning_count']}):\n"
                        for warning in validation['warnings']:
                            response += f"  ⚠️  {warning}\n"
                    
                    if validation['is_valid'] and validation['is_read_only']:
                        response += "\n✓ Query is safe to execute!\n"
                    else:
                        response += "\n✗ Query is NOT safe to execute!\n"
                    
                    return response
                else:
                    return f"[ERROR] Validation Failed: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error validating query: {str(e)}"
        
        @self.mcp.tool()
        async def test_connection(request: ConnectionTestRequest) -> str:
            """
            Test database connection without executing queries.
            
            This tool verifies database connectivity:
            - Tests connection establishment
            - Verifies credentials
            - Checks network connectivity
            - Returns connection metadata
            
            Args:
                request: ConnectionTestRequest with connection parameters
            
            Returns:
                Connection test results
            """
            try:
                result = await self.orchestrator.test_database_connection(
                    db_type=request.db_type,
                    connection_string=request.connection_string,
                    host=request.host,
                    port=request.port,
                    database=request.database,
                    username=request.username,
                    password=request.password
                )
                
                if result["success"]:
                    conn_info = result["connection_info"]
                    is_connected = result["is_connected"]
                    
                    response = f"""[CONNECTION TEST] Database Connection Test Results:

Status: {'✓ CONNECTED' if is_connected else '✗ FAILED'}

Connection Details:
• Database Type: {conn_info['database_type']}
• Host: {conn_info['host']}
• Port: {conn_info['port']}
• Database: {conn_info['database']}
• Username: {conn_info['username']}
• Pool Size: {conn_info.get('pool_size', 'N/A')}
"""
                    return response
                else:
                    return f"[ERROR] Connection Test Failed: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error testing connection: {str(e)}"
        
        @self.mcp.tool()
        async def get_supported_databases() -> str:
            """
            Get list of supported database types.
            
            Returns the list of database engines supported by this tool.
            Currently supports PostgreSQL, with planned support for:
            - MySQL
            - SQL Server
            - SQLite
            - MongoDB
            
            Returns:
                List of supported database types
            """
            try:
                result = self.orchestrator.get_supported_databases()
                
                if result["success"]:
                    databases = result["supported_databases"]
                    
                    response = f"""[INFO] Supported Database Types:

Currently Supported:
"""
                    for db in databases:
                        response += f"  ✓ {db}\n"
                    
                    response += """
Planned Support:
  ⏳ mysql
  ⏳ sqlserver
  ⏳ sqlite
  ⏳ mongodb

Use these values for the 'db_type' parameter in database queries.
"""
                    return response
                else:
                    return f"[ERROR] Failed to get supported databases: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                return f"[ERROR] Error getting supported databases: {str(e)}"
    
    def get_mcp_app(self):
        """Get the FastMCP application"""
        return self.mcp