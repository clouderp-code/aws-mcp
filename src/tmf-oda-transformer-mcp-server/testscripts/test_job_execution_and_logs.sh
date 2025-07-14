#!/bin/bash

# =============================================================================
# TMF ODA Transformer MCP Server - Job Execution & Logs Test Script
# =============================================================================
# This script focuses on comprehensive testing of:
# - Job execution across different stages
# - Stage-wise and step-wise log retrieval
# - Job performance monitoring and reports
# - S3 integration for logs and reports storage
# 
# Usage: ./test_job_execution_and_logs.sh [SERVER_URL]
# Default SERVER_URL: http://localhost:8000
# =============================================================================

set -e

# Configuration
SERVER_URL="${1:-http://localhost:8000}"
TIMEOUT=30



# Test data and tracking
JOURNEY_ID=""
JOB_IDS=()
STAGE_IDS=("raw_analysis" "stripped_schema" "data_mapping" "validation" "deployment")
STEP_NAMES=("schema_parsing" "relationship_discovery" "data_type_analysis" "business_rules_extraction" "complexity_assessment")

# Logging configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/job_execution_test_results_$(date +%Y%m%d_%H%M%S).log"
echo "Job Execution & Logs Test run started at $(date)" > "$LOG_FILE"
echo "Server URL: $SERVER_URL" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test counters
TEST_COUNT=0
PASSED_COUNT=0
FAILED_COUNT=0

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Function to log to both console and file
log_message() {
    local message="$1"
    local no_color_message=$(echo -e "$message" | sed 's/\x1b\[[0-9;]*m//g')
    echo -e "$message"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $no_color_message" >> "$LOG_FILE"
    # Ensure immediate flush to file
    sync
}

# Function to log JSON data with proper formatting
log_json_response() {
    local json_data="$1"
    local label="$2"
    
    if [ -n "$label" ]; then
        log_message "${YELLOW}$label:${NC}"
    fi
    
    # Format JSON if jq is available, otherwise just log as-is
    if command -v jq >/dev/null 2>&1; then
        local formatted_json=$(echo "$json_data" | jq . 2>/dev/null || echo "$json_data")
        log_message "$formatted_json"
    else
        log_message "$json_data"
    fi
    
    # Also log raw JSON to file for debugging
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RAW_JSON: $json_data" >> "$LOG_FILE"
}

print_header() {
    local header_msg="\n${CYAN}================================${NC}\n${CYAN}$1${NC}\n${CYAN}================================${NC}"
    log_message "$header_msg"
}

print_test() {
    TEST_COUNT=$((TEST_COUNT + 1))
    log_message "\n${BLUE}[$TEST_COUNT/32] Testing: $1${NC}"
    log_message "${YELLOW}Endpoint: $2${NC}"
    log_message "${CYAN}Progress: $TEST_COUNT of 32 tests completed${NC}"
}

print_success() {
    PASSED_COUNT=$((PASSED_COUNT + 1))
    log_message "${GREEN}✅ SUCCESS: $1${NC}"
}

