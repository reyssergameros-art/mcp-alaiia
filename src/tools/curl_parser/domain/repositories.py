"""
Repository interface for cURL parsing.
Following Repository Pattern and Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from .models import ParsedCurlRequest


class CurlParserRepository(ABC):
    """
    Interface for parsing cURL commands.
    
    Following SOLID:
    - DIP: High-level modules depend on this abstraction
    - ISP: Single focused responsibility
    """
    
    @abstractmethod
    async def parse_curl_command(self, curl_command: str) -> ParsedCurlRequest:
        """
        Parse a cURL command string into structured data.
        
        Args:
            curl_command: Raw cURL command string
            
        Returns:
            ParsedCurlRequest with extracted data
            
        Raises:
            ValueError: If cURL command is invalid
        """
        pass
