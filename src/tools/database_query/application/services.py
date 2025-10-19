"""
Database Query Service.

This module implements the application service layer for database query operations,
orchestrating validation, connection, execution, and result formatting.
"""

import json
from typing import Dict, Any, Optional
from ..domain.models import QueryRequest, QueryResult, QueryValidationResult, DatabaseConnection
from ..domain.repositories import IDatabaseAdapter
from ..infrastructure.adapters.factory import DatabaseAdapterFactory


class DatabaseQueryService:
    """
    Application service for database query operations.
    
    Orchestrates the complete flow of query execution:
    1. Validation
    2. Connection establishment
    3. Query execution
    4. Result formatting
    5. Resource cleanup
    """
    
    def __init__(self):
        """Initialize the database query service."""
        self._adapters: Dict[str, IDatabaseAdapter] = {}
    
    async def execute_query(self, request: QueryRequest) -> Dict[str, Any]:
        """
        Execute a database query with full orchestration.
        
        Args:
            request: Query request with connection and query details
            
        Returns:
            Dictionary with query results and metadata
            
        Raises:
            ValueError: If query validation fails
            ConnectionError: If connection fails
            Exception: For other execution errors
        """
        adapter = None
        
        try:
            # Step 1: Create adapter
            adapter = DatabaseAdapterFactory.create_adapter(request.connection)
            
            # Step 2: Validate query before connecting
            validation = adapter.validate_query(request.query)
            if not validation.is_valid or not validation.is_read_only:
                return {
                    "success": False,
                    "error": "Query validation failed",
                    "validation": validation.get_summary()
                }
            
            # Step 3: Connect to database
            await adapter.connect()
            
            # Step 4: Test connection
            if not await adapter.test_connection():
                return {
                    "success": False,
                    "error": "Connection test failed"
                }
            
            # Step 5: Execute query
            result = await adapter.execute_query(
                query=request.query,
                timeout=request.timeout,
                max_rows=request.max_rows
            )
            
            # Step 6: Format result based on requested format
            formatted_result = self._format_result(result, request.output_format)
            
            # Step 7: Build response
            response = {
                "success": True,
                "result": formatted_result,
                "summary": result.get_summary(),
                "validation": validation.get_summary() if request.include_metadata else None,
                "connection_info": adapter.get_connection_info() if request.include_metadata else None
            }
            
            return response
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Validation error: {str(e)}"
            }
        except ConnectionError as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
        except TimeoutError as e:
            return {
                "success": False,
                "error": f"Timeout error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
        finally:
            # Step 8: Always cleanup resources
            if adapter and adapter.is_connected:
                await adapter.disconnect()
    
    async def validate_query_only(self, connection: DatabaseConnection, query: str) -> Dict[str, Any]:
        """
        Validate a query without executing it.
        
        Args:
            connection: Database connection configuration
            query: SQL query to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            adapter = DatabaseAdapterFactory.create_adapter(connection)
            validation = adapter.validate_query(query)
            
            return {
                "success": True,
                "validation": validation.get_summary()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    async def test_connection_only(self, connection: DatabaseConnection) -> Dict[str, Any]:
        """
        Test database connection without executing queries.
        
        Args:
            connection: Database connection configuration
            
        Returns:
            Dictionary with connection test results
        """
        adapter = None
        
        try:
            adapter = DatabaseAdapterFactory.create_adapter(connection)
            await adapter.connect()
            
            is_healthy = await adapter.test_connection()
            connection_info = adapter.get_connection_info()
            
            return {
                "success": True,
                "is_connected": is_healthy,
                "connection_info": connection_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }
        finally:
            if adapter and adapter.is_connected:
                await adapter.disconnect()
    
    def get_supported_databases(self) -> Dict[str, Any]:
        """
        Get list of supported database types.
        
        Returns:
            Dictionary with supported databases
        """
        return {
            "success": True,
            "supported_databases": DatabaseAdapterFactory.get_supported_databases()
        }
    
    # ======================== Helper Methods ========================
    
    def _format_result(self, result: QueryResult, output_format: str) -> Any:
        """
        Format query result based on requested format.
        
        Args:
            result: Query result to format
            output_format: Desired format (json, csv, markdown, table)
            
        Returns:
            Formatted result
        """
        if output_format == "json":
            return result.to_dict(include_rows=True)
        
        elif output_format == "csv":
            return result.to_csv()
        
        elif output_format == "markdown":
            return result.to_markdown()
        
        elif output_format == "table":
            return self._format_as_table(result)
        
        else:
            # Default to JSON
            return result.to_dict(include_rows=True)
    
    def _format_as_table(self, result: QueryResult) -> str:
        """
        Format result as ASCII table.
        
        Args:
            result: Query result to format
            
        Returns:
            ASCII table string
        """
        if not result.rows:
            return "No results"
        
        # Calculate column widths
        col_widths = {}
        for col in result.columns:
            col_widths[col.name] = len(col.name)
        
        for row in result.rows:
            for col in result.columns:
                value_len = len(str(row.get(col.name, "")))
                col_widths[col.name] = max(col_widths[col.name], value_len)
        
        # Build table
        lines = []
        
        # Header
        header_parts = []
        separator_parts = []
        for col in result.columns:
            width = col_widths[col.name]
            header_parts.append(col.name.ljust(width))
            separator_parts.append("-" * width)
        
        lines.append(" | ".join(header_parts))
        lines.append(" | ".join(separator_parts))
        
        # Rows
        for row in result.rows:
            row_parts = []
            for col in result.columns:
                width = col_widths[col.name]
                value = str(row.get(col.name, ""))
                row_parts.append(value.ljust(width))
            lines.append(" | ".join(row_parts))
        
        return "\n".join(lines)
    
    async def execute_query_with_output_file(
        self,
        request: QueryRequest,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute query and optionally save results to file.
        
        Args:
            request: Query request
            output_file: Optional file path to save results
            
        Returns:
            Dictionary with execution results and file path
        """
        response = await self.execute_query(request)
        
        if response["success"] and output_file:
            try:
                # Save to file based on format
                if request.output_format == "json":
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(response, f, indent=2, default=str)
                else:
                    # For CSV, markdown, table formats
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(response["result"])
                
                response["output_file"] = output_file
            except Exception as e:
                response["file_error"] = f"Failed to save to file: {str(e)}"
        
        return response
