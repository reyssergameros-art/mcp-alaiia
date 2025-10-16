"""
Repository interfaces for cURL generation.
Following the Repository Pattern and Dependency Inversion Principle (SOLID).
"""

from abc import ABC, abstractmethod
from typing import List
from .models import CurlCommand, PostmanCollection


class CurlExportRepository(ABC):
    """
    Abstract repository interface for exporting cURL commands and collections.
    
    This interface defines the contract for persistence operations,
    allowing different implementations (file system, database, cloud storage, etc.)
    without changing the domain or application layers.
    
    Following:
    - Dependency Inversion Principle: High-level modules don't depend on low-level modules
    - Interface Segregation Principle: Focused interface for cURL export operations
    """
    
    @abstractmethod
    async def save_curl_commands(self, commands: List[CurlCommand], output_file: str) -> str:
        """
        Save cURL commands to persistent storage.
        
        Args:
            commands: List of CurlCommand domain objects
            output_file: Path where commands should be saved
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            IOError: If file cannot be written
            ValueError: If commands list is empty or invalid
        """
        pass
    
    @abstractmethod
    async def save_postman_collection(self, collection: PostmanCollection, output_file: str) -> str:
        """
        Save Postman collection to persistent storage.
        
        Args:
            collection: PostmanCollection domain object
            output_file: Path where collection should be saved
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            IOError: If file cannot be written
            ValueError: If collection is invalid
        """
        pass
