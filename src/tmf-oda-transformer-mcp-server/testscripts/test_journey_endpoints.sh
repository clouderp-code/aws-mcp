#!/bin/bash

# =============================================================================
# TMF ODA Transformer MCP Server - Journey Tool Test Script
# =============================================================================
# This script tests all journey and logs endpoints based on the pytest test suite
# Usage: ./test_journey_endpoints.sh [SERVER_URL]
# Default SERVER_URL: http://localhost:8000
# =============================================================================

set -e

# Configuration
SERVER_URL="${1:-http://localhost:8000}"
TIMEOUT=30
SAMPLE_JOURNEY_ID="JRN-TEST-001"  # Will be replaced with real journey ID
SAMPLE_JOB_ID="JOB-001-20240101120000"  # Will be replaced with real job ID
SAMPLE_STAGE_ID="raw_analysis"
SAMPLE_RULE_ID="RULE-001"

# Variables to store real IDs during test execution
REAL_JOURNEY_ID=""
REAL_JOB_ID=""
CREATED_JOURNEY_ID=""
CREATED_JOB_ID=""

# Logging configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/test_journey_results_$(date +%Y%m%d_%H%M%S).log"
echo "Test run started at $(date)" > "$LOG_FILE"
echo "Server URL: $SERVER_URL" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counter
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
    log_message "\n${BLUE}[$TEST_COUNT/51] Testing: $1${NC}"
    log_message "${YELLOW}Endpoint: $2${NC}"
    log_message "${CYAN}Progress: $TEST_COUNT of 51 tests completed${NC}"
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

# Function to get real journey ID from system
get_real_journey_id() {
    log_message "${BLUE}Getting real journey ID from system...${NC}"
    local response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d '{"action": "read", "journey_id": "", "limit": 1}' \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        REAL_JOURNEY_ID=$(echo "$response" | jq -r '.result.journeys[0].journeyId // empty' 2>/dev/null)
        if [[ -n "$REAL_JOURNEY_ID" ]]; then
            log_message "${GREEN}✅ Found real journey ID: $REAL_JOURNEY_ID${NC}"
            return 0
        fi
    fi
    
    log_message "${YELLOW}⚠️  No existing journeys found, will create a test journey${NC}"
    return 1
}

