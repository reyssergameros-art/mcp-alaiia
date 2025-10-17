"""
Application service for Karate Java project generation.
Following Application Service pattern and SRP.
"""

import os
from typing import Dict, Any, List, Optional
from ..domain.models import (
    KarateJavaProject,
    MavenProject,
    ProjectConfig,
    JavaClass,
    JavaMethod,
    JavaField,
    FeatureFile,
    JavaAccessModifier,
    JavaClassType
)
from ..domain.repositories import KarateJavaRepository
from .templates import JavaTemplates, MavenTemplates, KarateTemplates


class KarateJavaGenerationService:
    """
    Service that orchestrates Karate Java project generation.
    
    Following SOLID:
    - SRP: Only handles project generation orchestration
    - DIP: Depends on repository abstraction
    - OCP: Extensible without modification
    """
    
    def __init__(self, repository: KarateJavaRepository):
        """Initialize with repository dependency."""
        self.repository = repository
        self.java_templates = JavaTemplates()
        self.maven_templates = MavenTemplates()
        self.karate_templates = KarateTemplates()
    
    async def generate_project(
        self,
        swagger_data: Dict[str, Any],
        features_data: Dict[str, Any],
        output_dir: str,
        config: Optional[Dict[str, Any]] = None
    ) -> KarateJavaProject:
        """
        Generate complete Karate Java project.
        
        Args:
            swagger_data: Swagger analysis result
            features_data: Feature generation result
            output_dir: Output directory for project
            config: Optional project configuration
            
        Returns:
            KarateJavaProject with all generated artifacts
        """
        # 1. Build project model
        project = self._build_project_model(swagger_data, features_data, config)
        
        # 2. Create project structure
        await self.repository.create_project_structure(output_dir)
        
        # 3. Save Maven configuration
        await self.repository.save_maven_config(project.maven_config, output_dir)
        
        # 4. Save Java classes
        await self._save_java_classes(project, output_dir)
        
        # 5. Save feature files
        await self._save_features(project, output_dir)
        
        # 6. Save configurations
        await self._save_configurations(project, output_dir)
        
        # 7. Save additional files
        await self._save_additional_files(project, output_dir)
        
        return project
    
    def _build_project_model(
        self,
        swagger_data: Dict[str, Any],
        features_data: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> KarateJavaProject:
        """Build the complete project model."""
        # Extract base URL
        base_url = swagger_data.get('base_urls', ['http://localhost:8080'])[0]
        
        # Create Maven configuration
        maven_config = MavenProject(
            artifact_id=config.get('artifact_id', 'karate-tests') if config else 'karate-tests',
            name=swagger_data.get('title', 'API Tests'),
            description=f"Automated tests for {swagger_data.get('title', 'API')}"
        )
        
        # Create project configuration
        project_config = self._create_project_config(base_url, config)
        
        # Generate Java classes
        test_runners = self._generate_test_runners(features_data)
        hooks = self._generate_hooks()
        config_classes = self._generate_config_classes()
        utils = self._generate_utils()
        
        # Convert features
        features = self._convert_features(features_data)
        
        return KarateJavaProject(
            maven_config=maven_config,
            project_config=project_config,
            test_runners=test_runners,
            hooks=hooks,
            config_classes=config_classes,
            utils=utils,
            features=features
        )
    
    def _create_project_config(
        self,
        base_url: str,
        config: Optional[Dict[str, Any]]
    ) -> ProjectConfig:
        """Create project configuration."""
        environments = {
            'dev': {'baseUrl': 'http://localhost:8080'},
            'qa': {'baseUrl': base_url},
            'prod': {'baseUrl': base_url}
        }
        
        if config and 'environments' in config:
            environments.update(config['environments'])
        
        return ProjectConfig(
            base_url=base_url,
            environments=environments,
            timeout=config.get('timeout', 30000) if config else 30000,
            parallel_execution=config.get('parallel', False) if config else False,
            threads=config.get('threads', 5) if config else 5
        )
    
    def _generate_test_runners(self, features_data: Dict[str, Any]) -> List[JavaClass]:
        """Generate test runner classes for each feature."""
        runners = []
        package = "com.automation.runners"
        
        for feature in features_data.get('features', []):
            feature_name = feature.get('feature_name', 'Test')
            # Clean name for class
            class_name = self._to_class_name(feature_name) + "Test"
            
            # Get tags
            tags = feature.get('tags', [])
            
            # Determine feature path
            feature_path = f"features/{self._to_snake_case(feature_name)}.feature"
            
            # Generate class code using template
            class_code = self.java_templates.test_runner_class(
                package=package,
                class_name=class_name,
                feature_path=feature_path,
                tags=tags
            )
            
            # Create JavaClass from template (simplified)
            java_class = self._parse_class_from_template(class_code, package, class_name)
            runners.append(java_class)
        
        # Add parallel runner if configured
        if features_data.get('total_scenarios', 0) > 1:
            parallel_code = self.java_templates.parallel_runner_class(package, threads=5)
            parallel_class = self._parse_class_from_template(parallel_code, package, "ParallelTestRunner")
            runners.append(parallel_class)
        
        return runners
    
    def _generate_hooks(self) -> List[JavaClass]:
        """Generate hook classes."""
        package = "com.automation.hooks"
        
        hooks_code = self.java_templates.test_hooks_class(package)
        hooks_class = self._parse_class_from_template(hooks_code, package, "TestHooks")
        
        return [hooks_class]
    
    def _generate_config_classes(self) -> List[JavaClass]:
        """Generate configuration classes."""
        package = "com.automation.config"
        
        config_code = self.java_templates.test_config_class(package)
        config_class = self._parse_class_from_template(config_code, package, "TestConfig")
        
        return [config_class]
    
    def _generate_utils(self) -> List[JavaClass]:
        """Generate utility classes."""
        package = "com.automation.utils"
        utils = []
        
        # API Helper
        api_helper_code = self.java_templates.api_helper_class(package)
        api_helper = self._parse_class_from_template(api_helper_code, package, "ApiHelper")
        utils.append(api_helper)
        
        # Data Generator
        data_gen_code = self.java_templates.data_generator_class(package)
        data_gen = self._parse_class_from_template(data_gen_code, package, "DataGenerator")
        utils.append(data_gen)
        
        return utils
    
    def _convert_features(self, features_data: Dict[str, Any]) -> List[FeatureFile]:
        """Convert feature data to FeatureFile objects."""
        feature_files = []
        
        for feature in features_data.get('features', []):
            feature_name = feature.get('feature_name', 'test')
            filename = f"{self._to_snake_case(feature_name)}.feature"
            
            feature_file = FeatureFile(
                name=filename,
                path=f"features/{filename}",
                content=feature.get('content', ''),
                tags=feature.get('tags', [])
            )
            feature_files.append(feature_file)
        
        return feature_files
    
    def _parse_class_from_template(
        self,
        template_code: str,
        package: str,
        class_name: str
    ) -> JavaClass:
        """
        Create JavaClass from template code.
        Simplified version - stores template as-is.
        """
        # Extract imports from template
        imports = []
        for line in template_code.split('\n'):
            if line.strip().startswith('import '):
                import_stmt = line.strip().replace('import ', '').replace(';', '')
                imports.append(import_stmt)
        
        # Create class with template code stored
        java_class = JavaClass(
            package=package,
            name=class_name,
            imports=imports
        )
        
        # Store the complete template code in a special method
        # This is a simplified approach - in production you might parse the actual structure
        java_class._template_code = template_code
        
        return java_class
    
    async def _save_java_classes(self, project: KarateJavaProject, output_dir: str) -> None:
        """Save all Java classes."""
        all_classes = (
            project.test_runners +
            project.hooks +
            project.config_classes +
            project.utils
        )
        
        for java_class in all_classes:
            await self.repository.save_java_class(java_class, output_dir, "test")
    
    async def _save_features(self, project: KarateJavaProject, output_dir: str) -> None:
        """Save all feature files."""
        for feature in project.features:
            await self.repository.save_feature_file(feature, output_dir)
    
    async def _save_configurations(self, project: KarateJavaProject, output_dir: str) -> None:
        """Save configuration files."""
        # Karate config
        karate_config = self.karate_templates.karate_config_js(project.project_config)
        await self.repository.save_karate_config(karate_config, output_dir)
        
        # Logback config
        logback_config = self.karate_templates.logback_xml()
        await self.repository.save_logback_config(logback_config, output_dir)
        
        # Environment properties
        for env_name, env_props in project.project_config.environments.items():
            filename = f"{env_name}.properties"
            await self.repository.save_properties_file(env_props, filename, output_dir)
    
    async def _save_additional_files(self, project: KarateJavaProject, output_dir: str) -> None:
        """Save additional project files."""
        # README
        readme = self.karate_templates.readme(
            project_name=project.maven_config.name,
            base_url=project.project_config.base_url,
            features_count=len(project.features)
        )
        await self.repository.save_readme(readme, output_dir)
        
        # .gitignore
        gitignore = self.karate_templates.gitignore()
        with open(os.path.join(output_dir, '.gitignore'), 'w', encoding='utf-8') as f:
            f.write(gitignore)
    
    def get_project_summary(self, project: KarateJavaProject) -> Dict[str, Any]:
        """Get project generation summary."""
        return project.get_summary()
    
    @staticmethod
    def _to_class_name(text: str) -> str:
        """Convert text to Java class name (PascalCase)."""
        # Remove special characters and split by spaces/underscores
        words = text.replace('-', ' ').replace('_', ' ').split()
        # Capitalize first letter of each word
        return ''.join(word.capitalize() for word in words if word)
    
    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        # Replace spaces and hyphens with underscores
        text = text.replace(' ', '_').replace('-', '_')
        # Convert to lowercase
        return text.lower()
