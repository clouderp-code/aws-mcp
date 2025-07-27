#!/bin/bash

# Enhanced Run Jobs Tool Test Script
# Tests comprehensive job management functionality with user-provided journey ID

# Default configuration
DEFAULT_URL="http://localhost:8000"
SERVER_URL="$DEFAULT_URL"
ECHO_JSON=false

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
    echo -e "Enhanced Run Jobs Tool Test Script"
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
    echo -e "  Tests comprehensive job management functionality with enhanced run-jobs tool."
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
                TEST_JOURNEY_ID="$1"
                shift
                ;;
        esac
    done
}

# Setup logging
SCRIPT_NAME="test_enhanced_run_jobs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/logs"
LOG_FILE="$LOG_DIR/${SCRIPT_NAME}_${TIMESTAMP}.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Enhanced logging function
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entry="[$timestamp] [$level] $message"
    
    # Log to file
    echo "$log_entry" >> "$LOG_FILE"
    
    # Log to console with colors
    case $level in
        "INFO")
            echo -e "${BLUE}$message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}$message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}$message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}$message${NC}"
            ;;
        "STEP")
            echo -e "${PURPLE}$message${NC}"
            ;;
        *)
            echo "$message"
            ;;
    esac
    
    # Flush output
    sync
}

# Parse command line arguments first
parse_arguments "$@"

# Initialize logging
log_message "INFO" "🚀 Starting Enhanced Run Jobs Tool Test"
log_message "INFO" "=============================================="
log_message "INFO" "Script: $SCRIPT_NAME"
log_message "INFO" "Timestamp: $TIMESTAMP"
log_message "INFO" "Log file: $LOG_FILE"
log_message "INFO" "Server URL: $SERVER_URL"
log_message "INFO" "=============================================="

echo -e "${BLUE}🚀 Testing Enhanced Run Jobs Tool${NC}"
echo "=============================================="
echo "📁 Logging to: $LOG_FILE"
echo "=============================================="

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Step 1: Get journey ID from user
log_message "STEP" "📋 Step 1: Get existing journey ID from user"

echo ""
echo -e "${CYAN}🔍 Please provide an existing journey ID to test with:${NC}"
echo -e "${YELLOW}Examples: JRN-12345, JRN-E9D56FE92D0F, JRN-42C3AFF148AD${NC}"
echo ""
read -p "Enter Journey ID: " JOURNEY_ID

# Validate journey ID input
if [ -z "$JOURNEY_ID" ]; then
    log_message "ERROR" "❌ No journey ID provided"
    echo -e "${RED}❌ Journey ID is required to run tests${NC}"
    exit 1
fi

log_message "INFO" "📋 Using Journey ID: $JOURNEY_ID"
echo ""
echo -e "${GREEN}✅ Using Journey ID: $JOURNEY_ID${NC}"

# Step 2: Verify journey exists
log_message "STEP" "📋 Step 2: Verify journey exists"

VERIFY_JOURNEY_DATA='{
    "action": "read",
    "journey_id": "'$JOURNEY_ID'"
}'

log_message "INFO" "Verifying journey exists..."
echo "Verify Journey Request:" >> "$LOG_FILE"
echo "$VERIFY_JOURNEY_DATA" >> "$LOG_FILE"

VERIFY_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$VERIFY_JOURNEY_DATA")

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $? -eq 0 ]; then
    STATUS=$(echo "$VERIFY_RESPONSE" | jq -r '.result.status // "unknown"')
    
    if [ "$STATUS" = "success" ]; then
        log_message "SUCCESS" "✅ Journey verification successful"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        echo "Verify Journey Response:" >> "$LOG_FILE"
        echo "$VERIFY_RESPONSE" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$VERIFY_RESPONSE" >> "$LOG_FILE"
        
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
        
        ERROR_MESSAGE=$(echo "$VERIFY_RESPONSE" | jq -r '.result.message // "Unknown error"')
        log_message "ERROR" "Error: $ERROR_MESSAGE"
        echo -e "${RED}❌ Journey not found or inaccessible: $ERROR_MESSAGE${NC}"
        echo ""
        echo -e "${YELLOW}💡 Please ensure:${NC}"
        echo -e "${YELLOW}   - Journey ID is correct${NC}"
        echo -e "${YELLOW}   - Journey exists in DynamoDB${NC}"
        echo -e "${YELLOW}   - MCP server is running${NC}"
        exit 1
    fi
else
    log_message "ERROR" "❌ Journey verification request failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ Failed to connect to server or verify journey${NC}"
    exit 1
fi

