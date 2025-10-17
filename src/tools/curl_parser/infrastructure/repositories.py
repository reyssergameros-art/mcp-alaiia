"""
Infrastructure implementation of cURL parser.
Uses regex and shlex for parsing cURL commands.
"""

import shlex
from typing import List
from ..domain.models import ParsedCurlRequest, ParsedHeader
from ..domain.repositories import CurlParserRepository


class RegexCurlParser(CurlParserRepository):
    """
    Regex-based cURL parser implementation.
    
    Following SOLID:
    - SRP: Only parses cURL commands
    - DIP: Implements abstract interface
    """
    
    async def parse_curl_command(self, curl_command: str) -> ParsedCurlRequest:
        """
        Parse cURL command using shlex and pattern matching.
        
        Supports:
        - curl http://example.com
        - curl -X POST http://example.com
        - curl -H "Header: value" http://example.com
        - curl -d '{"key":"value"}' http://example.com
        
        Args:
            curl_command: Raw cURL command
            
        Returns:
            ParsedCurlRequest with extracted data
            
        Raises:
            ValueError: If parsing fails
        """
        if not curl_command or not curl_command.strip():
            raise ValueError("cURL command cannot be empty")
        
        # Clean command
        curl_command = curl_command.strip()
        
        # Remove 'curl' prefix
        if curl_command.startswith('curl '):
            curl_command = curl_command[5:].strip()
        
        try:
            # Parse with shlex for proper quote handling
            args = shlex.split(curl_command)
        except ValueError as e:
            raise ValueError(f"Failed to parse cURL: {str(e)}")
        
        # Extract components
        method = self._extract_method(args)
        url = self._extract_url(args)
        headers = self._extract_headers(args)
        body = self._extract_body(args)
        
        if not url:
            raise ValueError("No URL found in cURL command")
        
        return ParsedCurlRequest(
            method=method,
            url=url,
            headers=headers,
            body=body,
            raw_curl=f"curl {curl_command}"
        )
    
    def _extract_method(self, args: List[str]) -> str:
        """Extract HTTP method from args."""
        for i, arg in enumerate(args):
            if arg in ['-X', '--request'] and i + 1 < len(args):
                return args[i + 1].upper()
        
        # If has data, default to POST
        for arg in args:
            if arg in ['-d', '--data', '--data-raw', '--data-binary']:
                return 'POST'
        
        return 'GET'
    
    def _extract_url(self, args: List[str]) -> str:
        """Extract URL from args."""
        skip_next = False
        url_candidates = []
        
        flags_with_values = [
            '-X', '--request',
            '-H', '--header',
            '-d', '--data', '--data-raw', '--data-binary',
            '-u', '--user',
            '-A', '--user-agent',
            '-e', '--referer',
            '-o', '--output',
            '-T', '--upload-file'
        ]
        
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            
            if arg in flags_with_values:
                skip_next = True
                continue
            
            if arg.startswith('-'):
                continue
            
            url_candidates.append(arg)
        
        # Find best URL candidate
        for candidate in url_candidates:
            if '://' in candidate or candidate.startswith('/') or candidate.startswith('http'):
                return candidate
            if '.' in candidate or candidate.startswith('localhost'):
                return f"http://{candidate}"
        
        return url_candidates[-1] if url_candidates else ""
    
    def _extract_headers(self, args: List[str]) -> List[ParsedHeader]:
        """Extract headers from args."""
        headers = []
        
        i = 0
        while i < len(args):
            if args[i] in ['-H', '--header'] and i + 1 < len(args):
                header_str = args[i + 1]
                
                if ':' in header_str:
                    name, value = header_str.split(':', 1)
                    headers.append(ParsedHeader(
                        name=name.strip(),
                        value=value.strip()
                    ))
                
                i += 2
            else:
                i += 1
        
        return headers
    
    def _extract_body(self, args: List[str]) -> str:
        """Extract request body from args."""
        i = 0
        while i < len(args):
            if args[i] in ['-d', '--data', '--data-raw', '--data-binary'] and i + 1 < len(args):
                return args[i + 1]
            i += 1
        
        return None
