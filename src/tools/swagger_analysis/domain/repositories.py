"""Repository interface for swagger analysis."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import SwaggerAnalysisResult


class SwaggerRepository(ABC):
    """Abstract repository for swagger operations."""
    
    @abstractmethod
    async def fetch_swagger_spec(self, url: str) -> Dict[str, Any]:
        """Fetch swagger specification from URL."""
        pass
    
    @abstractmethod
    async def parse_swagger_spec(self, spec: Dict[str, Any]) -> SwaggerAnalysisResult:
        """Parse swagger specification into analysis result."""
        pass