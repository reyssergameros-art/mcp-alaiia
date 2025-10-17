"""
Application service for cURL parsing.
Following Application Service pattern and SRP.
"""

from ..domain.models import CurlParseResult
from ..domain.repositories import CurlParserRepository


class CurlParsingService:
    """
    Service that orchestrates cURL parsing.
    
    This service:
    - Parses cURL commands
    - Converts to swagger-compatible format
    - Does NOT modify existing generators
    
    Following SOLID:
    - SRP: Only handles cURL parsing orchestration
    - DIP: Depends on repository abstraction
    - OCP: Extensible without modification
    """
    
    def __init__(self, repository: CurlParserRepository):
        """Initialize with repository dependency."""
        self.repository = repository
    
    async def parse_curl(self, curl_command: str) -> CurlParseResult:
        """
        Parse cURL command and prepare for test generation.
        
        Args:
            curl_command: Raw cURL command string
            
        Returns:
            CurlParseResult ready to be converted to swagger format
            
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