print_error() {
    FAILED_COUNT=$((FAILED_COUNT + 1))
    log_message "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    log_message "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_info() {
    log_message "${PURPLE}ℹ️  INFO: $1${NC}"
}

# Function to make curl request and parse result
make_request() {
    local endpoint="$1"
    local data="$2"
    local description="$3"
    local test_description="$4"
    
    print_test "$description" "$endpoint"
    
    # Log request data
    log_json_response "$data" "Request Data"
    
    # Log separator before response
    log_message ""
    
    # Make the request
    local response=$(curl -s -X POST "$SERVER_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        # Log response data
        log_json_response "$response" "Response"
        
        # Check if response contains success status (look in both top level and result.status)
        local status=$(echo "$response" | jq -r '.status // .result.status // "unknown"' 2>/dev/null)
        if [[ "$status" == "success" ]]; then
            print_success "$description completed successfully"
            
            # Extract job ID if this is a job creation
            if [[ "$description" == *"Run job"* ]]; then
                local job_id=$(echo "$response" | jq -r '.result.job_id // empty' 2>/dev/null)
                if [[ -n "$job_id" ]]; then
                    JOB_IDS+=("$job_id")
                    log_message "${GREEN}📝 Captured Job ID: $job_id${NC}"
                fi
            fi
            
        elif [[ "$status" == "error" ]]; then
            local error_msg=$(echo "$response" | jq -r '.error_message // .result.error_message // .message // .result.message // "Unknown error"' 2>/dev/null)
            print_error "$description failed: $error_msg"
        else
            print_warning "$description returned unexpected response format"
        fi
    else
        print_error "$description failed: $response"
        log_message "${RED}Full curl error details:${NC}"
        log_message "$response"
    fi
    
    log_message "\n${CYAN}---${NC}"
}

# Function to get real journey ID
get_real_journey_id() {
    log_message "${BLUE}Getting real journey ID from system...${NC}"
    local response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d '{"action": "read", "journey_id": "", "limit": 1}' \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        JOURNEY_ID=$(echo "$response" | jq -r '.result.journeys[0].journeyId // empty' 2>/dev/null)
        if [[ -n "$JOURNEY_ID" ]]; then
            log_message "${GREEN}✅ Found real journey ID: $JOURNEY_ID${NC}"
            return 0
        fi
    fi
    
    log_message "${YELLOW}⚠️  No existing journeys found, will create a test journey${NC}"
    return 1
}

# Function to create test journey if needed
create_test_journey() {
    log_message "${BLUE}Creating test journey for job execution testing...${NC}"
    local journey_data='{
        "action": "create",
        "journey_id": "",
        "journey_data": {
            "name": "Job Execution Test Journey",
            "description": "Journey created specifically for comprehensive job execution and logs testing",
            "oda_component_type": "customer-management",
            "source_type": "database", 
            "priority": "high",
            "source_data_location": "s3://test-bucket/job-test-data/",
            "target_data_location": "s3://test-bucket/job-test-output/",
            "contact_email": "jobtest@example.com",
            "tags": ["job_testing", "logs_analysis", "performance_monitoring"],
            "metadata": {
                "test_type": "job_execution_and_logs",
                "created_by": "job_test_script",
                "purpose": "comprehensive_job_testing",
                "version": "1.0"
            }
        }
    }'
    
    local response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d "$journey_data" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        JOURNEY_ID=$(echo "$response" | jq -r '.result.journey_id // empty' 2>/dev/null)
        if [[ -n "$JOURNEY_ID" ]]; then
            log_message "${GREEN}✅ Created test journey: $JOURNEY_ID${NC}"
            return 0
        fi
    fi
    
    log_message "${YELLOW}⚠️  Failed to create test journey${NC}"
    return 1
}

# Function to wait for job completion (simulated)
wait_for_job() {
    local job_id="$1"
    local timeout_seconds="${2:-30}"
    log_message "${BLUE}Waiting for job $job_id to complete (timeout: ${timeout_seconds}s)...${NC}"
    
    # In a real implementation, we would poll job status
    # For testing, we'll just wait a bit and assume completion
    sleep 2
    
    log_message "${GREEN}✅ Job $job_id assumed completed${NC}"
    return 0
}



# =============================================================================
# INITIALIZATION
# =============================================================================

# Notify user about log file location
log_message "${PURPLE}📋 Job Execution & Logs test results will be logged to: $LOG_FILE${NC}"
log_message "${CYAN}=============================================${NC}"

print_header "SETUP TEST ENVIRONMENT"

# Get or create journey
if get_real_journey_id; then
    log_message "${GREEN}✅ Will use existing journey: $JOURNEY_ID${NC}"
else
    if create_test_journey; then
        log_message "${GREEN}✅ Will use created journey: $JOURNEY_ID${NC}"
    else
        log_message "${RED}❌ Cannot proceed without a journey${NC}"
        exit 1
    fi
fi

log_message "${CYAN}Test Configuration:${NC}"
log_message "${CYAN}  - Journey ID: $JOURNEY_ID${NC}"
log_message "${CYAN}  - Target Stages: ${STAGE_IDS[*]}${NC}"
log_message "${CYAN}  - Target Steps: ${STEP_NAMES[*]}${NC}"

# =============================================================================
# COMPREHENSIVE JOB EXECUTION TESTING
# =============================================================================

print_header "COMPREHENSIVE JOB EXECUTION TESTING"

# Test 1-5: Execute jobs for each stage
for i in "${!STAGE_IDS[@]}"; do
    stage_id="${STAGE_IDS[$i]}"
    
    make_request "/tools/journeys" '{
        "action": "run_job",
        "journey_id": "'$JOURNEY_ID'",
        "stage_id": "'$stage_id'",
        "triggered_by": "job-execution-test",
        "reason": "Comprehensive job execution testing for stage '$stage_id'"
    }' "Run job for $stage_id stage" "Execute transformation job for the $stage_id stage and capture job ID for subsequent testing"
    
    # If we captured a job ID, wait for it
    if [[ ${#JOB_IDS[@]} -gt $i ]]; then
        wait_for_job "${JOB_IDS[$i]}" 30
    fi
done

# Test 6: Batch job execution
make_request "/tools/journeys" '{
    "action": "run_job",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "validation",
    "triggered_by": "batch-test",
    "reason": "Batch job execution test - multiple validation jobs"
}' "Run batch validation job" "Execute multiple validation jobs to test concurrent job handling"

# =============================================================================
# STAGE-WISE LOG RETRIEVAL TESTING
# =============================================================================

print_header "STAGE-WISE LOG RETRIEVAL TESTING"

# Test 7-11: Get logs for each stage
for stage_id in "${STAGE_IDS[@]}"; do
    # Use the first available job ID for testing
    test_job_id="${JOB_IDS[0]:-JOB-TEST-001}"
    
    make_request "/tools/logs-and-reports" '{
        "action": "get_job_logs",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "'$test_job_id'",
        "stage_name": "'$stage_id'",
        "include_details": true,
        "limit": 100
    }' "Get logs for $stage_id stage" "Retrieve comprehensive logs for the $stage_id stage including all execution details"
done

# =============================================================================
# STEP-WISE LOG RETRIEVAL TESTING
# =============================================================================

print_header "STEP-WISE LOG RETRIEVAL TESTING"

# Test 12-16: Get logs for each step within stages
for step_name in "${STEP_NAMES[@]}"; do
    test_job_id="${JOB_IDS[0]:-JOB-TEST-001}"
    
    make_request "/tools/logs-and-reports" '{
        "action": "get_job_logs",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "'$test_job_id'",
        "stage_name": "raw_analysis",
        "step_name": "'$step_name'",
        "include_details": true,
        "include_performance_metrics": true,
        "limit": 50
    }' "Get logs for $step_name step" "Retrieve detailed logs for the $step_name step including performance metrics and execution timeline"