# Function to create a test journey
create_test_journey() {
    log_message "${BLUE}Creating test journey for comprehensive testing...${NC}"
    local journey_data='{
        "action": "create",
        "journey_id": "",
        "journey_data": {
            "name": "Comprehensive Test Journey",
            "description": "Journey created for comprehensive endpoint testing",
            "oda_component_type": "customer-management",
            "source_type": "database", 
            "priority": "high",
            "source_data_location": "s3://test-bucket/test-data/",
            "target_data_location": "s3://test-bucket/transformed-data/",
            "contact_email": "test@example.com",
            "tags": ["test", "comprehensive", "customer-management"],
            "metadata": {
                "test_run": true,
                "created_by": "test_script",
                "purpose": "comprehensive_testing",
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
        CREATED_JOURNEY_ID=$(echo "$response" | jq -r '.result.journey_id // empty' 2>/dev/null)
        if [[ -n "$CREATED_JOURNEY_ID" ]]; then
            log_message "${GREEN}✅ Created test journey: $CREATED_JOURNEY_ID${NC}"
            return 0
        fi
    fi
    
    log_message "${YELLOW}⚠️  Failed to create test journey, will use existing one${NC}"
    return 1
}

# Function to run a test job and capture its ID
run_test_job() {
    local journey_id="${1:-$REAL_JOURNEY_ID}"
    log_message "${BLUE}Running test job to capture real job ID...${NC}"
    
    local job_data='{
        "action": "run_job",
        "journey_id": "'$journey_id'",
        "stage_id": "raw_analysis",
        "triggered_by": "test-script",
        "reason": "Test job for comprehensive testing"
    }'
    
    local response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d "$job_data" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        CREATED_JOB_ID=$(echo "$response" | jq -r '.result.job_id // empty' 2>/dev/null)
        if [[ -n "$CREATED_JOB_ID" ]]; then
            log_message "${GREEN}✅ Created test job: $CREATED_JOB_ID${NC}"
            return 0
        fi
    fi
    
    log_message "${YELLOW}⚠️  Failed to create test job${NC}"
    return 1
}

# =============================================================================
# INITIALIZATION
# =============================================================================

# Notify user about log file location
log_message "${PURPLE}📋 Test results will be logged to: $LOG_FILE${NC}"
log_message "${CYAN}=============================================${NC}"

# =============================================================================
# SETUP REAL TEST DATA
# =============================================================================

print_header "SETUP REAL TEST DATA"

# Get real journey ID from system
if get_real_journey_id; then
    SAMPLE_JOURNEY_ID="$REAL_JOURNEY_ID"
    log_message "${GREEN}✅ Will use existing journey: $SAMPLE_JOURNEY_ID${NC}"
else
    # Try to create a test journey
    if create_test_journey; then
        SAMPLE_JOURNEY_ID="$CREATED_JOURNEY_ID"
        log_message "${GREEN}✅ Will use created journey: $SAMPLE_JOURNEY_ID${NC}"
    else
        log_message "${YELLOW}⚠️  Using fallback journey ID: $SAMPLE_JOURNEY_ID${NC}"
    fi
fi

# Create a test job to use for job-related tests
if run_test_job "$SAMPLE_JOURNEY_ID"; then
    SAMPLE_JOB_ID="$CREATED_JOB_ID"
    log_message "${GREEN}✅ Will use created job: $SAMPLE_JOB_ID${NC}"
else
    log_message "${YELLOW}⚠️  Using fallback job ID: $SAMPLE_JOB_ID${NC}"
fi

log_message "${CYAN}Final test configuration:${NC}"
log_message "${CYAN}  - Journey ID: $SAMPLE_JOURNEY_ID${NC}"
log_message "${CYAN}  - Job ID: $SAMPLE_JOB_ID${NC}"
log_message "${CYAN}  - Stage ID: $SAMPLE_STAGE_ID${NC}"

# =============================================================================
# BASIC HEALTH CHECKS
# =============================================================================

print_header "BASIC HEALTH CHECKS"

log_message "\n${BLUE}Checking server health...${NC}"
health_response=$(curl -s -X GET "$SERVER_URL/health" --connect-timeout $TIMEOUT --max-time $TIMEOUT 2>&1)
if [[ $? -eq 0 ]]; then
    log_message "${GREEN}✅ Server is healthy${NC}"
    log_json_response "$health_response"
else
    log_message "${RED}❌ Server health check failed: $health_response${NC}"
    exit 1
fi

log_message "\n${BLUE}Getting server info...${NC}"
info_response=$(curl -s -X GET "$SERVER_URL/mcp/server/info" --connect-timeout $TIMEOUT --max-time $TIMEOUT 2>&1)
if [[ $? -eq 0 ]]; then
    log_message "${GREEN}✅ Server info retrieved${NC}"
    log_json_response "$info_response"
else
    log_message "${RED}❌ Server info failed: $info_response${NC}"
fi

log_message "\n${BLUE}Listing available tools...${NC}"
tools_response=$(curl -s -X GET "$SERVER_URL/tools" --connect-timeout $TIMEOUT --max-time $TIMEOUT 2>&1)
if [[ $? -eq 0 ]]; then
    log_message "${GREEN}✅ Tools list retrieved${NC}"
    log_json_response "$tools_response"
else
    log_message "${RED}❌ Tools list failed: $tools_response${NC}"
fi

# =============================================================================
# JOURNEY CRUD OPERATIONS
# =============================================================================

print_header "JOURNEY CRUD OPERATIONS"

# Test 1: List all journeys (READ - default action)
make_request "/tools/journeys" '{
    "action": "read",
    "journey_id": "",
    "include_stages": true,
    "include_job_history": true,
    "limit": 50
}' "List all journeys"

# Test 2: Create journey
make_request "/tools/journeys" '{
    "action": "create",
    "journey_id": "",
    "journey_data": {
        "name": "Test Product Catalog Journey",
        "description": "A test journey for product catalog transformation",
        "oda_component_type": "product-catalog-management",
        "source_type": "database",
        "priority": "high"
    }
}' "Create new journey"

# Test 3: Update journey
make_request "/tools/journeys" '{
    "action": "update",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "journey_data": {
        "status": "completed",
        "overall_progress": 100
    }
}' "Update journey"

# Test 4: Delete journey
make_request "/tools/journeys" '{
    "action": "delete",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "Delete journey"

# =============================================================================
# STAGE MANAGEMENT OPERATIONS
# =============================================================================

print_header "STAGE MANAGEMENT OPERATIONS"

# Test 5: List stages
make_request "/tools/journeys" '{
    "action": "list_stages",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "List journey stages"

