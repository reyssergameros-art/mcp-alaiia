"""Main MCP server implementation with integrated tools."""
import asyncio
import json
import os
from typing import Dict, Any, List
from dataclasses import asdict

# Import tool services
from src.tools.swagger_analysis.application.services import SwaggerAnalysisService
from src.tools.swagger_analysis.infrastructure.repositories import HttpSwaggerRepository
from src.tools.feature_generator.application.services import FeatureGenerationService
from src.tools.feature_generator.infrastructure.repositories import KarateFeatureRepository
from src.tools.jmeter_generator.application.services import JMeterGenerationService
from src.tools.jmeter_generator.infrastructure.repositories import XmlJMeterRepository
from src.tools.curl_generator.application.services import CurlGenerationService
from src.tools.curl_generator.infrastructure.repositories import JsonCurlRepository
from src.tools.curl_parser.application.services import CurlParsingService
from src.tools.curl_parser.infrastructure.repositories import RegexCurlParser
from src.tools.karate_java_generator.application.services import KarateJavaGenerationService
from src.tools.karate_java_generator.infrastructure.repositories import FileSystemKarateJavaRepository


class MCPToolsOrchestrator:
    """Orchestrator for all MCP tools that coordinates their interactions."""
    
    def __init__(self):
        # Initialize repositories
        self.swagger_repo = HttpSwaggerRepository()
        self.feature_repo = KarateFeatureRepository()
        self.jmeter_repo = XmlJMeterRepository()
        self.curl_repo = JsonCurlRepository()
        self.curl_parser_repo = RegexCurlParser()
        self.karate_java_repo = FileSystemKarateJavaRepository()
        
        # Initialize services
        self.swagger_service = SwaggerAnalysisService(self.swagger_repo)
        self.feature_service = FeatureGenerationService(self.feature_repo)
        self.jmeter_service = JMeterGenerationService(self.jmeter_repo)
        self.curl_service = CurlGenerationService(self.curl_repo)
        self.curl_parser_service = CurlParsingService(self.curl_parser_repo)
        self.karate_java_service = KarateJavaGenerationService(self.karate_java_repo)
    
    async def analyze_swagger_from_url(self, swagger_url: str) -> Dict[str, Any]:
        """
        Tool 1: Analyze swagger specification from URL.
        
        Args:
            swagger_url: URL to the swagger/OpenAPI specification
            
        Returns:
            Comprehensive swagger analysis result
        """
        try:
            # Use swagger analysis service
            result = await self.swagger_service.analyze_swagger(swagger_url)
            
            # Convert to dictionary for JSON serialization
            result_dict = {
                "title": result.title,
                "version": result.version,
                "description": result.description,
                "contact_info": result.contact_info,
                "license_info": result.license_info,
                "base_urls": result.base_urls,
                "total_endpoints": result.total_endpoints,
                "endpoints": []
            }
            
            # Convert endpoints using service method
            for endpoint in result.endpoints:
                endpoint_dict = {
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "summary": endpoint.summary,
                    "description": endpoint.description,
                    "operation_id": endpoint.operation_id,
                    "tags": endpoint.tags,
                    "headers": [self.swagger_service.convert_field_info_to_dict(h) for h in endpoint.headers],
                    "path_parameters": [self.swagger_service.convert_field_info_to_dict(p) for p in endpoint.path_parameters],
                    "query_parameters": [self.swagger_service.convert_field_info_to_dict(q) for q in endpoint.query_parameters],
                    "request_body": {k: self.swagger_service.convert_field_info_to_dict(v) for k, v in endpoint.request_body.items()} if endpoint.request_body else None,
                    "request_content_type": endpoint.request_content_type,
                    "responses": [self.swagger_service.convert_response_info_to_dict(r) for r in endpoint.responses]
                }
                result_dict["endpoints"].append(endpoint_dict)
            
            # Get summary
            summary = self.swagger_service.get_analysis_summary(result)
            result_dict["summary"] = summary
            
            return {
                "success": True,
                "data": result_dict,
                "message": f"Successfully analyzed {result.total_endpoints} endpoints from swagger specification"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze swagger specification"
            }
    
    async def generate_features_from_swagger(self, swagger_data: Dict[str, Any], output_dir: str = None) -> Dict[str, Any]:
        """
        Tool 2: Generate Karate DSL feature files from swagger analysis.
        
        Args:
            swagger_data: Swagger analysis result from tool 1
            output_dir: Directory to save feature files (optional)
            
        Returns:
            Feature generation result with file paths if saved
        """
        try:
            # Use feature generation service
            result = await self.feature_service.generate_features_from_swagger(swagger_data)
            
            # Convert to dictionary
            result_dict = {
                "base_url": result.base_url,
                "total_scenarios": result.total_scenarios,
                "features": []
            }
            
            # Convert features
            for feature in result.features:
                feature_dict = {
                    "feature_name": feature.feature_name,
                    "description": feature.description,
                    "tags": feature.tags,
                    "background_steps": feature.background_steps,
                    "scenarios": [],
                    "content": result.get_feature_content(feature)
                }
                
                # Convert scenarios
                for scenario in feature.scenarios:
                    scenario_dict = {
                        "name": scenario.name,
                        "description": scenario.description,
                        "given_steps": scenario.given_steps,
                        "when_steps": scenario.when_steps,
                        "then_steps": scenario.then_steps,
                        "examples": scenario.examples
                    }
                    feature_dict["scenarios"].append(scenario_dict)
                
                result_dict["features"].append(feature_dict)
            
            # Save files if output directory is provided
            saved_files = []
            if output_dir:
                saved_files = await self.feature_service.save_features_to_directory(result, output_dir)
            
            # Get summary
            summary = self.feature_service.get_features_summary(result)
            result_dict["summary"] = summary
            result_dict["saved_files"] = saved_files
            
            return {
                "success": True,
                "data": result_dict,
                "message": f"Successfully generated {len(result.features)} feature files with {result.total_scenarios} scenarios"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate feature files"
            }
    
    async def generate_jmeter_from_swagger(self, swagger_data: Dict[str, Any], output_file: str = None) -> Dict[str, Any]:
        """
        Tool 3a: Generate JMeter test plan from swagger analysis.
        
        Args:
            swagger_data: Swagger analysis result from tool 1
            output_file: File path to save JMX file (optional)
            
        Returns:
            JMeter generation result with file path if saved
        """
        try:
            # Use JMeter generation service
            result = await self.jmeter_service.generate_from_swagger(swagger_data)
            
            # Save file if output path is provided
            saved_file = None
            if output_file:
                saved_file = await self.jmeter_service.save_test_plan(result, output_file)
            
            # Get summary
            summary = self.jmeter_service.get_test_plan_summary(result)
            
            return {
                "success": True,
                "data": {
                    "test_plan_name": result.test_plan.name,
                    "total_requests": result.total_requests,
                    "total_thread_groups": result.total_thread_groups,
                    "xml_content": result.xml_content,
                    "summary": summary,
                    "saved_file": saved_file
                },
                "message": f"Successfully generated JMeter test plan with {result.total_thread_groups} thread groups and {result.total_requests} requests"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate JMeter test plan from swagger"
            }
    
    async def generate_jmeter_from_features(self, features_data: Dict[str, Any], output_file: str = None) -> Dict[str, Any]:
        """
        Tool 3b: Generate JMeter test plan from feature files.
        
        Args:
            features_data: Feature generation result from tool 2
            output_file: File path to save JMX file (optional)
            
        Returns:
            JMeter generation result with file path if saved
        """
        try:
            # Use JMeter generation service
            result = await self.jmeter_service.generate_from_features(features_data)
            
            # Save file if output path is provided
            saved_file = None
            if output_file:
                saved_file = await self.jmeter_service.save_test_plan(result, output_file)
            
            # Get summary
            summary = self.jmeter_service.get_test_plan_summary(result)
            
            return {
                "success": True,
                "data": {
                    "test_plan_name": result.test_plan.name,
                    "total_requests": result.total_requests,
                    "total_thread_groups": result.total_thread_groups,
                    "xml_content": result.xml_content,
                    "summary": summary,
                    "saved_file": saved_file
                },
                "message": f"Successfully generated JMeter test plan with {result.total_thread_groups} thread groups and {result.total_requests} requests"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate JMeter test plan from features"
            }
    
    async def generate_curl_from_swagger(self, swagger_data: Dict[str, Any], output_dir: str = "./output") -> Dict[str, Any]:
        """
        Tool 4: Generate cURL commands and Postman collection from swagger analysis.
        
        Args:
            swagger_data: Swagger analysis result from tool 1
            output_dir: Directory to save generated files (optional)
            
        Returns:
            cURL generation result with file paths
        """
        try:
            # Use cURL generation service
            result = await self.curl_service.generate_from_swagger(swagger_data)
            
            # Prepare output file paths
            curl_file = os.path.join(output_dir, "curl_commands.sh")
            postman_file = os.path.join(output_dir, "postman_collection.json")
            
            # Save cURL commands
            curl_path = await self.curl_service.export_curl_commands(
                result.curl_commands,
                curl_file
            )
            
            # Save Postman collection
            postman_path = await self.curl_service.export_postman_collection(
                result.postman_collection,
                postman_file
            )
            
            return {
                "success": True,
                "data": {
                    "total_commands": result.total_commands,
                    "base_url": result.base_url,
                    "curl_file": curl_path,
                    "postman_file": postman_path,
                    "collection_name": result.postman_collection.name,
                    "summary": result.get_summary()
                },
                "message": f"Successfully generated {result.total_commands} cURL commands and Postman collection"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate cURL commands"
            }
    
    async def parse_curl_to_tests(self, curl_command: str, output_dir: str = "./output") -> Dict[str, Any]:
        """
        Tool 5: Parse cURL and generate tests using EXISTING generators.
        
        This method:
        1. Parses the cURL command
        2. Converts to swagger-compatible format using dedicated mapper
        3. REUSES feature_generator (without modification)
        4. REUSES jmeter_generator (without modification)
        
        Args:
            curl_command: Raw cURL command string
            output_dir: Output directory for generated files
            
        Returns:
            Generation results
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Parse cURL
            parse_result = await self.curl_parser_service.parse_curl(curl_command)
            
            # Step 2: Convert to swagger-compatible format using mapper
            swagger_data = self.curl_parser_service.convert_to_swagger(parse_result)
            
            # Step 3: Generate features using EXISTING generator
            features_dir = os.path.join(output_dir, "features")
            features_result = await self.generate_features_from_swagger(swagger_data, features_dir)
            
            # Step 4: Generate JMeter using EXISTING generator
            jmx_file = os.path.join(output_dir, "test_plan_from_curl.jmx")
            jmeter_result = await self.generate_jmeter_from_swagger(swagger_data, jmx_file)
            
            return {
                "success": True,
                "data": {
                    "parsed_curl": parse_result.get_summary(),
                    "swagger_data": swagger_data,
                    "features_generation": features_result.get("data") if features_result.get("success") else None,
                    "jmeter_generation": jmeter_result.get("data") if jmeter_result.get("success") else None,
                    "output_directory": output_dir
                },
                "message": "Successfully generated tests from cURL command"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to parse cURL and generate tests"
            }
    
    async def generate_karate_java_project(
        self,
        swagger_url: str = None,
        curl_command: str = None,
        output_dir: str = "./output/karate-project",
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Tool 7: Generate complete Karate Java project.
        
        This tool:
        1. Analyzes API (from Swagger or cURL)
        2. Generates feature files
        3. Creates complete Maven Java project with:
           - Test runners
           - Hooks
           - Configuration classes
           - Utility classes
           - Karate features
           - Maven pom.xml
           - README and documentation
        
        Args:
            swagger_url: URL to swagger specification (optional if curl_command provided)
            curl_command: cURL command (optional if swagger_url provided)
            output_dir: Directory to create the project
            config: Optional project configuration
            
        Returns:
            Complete project generation result
        """
        try:
            # Validate inputs
            if not swagger_url and not curl_command:
                raise ValueError("Either swagger_url or curl_command must be provided")
            
            # Step 1: Get swagger data
            if swagger_url:
                swagger_result = await self.analyze_swagger_from_url(swagger_url)
                if not swagger_result["success"]:
                    return swagger_result
                swagger_data = swagger_result["data"]
            else:
                # Parse cURL and convert to swagger format
                parse_result = await self.curl_parser_service.parse_curl(curl_command)
                swagger_data = self.curl_parser_service.convert_to_swagger(parse_result)
            
            # Step 2: Generate features (reuse existing generator)
            features_result = await self.feature_service.generate_features_from_swagger(swagger_data)
            features_data = {
                "base_url": features_result.base_url,
                "total_scenarios": features_result.total_scenarios,
                "features": []
            }
            
            # Convert features to dict format
            for feature in features_result.features:
                # Generate feature content using the service method
                feature_content = features_result.get_feature_content(feature)
                
                feature_dict = {
                    "feature_name": feature.feature_name,
                    "description": feature.description,
                    "tags": feature.tags if feature.tags else [],
                    "content": feature_content,
                    "scenarios": []
                }
                
                for scenario in feature.scenarios:
                    scenario_dict = {
                        "name": scenario.name,
                        "description": scenario.description,
                        "given_steps": scenario.given_steps,
                        "when_steps": scenario.when_steps,
                        "then_steps": scenario.then_steps
                    }
                    feature_dict["scenarios"].append(scenario_dict)
                
                features_data["features"].append(feature_dict)
            
            # Step 3: Generate Karate Java project
            project = await self.karate_java_service.generate_project(
                swagger_data=swagger_data,
                features_data=features_data,
                output_dir=output_dir,
                config=config
            )
            
            # Get project summary
            summary = self.karate_java_service.get_project_summary(project)
            
            return {
                "success": True,
                "data": {
                    "project_path": output_dir,
                    "summary": summary,
                    "maven_config": {
                        "group_id": project.maven_config.group_id,
                        "artifact_id": project.maven_config.artifact_id,
                        "version": project.maven_config.version,
                        "karate_version": project.maven_config.karate_version
                    },
                    "files_generated": {
                        "java_classes": summary["total_java_classes"],
                        "test_runners": summary["test_runners"],
                        "hooks": summary["hooks"],
                        "config_classes": summary["config_classes"],
                        "utils": summary["utils"],
                        "features": summary["total_features"]
                    }
                },
                "message": f"Successfully generated Karate Java project at {output_dir}"
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "message": f"Failed to generate Karate Java project: {str(e)}"
            }
    
    async def complete_workflow(self, swagger_url: str, output_dir: str = "./output") -> Dict[str, Any]:
        """
        Complete workflow: Swagger -> Features -> JMeter -> cURL.
        
        Args:
            swagger_url: URL to the swagger/OpenAPI specification
            output_dir: Directory to save all output files
            
        Returns:
            Complete workflow result with all generated artifacts
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Analyze swagger
            swagger_result = await self.analyze_swagger_from_url(swagger_url)
            if not swagger_result["success"]:
                return swagger_result
            
            swagger_data = swagger_result["data"]
            
            # Step 2: Generate features
            features_dir = os.path.join(output_dir, "features")
            features_result = await self.generate_features_from_swagger(swagger_data, features_dir)
            if not features_result["success"]:
                return features_result
            
            features_data = features_result["data"]
            
            # Step 3a: Generate JMeter from swagger
            jmx_from_swagger_file = os.path.join(output_dir, "test_plan_from_swagger.jmx")
            jmeter_swagger_result = await self.generate_jmeter_from_swagger(swagger_data, jmx_from_swagger_file)
            
            # Step 3b: Generate JMeter from features
            jmx_from_features_file = os.path.join(output_dir, "test_plan_from_features.jmx")
            jmeter_features_result = await self.generate_jmeter_from_features(features_data, jmx_from_features_file)
            
            # Step 4: Generate cURL commands and Postman collection
            curl_result = await self.generate_curl_from_swagger(swagger_data, output_dir)
            
            return {
                "success": True,
                "data": {
                    "swagger_analysis": swagger_data,
                    "features_generation": features_data,
                    "jmeter_from_swagger": jmeter_swagger_result["data"] if jmeter_swagger_result["success"] else None,
                    "jmeter_from_features": jmeter_features_result["data"] if jmeter_features_result["success"] else None,
                    "curl_generation": curl_result["data"] if curl_result["success"] else None,
                    "output_directory": output_dir
                },
                "message": "Complete workflow executed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute complete workflow"
            }
