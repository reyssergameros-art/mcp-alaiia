"""Infrastructure implementation for feature generation."""
import os
import re
from typing import Dict, Any, List
from ..domain.repositories import FeatureRepository
from ..domain.models import FeatureGenerationResult, FeatureFile, FeatureScenario


class KarateFeatureRepository(FeatureRepository):
    """Karate DSL implementation of feature repository."""
    
    async def generate_features_from_swagger(self, swagger_data: Dict[str, Any]) -> FeatureGenerationResult:
        """Generate Karate DSL feature files from swagger analysis result."""
        
        base_urls = swagger_data.get('base_urls', [''])
        base_url = base_urls[0] if base_urls else ''
        endpoints = swagger_data.get('endpoints', [])
        
        features = []
        total_scenarios = 0
        
        # Group endpoints by tags or create one feature per endpoint
        grouped_endpoints = self._group_endpoints_by_tag(endpoints)
        
        for group_name, group_endpoints in grouped_endpoints.items():
            feature = self._create_feature_for_endpoints(group_name, group_endpoints, base_url)
            features.append(feature)
            total_scenarios += len(feature.scenarios)
        
        return FeatureGenerationResult(
            features=features,
            base_url=base_url,
            total_scenarios=total_scenarios
        )
    
    async def save_feature_files(self, features: List[FeatureFile], output_dir: str) -> List[str]:
        """Save feature files to disk."""
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        for feature in features:
            # Create filename from feature name
            filename = self._sanitize_filename(feature.feature_name) + '.feature'
            file_path = os.path.join(output_dir, filename)
            
            # Generate feature content
            content = self._generate_karate_feature_content(feature)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files.append(file_path)
        
        return saved_files
    
    def _group_endpoints_by_tag(self, endpoints: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group endpoints by their tags."""
        grouped = {}
        
        for endpoint in endpoints:
            tags = endpoint.get('tags', [])
            
            if not tags:
                # If no tags, use the first part of the path as group
                path = endpoint.get('path', '')
                tag = self._extract_tag_from_path(path)
            else:
                tag = tags[0]  # Use first tag
            
            if tag not in grouped:
                grouped[tag] = []
            grouped[tag].append(endpoint)
        
        return grouped
    
    def _extract_tag_from_path(self, path: str) -> str:
        """Extract a tag from the path."""
        parts = path.strip('/').split('/')
        if parts and parts[0]:
            return parts[0].replace('{', '').replace('}', '')
        return 'api'
    
    def _create_feature_for_endpoints(self, group_name: str, endpoints: List[Dict[str, Any]], base_url: str) -> FeatureFile:
        """Create a feature file for a group of endpoints."""
        feature_name = f"{group_name.title()} API Tests"
        description = f"API tests for {group_name} endpoints"
        
        # Background steps common to all scenarios
        background_steps = [
            f"url '{base_url}'",
            "header Content-Type = 'application/json'",
            "header Accept = 'application/json'"
        ]
        
        scenarios = []
        
        for endpoint in endpoints:
            scenarios.extend(self._create_scenarios_for_endpoint(endpoint))
        
        return FeatureFile(
            feature_name=feature_name,
            description=description,
            background_steps=background_steps,
            scenarios=scenarios,
            tags=[group_name.lower(), 'api']
        )
    
    def _create_scenarios_for_endpoint(self, endpoint: Dict[str, Any]) -> List[FeatureScenario]:
        """Create test scenarios for a single endpoint."""
        scenarios = []
        
        method = endpoint.get('method', 'GET').lower()
        path = endpoint.get('path', '')
        summary = endpoint.get('summary', '')
        
        # Main success scenario
        scenario_name = f"{method.upper()} {path}"
        if summary:
            scenario_name += f" - {summary}"
        
        given_steps = []
        when_steps = []
        then_steps = []
        
        # Add path parameters if any
        path_params = endpoint.get('path_parameters', [])
        if path_params:
            for param in path_params:
                given_steps.append(f"def {param['name']} = '{self._get_example_value(param)}'")
        
        # Add query parameters if any
        query_params = endpoint.get('query_parameters', [])
        if query_params:
            param_assignments = []
            for param in query_params:
                param_assignments.append(f"'{param['name']}': '{self._get_example_value(param)}'")
            given_steps.append(f"def queryParams = {{{', '.join(param_assignments)}}}")
        
        # Add headers if any
        headers = endpoint.get('headers', [])
        if headers:
            for header in headers:
                given_steps.append(f"header {header['name']} = '{self._get_example_value(header)}'")
        
        # Add request body if any
        request_body = endpoint.get('request_body')
        if request_body and method in ['post', 'put', 'patch']:
            body_example = self._generate_request_body_example(request_body)
            given_steps.append(f"def requestBody = {body_example}")
            when_steps.append(f"request requestBody")
        
        # When step - make the request
        path_with_params = self._replace_path_parameters(path, path_params)
        
        # Build the method call
        if query_params:
            when_steps.append("params queryParams")
        
        when_steps.append(f"method {method} '{path_with_params}'")
        
        # Then steps - verify response
        responses = endpoint.get('responses', [])
        success_responses = [r for r in responses if r['status_code'].startswith('2')]
        
        if success_responses:
            status_code = success_responses[0]['status_code']
            then_steps.append(f"status {status_code}")
            
            # Add response validation if schema is available
            response_schema = success_responses[0].get('schema')
            if response_schema:
                then_steps.extend(self._generate_response_validation(response_schema))
        else:
            then_steps.append("status 200")
        
        scenarios.append(FeatureScenario(
            name=scenario_name,
            description=endpoint.get('description'),
            given_steps=given_steps,
            when_steps=when_steps,
            then_steps=then_steps
        ))
        
        # Add error scenarios for each error response
        for response in responses:
            if not response['status_code'].startswith('2'):
                error_scenario = self._create_error_scenario(endpoint, response)
                scenarios.append(error_scenario)
        
        return scenarios
    
    def _create_error_scenario(self, endpoint: Dict[str, Any], error_response: Dict[str, Any]) -> FeatureScenario:
        """Create an error scenario for an endpoint."""
        method = endpoint.get('method', 'GET').upper()
        path = endpoint.get('path', '')
        status_code = error_response['status_code']
        description = error_response.get('description', 'Error case')
        
        scenario_name = f"{method} {path} - {status_code} Error"
        
        # For error scenarios, we might need invalid data
        given_steps = ["def invalidData = 'invalid'"]
        when_steps = [f"method {method.lower()} '{path}'"]
        then_steps = [f"status {status_code}"]
        
        return FeatureScenario(
            name=scenario_name,
            description=description,
            given_steps=given_steps,
            when_steps=when_steps,
            then_steps=then_steps
        )
    
    def _get_example_value(self, field: Dict[str, Any]) -> str:
        """Get an example value for a field."""
        if 'example' in field and field['example'] is not None:
            return str(field['example'])
        
        data_type = field.get('data_type', 'string')
        field_format = field.get('format', {})
        
        # Get format value if it's a dict
        if isinstance(field_format, dict):
            format_name = field_format.get('value', 'none')
        else:
            format_name = str(field_format).lower()
        
        # Generate example based on type and format
        if data_type == 'string':
            if 'email' in format_name:
                return 'test@example.com'
            elif 'uuid' in format_name:
                return '123e4567-e89b-12d3-a456-426614174000'
            elif 'date' in format_name:
                return '2023-12-01'
            elif 'phone' in format_name:
                return '+1234567890'
            else:
                return 'example_value'
        elif data_type == 'integer':
            return '123'
        elif data_type == 'number':
            return '123.45'
        elif data_type == 'boolean':
            return 'true'
        else:
            return 'example_value'
    
    def _generate_request_body_example(self, request_body: Dict[str, Any]) -> str:
        """Generate an example request body for Karate."""
        if not request_body:
            return '{}'
        
        example_obj = {}
        for field_name, field_info in request_body.items():
            example_value = self._get_example_value(field_info)
            
            # Convert to appropriate type for Karate
            data_type = field_info.get('data_type', 'string')
            if data_type == 'integer':
                try:
                    example_obj[field_name] = int(example_value)
                except:
                    example_obj[field_name] = 123
            elif data_type == 'number':
                try:
                    example_obj[field_name] = float(example_value)
                except:
                    example_obj[field_name] = 123.45
            elif data_type == 'boolean':
                example_obj[field_name] = example_value.lower() == 'true' if isinstance(example_value, str) else bool(example_value)
            else:
                example_obj[field_name] = str(example_value)
        
        # Format as Karate object
        import json
        return json.dumps(example_obj)
    
    def _replace_path_parameters(self, path: str, path_params: List[Dict[str, Any]]) -> str:
        """Replace path parameters with variable references."""
        result_path = path
        for param in path_params:
            param_name = param['name']
            result_path = result_path.replace(f'{{{param_name}}}', f'#{{{param_name}}}')
        return result_path
    
    def _generate_response_validation(self, schema: Dict[str, Any]) -> List[str]:
        """Generate response validation steps."""
        validations = []
        
        if schema.get('type') == 'object':
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            for prop_name in required:
                validations.append(f"match response.{prop_name} == '#present'")
        
        return validations
    
    def _generate_karate_feature_content(self, feature: FeatureFile) -> str:
        """Generate the actual Karate feature file content."""
        content_lines = []
        
        # Add tags if any
        if feature.tags:
            content_lines.append(f"@{' @'.join(feature.tags)}")
        
        # Add feature header
        content_lines.append(f"Feature: {feature.feature_name}")
        
        if feature.description:
            content_lines.append("")
            content_lines.append(f"  {feature.description}")
        
        content_lines.append("")
        
        # Add background if any
        if feature.background_steps:
            content_lines.append("  Background:")
            for step in feature.background_steps:
                content_lines.append(f"    * {step}")
            content_lines.append("")
        
        # Add scenarios
        for scenario in feature.scenarios:
            if scenario.description:
                content_lines.append(f"  # {scenario.description}")
            
            content_lines.append(f"  Scenario: {scenario.name}")
            
            # All steps with proper Karate syntax
            all_steps = []
            
            # Given steps
            all_steps.extend(scenario.given_steps)
            
            # When steps
            all_steps.extend(scenario.when_steps)
            
            # Then steps
            all_steps.extend(scenario.then_steps)
            
            # Write all steps with * prefix
            for step in all_steps:
                content_lines.append(f"    * {step}")
            
            content_lines.append("")
        
        return "\n".join(content_lines)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized.lower()