# Test 6: Add stage
make_request "/tools/journeys" '{
    "action": "add_stage",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_data": {
        "stage_id": "custom_validation",
        "name": "Custom Validation Stage",
        "description": "Custom validation and quality checks",
        "type": "custom",
        "priority": 5,
        "depends_on": ["data_analysis"],
        "execution_timeout": 1800,
        "retry_count": 2,
        "can_skip": false,
        "estimated_duration": 1800,
        "second_brain_enabled": true,
        "resources": {
            "cpu": "2 vCPU",
            "memory": "4 GB",
            "storage": "100 GB"
        },
        "parameters": {
            "validation_rules": ["schema_check", "data_quality", "business_rules"],
            "quality_threshold": 0.95,
            "parallel_execution": true
        },
        "s3_config": {
            "logs_bucket": "transformation-journey-logs",
            "reports_bucket": "transformation-journey-reports"
        }
    }
}' "Add custom stage"

# Test 7: Update stage
make_request "/tools/journeys" '{
    "action": "update_stage",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "raw_analysis",
    "stage_data": {
        "name": "Raw Analysis - Updated",
        "description": "Updated raw input analysis and processing",
        "type": "analysis",
        "priority": 2,
        "depends_on": [],
        "execution_timeout": 2700,
        "retry_count": 3,
        "can_skip": false,
        "estimated_duration": 2700,
        "second_brain_enabled": true,
        "resources": {
            "cpu": "4 vCPU",
            "memory": "8 GB",
            "storage": "200 GB"
        },
        "parameters": {
            "analysis_depth": "comprehensive",
            "include_metadata": true,
            "parallel_processing": true
        },
        "s3_config": {
            "logs_bucket": "transformation-journey-logs",
            "reports_bucket": "transformation-journey-reports"
        }
    }
}' "Update stage"

# Test 8: Delete stage
make_request "/tools/journeys" '{
    "action": "delete_stage",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "custom_analysis"
}' "Delete stage"

# Test 9: Add default stages
make_request "/tools/journeys" '{
    "action": "add_default_stages",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "Add default TMF ODA stages"

# =============================================================================
# RULES MANAGEMENT OPERATIONS
# =============================================================================

print_header "RULES MANAGEMENT OPERATIONS"

# Test 10: List rules
make_request "/tools/journeys" '{
    "action": "list_rules",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "data_mapping"
}' "List stage rules"

# Test 11: Add rule
make_request "/tools/journeys" '{
    "action": "add_rule",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "data_mapping",
    "rule_data": {
        "title": "Customer ID Mapping Rule",
        "description": "Maps customer_id field from source to target schema with validation",
        "type": "field_mapping",
        "priority": "high",
        "scope": "field_level",
        "context": {
            "source_system": "legacy_crm",
            "target_system": "tmf_oda",
            "data_type": "customer_identifier",
            "business_context": "customer_management"
        },
        "content": {
            "mapping_rules": {
                "source_field": "cust_id",
                "target_field": "customer_id",
                "transformation": "direct_mapping",
                "validation": "not_null"
            },
            "business_rules": [
                "Customer ID must be unique",
                "Customer ID format: alphanumeric, max 50 chars"
            ],
            "error_handling": {
                "on_missing": "reject_record",
                "on_invalid_format": "apply_default_format"
            }
        },
        "status": "active",
        "createdBy": "test-script",
        "version": "1.0",
        "tags": ["data_mapping", "customer_id", "field_mapping"],
        "applicableStages": ["data_mapping", "schema_validation"]
    }
}' "Add mapping rule"

# Test 12: Update rule
make_request "/tools/journeys" '{
    "action": "update_rule",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "data_mapping",
    "rule_id": "'"$SAMPLE_RULE_ID"'",
    "rule_data": {
        "priority": "critical",
        "description": "Updated customer ID mapping with enhanced validation"
    }
}' "Update rule"

# Test 13: Delete rule
make_request "/tools/journeys" '{
    "action": "delete_rule",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "data_mapping",
    "rule_id": "'"$SAMPLE_RULE_ID"'"
}' "Delete rule"

# =============================================================================
# JOB MANAGEMENT OPERATIONS
# =============================================================================

print_header "JOB MANAGEMENT OPERATIONS"

# Test 14: List jobs
make_request "/tools/journeys" '{
    "action": "list_jobs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "'"$SAMPLE_STAGE_ID"'"
}' "List jobs"

# Test 15: Get job details
make_request "/tools/journeys" '{
    "action": "get_job",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'"
}' "Get job details"

