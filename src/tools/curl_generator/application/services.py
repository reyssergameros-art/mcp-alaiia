"""
Application service for cURL command generation.
Following the Application Service pattern and Single Responsibility Principle.
"""

from typing import Dict, List, Any
import json
from ..domain.models import (
    CurlCommand, 
    PostmanCollection, 
    PostmanItem, 
    PostmanRequest,
    CurlGenerationResult
)
from ..domain.repositories import CurlExportRepository
from ....shared.utils.field_filter import should_include_field_in_request


class CurlGenerationService:
    """
    Application service that orchestrates cURL command generation.
    
    This service contains the business logic for:
    - Transforming Swagger data into cURL commands
    - Building Postman collections
    - Coordinating with the repository for persistence
    
    Following:
    - Single Responsibility Principle: Only handles cURL generation logic
    - Dependency Inversion Principle: Depends on repository abstraction
    - Open/Closed Principle: Can be extended without modification
    """
    
    def __init__(self, repository: CurlExportRepository):
        """
        Initialize service with repository dependency.
        
        Args:
            repository: Implementation of CurlExportRepository interface
        """
        self.repository = repository
    
    async def generate_from_swagger(self, swagger_data: Dict[str, Any]) -> CurlGenerationResult:
        """
        Generate cURL commands and Postman collection from Swagger analysis data.
        
        This method implements the core business logic for transforming
        Swagger/OpenAPI specifications into executable cURL commands and
        importable Postman collections.
        
        Args:
            swagger_data: Swagger analysis result containing endpoints, headers, etc.
            
        Returns:
            CurlGenerationResult containing all generated artifacts
            
        Raises:
            ValueError: If swagger_data is invalid or missing required fields
        """
        # Validate input
        if not swagger_data or 'endpoints' not in swagger_data:
            raise ValueError("Invalid swagger_data: missing 'endpoints' field")
        
        curl_commands = []
        postman_items = []
        
        # Extract base URL
        base_urls = swagger_data.get('base_urls', ['http://localhost:8080'])
        base_url = base_urls[0] if base_urls else 'http://localhost:8080'
        
        # Process each endpoint
        for endpoint in swagger_data.get('endpoints', []):
            curl_cmd, postman_item = self._process_endpoint(endpoint, base_url)
            curl_commands.append(curl_cmd)
            postman_items.append(postman_item)
        
        # Create Postman collection
        collection = PostmanCollection(
            name=swagger_data.get('title', 'API Collection'),
            items=postman_items,
            base_url=base_url,
            description=swagger_data.get('description')
        )
        
        # Create result aggregate
        result = CurlGenerationResult(
            curl_commands=curl_commands,
            postman_collection=collection,
            total_commands=len(curl_commands),
            base_url=base_url
        )
        
        return result
    
    def _process_endpoint(self, endpoint: Dict[str, Any], base_url: str) -> tuple:
        """
        Process a single endpoint to create cURL command and Postman item.
        
        Args:
            endpoint: Endpoint data from Swagger analysis
            base_url: Base URL for the API
            
        Returns:
            Tuple of (CurlCommand, PostmanItem)
        """
        # Build full URL
        path = endpoint.get('path', '/')
        url = f"{base_url}{path}"
        
        # Replace path parameters with placeholders
        for param in endpoint.get('path_parameters', []):
            param_name = param.get('name', '')
            # Replace {param} with example or placeholder
            example = param.get('example', f'<{param_name}>')
            url = url.replace(f"{{{param_name}}}", str(example))
        
        # Collect headers
        headers = self._build_headers(endpoint)
        
        # Build request body
        body = self._build_request_body(endpoint, endpoint['method'])
        
        # Create cURL command
        curl_cmd = CurlCommand(
            name=f"{endpoint['method']} {endpoint['path']}",
            method=endpoint['method'],
            url=url,
            headers=headers,
            body=body,
            description=endpoint.get('summary')
        )
        
        # Create Postman item
        postman_item = self._create_postman_item(endpoint, url, headers, body)
        
        return curl_cmd, postman_item
    
    def _build_headers(self, endpoint: Dict[str, Any]) -> Dict[str, str]:
        """
        Build headers dictionary from endpoint data.
        
        Args:
            endpoint: Endpoint data from Swagger analysis
            
        Returns:
            Dictionary of header name to value
        """
        headers = {}
        
        # Add defined headers
        for header in endpoint.get('headers', []):
            header_name = header.get('name', '')
            header_value = header.get('example', 'value')
            headers[header_name] = str(header_value)
        
        # Add Content-Type if endpoint has request body
        if endpoint.get('request_body'):
            content_type = endpoint.get('request_content_type', 'application/json')
            headers['Content-Type'] = content_type
        
        return headers
    
    def _build_request_body(self, endpoint: Dict[str, Any], method: str = 'POST') -> str:
        """
        Build request body from endpoint data, filtering out read-only fields.
        
        Args:
            endpoint: Endpoint data from Swagger analysis
            method: HTTP method (POST, PUT, etc.)
            
        Returns:
            JSON string of request body or None if no body
        """
        request_body = endpoint.get('request_body')
        if not request_body:
            return None
        
        # Build body object with examples
        body_data = {}
        for field_name, field_info in request_body.items():
            # Apply field filter to exclude read-only/autogenerated fields
            if not should_include_field_in_request(field_info, method.upper()):
                continue
                
            # Use example if available, otherwise create placeholder
            if field_info.get('example') is not None:
                body_data[field_name] = field_info['example']
            else:
                # Create placeholder based on type
                data_type = field_info.get('data_type', 'string')
                body_data[field_name] = self._get_type_placeholder(data_type, field_name)
        
        return json.dumps(body_data, indent=2, ensure_ascii=False)
    
    def _get_type_placeholder(self, data_type: str, field_name: str) -> Any:
        """
        Get placeholder value based on data type.
        
        Args:
            data_type: Field data type
            field_name: Field name for placeholder
            
        Returns:
            Appropriate placeholder value
        """
        type_map = {
            'integer': 0,
            'number': 0.0,
            'boolean': False,
            'array': [],
            'object': {},
            'string': f'<{field_name}>'
        }
        return type_map.get(data_type, f'<{field_name}>')
    
    def _create_postman_item(
        self, 
        endpoint: Dict[str, Any], 
        url: str, 
        headers: Dict[str, str], 
        body: str
    ) -> PostmanItem:
        """
        Create Postman collection item from endpoint data.
        
        Args:
            endpoint: Endpoint data from Swagger analysis
            url: Full URL with replaced parameters
            headers: Headers dictionary
            body: Request body string
            
        Returns:
            PostmanItem object
        """
        # Convert headers to Postman format
        postman_headers = [
            {"key": key, "value": value, "type": "text"} 
            for key, value in headers.items()
        ]
        
        # Replace base URL with variable (robust version)
        from urllib.parse import urlparse
        
        parsed_url = urlparse(url)
        if parsed_url.scheme and parsed_url.netloc:
            # Full URL: replace scheme://netloc with {{baseUrl}}
            base_part = f"{parsed_url.scheme}://{parsed_url.netloc}"
            postman_url = url.replace(base_part, '{{baseUrl}}', 1)
        else:
            # Already relative or has variable
            postman_url = url
        
        # Create request
        postman_request = PostmanRequest(
            method=endpoint['method'],
            url=postman_url,
            headers=postman_headers,
            body=body
        )
        
        # Create item with descriptive name
        item_name = f"{endpoint['method']} {endpoint['path']}"
        if endpoint.get('summary'):
            item_name += f" - {endpoint['summary']}"
        
        return PostmanItem(
            name=item_name,
            request=postman_request
        )
    
    async def export_curl_commands(self, curl_commands: List[CurlCommand], output_file: str) -> str:
        """
        Export cURL commands to file using repository.
        
        Args:
            curl_commands: List of CurlCommand objects
            output_file: Path for output file
            
        Returns:
            Absolute path to saved file
        """
        return await self.repository.save_curl_commands(curl_commands, output_file)
    
    async def export_postman_collection(self, collection: PostmanCollection, output_file: str) -> str:
        """
        Export Postman collection to file using repository.
        
        Args:
            collection: PostmanCollection object
            output_file: Path for output file
            
        Returns:
            Absolute path to saved file
        """
        return await self.repository.save_postman_collection(collection, output_file)
