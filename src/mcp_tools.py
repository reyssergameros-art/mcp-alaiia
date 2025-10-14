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


class MCPToolsOrchestrator:
    """Orchestrator for all MCP tools that coordinates their interactions."""
    
    def __init__(self):
        # Initialize repositories
        self.swagger_repo = HttpSwaggerRepository()
        self.feature_repo = KarateFeatureRepository()
        self.jmeter_repo = XmlJMeterRepository()
        
        # Initialize services
        self.swagger_service = SwaggerAnalysisService(self.swagger_repo)
        self.feature_service = FeatureGenerationService(self.feature_repo)
        self.jmeter_service = JMeterGenerationService(self.jmeter_repo)
    
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
            
            # Convert endpoints
            for endpoint in result.endpoints:
                endpoint_dict = {
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "summary": endpoint.summary,
                    "description": endpoint.description,
                    "operation_id": endpoint.operation_id,
                    "tags": endpoint.tags,
                    "headers": [self._field_info_to_dict(h) for h in endpoint.headers],
                    "path_parameters": [self._field_info_to_dict(p) for p in endpoint.path_parameters],
                    "query_parameters": [self._field_info_to_dict(q) for q in endpoint.query_parameters],
                    "request_body": {k: self._field_info_to_dict(v) for k, v in endpoint.request_body.items()} if endpoint.request_body else None,
                    "request_content_type": endpoint.request_content_type,
                    "responses": [self._response_info_to_dict(r) for r in endpoint.responses]
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
    
    async def complete_workflow(self, swagger_url: str, output_dir: str = "./output") -> Dict[str, Any]:
        """
        Complete workflow: Swagger -> Features -> JMeter.
        
        Args:
            swagger_url: URL to the swagger/OpenAPI specification
            output_dir: Directory to save all output files
            
        Returns:
            Complete workflow result
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
            
            return {
                "success": True,
                "data": {
                    "swagger_analysis": swagger_data,
                    "features_generation": features_data,
                    "jmeter_from_swagger": jmeter_swagger_result["data"] if jmeter_swagger_result["success"] else None,
                    "jmeter_from_features": jmeter_features_result["data"] if jmeter_features_result["success"] else None,
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
    
    def _field_info_to_dict(self, field_info) -> Dict[str, Any]:
        """Convert FieldInfo to dictionary."""
        return {
            "name": field_info.name,
            "data_type": field_info.data_type,
            "required": field_info.required,
            "format": field_info.format.value if hasattr(field_info.format, 'value') else str(field_info.format),
            "description": field_info.description,
            "example": field_info.example,
            "enum_values": field_info.enum_values,
            "pattern": field_info.pattern,
            "minimum": field_info.minimum,
            "maximum": field_info.maximum
        }
    
    def _response_info_to_dict(self, response_info) -> Dict[str, Any]:
        """Convert ResponseInfo to dictionary."""
        return {
            "status_code": response_info.status_code,
            "description": response_info.description,
            "content_type": response_info.content_type,
            "schema": response_info.schema,
            "example": response_info.example
        }


# CLI interface for testing
async def main():
    """Main function for CLI testing."""
    orchestrator = MCPToolsOrchestrator()
    
    # Example usage
    swagger_url = input("Enter Swagger URL (or press Enter for example): ").strip()
    if not swagger_url:
        swagger_url = "https://petstore.swagger.io/v2/swagger.json"
    
    output_dir = input("Enter output directory (or press Enter for './output'): ").strip()
    if not output_dir:
        output_dir = "./output"
    
    print("\n🚀 Starting complete workflow...")
    
    # Execute complete workflow
    result = await orchestrator.complete_workflow(swagger_url, output_dir)
    
    if result["success"]:
        print("✅ Workflow completed successfully!")
        print(f"📁 Output directory: {result['data']['output_directory']}")
        
        swagger_data = result["data"]["swagger_analysis"]
        print(f"📊 Swagger Analysis: {swagger_data['total_endpoints']} endpoints analyzed")
        
        features_data = result["data"]["features_generation"]
        print(f"🎯 Features Generated: {len(features_data['features'])} feature files with {features_data['total_scenarios']} scenarios")
        
        if result["data"]["jmeter_from_swagger"]:
            jmeter_swagger = result["data"]["jmeter_from_swagger"]
            print(f"⚡ JMeter from Swagger: {jmeter_swagger['total_thread_groups']} thread groups, {jmeter_swagger['total_requests']} requests")
        
        if result["data"]["jmeter_from_features"]:
            jmeter_features = result["data"]["jmeter_from_features"]
            print(f"⚡ JMeter from Features: {jmeter_features['total_thread_groups']} thread groups, {jmeter_features['total_requests']} requests")
    else:
        print(f"❌ Workflow failed: {result['message']}")
        if "error" in result:
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())