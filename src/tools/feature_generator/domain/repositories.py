"""Repository interface for feature generation."""
from abc import ABC, abstractmethod
from typing import List, Any, Dict
from .models import FeatureGenerationResult, FeatureFile


class FeatureRepository(ABC):
    """Abstract repository for feature operations."""
    
    @abstractmethod
    async def generate_features_from_swagger(self, swagger_data: Dict[str, Any]) -> FeatureGenerationResult:
        """Generate feature files from swagger analysis result."""
        pass
    
    @abstractmethod
    async def save_feature_files(self, features: List[FeatureFile], output_dir: str) -> List[str]:
        """Save feature files to disk."""
        pass