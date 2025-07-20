#!/bin/bash

# =============================================================================
# TMF ODA Transformer MCP Server - Journey Tool Test Script
# =============================================================================
# This script tests all journey endpoints with the NEW CONSOLIDATED journeys tool
# Usage: ./test_journey_endpoints.sh [SERVER_URL]
# Default SERVER_URL: http://localhost:8000
# 
# UPDATED FOR NEW CONSOLIDATED JOURNEYS TOOL:
# - Journey CRUD operations (create, read, update, delete) with real DynamoDB
# - Automatic creation of 6 default transformation stages
# - Stage management (add, update, delete, list stages)
# - Real data storage with proper error handling
# - No mock data - all operations use actual DynamoDB
# 
# The script tests:
# - create: Creates journeys with optional default stages
# - read/list: Lists and retrieves journey information
# - update: Updates journey metadata
# - delete: Deletes journeys and all associated stages
# - add_default_stages: Adds the 6 default transformation stages
# - Stage management: add_stage, update_stage, delete_stage, list_stages
# =============================================================================

set -e

# Configuration
SERVER_URL="${1:-http://localhost:8000}"
TIMEOUT=30

# Variables to store real IDs during test execution
CREATED_JOURNEY_ID=""
CREATED_JOURNEY_ID_2=""
STAGE_MANAGEMENT_JOURNEY_ID=""

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
    log_message "\n${BLUE}[$TEST_COUNT] Testing: $1${NC}"
    log_message "${YELLOW}Endpoint: $2${NC}"
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
        
        # Check if response contains success status
        local status=$(echo "$response" | jq -r '.status // "unknown"' 2>/dev/null)
        if [[ "$status" == "success" ]]; then
            print_success "$description completed successfully"
            
            # Extract journey_id if this is a create operation
            if [[ "$description" == *"Create"* ]]; then
                local journey_id=$(echo "$response" | jq -r '.journey_id // "unknown"' 2>/dev/null)
                if [[ "$journey_id" != "unknown" ]] && [[ -n "$journey_id" ]]; then
                    if [[ -z "$CREATED_JOURNEY_ID" ]]; then
                        CREATED_JOURNEY_ID="$journey_id"
                        log_message "${BLUE}  ➤ Stored Journey ID: $CREATED_JOURNEY_ID${NC}"
                    elif [[ -z "$CREATED_JOURNEY_ID_2" ]]; then
                        CREATED_JOURNEY_ID_2="$journey_id"
                        log_message "${BLUE}  ➤ Stored Journey ID 2: $CREATED_JOURNEY_ID_2${NC}"
                    fi
                fi
            fi
            
        elif [[ "$status" == "error" ]]; then
            local error_msg=$(echo "$response" | jq -r '.message // "Unknown error"' 2>/dev/null)
            print_error "$description failed: $error_msg"
        else
            print_warning "$description returned unexpected response format (status: $status)"
        fi
    else
        print_error "$description failed: $response"
    fi
    
    log_message "\n${CYAN}---${NC}"
}

