#!/bin/bash

# Journey Creation Test (No Cleanup)
# Creates a journey with default stages but leaves data in DynamoDB for inspection

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVER_URL="http://localhost:8000"

# Logging configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../../logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/test_journey_create_$(date +%Y-%m-%d_%H-%M-%S).log"
EXECUTION_ID="CREATE_$(date +%s)"

# Initialize logging
setup_logging() {
    echo "=== Journey Creation Test Log - $(date) ===" > "$LOG_FILE"
    echo "Execution ID: $EXECUTION_ID" >> "$LOG_FILE"
    echo "Server URL: $SERVER_URL" >> "$LOG_FILE"
    echo "Log File: $LOG_FILE" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
}

# Enhanced logging functions
log_to_file() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $level | $message" >> "$LOG_FILE"
}

log_info() {
    local message="$1"
    echo -e "${CYAN}ℹ️  $message${NC}"
    log_to_file "INFO" "$message"
}

log_success() {
    local message="$1"
    echo -e "${GREEN}✅ $message${NC}"
    log_to_file "SUCCESS" "$message"
}

log_error() {
    local message="$1"
    echo -e "${RED}❌ $message${NC}"
    log_to_file "ERROR" "$message"
}

log_warning() {
    local message="$1"
    echo -e "${YELLOW}⚠️  $message${NC}"
    log_to_file "WARNING" "$message"
}

log_step() {
    local message="$1"
    echo -e "${PURPLE}🔄 $message${NC}"
    log_to_file "STEP" "$message"
}

log_debug() {
    local message="$1"
    log_to_file "DEBUG" "$message"
}

# API helper functions
call_api() {
    local action="$1"
    local data="$2"
    log_debug "API Call - Action: $action, Data: $data"
    local response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d "$data")
    log_debug "API Response: $response"
    echo "$response"
}

check_api_success() {
    local response="$1"
    echo "$response" | jq -e '.result.status == "success"' >/dev/null 2>&1
}

get_total_dynamodb_records() {
    aws dynamodb scan \
        --table-name TransformationSystem \
        --select COUNT \
        --query 'Count' \
        --output text 2>/dev/null || echo "0"
}

get_journey_record_count() {
    local journey_id="$1"
    clean_id=${journey_id#JRN-}
    aws dynamodb scan \
        --table-name TransformationSystem \
        --filter-expression "begins_with(PK, :pk)" \
        --expression-attribute-values "{\":pk\":{\"S\":\"JOURNEY#$clean_id\"}}" \
        --select COUNT \
        --query 'Count' \
        --output text 2>/dev/null || echo "0"
}

# Initialize logging
setup_logging

# Test Header
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              🏗️  Journey Creation Test (Persistent)        ║"
echo "║           Create Journey + Stages (No Cleanup)              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log_info "Starting Journey Creation Test"
log_info "Execution ID: $EXECUTION_ID"
log_info "Log file: $LOG_FILE"

# Phase 1: Initial State
echo -e "${PURPLE}📊 PHASE 1: Initial State Assessment${NC}"
echo "=================================================="
log_step "Getting initial DynamoDB record count"
INITIAL_DB_COUNT=$(get_total_dynamodb_records)
log_info "Initial DynamoDB records: $INITIAL_DB_COUNT"

log_step "Getting initial journey count via API"
INITIAL_COUNT_RESPONSE=$(call_api "list" '{"action": "list"}')
if check_api_success "$INITIAL_COUNT_RESPONSE"; then
    INITIAL_JOURNEY_COUNT=$(echo "$INITIAL_COUNT_RESPONSE" | jq -r '.result.total_journeys // 0')
    log_info "Initial journey count: $INITIAL_JOURNEY_COUNT"
else
    log_warning "Could not get initial journey count"
    INITIAL_JOURNEY_COUNT=0
fi

# Phase 2: Journey Creation
echo -e "\n${PURPLE}🆕 PHASE 2: Journey Creation with Comprehensive Metadata${NC}"
echo "=============================================================="

log_step "Creating journey with comprehensive metadata"

CREATE_DATA="{
    \"action\": \"create\",
    \"odaComponentType\": \"customer-management\",
    \"name\": \"TMF ODA Schema Transformation\",
    \"description\": \"Comprehensive transformation of legacy database schema to TMF ODA compliance standards\",
    \"priority\": \"high\",
    \"createdBy\": \"system_admin\"
}"

