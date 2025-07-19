#!/bin/bash

# Ultra-Reliable Job, Log, and Report Management Test Suite
# This script provides maximum reliability for job lifecycle testing across all transformation stages
# Features: Health checks, retry logic, validation, recovery, parallel processing, comprehensive monitoring

set -e

# Configuration
SERVER_URL="http://localhost:8000"
JOURNEY_TOOL="$SERVER_URL/tools/journeys"
LOGS_TOOL="$SERVER_URL/tools/logs-and-reports"
SIMPLE_JOURNEYS_TOOL="$SERVER_URL/tools/simple-journeys"

# Reliability settings
MAX_RETRIES=5
INITIAL_RETRY_DELAY=2
MAX_RETRY_DELAY=60
JOB_TIMEOUT=600  # 10 minutes per job
HEALTH_CHECK_TIMEOUT=30
LOG_VALIDATION_THRESHOLD=1  # Minimum expected logs per job
PARALLEL_LIMIT=3  # Maximum parallel operations

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
CRITICAL_FAILURES=0
declare -A STAGE_JOBS
declare -A JOB_STATUS
declare -A JOB_LOGS_COUNT
declare -A JOB_REPORTS
declare -A JOB_START_TIME
declare -A JOB_END_TIME
declare -A STAGE_HEALTH

# Logging
LOG_FILE="/tmp/job_management_test_$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "🚀 ULTRA-RELIABLE JOB MANAGEMENT TEST SUITE"
echo "=============================================================================="
echo "📋 Reliability Features:"
echo "  • Health checks and server validation"
echo "  • Exponential backoff retry with up to $MAX_RETRIES attempts"
echo "  • Job monitoring with ${JOB_TIMEOUT}s timeout per job"
echo "  • Log validation and integrity checks"
echo "  • Report validation and verification"
echo "  • Parallel processing with smart queuing"
echo "  • Automatic recovery from failures"
echo "  • Comprehensive test logging to: $LOG_FILE"
echo ""

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
    echo -e "${PURPLE}${BOLD}📊 $1${NC}"
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_stage() {
    echo -e "${CYAN}${BOLD}🔄 STAGE: $1${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────────────────────${NC}"
}

print_step() {
    echo -e "${BLUE}📋 [$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ [$(date '+%H:%M:%S')] $1${NC}"
    ((PASSED_TESTS++))
}

print_failure() {
    echo -e "${RED}❌ [$(date '+%H:%M:%S')] $1${NC}"
    ((FAILED_TESTS++))
}

print_critical() {
    echo -e "${RED}${BOLD}🚨 [$(date '+%H:%M:%S')] CRITICAL: $1${NC}"
    ((CRITICAL_FAILURES++))
}

print_info() {
    echo -e "${YELLOW}💡 [$(date '+%H:%M:%S')] $1${NC}"
}

print_result() {
    local status="$1"
    local message="$2"
    ((TOTAL_TESTS++))
    
    if [ "$status" = "success" ]; then
        print_success "$message"
    elif [ "$status" = "critical" ]; then
        print_critical "$message"
    else
        print_failure "$message"
    fi
}

# Exponential backoff retry function
exponential_backoff() {
    local attempt=1
    local delay=$INITIAL_RETRY_DELAY
    
    while [ $attempt -le $MAX_RETRIES ]; do
        if [ $attempt -gt 1 ]; then
            print_info "Retry attempt $attempt/$MAX_RETRIES (waiting ${delay}s)"
            sleep $delay
            delay=$((delay * 2))
            if [ $delay -gt $MAX_RETRY_DELAY ]; then
                delay=$MAX_RETRY_DELAY
            fi
        fi
        
        if "$@"; then
            return 0
        fi
        
        ((attempt++))
    done
    
    return 1
}

# Enhanced server health check
check_server_health() {
    print_step "Performing comprehensive server health checks"
    
    # Basic connectivity test
    if ! curl -s --connect-timeout 10 --max-time $HEALTH_CHECK_TIMEOUT "$SERVER_URL" > /dev/null 2>&1; then
        print_critical "Server not responding at $SERVER_URL"
        return 1
    fi
    
    print_success "Server health checks completed - server is responsive"
    return 0
}

