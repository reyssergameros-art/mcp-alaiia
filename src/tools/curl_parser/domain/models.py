"""
Domain models for cURL parsing.
Following Domain-Driven Design principles.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ParsedHeader:
    """Domain model representing a parsed HTTP header."""
    name: str
    value: str


@dataclass
class ParsedCurlRequest:
    """
    Domain model representing a parsed cURL command.
    
    This model contains ONLY the parsed data from the cURL command,
    without any business logic or assumptions.
    """
    method: str
    url: str
    headers: List[ParsedHeader] = field(default_factory=list)
    body: Optional[str] = None
    raw_curl: Optional[str] = None
    
    def get_base_url(self) -> str:
        """Extract base URL (protocol + host + port) from full URL."""
        if "://" not in self.url:
            # If no protocol, assume http and return as-is for localhost-style URLs
            return self.url.split("/")[0] if "/" in self.url else self.url
        
        protocol, rest = self.url.split("://", 1)
        host_port = rest.split("/")[0]
        return f"{protocol}://{host_port}"
    
    def get_path(self) -> str:
        """Extract path component from URL."""
        if "://" not in self.url:
            # No protocol, treat whole thing as path if starts with /
            if self.url.startswith("/"):
                return self.url.split("?")[0]  # Remove query string
            # Otherwise assume it's just host, return /
            parts = self.url.split("/", 1)
            return "/" + parts[1].split("?")[0] if len(parts) > 1 else "/"
        
        # Has protocol
        _, rest = self.url.split("://", 1)
        path_parts = rest.split("/", 1)
        
        if len(path_parts) > 1:
            path = "/" + path_parts[1]
            return path.split("?")[0]  # Remove query string
        
        return "/"
    
    def get_headers_dict(self) -> Dict[str, str]:
        """Convert headers list to dictionary."""
        return {header.name: header.value for header in self.headers}


@dataclass
class CurlParseResult:
    """
    Aggregate root for cURL parsing results.
    Contains the parsed request ready to be converted to swagger format.
    """
    parsed_request: ParsedCurlRequest
    
    def to_swagger_data(self) -> Dict[str, Any]:
        """
        Convert parsed cURL to swagger-compatible format.
        This enables reuse of existing feature_generator and jmeter_generator.
        """
        # Extract URL components
        base_url = self.parsed_request.get_base_url()
        path = self.parsed_request.get_path()
        method = self.parsed_request.method
        
        # Build headers in swagger format
        headers_list = []
        for header in self.parsed_request.headers:
            headers_list.append({
                "name": header.name,
                "required": True,
                "data_type": "string",
                "example": header.value,
                "description": f"Header from cURL"
            })
        
        # Build request body in swagger format if present
        request_body_dict = {}
        if self.parsed_request.body:
            request_body_dict = self._parse_body_to_swagger_format(
                self.parsed_request.body
            )
        
        # Detect path parameters (e.g., /users/{id})
        path_parameters = self._extract_path_parameters(path)
        
        # Build endpoint structure compatible with existing generators
        endpoint = {
            "path": path,
            "method": method,
            "summary": f"{method} request to {path}",
            "description": "Generated from cURL command",
            "headers": headers_list,
            "request_body": request_body_dict,
            "path_parameters": path_parameters,
            "query_parameters": [],
            "responses": [
                {
                    "status_code": "200",
                    "description": "Successful response",
                    "content_type": "*/*"
                }
            ]
        }
        
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
        import json
        
        result = {}
        
        try:
            # Try to parse as JSON
            body_data = json.loads(body_str)
            
            if isinstance(body_data, dict):
                for field_name, field_value in body_data.items():
                    result[field_name] = {
                        "name": field_name,
                        "data_type": self._infer_type(field_value),
                        "required": True,
                        "example": field_value,
                        "description": f"Field from cURL body"
                    }
        except (json.JSONDecodeError, TypeError):
            # Not JSON, treat as raw
            result["raw_body"] = {
                "name": "raw_body",
                "data_type": "string",
                "required": True,
                "example": body_str,
                "description": "Raw body data"
            }
        
        return result
    
    def _infer_type(self, value: Any) -> str:
        """Infer swagger data type from Python value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"
    
    def _extract_path_parameters(self, path: str) -> List[Dict[str, Any]]:
        """Extract path parameters like {id} or :id from path."""
        import re
        
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
                    path_params.append({
                        "name": match,
                        "required": True,
                        "data_type": "string",
                        "example": f"<{match}>",
                        "description": f"Path parameter"
                    })
        
        return path_params
    
    def _generate_title_from_path(self, path: str, method: str) -> str:
        """Generate API title from path."""
        # Extract first meaningful part of path
        parts = [p for p in path.split('/') if p and not p.startswith('{') and not p.startswith(':')]
        
        if parts:
            resource = parts[0].replace('_', ' ').replace('-', ' ').title()
            return f"{resource} API (from cURL)"
        
        return f"{method} API (from cURL)"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of parsing results."""
        return {
            "method": self.parsed_request.method,
            "url": self.parsed_request.url,
            "path": self.parsed_request.get_path(),
            "base_url": self.parsed_request.get_base_url(),
            "headers_count": len(self.parsed_request.headers),
            "has_body": self.parsed_request.body is not None
        }