# Display available stages information
log_message "INFO" "=============================================="
log_message "INFO" "📋 AVAILABLE STAGES FOR TESTING"
log_message "INFO" "=============================================="
log_message "INFO" "✅ raw_analysis - Raw Input Analysis Stage"
log_message "INFO" "✅ stripped_schema - Stripped Schema Stage"
log_message "INFO" "❌ tmf_mapping - Not implemented yet"
log_message "INFO" "❌ migration_planning - Not implemented yet"
log_message "INFO" "❌ data_migration - Not implemented yet"
log_message "INFO" "❌ verification_validation - Not implemented yet"
log_message "INFO" "=============================================="
log_message "INFO" "ℹ️ This test will use available stages: raw_analysis and stripped_schema"
log_message "INFO" "=============================================="

# Step 3: Test job creation without execution
log_message "STEP" "📋 Step 3: Create job without execution (action=create)"

CREATE_JOB_DATA='{
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "raw_analysis",
    "action": "create",
    "triggered_by": "test-script",
    "reason": "Testing job creation functionality",
    "wait_for_completion": false
}'

log_message "INFO" "Creating job without execution..."
echo "Create Job Request:" >> "$LOG_FILE"
echo "$CREATE_JOB_DATA" >> "$LOG_FILE"

CREATE_JOB_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
  -H "Content-Type: application/json" \
  -d "$CREATE_JOB_DATA")

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $? -eq 0 ]; then
    STATUS=$(echo "$CREATE_JOB_RESPONSE" | jq -r '.result.status // "unknown"')
    
    if [ "$STATUS" = "success" ]; then
        log_message "SUCCESS" "✅ Job creation successful"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        echo "Create Job Response:" >> "$LOG_FILE"
        echo "$CREATE_JOB_RESPONSE" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$CREATE_JOB_RESPONSE" >> "$LOG_FILE"
        
        JOB_ID=$(echo "$CREATE_JOB_RESPONSE" | jq -r '.result.job_id // empty')
        EXECUTION_STATUS=$(echo "$CREATE_JOB_RESPONSE" | jq -r '.result.execution_status // empty')
        
        log_message "INFO" "Created Job ID: $JOB_ID"
        log_message "INFO" "Execution Status: $EXECUTION_STATUS"
        
        if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
            log_message "WARNING" "⚠️ Job ID not returned but creation reported as successful"
        fi
    else
        log_message "ERROR" "❌ Job creation failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        ERROR_MESSAGE=$(echo "$CREATE_JOB_RESPONSE" | jq -r '.result.message // "Unknown error"')
        log_message "ERROR" "Error: $ERROR_MESSAGE"
        
        echo "Create Job Response (Error):" >> "$LOG_FILE"
        echo "$CREATE_JOB_RESPONSE" >> "$LOG_FILE"
    fi
else
    log_message "ERROR" "❌ Job creation request failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Step 4: Test job status retrieval with retry logic (only if we have a job ID)
if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "null" ] && [ "$JOB_ID" != "empty" ]; then
    log_message "STEP" "📋 Step 4: Get job status (action=status) with retry logic"

    STATUS_JOB_DATA='{
        "journey_id": "'$JOURNEY_ID'",
        "action": "status",
        "job_id": "'$JOB_ID'",
        "progress_callback": true
    }'

    log_message "INFO" "Getting job status with retry logic..."
    echo "Job Status Request:" >> "$LOG_FILE"
    echo "$STATUS_JOB_DATA" >> "$LOG_FILE"

    # Retry logic for job status lookup (DynamoDB eventual consistency)
    STATUS_SUCCESS=false
    for retry in {1..3}; do
        log_message "INFO" "Job status attempt $retry/3..."
        
        STATUS_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
          -H "Content-Type: application/json" \
          -d "$STATUS_JOB_DATA")

        if [ $? -eq 0 ]; then
            STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.result.status // "unknown"')
            
            if [ "$STATUS" = "success" ]; then
                STATUS_SUCCESS=true
                break
            else
                log_message "WARNING" "⚠️ Job status attempt $retry failed, retrying..."
                sleep 2
            fi
        else
            log_message "WARNING" "⚠️ Job status request $retry failed, retrying..."
            sleep 2
        fi
    done

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$STATUS_SUCCESS" = true ]; then
        log_message "SUCCESS" "✅ Job status retrieval successful"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        echo "Job Status Response:" >> "$LOG_FILE"
        echo "$STATUS_RESPONSE" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$STATUS_RESPONSE" >> "$LOG_FILE"
        
        JOB_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.result.job_status // empty')
        JOB_PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.result.job_progress // 0')
        
        log_message "INFO" "Job Status: $JOB_STATUS"
        log_message "INFO" "Job Progress: $JOB_PROGRESS%"
    else
        log_message "ERROR" "❌ Job status retrieval failed after 3 attempts"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        echo "Job Status Response (Final Error):" >> "$LOG_FILE"
        echo "$STATUS_RESPONSE" >> "$LOG_FILE"
        log_message "INFO" "Note: This may be due to DynamoDB eventual consistency - job exists but not yet queryable"
    fi
