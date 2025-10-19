"""
Database Adapter Interface.

This module defines the abstract interface for database adapters,
following the Repository and Adapter patterns.
"""

from abc import ABC, abstractmethod
from typing import Optional
from .models import QueryResult, QueryValidationResult, DatabaseConnection


class IDatabaseAdapter(ABC):
    """
    Abstract interface for database adapters.
    
    This interface defines the contract that all database adapters must implement,
    following the Dependency Inversion Principle (SOLID).
    """
    
    def __init__(self, connection: DatabaseConnection):
        """
        Initialize adapter with connection configuration.
        
        Args:
            connection: Database connection configuration
        """
        self.connection = connection
        self._connection_pool: Optional[any] = None
        self._is_connected: bool = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close database connection and clean up resources.
        
        This method should be called when the adapter is no longer needed
        to properly release database resources.
        """
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, timeout: int = 30, max_rows: int = 1000) -> QueryResult:
        """
        Execute a read-only SQL query.
        
        Args:
            query: SQL query to execute (SELECT, WITH, etc.)
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
            
        Returns:
            QueryResult with rows, columns, and metadata
            
        Raises:
            ValueError: If query is not read-only
            TimeoutError: If query exceeds timeout
            Exception: For other database errors
        """
        pass
    
    @abstractmethod
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        Validate SQL query for safety and correctness.
        
        This method ensures:
        - Query is read-only (SELECT, WITH allowed)
        - No write operations (INSERT, UPDATE, DELETE, DROP, etc.)
        - No dangerous operations (TRUNCATE, ALTER, CREATE, etc.)
        - Query syntax is valid
        
        Args:
            query: SQL query to validate
            
        Returns:
            QueryValidationResult with validation status and messages
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test database connection without executing queries.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_connection_info(self) -> dict:
        """
        Get safe connection information (without sensitive data).
        
        Returns:
            Dictionary with connection details (no passwords)
        """
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is currently connected."""
        return self._is_connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
