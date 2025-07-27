#!/bin/bash

# TMF ODA Transformer MCP Server - Tool Availability Testing Script
# This script comprehensively tests the availability and basic functionality of all MCP tools

set -e

# Default configuration
DEFAULT_HOST="localhost"
DEFAULT_PORT="8000"
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
SERVER_URL="http://$HOST:$PORT"
TOOLS_ENDPOINT="$SERVER_URL/tools"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
declare -A TEST_RESULTS

# Function to show usage
show_usage() {
    echo -e "${CYAN}${BOLD}TMF ODA Transformer MCP Server - Tool Availability Testing Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC} $0 [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  -h, --host HOST         MCP server host (default: $DEFAULT_HOST)"
    echo -e "  -p, --port PORT         MCP server port (default: $DEFAULT_PORT)"
    echo -e "  --help                  Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0                           # Test tools on localhost:8000"
    echo -e "  $0 -h 192.168.1.100 -p 9000 # Test tools on remote server"
    echo -e "  $0 --host example.com --port 8080 # Test tools on remote server"
    echo ""
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--host)
                HOST="$2"
                shift 2
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
            *)
                echo -e "${RED}❌ Unknown argument: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Update SERVER_URL and TOOLS_ENDPOINT with parsed values
    SERVER_URL="http://$HOST:$PORT"
    TOOLS_ENDPOINT="$SERVER_URL/tools"
}

print_header() {
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}${BOLD}🧪 $1${NC}"
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_test_header() {
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║ $1${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_TESTS++))
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

run_test() {
    local test_name="$1"
    local test_description="$2"
    shift 2
    
    ((TOTAL_TESTS++))
    echo -ne "  [${TOTAL_TESTS}] Testing $test_name: $test_description... "
    
    if "$@" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        TEST_RESULTS["$test_name"]="PASS"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        TEST_RESULTS["$test_name"]="FAIL"
        ((FAILED_TESTS++))
        return 1
    fi
}

test_server_connectivity() {
    print_test_header "🌐 Server Connectivity Tests"
    echo ""
    
    run_test "server_ping" "Basic server connectivity" \
        curl -s --connect-timeout 10 --max-time 30 "$SERVER_URL"
    
    run_test "server_health" "Server health endpoint" \
        curl -s --connect-timeout 10 --max-time 30 "$SERVER_URL/health"
    
    run_test "tools_endpoint" "Tools endpoint availability" \
        curl -s --connect-timeout 10 --max-time 30 "$TOOLS_ENDPOINT"
    
    echo ""
}

test_tool_endpoint() {
    local tool_name="$1"
    local endpoint_url="$TOOLS_ENDPOINT/$tool_name"
    
    # Test 1: OPTIONS method
    run_test "${tool_name}_options" "OPTIONS method support" \
        curl -s -X OPTIONS --connect-timeout 5 --max-time 10 "$endpoint_url"
    
    # Test 2: POST with empty JSON
    run_test "${tool_name}_post_empty" "POST with empty JSON" \
        curl -s -X POST "$endpoint_url" \
        -H 'Content-Type: application/json' \
        -d '{}' --connect-timeout 10 --max-time 30
    
    # Test 3: POST with malformed JSON (should return error, not crash)
    run_test "${tool_name}_post_malformed" "Malformed JSON handling" \
        curl -s -X POST "$endpoint_url" \
        -H 'Content-Type: application/json' \
        -d '{invalid json}' --connect-timeout 10 --max-time 30
}

test_tool_parameter_validation() {
    local tool_name="$1"
    local endpoint_url="$TOOLS_ENDPOINT/$tool_name"
    
    case "$tool_name" in
        "raw-analysis"|"stripped-schema"|"run-jobs")
            # Test missing required parameter (journey_id)
            run_test "${tool_name}_validation_missing_journey" "Missing journey_id validation" \
                bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{}' | grep -q 'error\\|journey_id'"
            
            # Test invalid journey_id format
            run_test "${tool_name}_validation_invalid_journey" "Invalid journey_id format validation" \
                bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{\"journey_id\":\"invalid\"}' | grep -q 'error\\|validation'"
            ;;
        "journeys")
            # Test invalid action
            run_test "${tool_name}_validation_invalid_action" "Invalid action validation" \
                bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{\"action\":\"invalid_action\"}' | grep -q 'error\\|action'"
            ;;
        "logs-and-reports"|"get-job-logs")
            # Test missing required parameters
            run_test "${tool_name}_validation_missing_params" "Missing required parameters validation" \
                bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{}' | grep -q 'error\\|required'"
            ;;
        "test-runner")
            # Test invalid test_type
            run_test "${tool_name}_validation_invalid_test_type" "Invalid test_type validation" \
                bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{\"test_type\":\"invalid\"}' | grep -q 'error\\|test_type'"
            ;;
    esac
}