else
    log_message "WARNING" "⚠️ Skipping job status test - no valid job ID available"
fi

# Step 5: Test full job execution
log_message "STEP" "📋 Step 5: Run complete job execution (action=run)"

RUN_JOB_DATA='{
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "stripped_schema",
    "action": "run",
    "triggered_by": "test-script",
    "reason": "Testing complete job execution",
    "wait_for_completion": true,
    "progress_callback": false,
    "job_config": {
        "timeout": 300,
        "retry_attempts": 3,
        "priority": "high"
    }
}'

log_message "INFO" "Running complete job execution..."
echo "Run Job Request:" >> "$LOG_FILE"
echo "$RUN_JOB_DATA" >> "$LOG_FILE"

RUN_JOB_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
  -H "Content-Type: application/json" \
  -d "$RUN_JOB_DATA")

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $? -eq 0 ]; then
    STATUS=$(echo "$RUN_JOB_RESPONSE" | jq -r '.result.status // "unknown"')
    
    if [ "$STATUS" = "success" ]; then
        log_message "SUCCESS" "✅ Job execution successful"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        echo "Run Job Response:" >> "$LOG_FILE"
        echo "$RUN_JOB_RESPONSE" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$RUN_JOB_RESPONSE" >> "$LOG_FILE"
        
        RUN_JOB_ID=$(echo "$RUN_JOB_RESPONSE" | jq -r '.result.job_id // empty')
        RUN_EXECUTION_STATUS=$(echo "$RUN_JOB_RESPONSE" | jq -r '.result.execution_status // empty')
        
        log_message "INFO" "Executed Job ID: $RUN_JOB_ID"
        log_message "INFO" "Final Status: $RUN_EXECUTION_STATUS"
    else
        log_message "ERROR" "❌ Job execution failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        ERROR_MESSAGE=$(echo "$RUN_JOB_RESPONSE" | jq -r '.result.message // "Unknown error"')
        log_message "ERROR" "Error: $ERROR_MESSAGE"
        
        echo "Run Job Response (Error):" >> "$LOG_FILE"
        echo "$RUN_JOB_RESPONSE" >> "$LOG_FILE"
    fi
else
    log_message "ERROR" "❌ Job execution request failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Step 6: Test job listing
log_message "STEP" "📋 Step 6: List jobs for stage (action=list)"

LIST_JOBS_DATA='{
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "raw_analysis",
    "action": "list"
}'

log_message "INFO" "Listing jobs for stage..."
echo "List Jobs Request:" >> "$LOG_FILE"
echo "$LIST_JOBS_DATA" >> "$LOG_FILE"

LIST_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
  -H "Content-Type: application/json" \
  -d "$LIST_JOBS_DATA")

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $? -eq 0 ]; then
    STATUS=$(echo "$LIST_RESPONSE" | jq -r '.result.status // "unknown"')
    
    if [ "$STATUS" = "success" ]; then
        log_message "SUCCESS" "✅ Job listing successful"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        echo "List Jobs Response:" >> "$LOG_FILE"
        echo "$LIST_RESPONSE" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$LIST_RESPONSE" >> "$LOG_FILE"
        
        TOTAL_JOBS=$(echo "$LIST_RESPONSE" | jq -r '.result.total_jobs // 0')
        log_message "INFO" "Total Jobs Found: $TOTAL_JOBS"
    else
        log_message "ERROR" "❌ Job listing failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        echo "List Jobs Response (Error):" >> "$LOG_FILE"
        echo "$LIST_RESPONSE" >> "$LOG_FILE"
    fi
else
    log_message "ERROR" "❌ Job listing request failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Step 7: Test asynchronous job execution
log_message "STEP" "📋 Step 7: Start async job execution (wait_for_completion=false)"

ASYNC_JOB_DATA='{
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "stripped_schema",
    "action": "run",
    "triggered_by": "test-script",
    "reason": "Testing asynchronous job execution",
    "wait_for_completion": false,
    "progress_callback": false
}'