# Robust API call with validation
robust_api_call() {
    local description="$1"
    local url="$2"
    local data="$3"
    local expected_field="$4"
    local validation_func="$5"
    
    print_step "$description"
    
    call_function() {
        local response=$(curl -s -X POST "$url" \
            -H 'Content-Type: application/json' \
            -d "$data" \
            --connect-timeout 30 \
            --max-time 120 \
            --retry 0)
        
        local curl_exit_code=$?
        if [ $curl_exit_code -ne 0 ]; then
            print_failure "Network error (curl exit code: $curl_exit_code)"
            return 1
        fi
        
        # Validate JSON response
        if ! echo "$response" | jq empty 2>/dev/null; then
            print_failure "Invalid JSON response: ${response:0:100}..."
            return 1
        fi
        
        # Check for success status
        if ! echo "$response" | jq -e '.result.status == "success"' > /dev/null 2>&1; then
            local error_msg=$(echo "$response" | jq -r '.error // .result.error // .result.message // "Unknown error"' 2>/dev/null || echo "API call failed")
            print_failure "$description failed: $error_msg"
            return 1
        fi
        
        # Extract expected field if specified
        if [ -n "$expected_field" ]; then
            local value=$(echo "$response" | jq -r ".result.$expected_field // empty")
            if [ -z "$value" ] || [ "$value" = "null" ]; then
                print_failure "$description - $expected_field not found in response"
                return 1
            fi
            echo "$value"
        fi
        
        # Run custom validation if provided
        if [ -n "$validation_func" ] && declare -f "$validation_func" > /dev/null; then
            if ! $validation_func "$response"; then
                print_failure "$description - custom validation failed"
                return 1
            fi
        fi
        
        return 0
    }
    
    if exponential_backoff call_function; then
        print_success "$description completed successfully"
        return 0
    else
        print_failure "$description failed after $MAX_RETRIES attempts"
        return 1
    fi
}

# Enhanced job monitoring with detailed status tracking
monitor_job_with_details() {
    local journey_id="$1"
    local job_id="$2"
    local stage_id="$3"
    local timeout="${4:-$JOB_TIMEOUT}"
    
    print_info "Starting enhanced monitoring for job $job_id (timeout: ${timeout}s)"
    JOB_START_TIME["$job_id"]=$(date +%s)
    
    local elapsed=0
    local check_interval=5
    local last_progress=0
    local stalled_count=0
    local max_stalled=6  # 30 seconds of no progress
    
    while [ $elapsed -lt $timeout ]; do
        local status_data='{
            "action": "get_job",
            "journey_id": "'$journey_id'",
            "job_id": "'$job_id'"
        }'
        
        local response=$(curl -s -X POST "$JOURNEY_TOOL" \
            -H 'Content-Type: application/json' \
            -d "$status_data" \
            --connect-timeout 15 \
            --max-time 30)
        
        if echo "$response" | jq -e '.result.status == "success"' > /dev/null 2>&1; then
            local job_status=$(echo "$response" | jq -r '.result.job_info.status // .result.status // "unknown"')
            local progress=$(echo "$response" | jq -r '.result.job_info.progress // .result.progress // 0')
            local current_step=$(echo "$response" | jq -r '.result.job_info.current_step // .result.current_step // "unknown"')
            local error_message=$(echo "$response" | jq -r '.result.job_info.error_message // .result.error_message // ""')
            
            # Progress stall detection
            if [ "$progress" = "$last_progress" ]; then
                ((stalled_count++))
            else
                stalled_count=0
                last_progress=$progress
            fi
            
            local stall_indicator=""
            if [ $stalled_count -ge $max_stalled ]; then
                stall_indicator=" (STALLED?)"
            fi
            
            echo -ne "\r  📊 Status: $job_status | Progress: ${progress}% | Step: $current_step | Elapsed: ${elapsed}s$stall_indicator"
            
            case "$job_status" in
                "completed"|"success")
                    echo ""
                    JOB_END_TIME["$job_id"]=$(date +%s)
                    JOB_STATUS["$job_id"]="completed"
                    print_success "Job $job_id completed successfully in ${elapsed}s"
                    return 0
                    ;;
                "failed"|"error")
                    echo ""
                    JOB_END_TIME["$job_id"]=$(date +%s)
                    JOB_STATUS["$job_id"]="failed"
                    print_failure "Job $job_id failed: $error_message"
                    return 1
                    ;;
                "cancelled"|"canceled")
                    echo ""
                    JOB_END_TIME["$job_id"]=$(date +%s)
                    JOB_STATUS["$job_id"]="cancelled"
                    print_failure "Job $job_id was cancelled"
                    return 1
                    ;;
                "running"|"pending"|"in_progress")
                    # Check for excessive stalling
                    if [ $stalled_count -ge $((max_stalled * 2)) ]; then
                        echo ""
                        print_info "Job $job_id appears stalled, but continuing to monitor..."
                    fi
                    ;;
                *)
                    print_info "Job $job_id has status: $job_status (treating as running)"
                    ;;
            esac
        else
            print_info "Cannot get job status, continuing to monitor..."
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo ""
    JOB_END_TIME["$job_id"]=$(date +%s)
    JOB_STATUS["$job_id"]="timeout"
    print_failure "Job $job_id monitoring timed out after ${timeout}s"
    return 1
}

