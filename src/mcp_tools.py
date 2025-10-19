"""Main MCP server implementation with integrated tools."""
import asyncio
import json
import os
from typing import Dict, Any, List
from dataclasses import asdict
from datetime import datetime

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
from src.tools.database_query.application.services import DatabaseQueryService
from src.tools.database_query.domain.models import DatabaseConnection, QueryRequest, DatabaseType

# Import shared components
from src.shared.output_manager import OutputManager


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
        self.database_query_service = DatabaseQueryService()
    
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
    
    async def generate_features_from_swagger(self, swagger_data: Dict[str, Any], output_dir: str = None, use_auto_structure: bool = True) -> Dict[str, Any]:
        """
        Tool 2: Generate Karate DSL feature files from swagger analysis.
        
        Args:
            swagger_data: Swagger analysis result from tool 1
            output_dir: Directory to save feature files (optional, auto-generated if None)
            use_auto_structure: Whether to use OutputManager auto structure (default: True)
            
        Returns:
            Feature generation result with file paths if saved
        """
        try:
            execution_start = datetime.now()
            
            # Use feature generation service
            result = await self.feature_service.generate_features_from_swagger(swagger_data)
            
            # Determinar output directory
            # SOLO usar auto-structure si está habilitado Y no se proporciona un directorio específico
            if use_auto_structure and (output_dir is None or OutputManager.should_use_auto_structure(output_dir)):
                # Usar OutputManager para estructura automática
                identifier = OutputManager.extract_identifier_from_swagger(swagger_data)
                output_path = OutputManager.create_output_directory(
                    'features',
                    identifier,
                    execution_start
                )
                
                # Usar directamente el path creado por OutputManager (sin subdirectorio extra)
                actual_output_dir = str(output_path)
                
                # Guardar metadatos
                metadata = {
                    'output_type': 'features',
                    'source': {
                        'type': 'swagger',
                        'title': swagger_data.get('title', 'Unknown'),
                        'base_urls': swagger_data.get('base_urls', [])
                    },
                    'execution_time_seconds': None,  # Se actualiza al final
                    'summary': {
                        'total_features': len(result.features),
                        'total_scenarios': result.total_scenarios
                    }
                }
            else:
                # Respetar directorio manual o cuando use_auto_structure=False
                actual_output_dir = output_dir if output_dir else "./output/features"
                output_path = None
                # Asegurar que el directorio existe
                os.makedirs(actual_output_dir, exist_ok=True)
            
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
            
            # Save files
            saved_files = []
            if actual_output_dir:
                saved_files = await self.feature_service.save_features_to_directory(result, actual_output_dir)
            
            # Get summary
            summary = self.feature_service.get_features_summary(result)
            result_dict["summary"] = summary
            result_dict["saved_files"] = saved_files
            result_dict["output_directory"] = str(output_path) if output_path else actual_output_dir
            
            # Guardar metadatos y summary si usamos estructura automática
            if output_path:
                execution_time = (datetime.now() - execution_start).total_seconds()
                metadata['execution_time_seconds'] = execution_time
                metadata['summary']['files_generated'] = len(saved_files)
                
                OutputManager.save_metadata(output_path, metadata)
                OutputManager.save_summary(output_path, summary)
            
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
    
    async def generate_jmeter_from_swagger(self, swagger_data: Dict[str, Any], output_file: str = None, use_auto_structure: bool = True) -> Dict[str, Any]:
        """
        Tool 3a: Generate JMeter test plan from swagger analysis.
        
        Args:
            swagger_data: Swagger analysis result from tool 1
            output_file: File path to save JMX file (optional)
            use_auto_structure: Whether to use OutputManager auto structure (default: True)
            
        Returns:
            JMeter generation result with file path if saved
        """
        try:
            # Use JMeter generation service
            result = await self.jmeter_service.generate_from_swagger(swagger_data)
            
            # Determinar output file
            saved_file = None
            # SOLO usar auto-structure si está habilitado Y no se proporciona un archivo específico
            if use_auto_structure and (output_file is None or OutputManager.should_use_auto_structure(output_file)):
                # Usar OutputManager para estructura automática
                execution_start = datetime.now()
                identifier = OutputManager.extract_identifier_from_swagger(swagger_data)
                output_path = OutputManager.create_output_directory(
                    'jmeter',
                    identifier,
                    execution_start
                )
                actual_output_file = str(output_path / "test-plan.jmx")
                
                # Guardar metadatos
                metadata = {
                    'output_type': 'jmeter',
                    'source': {
                        'type': 'swagger',
                        'title': swagger_data.get('title', 'Unknown'),
                        'base_urls': swagger_data.get('base_urls', [])
                    },
                    'summary': {
                        'total_thread_groups': result.total_thread_groups,
                        'total_requests': result.total_requests
                    }
                }
                OutputManager.save_metadata(output_path, metadata)
                saved_file = await self.jmeter_service.save_test_plan(result, actual_output_file)
            elif output_file:
                # Respetar path manual cuando use_auto_structure=False o path específico
                actual_output_file = output_file
                # Asegurar que el directorio padre existe
                os.makedirs(os.path.dirname(actual_output_file), exist_ok=True)
                saved_file = await self.jmeter_service.save_test_plan(result, actual_output_file)
            
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
    
    async def generate_jmeter_from_features(self, features_data: Dict[str, Any], output_file: str = None, use_auto_structure: bool = True) -> Dict[str, Any]:
        """
        Tool 3b: Generate JMeter test plan from feature files.
        
        Args:
            features_data: Features generation result from tool 2
            output_file: File path to save JMX file (optional)
            use_auto_structure: Whether to use OutputManager auto structure (default: True)
            
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
    
    async def generate_curl_from_swagger(self, swagger_data: Dict[str, Any], output_dir: str = None, use_auto_structure: bool = True) -> Dict[str, Any]:
        """
        Tool 4: Generate cURL commands and Postman collection from swagger analysis.
        
        Args:
            swagger_data: Swagger analysis result from tool 1
            output_dir: Directory to save generated files (optional, auto-generated if None)
            use_auto_structure: Whether to use OutputManager auto structure (default: True)
            
        Returns:
            cURL generation result with file paths
        """
        try:
            execution_start = datetime.now()
            
            # Use cURL generation service
            result = await self.curl_service.generate_from_swagger(swagger_data)
            
            # Determinar output directory
            # SOLO usar auto-structure si está habilitado Y no se proporciona un directorio específico
            if use_auto_structure and (output_dir is None or OutputManager.should_use_auto_structure(output_dir)):
                # Usar OutputManager para estructura automática
                identifier = OutputManager.extract_identifier_from_swagger(swagger_data)
                output_path = OutputManager.create_output_directory(
                    'curl',
                    identifier,
                    execution_start
                )
                actual_output_dir = str(output_path)
                
                # Guardar metadatos
                metadata = {
                    'output_type': 'curl',
                    'source': {
                        'type': 'swagger',
                        'title': swagger_data.get('title', 'Unknown'),
                        'base_urls': swagger_data.get('base_urls', [])
                    },
                    'execution_time_seconds': None,
                    'summary': {
                        'total_commands': result.total_commands
                    }
                }
            else:
                # Respetar directorio manual o cuando use_auto_structure=False
                actual_output_dir = output_dir if output_dir else "./output/curl"
                output_path = None
                # Asegurar que el directorio existe
                os.makedirs(actual_output_dir, exist_ok=True)
            
            # Prepare output file paths
            curl_file = os.path.join(actual_output_dir, "commands.sh")
            postman_file = os.path.join(actual_output_dir, "postman-collection.json")
            
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
            
            # Guardar metadatos y summary si usamos estructura automática
            if output_path:
                execution_time = (datetime.now() - execution_start).total_seconds()
                metadata['execution_time_seconds'] = execution_time
                metadata['summary']['files_generated'] = 2
                
                OutputManager.save_metadata(output_path, metadata)
                OutputManager.save_summary(output_path, result.get_summary())
            
            return {
                "success": True,
                "data": {
                    "total_commands": result.total_commands,
                    "base_url": result.base_url,
                    "curl_file": curl_path,
                    "postman_file": postman_path,
                    "collection_name": result.postman_collection.name,
                    "summary": result.get_summary(),
                    "output_directory": str(output_path) if output_path else actual_output_dir
                },
                "message": f"Successfully generated {result.total_commands} cURL commands and Postman collection"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate cURL commands"
            }
    
    async def parse_curl_to_tests(self, curl_command: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Tool 5: Parse cURL and generate tests using EXISTING generators.
        
        This method:
        1. Parses the cURL command
        2. Converts to swagger-compatible format using dedicated mapper
        3. REUSES feature_generator (without modification)
        4. REUSES jmeter_generator (without modification)
        
        Args:
            curl_command: Raw cURL command string
            output_dir: Output directory for generated files (optional, auto-generated if None)
            
        Returns:
            Generation results
        """
        try:
            execution_start = datetime.now()
            
            # Step 1: Parse cURL
            parse_result = await self.curl_parser_service.parse_curl(curl_command)
            
            # Step 2: Convert to swagger-compatible format using mapper
            swagger_data = self.curl_parser_service.convert_to_swagger(parse_result)
            
            # Determinar output directory
            if OutputManager.should_use_auto_structure(output_dir):
                # Usar OutputManager para estructura automática
                identifier = OutputManager.extract_identifier_from_curl(curl_command)
                output_path = OutputManager.create_output_directory(
                    'curl_parser',
                    identifier,
                    execution_start
                )
                actual_output_dir = str(output_path)
            else:
                # Respetar directorio manual
                actual_output_dir = output_dir
                output_path = None
                os.makedirs(actual_output_dir, exist_ok=True)
            
            # Step 3: Generate features using EXISTING generator (con subdirectorio)
            features_dir = os.path.join(actual_output_dir, "features")
            features_result = await self.generate_features_from_swagger(
                swagger_data, 
                features_dir, 
                use_auto_structure=False  # Evitar duplicación: ya tenemos estructura base
            )
            
            # Step 4: Generate JMeter using EXISTING generator (con subdirectorio)
            jmeter_dir = os.path.join(actual_output_dir, "jmeter")
            os.makedirs(jmeter_dir, exist_ok=True)
            jmx_file = os.path.join(jmeter_dir, "test-plan.jmx")
            jmeter_result = await self.generate_jmeter_from_swagger(
                swagger_data, 
                jmx_file, 
                use_auto_structure=False  # Evitar duplicación: ya tenemos estructura base
            )
            
            return {
                "success": True,
                "data": {
                    "parsed_curl": parse_result.get_summary(),
                    "swagger_data": swagger_data,
                    "features_generation": features_result.get("data") if features_result.get("success") else None,
                    "jmeter_generation": jmeter_result.get("data") if jmeter_result.get("success") else None,
                    "output_directory": str(output_path) if output_path else actual_output_dir
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
        output_dir: str = None,
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
            output_dir: Directory to create the project (optional, auto-generated if None)
            config: Optional project configuration
            
        Returns:
            Complete project generation result
        """
        try:
            execution_start = datetime.now()
            
            # Validate inputs
            if not swagger_url and not curl_command:
                raise ValueError("Either swagger_url or curl_command must be provided")
            
            # Step 1: Get swagger data
            if swagger_url:
                swagger_result = await self.analyze_swagger_from_url(swagger_url)
                if not swagger_result["success"]:
                    return swagger_result
                swagger_data = swagger_result["data"]
                source_identifier = OutputManager.extract_identifier_from_swagger(swagger_data)
            else:
                # Parse cURL and convert to swagger format
                parse_result = await self.curl_parser_service.parse_curl(curl_command)
                swagger_data = self.curl_parser_service.convert_to_swagger(parse_result)
                source_identifier = OutputManager.extract_identifier_from_curl(curl_command)
            
            # Determinar output directory
            if OutputManager.should_use_auto_structure(output_dir):
                # Usar OutputManager para estructura automática
                output_path = OutputManager.create_output_directory(
                    'karate_project',
                    source_identifier,
                    execution_start
                )
                actual_output_dir = str(output_path)
                
                # Guardar metadatos
                metadata = {
                    'output_type': 'karate_project',
                    'source': {
                        'type': 'swagger' if swagger_url else 'curl',
                        'url': swagger_url if swagger_url else None,
                        'command': curl_command[:200] + '...' if curl_command and len(curl_command) > 200 else curl_command,
                        'title': swagger_data.get('title', 'Unknown')
                    },
                    'execution_time_seconds': None
                }
            else:
                # Respetar directorio manual
                actual_output_dir = output_dir
                output_path = None
            
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
                output_dir=actual_output_dir,
                config=config
            )
            
            # Get project summary
            summary = self.karate_java_service.get_project_summary(project)
            
            # Guardar metadatos y summary si usamos estructura automática
            if output_path:
                execution_time = (datetime.now() - execution_start).total_seconds()
                metadata['execution_time_seconds'] = execution_time
                metadata['summary'] = summary
                
                OutputManager.save_metadata(output_path, metadata)
            
            return {
                "success": True,
                "data": {
                    "project_path": str(output_path) if output_path else actual_output_dir,
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
                "message": f"Successfully generated Karate Java project at {str(output_path) if output_path else actual_output_dir}"
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "message": f"Failed to generate Karate Java project: {str(e)}"
            }
    
    async def complete_workflow(self, swagger_url: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Complete workflow: Swagger -> Features -> JMeter -> cURL.
        
        Args:
            swagger_url: URL to the swagger/OpenAPI specification
            output_dir: Directory to save all output files (optional, auto-generated if None)
            
        Returns:
            Complete workflow result with all generated artifacts
        """
        try:
            execution_start = datetime.now()
            
            # Step 1: Analyze swagger
            swagger_result = await self.analyze_swagger_from_url(swagger_url)
            if not swagger_result["success"]:
                return swagger_result
            
            swagger_data = swagger_result["data"]
            
            # Determinar output directory
            if OutputManager.should_use_auto_structure(output_dir):
                # Usar OutputManager para estructura de workflow completo
                identifier = OutputManager.extract_identifier_from_swagger(swagger_data)
                workflow_paths = OutputManager.create_workflow_structure(
                    identifier,
                    execution_start
                )
                actual_output_dir = str(workflow_paths['base'])
                
                # Guardar metadatos principales
                metadata = {
                    'output_type': 'complete_workflow',
                    'source': {
                        'type': 'swagger',
                        'url': swagger_url,
                        'title': swagger_data.get('title', 'Unknown'),
                        'base_urls': swagger_data.get('base_urls', [])
                    },
                    'execution_time_seconds': None,
                    'summary': {}
                }
                
                # Guardar análisis de swagger
                swagger_file = workflow_paths['swagger_analysis'] / "swagger-analysis.json"
                with open(swagger_file, 'w', encoding='utf-8') as f:
                    json.dump(swagger_data, f, indent=2)
            else:
                # Respetar directorio manual
                actual_output_dir = output_dir
                workflow_paths = None
                os.makedirs(actual_output_dir, exist_ok=True)
            
            # Step 2: Generate features (sin auto-structure para evitar duplicación)
            features_dir = str(workflow_paths['features']) if workflow_paths else os.path.join(actual_output_dir, "features")
            features_result = await self.generate_features_from_swagger(swagger_data, features_dir, use_auto_structure=False)
            if not features_result["success"]:
                return features_result
            
            features_data = features_result["data"]
            
            # Step 3: Generate JMeter from swagger (sin auto-structure para evitar duplicación)
            jmx_dir = str(workflow_paths['jmeter']) if workflow_paths else os.path.join(actual_output_dir, "jmeter")
            os.makedirs(jmx_dir, exist_ok=True)
            jmx_file = os.path.join(jmx_dir, "test-plan.jmx")
            jmeter_result = await self.generate_jmeter_from_swagger(swagger_data, jmx_file, use_auto_structure=False)
            
            # Step 4: Generate cURL commands and Postman collection (sin auto-structure para evitar duplicación)
            curl_dir = str(workflow_paths['curl']) if workflow_paths else os.path.join(actual_output_dir, "curl")
            curl_result = await self.generate_curl_from_swagger(swagger_data, curl_dir, use_auto_structure=False)
            
            # Guardar metadatos y summary si usamos estructura automática
            if workflow_paths:
                execution_time = (datetime.now() - execution_start).total_seconds()
                metadata['execution_time_seconds'] = execution_time
                metadata['summary'] = {
                    'swagger_analyzed': True,
                    'features_generated': features_result["success"],
                    'total_features': len(features_data.get('features', [])),
                    'jmeter_generated': jmeter_result["success"],
                    'curl_generated': curl_result["success"]
                }
                
                OutputManager.save_metadata(workflow_paths['base'], metadata)
            
            return {
                "success": True,
                "data": {
                    "swagger_analysis": swagger_data,
                    "features_generation": features_data,
                    "jmeter_generation": jmeter_result["data"] if jmeter_result["success"] else None,
                    "curl_generation": curl_result["data"] if curl_result["success"] else None,
                    "output_directory": actual_output_dir
                },
                "message": "Complete workflow executed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute complete workflow"
            }
    
    async def execute_database_query(
        self,
        query: str,
        db_type: str,
        connection_string: str = None,
        host: str = None,
        port: int = None,
        database: str = None,
        username: str = None,
        password: str = None,
        timeout: int = 30,
        max_rows: int = 1000,
        output_format: str = "json",
        include_metadata: bool = True,
        output_file: str = None
    ) -> Dict[str, Any]:
        """
        Tool 8: Execute database query with validation and result formatting.
        
        Args:
            query: SQL query to execute (read-only operations only)
            db_type: Database type (postgres, mysql, sqlserver, sqlite)
            connection_string: Full connection string (alternative to individual params)
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            timeout: Query timeout in seconds (default: 30)
            max_rows: Maximum number of rows to return (default: 1000)
            output_format: Output format (json, csv, markdown, table)
            include_metadata: Include validation and connection metadata
            output_file: Optional file path to save results
            
        Returns:
            Dictionary with query results or error details
        """
        try:
            # Validate db_type
            try:
                database_type = DatabaseType[db_type.upper()]
            except KeyError:
                return {
                    "success": False,
                    "error": f"Invalid database type: {db_type}",
                    "supported_types": DatabaseQueryService().get_supported_databases()
                }
            
            # Build connection configuration
            connection = DatabaseConnection(
                db_type=database_type,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
                connection_string=connection_string
            )
            
            # Build query request
            request = QueryRequest(
                query=query,
                connection=connection,
                timeout=timeout,
                max_rows=max_rows,
                output_format=output_format,
                include_metadata=include_metadata
            )
            
            # Execute query with optional file output
            if output_file:
                result = await self.database_query_service.execute_query_with_output_file(
                    request=request,
                    output_file=output_file
                )
            else:
                result = await self.database_query_service.execute_query(request=request)
            
            return result
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid request parameters: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute database query: {str(e)}"
            }
    
    async def validate_database_query(
        self,
        query: str,
        db_type: str
    ) -> Dict[str, Any]:
        """
        Tool 9: Validate database query without executing it.
        
        Args:
            query: SQL query to validate
            db_type: Database type (postgres, mysql, sqlserver, sqlite)
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Validate db_type
            try:
                database_type = DatabaseType[db_type.upper()]
            except KeyError:
                return {
                    "success": False,
                    "error": f"Invalid database type: {db_type}",
                    "supported_types": DatabaseQueryService().get_supported_databases()
                }
            
            # Create minimal connection (not used for validation)
            connection = DatabaseConnection(
                db_type=database_type,
                connection_string="dummy://localhost"
            )
            
            # Validate query only
            result = await self.database_query_service.validate_query_only(
                connection=connection,
                query=query
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to validate query: {str(e)}"
            }
    
    async def test_database_connection(
        self,
        db_type: str,
        connection_string: str = None,
        host: str = None,
        port: int = None,
        database: str = None,
        username: str = None,
        password: str = None
    ) -> Dict[str, Any]:
        """
        Tool 10: Test database connection without executing queries.
        
        Args:
            db_type: Database type (postgres, mysql, sqlserver, sqlite)
            connection_string: Full connection string (alternative to individual params)
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            
        Returns:
            Dictionary with connection test results
        """
        try:
            # Validate db_type
            try:
                database_type = DatabaseType[db_type.upper()]
            except KeyError:
                return {
                    "success": False,
                    "error": f"Invalid database type: {db_type}",
                    "supported_types": DatabaseQueryService().get_supported_databases()
                }
            
            # Build connection configuration
            connection = DatabaseConnection(
                db_type=database_type,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
                connection_string=connection_string
            )
            
            # Test connection
            result = await self.database_query_service.test_connection_only(connection)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to test connection: {str(e)}"
            }
    
    def get_supported_databases(self) -> Dict[str, Any]:
        """
        Tool 11: Get list of supported database types.
        
        Returns:
            Dictionary with supported databases
        """
        return self.database_query_service.get_supported_databases()
