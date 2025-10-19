"""
PostgreSQL Database Adapter.

This module implements the IDatabaseAdapter interface for PostgreSQL databases
using asyncpg for async operations.
"""

import re
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict, Any
from ...domain.repositories import IDatabaseAdapter
from ...domain.models import (
    DatabaseConnection,
    QueryResult,
    QueryValidationResult,
    ColumnMetadata,
    DatabaseType
)


class PostgresAdapter(IDatabaseAdapter):
    """
    PostgreSQL database adapter implementation using asyncpg.
    
    Provides secure, read-only query execution with validation and timeout support.
    """
    
    # Dangerous SQL operations that must be blocked
    WRITE_OPERATIONS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'MERGE',
        'REPLACE', 'RENAME', 'COMMENT', 'VACUUM'
    }
    
    # Allowed read operations
    READ_OPERATIONS = {'SELECT', 'WITH', 'SHOW', 'EXPLAIN', 'DESCRIBE'}
    
    def __init__(self, connection: DatabaseConnection):
        """
        Initialize PostgreSQL adapter.
        
        Args:
            connection: Database connection configuration
        """
        super().__init__(connection)
        self._connection_pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> bool:
        """
        Establish connection pool to PostgreSQL database.
        
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Build connection parameters
            if self.connection.connection_string:
                # Use connection string directly
                self._connection_pool = await asyncpg.create_pool(
                    self.connection.connection_string,
                    min_size=1,
                    max_size=5,
                    command_timeout=60,
                    **self.connection.options
                )
            else:
                # Use individual parameters
                self._connection_pool = await asyncpg.create_pool(
                    host=self.connection.host,
                    port=self.connection.port or 5432,
                    database=self.connection.database,
                    user=self.connection.username,
                    password=self.connection.password,
                    min_size=1,
                    max_size=5,
                    command_timeout=60,
                    **self.connection.options
                )
            
            self._is_connected = True
            return True
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close connection pool and clean up resources."""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
            self._is_connected = False
    
    async def execute_query(self, query: str, timeout: int = 30, max_rows: int = 1000) -> QueryResult:
        """
        Execute a read-only SQL query.
        
        Args:
            query: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
            
        Returns:
            QueryResult with rows, columns, and metadata
            
        Raises:
            ValueError: If query is not read-only
            TimeoutError: If query exceeds timeout
            ConnectionError: If not connected
        """
        if not self._is_connected or not self._connection_pool:
            raise ConnectionError("Not connected to database. Call connect() first.")
        
        # Validate query first
        validation = self.validate_query(query)
        if not validation.is_valid or not validation.is_read_only:
            errors = "; ".join(validation.errors)
            raise ValueError(f"Query validation failed: {errors}")
        
        start_time = datetime.now()
        
        try:
            async with self._connection_pool.acquire() as conn:
                # Set statement timeout
                await conn.execute(f'SET statement_timeout = {timeout * 1000}')
                
                # Execute query with row limit
                limited_query = self._add_limit_to_query(query, max_rows + 1)
                records = await conn.fetch(limited_query)
                
                # Check if results were truncated
                truncated = len(records) > max_rows
                if truncated:
                    records = records[:max_rows]
                
                # Get column metadata
                columns = self._extract_column_metadata(records)
                
                # Convert records to list of dicts
                rows = [dict(record) for record in records]
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return QueryResult(
                    rows=rows,
                    columns=columns,
                    row_count=len(rows),
                    execution_time=execution_time,
                    query=query,
                    timestamp=start_time,
                    database_type=DatabaseType.POSTGRES.value,
                    truncated=truncated
                )
                
        except asyncpg.QueryCanceledError:
            raise TimeoutError(f"Query exceeded timeout of {timeout} seconds")
        except asyncpg.PostgresError as e:
            raise Exception(f"PostgreSQL error: {e.message}")
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        Validate SQL query for safety and correctness.
        
        Args:
            query: SQL query to validate
            
        Returns:
            QueryValidationResult with validation status
        """
        errors = []
        warnings = []
        detected_operations = []
        
        if not query or not query.strip():
            errors.append("Query cannot be empty")
            return QueryValidationResult(
                is_valid=False,
                is_read_only=False,
                errors=errors,
                warnings=warnings,
                detected_operations=detected_operations
            )
        
        # Normalize query for analysis
        normalized_query = self._normalize_query(query)
        
        # Extract SQL operations
        detected_operations = self._extract_operations(normalized_query)
        
        # Check for write operations
        write_ops_found = set(detected_operations) & self.WRITE_OPERATIONS
        if write_ops_found:
            errors.append(f"Write operations not allowed: {', '.join(write_ops_found)}")
        
        # Check for dangerous patterns
        dangerous_patterns = self._check_dangerous_patterns(normalized_query)
        if dangerous_patterns:
            errors.append(f"Dangerous patterns detected: {', '.join(dangerous_patterns)}")
        
        # Check if it's a read-only query
        read_ops_found = set(detected_operations) & self.READ_OPERATIONS
        is_read_only = bool(read_ops_found) and not write_ops_found and not dangerous_patterns
        
        # Warnings for complex queries
        if ';' in normalized_query:
            warnings.append("Multiple statements detected. Only the first statement will be executed.")
        
        if len(normalized_query) > 10000:
            warnings.append("Query is very long. Consider simplifying.")
        
        is_valid = len(errors) == 0
        
        return QueryValidationResult(
            is_valid=is_valid,
            is_read_only=is_read_only,
            errors=errors,
            warnings=warnings,
            detected_operations=detected_operations
        )
    
    async def test_connection(self) -> bool:
        """
        Test database connection without executing queries.
        
        Returns:
            True if connection is healthy
        """
        if not self._is_connected or not self._connection_pool:
            return False
        
        try:
            async with self._connection_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception:
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get safe connection information.
        
        Returns:
            Dictionary with connection details (no passwords)
        """
        return {
            "database_type": DatabaseType.POSTGRES.value,
            "host": self.connection.host or "from_connection_string",
            "port": self.connection.port or 5432,
            "database": self.connection.database or "from_connection_string",
            "username": self.connection.username or "from_connection_string",
            "is_connected": self._is_connected,
            "pool_size": self._connection_pool.get_size() if self._connection_pool else 0
        }
    
    # ======================== Helper Methods ========================
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for analysis (uppercase, remove comments)."""
        # Remove SQL comments
        query = re.sub(r'--[^\n]*', '', query)  # Single-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)  # Multi-line comments
        
        # Convert to uppercase for analysis
        return query.upper().strip()
    
    def _extract_operations(self, normalized_query: str) -> List[str]:
        """Extract SQL operations from query."""
        operations = []
        
        # Find all SQL keywords at the beginning of statements
        pattern = r'\b(' + '|'.join(self.READ_OPERATIONS | self.WRITE_OPERATIONS) + r')\b'
        matches = re.findall(pattern, normalized_query)
        
        return list(set(matches))
    
    def _check_dangerous_patterns(self, normalized_query: str) -> List[str]:
        """Check for dangerous SQL patterns."""
        dangerous = []
        
        # Check for semicolons (multiple statements)
        if normalized_query.count(';') > 1:
            dangerous.append("multiple_statements")
        
        # Check for INTO clause (could be SELECT INTO)
        if ' INTO ' in normalized_query and 'SELECT' in normalized_query:
            dangerous.append("select_into")
        
        # Check for stored procedure execution
        if any(keyword in normalized_query for keyword in ['EXEC ', 'EXECUTE ', 'CALL ']):
            dangerous.append("procedure_execution")
        
        return dangerous
    
    def _add_limit_to_query(self, query: str, limit: int) -> str:
        """Add LIMIT clause to query if not present."""
        normalized = query.upper().strip()
        
        # Check if query already has LIMIT
        if 'LIMIT' in normalized:
            return query
        
        # Add LIMIT at the end
        return f"{query.rstrip(';')} LIMIT {limit}"
    
    def _extract_column_metadata(self, records: List[asyncpg.Record]) -> List[ColumnMetadata]:
        """Extract column metadata from query results."""
        if not records:
            return []
        
        columns = []
        first_record = records[0]
        
        for key in first_record.keys():
            value = first_record[key]
            
            # Determine data type
            data_type = type(value).__name__ if value is not None else "unknown"
            
            columns.append(ColumnMetadata(
                name=key,
                data_type=data_type,
                nullable=True  # asyncpg doesn't provide this info easily
            ))
        
        return columns