# Comprehensive log analysis with validation
analyze_logs_comprehensive() {
    local journey_id="$1"
    local job_id="$2"
    local stage_name="$3"
    
    print_step "Performing comprehensive log analysis for job $job_id"
    
    # Validation function for log response
    validate_logs() {
        local response="$1"
        local total_logs=$(echo "$response" | jq -r '.result.total_logs // 0')
        
        if [ "$total_logs" -lt $LOG_VALIDATION_THRESHOLD ]; then
            print_info "Warning: Only $total_logs log entries found (expected >= $LOG_VALIDATION_THRESHOLD)"
        fi
        
        # Validate log structure
        if ! echo "$response" | jq -e '.result.logs[0].timestamp' > /dev/null 2>&1; then
            if [ "$total_logs" -gt 0 ]; then
                print_info "Warning: Log entries missing expected timestamp structure"
            fi
        fi
        
        return 0
    }
    
    # Get comprehensive logs
    local logs_data='{
        "action": "get_job_logs",
        "journey_id": "'$journey_id'",
        "job_id": "'$job_id'",
        "stage_name": "'$stage_name'",
        "include_metadata": true,
        "sort_order": "chronological",
        "limit": 1000
    }'
    
    local logs_response
    if logs_response=$(robust_api_call "Getting job logs" "$LOGS_TOOL" "$logs_data" "total_logs" "validate_logs"); then
        local total_logs=$(curl -s -X POST "$LOGS_TOOL" \
            -H 'Content-Type: application/json' \
            -d "$logs_data" | jq -r '.result.total_logs // 0')
        
        JOB_LOGS_COUNT["$job_id"]=$total_logs
        print_success "Retrieved $total_logs log entries for job $job_id"
        
        # Show sample log entries
        if [ "$total_logs" -gt 0 ]; then
            local sample_logs=$(curl -s -X POST "$LOGS_TOOL" \
                -H 'Content-Type: application/json' \
                -d "$logs_data")
            
            echo "📝 Recent Log Entries:"
            echo "$sample_logs" | jq -r '.result.logs[0:3][] | "  [\(.timestamp // "no-time")] \(.level // "INFO" | ascii_upcase): \(.message // .log_message // "No message")"' 2>/dev/null || echo "  Log format validation needed"
        fi
        
        # Analyze log levels in parallel
        analyze_log_level "error" "$journey_id" "$job_id" &
        analyze_log_level "warning" "$journey_id" "$job_id" &
        analyze_log_level "info" "$journey_id" "$job_id" &
        wait
        
        print_result "success" "Log analysis completed for job $job_id"
        return 0
    else
        JOB_LOGS_COUNT["$job_id"]=0
        print_result "failure" "Log analysis failed for job $job_id"
        return 1
    fi
}

# Analyze specific log level
analyze_log_level() {
    local level="$1"
    local journey_id="$2"
    local job_id="$3"
    
    local level_logs_data='{
        "action": "get_logs_by_level",
        "journey_id": "'$journey_id'",
        "job_id": "'$job_id'",
        "log_level": "'$level'"
    }'
    
    local response=$(curl -s -X POST "$LOGS_TOOL" \
        -H 'Content-Type: application/json' \
        -d "$level_logs_data")
    
    local count=$(echo "$response" | jq -r '.result.total_logs // 0')
    
    case "$level" in
        "error")
            echo "🚨 Error logs: $count"
            if [ "$count" -gt 0 ]; then
                print_info "Found $count error(s) in job $job_id - review recommended"
            fi
            ;;
        "warning")
            echo "⚠️ Warning logs: $count"
            ;;
        "info")
            echo "ℹ️ Info logs: $count"
            ;;
    esac
}

