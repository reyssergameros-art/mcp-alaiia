"""
Database Adapter Factory.

This module implements the Factory pattern to create database adapters
based on the database type.
"""

from typing import Dict, Type
from ...domain.repositories import IDatabaseAdapter
from ...domain.models import DatabaseConnection, DatabaseType
from .postgres_adapter import PostgresAdapter


class DatabaseAdapterFactory:
    """
    Factory for creating database adapters.
    
    Follows the Factory and Strategy patterns to instantiate the appropriate
    database adapter based on the database type.
    """
    
    # Registry of available adapters
    _adapters: Dict[DatabaseType, Type[IDatabaseAdapter]] = {
        DatabaseType.POSTGRES: PostgresAdapter,
        # Future adapters can be registered here:
        # DatabaseType.MYSQL: MySQLAdapter,
        # DatabaseType.SQLSERVER: SQLServerAdapter,
        # DatabaseType.SQLITE: SQLiteAdapter,
    }
    
    @classmethod
    def create_adapter(cls, connection: DatabaseConnection) -> IDatabaseAdapter:
        """
        Create a database adapter instance.
        
        Args:
            connection: Database connection configuration
            
        Returns:
            IDatabaseAdapter instance for the specified database type
            
        Raises:
            ValueError: If database type is not supported
        """
        if connection.db_type not in cls._adapters:
            supported_types = ', '.join([db.value for db in cls._adapters.keys()])
            raise ValueError(
                f"Database type '{connection.db_type.value}' is not supported. "
                f"Supported types: {supported_types}"
            )
        
        adapter_class = cls._adapters[connection.db_type]
        return adapter_class(connection)
    
    @classmethod
    def register_adapter(cls, db_type: DatabaseType, adapter_class: Type[IDatabaseAdapter]) -> None:
        """
        Register a new database adapter.
        
        This allows for runtime extension of supported database types,
        following the Open/Closed Principle (SOLID).
        
        Args:
            db_type: Database type enum
            adapter_class: Adapter class that implements IDatabaseAdapter
            
        Raises:
            TypeError: If adapter_class doesn't implement IDatabaseAdapter
        """
        if not issubclass(adapter_class, IDatabaseAdapter):
            raise TypeError(
                f"Adapter class must implement IDatabaseAdapter interface. "
                f"Got: {adapter_class.__name__}"
            )
        
        cls._adapters[db_type] = adapter_class
    
    @classmethod
    def get_supported_databases(cls) -> list[str]:
        """
        Get list of supported database types.
        
        Returns:
            List of supported database type names
        """
        return [db.value for db in cls._adapters.keys()]
    
    @classmethod
    def is_supported(cls, db_type: DatabaseType) -> bool:
        """
        Check if a database type is supported.
        
        Args:
            db_type: Database type to check
            
        Returns:
            True if supported, False otherwise
        """
        return db_type in cls._adapters