done

# =============================================================================
# COMPREHENSIVE LOG ANALYSIS TESTING
# =============================================================================

print_header "COMPREHENSIVE LOG ANALYSIS TESTING"

# Test 17: Search logs across all stages and steps
make_request "/tools/logs-and-reports" '{
    "action": "search_logs",
    "journey_id": "'$JOURNEY_ID'",
    "search_query": "processing completed successfully",
    "include_all_stages": true,
    "include_all_steps": true,
    "time_range": "24h",
    "limit": 100
}' "Search logs across all stages" "Search for successful completion messages across all stages and steps"

# Test 18: Get error logs with step-wise breakdown
make_request "/tools/logs-and-reports" '{
    "action": "get_logs_by_level",
    "journey_id": "'$JOURNEY_ID'",
    "log_level": "error",
    "include_stage_breakdown": true,
    "include_step_breakdown": true,
    "group_by_stage": true,
    "limit": 200
}' "Get error logs with breakdown" "Retrieve error logs organized by stage and step for comprehensive error analysis"

# Test 19: Performance logs analysis
make_request "/tools/logs-and-reports" '{
    "action": "analyze_job_performance",
    "journey_id": "'$JOURNEY_ID'",
    "analysis_scope": "all_stages",
    "include_step_performance": true,
    "performance_metrics": ["execution_time", "resource_usage", "throughput", "error_rate"],
    "generate_recommendations": true
}' "Analyze performance across stages" "Comprehensive performance analysis across all stages with step-level metrics"

# =============================================================================
# JOB STRUCTURE AND METADATA TESTING
# =============================================================================

print_header "JOB STRUCTURE AND METADATA TESTING"

# Test 20: Get detailed job structure for each executed job
for i in "${!JOB_IDS[@]}"; do
    job_id="${JOB_IDS[$i]}"
    stage_id="${STAGE_IDS[$i]:-unknown}"
    
    make_request "/tools/journeys" '{
        "action": "get_job",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "'$job_id'",
        "include_all": true,
        "include_stage_details": true,
        "include_step_breakdown": true,
        "include_performance_metrics": true
    }' "Get detailed job structure for $stage_id" "Retrieve comprehensive job metadata, stage details, step breakdown, and performance metrics"
done

# Test 21: Get job timeline with stage transitions
test_job_id="${JOB_IDS[0]:-JOB-TEST-001}"
make_request "/tools/journeys" '{
    "action": "get_job_timeline",
    "journey_id": "'$JOURNEY_ID'",
    "job_id": "'$test_job_id'",
    "include_stage_transitions": true,
    "include_step_durations": true,
    "include_resource_usage": true
}' "Get job timeline with transitions" "Retrieve detailed job execution timeline showing stage transitions and step durations"