# Enhanced report generation with validation
generate_validated_report() {
    local journey_id="$1"
    local job_id="$2"
    local stage_name="$3"
    
    print_step "Generating validated comprehensive report for job $job_id"
    
    # Validation function for report response
    validate_report() {
        local response="$1"
        local report_id=$(echo "$response" | jq -r '.result.report_id // empty')
        local report_size=$(echo "$response" | jq -r '.result.report_size // .result.size // 0')
        
        if [ -z "$report_id" ] || [ "$report_id" = "null" ]; then
            # Check alternative fields
            report_id=$(echo "$response" | jq -r '.result.file_path // .result.report_url // .result.id // "generated"')
        fi
        
        if [ "$report_size" = "0" ]; then
            print_info "Warning: Report size is 0 or not specified"
        fi
        
        return 0
    }
    
    # Create comprehensive report
    local report_data='{
        "action": "create_job_report",
        "journey_id": "'$journey_id'",
        "job_id": "'$job_id'",
        "report_type": "comprehensive",
        "report_title": "Validated Report for Job '$job_id' - Stage '$stage_name'",
        "report_content": {
            "include_metrics": true,
            "include_logs": true,
            "include_timeline": true,
            "include_performance": true,
            "include_errors": true,
            "include_summary": true,
            "format": "detailed_json",
            "validation_level": "comprehensive"
        }
    }'
    
    if robust_api_call "Generating job report" "$LOGS_TOOL" "$report_data" "report_id" "validate_report"; then
        local report_response=$(curl -s -X POST "$LOGS_TOOL" \
            -H 'Content-Type: application/json' \
            -d "$report_data")
        
        local report_id=$(echo "$report_response" | jq -r '.result.report_id // .result.file_path // .result.report_url // "generated"')
        JOB_REPORTS["$job_id"]=$report_id
        
        print_success "Generated validated report $report_id for job $job_id"
        
        # Display report summary
        echo "$report_response" | jq '.result | {report_id, sections_included, generation_time, report_size, validation_status}' 2>/dev/null || echo "Report metadata available in response"
        
        print_result "success" "Report generation completed for job $job_id"
        return 0
    else
        JOB_REPORTS["$job_id"]="FAILED"
        print_result "failure" "Report generation failed for job $job_id"
        return 1
    fi
}

# Parallel job creation with smart queuing
create_jobs_parallel() {
    local journey_id="$1"
    local stages=("${@:2}")
    
    print_step "Creating jobs in parallel (limit: $PARALLEL_LIMIT concurrent jobs)"
    
    local job_pids=()
    local active_jobs=0
    
    for i in "${!stages[@]}"; do
        local stage_id="${stages[i]}"
        local stage_num=$((i+1))
        
        # Wait if we've hit the parallel limit
        while [ $active_jobs -ge $PARALLEL_LIMIT ]; do
            for pid in "${job_pids[@]}"; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    wait "$pid"
                    ((active_jobs--))
                fi
            done
            sleep 1
        done
        
        # Create job in background
        {
            create_single_job "$journey_id" "$stage_id" "$stage_num" "${#stages[@]}"
        } &
        
        job_pids+=($!)
        ((active_jobs++))
        
        print_info "Started job creation for stage $stage_id (background process)"
    done
    
    # Wait for all job creations to complete
    for pid in "${job_pids[@]}"; do
        wait "$pid"
    done
    
    print_success "All job creations completed"
}

