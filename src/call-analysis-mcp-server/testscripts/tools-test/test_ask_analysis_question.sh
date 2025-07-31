#!/bin/bash

# Call Analysis MCP Server - Test Script for ask-analysis-question tool
# This script tests the ask-analysis-question endpoint with realistic parameters

set -e

# Configuration
SERVER_URL="http://localhost:8000"
TOOL_ENDPOINT="$SERVER_URL/tools/ask-analysis-question"

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
    echo -e "${PURPLE}${BOLD}📊 Test Script: ask-analysis-question Tool${NC}"
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

test_basic_question() {
    echo -e "${BLUE}🧪 Testing basic question functionality...${NC}"
    
    # Test data with basic question
    local test_data='{
        "question": "What are the key insights from the call analysis?",
        "context_type": "auto"
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
        print_success "Basic question test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_quality_questions() {
    echo -e "${BLUE}🧪 Testing quality-focused questions...${NC}"
    
    # Test data with quality context
    local test_data='{
        "question": "How is the overall call quality performing?",
        "context_type": "quality",
        "report_file_path": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
    }'
    
    echo -e "${CYAN}📤 Sending quality-focused question...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "Quality questions test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_deals_questions() {
    echo -e "${BLUE}🧪 Testing deals-focused questions...${NC}"
    
    # Test data with deals context
    local test_data='{
        "question": "What is the conversion rate for sales calls?",
        "context_type": "deals",
        "report_file_path": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
    }'
    
    echo -e "${CYAN}📤 Sending deals-focused question...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "Deals questions test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_training_questions() {
    echo -e "${BLUE}🧪 Testing training-focused questions...${NC}"
    
    # Test data with training context
    local test_data='{
        "question": "What training opportunities are identified from the call analysis?",
        "context_type": "training",
        "report_file_path": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
    }'
    
    echo -e "${CYAN}📤 Sending training-focused question...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "Training questions test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_complex_questions() {
    echo -e "${BLUE}🧪 Testing complex analytical questions...${NC}"
    
    # Test data with complex question
    local test_data='{
        "question": "What are the top 3 factors contributing to successful call outcomes and how do they correlate with agent performance metrics?",
        "context_type": "auto",
        "report_file_path": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
    }'
    
    echo -e "${CYAN}📤 Sending complex analytical question...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "Complex questions test completed"
    else
        print_error "Request failed"
        return 1
    fi
}

test_error_handling() {
    echo -e "${BLUE}🧪 Testing error handling...${NC}"
    
    # Test with missing required question parameter
    local test_data='{
        "context_type": "auto"
    }'
    
    echo -e "${CYAN}📤 Testing with missing question parameter...${NC}"
    
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

test_invalid_context() {
    echo -e "${BLUE}🧪 Testing with invalid context type...${NC}"
    
    # Test with invalid context type
    local test_data='{
        "question": "What are the insights?",
        "context_type": "invalid_context"
    }'
    
    echo -e "${CYAN}📤 Testing with invalid context type...${NC}"
    
    local response=$(curl -s -X POST "$TOOL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}📥 Response received:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_warning "Invalid context test completed (expected error)"
    else
        print_error "Request failed"
    fi
}

show_usage() {
    echo -e "${CYAN}${BOLD}Usage:${NC} $0 [OPTION]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  --basic              Run basic question test"
    echo -e "  --quality            Run quality-focused questions test"
    echo -e "  --deals              Run deals-focused questions test"
    echo -e "  --training           Run training-focused questions test"
    echo -e "  --complex            Run complex analytical questions test"
    echo -e "  --error-handling     Run error handling tests"
    echo -e "  --invalid-context    Run invalid context type test"
    echo -e "  --all                Run all tests (default)"
    echo -e "  --help               Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 --basic              # Test basic question functionality"
    echo -e "  $0 --quality            # Test quality-focused questions"
    echo -e "  $0 --deals              # Test deals-focused questions"
    echo -e "  $0 --training           # Test training-focused questions"
    echo -e "  $0 --complex            # Test complex analytical questions"
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
    local run_quality=false
    local run_deals=false
    local run_training=false
    local run_complex=false
    local run_error_handling=false
    local run_invalid_context=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --basic)
                run_basic=true
                shift
                ;;
            --quality)
                run_quality=true
                shift
                ;;
            --deals)
                run_deals=true
                shift
                ;;
            --training)
                run_training=true
                shift
                ;;
            --complex)
                run_complex=true
                shift
                ;;
            --error-handling)
                run_error_handling=true
                shift
                ;;
            --invalid-context)
                run_invalid_context=true
                shift
                ;;
            --all)
                run_basic=true
                run_quality=true
                run_deals=true
                run_training=true
                run_complex=true
                run_error_handling=true
                run_invalid_context=true
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
    if [ "$run_basic" = false ] && [ "$run_quality" = false ] && [ "$run_deals" = false ] && [ "$run_training" = false ] && [ "$run_complex" = false ] && [ "$run_error_handling" = false ] && [ "$run_invalid_context" = false ]; then
        run_basic=true
        run_quality=true
        run_deals=true
        run_training=true
        run_complex=true
        run_error_handling=true
        run_invalid_context=true
    fi
    
    # Check server availability
    if ! check_server; then
        exit 1
    fi
    
    echo ""
    
    # Run selected tests
    if [ "$run_basic" = true ]; then
        test_basic_question
        echo ""
    fi
    
    if [ "$run_quality" = true ]; then
        test_quality_questions
        echo ""
    fi
    
    if [ "$run_deals" = true ]; then
        test_deals_questions
        echo ""
    fi
    
    if [ "$run_training" = true ]; then
        test_training_questions
        echo ""
    fi
    
    if [ "$run_complex" = true ]; then
        test_complex_questions
        echo ""
    fi
    
    if [ "$run_error_handling" = true ]; then
        test_error_handling
        echo ""
    fi
    
    if [ "$run_invalid_context" = true ]; then
        test_invalid_context
        echo ""
    fi
    
    print_header
    print_success "All tests completed for ask-analysis-question tool"
    echo -e "${CYAN}📊 Tool: ask-analysis-question${NC}"
    echo -e "${CYAN}🔗 Endpoint: $TOOL_ENDPOINT${NC}"
    echo -e "${CYAN}📝 Description: Ask natural language questions about call analysis and business intelligence reports to get specific insights with evidence${NC}"
}

# Run main function
main "$@" 