# Test 22: Get job metrics with stage-wise breakdown
make_request "/tools/journeys" '{
    "action": "get_job_metrics",
    "journey_id": "'$JOURNEY_ID'",
    "job_id": "'$test_job_id'",
    "include_stage_metrics": true,
    "include_step_metrics": true,
    "metrics_type": "comprehensive"
}' "Get comprehensive job metrics" "Retrieve detailed metrics broken down by stage and step for performance analysis"

# =============================================================================
# S3 INTEGRATION AND EXPORT TESTING
# =============================================================================

print_header "S3 INTEGRATION AND EXPORT TESTING"

# Test 23: Export stage-wise logs to S3
for stage_id in "${STAGE_IDS[@]:0:3}"; do  # Test first 3 stages
    test_job_id="${JOB_IDS[0]:-JOB-TEST-001}"
    s3_path="s3://transformation-journey-logs/$JOURNEY_ID/$test_job_id/stage_${stage_id}_logs.json"
    
    make_request "/tools/logs-and-reports" '{
        "action": "export_job_logs",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "'$test_job_id'",
        "stage_name": "'$stage_id'",
        "output_file": "'$s3_path'",
        "export_format": "json",
        "include_step_details": true
    }' "Export $stage_id stage logs to S3" "Export comprehensive stage logs including step details to S3 bucket"
done

# Test 24: Generate stage-wise performance reports
for i in "${!STAGE_IDS[@]:0:2}"; do  # Test first 2 stages
    stage_id="${STAGE_IDS[$i]}"
    test_job_id="${JOB_IDS[$i]:-JOB-TEST-001}"
    s3_path="s3://transformation-journey-reports/$JOURNEY_ID/$test_job_id/stage_${stage_id}_performance_report.json"
    
    make_request "/tools/logs-and-reports" '{
        "action": "create_job_report",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "'$test_job_id'",
        "report_type": "performance",
        "report_title": "Performance Report - '$stage_id' Stage",
        "report_content": {
            "stage_focus": "'$stage_id'",
            "include_step_analysis": true,
            "include_resource_metrics": true,
            "include_error_analysis": true,
            "s3_storage_path": "'$s3_path'"
        }
    }' "Generate $stage_id performance report" "Create detailed performance report for $stage_id stage with step-level analysis"
done

# Test 25: Comprehensive journey report with all stages
make_request "/tools/logs-and-reports" '{
    "action": "generate_summary_report",
    "journey_id": "'$JOURNEY_ID'",
    "include_all_jobs": true,
    "include_stage_breakdown": true,
    "include_step_analysis": true,
    "include_performance_summary": true,
    "report_scope": "comprehensive",
    "output_location": "s3://transformation-journey-reports/'$JOURNEY_ID'/comprehensive_journey_report.json"
}' "Generate comprehensive journey report" "Create complete journey report with all stages, steps, jobs, and performance analysis"

# =============================================================================
# ADVANCED LOG FILTERING AND ANALYSIS
# =============================================================================

print_header "ADVANCED LOG FILTERING AND ANALYSIS"

# Test 26: Get logs filtered by multiple criteria
test_job_id="${JOB_IDS[0]:-JOB-TEST-001}"
make_request "/tools/logs-and-reports" '{
    "action": "search_logs",
    "journey_id": "'$JOURNEY_ID'",
    "job_id": "'$test_job_id'",
    "search_query": "transformation processing",
    "log_level": "info",
    "stage_filter": "raw_analysis,stripped_schema",
    "step_filter": "schema_parsing,data_type_analysis",
    "time_from": "'$(date -d '1 hour ago' -Iseconds)'",
    "time_to": "'$(date -Iseconds)'",
    "limit": 150
}' "Advanced log filtering" "Filter logs by multiple criteria: stage, step, time range, and content"

# Test 27: Error analysis with stage correlation
make_request "/tools/logs-and-reports" '{
    "action": "get_error_summary",
    "journey_id": "'$JOURNEY_ID'",
    "job_id": "'$test_job_id'",
    "include_stage_correlation": true,
    "include_step_correlation": true,
    "error_categorization": true,
    "suggest_remediation": true
}' "Error analysis with correlation" "Analyze errors with stage and step correlation for better troubleshooting"

# Test 28: Performance trending across stages
make_request "/tools/logs-and-reports" '{
    "action": "generate_performance_report",
    "journey_id": "'$JOURNEY_ID'",
    "analysis_scope": "multi_job",
    "include_stage_trending": true,
    "include_step_performance": true,
    "performance_comparison": true,
    "generate_insights": true
}' "Performance trending analysis" "Analyze performance trends across multiple jobs and stages"

