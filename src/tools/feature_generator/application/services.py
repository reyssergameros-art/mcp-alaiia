"""Application services for feature generation."""
from typing import Dict, Any, List
from ..domain.repositories import FeatureRepository
from ..domain.models import FeatureGenerationResult, FeatureFile


class FeatureGenerationService:
    """Service for generating feature files from swagger analysis."""
    
    def __init__(self, repository: FeatureRepository):
        self._repository = repository
    
    async def generate_features_from_swagger(self, swagger_data: Dict[str, Any]) -> FeatureGenerationResult:
        """
        Generate feature files from swagger analysis result.
        
        Args:
            swagger_data: Swagger analysis result data
            
        Returns:
            FeatureGenerationResult with generated features
        """
        return await self._repository.generate_features_from_swagger(swagger_data)
    
    async def save_features_to_directory(self, 
                                       features: FeatureGenerationResult, 
                                       output_dir: str) -> List[str]:
        """
        Save generated features to a directory.
        
        Args:
            features: The feature generation result
            output_dir: Directory to save files
            
        Returns:
            List of created file paths
        """
        return await self._repository.save_feature_files(features.features, output_dir)
    
    def get_features_summary(self, features: FeatureGenerationResult) -> Dict[str, Any]:
        """
        Get a summary of the generated features.
        
        Args:
            features: The feature generation result
            
        Returns:
            Dictionary with summary information
        """
        return {
            "total_features": len(features.features),
            "total_scenarios": features.total_scenarios,
            "base_url": features.base_url,
            "features_by_tag": self._count_features_by_tag(features.features),
            "scenarios_per_feature": [len(f.scenarios) for f in features.features]
        }
    
    def _count_features_by_tag(self, features: List[FeatureFile]) -> Dict[str, int]:
        """Count features by their tags."""
        tag_count = {}
        for feature in features:
            for tag in feature.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        return tag_count