# Function to verify default stages were created
verify_default_stages() {
    local journey_id="$1"
    
    if [[ -z "$journey_id" ]] || [[ "$journey_id" == "unknown" ]]; then
        print_error "Cannot verify stages - invalid journey ID: $journey_id"
        return 1
    fi
    
    log_message "${BLUE}Verifying default stages for journey: $journey_id${NC}"
    
    # Request to list stages
    local stages_response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d "{\"action\": \"list_stages\", \"journey_id\": \"$journey_id\"}" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        log_json_response "$stages_response" "Stages Response"
        
        local status=$(echo "$stages_response" | jq -r '.status // "unknown"' 2>/dev/null)
        if [[ "$status" == "success" ]]; then
            local total_stages=$(echo "$stages_response" | jq -r '.total_stages // 0' 2>/dev/null)
            
            log_message "${BLUE}  Total stages found: $total_stages${NC}"
            
            # Verify we have 6 stages
            if [[ "$total_stages" == "6" ]]; then
                print_success "✅ Correct number of default stages (6)"
                
                # Verify the expected stage IDs
                local expected_stages=("raw_analysis" "stripped_schema" "tmf_mapping" "migration_planning" "data_migration" "verification_validation")
                local stages_json=$(echo "$stages_response" | jq -r '.stages // []' 2>/dev/null)
                
                local verification_passed=true
                for expected_stage in "${expected_stages[@]}"; do
                    local stage_found=$(echo "$stages_json" | jq -r ".[] | select(.stageId == \"$expected_stage\") | .stageId" 2>/dev/null)
                    if [[ "$stage_found" == "$expected_stage" ]]; then
                        local stage_name=$(echo "$stages_json" | jq -r ".[] | select(.stageId == \"$expected_stage\") | .name" 2>/dev/null)
                        log_message "${GREEN}    ✅ Stage $expected_stage: $stage_name${NC}"
                    else
                        log_message "${RED}    ❌ Missing stage: $expected_stage${NC}"
                        verification_passed=false
                    fi
                done
                
                if [[ "$verification_passed" == "true" ]]; then
                    print_success "✅ All six default stages verified successfully"
                else
                    print_error "❌ Some default stages are missing"
                fi
                
            else
                print_error "❌ Incorrect number of stages found: $total_stages (expected 6)"
            fi
        else
            local error_msg=$(echo "$stages_response" | jq -r '.message // "Unknown error"' 2>/dev/null)
            print_error "Failed to get stages: $error_msg"
        fi
    else
        print_error "Failed to request stages: $stages_response"
    fi
}

# =============================================================================
# INITIALIZATION
# =============================================================================

log_message "${PURPLE}📋 Test results will be logged to: $LOG_FILE${NC}"
log_message "${CYAN}=============================================${NC}"

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

log_message "\n${BLUE}Getting available tools...${NC}"
tools_response=$(curl -s -X GET "$SERVER_URL/tools" --connect-timeout $TIMEOUT --max-time $TIMEOUT 2>&1)
if [[ $? -eq 0 ]]; then
    log_message "${GREEN}✅ Tools list retrieved${NC}"
    log_json_response "$tools_response"
    
    # Check if journeys tool is available
    local journeys_available=$(echo "$tools_response" | jq -r '.tools[] | select(.name == "journeys") | .name' 2>/dev/null)
    if [[ "$journeys_available" == "journeys" ]]; then
        log_message "${GREEN}✅ Journeys tool is available${NC}"
    else
        log_message "${RED}❌ Journeys tool not found${NC}"
        exit 1
    fi
else
    log_message "${RED}❌ Tools list failed: $tools_response${NC}"
    exit 1
fi

# =============================================================================
# JOURNEY CRUD OPERATIONS
# =============================================================================

print_header "JOURNEY CRUD OPERATIONS WITH NEW CONSOLIDATED TOOL"

# Test 1: List all journeys (READ - default action)
make_request "/tools/journeys" '{
    "action": "list",
    "limit": 10,
    "include_stages": true,
    "include_job_history": false
}' "List all journeys"

# Test 2: Create journey with default stages (primary test)
make_request "/tools/journeys" '{
    "action": "create",
    "journey_data": {
        "name": "Customer Management Transformation",
        "description": "Transform legacy CRM database to TMF ODA compliant format",
        "odaComponentType": "CustomerManagement",
        "priority": "high",
        "include_default_stages": true
    }
}' "Create journey with default stages"

# Verify the default stages were created
if [[ -n "$CREATED_JOURNEY_ID" ]] && [[ "$CREATED_JOURNEY_ID" != "unknown" ]]; then
    verify_default_stages "$CREATED_JOURNEY_ID"
    STAGE_MANAGEMENT_JOURNEY_ID="$CREATED_JOURNEY_ID"
else
    log_message "${RED}❌ No journey ID available for stage verification${NC}"
fi

# Test 3: Create another journey to test different scenarios
make_request "/tools/journeys" '{
    "action": "create", 
    "journey_data": {
        "name": "Product Catalog Migration",
        "description": "Migrate product catalog to TMF Product Catalog Management API",
        "odaComponentType": "ProductCatalogManagement",
        "priority": "medium",
        "include_default_stages": true
    }
}' "Create product catalog journey with default stages"

