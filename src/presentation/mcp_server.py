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
            3. Creates JMeter .jmx test plans (both from Swagger and Features)
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
                    
                    if data.get('jmeter_from_swagger'):
                        jmeter_swagger = data['jmeter_from_swagger']
                        summary += f"\n• From Swagger: {jmeter_swagger['total_requests']} requests"
                    
                    if data.get('jmeter_from_features'):
                        jmeter_features = data['jmeter_from_features']
                        summary += f"\n• From Features: {jmeter_features['total_requests']} requests"
                    
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
    
    def get_mcp_app(self):
        """Get the FastMCP application"""
        return self.mcp