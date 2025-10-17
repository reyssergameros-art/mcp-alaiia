"""
File system implementation of KarateJavaRepository.
Handles actual file and directory operations.
"""

import os
import json
from typing import Dict, Any
from ..domain.repositories import KarateJavaRepository
from ..domain.models import KarateJavaProject, JavaClass, FeatureFile, MavenProject
from ..application.templates import MavenTemplates


class FileSystemKarateJavaRepository(KarateJavaRepository):
    """
    File system implementation of Karate Java repository.
    
    Following SOLID:
    - SRP: Only handles file system operations
    - DIP: Implements abstract repository interface
    - OCP: Can be extended for other storage types
    """
    
    def __init__(self):
        """Initialize repository."""
        self.maven_templates = MavenTemplates()
    
    async def create_project_structure(self, output_dir: str) -> None:
        """Create the complete Maven project directory structure."""
        directories = [
            # Main source directories
            os.path.join(output_dir, "src", "main", "java"),
            os.path.join(output_dir, "src", "main", "resources"),
            
            # Test source directories
            os.path.join(output_dir, "src", "test", "java", "com", "automation", "runners"),
            os.path.join(output_dir, "src", "test", "java", "com", "automation", "hooks"),
            os.path.join(output_dir, "src", "test", "java", "com", "automation", "config"),
            os.path.join(output_dir, "src", "test", "java", "com", "automation", "utils"),
            
            # Test resources
            os.path.join(output_dir, "src", "test", "resources", "features"),
            os.path.join(output_dir, "src", "test", "resources", "data"),
            os.path.join(output_dir, "src", "test", "resources", "data", "schemas"),
            os.path.join(output_dir, "src", "test", "resources", "config"),
            
            # Target directory
            os.path.join(output_dir, "target")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    async def save_maven_config(self, maven_config: MavenProject, output_dir: str) -> str:
        """Save pom.xml file."""
        pom_content = self.maven_templates.pom_xml(maven_config)
        pom_path = os.path.join(output_dir, "pom.xml")
        
        with open(pom_path, 'w', encoding='utf-8') as f:
            f.write(pom_content)
        
        return pom_path
    
    async def save_java_class(
        self,
        java_class: JavaClass,
        output_dir: str,
        source_type: str = "test"
    ) -> str:
        """Save a Java class file."""
        # Determine base path
        base_path = os.path.join(output_dir, "src", source_type, "java")
        
        # Get package path
        package_path = java_class.package.replace(".", os.sep)
        
        # Create full directory path
        full_dir = os.path.join(base_path, package_path)
        os.makedirs(full_dir, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(full_dir, f"{java_class.name}.java")
        
        # Get code content
        # Check if we have template code stored (from service)
        if hasattr(java_class, '_template_code'):
            code_content = java_class._template_code
        else:
            code_content = java_class.to_code()
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        return file_path
    
    async def save_feature_file(
        self,
        feature: FeatureFile,
        output_dir: str
    ) -> str:
        """Save a Karate feature file."""
        # Feature files go in test/resources/features
        features_dir = os.path.join(output_dir, "src", "test", "resources", "features")
        
        # Extract directory from path if present
        if '/' in feature.path:
            parts = feature.path.split('/')
            # Skip 'features' if it's the first part
            if parts[0] == 'features':
                parts = parts[1:]
            
            if len(parts) > 1:
                # Create subdirectories
                sub_dirs = os.path.join(features_dir, *parts[:-1])
                os.makedirs(sub_dirs, exist_ok=True)
                file_path = os.path.join(sub_dirs, parts[-1])
            else:
                file_path = os.path.join(features_dir, parts[0])
        else:
            file_path = os.path.join(features_dir, feature.name)
        
        # Write feature file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(feature.content)
        
        return file_path
    
    async def save_karate_config(
        self,
        config_content: str,
        output_dir: str
    ) -> str:
        """Save karate-config.js file."""
        config_path = os.path.join(
            output_dir,
            "src", "test", "resources",
            "karate-config.js"
        )
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return config_path
    
    async def save_properties_file(
        self,
        properties: Dict[str, str],
        filename: str,
        output_dir: str
    ) -> str:
        """Save properties file."""
        config_dir = os.path.join(output_dir, "src", "test", "resources", "config")
        os.makedirs(config_dir, exist_ok=True)
        
        file_path = os.path.join(config_dir, filename)
        
        # Write properties in Java properties format
        with open(file_path, 'w', encoding='utf-8') as f:
            for key, value in properties.items():
                f.write(f"{key}={value}\n")
        
        return file_path
    
    async def save_readme(
        self,
        readme_content: str,
        output_dir: str
    ) -> str:
        """Save README.md file."""
        readme_path = os.path.join(output_dir, "README.md")
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return readme_path
    
    async def save_logback_config(
        self,
        logback_content: str,
        output_dir: str
    ) -> str:
        """Save logback-test.xml configuration."""
        logback_path = os.path.join(
            output_dir,
            "src", "test", "resources",
            "logback-test.xml"
        )
        
        with open(logback_path, 'w', encoding='utf-8') as f:
            f.write(logback_content)
        
        return logback_path
    
    async def save_test_data(
        self,
        data: Dict[str, Any],
        filename: str,
        output_dir: str
    ) -> str:
        """Save test data JSON file."""
        data_dir = os.path.join(output_dir, "src", "test", "resources", "data")
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = os.path.join(data_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return file_path
