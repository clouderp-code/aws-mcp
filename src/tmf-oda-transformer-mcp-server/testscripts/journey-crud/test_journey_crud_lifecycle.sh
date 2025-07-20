#!/bin/bash

# Journey CRUD Lifecycle Test
# Tests complete journey lifecycle: Create → Update → Delete
# Verifies all related records are properly managed

set -e

# Configuration
SERVER_URL="http://localhost:8000"
TEST_JOURNEY_NAME="Test Journey CRUD $(date +%s)"
TEST_DESCRIPTION="Comprehensive CRUD test journey with full lifecycle validation"
ODA_COMPONENT_TYPE="ProductCatalogManagement"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

# Function to get DynamoDB record count
get_dynamodb_count() {
    aws dynamodb scan \
        --table-name TransformationSystem \
        --select COUNT \
        --output json 2>/dev/null | jq -r '.Count // 0'
}

# Function to get journey-specific record count
get_journey_record_count() {
    local journey_id="$1"
    local clean_id="${journey_id#JRN-}"
    
    aws dynamodb query \
        --table-name TransformationSystem \
        --key-condition-expression "PK = :pk" \
        --expression-attribute-values "{\":pk\":{\"S\":\"JOURNEY#${clean_id}\"}}" \
        --select COUNT \
        --output json 2>/dev/null | jq -r '.Count // 0'
}

# API helper functions
call_api() {
    local action="$1"
    local data="$2"
    curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d "$data"
}

# Function to extract journey ID from response
extract_journey_id() {
    echo "$1" | jq -r '.result.journey_id // .result.journeyId // empty'
}

# Function to check API response status
check_api_success() {
    local response="$1"
    local status=$(echo "$response" | jq -r '.result.status // empty')
    
    if [ "$status" = "success" ]; then
        return 0
    else
        log_error "API call failed: $(echo "$response" | jq -r '.result.message // "Unknown error"')"
        return 1
    fi
}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 🧪 Journey CRUD Lifecycle Test              ║"
echo "║              Complete Create → Update → Delete              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Phase 1: Initial State
echo -e "\n${PURPLE}📊 PHASE 1: Initial State Assessment${NC}"
echo "=================================================="

log_step "Getting initial DynamoDB record count"
INITIAL_DB_COUNT=$(get_dynamodb_count)
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
echo -e "\n${PURPLE}🆕 PHASE 2: Journey Creation with Metadata${NC}"
echo "=============================================="

log_step "Creating journey with comprehensive metadata"

CREATE_DATA="{
    \"action\": \"create\",
    \"journey_data\": {
        \"name\": \"$TEST_JOURNEY_NAME\",
        \"description\": \"$TEST_DESCRIPTION\",
        \"odaComponentType\": \"$ODA_COMPONENT_TYPE\",
        \"sourceSystem\": \"TestSystem\",
        \"targetSystem\": \"TMF-ODA\",
        \"priority\": \"high\",
        \"estimatedDuration\": \"2h 30m\",
        \"tags\": [\"test\", \"crud\", \"validation\"],
        \"owner\": \"test-user\",
        \"version\": \"1.0.0\",
        \"environment\": \"test\"
    }
}"

CREATE_RESPONSE=$(call_api "create" "$CREATE_DATA")

if check_api_success "$CREATE_RESPONSE"; then
    JOURNEY_ID=$(extract_journey_id "$CREATE_RESPONSE")
    if [ -n "$JOURNEY_ID" ]; then
        log_success "Journey created successfully: $JOURNEY_ID"
    else
        log_error "Journey created but ID not found in response"
        exit 1
    fi
else
    log_error "Failed to create journey"
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
    log_warning "Failed to add default stages - continuing with test"
fi

# Verify both journey and stages in DynamoDB
log_step "Verifying journey and stages creation in DynamoDB"
JOURNEY_RECORDS_AFTER_STAGES=$(get_journey_record_count "$JOURNEY_ID")
log_info "Journey records after stage creation: $JOURNEY_RECORDS_AFTER_STAGES"