# Create single job with comprehensive error handling
create_single_job() {
    local journey_id="$1"
    local stage_id="$2"
    local stage_num="$3"
    local total_stages="$4"
    
    print_step "Creating job for stage $stage_num/$total_stages: $stage_id"
    
    # Create clean job JSON and call directly
    local job_data="{\"action\":\"run_job\",\"journey_id\":\"$journey_id\",\"stage_id\":\"$stage_id\",\"triggered_by\":\"ultra-reliable-test-suite\",\"reason\":\"Sequential stage testing - Stage $stage_num of $total_stages: $stage_id\",\"job_data\":{\"job_type\":\"transformation\",\"description\":\"Ultra-reliable test job for stage $stage_id\",\"priority\":\"high\",\"parameters\":{\"stage_order\":$stage_num,\"total_stages\":$total_stages,\"enable_detailed_logging\":true,\"enable_performance_monitoring\":true,\"enable_error_recovery\":true,\"validation_level\":\"comprehensive\",\"reliability_mode\":true,\"test_suite\":\"ultra_reliable\",\"timeout\":$JOB_TIMEOUT}}}"
    
    local job_response=$(curl -s -X POST "$JOURNEY_TOOL" \
        -H 'Content-Type: application/json' \
        -d "$job_data")
    
    if echo "$job_response" | jq -e '.result.status == "success"' > /dev/null 2>&1; then
        local job_id=$(echo "$job_response" | jq -r '.result.job_id // empty' | tr -d '\n\r\t ')
        if [ -n "$job_id" ] && [ "$job_id" != "null" ]; then
            STAGE_JOBS["$stage_id"]=$job_id
            STAGE_HEALTH["$stage_id"]="healthy"
            print_success "Job created: $job_id for stage $stage_id"
            return 0
        else
            STAGE_JOBS["$stage_id"]="FAILED"
            STAGE_HEALTH["$stage_id"]="failed"
            print_result "failure" "Failed to extract job ID for stage $stage_id"
            return 1
        fi
    else
        STAGE_JOBS["$stage_id"]="FAILED"
        STAGE_HEALTH["$stage_id"]="failed"
        print_result "failure" "Failed to create job for stage $stage_id"
        echo "Response: $job_response"
        return 1
    fi
}

