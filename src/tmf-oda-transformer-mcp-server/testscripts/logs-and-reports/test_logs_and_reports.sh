#!/bin/bash

# =============================================================================
# TMF ODA Transformer MCP Server - Logs and Reports Tool Test
# =============================================================================
# 
# This script comprehensively tests the logs-and-reports tool to ensure:
# 1. Job logs can be retrieved based on journey, stage, and step
# 2. Detailed reports can be generated for jobs
# 3. Log filtering and search capabilities work correctly
# 4. Report generation and analysis features function properly
# 5. Integration with run-jobs tool provides end-to-end functionality
#
# Usage: ./test_logs_and_reports.sh [URL] [journey_id]
# Example: ./test_logs_and_reports.sh http://18.191.87.212:8000 JRN-3E639E2E6F91
#
# =============================================================================

set -euo pipefail

# Default configuration
DEFAULT_URL="http://localhost:8000"
SERVER_URL="$DEFAULT_URL"

# Function to parse URL and extract components
parse_url() {
    local url="$1"
    
    # Remove protocol (http:// or https://)
    local url_no_protocol="${url#http://}"
    url_no_protocol="${url_no_protocol#https://}"
    
    # Extract host and port
    if [[ "$url_no_protocol" == *":"* ]]; then
        HOST="${url_no_protocol%:*}"
        PORT="${url_no_protocol#*:}"
        # Remove any path after port
        PORT="${PORT%%/*}"
    else
        HOST="$url_no_protocol"
        # Remove any path after host
        HOST="${HOST%%/*}"
        PORT="8000"  # Default port
    fi
    
    # Reconstruct the URL
    if [[ "$url" == https://* ]]; then
        SERVER_URL="https://$HOST:$PORT"
    else
        SERVER_URL="http://$HOST:$PORT"
    fi
}

# Function to show usage
show_usage() {
    echo -e "TMF ODA Transformer MCP Server - Logs and Reports Tool Test"
    echo ""
    echo -e "Usage: $0 [URL] [journey_id]"
    echo ""
    echo -e "Arguments:"
    echo -e "  URL                    MCP server URL (default: $DEFAULT_URL)"
    echo -e "  journey_id             Journey ID to test with (optional)"
    echo ""
    echo -e "Examples:"
    echo -e "  $0                                            # Test on localhost:8000"
    echo -e "  $0 http://192.168.1.100:9000                  # Test on remote server"
    echo -e "  $0 http://18.191.87.212:8000 JRN-DEMO-001     # Test specific journey on remote server"
    echo -e "  $0 https://api.company.com                    # Use HTTPS connection"
    echo ""
    echo -e "Description:"
    echo -e "  Comprehensively tests the logs-and-reports tool functionality."
    echo ""
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            http://*|https://*)
                parse_url "$1"
                shift
                ;;
            -*)
                echo -e "❌ Unknown option: $1"
                echo -e "💡 Use URL format instead: $0 http://host:port"
                show_usage
                exit 1
                ;;
            *)
                # This is the journey_id
                JOURNEY_ID="$1"
                shift
                ;;
        esac
    done
}

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0" .sh)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$SCRIPT_DIR/../logs"
LOG_FILE="$LOG_DIR/${SCRIPT_NAME}_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test statistics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test data arrays for comprehensive testing
STAGE_IDS=("raw_analysis" "stripped_schema")
STEP_NAMES=("schema_parsing" "relationship_discovery" "data_type_analysis" "business_rules_extraction")
LOG_LEVELS=("info" "warning" "error" "debug")
REPORT_TYPES=("summary" "performance" "error_analysis" "custom")

# Job IDs collected during testing (will be populated)
JOB_IDS=()

# Parse command line arguments first
parse_arguments "$@"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_message() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    case "$level" in
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ️ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️ $message${NC}" ;;
        "STEP") echo -e "${PURPLE}📋 $message${NC}" ;;
        *) echo "$message" ;;
    esac
}

print_header() {
    local title="$1"
    echo
    echo -e "${CYAN}=============================================="
    echo -e "$title"
    echo -e "==============================================${NC}"
    echo
}

print_separator() {
    echo -e "${CYAN}----------------------------------------------${NC}"
}

