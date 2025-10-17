"""
Shared mapper for swagger-compatible data structures.
Centralizes common conversion logic to avoid duplication.

Following SOLID:
- SRP: Only handles swagger format conversion
- OCP: Extensible for new field types
- DIP: Pure functions, no dependencies
"""

from typing import Dict, Any, List, Optional


class SwaggerDataMapper:
    """
    Utility class for creating swagger-compatible data structures.
    Used by multiple tools (swagger_analysis, curl_parser, etc.)
    """
    
    @staticmethod
    def create_field_dict(
        name: str,
        data_type: str = "string",
        required: bool = True,
        example: Any = None,
        description: str = "",
        format_value: Optional[str] = None,
        enum_values: Optional[List[str]] = None,
        pattern: Optional[str] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized field dictionary for swagger format.
        
        Args:
            name: Field name
            data_type: Data type (string, integer, boolean, etc.)
            required: Whether field is required
            example: Example value
            description: Field description
            format_value: Format specification (e.g., "uuid", "date-time")
            enum_values: Allowed values for enum types
            pattern: Regex pattern for validation
            minimum: Minimum value for numbers
            maximum: Maximum value for numbers
            
        Returns:
            Swagger-compatible field dictionary
        """
        field_dict = {
            "name": name,
            "data_type": data_type,
            "required": required,
            "description": description
        }
        
        if example is not None:
            field_dict["example"] = example
        
        if format_value:
            field_dict["format"] = format_value
        
        if enum_values:
            field_dict["enum_values"] = enum_values
        
        if pattern:
            field_dict["pattern"] = pattern
        
        if minimum is not None:
            field_dict["minimum"] = minimum
        
        if maximum is not None:
            field_dict["maximum"] = maximum
        
        return field_dict
    
    @staticmethod
    def create_response_dict(
        status_code: str,
        description: str = "",
        content_type: str = "application/json",
        schema: Optional[Dict] = None,
        example: Any = None
    ) -> Dict[str, Any]:
        """
        Create a standardized response dictionary for swagger format.
        
        Args:
            status_code: HTTP status code
            description: Response description
            content_type: Content type header
            schema: Response schema
            example: Example response
            
        Returns:
            Swagger-compatible response dictionary
        """
        response_dict = {
            "status_code": status_code,
            "description": description,
            "content_type": content_type
        }
        
        if schema:
            response_dict["schema"] = schema
        
        if example is not None:
            response_dict["example"] = example
        
        return response_dict
    
    @staticmethod
    def create_endpoint_dict(
        method: str,
        path: str,
        summary: str = "",
        description: str = "",
        operation_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        headers: Optional[List[Dict]] = None,
        path_parameters: Optional[List[Dict]] = None,
        query_parameters: Optional[List[Dict]] = None,
        request_body: Optional[Dict[str, Dict]] = None,
        request_content_type: str = "application/json",
        responses: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized endpoint dictionary for swagger format.
        
        Args:
            method: HTTP method
            path: Endpoint path
            summary: Short summary
            description: Detailed description
            operation_id: Unique operation identifier
            tags: Categorization tags
            headers: List of header dictionaries
            path_parameters: List of path parameter dictionaries
            query_parameters: List of query parameter dictionaries
            request_body: Dictionary of body field dictionaries
            request_content_type: Request content type
            responses: List of response dictionaries
            
        Returns:
            Swagger-compatible endpoint dictionary
        """
        endpoint_dict = {
            "method": method,
            "path": path,
            "summary": summary,
            "description": description,
            "headers": headers or [],
            "path_parameters": path_parameters or [],
            "query_parameters": query_parameters or [],
            "request_body": request_body,
            "request_content_type": request_content_type,
            "responses": responses or []
        }
        
        if operation_id:
            endpoint_dict["operation_id"] = operation_id
        
        if tags:
            endpoint_dict["tags"] = tags
        
        return endpoint_dict
    
    @staticmethod
    def infer_type_from_value(value: Any) -> str:
        """
        Infer swagger data type from Python value.
        
        Args:
            value: Python value
            
        Returns:
            Swagger type string
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"