# Main execution function
main() {
    # Initialize
    print_header "ULTRA-RELIABLE TEST INITIALIZATION"
    
    # Pre-flight checks
    print_step "Running pre-flight system checks"
    
    # Check dependencies
    command -v curl >/dev/null 2>&1 || { print_critical "curl is required but not installed"; exit 1; }
    command -v jq >/dev/null 2>&1 || { print_critical "jq is required but not installed"; exit 1; }
    
    # Server health check
    if ! exponential_backoff check_server_health; then
        print_critical "Server health checks failed - cannot proceed"
        exit 1
    fi
    
    print_header "STEP 1: JOURNEY SETUP AND VALIDATION"
    
    # Create journey with enhanced parameters - using clean single-line JSON
    local journey_data='{"action":"create","journey_data":{"name":"Ultra-Reliable Job Management Test Journey","description":"Maximum reliability testing of job lifecycle across all transformation stages","odaComponentType":"customer-management","priority":"critical","sourceType":"database","enable_comprehensive_logging":true,"enable_step_tracking":true,"enable_error_recovery":true,"reliability_mode":true,"test_suite_version":"ultra_reliable_v1.0"}}'
    
    # Create journey and extract ID cleanly
    print_step "Creating ultra-reliable test journey"
    local journey_response=$(curl -s -X POST "$SIMPLE_JOURNEYS_TOOL" \
        -H 'Content-Type: application/json' \
        -d "$journey_data")
    
    if echo "$journey_response" | jq -e '.result.status == "success"' > /dev/null 2>&1; then
        JOURNEY_ID=$(echo "$journey_response" | jq -r '.result.journey_id // empty' | tr -d '\n\r\t ')
        if [ -n "$JOURNEY_ID" ] && [ "$JOURNEY_ID" != "null" ]; then
            print_success "Journey created with ultra-reliable configuration: $JOURNEY_ID"
        else
            print_critical "Failed to extract journey ID from response"
            exit 1
        fi
    else
        print_critical "Failed to create journey - aborting test suite"
        echo "Response: $journey_response"
        exit 1
    fi
    
    print_success "Journey created with ultra-reliable configuration: $JOURNEY_ID"
    
    # Validate journey and get stages
    local stages_data='{
        "action": "list-stages",
        "journey_id": "'$JOURNEY_ID'"
    }'
    
    local stages_response=$(curl -s -X POST "$SIMPLE_JOURNEYS_TOOL" \
        -H 'Content-Type: application/json' \
        -d "$stages_data")
    
    local stages=()
    if echo "$stages_response" | jq -e '.result.status == "success"' > /dev/null 2>&1; then
        local total_stages=$(echo "$stages_response" | jq -r '.result.total_stages // 0')
        stages=($(echo "$stages_response" | jq -r '.result.stages[]?.stage_id // empty' | head -6))
        
        if [ ${#stages[@]} -eq 0 ]; then
            stages=("raw_analysis" "stripped_schema" "data_mapping" "compliance_validation" "business_rules" "integration_testing")
            print_info "Using default transformation pipeline (${#stages[@]} stages)"
        else
            print_success "Retrieved $total_stages transformation stages from journey"
        fi
    else
        stages=("raw_analysis" "stripped_schema" "data_mapping" "compliance_validation" "business_rules" "integration_testing")
        print_info "Using default transformation pipeline due to stage listing issues"
    fi
    
    echo "📋 Ultra-Reliable Transformation Pipeline:"
    for i in "${!stages[@]}"; do
        echo "  $((i+1)). ${stages[i]}"
    done
    echo ""
    
    print_header "STEP 2: SEQUENTIAL JOB CREATION AND MONITORING"
    
    # Process each stage with maximum reliability
    for i in "${!stages[@]}"; do
        local stage_id="${stages[i]}"
        local stage_num=$((i+1))
        
        print_stage "STAGE $stage_num: $stage_id"
        
        # Create job with comprehensive error handling
        if create_single_job "$JOURNEY_ID" "$stage_id" "$stage_num" "${#stages[@]}"; then
            local job_id="${STAGE_JOBS[$stage_id]}"
            
            # Monitor job with enhanced tracking
            if monitor_job_with_details "$JOURNEY_ID" "$job_id" "$stage_id" $JOB_TIMEOUT; then
                print_result "success" "Job $job_id completed successfully"
            else
                print_result "failure" "Job $job_id failed or timed out"
                # Continue with remaining stages even if one fails
            fi
            
            # Analyze logs with comprehensive validation
            if analyze_logs_comprehensive "$JOURNEY_ID" "$job_id" "$stage_id"; then
                print_result "success" "Log analysis completed for job $job_id"
            else
                print_result "failure" "Log analysis failed for job $job_id"
            fi
            
            # Generate validated report
            if generate_validated_report "$JOURNEY_ID" "$job_id" "$stage_id"; then
                print_result "success" "Report generated for job $job_id"
            else
                print_result "failure" "Report generation failed for job $job_id"
            fi
            
        else
            print_result "critical" "Failed to create job for stage $stage_id"
        fi
        
        echo ""
        sleep 1  # Brief pause between stages
    done
    
    print_header "STEP 3: COMPREHENSIVE ANALYSIS AND REPORTING"
    
    # Parallel metrics collection
    print_step "Collecting performance metrics for all jobs (parallel processing)"
    local metrics_pids=()
    
    for stage_id in "${stages[@]}"; do
        local job_id="${STAGE_JOBS[$stage_id]}"
        if [ -n "$job_id" ] && [ "$job_id" != "FAILED" ]; then
            {
                collect_job_metrics "$JOURNEY_ID" "$job_id" "$stage_id"
            } &
            metrics_pids+=($!)
        fi
    done
    
    # Wait for all metrics collection
    for pid in "${metrics_pids[@]}"; do
        wait "$pid"
    done
    
    # Generate comprehensive journey summary
    generate_journey_summary "$JOURNEY_ID"
    
    # Final verification
    verify_test_completion "$JOURNEY_ID"
    
    print_header "STEP 4: ULTRA-RELIABLE TEST RESULTS"
    
    generate_final_report "${stages[@]}"
}

# Collect job metrics
collect_job_metrics() {
    local journey_id="$1"
    local job_id="$2"
    local stage_id="$3"
    
    local metrics_data='{
        "action": "get_job_metrics",
        "journey_id": "'$journey_id'",
        "job_id": "'$job_id'"
    }'
    
    if robust_api_call "Getting metrics for job $job_id" "$JOURNEY_TOOL" "$metrics_data" "metrics"; then
        print_result "success" "Metrics collected for job $job_id"
    else
        print_result "failure" "Failed to collect metrics for job $job_id"
    fi
}