# Test 16: Run job
make_request "/tools/journeys" '{
    "action": "run_job",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "'"$SAMPLE_STAGE_ID"'",
    "triggered_by": "test-user",
    "reason": "Manual test execution"
}' "Run job"

# Test 17: Cancel job
make_request "/tools/journeys" '{
    "action": "cancel_job",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "reason": "Test cancellation"
}' "Cancel job"

# Test 18: Update job status
make_request "/tools/journeys" '{
    "action": "update_job_status",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "job_status": "running",
    "progress": 75,
    "current_step": "schema_processing"
}' "Update job status"

# Test 19: Retry job
make_request "/tools/journeys" '{
    "action": "retry_job",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "triggered_by": "test-user",
    "reason": "Retry after fixing data issue"
}' "Retry job"

# Test 20: Get job metrics
make_request "/tools/journeys" '{
    "action": "get_job_metrics",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'"
}' "Get job metrics"

# Test 21: Get job timeline
make_request "/tools/journeys" '{
    "action": "get_job_timeline",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'"
}' "Get job timeline"

# Test 22: Batch cancel jobs
make_request "/tools/journeys" '{
    "action": "batch_cancel_jobs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_ids": "JOB-003-20240101140000,JOB-004-20240101150000,JOB-005-20240101160000",
    "reason": "Batch test cancellation"
}' "Batch cancel jobs"

# =============================================================================
# INTERACTIVE FEATURES
# =============================================================================

print_header "INTERACTIVE FEATURES"

# Test 23: Dashboard
make_request "/tools/journeys" '{
    "action": "dashboard",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "Get dashboard"

# Test 24: Journey summary
make_request "/tools/journeys" '{
    "action": "get_journey_summary",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "Get journey summary"

# =============================================================================
# LOGS AND REPORTS OPERATIONS
# =============================================================================

print_header "LOGS AND REPORTS OPERATIONS"

# Test 25: Get job logs
make_request "/tools/logs-and-reports" '{
    "action": "get_job_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "stage_name": "'"$SAMPLE_STAGE_ID"'",
    "step_name": "schema_parsing"
}' "Get job logs"

# Test 26: Add log entry
make_request "/tools/logs-and-reports" '{
    "action": "add_log_entry",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "step_name": "schema_parsing",
    "log_level": "INFO",
    "log_message": "Custom log entry for testing"
}' "Add log entry"

# Test 27: Search logs
make_request "/tools/logs-and-reports" '{
    "action": "search_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "search_query": "error schema parsing"
}' "Search logs"

# Test 28: Get logs by level
make_request "/tools/logs-and-reports" '{
    "action": "get_logs_by_level",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "log_level": "error"
}' "Get logs by level"

# Test 29: Export job logs
make_request "/tools/logs-and-reports" '{
    "action": "export_job_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "output_file": "/tmp/test_export_logs_json.json",
    "export_format": "json"
}' "Export job logs"

# Test 30: Get error summary
make_request "/tools/logs-and-reports" '{
    "action": "get_error_summary",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'"
}' "Get error summary"

# Test 31: Generate summary report
make_request "/tools/logs-and-reports" '{
    "action": "generate_summary_report",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "report_type": "comprehensive",
    "report_title": "Test Journey Summary Report"
}' "Generate summary report"

# Test 32: Analyze job performance
make_request "/tools/logs-and-reports" '{
    "action": "analyze_job_performance",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "analysis_period": "24h"
}' "Analyze job performance"

# =============================================================================
# COMPREHENSIVE JOB LOG TESTING
# =============================================================================

print_header "COMPREHENSIVE JOB LOG TESTING"

# Test 33: Get job logs with S3 integration
make_request "/tools/logs-and-reports" '{
    "action": "get_job_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "stage_name": "raw_analysis",
    "step_name": "schema_parsing",
    "log_level": "info",
    "limit": 100,
    "include_metadata": true,
    "include_s3_location": true,
    "s3_bucket": "transformation-journey-logs"
}' "Get detailed job logs with S3 integration"

# Test 34: Get job logs for different stages with S3 storage
make_request "/tools/logs-and-reports" '{
    "action": "get_job_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "stage_name": "stripped_schema",
    "step_name": "all",
    "include_performance_metrics": true,
    "s3_bucket": "transformation-journey-logs",
    "auto_archive_to_s3": true
}' "Get job logs for stripped schema stage with S3 storage"