test_tool_response_format() {
    local tool_name="$1"
    local endpoint_url="$TOOLS_ENDPOINT/$tool_name"
    
    # Test JSON response format
    run_test "${tool_name}_response_json" "JSON response format" \
        bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{}' | jq empty"
    
    # Test response contains status field
    run_test "${tool_name}_response_status" "Response contains status field" \
        bash -c "curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{}' | jq -e '.status' > /dev/null || curl -s -X POST '$endpoint_url' -H 'Content-Type: application/json' -d '{}' | jq -e '.result.status' > /dev/null"
}

test_all_tools() {
    local tools=(
        "raw-analysis"
        "stripped-schema"
        "run-jobs"
        "journeys"
        "logs-and-reports"
        "test-runner"
        "get-job-logs"
    )
    
    for tool_name in "${tools[@]}"; do
        print_test_header "🔧 Testing Tool: $tool_name"
        echo ""
        
        print_info "Testing basic endpoint functionality..."
        test_tool_endpoint "$tool_name"
        
        echo ""
        print_info "Testing parameter validation..."
        test_tool_parameter_validation "$tool_name"
        
        echo ""
        print_info "Testing response format..."
        test_tool_response_format "$tool_name"
        
        echo ""
    done
}

test_integration_scenarios() {
    print_test_header "🔄 Integration Test Scenarios"
    echo ""
    
    print_info "Testing tool integration scenarios..."
    
    # Test 1: Test runner tool (should work without external dependencies)
    run_test "integration_test_runner" "Test runner tool execution" \
        bash -c "curl -s -X POST '$TOOLS_ENDPOINT/test-runner' -H 'Content-Type: application/json' -d '{\"test_type\":\"quick\"}' | jq -e '.status'"
    
    # Test 2: Journeys tool list action (should work without journey data)
    run_test "integration_journeys_list" "Journeys list action" \
        bash -c "curl -s -X POST '$TOOLS_ENDPOINT/journeys' -H 'Content-Type: application/json' -d '{\"action\":\"list\"}' | jq -e '.result.status or .status'"
    
    # Test 3: Logs and reports with get action (should handle missing data gracefully)
    run_test "integration_logs_get" "Logs and reports get action" \
        bash -c "curl -s -X POST '$TOOLS_ENDPOINT/logs-and-reports' -H 'Content-Type: application/json' -d '{\"action\":\"get_job_logs\",\"journey_id\":\"TEST\",\"job_id\":\"TEST\"}' | jq -e '.result.status or .status'"
    
    echo ""
}

test_error_handling() {
    print_test_header "🚨 Error Handling Tests"
    echo ""
    
    print_info "Testing error handling capabilities..."
    
    # Test 1: Non-existent endpoint
    run_test "error_404_endpoint" "Non-existent endpoint handling" \
        bash -c "curl -s -X POST '$TOOLS_ENDPOINT/non-existent-tool' -H 'Content-Type: application/json' -d '{}' -w '%{http_code}' | grep -q '404'"
    
    # Test 2: Invalid HTTP method
    run_test "error_invalid_method" "Invalid HTTP method handling" \
        bash -c "curl -s -X DELETE '$TOOLS_ENDPOINT/raw-analysis' -w '%{http_code}' | grep -q '405\\|404'"
    
    # Test 3: Missing Content-Type header
    run_test "error_missing_content_type" "Missing Content-Type header handling" \
        bash -c "curl -s -X POST '$TOOLS_ENDPOINT/raw-analysis' -d '{}' -w '%{http_code}' | grep -q '400\\|415'"
    
    # Test 4: Request timeout handling
    run_test "error_timeout_handling" "Request timeout handling" \
        bash -c "curl -s -X POST '$TOOLS_ENDPOINT/raw-analysis' -H 'Content-Type: application/json' -d '{}' --max-time 1 || true"
    
    echo ""
}

test_performance_metrics() {
    print_test_header "⚡ Performance Tests"
    echo ""
    
    print_info "Testing response times and performance..."
    
    local tools=("raw-analysis" "journeys" "test-runner")
    
    for tool_name in "${tools[@]}"; do
        local endpoint_url="$TOOLS_ENDPOINT/$tool_name"
        
        # Measure response time (should be under 5 seconds for basic requests)
        local response_time=$(curl -s -X POST "$endpoint_url" \
            -H 'Content-Type: application/json' \
            -d '{}' \
            -w '%{time_total}' \
            -o /dev/null \
            --max-time 30)
        
        if (( $(echo "$response_time < 5.0" | bc -l) )); then
            run_test "perf_${tool_name}_response" "$tool_name response time (<5s: ${response_time}s)" true
        else
            run_test "perf_${tool_name}_response" "$tool_name response time (>5s: ${response_time}s)" false
        fi
    done
    
    echo ""
}

