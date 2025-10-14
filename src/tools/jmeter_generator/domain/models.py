"""Domain models for JMeter generation."""
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum


class HttpMethod(Enum):
    """HTTP methods supported by JMeter."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class JMeterHeader:
    """Represents an HTTP header in JMeter."""
    name: str
    value: str


@dataclass
class JMeterParameter:
    """Represents a parameter (query or form) in JMeter."""
    name: str
    value: str
    url_encode: bool = True


@dataclass
class JMeterHttpRequest:
    """Represents an HTTP request in JMeter."""
    name: str
    method: HttpMethod
    path: str
    headers: List[JMeterHeader]
    parameters: List[JMeterParameter]
    body_data: Optional[str] = None
    content_encoding: str = "UTF-8"
    follow_redirects: bool = True
    use_keepalive: bool = True


@dataclass
class JMeterThreadGroup:
    """Represents a Thread Group in JMeter."""
    name: str
    num_threads: int = 1
    ramp_time: int = 1
    loop_count: int = 1
    continue_on_error: bool = False
    http_requests: List[JMeterHttpRequest] = None
    
    def __post_init__(self):
        if self.http_requests is None:
            self.http_requests = []


@dataclass
class JMeterTestPlan:
    """Represents a complete JMeter test plan."""
    name: str
    base_url: str
    port: int = 80
    protocol: str = "http"
    thread_groups: List[JMeterThreadGroup] = None
    
    def __post_init__(self):
        if self.thread_groups is None:
            self.thread_groups = []


@dataclass
class JMeterGenerationResult:
    """Result of JMeter generation process."""
    test_plan: JMeterTestPlan
    xml_content: str
    total_requests: int
    total_thread_groups: int