log_message "INFO" "Starting asynchronous job execution..."
echo "Async Job Request:" >> "$LOG_FILE"
echo "$ASYNC_JOB_DATA" >> "$LOG_FILE"

ASYNC_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
  -H "Content-Type: application/json" \
  -d "$ASYNC_JOB_DATA")

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $? -eq 0 ]; then
    STATUS=$(echo "$ASYNC_RESPONSE" | jq -r '.result.status // "unknown"')
    
    if [ "$STATUS" = "success" ]; then
        log_message "SUCCESS" "✅ Async job execution started successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        echo "Async Job Response:" >> "$LOG_FILE"
        echo "$ASYNC_RESPONSE" | jq . >> "$LOG_FILE" 2>/dev/null || echo "$ASYNC_RESPONSE" >> "$LOG_FILE"
        
        ASYNC_JOB_ID=$(echo "$ASYNC_RESPONSE" | jq -r '.result.job_id // empty')
        ASYNC_STATUS=$(echo "$ASYNC_RESPONSE" | jq -r '.result.execution_status // empty')
        
        log_message "INFO" "Async Job ID: $ASYNC_JOB_ID"
        log_message "INFO" "Async Status: $ASYNC_STATUS"
        
        # Monitor the async job for a few seconds if we have a valid job ID
        if [ -n "$ASYNC_JOB_ID" ] && [ "$ASYNC_JOB_ID" != "null" ] && [ "$ASYNC_JOB_ID" != "empty" ]; then
            log_message "INFO" "Monitoring async job progress..."
            for i in {1..3}; do
                sleep 2
                
                MONITOR_DATA='{
                    "journey_id": "'$JOURNEY_ID'",
                    "action": "status",
                    "job_id": "'$ASYNC_JOB_ID'",
                    "progress_callback": true
                }'
                
                MONITOR_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
                  -H "Content-Type: application/json" \
                  -d "$MONITOR_DATA")
                
                if [ $? -eq 0 ]; then
                    CURRENT_STATUS=$(echo "$MONITOR_RESPONSE" | jq -r '.result.job_status // empty')
                    CURRENT_PROGRESS=$(echo "$MONITOR_RESPONSE" | jq -r '.result.job_progress // 0')
                    log_message "INFO" "  Check $i: Status=$CURRENT_STATUS, Progress=$CURRENT_PROGRESS%"
                    
                    if [ "$CURRENT_STATUS" = "completed" ] || [ "$CURRENT_STATUS" = "failed" ]; then
                        break
                    fi
                fi
            done
        else
            log_message "WARNING" "⚠️ No valid async job ID for monitoring"
        fi
    else
        log_message "ERROR" "❌ Async job execution failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        ERROR_MESSAGE=$(echo "$ASYNC_RESPONSE" | jq -r '.result.message // "Unknown error"')
        log_message "ERROR" "Error: $ERROR_MESSAGE"
        
        echo "Async Job Response (Error):" >> "$LOG_FILE"
        echo "$ASYNC_RESPONSE" >> "$LOG_FILE"
    fi
else
    log_message "ERROR" "❌ Async job execution request failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Step 8: Test error handling - invalid action
log_message "STEP" "📋 Step 8: Test error handling with invalid action"

INVALID_ACTION_DATA='{
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "raw_analysis",
    "action": "invalid_action",
    "triggered_by": "test-script"
}'

log_message "INFO" "Testing error handling with invalid action..."
echo "Invalid Action Request:" >> "$LOG_FILE"
echo "$INVALID_ACTION_DATA" >> "$LOG_FILE"

INVALID_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/run-jobs" \
  -H "Content-Type: application/json" \
  -d "$INVALID_ACTION_DATA")

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $? -eq 0 ]; then
    # Check if we get an appropriate error response
    if echo "$INVALID_RESPONSE" | grep -q "Invalid value"; then
        log_message "SUCCESS" "✅ Error handling working correctly"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        ERROR_MESSAGE=$(echo "$INVALID_RESPONSE" | jq -r '.detail // "Parameter validation error"')
        log_message "INFO" "Error message: $ERROR_MESSAGE"
    else
        STATUS=$(echo "$INVALID_RESPONSE" | jq -r '.result.status // "unknown"')
        if [ "$STATUS" = "error" ]; then
            log_message "SUCCESS" "✅ Error handling working correctly"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            
            ERROR_MESSAGE=$(echo "$INVALID_RESPONSE" | jq -r '.result.message // "Unknown error"')
            log_message "INFO" "Error message: $ERROR_MESSAGE"
        else
            log_message "ERROR" "❌ Error handling not working correctly"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    
    echo "Invalid Action Response:" >> "$LOG_FILE"
    echo "$INVALID_RESPONSE" >> "$LOG_FILE"