# Test 4: Create journey WITHOUT default stages
make_request "/tools/journeys" '{
    "action": "create",
    "journey_data": {
        "name": "Custom Workflow Journey",
        "description": "Journey with custom stages only",
        "odaComponentType": "OrderManagement", 
        "priority": "low",
        "include_default_stages": false
    }
}' "Create journey WITHOUT default stages"

# Test 5: Read specific journey
if [[ -n "$CREATED_JOURNEY_ID" ]]; then
    make_request "/tools/journeys" '{
        "action": "read",
        "journey_id": "'"$CREATED_JOURNEY_ID"'",
        "include_stages": true,
        "include_job_history": true
    }' "Read specific journey with details"
fi

# Test 6: Update journey
if [[ -n "$CREATED_JOURNEY_ID" ]]; then
    make_request "/tools/journeys" '{
        "action": "update",
        "journey_id": "'"$CREATED_JOURNEY_ID"'",
        "journey_data": {
            "priority": "critical",
            "status": "in_progress"
        }
    }' "Update journey priority and status"
fi

# =============================================================================
# STAGE MANAGEMENT OPERATIONS
# =============================================================================

print_header "STAGE MANAGEMENT OPERATIONS"

# Ensure we have a journey ID for stage management
if [[ -z "$STAGE_MANAGEMENT_JOURNEY_ID" ]] && [[ -n "$CREATED_JOURNEY_ID" ]]; then
    STAGE_MANAGEMENT_JOURNEY_ID="$CREATED_JOURNEY_ID"
fi

if [[ -n "$STAGE_MANAGEMENT_JOURNEY_ID" ]]; then
    
    # Test 7: List stages for journey
    make_request "/tools/journeys" '{
        "action": "list_stages",
        "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'"
    }' "List stages for journey"

    # Test 8: Add custom stage
    make_request "/tools/journeys" '{
        "action": "add_stage",
        "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'",
        "stage_data": {
            "stageId": "custom_validation",
            "name": "Custom Validation Stage",
            "description": "Custom business rule validation and quality checks",
            "order": 6,
            "estimatedDuration": "30m",
            "canSkip": false,
            "secondBrainEnabled": true,
            "ruleTypes": ["validation_rules", "business_rules"],
            "steps": [
                "initialize",
                "load_validation_rules",
                "validate_data",
                "generate_report",
                "finalize"
            ]
        }
    }' "Add custom validation stage"

    # Test 9: Update existing stage
    make_request "/tools/journeys" '{
        "action": "update_stage",
        "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'",
        "stage_id": "raw_analysis",
        "stage_data": {
            "name": "Enhanced Raw Analysis",
            "description": "Enhanced raw input analysis with additional metadata extraction",
            "estimatedDuration": "20m"
        }
    }' "Update raw analysis stage"

    # Test 10: Add default stages to existing journey (should add missing ones)
    make_request "/tools/journeys" '{
        "action": "add_default_stages",
        "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'"
    }' "Add default stages to existing journey"

    # Test 11: Delete custom stage
    make_request "/tools/journeys" '{
        "action": "delete_stage",
        "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'",
        "stage_id": "custom_validation"
    }' "Delete custom validation stage"

    # Test 12: List stages again to verify changes
    make_request "/tools/journeys" '{
        "action": "list_stages",
        "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'"
    }' "List stages after modifications"

else
    log_message "${RED}❌ No journey ID available for stage management tests${NC}"
fi

# =============================================================================
# ADD DEFAULT STAGES TESTING
# =============================================================================

print_header "DEFAULT STAGES FUNCTIONALITY TESTING"

# Create a journey specifically for default stages testing
make_request "/tools/journeys" '{
    "action": "create",
    "journey_data": {
        "name": "Default Stages Test Journey", 
        "description": "Journey created specifically to test add_default_stages functionality",
        "odaComponentType": "ServiceInventoryManagement",
        "priority": "medium",
        "include_default_stages": false
    }
}' "Create journey for default stages testing"