make_request() {
    local url="$1"
    local data="$2"
    local description="$3"
    
    log_message "INFO" "Testing: $description"
    echo "Request to $url:" >> "$LOG_FILE"
    echo "$data" >> "$LOG_FILE"
    
    local response=$(curl -s -X POST "$SERVER_URL$url" \
        -H "Content-Type: application/json" \
        -d "$data")
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo "Response:" >> "$LOG_FILE"
    echo "$response" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$response" >> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        local status=$(echo "$response" | jq -r '.result.status // "unknown"' 2>/dev/null || echo "unknown")
        
        if [ "$status" = "success" ]; then
            log_message "SUCCESS" "$description"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            echo "$response"
            return 0
        else
            local error_msg=$(echo "$response" | jq -r '.result.message // .error // "Unknown error"' 2>/dev/null || echo "Parse error")
            log_message "ERROR" "$description failed: $error_msg"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    else
        log_message "ERROR" "$description failed: Request failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# =============================================================================
# MAIN SCRIPT LOGIC
# =============================================================================

main() {
    # Print script header
    print_header "🔍📊 TMF ODA Transformer - Logs and Reports Tool Test"
    log_message "INFO" "Script: $SCRIPT_NAME"
    log_message "INFO" "Timestamp: $TIMESTAMP"
    log_message "INFO" "Log file: $LOG_FILE"
    log_message "INFO" "Server URL: $SERVER_URL"
    
    echo "=============================================="
    echo "Script: $SCRIPT_NAME"
    echo "Timestamp: $TIMESTAMP"
    echo "Log file: $LOG_FILE"
    echo "Server URL: $SERVER_URL"
    echo "=============================================="
    
    # Step 1: Get or validate journey ID
    if [ $# -ge 1 ]; then
        JOURNEY_ID="$1"
        log_message "INFO" "Using provided Journey ID: $JOURNEY_ID"
    else
        print_header "📋 Step 1: Get existing journey ID from user"
        echo "🔍 Please provide an existing journey ID to test with:"
        echo "Examples: JRN-12345, JRN-E9D56FE92D0F, JRN-42C3AFF148AD"
        echo
        read -p "Enter Journey ID: " JOURNEY_ID
        
        if [ -z "$JOURNEY_ID" ]; then
            log_message "ERROR" "Journey ID cannot be empty"
            exit 1
        fi
    fi
    
    log_message "INFO" "📋 Using Journey ID: $JOURNEY_ID"
    echo -e "${GREEN}✅ Using Journey ID: $JOURNEY_ID${NC}"
    
    # Step 2: Verify journey exists
    print_header "📋 Step 2: Verify journey exists"
    
    VERIFY_JOURNEY_DATA='{
        "action": "read",
        "journey_id": "'$JOURNEY_ID'"
    }'
    
    log_message "INFO" "Verifying journey exists..."
    VERIFY_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d "$VERIFY_JOURNEY_DATA")
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $? -eq 0 ]; then
        STATUS=$(echo "$VERIFY_RESPONSE" | jq -r '.result.status // "unknown"')
        
        if [ "$STATUS" = "success" ]; then
            log_message "SUCCESS" "✅ Journey verification successful"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            
            JOURNEY_NAME=$(echo "$VERIFY_RESPONSE" | jq -r '.result.journey.name // "Unknown"')
            JOURNEY_STATUS=$(echo "$VERIFY_RESPONSE" | jq -r '.result.journey.status // "unknown"')
            TOTAL_STAGES=$(echo "$VERIFY_RESPONSE" | jq -r '.result.journey.stageSummary | keys | length // 0')
            
            log_message "INFO" "Journey Name: $JOURNEY_NAME"
            log_message "INFO" "Journey Status: $JOURNEY_STATUS"
            log_message "INFO" "Total Stages: $TOTAL_STAGES"
            
            echo -e "${GREEN}✅ Journey verified: $JOURNEY_NAME (Status: $JOURNEY_STATUS)${NC}"
        else
            log_message "ERROR" "❌ Journey verification failed"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            exit 1
        fi
    else
        log_message "ERROR" "❌ Journey verification request failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        exit 1
    fi
    
    # Step 3: Create some test jobs to generate logs and reports
    print_header "📋 Step 3: Create test jobs for log and report generation"
    
    log_message "INFO" "Creating test jobs for the first two stages..."
    
    for stage_id in "${STAGE_IDS[@]}"; do
        log_message "INFO" "Creating job for stage: $stage_id"
        
        JOB_DATA='{
            "journey_id": "'$JOURNEY_ID'",
            "stage_id": "'$stage_id'",
            "action": "run",
            "triggered_by": "logs-test-script",
            "reason": "Creating jobs for logs and reports testing",
            "wait_for_completion": true
        }'
        
        JOB_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
            -H "Content-Type: application/json" \
            -d "$JOB_DATA")
        
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if [ $? -eq 0 ]; then
            JOB_STATUS=$(echo "$JOB_RESPONSE" | jq -r '.result.status // "unknown"')
            
            if [ "$JOB_STATUS" = "success" ]; then
                JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.result.job_id // "unknown"')
                JOB_IDS+=("$JOB_ID")
                log_message "SUCCESS" "✅ Job created successfully: $JOB_ID for stage $stage_id"
                PASSED_TESTS=$((PASSED_TESTS + 1))
                
                # Small delay to allow logs to be generated
                sleep 2
            else
                log_message "ERROR" "❌ Job creation failed for stage $stage_id"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        else
            log_message "ERROR" "❌ Job creation request failed for stage $stage_id"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    done
    
    log_message "INFO" "Created ${#JOB_IDS[@]} test jobs: ${JOB_IDS[*]}"
    
    # Step 4: Test basic log retrieval
    print_header "📋 Step 4: Test Basic Log Retrieval"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        TEST_STAGE_ID="${STAGE_IDS[0]}"
        
        log_message "INFO" "Testing basic log retrieval for job: $TEST_JOB_ID"
        
        make_request "/tools/logs-and-reports" '{
            "action": "get_job_logs",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'",
            "stage_name": "'$TEST_STAGE_ID'",
            "limit": 50
        }' "Get basic job logs"
        
    else
        log_message "WARNING" "⚠️ No test jobs available for log testing"
    fi
    
    # Step 5: Test step-specific log retrieval
    print_header "📋 Step 5: Test Step-Specific Log Retrieval"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        TEST_STAGE_ID="${STAGE_IDS[0]}"
        
        for step_name in "${STEP_NAMES[@]}"; do
            log_message "INFO" "Testing step-specific logs for: $step_name"
            
            make_request "/tools/logs-and-reports" '{
                "action": "get_job_logs",
                "journey_id": "'$JOURNEY_ID'",
                "job_id": "'$TEST_JOB_ID'",
                "stage_name": "'$TEST_STAGE_ID'",
                "step_name": "'$step_name'",
                "include_details": true,
                "limit": 20
            }' "Get logs for step: $step_name"
        done
    fi
    
    # Step 6: Test log filtering by level
    print_header "📋 Step 6: Test Log Filtering by Level"
    
    for log_level in "${LOG_LEVELS[@]}"; do
        log_message "INFO" "Testing log filtering for level: $log_level"
        
        make_request "/tools/logs-and-reports" '{
            "action": "get_logs_by_level",
            "journey_id": "'$JOURNEY_ID'",
            "log_level": "'$log_level'",
            "limit": 30
        }' "Get logs by level: $log_level"
    done
    
    # Step 7: Test log search functionality
    print_header "📋 Step 7: Test Log Search Functionality"
    
    SEARCH_QUERIES=("schema" "processing" "completed" "analysis" "error")
    
    for search_query in "${SEARCH_QUERIES[@]}"; do
        log_message "INFO" "Testing log search for query: $search_query"
        
        make_request "/tools/logs-and-reports" '{
            "action": "search_logs",
            "journey_id": "'$JOURNEY_ID'",
            "search_query": "'$search_query'",
            "limit": 25
        }' "Search logs for: $search_query"
    done
    
    # Step 8: Test error summary functionality
    print_header "📋 Step 8: Test Error Summary Functionality"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        make_request "/tools/logs-and-reports" '{
            "action": "get_error_summary",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'"
        }' "Get error summary for job: $TEST_JOB_ID"
    fi
    
    # Step 9: Test available logs listing
    print_header "📋 Step 9: Test Available Logs Listing"
    
    make_request "/tools/logs-and-reports" '{
        "action": "list_available_logs",
        "journey_id": "'$JOURNEY_ID'"
    }' "List available logs for journey"
    
    # Step 10: Test basic report generation
    print_header "📋 Step 10: Test Basic Report Generation"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        make_request "/tools/logs-and-reports" '{
            "action": "get_job_reports",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'"
        }' "Get existing job reports"
    fi
    
    # Step 11: Test detailed report generation
    print_header "📋 Step 11: Test Detailed Report Generation"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        for report_type in "${REPORT_TYPES[@]}"; do
            log_message "INFO" "Testing $report_type report generation"
            
            # Create a safe report title
            REPORT_TITLE=$(echo "$report_type" | tr '_' ' ' | sed 's/\b\w/\U&/g')
            
            make_request "/tools/logs-and-reports" '{
                "action": "create_job_report",
                "journey_id": "'$JOURNEY_ID'",
                "job_id": "'$TEST_JOB_ID'",
                "report_type": "'$report_type'",
                "report_title": "'$REPORT_TITLE' Report for Job '$TEST_JOB_ID'"
            }' "Create $report_type report"
        done
    fi
    
    # Step 12: Test summary report generation
    print_header "📋 Step 12: Test Summary Report Generation"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        make_request "/tools/logs-and-reports" '{
            "action": "generate_summary_report",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'"
        }' "Generate comprehensive summary report"
    fi
    
    # Step 13: Test performance analysis
    print_header "📋 Step 13: Test Performance Analysis"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        make_request "/tools/logs-and-reports" '{
            "action": "analyze_job_performance",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'",
            "include_recommendations": true
        }' "Analyze job performance with recommendations"
        
        make_request "/tools/logs-and-reports" '{
            "action": "generate_performance_report",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'"
        }' "Generate detailed performance report"
    fi
    
    # Step 14: Test error pattern analysis
    print_header "📋 Step 14: Test Error Pattern Analysis"
    
    make_request "/tools/logs-and-reports" '{
        "action": "analyze_error_patterns",
        "journey_id": "'$JOURNEY_ID'",
        "analysis_period": "24h"
    }' "Analyze error patterns across journey"
    
    # Step 15: Test insights generation
    print_header "📋 Step 15: Test Insights Generation"
    
    make_request "/tools/logs-and-reports" '{
        "action": "generate_insights",
        "journey_id": "'$JOURNEY_ID'",
        "analysis_period": "24h"
    }' "Generate comprehensive insights"
    
    # Step 16: Test recommendations
    print_header "📋 Step 16: Test Recommendations"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        make_request "/tools/logs-and-reports" '{
            "action": "get_recommendations",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'"
        }' "Get improvement recommendations"
    fi
    
    # Step 17: Test log export functionality
    print_header "📋 Step 17: Test Log Export Functionality"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        
        EXPORT_FORMATS=("json" "csv" "txt")
        
        for format in "${EXPORT_FORMATS[@]}"; do
            log_message "INFO" "Testing log export in $format format"
            
            make_request "/tools/logs-and-reports" '{
                "action": "export_job_logs",
                "journey_id": "'$JOURNEY_ID'",
                "job_id": "'$TEST_JOB_ID'",
                "export_format": "'$format'",
                "output_file": "/tmp/job_logs_'$TEST_JOB_ID'_'$TIMESTAMP'.'$format'"
            }' "Export job logs in $format format"
        done
    fi
    
    # Step 18: Test advanced filtering combinations
    print_header "📋 Step 18: Test Advanced Filtering Combinations"
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        TEST_JOB_ID="${JOB_IDS[0]}"
        TEST_STAGE_ID="${STAGE_IDS[0]}"
        
        make_request "/tools/logs-and-reports" '{
            "action": "get_job_logs",
            "journey_id": "'$JOURNEY_ID'",
            "job_id": "'$TEST_JOB_ID'",
            "stage_name": "'$TEST_STAGE_ID'",
            "level_filter": "info",
            "step_filter": "schema_parsing",
            "include_details": true,
            "limit": 15
        }' "Get logs with combined filters (stage + level + step)"
        
        make_request "/tools/logs-and-reports" '{
            "action": "search_logs",
            "journey_id": "'$JOURNEY_ID'",
            "search_query": "completed",
            "level_filter": "info",
            "step_filter": "data_type_analysis",
            "limit": 10
        }' "Search logs with multiple filters"
    fi
    
    # Step 19: Test error handling
    print_header "📋 Step 19: Test Error Handling"
    
    # Test with missing required parameters
    make_request "/tools/logs-and-reports" '{
        "action": "get_job_logs"
    }' "Test missing journey_id (should fail)" || true
    
    make_request "/tools/logs-and-reports" '{
        "action": "get_job_logs",
        "journey_id": "'$JOURNEY_ID'"
    }' "Test missing job_id (should fail)" || true
    
    # Test with invalid action
    make_request "/tools/logs-and-reports" '{
        "action": "invalid_action",
        "journey_id": "'$JOURNEY_ID'"
    }' "Test invalid action (should fail)" || true
    
    # Test with non-existent job
    make_request "/tools/logs-and-reports" '{
        "action": "get_job_logs",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "JOB-NONEXISTENT-000"
    }' "Test non-existent job_id (should handle gracefully)" || true
    
    # Print final results
    print_header "📊 TEST RESULTS SUMMARY"
    
    echo "=============================================="
    echo "🎯 TMF ODA Logs and Reports Tool Test Summary"
    echo "=============================================="
    echo "Journey ID Used: $JOURNEY_ID"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed Tests: $PASSED_TESTS"
    echo "Failed Tests: $FAILED_TESTS"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo "Success Rate: 100%"
    else
        echo -e "${YELLOW}⚠️ Some tests failed${NC}"
        echo "Success Rate: $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%"
    fi
    
    echo "=============================================="
    echo ""
    echo "🎯 Logs and Reports Tool Test Summary:"
    echo "• ✅ Basic Log Retrieval - Tests getting job logs by journey/job"
    echo "• ✅ Step-Specific Logs - Tests getting logs by specific steps"
    echo "• ✅ Log Level Filtering - Tests filtering logs by level (error, warning, info, debug)"
    echo "• ✅ Log Search - Tests searching logs with various queries"
    echo "• ✅ Error Summary - Tests error analysis and summary generation"
    echo "• ✅ Available Logs - Tests listing available log sources"
    echo "• ✅ Report Generation - Tests creating various types of reports"
    echo "• ✅ Performance Analysis - Tests job performance analysis and recommendations"
    echo "• ✅ Error Pattern Analysis - Tests error pattern analysis across journey"
    echo "• ✅ Insights Generation - Tests generating insights from logs and metrics"
    echo "• ✅ Log Export - Tests exporting logs in multiple formats"
    echo "• ✅ Advanced Filtering - Tests combining multiple filters"
    echo "• ✅ Error Handling - Tests validation and error scenarios"
    echo ""
    echo "📋 Key Features Tested:"
    echo "• ✅ Journey/Stage/Step-based log retrieval"
    echo "• ✅ Detailed report generation for jobs"
    echo "• ✅ Log filtering and search capabilities"
    echo "• ✅ Performance analysis and recommendations"
    echo "• ✅ Error analysis and pattern detection"
    echo "• ✅ Multiple export formats"
    echo "• ✅ Comprehensive error handling"
    echo ""
    echo "=============================================="
    echo "🔧 Example API Calls for Journey $JOURNEY_ID:"
    echo "=============================================="
    
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        EXAMPLE_JOB_ID="${JOB_IDS[0]}"
        echo "Get Job Logs by Stage and Step:"
        echo "  curl -X POST $SERVER_URL/tools/logs-and-reports \\"
        echo "    -H 'Content-Type: application/json' \\"
        echo "    -d '{\"action\":\"get_job_logs\",\"journey_id\":\"$JOURNEY_ID\",\"job_id\":\"$EXAMPLE_JOB_ID\",\"stage_name\":\"raw_analysis\",\"step_name\":\"schema_parsing\"}'"
        echo ""
        echo "Generate Performance Report:"
        echo "  curl -X POST $SERVER_URL/tools/logs-and-reports \\"
        echo "    -H 'Content-Type: application/json' \\"
        echo "    -d '{\"action\":\"generate_performance_report\",\"journey_id\":\"$JOURNEY_ID\",\"job_id\":\"$EXAMPLE_JOB_ID\"}'"
        echo ""
        echo "Search Logs:"
        echo "  curl -X POST $SERVER_URL/tools/logs-and-reports \\"
        echo "    -H 'Content-Type: application/json' \\"
        echo "    -d '{\"action\":\"search_logs\",\"journey_id\":\"$JOURNEY_ID\",\"search_query\":\"schema\",\"level_filter\":\"info\"}'"
    fi
    
    echo "=============================================="
    echo "📁 Detailed logs saved to: $LOG_FILE"
    echo "🕒 Test completed at: $(date)"
    echo "=============================================="
    echo ""
    echo -e "${GREEN}🎉 Logs and Reports Tool test completed!${NC}"
    echo "=============================================="
    echo "✅ Journey ID used: $JOURNEY_ID"
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        echo "✅ Test jobs created: ${JOB_IDS[*]}"
    fi
    echo "✅ Log retrieval by journey/stage/step tested"
    echo "✅ Report generation and analysis tested"
    echo "✅ Advanced filtering and search tested"
    echo "✅ Error handling verified"
    echo ""
    echo "📊 Test Results:"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%"
    echo ""
    echo "📁 Detailed logs saved to: $LOG_FILE"
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Trap for cleanup on script exit
cleanup() {
    log_message "INFO" "Script execution completed"
}

trap cleanup EXIT

# Check if server is running
if ! curl -s "$SERVER_URL/tools" > /dev/null; then
    log_message "ERROR" "❌ MCP Server not accessible at $SERVER_URL"
    log_message "ERROR" "Please start the server first: cd /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server && python -m awslabs.tmf_oda_transformer_mcp_server.server"
    exit 1
fi

# Check if jq is available for JSON parsing
if ! command -v jq > /dev/null; then
    log_message "ERROR" "❌ jq is required for JSON parsing but not installed"
    log_message "ERROR" "Please install jq: apt-get update && apt-get install -y jq"
    exit 1
fi

# Execute main function
main 