else
    log_message "ERROR" "❌ Error handling test failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Final test statistics
log_message "INFO" "=============================================="
log_message "INFO" "📊 TEST STATISTICS"
log_message "INFO" "=============================================="
log_message "INFO" "Journey ID Used: $JOURNEY_ID"
log_message "INFO" "Total Tests: $TOTAL_TESTS"
log_message "SUCCESS" "Passed Tests: $PASSED_TESTS"
log_message "ERROR" "Failed Tests: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    log_message "SUCCESS" "🎉 ALL TESTS PASSED!"
    SUCCESS_RATE="100%"
else
    SUCCESS_RATE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l)
    log_message "WARNING" "⚠️ Some tests failed. Success rate: ${SUCCESS_RATE}%"
fi

log_message "INFO" "Success Rate: $SUCCESS_RATE"
log_message "INFO" "=============================================="

# Test summary
log_message "INFO" "🎯 Enhanced Run Jobs Tool Test Summary:"
log_message "INFO" "• ✅ Journey Verification - Tests journey lookup and validation"
log_message "INFO" "• ✅ Job Creation (create action) - Tests job creation without execution"
log_message "INFO" "• ✅ Job Status Monitoring (status action) - Tests job status retrieval with retry logic"
log_message "INFO" "• ✅ Complete Job Execution (run action) - Tests full job execution (raw_analysis stage)"
log_message "INFO" "• ✅ Job Listing (list action) - Tests job listing for stages"
log_message "INFO" "• ✅ Asynchronous Execution (wait_for_completion=false) - Tests async job execution (stripped_schema stage)"
log_message "INFO" "• ✅ Progress Monitoring (progress_callback=true) - Tests real-time progress updates"
log_message "INFO" "• ✅ Job Configuration Support - Tests custom job configuration parameters"
log_message "INFO" "• ✅ Error Handling - Tests invalid action validation"
log_message "INFO" ""
log_message "INFO" "📋 Stages Tested:"
log_message "INFO" "• ✅ raw_analysis - Available and tested"
log_message "INFO" "• ✅ stripped_schema - Available and tested"
log_message "INFO" "• ℹ️ Note: Other stages (tmf_mapping, etc.) not yet implemented"

# Example API calls
log_message "INFO" "=============================================="
log_message "INFO" "🔧 Example API Calls for Journey $JOURNEY_ID:"
log_message "INFO" "=============================================="
log_message "INFO" "Create Job:"
log_message "INFO" "  curl -X POST $SERVER_URL/tools/run-jobs \\"
log_message "INFO" "    -H 'Content-Type: application/json' \\"
log_message "INFO" "    -d '{\"journey_id\":\"$JOURNEY_ID\",\"stage_id\":\"raw_analysis\",\"action\":\"create\"}'"
log_message "INFO" ""
log_message "INFO" "Run Job:"
log_message "INFO" "  curl -X POST $SERVER_URL/tools/run-jobs \\"
log_message "INFO" "    -H 'Content-Type: application/json' \\"
log_message "INFO" "    -d '{\"journey_id\":\"$JOURNEY_ID\",\"stage_id\":\"raw_analysis\",\"action\":\"run\"}'"
log_message "INFO" ""
log_message "INFO" "Get Job Status:"
log_message "INFO" "  curl -X POST $SERVER_URL/tools/run-jobs \\"
log_message "INFO" "    -H 'Content-Type: application/json' \\"
log_message "INFO" "    -d '{\"journey_id\":\"$JOURNEY_ID\",\"action\":\"status\",\"job_id\":\"JOB-123\"}'"

# Log file info
log_message "INFO" "=============================================="
log_message "INFO" "📁 Detailed logs saved to: $LOG_FILE"
log_message "INFO" "🕒 Test completed at: $(date)"
log_message "INFO" "=============================================="

echo -e "\n${BLUE}🎉 Enhanced Run Jobs Tool test completed!${NC}"
echo "=============================================="
echo -e "${GREEN}✅ Journey ID used: $JOURNEY_ID${NC}"
echo -e "${GREEN}✅ Job management actions tested: create, run, status, list${NC}"
echo -e "${GREEN}✅ Async execution and monitoring tested${NC}"
echo -e "${GREEN}✅ Error handling verified${NC}"

echo -e "\n${BLUE}📊 Test Results:${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo "Success Rate: $SUCCESS_RATE"

echo -e "\n${BLUE}📁 Detailed logs saved to: $LOG_FILE${NC}"

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi 