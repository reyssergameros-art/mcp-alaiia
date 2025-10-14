"""Infrastructure implementation for swagger analysis."""
import httpx
import json
from typing import Dict, Any, List, Optional
from ..domain.repositories import SwaggerRepository
from ..domain.models import (
    SwaggerAnalysisResult, EndpointInfo, FieldInfo, ResponseInfo, FieldFormat
)

# Simple YAML parser for basic OpenAPI specs (without external dependency)
def simple_yaml_load(text: str) -> Dict[str, Any]:
    """Simple YAML parser for basic OpenAPI specifications."""
    # This is a very basic YAML parser for demonstration
    # In production, you should use a proper YAML library
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        # Fallback: Try to parse as JSON or return empty dict
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Very basic YAML-to-JSON conversion for simple cases
            lines = text.split('\n')
            result = {}
            current_key = None
            
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    result[key] = value
            
            return result


class HttpSwaggerRepository(SwaggerRepository):
    """HTTP implementation of swagger repository."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def fetch_swagger_spec(self, url: str) -> Dict[str, Any]:
        """Fetch swagger specification from URL or file path."""
        
        # Check if it's a local file path
        if url.startswith('file://') or (not url.startswith('http://') and not url.startswith('https://')):
            # Handle local file
            import os
            file_path = url.replace('file://', '') if url.startswith('file://') else url
            
            if not os.path.isabs(file_path):
                # If relative path, make it absolute
                file_path = os.path.abspath(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to parse as JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try simple YAML parsing
                return simple_yaml_load(content)
        
        # Handle remote URL
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                return response.json()
            elif 'application/yaml' in content_type or 'text/yaml' in content_type:
                return simple_yaml_load(response.text)
            else:
                # Try to parse as JSON first, then YAML
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return simple_yaml_load(response.text)
    
    async def parse_swagger_spec(self, spec: Dict[str, Any]) -> SwaggerAnalysisResult:
        """Parse swagger specification into analysis result."""
        # Extract basic info
        info = spec.get('info', {})
        title = info.get('title')
        version = info.get('version')
        description = info.get('description')
        contact_info = info.get('contact', {})
        license_info = info.get('license', {})
        
        # Extract base URLs
        base_urls = self._extract_base_urls(spec)
        
        # Extract endpoints
        endpoints = self._extract_endpoints(spec)
        
        return SwaggerAnalysisResult(
            title=title,
            version=version,
            description=description,
            contact_info=contact_info,
            license_info=license_info,
            base_urls=base_urls,
            total_endpoints=len(endpoints),
            endpoints=endpoints
        )
    
    def _extract_base_urls(self, spec: Dict[str, Any]) -> List[str]:
        """Extract base URLs from swagger spec."""
        base_urls = []
        
        # OpenAPI 3.x
        if 'servers' in spec:
            for server in spec['servers']:
                base_urls.append(server.get('url', ''))
        
        # Swagger 2.0
        elif 'host' in spec:
            schemes = spec.get('schemes', ['http'])
            host = spec['host']
            base_path = spec.get('basePath', '')
            
            for scheme in schemes:
                base_urls.append(f"{scheme}://{host}{base_path}")
        
        return base_urls
    
    def _extract_endpoints(self, spec: Dict[str, Any]) -> List[EndpointInfo]:
        """Extract all endpoints from swagger spec."""
        endpoints = []
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            if isinstance(path_item, dict):
                for method, operation in path_item.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                        endpoint = self._parse_endpoint(path, method, operation, spec)
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_endpoint(self, path: str, method: str, operation: Dict[str, Any], spec: Dict[str, Any]) -> EndpointInfo:
        """Parse a single endpoint operation."""
        endpoint = EndpointInfo(
            method=method.upper(),
            path=path,
            summary=operation.get('summary'),
            description=operation.get('description'),
            operation_id=operation.get('operationId'),
            tags=operation.get('tags', [])
        )
        
        # Parse parameters
        parameters = operation.get('parameters', [])
        for param in parameters:
            field_info = self._parse_parameter(param, spec)
            
            if param.get('in') == 'header':
                endpoint.headers.append(field_info)
            elif param.get('in') == 'path':
                endpoint.path_parameters.append(field_info)
            elif param.get('in') == 'query':
                endpoint.query_parameters.append(field_info)
        
        # Parse request body (OpenAPI 3.x)
        if 'requestBody' in operation:
            endpoint.request_body, endpoint.request_content_type = self._parse_request_body(
                operation['requestBody'], spec
            )
        
        # Parse responses
        responses = operation.get('responses', {})
        for status_code, response_spec in responses.items():
            response_info = self._parse_response(status_code, response_spec, spec)
            endpoint.responses.append(response_info)
        
        return endpoint
    
    def _parse_parameter(self, param: Dict[str, Any], spec: Dict[str, Any]) -> FieldInfo:
        """Parse a parameter into FieldInfo."""
        name = param.get('name', '')
        required = param.get('required', False)
        description = param.get('description')
        
        # Handle schema (OpenAPI 3.x) or direct type (Swagger 2.0)
        if 'schema' in param:
            schema = param['schema']
        else:
            schema = param
        
        data_type = schema.get('type', 'string')
        format_str = schema.get('format', '')
        field_format = self._parse_format(data_type, format_str)
        
        return FieldInfo(
            name=name,
            data_type=data_type,
            required=required,
            format=field_format,
            description=description,
            example=schema.get('example'),
            enum_values=schema.get('enum'),
            pattern=schema.get('pattern'),
            minimum=schema.get('minimum'),
            maximum=schema.get('maximum')
        )
    
    def _parse_request_body(self, request_body: Dict[str, Any], spec: Dict[str, Any]) -> tuple:
        """Parse request body into field info dictionary."""
        content = request_body.get('content', {})
        
        for content_type, content_spec in content.items():
            schema = content_spec.get('schema', {})
            fields = self._parse_schema_properties(schema, spec)
            return fields, content_type
        
        return None, None
    
    def _parse_schema_properties(self, schema: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, FieldInfo]:
        """Parse schema properties into field info dictionary."""
        fields = {}
        
        # Resolve $ref if present
        if '$ref' in schema:
            schema = self._resolve_ref(schema['$ref'], spec)
        
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        for field_name, field_schema in properties.items():
            # Resolve nested $ref
            if '$ref' in field_schema:
                field_schema = self._resolve_ref(field_schema['$ref'], spec)
            
            data_type = field_schema.get('type', 'string')
            format_str = field_schema.get('format', '')
            field_format = self._parse_format(data_type, format_str)
            
            fields[field_name] = FieldInfo(
                name=field_name,
                data_type=data_type,
                required=field_name in required_fields,
                format=field_format,
                description=field_schema.get('description'),
                example=field_schema.get('example'),
                enum_values=field_schema.get('enum'),
                pattern=field_schema.get('pattern'),
                minimum=field_schema.get('minimum'),
                maximum=field_schema.get('maximum')
            )
        
        return fields
    
    def _parse_response(self, status_code: str, response_spec: Dict[str, Any], spec: Dict[str, Any]) -> ResponseInfo:
        """Parse a response specification."""
        description = response_spec.get('description', '')
        
        # Parse content (OpenAPI 3.x)
        content = response_spec.get('content', {})
        content_type = None
        schema = None
        example = None
        
        for ct, ct_spec in content.items():
            content_type = ct
            schema = ct_spec.get('schema', {})
            example = ct_spec.get('example') or schema.get('example')
            break  # Take the first content type
        
        # Fallback for Swagger 2.0
        if not content_type and 'schema' in response_spec:
            schema = response_spec['schema']
            example = response_spec.get('examples')
        
        return ResponseInfo(
            status_code=status_code,
            description=description,
            content_type=content_type,
            schema=schema,
            example=example
        )
    
    def _resolve_ref(self, ref: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a $ref reference."""
        if not ref.startswith('#/'):
            return {}
        
        path_parts = ref[2:].split('/')
        current = spec
        
        try:
            for part in path_parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return {}
    
    def _parse_format(self, data_type: str, format_str: str) -> FieldFormat:
        """Parse data type and format into FieldFormat enum."""
        format_mapping = {
            'uuid': FieldFormat.UUID,
            'date': FieldFormat.DATE,
            'date-time': FieldFormat.DATETIME,
            'email': FieldFormat.EMAIL,
            'password': FieldFormat.PASSWORD,
            'uri': FieldFormat.URI,
            'ipv4': FieldFormat.IPV4,
            'ipv6': FieldFormat.IPV6,
            'binary': FieldFormat.BINARY,
            'byte': FieldFormat.BYTE,
            'int32': FieldFormat.INT32,
            'int64': FieldFormat.INT64,
            'float': FieldFormat.FLOAT,
            'double': FieldFormat.DOUBLE
        }
        
        # Check format first
        if format_str.lower() in format_mapping:
            return format_mapping[format_str.lower()]
        
        # Check for common patterns in field names or descriptions
        if 'phone' in format_str.lower() or 'mobile' in format_str.lower() or 'cell' in format_str.lower():
            return FieldFormat.PHONE
        
        return FieldFormat.NONE