CREATE_RESPONSE=$(call_api "create" "$CREATE_DATA")
echo "DEBUG: CREATE_RESPONSE=$CREATE_RESPONSE"

if check_api_success "$CREATE_RESPONSE"; then
    JOURNEY_ID=$(echo "$CREATE_RESPONSE" | jq -r '.result.journey_id')
    log_success "Journey created successfully: $JOURNEY_ID"
else
    log_error "Failed to create journey"
    echo "$CREATE_RESPONSE" | jq -r '.result.message // "Unknown error"'
    exit 1
fi

# Phase 3: Add Default Stages
echo -e "\n${PURPLE}🏗️  PHASE 3: Adding Six Default Transformation Stages${NC}"
echo "===================================================="

log_step "Adding default transformation stages to journey"

ADD_STAGES_DATA="{
    \"action\": \"add_default_stages\",
    \"journey_id\": \"$JOURNEY_ID\"
}"

ADD_STAGES_RESPONSE=$(call_api "add_default_stages" "$ADD_STAGES_DATA")

if check_api_success "$ADD_STAGES_RESPONSE"; then
    STAGES_ADDED=$(echo "$ADD_STAGES_RESPONSE" | jq -r '.result.stages_added // 0')
    TOTAL_STAGES=$(echo "$ADD_STAGES_RESPONSE" | jq -r '.result.total_stages // 0')
    log_success "Default stages added successfully: $STAGES_ADDED/$TOTAL_STAGES stages"
    log_info "Expected stages: raw_analysis, stripped_schema, tmf_mapping, migration_planning, data_migration, verification_validation"
else
    log_warning "Failed to add default stages"
    echo "$ADD_STAGES_RESPONSE" | jq -r '.result.message // "Unknown error"'
fi

# Phase 4: Final Verification
echo -e "\n${PURPLE}📊 PHASE 4: Final State Verification${NC}"
echo "====================================="

log_step "Verifying journey and stages creation in DynamoDB"
FINAL_DB_COUNT=$(get_total_dynamodb_records)
JOURNEY_RECORDS=$(get_journey_record_count "$JOURNEY_ID")
log_info "Total DynamoDB records: $FINAL_DB_COUNT"
log_info "Journey-specific records: $JOURNEY_RECORDS"

FINAL_COUNT_RESPONSE=$(call_api "list" '{"action": "list"}')
if check_api_success "$FINAL_COUNT_RESPONSE"; then
    FINAL_JOURNEY_COUNT=$(echo "$FINAL_COUNT_RESPONSE" | jq -r '.result.total_journeys // 0')
    log_info "API journey count: $FINAL_JOURNEY_COUNT"
else
    log_warning "Could not get final journey count"
fi

# Summary
echo -e "\n${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    📋 CREATION RESULTS                       ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Journey ID: $JOURNEY_ID"
echo "║ Creation: ✅ SUCCESS"
echo "║ Default Stages: ${STAGES_ADDED:-0}/${TOTAL_STAGES:-6} stages added"
echo "║ DynamoDB Records Created: $((FINAL_DB_COUNT - INITIAL_DB_COUNT))"
echo "║ Journey-Specific Records: $JOURNEY_RECORDS"
echo "║ API Journey Count: $FINAL_JOURNEY_COUNT"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}🎉 JOURNEY CREATION COMPLETED - DATA PERSISTED IN DYNAMODB! 🎉${NC}"
echo -e "${CYAN}💡 To view the data in DynamoDB:${NC}"
echo -e "${CYAN}   aws dynamodb scan --table-name TransformationSystem --query 'Items[*].[PK.S,SK.S,EntityType.S]' --output table${NC}"
echo -e "${CYAN}💡 To clean up later, run: ./clean_journeys_data.sh${NC}" 

# Final logging
log_success "Journey Creation Test Completed Successfully"
log_info "Journey ID: $JOURNEY_ID"
log_info "Total DynamoDB records created: $((FINAL_DB_COUNT - INITIAL_DB_COUNT))"
log_info "Journey-specific records: $JOURNEY_RECORDS"
log_info "Test execution completed at: $(date)"
log_info "Log file saved to: $LOG_FILE"

echo ""
echo -e "${CYAN}📋 Test logs saved to: $LOG_FILE${NC}" 