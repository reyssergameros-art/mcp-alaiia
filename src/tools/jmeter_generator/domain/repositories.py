"""Repository interface for JMeter generation."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import JMeterGenerationResult


class JMeterRepository(ABC):
    """Abstract repository for JMeter operations."""
    
    @abstractmethod
    async def generate_jmx_from_swagger(self, swagger_data: Dict[str, Any]) -> JMeterGenerationResult:
        """Generate JMX test plan from swagger analysis result."""
        pass
    
    @abstractmethod
    async def generate_jmx_from_features(self, features_data: Dict[str, Any]) -> JMeterGenerationResult:
        """Generate JMX test plan from feature files data."""
        pass
    
    @abstractmethod
    async def save_jmx_file(self, result: JMeterGenerationResult, file_path: str) -> str:
        """Save JMX file to disk."""
        pass