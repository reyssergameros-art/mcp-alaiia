"""
Application-level mapper for converting cURL parse results to swagger format.
Following SRP: Only handles cURL -> Swagger conversion.
"""

import json
import re
from typing import Dict, Any, List
from ..domain.models import CurlParseResult
from src.shared.mappers import SwaggerDataMapper


class CurlToSwaggerMapper:
    """
    Maps parsed cURL data to swagger-compatible format.
    
    This enables reuse of existing feature_generator and jmeter_generator
    without modifying them (OCP).
    
    Following SOLID:
    - SRP: Only converts cURL to swagger format
    - OCP: Doesn't modify existing generators
    - DIP: Uses shared SwaggerDataMapper
    """
    
    def __init__(self):
        """Initialize mapper."""
        self.swagger_mapper = SwaggerDataMapper()
    
    def map_to_swagger(self, parse_result: CurlParseResult) -> Dict[str, Any]:
        """
        Convert parsed cURL to swagger-compatible format.
        
        Args:
            parse_result: CurlParseResult from parser
            
        Returns:
            Swagger-compatible data structure
        """
        parsed_request = parse_result.parsed_request
        
        # Extract URL components
        base_url = parsed_request.get_base_url()
        path = parsed_request.get_path()
        method = parsed_request.method
        
        # Build headers using shared mapper
        headers_list = []
        for header in parsed_request.headers:
            header_dict = self.swagger_mapper.create_field_dict(
                name=header.name,
                data_type="string",
                required=True,
                example=header.value,
                description="Header from cURL"
            )
            headers_list.append(header_dict)
        
        # Build request body if present
        request_body_dict = None
        if parsed_request.body:
            request_body_dict = self._parse_body_to_swagger_format(
                parsed_request.body
            )
        
        # Detect path parameters (e.g., /users/{id})
        path_parameters = self._extract_path_parameters(path)
        
        # Build endpoint using shared mapper
        endpoint = self.swagger_mapper.create_endpoint_dict(
            method=method,
            path=path,
            summary=f"{method} request to {path}",
            description="Generated from cURL command",
            headers=headers_list,
            path_parameters=path_parameters,
            query_parameters=[],
            request_body=request_body_dict,
            responses=[
                self.swagger_mapper.create_response_dict(
                    status_code="200",
                    description="Successful response",
                    content_type="*/*"
                )
            ]
        )
        
        # Generate API title from path
        api_title = self._generate_title_from_path(path, method)
        
        # Return swagger-compatible structure
        return {
            "title": api_title,
            "version": "1.0.0",
            "description": "API generated from cURL command",
            "base_urls": [base_url],
            "total_endpoints": 1,
            "endpoints": [endpoint]
        }
    
    def _parse_body_to_swagger_format(self, body_str: str) -> Dict[str, Any]:
        """Convert request body to swagger field format."""
        result = {}
        
        try:
            # Try to parse as JSON
            body_data = json.loads(body_str)
            
            if isinstance(body_data, dict):
                for field_name, field_value in body_data.items():
                    result[field_name] = self.swagger_mapper.create_field_dict(
                        name=field_name,
                        data_type=self.swagger_mapper.infer_type_from_value(field_value),
                        required=True,
                        example=field_value,
                        description="Field from cURL body"
                    )
        except (json.JSONDecodeError, TypeError):
            # Not JSON, treat as raw
            result["raw_body"] = self.swagger_mapper.create_field_dict(
                name="raw_body",
                data_type="string",
                required=True,
                example=body_str,
                description="Raw body data"
            )
        
        return result
    
    def _extract_path_parameters(self, path: str) -> List[Dict[str, Any]]:
        """Extract path parameters like {id} or :id from path."""
        path_params = []
        
        # Match {param} or :param patterns
        patterns = [
            r'\{([^}]+)\}',  # {id}
            r':([a-zA-Z_][a-zA-Z0-9_]*)'  # :id
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, path)
            for match in matches:
                if match not in [p['name'] for p in path_params]:
                    param_dict = self.swagger_mapper.create_field_dict(
                        name=match,
                        data_type="string",
                        required=True,
                        example=f"<{match}>",
                        description="Path parameter"
                    )
                    path_params.append(param_dict)
        
        return path_params
    
    def _generate_title_from_path(self, path: str, method: str) -> str:
        """Generate API title from path."""
        # Extract first meaningful part of path
        parts = [p for p in path.split('/') if p and not p.startswith('{') and not p.startswith(':')]
        
        if parts:
            resource = parts[0].replace('_', ' ').replace('-', ' ').title()
            return f"{resource} API (from cURL)"
        
        return f"{method} API (from cURL)"
