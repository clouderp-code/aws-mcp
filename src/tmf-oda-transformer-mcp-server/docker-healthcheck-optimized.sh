#!/bin/bash
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

set -euo pipefail

# Function to check critical dependencies
check_dependencies() {
    local deps=("boto3" "pydantic" "loguru" "mcp")
    for dep in "${deps[@]}"; do
        if ! python -c "import $dep" 2>/dev/null; then
            echo "ERROR: Critical dependency '$dep' not available"
            return 1
        fi
    done
    return 0
}

# Function to check module importability
check_module_import() {
    if ! python -c "
import awslabs.tmf_oda_transformer_mcp_server.server as server
import awslabs.tmf_oda_transformer_mcp_server.models as models
print('Module imports successful')
" 2>/dev/null; then
        echo "ERROR: TMF ODA Transformer modules cannot be imported"
        return 1
    fi
    return 0
}

# Function to check tool availability
check_tools() {
    if ! python -c "
from awslabs.tmf_oda_transformer_mcp_server.server import (
    schema_analyzer_tool,
    db_analyzer_tool,
    raw_analysis_tool,
    stripped_schema_tool,
    get_job_logs_tool,
    test_runner_tool
)
print('All 6 tools available')
" 2>/dev/null; then
        echo "ERROR: MCP tools are not properly available"
        return 1
    fi
    return 0
}

# Main health check
main() {
    echo "Starting TMF ODA Transformer MCP Server health check..."
    
    # Check 1: Critical dependencies
    if ! check_dependencies; then
        echo "FAIL: Dependency check failed"
        exit 1
    fi
    echo "✓ Dependencies check passed"
    
    # Check 2: Module imports
    if ! check_module_import; then
        echo "FAIL: Module import check failed"
        exit 1
    fi
    echo "✓ Module import check passed"
    
    # Check 3: Tool availability
    if ! check_tools; then
        echo "FAIL: Tool availability check failed"
        exit 1
    fi
    echo "✓ Tool availability check passed"
    
    echo "SUCCESS: TMF ODA Transformer MCP Server is healthy"
    exit 0
}

# Run main function
main "$@" 