# Test 35: Search logs with advanced filters
make_request "/tools/logs-and-reports" '{
    "action": "search_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "search_query": "processing completed",
    "log_level": "info",
    "time_from": "2024-01-01T00:00:00Z",
    "time_to": "2024-12-31T23:59:59Z",
    "limit": 50
}' "Search logs with advanced filters"

# Test 36: Get logs by multiple levels
make_request "/tools/logs-and-reports" '{
    "action": "get_logs_by_level",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "log_level": "warning",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "stage_name": "raw_analysis",
    "include_context": true
}' "Get warning logs with context"

# Test 37: Export logs in different formats
make_request "/tools/logs-and-reports" '{
    "action": "export_job_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "output_file": "/tmp/test_export_logs_csv.csv",
    "export_format": "csv"
}' "Export job logs in CSV format"

# =============================================================================
# S3 OPERATIONS AND REPORTS TESTING
# =============================================================================
# 
# This section tests the S3 integration for TMF ODA transformation journeys:
#
# S3 Bucket Structure:
# - transformation-journey-logs/    : Job execution logs, debug data, operational logs
# - transformation-journey-reports/ : Analysis reports, performance metrics, summaries
#
# S3 Path Structure:
# - logs:    s3://transformation-journey-logs/{journey_id}/{job_id}/logs/
# - reports: s3://transformation-journey-reports/{journey_id}/{job_id}/reports/
# - analytics: s3://transformation-journey-reports/{journey_id}/analytics/
#
# Tests Cover:
# - Log export to S3 with proper path generation
# - Report generation with S3 storage integration  
# - Performance analysis with S3 metrics inclusion
# - Job report retrieval from S3 locations
# - Available logs listing with S3 location metadata
# =============================================================================

print_header "S3 OPERATIONS AND REPORTS TESTING"

# Test 38: Export job logs to S3 (transformation-journey-logs bucket)
make_request "/tools/logs-and-reports" '{
    "action": "export_job_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "output_file": "s3://transformation-journey-logs/'"$SAMPLE_JOURNEY_ID"'/'"$SAMPLE_JOB_ID"'/job_logs_export.json",
    "export_format": "json"
}' "Export job logs to S3 logs bucket"

# Test 39: Generate job summary report with S3 storage
make_request "/tools/logs-and-reports" '{
    "action": "generate_job_summary_report",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "output_location": "s3://transformation-journey-reports/'"$SAMPLE_JOURNEY_ID"'/'"$SAMPLE_JOB_ID"'/summary_report.json"
}' "Generate job summary report to S3"

# Test 40: Create job performance report in S3
make_request "/tools/logs-and-reports" '{
    "action": "create_job_report",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "report_type": "performance",
    "report_title": "Job Performance Analysis Report",
    "content": {
        "analysis_type": "performance",
        "metrics_analyzed": ["execution_time", "resource_usage", "error_rate", "s3_operations"],
        "findings": [
            "Job completed within expected timeframe",
            "Resource usage was optimal", 
            "No critical errors detected",
            "S3 operations performed efficiently"
        ],
        "s3_metrics": {
            "logs_stored": "s3://transformation-journey-logs/'"$SAMPLE_JOURNEY_ID"'/'"$SAMPLE_JOB_ID"'/",
            "reports_stored": "s3://transformation-journey-reports/'"$SAMPLE_JOURNEY_ID"'/'"$SAMPLE_JOB_ID"'/",
            "storage_efficiency": "optimized"
        }
    },
    "summary": "Overall performance was excellent with efficient S3 integration",
    "output_location": "s3://transformation-journey-reports/'"$SAMPLE_JOURNEY_ID"'/'"$SAMPLE_JOB_ID"'/performance_report.json"
}' "Create job performance report with S3 storage"

# Test 41: Performance analysis with S3 integration
make_request "/tools/logs-and-reports" '{
    "action": "analyze_job_performance",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "analysis_period": "24h",
    "include_s3_metrics": true,
    "output_location": "s3://transformation-journey-reports/'"$SAMPLE_JOURNEY_ID"'/analytics/performance_analysis.json"
}' "Analyze job performance with S3 metrics"

# Test 42: Get job reports from S3
make_request "/tools/logs-and-reports" '{
    "action": "get_job_reports",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "stage_name": "raw_analysis",
    "include_s3_location": true,
    "s3_bucket": "transformation-journey-reports"
}' "Get job reports from S3 storage"

# Test 43: List available logs with S3 locations
make_request "/tools/logs-and-reports" '{
    "action": "list_available_logs",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "include_s3_locations": true,
    "logs_bucket": "transformation-journey-logs",
    "reports_bucket": "transformation-journey-reports"
}' "List available logs with S3 locations"