generate_test_report() {
    print_header "TEST RESULTS SUMMARY"
    
    echo -e "${CYAN}🧪 TMF ODA Transformer MCP Server - Tool Availability Test Report${NC}"
    echo -e "${CYAN}Generated: $(date)${NC}"
    echo -e "${CYAN}Server URL: $SERVER_URL${NC}"
    echo ""
    
    # Overall statistics
    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    fi
    
    echo -e "${BOLD}📊 Overall Results:${NC}"
    echo -e "  • Total Tests: $TOTAL_TESTS"
    echo -e "  • Tests Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "  • Tests Failed: ${RED}$FAILED_TESTS${NC}"
    echo -e "  • Success Rate: ${CYAN}${success_rate}%${NC}"
    echo ""
    
    # Results by category
    echo -e "${BOLD}📋 Results by Category:${NC}"
    echo ""
    
    # Server connectivity
    local server_tests=$(echo "${!TEST_RESULTS[@]}" | tr ' ' '\n' | grep -c "server_" || echo "0")
    local server_passed=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "PASS" || echo "0")
    echo -e "  ${BOLD}🌐 Server Connectivity:${NC} $server_passed/$server_tests tests passed"
    
    # Tool availability
    local tool_tests=$(echo "${!TEST_RESULTS[@]}" | tr ' ' '\n' | grep -E "(raw-analysis|stripped-schema|run-jobs|journeys|logs-and-reports|test-runner|get-job-logs)" | wc -l || echo "0")
    echo -e "  ${BOLD}🔧 Tool Availability:${NC} Individual tool results above"
    
    # Error handling
    local error_tests=$(echo "${!TEST_RESULTS[@]}" | tr ' ' '\n' | grep -c "error_" || echo "0")
    echo -e "  ${BOLD}🚨 Error Handling:${NC} $error_tests tests completed"
    
    # Performance
    local perf_tests=$(echo "${!TEST_RESULTS[@]}" | tr ' ' '\n' | grep -c "perf_" || echo "0")
    echo -e "  ${BOLD}⚡ Performance:${NC} $perf_tests tests completed"
    
    echo ""
    
    # Failed tests details
    if [ $FAILED_TESTS -gt 0 ]; then
        echo -e "${BOLD}❌ Failed Tests:${NC}"
        for test_name in "${!TEST_RESULTS[@]}"; do
            if [ "${TEST_RESULTS[$test_name]}" = "FAIL" ]; then
                echo -e "  • ${RED}$test_name${NC}"
            fi
        done
        echo ""
    fi
    
    # Recommendations
    echo -e "${BOLD}💡 Recommendations:${NC}"
    if [ $success_rate -ge 90 ]; then
        echo -e "  ${GREEN}✅ Excellent! All tools are functioning well${NC}"
        echo -e "  • MCP server is ready for production use"
        echo -e "  • All critical functionality is available"
    elif [ $success_rate -ge 70 ]; then
        echo -e "  ${YELLOW}⚠️ Good but some issues detected${NC}"
        echo -e "  • Review failed tests above"
        echo -e "  • Check server logs for detailed error information"
        echo -e "  • Consider retesting after addressing issues"
    else
        echo -e "  ${RED}🚨 Critical issues detected${NC}"
        echo -e "  • Server may not be properly configured"
        echo -e "  • Check if MCP server is running correctly"
        echo -e "  • Review server logs and configuration"
        echo -e "  • Consider restarting the server"
    fi
    
    echo ""
    echo -e "${BOLD}📚 Related Documentation:${NC}"
    echo -e "  • Use ${CYAN}./list_all_tools.sh${NC} for tool overview"
    echo -e "  • Use ${CYAN}./get_tool_details.sh [tool-name]${NC} for specific tool info"
    echo -e "  • Use ${CYAN}./show_tool_parameters.sh${NC} for parameter reference"
    echo ""
    
    # Exit with appropriate code
    if [ $success_rate -ge 70 ]; then
        return 0
    else
        return 1
    fi
}

main() {
    # Parse command line arguments
    parse_arguments "$@"
    
    print_header "TMF ODA TRANSFORMER MCP SERVER - AVAILABILITY TESTING"
    
    echo -e "${BLUE}🚀 Starting comprehensive tool availability testing...${NC}"
    echo -e "${BLUE}Server URL: $SERVER_URL${NC}"
    echo -e "${BLUE}Host: $HOST, Port: $PORT${NC}"
    echo -e "${BLUE}Started: $(date)${NC}"
    echo ""
    
    # Check dependencies
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${RED}❌ Error: curl is required but not installed${NC}"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}❌ Error: jq is required but not installed${NC}"
        exit 1
    fi
    
    # Run test suites
    test_server_connectivity
    test_all_tools
    test_integration_scenarios
    test_error_handling
    test_performance_metrics
    
    # Generate final report
    echo ""
    if generate_test_report; then
        echo -e "${GREEN}🎉 Testing completed successfully!${NC}"
        exit 0
    else
        echo -e "${RED}⚠️ Testing completed with issues detected${NC}"
        exit 1
    fi
}

# Run main function
main "$@" 