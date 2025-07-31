#!/bin/bash

# Call Analysis MCP Server - Test Script for analyze-transcript tool
# This script tests the analyze-transcript endpoint with realistic parameters

set -e

# Configuration
SERVER_URL="http://localhost:8000"
TOOL_ENDPOINT="$SERVER_URL/tools/analyze-transcript"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}${BOLD}📊 Test Script: analyze-transcript Tool${NC}"
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_server() {
    echo -e "${BLUE}🔍 Checking server availability...${NC}"
    
    if curl -s --connect-timeout 3 --max-time 5 "$SERVER_URL/health" > /dev/null 2>&1; then
        print_success "Server is running at $SERVER_URL"
        return 0
    else
        print_error "Server is not accessible at $SERVER_URL"
        echo -e "${YELLOW}💡 Start the server with: python -m awslabs.call_analysis_mcp_server.mcp_http_server${NC}"
        return 1
    fi
}

test_basic_functionality() {
    echo -e "${BLUE}🧪 Testing basic analyze-transcript functionality...${NC}"
    
    # Test data with minimal required parameters
    local test_data='{
        "s3_bucket": "call-transcripts-demo",
        "s3_key": "transcripts/sample-call-001.json",
        "output_bucket": "call-analysis-results",
        "output_prefix": "analysis-001",
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $TOOL_ENDPOINT${NC}"
    echo -e "${CYAN}📋 Test data:${NC}"
    echo "$test_data" | jq '.' 2>/dev/null || echo "$test_data"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "Basic functionality test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_with_analysis_options() {
    echo -e "${BLUE}🧪 Testing with analysis options...${NC}"
    
    # Test data with analysis options
    local test_data='{
        "s3_bucket": "call-transcripts-demo",
        "s3_key": "transcripts/sample-call-002.json",
        "output_bucket": "call-analysis-results",
        "output_prefix": "analysis-002",
        "analysis_options": {
            "sentiment_analysis": true,
            "topic_extraction": true,
            "compliance_check": true,
            "performance_metrics": true,
            "conversation_flow": true
        },
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request with analysis options...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "Analysis options test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_error_handling() {
    echo -e "${BLUE}🧪 Testing error handling...${NC}"
    
    # Test with missing required parameters
    local test_data='{
        "s3_bucket": "call-transcripts-demo"
    }'
    
    echo -e "${CYAN}📤 Testing with missing required parameters...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_warning "Error handling test completed (expected error)"
    else
        print_error "Request failed"
    fi
}

test_invalid_parameters() {
    echo -e "${BLUE}🧪 Testing with invalid parameters...${NC}"
    
    # Test with invalid bucket name
    local test_data='{
        "s3_bucket": "",
        "s3_key": "transcripts/sample-call-003.json",
        "output_bucket": "call-analysis-results"
    }'
    
    echo -e "${CYAN}📤 Testing with invalid bucket name...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_warning "Invalid parameters test completed (expected error)"
    else
        print_error "Request failed"
    fi
}

show_usage() {
    echo -e "${CYAN}${BOLD}Usage:${NC} $0 [OPTION]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  --basic              Run basic functionality test"
    echo -e "  --analysis-options   Run test with analysis options"
    echo -e "  --error-handling     Run error handling tests"
    echo -e "  --invalid-params     Run invalid parameters test"
    echo -e "  --all                Run all tests (default)"
    echo -e "  --help               Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 --basic              # Test basic functionality"
    echo -e "  $0 --analysis-options   # Test with analysis options"
    echo -e "  $0 --all                # Run all tests"
}

main() {
    print_header
    
    # Check dependencies
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        print_warning "jq is not installed - JSON output will not be formatted"
    fi
    
    # Parse command line arguments
    local run_basic=false
    local run_analysis_options=false
    local run_error_handling=false
    local run_invalid_params=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --basic)
                run_basic=true
                shift
                ;;
            --analysis-options)
                run_analysis_options=true
                shift
                ;;
            --error-handling)
                run_error_handling=true
                shift
                ;;
            --invalid-params)
                run_invalid_params=true
                shift
                ;;
            --all)
                run_basic=true
                run_analysis_options=true
                run_error_handling=true
                run_invalid_params=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Default to all tests if none specified
    if [ "$run_basic" = false ] && [ "$run_analysis_options" = false ] && [ "$run_error_handling" = false ] && [ "$run_invalid_params" = false ]; then
        run_basic=true
        run_analysis_options=true
        run_error_handling=true
        run_invalid_params=true
    fi
    
    # Check server availability
    if ! check_server; then
        exit 1
    fi
    
    echo ""
    
    # Run selected tests
    if [ "$run_basic" = true ]; then
        test_basic_functionality
        echo ""
    fi
    
    if [ "$run_analysis_options" = true ]; then
        test_with_analysis_options
        echo ""
    fi
    
    if [ "$run_error_handling" = true ]; then
        test_error_handling
        echo ""
    fi
    
    if [ "$run_invalid_params" = true ]; then
        test_invalid_parameters
        echo ""
    fi
    
    print_header
    print_success "All tests completed for analyze-transcript tool"
    echo -e "${CYAN}📊 Tool: analyze-transcript${NC}"
    echo -e "${CYAN}🔗 Endpoint: $TOOL_ENDPOINT${NC}"
    echo -e "${CYAN}📝 Description: Analyze a single call transcript from S3 and generate comprehensive AI-powered analysis with KPIs${NC}"
}

# Run main function
main "$@" 