# S3 Integration Summary:
# - transformation-journey-logs: Stores job execution logs, debug information, and operational data
# - transformation-journey-reports: Stores analysis reports, performance metrics, and summary data
# - Tests verify proper S3 bucket integration, file path generation, and data archival

# =============================================================================
# INTEGRATION TESTING
# =============================================================================

print_header "INTEGRATION TESTING"

# Test 44: End-to-end workflow test with S3 logging
make_request "/tools/journeys" '{
    "action": "run_job",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "stage_id": "stripped_schema",
    "triggered_by": "integration-test",
    "reason": "End-to-end workflow testing with S3 integration",
    "enable_s3_logging": true,
    "s3_logs_bucket": "transformation-journey-logs",
    "s3_reports_bucket": "transformation-journey-reports"
}' "End-to-end workflow test with S3 integration"

# Test 45: Add log entry with S3 archival
make_request "/tools/logs-and-reports" '{
    "action": "add_log_entry",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "step_name": "integration_test",
    "log_level": "INFO",
    "log_message": "Integration test log entry with S3 archival enabled",
    "details": {
        "test_phase": "integration",
        "test_type": "end_to_end_s3",
        "system_state": "healthy",
        "s3_integration": "enabled",
        "logs_bucket": "transformation-journey-logs",
        "reports_bucket": "transformation-journey-reports"
    },
    "source": "test_script",
    "archive_to_s3": true,
    "s3_bucket": "transformation-journey-logs"
}' "Add integration test log entry with S3 archival"

# Test 46: Generate performance report with S3 output
make_request "/tools/logs-and-reports" '{
    "action": "generate_performance_report",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'",
    "job_id": "'"$SAMPLE_JOB_ID"'",
    "include_s3_metrics": true,
    "output_location": "s3://transformation-journey-reports/'"$SAMPLE_JOURNEY_ID"'/'"$SAMPLE_JOB_ID"'/final_performance_report.json",
    "s3_logs_analysis": {
        "analyze_logs_bucket": "transformation-journey-logs",
        "analyze_reports_bucket": "transformation-journey-reports"
    }
}' "Generate comprehensive performance report with S3 analysis"

# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

print_header "ERROR HANDLING TESTS"

# Test 47: Missing required journey_id
make_request "/tools/journeys" '{
    "action": "update",
    "journey_id": "",
    "journey_data": {"status": "completed"}
}' "Missing required journey_id"

# Test 48: Missing required data
make_request "/tools/journeys" '{
    "action": "create",
    "journey_id": "",
    "journey_data": null
}' "Missing required data"

# Test 49: Missing required parameters in logs
make_request "/tools/logs-and-reports" '{
    "action": "get_job_logs",
    "journey_id": "",
    "job_id": "",
    "stage_name": "",
    "step_name": ""
}' "Missing required parameters in logs"

# Test 50: Unsupported action in journeys
make_request "/tools/journeys" '{
    "action": "invalid_action",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "Unsupported action in journeys"

# Test 51: Unsupported action in logs
make_request "/tools/logs-and-reports" '{
    "action": "invalid_action",
    "journey_id": "'"$SAMPLE_JOURNEY_ID"'"
}' "Unsupported action in logs"

# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================

print_header "BACKWARD COMPATIBILITY TESTS"

# Note: Backward compatibility tests removed to focus on S3 integration testing

# =============================================================================
# SUMMARY
# =============================================================================

print_header "TEST SUMMARY"

log_message "\n${BLUE}Test Results:${NC}"
log_message "${GREEN}✅ Passed: $PASSED_COUNT${NC}"
log_message "${RED}❌ Failed: $FAILED_COUNT${NC}"
log_message "${YELLOW}📊 Total: $TEST_COUNT${NC}"

# Add final summary to log file
echo "" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"
echo "Test run completed at $(date)" >> "$LOG_FILE"
echo "Final Results - Passed: $PASSED_COUNT, Failed: $FAILED_COUNT, Total: $TEST_COUNT" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

if [ $FAILED_COUNT -eq 0 ]; then
    log_message "\n${GREEN}🎉 All tests completed! Some may have expected errors based on current implementation.${NC}"
    log_message "${PURPLE}📋 Full test log saved to: $LOG_FILE${NC}"
    exit 0
else
    log_message "\n${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    log_message "${PURPLE}📋 Full test log saved to: $LOG_FILE${NC}"
    exit 1
fi 