if [ "$JOURNEY_RECORDS_AFTER_STAGES" -gt 1 ]; then
    log_success "Journey and stages successfully stored in DynamoDB"
    EXPECTED_RECORDS=$((1 + ${STAGES_ADDED:-6}))  # 1 metadata + stages
    log_info "Expected records: ~$EXPECTED_RECORDS (1 metadata + $STAGES_ADDED stages)"
else
    log_warning "Only journey metadata found in DynamoDB"
fi

# Phase 4: Journey Update
echo -e "\n${PURPLE}🔄 PHASE 4: Journey Metadata Update${NC}"
echo "==================================="

log_step "Updating journey metadata"

UPDATE_DATA="{
    \"action\": \"update\",
    \"journey_id\": \"$JOURNEY_ID\",
    \"journey_data\": {
        \"description\": \"UPDATED: $TEST_DESCRIPTION - Modified in CRUD test\",
        \"priority\": \"critical\",
        \"estimatedDuration\": \"3h 15m\",
        \"tags\": [\"test\", \"crud\", \"validation\", \"updated\"],
        \"version\": \"1.1.0\",
        \"lastModified\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
        \"status\": \"active\"
    }
}"

UPDATE_RESPONSE=$(call_api "update" "$UPDATE_DATA")

if check_api_success "$UPDATE_RESPONSE"; then
    log_success "Journey metadata updated successfully"
else
    log_error "Failed to update journey metadata"
    exit 1
fi

# Phase 5: Verification of Update
echo -e "\n${PURPLE}🔍 PHASE 5: Update Verification${NC}"
echo "==============================="

log_step "Verifying journey update via API"

READ_DATA="{
    \"action\": \"read\",
    \"journey_id\": \"$JOURNEY_ID\"
}"

READ_RESPONSE=$(call_api "read" "$READ_DATA")

if check_api_success "$READ_RESPONSE"; then
    UPDATED_DESCRIPTION=$(echo "$READ_RESPONSE" | jq -r '.result.journey.description // empty')
    UPDATED_VERSION=$(echo "$READ_RESPONSE" | jq -r '.result.journey.version // empty')
    
    if [[ "$UPDATED_DESCRIPTION" == *"UPDATED"* ]]; then
        log_success "Description update verified: ✓"
    else
        log_warning "Description update not reflected"
    fi
    
    if [ "$UPDATED_VERSION" = "1.1.0" ]; then
        log_success "Version update verified: ✓"
    else
        log_warning "Version update not reflected"
    fi
else
    log_error "Failed to verify journey update"
fi

# Phase 6: Pre-Delete State
echo -e "\n${PURPLE}📋 PHASE 6: Pre-Delete State Assessment${NC}"
echo "========================================"

log_step "Checking state before deletion"

# Get current counts
CURRENT_DB_COUNT=$(get_dynamodb_count)
CURRENT_JOURNEY_RECORDS=$(get_journey_record_count "$JOURNEY_ID")

LIST_RESPONSE_PRE_DELETE=$(call_api "list")
CURRENT_JOURNEY_COUNT=$(echo "$LIST_RESPONSE_PRE_DELETE" | jq -r '.result.total_journeys // 0')

log_info "DynamoDB records before delete: $CURRENT_DB_COUNT"
log_info "Journey-specific records before delete: $CURRENT_JOURNEY_RECORDS"
log_info "Total journeys before delete: $CURRENT_JOURNEY_COUNT"

# Phase 7: Journey Deletion
echo -e "\n${PURPLE}🗑️  PHASE 7: Journey Deletion${NC}"
echo "=============================="

log_step "Deleting journey and all related records"

DELETE_DATA="{
    \"action\": \"delete\",
    \"journey_id\": \"$JOURNEY_ID\"
}"

DELETE_RESPONSE=$(call_api "delete" "$DELETE_DATA")

if check_api_success "$DELETE_RESPONSE"; then
    log_success "Delete API call successful"
else
    log_error "Failed to delete journey"
    exit 1
fi

# Phase 8: Post-Delete Verification
echo -e "\n${PURPLE}✅ PHASE 8: Post-Delete Verification${NC}"
echo "===================================="

