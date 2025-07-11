#!/bin/bash
# Script to run TMF ODA Transformer MCP Server for external access

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="tmf-oda-transformer-mcp-server:latest"
CONTAINER_NAME="tmf-oda-mcp-server"
HTTP_PORT="8000"
HOST_IP=$(hostname -I | awk '{print $1}')

print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if container is running
check_container() {
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        return 0
    else
        return 1
    fi
}

# Function to start the container
start_container() {
    print_color $BLUE "Starting TMF ODA MCP Server container..."
    
    # Stop existing container if running
    if check_container; then
        print_color $YELLOW "Stopping existing container..."
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
    
    # Run container with MCP HTTP transport server
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${HTTP_PORT}:${HTTP_PORT}" \
        -e PYTHONUNBUFFERED=1 \
        -e AWS_REGION=us-east-1 \
        -e TMF_ODA_REFERENCE_PATH=/opt/tmf-oda-references \
        --restart unless-stopped \
        "${IMAGE_NAME}" \
        python mcp_http_server.py
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "✅ Container started successfully!"
        print_color $BLUE "📡 Server accessible at: http://${HOST_IP}:${HTTP_PORT}"
        print_color $BLUE "🔗 MCP Endpoint: http://${HOST_IP}:${HTTP_PORT}/mcp"
    else
        print_color $RED "❌ Failed to start container"
        return 1
    fi
}

# Function to stop the container
stop_container() {
    if check_container; then
        print_color $BLUE "Stopping TMF ODA MCP Server container..."
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
        print_color $GREEN "✅ Container stopped"
    else
        print_color $YELLOW "⚠️ Container is not running"
    fi
}

# Function to show container status
show_status() {
    if check_container; then
        print_color $GREEN "✅ TMF ODA MCP Server is running"
        print_color $BLUE "📊 Container details:"
        docker ps -f name="${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        print_color $BLUE "📋 Recent logs:"
        docker logs "${CONTAINER_NAME}" --tail 10
        
        print_color $BLUE "🌐 Access URLs:"
        echo "   HTTP Endpoint: http://${HOST_IP}:${HTTP_PORT}"
        echo "   Health Check:  http://${HOST_IP}:${HTTP_PORT}/health"
        echo "   MCP Endpoint:  http://${HOST_IP}:${HTTP_PORT}/mcp"
    else
        print_color $RED "❌ TMF ODA MCP Server is not running"
    fi
}

# Function to show logs
show_logs() {
    if check_container; then
        print_color $BLUE "📋 Container logs:"
        docker logs "${CONTAINER_NAME}" -f
    else
        print_color $RED "❌ Container is not running"
    fi
}

# Function to test connectivity
test_connectivity() {
    if ! check_container; then
        print_color $RED "❌ Container is not running"
        return 1
    fi
    
    print_color $BLUE "🔗 Testing connectivity..."
    
    # Test HTTP endpoint
    if curl -s -f "http://${HOST_IP}:${HTTP_PORT}/health" >/dev/null; then
        print_color $GREEN "✅ HTTP health check passed"
    else
        print_color $RED "❌ HTTP health check failed"
    fi
    
    # Test MCP endpoint
    if curl -s -f "http://${HOST_IP}:${HTTP_PORT}/mcp" >/dev/null; then
        print_color $GREEN "✅ MCP endpoint accessible"
    else
        print_color $YELLOW "⚠️ MCP endpoint test inconclusive"
    fi
}

# Main function
main() {
    print_color $GREEN "🚀 TMF ODA Transformer MCP Server - External Access Manager"
    echo "=============================================================="
    
    case "${1:-start}" in
        "start")
            start_container
            sleep 3
            show_status
            ;;
        "stop")
            stop_container
            ;;
        "restart")
            stop_container
            sleep 2
            start_container
            sleep 3
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "test")
            test_connectivity
            ;;
        *)
            echo "Usage: $0 [start|stop|restart|status|logs|test]"
            echo ""
            echo "Commands:"
            echo "  start    - Start the MCP server container (default)"
            echo "  stop     - Stop the MCP server container"
            echo "  restart  - Restart the MCP server container"
            echo "  status   - Show container status and access URLs"
            echo "  logs     - Show container logs (follow mode)"
            echo "  test     - Test connectivity to the server"
            exit 1
            ;;
    esac
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_color $RED "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}" &>/dev/null; then
    print_color $RED "❌ Image ${IMAGE_NAME} not found. Please build it first."
    exit 1
fi

# Run main function
main "$@" 