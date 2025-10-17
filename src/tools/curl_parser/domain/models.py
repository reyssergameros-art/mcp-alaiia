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
    Contains the parsed request as a pure domain model.
    
    Following SOLID:
    - SRP: Only holds parsed data, no conversion logic
    - OCP: Conversion logic delegated to application layer mappers
    """
    parsed_request: ParsedCurlRequest
    
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