log_step "Verifying complete deletion"

# Wait a moment for deletion to complete
sleep 2

# Check DynamoDB record counts
FINAL_DB_COUNT=$(get_dynamodb_count)
FINAL_JOURNEY_RECORDS=$(get_journey_record_count "$JOURNEY_ID")

# Check API journey count
LIST_RESPONSE_FINAL=$(call_api "list")
FINAL_JOURNEY_COUNT=$(echo "$LIST_RESPONSE_FINAL" | jq -r '.result.total_journeys // 0')

# Calculate reductions
DB_REDUCTION=$((CURRENT_DB_COUNT - FINAL_DB_COUNT))
JOURNEY_COUNT_REDUCTION=$((CURRENT_JOURNEY_COUNT - FINAL_JOURNEY_COUNT))

log_info "DynamoDB records after delete: $FINAL_DB_COUNT"
log_info "Journey-specific records after delete: $FINAL_JOURNEY_RECORDS"
log_info "Total journeys after delete: $FINAL_JOURNEY_COUNT"

echo -e "\n${BLUE}📊 DELETION ANALYSIS${NC}"
echo "===================="
echo "DynamoDB reduction: $DB_REDUCTION records"
echo "Journey count reduction: $JOURNEY_COUNT_REDUCTION"
echo "Journey-specific records remaining: $FINAL_JOURNEY_RECORDS"
echo "Expected deletion: ~$((1 + ${STAGES_ADDED:-6})) records (1 metadata + ${STAGES_ADDED:-6} stages)"

# Phase 9: Results Summary
echo -e "\n${PURPLE}🎯 PHASE 9: CRUD Lifecycle Results Summary${NC}"
echo "==========================================="

# Validation checks
ALL_CHECKS_PASSED=true

if [ "$JOURNEY_COUNT_REDUCTION" -eq 1 ]; then
    log_success "API count correctly reduced by 1"
else
    log_error "API count reduction incorrect: expected 1, got $JOURNEY_COUNT_REDUCTION"
    ALL_CHECKS_PASSED=false
fi

if [ "$FINAL_JOURNEY_RECORDS" -eq 0 ]; then
    log_success "All journey-specific records removed from DynamoDB"
else
    log_error "Journey records still remain in DynamoDB: $FINAL_JOURNEY_RECORDS"
    ALL_CHECKS_PASSED=false
fi

EXPECTED_DELETION=$((1 + ${STAGES_ADDED:-6}))
if [ "$DB_REDUCTION" -ge "$EXPECTED_DELETION" ]; then
    log_success "DynamoDB records properly deleted: $DB_REDUCTION records (expected: ~$EXPECTED_DELETION)"
elif [ "$DB_REDUCTION" -gt 0 ]; then
    log_warning "Some DynamoDB records deleted: $DB_REDUCTION records (expected: ~$EXPECTED_DELETION)"
else
    log_error "No DynamoDB records were deleted"
    ALL_CHECKS_PASSED=false
fi

# Final summary box
echo -e "\n${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    📋 FINAL RESULTS                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Journey ID: $JOURNEY_ID"
echo "║ Creation: ✅ SUCCESS"
echo "║ Default Stages: ${STAGES_ADDED:-0}/${TOTAL_STAGES:-6} stages added"
echo "║ Update: ✅ SUCCESS"
echo "║ Deletion: ✅ SUCCESS"
echo "║ API Count Change: $JOURNEY_COUNT_REDUCTION"
echo "║ DynamoDB Records Deleted: $DB_REDUCTION (expected: ~$EXPECTED_DELETION)"
echo "║ Journey Records Remaining: $FINAL_JOURNEY_RECORDS"

if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo "║ Overall Status: 🎉 ALL TESTS PASSED"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${GREEN}🎉 CRUD LIFECYCLE TEST COMPLETED SUCCESSFULLY! 🎉${NC}"
    exit 0
else
    echo "║ Overall Status: ❌ SOME TESTS FAILED"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${RED}❌ CRUD LIFECYCLE TEST FAILED - CHECK ERRORS ABOVE${NC}"
    exit 1
fi 