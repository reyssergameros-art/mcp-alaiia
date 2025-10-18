"""
Domain models for cURL command generation.
Following Domain-Driven Design principles.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import uuid


@dataclass
class CurlCommand:
    """
    Domain model representing a cURL command.
    
    Attributes:
        name: Descriptive name for the command
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: Full URL endpoint
        headers: Dictionary of HTTP headers
        body: Optional request body as string
        description: Optional description of the command
    """
    name: str
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str] = None
    description: Optional[str] = None
    
    def to_curl_string(self, pretty: bool = True) -> str:
        """
        Convert domain model to cURL command string.
        
        Args:
            pretty: If True, format with line breaks for readability
            
        Returns:
            Formatted cURL command string
        """
        parts = [f"curl -X {self.method}"]
        
        # Add headers
        for key, value in self.headers.items():
            parts.append(f'-H "{key}: {value}"')
        
        # Add body if present
        if self.body:
            # Escape single quotes in body for shell safety
            escaped_body = self.body.replace("'", "'\"'\"'")
            parts.append(f"-d '{escaped_body}'")
        
        # Add URL
        parts.append(f'"{self.url}"')
        
        # Format output
        if pretty:
            return " \\\n  ".join(parts)
        return " ".join(parts)


@dataclass
class PostmanRequest:
    """
    Domain model for Postman request.
    
    Attributes:
        method: HTTP method
        url: Request URL
        headers: List of header dictionaries
        body: Optional request body
    """
    method: str
    url: str
    headers: List[Dict[str, str]]
    body: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """
        Convert to Postman request format.
        
        Generates a proper Postman v2.1 request object with correct URL structure.
        """
        from urllib.parse import urlparse
        
        # Parse the URL properly
        if '{{baseUrl}}' in self.url:
            # URL already has variable, extract path
            path_part = self.url.replace('{{baseUrl}}', '').strip('/')
            path_segments = [p for p in path_part.split('/') if p]
            host_segments = ["{{baseUrl}}"]
            raw_url = self.url
        else:
            # Full URL, need to parse and convert
            parsed = urlparse(self.url)
            
            # Extract host segments (for Postman format)
            if parsed.hostname:
                host_segments = ["{{baseUrl}}"]
            else:
                host_segments = ["{{baseUrl}}"]
            
            # Extract path segments
            path_segments = [p for p in parsed.path.strip('/').split('/') if p]
            
            # Build raw URL with variable
            if parsed.path:
                raw_url = f"{{{{baseUrl}}}}{parsed.path}"
            else:
                raw_url = "{{baseUrl}}"
            
            # Add query parameters if present
            if parsed.query:
                raw_url += f"?{parsed.query}"
        
        result = {
            "method": self.method,
            "header": self.headers,
            "url": {
                "raw": raw_url,
                "host": host_segments,
                "path": path_segments
            }
        }
        
        # Add query parameters to url object if present
        if '?' in self.url:
            query_string = self.url.split('?')[1]
            query_params = []
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params.append({
                        "key": key,
                        "value": value
                    })
            if query_params:
                result["url"]["query"] = query_params
        
        # Add body if present
        if self.body:
            result["body"] = {
                "mode": "raw",
                "raw": self.body,
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        
        return result


@dataclass
class PostmanItem:
    """
    Domain model for Postman collection item.
    
    Attributes:
        name: Item name
        request: PostmanRequest object
    """
    name: str
    request: PostmanRequest
    
    def to_dict(self) -> Dict:
        """Convert to Postman item format"""
        return {
            "name": self.name,
            "request": self.request.to_dict()
        }


@dataclass
class PostmanCollection:
    """
    Domain model for Postman Collection v2.1.
    
    Attributes:
        name: Collection name
        items: List of PostmanItem objects
        base_url: Base URL for the API
        description: Optional collection description
    """
    name: str
    items: List[PostmanItem]
    base_url: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """
        Convert to Postman collection v2.1 format.
        
        Generates a valid Postman Collection v2.1.0 JSON with:
        - Unique _postman_id (UUID v4)
        - Proper schema reference
        - Base URL as collection variable
        - All items properly formatted
        
        Returns:
            Dictionary in Postman collection JSON schema format
        """
        return {
            "info": {
                "name": self.name,
                "description": self.description or f"API Collection generated from Swagger by MCP-ALAIIA",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "_postman_id": str(uuid.uuid4()),
                "version": "1.0.0"
            },
            "variable": [
                {
                    "key": "baseUrl",
                    "value": self.base_url,
                    "type": "string"
                }
            ],
            "item": [item.to_dict() for item in self.items]
        }


@dataclass
class CurlGenerationResult:
    """
    Aggregate root for cURL generation results.
    
    Attributes:
        curl_commands: List of generated cURL commands
        postman_collection: Generated Postman collection
        total_commands: Total number of commands generated
        base_url: Base URL used for generation
    """
    curl_commands: List[CurlCommand]
    postman_collection: PostmanCollection
    total_commands: int
    base_url: str
    
    def get_summary(self) -> Dict:
        """Get summary of generation results"""
        return {
            "total_commands": self.total_commands,
            "base_url": self.base_url,
            "collection_name": self.postman_collection.name,
            "total_items": len(self.postman_collection.items)
        }
