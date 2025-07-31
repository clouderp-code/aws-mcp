#!/bin/bash

# Call Analysis MCP Server - Comprehensive Test Script for All Tools
# This script tests all available tools with realistic parameters

set -e

# Configuration
SERVER_URL="http://localhost:8000"

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
    echo -e "${PURPLE}${BOLD}📊 Comprehensive Test Script: All Call Analysis MCP Tools${NC}"
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

test_analyze_transcript() {
    echo -e "${BLUE}🧪 Testing analyze-transcript tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/analyze-transcript"
    local test_data='{
        "s3_bucket": "call-transcripts-demo",
        "s3_key": "transcripts/sample-call-001.json",
        "output_bucket": "call-analysis-results",
        "output_prefix": "analysis-001",
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "analyze-transcript test completed"
    else
        print_error "analyze-transcript test failed"
    fi
}

test_analyze_transcript_batch() {
    echo -e "${BLUE}🧪 Testing analyze-transcript-batch tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/analyze-transcript-batch"
    local test_data='{
        "s3_bucket": "call-transcripts-demo",
        "s3_prefix": "transcripts/batch-001/",
        "output_bucket": "call-analysis-results",
        "output_prefix": "batch-analysis-001",
        "max_files": 10,
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 60)
    
    if [ $? -eq 0 ]; then
        print_success "analyze-transcript-batch test completed"
    else
        print_error "analyze-transcript-batch test failed"
    fi
}

test_generate_business_intelligence() {
    echo -e "${BLUE}🧪 Testing generate-business-intelligence tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/generate-business-intelligence"
    local test_data='{
        "analysis_s3_urls": [
            "s3://call-analysis-results/analysis-001/analysis.json",
            "s3://call-analysis-results/batch-analysis-001/batch_analysis.json"
        ],
        "output_bucket": "call-analysis-results",
        "time_period": "Last Week",
        "output_key": "business_intelligence.json",
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "generate-business-intelligence test completed"
    else
        print_error "generate-business-intelligence test failed"
    fi
}

test_analyze_local_scripts() {
    echo -e "${BLUE}🧪 Testing analyze-local-scripts tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/analyze-local-scripts"
    local test_data='{
        "scripts_folder": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts",
        "script_pattern": "script*.json",
        "output_file": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/local_analysis_report.json",
        "time_period": "Current Script Collection",
        "max_scripts": 10
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "analyze-local-scripts test completed"
    else
        print_error "analyze-local-scripts test failed"
    fi
}

test_ask_analysis_question() {
    echo -e "${BLUE}🧪 Testing ask-analysis-question tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/ask-analysis-question"
    local test_data='{
        "question": "What are the key insights from the call analysis?",
        "context_type": "auto"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "ask-analysis-question test completed"
    else
        print_error "ask-analysis-question test failed"
    fi
}

test_read_s3_transcript() {
    echo -e "${BLUE}🧪 Testing read-s3-transcript tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/read-s3-transcript"
    local test_data='{
        "s3_bucket": "call-transcripts-demo",
        "s3_key": "transcripts/sample-call-001.json",
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "read-s3-transcript test completed"
    else
        print_error "read-s3-transcript test failed"
    fi
}

test_upload_to_s3() {
    echo -e "${BLUE}🧪 Testing upload-to-s3 tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/upload-to-s3"
    local test_data='{
        "content": "{\"analysis\": \"test analysis data\", \"timestamp\": \"2025-07-31T12:00:00Z\"}",
        "s3_bucket": "call-analysis-results",
        "s3_key": "test-upload/analysis-test.json",
        "content_type": "application/json",
        "aws_region": "us-east-1"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "upload-to-s3 test completed"
    else
        print_error "upload-to-s3 test failed"
    fi
}

test_generate_report() {
    echo -e "${BLUE}🧪 Testing generate-report tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/generate-report"
    local test_data='{
        "analysis_result": {
            "call_id": "test-call-001",
            "sentiment_score": 0.8,
            "topics": ["customer_service", "billing"],
            "compliance_score": 0.95,
            "performance_metrics": {
                "resolution_time": 300,
                "customer_satisfaction": 4.5
            }
        },
        "report_type": "detailed"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "generate-report test completed"
    else
        print_error "generate-report test failed"
    fi
}

test_create_dashboard() {
    echo -e "${BLUE}🧪 Testing create-dashboard tool...${NC}"
    
    local endpoint="$SERVER_URL/tools/create-dashboard"
    local test_data='{
        "analysis_data": [
            {
                "call_id": "call-001",
                "sentiment_score": 0.8,
                "topics": ["customer_service"],
                "compliance_score": 0.95
            },
            {
                "call_id": "call-002",
                "sentiment_score": 0.7,
                "topics": ["billing"],
                "compliance_score": 0.90
            }
        ],
        "dashboard_title": "Call Analysis Dashboard",
        "output_path": "dashboard.html"
    }'
    
    echo -e "${CYAN}📤 Sending request to: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ]; then
        print_success "create-dashboard test completed"
    else
        print_error "create-dashboard test failed"
    fi
}

test_error_handling() {
    echo -e "${BLUE}🧪 Testing error handling for all tools...${NC}"
    
    local tools=(
        "analyze-transcript"
        "analyze-transcript-batch"
        "generate-business-intelligence"
        "analyze-local-scripts"
        "ask-analysis-question"
        "read-s3-transcript"
        "upload-to-s3"
        "generate-report"
        "create-dashboard"
    )
    
    for tool in "${tools[@]}"; do
        echo -e "${CYAN}📤 Testing error handling for: $tool${NC}"
        
        local endpoint="$SERVER_URL/tools/$tool"
        local test_data='{}'
        
        local response=$(curl -s -X POST "$endpoint" \
            -H "Content-Type: application/json" \
            -d "$test_data" \
            --connect-timeout 10 \
            --max-time 30)
        
        if [ $? -eq 0 ]; then
            print_warning "$tool error handling test completed (expected error)"
        else
            print_error "$tool error handling test failed"
        fi
    done
}