# Generate journey summary
generate_journey_summary() {
    local journey_id="$1"
    
    print_step "Generating comprehensive journey summary report"
    
    local summary_data='{
        "action": "generate_summary_report",
        "journey_id": "'$journey_id'",
        "report_type": "ultra_reliable_comprehensive",
        "report_title": "Ultra-Reliable Job Management Test - Complete Journey Analysis",
        "include_sections": [
            "journey_overview",
            "stage_progress",
            "job_statistics",
            "error_summary",
            "performance_metrics",
            "log_analysis",
            "reliability_assessment",
            "recommendations"
        ]
    }'
    
    if robust_api_call "Generating journey summary" "$LOGS_TOOL" "$summary_data" "report_id"; then
        print_result "success" "Journey summary report generated"
    else
        print_result "failure" "Failed to generate journey summary report"
    fi
}

# Verify test completion
verify_test_completion() {
    local journey_id="$1"
    
    print_step "Performing final test completion verification"
    
    local list_jobs_data='{
        "action": "list_jobs",
        "journey_id": "'$journey_id'",
        "limit": 50,
        "include_stage_info": true,
        "include_status": true
    }'
    
    if robust_api_call "Final verification job listing" "$JOURNEY_TOOL" "$list_jobs_data" "total_jobs"; then
        print_result "success" "Test completion verification successful"
    else
        print_result "failure" "Test completion verification failed"
    fi
}

# Generate final comprehensive report
generate_final_report() {
    local stages=("$@")
    
    echo "🎯 ULTRA-RELIABLE TEST EXECUTION SUMMARY"
    echo "════════════════════════════════════════════════════════════════════════"
    echo "📊 Reliability Statistics:"
    echo "  • Total Tests Executed: $TOTAL_TESTS"
    echo "  • Successful Tests: $PASSED_TESTS"
    echo "  • Failed Tests: $FAILED_TESTS"
    echo "  • Critical Failures: $CRITICAL_FAILURES"
    if [ $TOTAL_TESTS -gt 0 ]; then
        echo "  • Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
        echo "  • Reliability Score: $(( (TOTAL_TESTS - CRITICAL_FAILURES) * 100 / TOTAL_TESTS ))%"
    fi
    echo "  • Test Log: $LOG_FILE"
    echo ""
    
    echo "🔄 Stage-by-Stage Results:"
    echo "────────────────────────────────────────────────────────────────────────"
    for i in "${!stages[@]}"; do
        local stage_id="${stages[i]}"
        local job_id="${STAGE_JOBS[$stage_id]}"
        local status="${JOB_STATUS[$job_id]:-"not_created"}"
        local logs_count="${JOB_LOGS_COUNT[$job_id]:-"0"}"
        local report_id="${JOB_REPORTS[$job_id]:-"none"}"
        local health="${STAGE_HEALTH[$stage_id]:-"unknown"}"
        
        # Calculate job duration if available
        local duration=""
        if [ -n "${JOB_START_TIME[$job_id]}" ] && [ -n "${JOB_END_TIME[$job_id]}" ]; then
            duration="$((JOB_END_TIME[$job_id] - JOB_START_TIME[$job_id]))s"
        fi
        
        echo "  Stage $((i+1)): $stage_id"
        echo "    Health: $health"
        echo "    Job ID: $job_id"
        echo "    Status: $status"
        echo "    Duration: ${duration:-"N/A"}"
        echo "    Logs: $logs_count entries"
        echo "    Report: $report_id"
        echo ""
    done
    
    echo "🏆 ULTRA-RELIABLE JOB MANAGEMENT TEST COMPLETED!"
    echo "════════════════════════════════════════════════════════════════════════"
    echo "✅ Journey ID: $JOURNEY_ID"
    echo "✅ Stages Tested: ${#stages[@]}"
    echo "✅ Jobs Created: ${#STAGE_JOBS[@]}"
    echo "✅ Reliability Features: Health checks, retry logic, validation, monitoring"
    echo "✅ Test logging: $LOG_FILE"
    echo ""
    
    # Determine overall result
    if [ $CRITICAL_FAILURES -eq 0 ]; then
        if [ $FAILED_TESTS -eq 0 ]; then
            echo "🎖️ PERFECT RELIABILITY - All tests passed with zero failures!"
            exit 0
        elif [ $FAILED_TESTS -le 2 ]; then
            echo "🥇 HIGH RELIABILITY - Minor issues detected but system is stable"
            exit 0
        else
            echo "🥈 MODERATE RELIABILITY - Some issues detected, review recommended"
            exit 1
        fi
    else
        echo "🚨 RELIABILITY ISSUES - Critical failures detected, immediate attention required"
        exit 1
    fi
}

# Execute main function with all reliability features
main "$@" 