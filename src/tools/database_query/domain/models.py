"""
Domain Models for Database Query Tool.

This module defines the core domain models for database query operations,
following Domain-Driven Design principles.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from .config import DB_DEFAULTS


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class QueryType(Enum):
    """Allowed query types (read-only operations)."""
    SELECT = "SELECT"
    WITH = "WITH"  # Common Table Expressions


@dataclass
class DatabaseConnection:
    """
    Database connection configuration.
    
    Attributes:
        db_type: Type of database engine
        host: Database host
        port: Database port
        database: Database name
        username: Database username
        password: Database password
        connection_string: Full connection string (alternative to individual params)
        options: Additional connection options
    """
    db_type: DatabaseType
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate connection parameters and apply defaults."""
        # Apply defaults if values not provided and no connection string
        if not self.connection_string:
            defaults = DB_DEFAULTS.get_defaults_for_db_type(self.db_type.value)
            
            if self.host is None:
                self.host = defaults.get("host")
            if self.port is None:
                self.port = defaults.get("port")
            if self.database is None:
                self.database = defaults.get("database")
            if self.username is None:
                self.username = defaults.get("username")
            if self.password is None:
                self.password = defaults.get("password")
        
        # Validate that we have minimum required connection info
        if not self.connection_string and not (self.host and self.database):
            raise ValueError("Either connection_string or host/database must be provided")
    
    def get_safe_summary(self) -> Dict[str, Any]:
        """Get connection summary without sensitive data."""
        return {
            "db_type": self.db_type.value,
            "host": self.host or "from_connection_string",
            "port": self.port,
            "database": self.database or "from_connection_string",
            "username": self.username or "from_connection_string",
            "has_password": bool(self.password),
            "has_connection_string": bool(self.connection_string)
        }


@dataclass
class QueryRequest:
    """
    Query execution request.
    
    Attributes:
        query: SQL query to execute
        connection: Database connection configuration
        timeout: Query timeout in seconds
        max_rows: Maximum number of rows to return
        output_format: Desired output format (json, csv, markdown, table)
        include_metadata: Include column metadata in response
    """
    query: str
    connection: DatabaseConnection
    timeout: int = 30
    max_rows: int = 1000
    output_format: str = "json"
    include_metadata: bool = True
    
    def __post_init__(self):
        """Validate query request."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.max_rows <= 0:
            raise ValueError("Max rows must be positive")
        
        if self.output_format not in ["json", "csv", "markdown", "table"]:
            raise ValueError(f"Invalid output format: {self.output_format}")


@dataclass
class ColumnMetadata:
    """
    Metadata for a result column.
    
    Attributes:
        name: Column name
        data_type: Column data type
        nullable: Whether column accepts NULL values
        precision: Numeric precision (if applicable)
        scale: Numeric scale (if applicable)
    """
    name: str
    data_type: str
    nullable: bool = True
    precision: Optional[int] = None
    scale: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "nullable": self.nullable,
            "precision": self.precision,
            "scale": self.scale
        }


@dataclass
class QueryResult:
    """
    Result of query execution.
    
    Attributes:
        rows: Query result rows
        columns: Column metadata
        row_count: Number of rows returned
        execution_time: Query execution time in seconds
        query: Original query executed
        timestamp: Execution timestamp
        database_type: Database type used
        truncated: Whether results were truncated due to max_rows limit
    """
    rows: List[Dict[str, Any]]
    columns: List[ColumnMetadata]
    row_count: int
    execution_time: float
    query: str
    timestamp: datetime
    database_type: str
    truncated: bool = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "row_count": self.row_count,
            "column_count": len(self.columns),
            "execution_time_seconds": round(self.execution_time, 4),
            "timestamp": self.timestamp.isoformat(),
            "database_type": self.database_type,
            "truncated": self.truncated,
            "query_preview": self.query[:100] + "..." if len(self.query) > 100 else self.query
        }
    
    def to_dict(self, include_rows: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "summary": self.get_summary(),
            "columns": [col.to_dict() for col in self.columns]
        }
        
        if include_rows:
            result["rows"] = self.rows
        
        return result
    
    def to_csv(self) -> str:
        """Convert results to CSV format."""
        if not self.rows:
            return ""
        
        # Header
        csv_lines = [",".join(col.name for col in self.columns)]
        
        # Rows
        for row in self.rows:
            csv_lines.append(",".join(str(row.get(col.name, "")) for col in self.columns))
        
        return "\n".join(csv_lines)
    
    def to_markdown(self) -> str:
        """Convert results to Markdown table format."""
        if not self.rows:
            return "No results"
        
        # Header
        header = "| " + " | ".join(col.name for col in self.columns) + " |"
        separator = "| " + " | ".join("---" for _ in self.columns) + " |"
        
        # Rows
        rows = []
        for row in self.rows:
            row_str = "| " + " | ".join(str(row.get(col.name, "")) for col in self.columns) + " |"
            rows.append(row_str)
        
        return "\n".join([header, separator] + rows)


@dataclass
class QueryValidationResult:
    """
    Result of query validation.
    
    Attributes:
        is_valid: Whether query is valid
        is_read_only: Whether query is read-only (SELECT, WITH)
        errors: List of validation errors
        warnings: List of validation warnings
        detected_operations: SQL operations detected in query
    """
    is_valid: bool
    is_read_only: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detected_operations: List[str] = field(default_factory=list)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "is_valid": self.is_valid,
            "is_read_only": self.is_read_only,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "detected_operations": self.detected_operations
        }
