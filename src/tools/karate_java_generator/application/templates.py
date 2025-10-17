"""
Templates for generating Java, Maven, and Karate configuration files.
Following Template Method Pattern and SRP.
"""

from typing import List, Dict, Any
from ..domain.models import MavenProject, ProjectConfig


class JavaTemplates:
    """Templates for Java code generation."""
    
    @staticmethod
    def test_runner_class(
        package: str,
        class_name: str,
        feature_path: str,
        tags: List[str] = None
    ) -> str:
        """
        Generate a Karate test runner class.
        
        Args:
            package: Java package name
            class_name: Name of the test class
            feature_path: Path to feature file
            tags: Optional tags to filter tests
        """
        tags_line = f'.tags("{", ".join(f"@{tag}" for tag in tags)}")' if tags else ""
        
        return f"""package {package};

import com.intuit.karate.junit5.Karate;

/**
 * Test runner for {class_name}.
 * Generated automatically by MCP-ALAIIA.
 */
public class {class_name} {{
    
    @Karate.Test
    Karate test() {{
        return Karate.run("classpath:{feature_path}")
                {tags_line}
                .relativeTo(getClass());
    }}
}}"""
    
    @staticmethod
    def parallel_runner_class(package: str, threads: int = 5) -> str:
        """Generate parallel test runner."""
        return f"""package {package};

import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

/**
 * Parallel test runner for executing all tests.
 * Generated automatically by MCP-ALAIIA.
 */
public class ParallelTestRunner {{
    
    @Test
    void testParallel() {{
        Results results = Runner.path("classpath:features")
                .parallel({threads});
        assertEquals(0, results.getFailCount(), results.getErrorMessages());
    }}
}}"""
    
    @staticmethod
    def test_hooks_class(package: str) -> str:
        """Generate test hooks class - simplified and compatible."""
        return f"""package {package};

import com.intuit.karate.RuntimeHook;
import com.intuit.karate.core.ScenarioRuntime;
import com.intuit.karate.Suite;

/**
 * Global test hooks for before/after suite and scenario execution.
 * Generated automatically by MCP-ALAIIA.
 * 
 * Note: This is a simplified implementation compatible with Karate 1.4.1
 */
public class TestHooks implements RuntimeHook {{
    
    @Override
    public void beforeSuite(Suite suite) {{
        System.out.println("=================================");
        System.out.println("Starting Test Suite Execution");
        System.out.println("=================================");
    }}
    
    @Override
    public void afterSuite(Suite suite) {{
        System.out.println("=================================");
        System.out.println("Test Suite Execution Completed");
        System.out.println("=================================");
    }}
    
    @Override
    public boolean beforeScenario(ScenarioRuntime sr) {{
        System.out.println(">> Starting Scenario: " + sr.scenario.getName());
        return true;
    }}
    
    @Override
    public void afterScenario(ScenarioRuntime sr) {{
        System.out.println("<< Completed Scenario: " + sr.scenario.getName());
        if (sr.result.isFailed()) {{
            System.err.println("   [FAILED] " + sr.result.getErrorMessage());
        }} else {{
            System.out.println("   [PASSED]");
        }}
    }}
}}"""
    
    @staticmethod
    def test_config_class(package: str) -> str:
        """Generate test configuration class."""
        return f"""package {package};

import java.util.HashMap;
import java.util.Map;

/**
 * Test configuration and shared utilities.
 * Generated automatically by MCP-ALAIIA.
 */
public class TestConfig {{
    
    private static final Map<String, String> config = new HashMap<>();
    
    static {{
        // Load configuration from system properties or environment
        config.put("env", System.getProperty("karate.env", "dev"));
    }}
    
    public static String getEnv() {{
        return config.get("env");
    }}
    
    public static String getProperty(String key) {{
        return config.get(key);
    }}
    
    public static void setProperty(String key, String value) {{
        config.put(key, value);
    }}
}}"""
    
    @staticmethod
    def api_helper_class(package: str) -> str:
        """Generate API helper utilities."""
        return f"""package {package};

import java.util.UUID;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Helper utilities for API testing.
 * Generated automatically by MCP-ALAIIA.
 */
public class ApiHelper {{
    
    /**
     * Generate a random UUID.
     */
    public static String generateUUID() {{
        return UUID.randomUUID().toString();
    }}
    
    /**
     * Get current timestamp in ISO format.
     */
    public static String getCurrentTimestamp() {{
        return LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME);
    }}
    
    /**
     * Generate random string of specified length.
     */
    public static String randomString(int length) {{
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {{
            int index = (int) (Math.random() * chars.length());
            sb.append(chars.charAt(index));
        }}
        return sb.toString();
    }}
    
    /**
     * Generate random integer between min and max.
     */
    public static int randomInt(int min, int max) {{
        return (int) (Math.random() * (max - min + 1)) + min;
    }}
}}"""
    
    @staticmethod
    def data_generator_class(package: str) -> str:
        """Generate test data generator class."""
        return f"""package {package};

import java.util.HashMap;
import java.util.Map;

/**
 * Test data generator for common test scenarios.
 * Generated automatically by MCP-ALAIIA.
 */
public class DataGenerator {{
    
    /**
     * Generate sample request headers.
     */
    public static Map<String, String> getSampleHeaders() {{
        Map<String, String> headers = new HashMap<>();
        headers.put("Content-Type", "application/json");
        headers.put("Accept", "application/json");
        headers.put("x-correlation-id", ApiHelper.generateUUID());
        headers.put("x-request-id", ApiHelper.generateUUID());
        return headers;
    }}
    
    /**
     * Generate sample request body.
     */
    public static Map<String, Object> getSampleRequestBody() {{
        Map<String, Object> body = new HashMap<>();
        body.put("name", "Test " + ApiHelper.randomString(5));
        body.put("description", "Generated test data");
        body.put("timestamp", ApiHelper.getCurrentTimestamp());
        return body;
    }}
}}"""


