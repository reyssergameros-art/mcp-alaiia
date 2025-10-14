"""Domain models for swagger analysis."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class FieldFormat(Enum):
    """Enum for common field formats."""
    UUID = "uuid"
    DATE = "date"
    DATETIME = "date-time"
    EMAIL = "email"
    PHONE = "phone"
    PASSWORD = "password"
    URI = "uri"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    BINARY = "binary"
    BYTE = "byte"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT = "float"
    DOUBLE = "double"
    NONE = "none"


@dataclass
class FieldInfo:
    """Information about a field (header, request body field, etc.)."""
    name: str
    data_type: str
    required: bool
    format: FieldFormat
    description: Optional[str] = None
    example: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None


@dataclass
class ResponseInfo:
    """Information about an API response."""
    status_code: str
    description: str
    content_type: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None


@dataclass
class EndpointInfo:
    """Detailed information about an API endpoint."""
    method: str
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    tags: List[str] = None
    headers: List[FieldInfo] = None
    path_parameters: List[FieldInfo] = None
    query_parameters: List[FieldInfo] = None
    request_body: Optional[Dict[str, FieldInfo]] = None
    request_content_type: Optional[str] = None
    responses: List[ResponseInfo] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.headers is None:
            self.headers = []
        if self.path_parameters is None:
            self.path_parameters = []
        if self.query_parameters is None:
            self.query_parameters = []
        if self.responses is None:
            self.responses = []


@dataclass
class SwaggerAnalysisResult:
    """Complete result of swagger analysis."""
    base_urls: List[str]
    total_endpoints: int
    endpoints: List[EndpointInfo]
    title: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    license_info: Optional[Dict[str, str]] = None