# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Static content and constants for Google Drive MCP server."""

import os


def _load_file_content(filename: str) -> str:
    """Load content from a static file.
    
    Args:
        filename: Name of the file to load.
        
    Returns:
        File content as string.
    """
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Content file {filename} not found."
    except Exception as e:
        return f"Error loading {filename}: {str(e)}"


# Load static content
MCP_INSTRUCTIONS = _load_file_content('MCP_INSTRUCTIONS.md')
GDRIVE_SETUP_GUIDE = _load_file_content('GDRIVE_SETUP_GUIDE.md')
GDRIVE_BEST_PRACTICES = _load_file_content('GDRIVE_BEST_PRACTICES.md')
GDRIVE_API_REFERENCE = _load_file_content('GDRIVE_API_REFERENCE.md')

__all__ = [
    'MCP_INSTRUCTIONS',
    'GDRIVE_SETUP_GUIDE',
    'GDRIVE_BEST_PRACTICES',
    'GDRIVE_API_REFERENCE',
] 