"""Application services for JMeter generation."""
from typing import Dict, Any
from ..domain.repositories import JMeterRepository
from ..domain.models import JMeterGenerationResult


class JMeterGenerationService:
    """Service for generating JMeter test plans."""
    
    def __init__(self, repository: JMeterRepository):
        self._repository = repository
    
    async def generate_from_swagger(self, swagger_data: Dict[str, Any]) -> JMeterGenerationResult:
        """
        Generate JMeter test plan from swagger analysis result.
        
        Args:
            swagger_data: Swagger analysis result data
            
        Returns:
            JMeterGenerationResult with generated test plan
        """
        return await self._repository.generate_jmx_from_swagger(swagger_data)
    
    async def generate_from_features(self, features_data: Dict[str, Any]) -> JMeterGenerationResult:
        """
        Generate JMeter test plan from feature files data.
        
        Args:
            features_data: Feature generation result data
            
        Returns:
            JMeterGenerationResult with generated test plan
        """
        return await self._repository.generate_jmx_from_features(features_data)
    
    async def save_test_plan(self, result: JMeterGenerationResult, file_path: str) -> str:
        """
        Save JMeter test plan to file.
        
        Args:
            result: The JMeter generation result
            file_path: Path to save the JMX file
            
        Returns:
            Path of the saved file
        """
        return await self._repository.save_jmx_file(result, file_path)
    
    def get_test_plan_summary(self, result: JMeterGenerationResult) -> Dict[str, Any]:
        """
        Get a summary of the test plan.
        
        Args:
            result: The JMeter generation result
            
        Returns:
            Dictionary with summary information
        """
        return {
            "test_plan_name": result.test_plan.name,
            "base_url": result.test_plan.base_url,
            "protocol": result.test_plan.protocol,
            "port": result.test_plan.port,
            "total_thread_groups": result.total_thread_groups,
            "total_requests": result.total_requests,
            "thread_groups": [
                {
                    "name": tg.name,
                    "num_threads": tg.num_threads,
                    "ramp_time": tg.ramp_time,
                    "loop_count": tg.loop_count,
                    "requests_count": len(tg.http_requests)
                }
                for tg in result.test_plan.thread_groups
            ]
        }