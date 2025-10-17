"""
Repository interface for Karate Java project generation.
Following Repository Pattern and Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import KarateJavaProject, JavaClass, FeatureFile, MavenProject


class KarateJavaRepository(ABC):
    """
    Abstract repository for Karate Java project generation.
    
    Following SOLID:
    - DIP: Abstract interface, implementations depend on this
    - ISP: Specific methods for each operation
    - SRP: Only handles project file operations
    """
    
    @abstractmethod
    async def create_project_structure(self, output_dir: str) -> None:
        """
        Create the complete project directory structure.
        
        Args:
            output_dir: Base directory for the project
        """
        pass
    
    @abstractmethod
    async def save_maven_config(self, maven_config: MavenProject, output_dir: str) -> str:
        """
        Save Maven pom.xml file.
        
        Args:
            maven_config: Maven configuration
            output_dir: Base directory for the project
            
        Returns:
            Path to saved pom.xml
        """
        pass
    
    @abstractmethod
    async def save_java_class(
        self,
        java_class: JavaClass,
        output_dir: str,
        source_type: str = "test"
    ) -> str:
        """
        Save a Java class file.
        
        Args:
            java_class: Java class to save
            output_dir: Base directory for the project
            source_type: 'main' or 'test'
            
        Returns:
            Path to saved .java file
        """
        pass
    
    @abstractmethod
    async def save_feature_file(
        self,
        feature: FeatureFile,
        output_dir: str
    ) -> str:
        """
        Save a Karate feature file.
        
        Args:
            feature: Feature file to save
            output_dir: Base directory for the project
            
        Returns:
            Path to saved .feature file
        """
        pass
    
    @abstractmethod
    async def save_karate_config(
        self,
        config_content: str,
        output_dir: str
    ) -> str:
        """
        Save karate-config.js file.
        
        Args:
            config_content: JavaScript configuration content
            output_dir: Base directory for the project
            
        Returns:
            Path to saved config file
        """
        pass
    
    @abstractmethod
    async def save_properties_file(
        self,
        properties: Dict[str, str],
        filename: str,
        output_dir: str
    ) -> str:
        """
        Save properties file.
        
        Args:
            properties: Key-value properties
            filename: Name of properties file (e.g., 'dev.properties')
            output_dir: Base directory for the project
            
        Returns:
            Path to saved properties file
        """
        pass
    
    @abstractmethod
    async def save_readme(
        self,
        readme_content: str,
        output_dir: str
    ) -> str:
        """
        Save README.md file.
        
        Args:
            readme_content: Markdown content
            output_dir: Base directory for the project
            
        Returns:
            Path to saved README.md
        """
        pass
    
    @abstractmethod
    async def save_logback_config(
        self,
        logback_content: str,
        output_dir: str
    ) -> str:
        """
        Save logback-test.xml configuration.
        
        Args:
            logback_content: XML configuration content
            output_dir: Base directory for the project
            
        Returns:
            Path to saved logback config
        """
        pass
    
    @abstractmethod
    async def save_test_data(
        self,
        data: Dict[str, Any],
        filename: str,
        output_dir: str
    ) -> str:
        """
        Save test data JSON file.
        
        Args:
            data: Test data dictionary
            filename: Name of data file
            output_dir: Base directory for the project
            
        Returns:
            Path to saved data file
        """
        pass