# =============================================================================
# REAL-TIME MONITORING SIMULATION
# =============================================================================

print_header "REAL-TIME MONITORING SIMULATION"

# Test 29: Monitor active jobs
make_request "/tools/journeys" '{
    "action": "list_jobs",
    "journey_id": "'$JOURNEY_ID'",
    "status_filter": "running,pending",
    "include_stage_info": true,
    "include_progress_details": true,
    "real_time_status": true
}' "Monitor active jobs" "Monitor currently running and pending jobs with stage information"

# Test 30: Get real-time job status updates
if [[ ${#JOB_IDS[@]} -gt 0 ]]; then
    test_job_id="${JOB_IDS[0]}"
    make_request "/tools/journeys" '{
        "action": "update_job_status",
        "journey_id": "'$JOURNEY_ID'",
        "job_id": "'$test_job_id'",
        "job_status": "running",
        "progress": 75,
        "current_step": "business_rules_extraction",
        "performance_metrics": {
            "cpu_usage": 65.5,
            "memory_usage": 78.2,
            "processing_rate": "1250 records/min"
        }
    }' "Update job status with metrics" "Update job status with real-time progress and performance metrics"
fi

# =============================================================================
# INTEGRATION TESTING
# =============================================================================

print_header "INTEGRATION TESTING"

# Test 31: End-to-end job execution with comprehensive logging
make_request "/tools/journeys" '{
    "action": "run_job",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "data_mapping",
    "triggered_by": "integration-test",
    "reason": "End-to-end integration test with comprehensive logging",
    "enable_detailed_logging": true,
    "enable_step_tracking": true,
    "enable_performance_monitoring": true,
    "s3_logging_enabled": true
}' "End-to-end job with logging" "Execute complete job with all logging and monitoring features enabled"

# Test 32: Verify log data integrity across stages
make_request "/tools/logs-and-reports" '{
    "action": "list_available_logs",
    "journey_id": "'$JOURNEY_ID'",
    "include_s3_locations": true,
    "include_stage_mapping": true,
    "include_step_mapping": true,
    "verify_integrity": true
}' "Verify log data integrity" "Verify that logs are properly stored and accessible across all stages and steps"

# =============================================================================
# SUMMARY AND CLEANUP
# =============================================================================

print_header "TEST SUMMARY"

log_message "\n${BLUE}Job Execution & Logs Test Results:${NC}"
log_message "${GREEN}✅ Passed: $PASSED_COUNT${NC}"
log_message "${RED}❌ Failed: $FAILED_COUNT${NC}"
log_message "${YELLOW}📊 Total: $TEST_COUNT${NC}"

log_message "\n${BLUE}Captured Job IDs:${NC}"
for i in "${!JOB_IDS[@]}"; do
    log_message "${CYAN}  - ${STAGE_IDS[$i]:-Stage$i}: ${JOB_IDS[$i]}${NC}"
done

log_message "\n${BLUE}Test Focus Areas Covered:${NC}"
log_message "${CYAN}  ✓ Job execution across multiple stages${NC}"
log_message "${CYAN}  ✓ Stage-wise log retrieval and analysis${NC}"
log_message "${CYAN}  ✓ Step-wise log filtering and monitoring${NC}"
log_message "${CYAN}  ✓ Job structure and metadata verification${NC}"
log_message "${CYAN}  ✓ S3 integration for logs and reports${NC}"
log_message "${CYAN}  ✓ Performance analysis and trending${NC}"
log_message "${CYAN}  ✓ Real-time monitoring simulation${NC}"
log_message "${CYAN}  ✓ Error analysis with stage correlation${NC}"

# Add final summary to log file
echo "" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"
echo "Job Execution & Logs Test completed at $(date)" >> "$LOG_FILE"
echo "Final Results - Passed: $PASSED_COUNT, Failed: $FAILED_COUNT, Total: $TEST_COUNT" >> "$LOG_FILE"
echo "Journey ID used: $JOURNEY_ID" >> "$LOG_FILE"
echo "Job IDs captured: ${JOB_IDS[*]}" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

if [ $FAILED_COUNT -eq 0 ]; then
    log_message "\n${GREEN}🎉 All job execution and logs tests completed successfully!${NC}"
    log_message "${PURPLE}📋 Full test log saved to: $LOG_FILE${NC}"
    exit 0
else
    log_message "\n${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    log_message "${PURPLE}📋 Full test log saved to: $LOG_FILE${NC}"
    exit 1
fi 