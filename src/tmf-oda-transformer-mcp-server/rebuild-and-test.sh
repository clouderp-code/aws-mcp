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

#==============================================================================
# TMF ODA Transformer MCP Server - Rebuild and Test Script
#==============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE_NAME="tmf-oda-transformer-mcp-server"
DOCKER_TAG="latest"
CONTAINER_NAME="tmf-oda-mcp-server"
HTTP_PORT="8000"
BASE_URL="http://localhost:${HTTP_PORT}"
TIMEOUT_SECONDS=60
DOCKERFILE_PATH="Dockerfile.optimized"
TEST_SCRIPT="test-external-access.py"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    local title=$1
    print_color $BLUE "\n============================================================"
    print_color $BLUE "🎯 ${title}"
    print_color $BLUE "============================================================"
}

# Function to check if command exists
check_command() {
    local cmd=$1
    if ! command -v $cmd &> /dev/null; then
        print_color $RED "❌ Error: $cmd is not installed or not in PATH"
        exit 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=$2
    local count=0
    
    print_color $CYAN "🕐 Waiting for service to be ready at $url (timeout: ${timeout}s)..."
    
    while [ $count -lt $timeout ]; do
        if curl -s -f $url/health > /dev/null 2>&1; then
            print_color $GREEN "✅ Health endpoint is ready!"
            
            # Also check MCP server info endpoint
            if curl -s -f $url/mcp/server/info > /dev/null 2>&1; then
                print_color $GREEN "✅ MCP protocol endpoints are ready!"
                return 0
            else
                print_color $YELLOW "⏳ MCP endpoints not ready yet..."
            fi
        fi
        sleep 1
        count=$((count + 1))
        if [ $((count % 10)) -eq 0 ]; then
            print_color $YELLOW "⏳ Still waiting... (${count}s elapsed)"
        fi
    done
    
    print_color $RED "❌ Service failed to start within ${timeout}s"
    return 1
}

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        print_color $RED "❌ Script failed with exit code $exit_code"
    fi
    
    print_color $CYAN "🧹 Cleaning up..."
    
    # Stop container if running
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        print_color $CYAN "🛑 Stopping container $CONTAINER_NAME..."
        docker stop $CONTAINER_NAME || true
    fi
    
    # Remove container if exists
    if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
        print_color $CYAN "🗑️ Removing container $CONTAINER_NAME..."
        docker rm $CONTAINER_NAME || true
    fi
    
    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT

# Main execution starts here
print_header "TMF ODA Transformer MCP Server - Rebuild and Test"
print_color $CYAN "🚀 Starting rebuild and test process..."
print_color $CYAN "📁 Working directory: $SCRIPT_DIR"
print_color $CYAN "🐳 Docker image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
print_color $CYAN "🌐 Test URL: $BASE_URL"

# Step 1: Validate prerequisites
print_header "Step 1: Validating Prerequisites"

# Check required commands
check_command "docker"
check_command "curl"
check_command "python3"

# Check if Dockerfile exists
if [ ! -f "$SCRIPT_DIR/$DOCKERFILE_PATH" ]; then
    print_color $RED "❌ Error: $DOCKERFILE_PATH not found in $SCRIPT_DIR"
    exit 1
fi

# Check if test script exists
if [ ! -f "$SCRIPT_DIR/$TEST_SCRIPT" ]; then
    print_color $RED "❌ Error: $TEST_SCRIPT not found in $SCRIPT_DIR"
    exit 1
fi

print_color $GREEN "✅ All prerequisites validated"

# Step 2: Stop and remove existing container
print_header "Step 2: Cleaning Up Existing Container"

# Stop container if running
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    print_color $CYAN "🛑 Stopping existing container $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME
    print_color $GREEN "✅ Container stopped"
else
    print_color $BLUE "ℹ️ No running container named $CONTAINER_NAME found"
fi

# Remove container if exists
if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
    print_color $CYAN "🗑️ Removing existing container $CONTAINER_NAME..."
    docker rm $CONTAINER_NAME
    print_color $GREEN "✅ Container removed"
else
    print_color $BLUE "ℹ️ No existing container named $CONTAINER_NAME found"
fi

# Step 3: Remove old Docker image
print_header "Step 3: Removing Old Docker Image"

if docker images -q $DOCKER_IMAGE_NAME:$DOCKER_TAG | grep -q .; then
    print_color $CYAN "🗑️ Removing old Docker image $DOCKER_IMAGE_NAME:$DOCKER_TAG..."
    docker rmi $DOCKER_IMAGE_NAME:$DOCKER_TAG
    print_color $GREEN "✅ Old Docker image removed"
else
    print_color $BLUE "ℹ️ No existing Docker image $DOCKER_IMAGE_NAME:$DOCKER_TAG found"
fi

# Step 4: Build new Docker image
print_header "Step 4: Building New Docker Image"

print_color $CYAN "🔨 Building Docker image from $DOCKERFILE_PATH..."
print_color $CYAN "📝 Build context: $SCRIPT_DIR"

# Change to script directory for build context
cd "$SCRIPT_DIR"

# Build the Docker image
docker build --no-cache -f $DOCKERFILE_PATH -t $DOCKER_IMAGE_NAME:$DOCKER_TAG .

print_color $GREEN "✅ Docker image built successfully"

# Show image details
print_color $CYAN "📊 Image details:"
docker images $DOCKER_IMAGE_NAME:$DOCKER_TAG

# Step 5: Run the new container
print_header "Step 5: Running New Container"

print_color $CYAN "🚀 Starting container $CONTAINER_NAME..."
print_color $CYAN "🔗 Port mapping: $HTTP_PORT:8000"

# Run container in background
docker run -d \
    --name $CONTAINER_NAME \
    -p $HTTP_PORT:8000 \
    --restart unless-stopped \
    $DOCKER_IMAGE_NAME:$DOCKER_TAG

print_color $GREEN "✅ Container started successfully"

# Show container status
print_color $CYAN "📊 Container status:"
docker ps -f name=$CONTAINER_NAME

# Step 6: Wait for service to be ready
print_header "Step 6: Waiting for Service Ready"

if wait_for_service $BASE_URL $TIMEOUT_SECONDS; then
    print_color $GREEN "✅ Service is ready for testing"
else
    print_color $RED "❌ Service failed to start. Checking logs..."
    docker logs $CONTAINER_NAME
    exit 1
fi

# Step 7: Run HTTP access tests
print_header "Step 7: Running HTTP Access Tests"

print_color $CYAN "🧪 Running comprehensive HTTP test suite..."
print_color $CYAN "📋 Test script: $TEST_SCRIPT"
print_color $CYAN "🎯 Target URL: $BASE_URL"

# Make test script executable
chmod +x "$SCRIPT_DIR/$TEST_SCRIPT"

# Run the test script
cd "$SCRIPT_DIR"
python3 $TEST_SCRIPT

# Capture test result
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_color $GREEN "✅ All HTTP tests passed!"
else
    print_color $RED "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi

# Step 8: Show final status and usage information
print_header "Step 8: Final Status and Usage Information"

print_color $CYAN "📊 Final Status:"
print_color $BLUE "  🐳 Container: $CONTAINER_NAME"
print_color $BLUE "  🏷️ Image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
print_color $BLUE "  🌐 HTTP URL: $BASE_URL"
print_color $BLUE "  📊 Health Check: $BASE_URL/health"
print_color $BLUE "  🛠️ Tools List: $BASE_URL/tools"

print_color $CYAN "\n📋 Available Tools:"
curl -s $BASE_URL/tools | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tools = data.get('tools', [])
    for tool in tools:
        print(f'  🔧 {tool.get(\"name\", \"Unknown\")} - {tool.get(\"description\", \"No description\")}')
except:
    print('  ❌ Could not retrieve tools list')
"

print_color $CYAN "\n🔗 MCP Protocol Endpoints:"
print_color $BLUE "  📊 Server Info: curl $BASE_URL/mcp/server/info"
print_color $BLUE "  🔧 Initialize: curl -X POST $BASE_URL/mcp/server/initialize"
print_color $BLUE "  📋 List Tools: curl -X POST $BASE_URL/mcp/tools/list"
print_color $BLUE "  🚀 Call Tool: curl -X POST $BASE_URL/mcp/tools/call"

print_color $CYAN "\n🔧 Management Commands:"
print_color $BLUE "  📋 View container logs: docker logs $CONTAINER_NAME"
print_color $BLUE "  🛑 Stop container: docker stop $CONTAINER_NAME"
print_color $BLUE "  🚀 Start container: docker start $CONTAINER_NAME"
print_color $BLUE "  🔄 Restart container: docker restart $CONTAINER_NAME"
print_color $BLUE "  🗑️ Remove container: docker rm $CONTAINER_NAME"

print_color $CYAN "\n🧪 Test Commands:"
print_color $BLUE "  🏃 Run quick tests: python3 $TEST_SCRIPT"
print_color $BLUE "  🔍 Health check: curl $BASE_URL/health"
print_color $BLUE "  📋 List tools: curl $BASE_URL/tools"

print_color $CYAN "\n📄 Log Files:"
print_color $BLUE "  🧪 Test results: http_test_results_*.json"
print_color $BLUE "  🐳 Container logs: docker logs $CONTAINER_NAME"

# Summary
print_header "Summary"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_color $GREEN "🎉 SUCCESS: TMF ODA MCP Server rebuilt and tested successfully!"
    print_color $GREEN "✅ Docker image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
    print_color $GREEN "✅ Container: $CONTAINER_NAME (running)"
    print_color $GREEN "✅ HTTP API: $BASE_URL (accessible)"
    print_color $GREEN "✅ All tools: Available and tested"
    print_color $GREEN "🚀 Your TMF ODA MCP Server is ready for use!"
else
    print_color $YELLOW "⚠️ PARTIAL SUCCESS: Container is running but some tests failed"
    print_color $YELLOW "✅ Docker image: $DOCKER_IMAGE_NAME:$DOCKER_TAG (built)"
    print_color $YELLOW "✅ Container: $CONTAINER_NAME (running)"
    print_color $YELLOW "⚠️ HTTP API: $BASE_URL (some issues detected)"
    print_color $YELLOW "📋 Check test results and container logs for details"
fi

# Exit with test result code
exit $TEST_EXIT_CODE 