class MavenTemplates:
    """Templates for Maven configuration files."""
    
    @staticmethod
    def pom_xml(config: MavenProject) -> str:
        """Generate pom.xml content."""
        # Generate dependencies XML
        deps_xml = []
        for dep in config.get_dependencies():
            dep_xml = f"""        <dependency>
            <groupId>{dep['groupId']}</groupId>
            <artifactId>{dep['artifactId']}</artifactId>
            <version>{dep['version']}</version>"""
            
            if 'scope' in dep:
                dep_xml += f"\n            <scope>{dep['scope']}</scope>"
            
            dep_xml += "\n        </dependency>"
            deps_xml.append(dep_xml)
        
        dependencies_section = "\n".join(deps_xml)
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{config.group_id}</groupId>
    <artifactId>{config.artifact_id}</artifactId>
    <version>{config.version}</version>
    <packaging>jar</packaging>

    <name>{config.name}</name>
    <description>{config.description}</description>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <java.version>{config.java_version}</java.version>
        <maven.compiler.source>{config.java_version}</maven.compiler.source>
        <maven.compiler.target>{config.java_version}</maven.compiler.target>
        <maven.compiler.release>{config.java_version}</maven.compiler.release>
        <karate.version>{config.karate_version}</karate.version>
        <junit.version>{config.junit_version}</junit.version>
    </properties>

    <dependencies>
{dependencies_section}
    </dependencies>

    <build>
        <testResources>
            <testResource>
                <directory>src/test/resources</directory>
                <filtering>false</filtering>
            </testResource>
        </testResources>
        
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <encoding>UTF-8</encoding>
                    <source>${{java.version}}</source>
                    <target>${{java.version}}</target>
                    <compilerArgs>
                        <arg>-parameters</arg>
                    </compilerArgs>
                </configuration>
            </plugin>
            
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.0.0-M9</version>
                <configuration>
                    <argLine>-Dfile.encoding=UTF-8</argLine>
                    <includes>
                        <include>**/*Test.java</include>
                        <include>**/Test*.java</include>
                        <include>**/*Runner.java</include>
                    </includes>
                    <systemPropertyVariables>
                        <karate.env>${{karate.env}}</karate.env>
                    </systemPropertyVariables>
                    <testFailureIgnore>false</testFailureIgnore>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>"""


class KarateTemplates:
    """Templates for Karate-specific configuration files."""
    
    @staticmethod
    def karate_config_js(config: ProjectConfig) -> str:
        """Generate karate-config.js content."""
        return config.get_karate_config_js()
    
    @staticmethod
    def logback_xml() -> str:
        """Generate logback-test.xml configuration."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
  
    <appender name="FILE" class="ch.qos.logback.core.FileAppender">
        <file>target/karate.log</file>
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <logger name="com.intuit.karate" level="INFO"/>
    
    <root level="INFO">
        <appender-ref ref="STDOUT" />
        <appender-ref ref="FILE" />
    </root>
    
</configuration>"""
    
    @staticmethod
    def gitignore() -> str:
        """Generate .gitignore file."""
        return """# Maven
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties

# IDE
.idea/
*.iml
.project
.classpath
.settings/
*.swp
*.bak
*~

# Karate
*.log
karate-reports/

# OS
.DS_Store
Thumbs.db"""
    
    @staticmethod
    def readme(project_name: str, base_url: str, features_count: int) -> str:
        """Generate README.md content."""
        return f"""# {project_name}

Automated API tests using Karate framework.
Generated automatically by MCP-ALAIIA.

## 📋 Overview

- **Base URL:** `{base_url}`
- **Total Features:** {features_count}
- **Framework:** Karate DSL with JUnit5
- **Build Tool:** Maven

## 🚀 Quick Start

### Prerequisites

- Java 11 or higher
- Maven 3.6+

### Running Tests

```bash
# Run all tests
mvn test

# Run specific environment
mvn test -Dkarate.env=qa

# Run with parallel execution
mvn test -Dkarate.options="--threads 5"

# Run specific tags
mvn test -Dkarate.options="--tags @smoke"
```

## 📁 Project Structure

```
src/
├── test/
│   ├── java/
│   │   └── com/automation/
│   │       ├── runners/          # Test runners
│   │       ├── hooks/            # Before/After hooks
│   │       ├── config/           # Configuration classes
│   │       └── utils/            # Helper utilities
│   └── resources/
│       ├── features/             # Karate feature files
│       ├── data/                 # Test data
│       ├── config/               # Environment configs
│       ├── karate-config.js      # Karate configuration
│       └── logback-test.xml      # Logging configuration
```

## 🔧 Configuration

### Environments

Configure different environments in `src/test/resources/config/`:
- `dev.properties` - Development
- `qa.properties` - QA/Staging
- `prod.properties` - Production

### Karate Config

Global configuration in `karate-config.js`:
- Base URL per environment
- Timeout settings
- Retry configuration

## 📊 Reports

After test execution, reports are generated in:
- `target/karate-reports/karate-summary.html` - HTML report
- `target/karate.log` - Execution log

## 🧪 Test Features

Features are organized by functionality in `src/test/resources/features/`.
Each feature includes:
- Success scenarios
- Error handling scenarios
- Edge cases

## 🔍 Debugging

Enable debug mode:
```bash
mvn test -Dkarate.options="--threads 1" -Dlogback.configurationFile=logback-debug.xml
```

## 📝 Notes

- All test data is located in `src/test/resources/data/`
- Helper utilities available in `com.automation.utils`
- Custom hooks in `com.automation.hooks`

## 🤝 Contributing

Generated automatically. Customize as needed for your project.

---

Generated by **MCP-ALAIIA** - AI-Powered API Test Generation
"""
