"""
cURL Parser Tool

Parses cURL commands and generates test artifacts using existing generators.

Architecture:
- Domain: Business models (ParsedCurlRequest, CurlParseResult)
- Application: Orchestration service (CurlParsingService)
- Infrastructure: Parsing implementation (RegexCurlParser)

IMPORTANT: This tool ONLY consumes existing generators without modifying them.
"""

from .domain.models import ParsedCurlRequest, CurlParseResult
from .application.services import CurlParsingService
from .infrastructure.repositories import RegexCurlParser

__all__ = ['ParsedCurlRequest', 'CurlParseResult', 'CurlParsingService', 'RegexCurlParser']
