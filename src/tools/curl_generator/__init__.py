"""
cURL Generator Tool

This tool generates cURL commands and Postman collections from Swagger/OpenAPI specifications.

Architecture:
- Domain: Business models and repository interfaces
- Application: Business logic and orchestration
- Infrastructure: Concrete implementations (file I/O)

Following SOLID principles and Hexagonal Architecture.
"""

from .domain.models import CurlCommand, PostmanCollection
from .application.services import CurlGenerationService
from .infrastructure.repositories import JsonCurlRepository

__all__ = [
    'CurlCommand',
    'PostmanCollection',
    'CurlGenerationService',
    'JsonCurlRepository'
]
