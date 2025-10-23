"""
Database Query Configuration.

Centralizes default connection parameters for database operations.
This allows easy configuration without changing business logic.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseDefaults:
    """
    Default database connection parameters.
    
    These values are used when not explicitly provided in the query request.
    Modify these values to match your environment.
    """
    # PostgreSQL defaults
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DATABASE: str = "quality"
    POSTGRES_USERNAME: str = "postgres"
    POSTGRES_PASSWORD: str = "Quality"
    
    # MySQL defaults (for future use)
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: Optional[str] = None
    MYSQL_USERNAME: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    
    # SQL Server defaults (for future use)
    SQLSERVER_HOST: str = "localhost"
    SQLSERVER_PORT: int = 1433
    SQLSERVER_DATABASE: Optional[str] = None
    SQLSERVER_USERNAME: Optional[str] = None
    SQLSERVER_PASSWORD: Optional[str] = None
    
    def get_defaults_for_db_type(self, db_type: str) -> dict:
        """
        Get default connection parameters for a specific database type.
        
        Args:
            db_type: Database type (postgres, mysql, sqlserver, etc.)
            
        Returns:
            Dictionary with default connection parameters
        """
        db_type_lower = db_type.lower()
        
        if db_type_lower == "postgres":
            return {
                "host": self.POSTGRES_HOST,
                "port": self.POSTGRES_PORT,
                "database": self.POSTGRES_DATABASE,
                "username": self.POSTGRES_USERNAME,
                "password": self.POSTGRES_PASSWORD
            }
        elif db_type_lower == "mysql":
            return {
                "host": self.MYSQL_HOST,
                "port": self.MYSQL_PORT,
                "database": self.MYSQL_DATABASE,
                "username": self.MYSQL_USERNAME,
                "password": self.MYSQL_PASSWORD
            }
        elif db_type_lower == "sqlserver":
            return {
                "host": self.SQLSERVER_HOST,
                "port": self.SQLSERVER_PORT,
                "database": self.SQLSERVER_DATABASE,
                "username": self.SQLSERVER_USERNAME,
                "password": self.SQLSERVER_PASSWORD
            }
        else:
            return {}


# Global instance for easy access
DB_DEFAULTS = DatabaseDefaults()
