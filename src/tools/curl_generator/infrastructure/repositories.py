"""
Infrastructure implementation of cURL export repository.
Following the Repository Pattern and handling I/O operations.
"""

import json
import os
from typing import List
from ..domain.models import CurlCommand, PostmanCollection
from ..domain.repositories import CurlExportRepository


class JsonCurlRepository(CurlExportRepository):
    """
    File system implementation of CurlExportRepository.
    
    This implementation handles:
    - Writing cURL commands to shell script files
    - Writing Postman collections to JSON files
    - Directory creation and file management
    - Path resolution and error handling
    
    Following:
    - Dependency Inversion Principle: Implements abstract interface
    - Single Responsibility Principle: Only handles file I/O
    """
    
    async def save_curl_commands(self, commands: List[CurlCommand], output_file: str) -> str:
        """
        Save cURL commands to a shell script file.
        
        Creates a properly formatted shell script with:
        - Shebang line for bash execution
        - Comments for each command
        - Formatted cURL commands with line continuations
        
        Args:
            commands: List of CurlCommand domain objects
            output_file: Path where commands should be saved
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            IOError: If file cannot be written
            ValueError: If commands list is empty
        """
        if not commands:
            raise ValueError("Cannot save empty commands list")
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write commands to file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write shell script header
            f.write("#!/bin/bash\n\n")
            f.write("# Generated cURL commands for API testing\n")
            f.write("# Each command can be executed independently\n")
            f.write(f"# Total commands: {len(commands)}\n\n")
            
            # Write separator
            f.write("# " + "=" * 70 + "\n\n")
            
            # Write each command
            for i, cmd in enumerate(commands, 1):
                # Write command header
                f.write(f"# Command {i}: {cmd.name}\n")
                if cmd.description:
                    f.write(f"# Description: {cmd.description}\n")
                f.write("# " + "-" * 70 + "\n")
                
                # Write the cURL command
                f.write(cmd.to_curl_string(pretty=True))
                f.write("\n\n")
                
                # Add separator between commands
                if i < len(commands):
                    f.write("# " + "=" * 70 + "\n\n")
        
        return os.path.abspath(output_file)
    
    async def save_postman_collection(self, collection: PostmanCollection, output_file: str) -> str:
        """
        Save Postman collection to JSON file.
        
        Creates a properly formatted Postman Collection v2.1 JSON file
        that can be directly imported into Postman.
        
        Args:
            collection: PostmanCollection domain object
            output_file: Path where collection should be saved
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            IOError: If file cannot be written
            ValueError: If collection is invalid
        """
        if not collection:
            raise ValueError("Cannot save None collection")
        
        if not collection.items:
            raise ValueError("Cannot save collection with no items")
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Convert collection to dictionary
        collection_dict = collection.to_dict()
        
        # Write to file with pretty formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                collection_dict, 
                f, 
                indent=2, 
                ensure_ascii=False,
                sort_keys=False
            )
        
        return os.path.abspath(output_file)