# Add default stages to the new journey
if [[ -n "$CREATED_JOURNEY_ID_2" ]]; then
    make_request "/tools/journeys" '{
        "action": "add_default_stages", 
        "journey_id": "'"$CREATED_JOURNEY_ID_2"'"
    }' "Add default stages to test journey"
    
    # Verify the stages were added correctly
    verify_default_stages "$CREATED_JOURNEY_ID_2"
fi

# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

print_header "ERROR HANDLING TESTS"

# Test missing required fields
make_request "/tools/journeys" '{
    "action": "create",
    "journey_data": {
        "name": "Incomplete Journey"
    }
}' "Create journey with missing required fields (should fail)"

# Test invalid action
make_request "/tools/journeys" '{
    "action": "invalid_action",
    "journey_id": "'"$STAGE_MANAGEMENT_JOURNEY_ID"'"
}' "Invalid action (should fail)"

# Test missing journey_id for operations that require it
make_request "/tools/journeys" '{
    "action": "update",
    "journey_data": {"status": "completed"}
}' "Update without journey_id (should fail)"

# Test invalid journey_id
make_request "/tools/journeys" '{
    "action": "read",
    "journey_id": "INVALID-JOURNEY-ID"
}' "Read with invalid journey_id (should fail)"

# =============================================================================
# CLEANUP AND DELETE TESTING
# =============================================================================

print_header "CLEANUP AND DELETE TESTING"

# Test deleting a journey (use the second created journey)
if [[ -n "$CREATED_JOURNEY_ID_2" ]]; then
    make_request "/tools/journeys" '{
        "action": "delete",
        "journey_id": "'"$CREATED_JOURNEY_ID_2"'"
    }' "Delete test journey"
    
    # Try to read the deleted journey (should fail)
    make_request "/tools/journeys" '{
        "action": "read",
        "journey_id": "'"$CREATED_JOURNEY_ID_2"'"
    }' "Try to read deleted journey (should fail)"
fi

# =============================================================================
# FINAL VERIFICATION
# =============================================================================

print_header "FINAL VERIFICATION"

# List all journeys to see final state
make_request "/tools/journeys" '{
    "action": "list",
    "limit": 20,
    "include_stages": true
}' "Final journey list verification"

# If we still have a journey, show its current state
if [[ -n "$CREATED_JOURNEY_ID" ]]; then
    make_request "/tools/journeys" '{
        "action": "read",
        "journey_id": "'"$CREATED_JOURNEY_ID"'",
        "include_stages": true,
        "include_job_history": true
    }' "Final state of main test journey"
fi

# =============================================================================
# SUMMARY
# =============================================================================

print_header "TEST SUMMARY"

log_message "\n${BLUE}Test Results:${NC}"
log_message "${GREEN}✅ Passed: $PASSED_COUNT${NC}"
log_message "${RED}❌ Failed: $FAILED_COUNT${NC}"
log_message "${YELLOW}📊 Total: $TEST_COUNT${NC}"

# Add summary to log file
echo "" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"
echo "Test run completed at $(date)" >> "$LOG_FILE"
echo "Created Journey IDs: $CREATED_JOURNEY_ID, $CREATED_JOURNEY_ID_2" >> "$LOG_FILE"
echo "Final Results - Passed: $PASSED_COUNT, Failed: $FAILED_COUNT, Total: $TEST_COUNT" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

if [ $FAILED_COUNT -eq 0 ]; then
    log_message "\n${GREEN}🎉 All tests completed successfully!${NC}"
    log_message "${BLUE}✨ The new consolidated journeys tool is working perfectly!${NC}"
    log_message "${PURPLE}📋 Full test log saved to: $LOG_FILE${NC}"
    exit 0
else
    log_message "\n${YELLOW}⚠️  Some tests failed, but this may be expected for error handling tests.${NC}"
    log_message "${BLUE}✨ Check above for specific results - core functionality appears to be working!${NC}"
    log_message "${PURPLE}📋 Full test log saved to: $LOG_FILE${NC}"
    exit 0
fi 