"""
Domain models for Karate Java project generation.
Following Domain-Driven Design principles.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum


class JavaAccessModifier(Enum):
    """Java access modifiers."""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE_PRIVATE = ""


class JavaClassType(Enum):
    """Java class types."""
    CLASS = "class"
    INTERFACE = "interface"
    ENUM = "enum"
    ABSTRACT_CLASS = "abstract class"


@dataclass
class JavaField:
    """Domain model representing a Java field."""
    name: str
    type: str
    access_modifier: JavaAccessModifier = JavaAccessModifier.PRIVATE
    is_static: bool = False
    is_final: bool = False
    initial_value: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    
    def to_code(self) -> str:
        """Generate Java code for this field."""
        parts = []
        
        # Annotations
        if self.annotations:
            parts.append("\n".join(f"    {ann}" for ann in self.annotations))
        
        # Access modifier
        modifiers = []
        if self.access_modifier.value:
            modifiers.append(self.access_modifier.value)
        if self.is_static:
            modifiers.append("static")
        if self.is_final:
            modifiers.append("final")
        
        field_line = f"    {' '.join(modifiers)} {self.type} {self.name}"
        
        if self.initial_value:
            field_line += f" = {self.initial_value}"
        
        field_line += ";"
        parts.append(field_line)
        
        return "\n".join(parts)


@dataclass
class JavaMethod:
    """Domain model representing a Java method."""
    name: str
    return_type: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)  # [(type, name)]
    body: str = ""
    access_modifier: JavaAccessModifier = JavaAccessModifier.PUBLIC
    is_static: bool = False
    is_abstract: bool = False
    annotations: List[str] = field(default_factory=list)
    throws: List[str] = field(default_factory=list)
    
    def to_code(self) -> str:
        """Generate Java code for this method."""
        parts = []
        
        # Annotations
        if self.annotations:
            parts.append("\n".join(f"    {ann}" for ann in self.annotations))
        
        # Method signature
        modifiers = []
        if self.access_modifier.value:
            modifiers.append(self.access_modifier.value)
        if self.is_static:
            modifiers.append("static")
        if self.is_abstract:
            modifiers.append("abstract")
        
        params = ", ".join(f"{ptype} {pname}" for ptype, pname in self.parameters)
        signature = f"    {' '.join(modifiers)} {self.return_type} {self.name}({params})"
        
        if self.throws:
            signature += f" throws {', '.join(self.throws)}"
        
        if self.is_abstract:
            signature += ";"
            parts.append(signature)
        else:
            signature += " {"
            parts.append(signature)
            
            # Method body
            if self.body:
                # Indent body
                body_lines = self.body.split("\n")
                indented_body = "\n".join(f"        {line}" if line.strip() else "" for line in body_lines)
                parts.append(indented_body)
            
            parts.append("    }")
        
        return "\n".join(parts)


@dataclass
class JavaClass:
    """Domain model representing a Java class."""
    package: str
    name: str
    class_type: JavaClassType = JavaClassType.CLASS
    imports: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    fields: List[JavaField] = field(default_factory=list)
    methods: List[JavaMethod] = field(default_factory=list)
    inner_classes: List['JavaClass'] = field(default_factory=list)
    
    def to_code(self) -> str:
        """Generate complete Java class code."""
        parts = []
        
        # Package declaration
        parts.append(f"package {self.package};")
        parts.append("")
        
        # Imports
        if self.imports:
            for imp in sorted(set(self.imports)):
                parts.append(f"import {imp};")
            parts.append("")
        
        # Class annotations
        if self.annotations:
            for ann in self.annotations:
                parts.append(ann)
        
        # Class declaration
        class_decl = f"public {self.class_type.value} {self.name}"
        
        if self.extends:
            class_decl += f" extends {self.extends}"
        
        if self.implements:
            class_decl += f" implements {', '.join(self.implements)}"
        
        class_decl += " {"
        parts.append(class_decl)
        
        # Fields
        if self.fields:
            parts.append("")
            for field_obj in self.fields:
                parts.append(field_obj.to_code())
        
        # Methods
        if self.methods:
            parts.append("")
            for method in self.methods:
                parts.append(method.to_code())
                parts.append("")
        
        # Inner classes
        if self.inner_classes:
            for inner in self.inner_classes:
                inner_code = inner.to_code()
                # Indent inner class
                indented = "\n".join(f"    {line}" if line.strip() else "" for line in inner_code.split("\n"))
                parts.append(indented)
                parts.append("")
        
        parts.append("}")
        
        return "\n".join(parts)
    
    def get_file_path(self) -> str:
        """Get relative file path for this class."""
        package_path = self.package.replace(".", "/")
        return f"{package_path}/{self.name}.java"


@dataclass
class MavenProject:
    """Domain model representing Maven project configuration."""
    group_id: str = "com.automation"
    artifact_id: str = "karate-tests"
    version: str = "1.0.0"
    name: str = "Karate API Tests"
    description: str = "Automated API tests using Karate framework"
    java_version: str = "11"
    karate_version: str = "1.4.1"
    junit_version: str = "5.9.3"
    additional_dependencies: List[Dict[str, str]] = field(default_factory=list)
    
    def get_dependencies(self) -> List[Dict[str, str]]:
        """Get all project dependencies."""
        deps = [
            {
                "groupId": "com.intuit.karate",
                "artifactId": "karate-junit5",
                "version": self.karate_version,
                "scope": "test"
            },
            {
                "groupId": "org.junit.jupiter",
                "artifactId": "junit-jupiter-api",
                "version": self.junit_version,
                "scope": "test"
            }
        ]
        
        if self.additional_dependencies:
            deps.extend(self.additional_dependencies)
        
        return deps


@dataclass
class FeatureFile:
    """Domain model representing a Karate feature file."""
    name: str
    path: str  # Relative path in resources
    content: str
    tags: List[str] = field(default_factory=list)


@dataclass
class ProjectConfig:
    """Domain model for project configuration."""
    base_url: str
    environments: Dict[str, Dict[str, str]] = field(default_factory=dict)
    timeout: int = 30000
    retry_count: int = 0
    parallel_execution: bool = False
    threads: int = 1
    
    def get_karate_config_js(self) -> str:
        """Generate karate-config.js content."""
        env_configs = []
        
        for env_name, env_props in self.environments.items():
            env_block = f"""  if (env === '{env_name}') {{"""
            for key, value in env_props.items():
                env_block += f"\n    config.{key} = '{value}';"
            env_block += "\n  }"
            env_configs.append(env_block)
        
        env_config_str = " else ".join(env_configs) if env_configs else ""
        
        return f"""function fn() {{
  var env = karate.env || 'dev';
  karate.log('karate.env:', env);
  
  var config = {{
    baseUrl: '{self.base_url}',
    timeout: {self.timeout},
    retryCount: {self.retry_count}
  }};
  
{env_config_str}
  
  return config;
}}"""


@dataclass
class KarateJavaProject:
    """
    Aggregate root for Karate Java project.
    Represents the complete project structure.
    
    Following DDD:
    - Aggregate Root: Ensures consistency
    - Value Objects: MavenProject, ProjectConfig
    - Entities: JavaClass, FeatureFile
    """
    maven_config: MavenProject
    project_config: ProjectConfig
    test_runners: List[JavaClass] = field(default_factory=list)
    hooks: List[JavaClass] = field(default_factory=list)
    config_classes: List[JavaClass] = field(default_factory=list)
    utils: List[JavaClass] = field(default_factory=list)
    features: List[FeatureFile] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_total_classes(self) -> int:
        """Get total number of Java classes."""
        return (
            len(self.test_runners) +
            len(self.hooks) +
            len(self.config_classes) +
            len(self.utils)
        )
    
    def get_total_features(self) -> int:
        """Get total number of feature files."""
        return len(self.features)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get project summary."""
        return {
            "project_name": self.maven_config.artifact_id,
            "total_java_classes": self.get_total_classes(),
            "total_features": self.get_total_features(),
            "test_runners": len(self.test_runners),
            "hooks": len(self.hooks),
            "config_classes": len(self.config_classes),
            "utils": len(self.utils),
            "base_url": self.project_config.base_url,
            "java_version": self.maven_config.java_version,
            "karate_version": self.maven_config.karate_version
        }
