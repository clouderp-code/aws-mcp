#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Build script for TMF ODA Transformer MCP Server Docker images

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
IMAGE_NAME="tmf-oda-transformer-mcp-server"
ORIGINAL_TAG="original"
OPTIMIZED_TAG="optimized"
BUILD_CONTEXT="."

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to build original Dockerfile
build_original() {
    print_color $BLUE "Building original Docker image..."
    if docker build -f Dockerfile -t "${IMAGE_NAME}:${ORIGINAL_TAG}" "${BUILD_CONTEXT}"; then
        print_color $GREEN "✓ Original image built successfully"
    else
        print_color $RED "✗ Failed to build original image"
        return 1
    fi
}

# Function to build optimized Dockerfile
build_optimized() {
    print_color $BLUE "Building optimized Docker image..."
    if docker build -f Dockerfile.optimized -t "${IMAGE_NAME}:${OPTIMIZED_TAG}" "${BUILD_CONTEXT}"; then
        print_color $GREEN "✓ Optimized image built successfully"
    else
        print_color $RED "✗ Failed to build optimized image"
        return 1
    fi
}

# Function to compare image sizes
compare_sizes() {
    print_color $BLUE "Comparing image sizes..."
    
    # Check if images exist
    if ! docker image inspect "${IMAGE_NAME}:${ORIGINAL_TAG}" &>/dev/null; then
        print_color $YELLOW "⚠ Original image not found, skipping size comparison"
        return 0
    fi
    
    if ! docker image inspect "${IMAGE_NAME}:${OPTIMIZED_TAG}" &>/dev/null; then
        print_color $YELLOW "⚠ Optimized image not found, skipping size comparison"
        return 0
    fi
    
    # Get image sizes
    original_size=$(docker image inspect "${IMAGE_NAME}:${ORIGINAL_TAG}" --format='{{.Size}}')
    optimized_size=$(docker image inspect "${IMAGE_NAME}:${OPTIMIZED_TAG}" --format='{{.Size}}')
    
    # Convert to human readable
    original_human=$(numfmt --to=iec-i --suffix=B --format="%.1f" $original_size)
    optimized_human=$(numfmt --to=iec-i --suffix=B --format="%.1f" $optimized_size)
    
    # Calculate savings
    if [ "$optimized_size" -lt "$original_size" ]; then
        saved_bytes=$((original_size - optimized_size))
        saved_human=$(numfmt --to=iec-i --suffix=B --format="%.1f" $saved_bytes)
        saved_percent=$(( (saved_bytes * 100) / original_size ))
        
        print_color $GREEN "📊 Size Comparison Results:"
        echo "   Original:  $original_human"
        echo "   Optimized: $optimized_human"
        echo "   Saved:     $saved_human (${saved_percent}% reduction)"
    else
        print_color $YELLOW "📊 Size Comparison Results:"
        echo "   Original:  $original_human"
        echo "   Optimized: $optimized_human"
        echo "   Note: Optimized image is larger (possibly due to additional dependencies)"
    fi
}

# Function to test images
test_images() {
    print_color $BLUE "Testing Docker images..."
    
    local images=("${IMAGE_NAME}:${ORIGINAL_TAG}" "${IMAGE_NAME}:${OPTIMIZED_TAG}")
    local tags=("original" "optimized")
    
    for i in "${!images[@]}"; do
        local image="${images[$i]}"
        local tag="${tags[$i]}"
        
        if docker image inspect "$image" &>/dev/null; then
            print_color $BLUE "Testing $tag image..."
            if timeout 30 docker run --rm "$image" --help &>/dev/null; then
                print_color $GREEN "✓ $tag image test passed"
            else
                print_color $YELLOW "⚠ $tag image test timed out or failed"
            fi
        else
            print_color $YELLOW "⚠ $tag image not found, skipping test"
        fi
    done
}

# Function to show layer information
show_layers() {
    print_color $BLUE "Docker image layers information..."
    
    local images=("${IMAGE_NAME}:${ORIGINAL_TAG}" "${IMAGE_NAME}:${OPTIMIZED_TAG}")
    local tags=("original" "optimized")
    
    for i in "${!images[@]}"; do
        local image="${images[$i]}"
        local tag="${tags[$i]}"
        
        if docker image inspect "$image" &>/dev/null; then
            layer_count=$(docker history "$image" --no-trunc | wc -l)
            print_color $BLUE "$tag image: $((layer_count - 1)) layers"
        fi
    done
}

# Function to clean up images
cleanup() {
    print_color $BLUE "Cleaning up Docker images..."
    
    local images=("${IMAGE_NAME}:${ORIGINAL_TAG}" "${IMAGE_NAME}:${OPTIMIZED_TAG}")
    
    for image in "${images[@]}"; do
        if docker image inspect "$image" &>/dev/null; then
            if docker rmi "$image" &>/dev/null; then
                print_color $GREEN "✓ Removed $image"
            else
                print_color $YELLOW "⚠ Failed to remove $image"
            fi
        fi
    done
}

# Main function
main() {
    print_color $GREEN "🐳 TMF ODA Transformer MCP Server Docker Build Script"
    echo "=================================================="
    
    case "${1:-build}" in
        "original")
            build_original
            ;;
        "optimized")
            build_optimized
            ;;
        "build")
            build_original
            build_optimized
            ;;
        "compare")
            compare_sizes
            show_layers
            ;;
        "test")
            test_images
            ;;
        "cleanup")
            cleanup
            ;;
        "all")
            build_original
            build_optimized
            compare_sizes
            show_layers
            test_images
            ;;
        *)
            echo "Usage: $0 [original|optimized|build|compare|test|cleanup|all]"
            echo ""
            echo "Commands:"
            echo "  original   - Build only the original Dockerfile"
            echo "  optimized  - Build only the optimized Dockerfile"
            echo "  build      - Build both images (default)"
            echo "  compare    - Compare image sizes and layers"
            echo "  test       - Test both images"
            echo "  cleanup    - Remove built images"
            echo "  all        - Run build, compare, and test"
            exit 1
            ;;
    esac
    
    print_color $GREEN "✅ Docker build script completed!"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_color $RED "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Run main function
main "$@" 