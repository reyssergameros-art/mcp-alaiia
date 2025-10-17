"""
Application service for cURL parsing.
Following Application Service pattern and SRP.
"""

from typing import Dict, Any
from ..domain.models import CurlParseResult
from ..domain.repositories import CurlParserRepository
from .mappers import CurlToSwaggerMapper


class CurlParsingService:
    """
    Service that orchestrates cURL parsing and conversion.
    
    This service:
    - Parses cURL commands
    - Converts to swagger-compatible format using dedicated mapper
    - Does NOT modify existing generators
    
    Following SOLID:
    - SRP: Only handles cURL parsing orchestration
    - DIP: Depends on repository abstraction
    - OCP: Extensible without modification
    """
    
    def __init__(self, repository: CurlParserRepository):
        """Initialize with repository dependency."""
        self.repository = repository
        self.mapper = CurlToSwaggerMapper()
    
    async def parse_curl(self, curl_command: str) -> CurlParseResult:
        """
        Parse cURL command.
        
        Args:
            curl_command: Raw cURL command string
            
        Returns:
            CurlParseResult with parsed data
            
        Raises:
            ValueError: If cURL command is invalid
        """
        if not curl_command or not curl_command.strip():
            raise ValueError("cURL command cannot be empty")
        
        # Parse using repository
        parsed_request = await self.repository.parse_curl_command(curl_command)
        
        # Create result aggregate
        result = CurlParseResult(parsed_request=parsed_request)
        
        return result
    
    def convert_to_swagger(self, parse_result: CurlParseResult) -> Dict[str, Any]:
        """
        Convert parsed cURL to swagger format.
        
        Args:
            parse_result: Parsed cURL result
            
        Returns:
            Swagger-compatible data structure
        """
        return self.mapper.map_to_swagger(parse_result)