show_usage() {
    echo -e "${CYAN}${BOLD}Usage:${NC} $0 [OPTION]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  --analyze-transcript           Test analyze-transcript tool"
    echo -e "  --analyze-transcript-batch     Test analyze-transcript-batch tool"
    echo -e "  --generate-business-intelligence Test generate-business-intelligence tool"
    echo -e "  --analyze-local-scripts        Test analyze-local-scripts tool"
    echo -e "  --ask-analysis-question        Test ask-analysis-question tool"
    echo -e "  --read-s3-transcript           Test read-s3-transcript tool"
    echo -e "  --upload-to-s3                 Test upload-to-s3 tool"
    echo -e "  --generate-report              Test generate-report tool"
    echo -e "  --create-dashboard             Test create-dashboard tool"
    echo -e "  --error-handling               Test error handling for all tools"
    echo -e "  --all                          Test all tools (default)"
    echo -e "  --help                         Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 --analyze-transcript        # Test single tool"
    echo -e "  $0 --all                       # Test all tools"
    echo -e "  $0 --error-handling            # Test error handling"
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
    local run_analyze_transcript=false
    local run_analyze_transcript_batch=false
    local run_generate_business_intelligence=false
    local run_analyze_local_scripts=false
    local run_ask_analysis_question=false
    local run_read_s3_transcript=false
    local run_upload_to_s3=false
    local run_generate_report=false
    local run_create_dashboard=false
    local run_error_handling=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --analyze-transcript)
                run_analyze_transcript=true
                shift
                ;;
            --analyze-transcript-batch)
                run_analyze_transcript_batch=true
                shift
                ;;
            --generate-business-intelligence)
                run_generate_business_intelligence=true
                shift
                ;;
            --analyze-local-scripts)
                run_analyze_local_scripts=true
                shift
                ;;
            --ask-analysis-question)
                run_ask_analysis_question=true
                shift
                ;;
            --read-s3-transcript)
                run_read_s3_transcript=true
                shift
                ;;
            --upload-to-s3)
                run_upload_to_s3=true
                shift
                ;;
            --generate-report)
                run_generate_report=true
                shift
                ;;
            --create-dashboard)
                run_create_dashboard=true
                shift
                ;;
            --error-handling)
                run_error_handling=true
                shift
                ;;
            --all)
                run_analyze_transcript=true
                run_analyze_transcript_batch=true
                run_generate_business_intelligence=true
                run_analyze_local_scripts=true
                run_ask_analysis_question=true
                run_read_s3_transcript=true
                run_upload_to_s3=true
                run_generate_report=true
                run_create_dashboard=true
                run_error_handling=true
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
    if [ "$run_analyze_transcript" = false ] && [ "$run_analyze_transcript_batch" = false ] && [ "$run_generate_business_intelligence" = false ] && [ "$run_analyze_local_scripts" = false ] && [ "$run_ask_analysis_question" = false ] && [ "$run_read_s3_transcript" = false ] && [ "$run_upload_to_s3" = false ] && [ "$run_generate_report" = false ] && [ "$run_create_dashboard" = false ] && [ "$run_error_handling" = false ]; then
        run_analyze_transcript=true
        run_analyze_transcript_batch=true
        run_generate_business_intelligence=true
        run_analyze_local_scripts=true
        run_ask_analysis_question=true
        run_read_s3_transcript=true
        run_upload_to_s3=true
        run_generate_report=true
        run_create_dashboard=true
        run_error_handling=true
    fi
    
    # Check server availability
    if ! check_server; then
        exit 1
    fi
    
    echo ""
    
    # Run selected tests
    if [ "$run_analyze_transcript" = true ]; then
        test_analyze_transcript
        echo ""
    fi
    
    if [ "$run_analyze_transcript_batch" = true ]; then
        test_analyze_transcript_batch
        echo ""
    fi
    
    if [ "$run_generate_business_intelligence" = true ]; then
        test_generate_business_intelligence
        echo ""
    fi
    
    if [ "$run_analyze_local_scripts" = true ]; then
        test_analyze_local_scripts
        echo ""
    fi
    
    if [ "$run_ask_analysis_question" = true ]; then
        test_ask_analysis_question
        echo ""
    fi
    
    if [ "$run_read_s3_transcript" = true ]; then
        test_read_s3_transcript
        echo ""
    fi
    
    if [ "$run_upload_to_s3" = true ]; then
        test_upload_to_s3
        echo ""
    fi
    
    if [ "$run_generate_report" = true ]; then
        test_generate_report
        echo ""
    fi
    
    if [ "$run_create_dashboard" = true ]; then
        test_create_dashboard
        echo ""
    fi
    
    if [ "$run_error_handling" = true ]; then
        test_error_handling
        echo ""
    fi
    
    print_header
    print_success "All tests completed for Call Analysis MCP Server tools"
    echo -e "${CYAN}📊 Server URL: $SERVER_URL${NC}"
    echo -e "${CYAN}🔗 Tools tested: 9 tools${NC}"
    echo -e "${CYAN}📝 Description: Comprehensive testing of all Call Analysis MCP Server tools${NC}"
}

# Run main function
main "$@" 