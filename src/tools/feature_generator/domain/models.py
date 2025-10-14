"""Domain models for feature generation."""
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class FeatureScenario:
    """Represents a single test scenario in a feature file."""
    name: str
    description: Optional[str]
    given_steps: List[str]
    when_steps: List[str]
    then_steps: List[str]
    examples: Optional[Dict[str, List[str]]] = None


@dataclass
class FeatureFile:
    """Represents a complete feature file."""
    feature_name: str
    description: str
    background_steps: List[str]
    scenarios: List[FeatureScenario]
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class FeatureGenerationResult:
    """Result of feature generation process."""
    features: List[FeatureFile]
    base_url: str
    total_scenarios: int
    
    def get_feature_content(self, feature: FeatureFile) -> str:
        """Generate the actual .feature file content."""
        content_lines = []
        
        # Add tags if any
        if feature.tags:
            content_lines.append(f"@{' @'.join(feature.tags)}")
        
        # Add feature header
        content_lines.append(f"Feature: {feature.feature_name}")
        
        if feature.description:
            content_lines.append(f"  {feature.description}")
        
        content_lines.append("")
        
        # Add background if any
        if feature.background_steps:
            content_lines.append("  Background:")
            for step in feature.background_steps:
                content_lines.append(f"    {step}")
            content_lines.append("")
        
        # Add scenarios
        for scenario in feature.scenarios:
            if scenario.description:
                content_lines.append(f"  # {scenario.description}")
            
            content_lines.append(f"  Scenario: {scenario.name}")
            
            # Given steps
            for step in scenario.given_steps:
                content_lines.append(f"    Given {step}")
            
            # When steps
            for step in scenario.when_steps:
                content_lines.append(f"    When {step}")
            
            # Then steps
            for step in scenario.then_steps:
                content_lines.append(f"    Then {step}")
            
            # Examples if any
            if scenario.examples:
                content_lines.append("    Examples:")
                headers = list(scenario.examples.keys())
                content_lines.append(f"      | {' | '.join(headers)} |")
                
                # Assuming all lists have the same length
                if headers and scenario.examples[headers[0]]:
                    for i in range(len(scenario.examples[headers[0]])):
                        row = [str(scenario.examples[header][i]) for header in headers]
                        content_lines.append(f"      | {' | '.join(row)} |")
            
            content_lines.append("")
        
        return "\n".join(content_lines)