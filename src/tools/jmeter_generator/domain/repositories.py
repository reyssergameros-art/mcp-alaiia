"""Repository interface for JMeter generation."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .models import JMeterGenerationResult


class JMeterRepository(ABC):
    """Abstract repository for JMeter operations."""
    
    @abstractmethod
    async def generate_jmx_from_swagger(
        self, 
        swagger_data: Dict[str, Any],
        test_scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> JMeterGenerationResult:
        """
        Generate JMX test plan from swagger analysis result.
        
        Args:
            swagger_data: Swagger analysis result data
            test_scenarios: Optional list of test scenarios with Thread Group configurations
        """
        pass
    
    @abstractmethod
    async def generate_jmx_from_features(self, features_data: Dict[str, Any]) -> JMeterGenerationResult:
        """Generate JMX test plan from feature files data."""
        pass
    
    @abstractmethod
    async def save_jmx_file(self, result: JMeterGenerationResult, file_path: str) -> str:
        """Save JMX file to disk."""
        pass