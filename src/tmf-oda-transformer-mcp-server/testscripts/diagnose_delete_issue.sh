#!/bin/bash

# Diagnostic script to understand the delete issue
set -e

SERVER_URL="${1:-http://localhost:8000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🔍 Diagnosing Journey Delete Issue${NC}"
echo "=================================="

# Step 1: Get a sample journey ID from API
echo -e "\n${YELLOW}1️⃣ Getting a sample journey from API${NC}"

api_response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
    -H "Content-Type: application/json" \
    -d '{"action": "list", "limit": 5, "include_stages": false}')

sample_journey_id=$(echo "$api_response" | jq -r '.result.journeys[0]?.journeyId // empty' 2>/dev/null)

if [[ -n "$sample_journey_id" ]]; then
    echo -e "${GREEN}✅ Found sample journey: $sample_journey_id${NC}"
else
    echo -e "${RED}❌ No journeys found in API${NC}"
    exit 1
fi

# Step 2: Check what this looks like in DynamoDB
echo -e "\n${YELLOW}2️⃣ Checking DynamoDB format for this journey${NC}"

# Extract the clean ID (remove JRN- prefix)
clean_id="${sample_journey_id#JRN-}"
expected_pk="JOURNEY#$clean_id"

echo -e "${CYAN}API Journey ID: $sample_journey_id${NC}"
echo -e "${CYAN}Expected DynamoDB PK: $expected_pk${NC}"

# Try to find this record in DynamoDB
if command -v aws >/dev/null 2>&1; then
    echo -e "\n${BLUE}Checking if this record exists in DynamoDB...${NC}"
    
    # Check for METADATA record
    metadata_check=$(aws dynamodb get-item \
        --table-name TransformationSystem \
        --key "{\"PK\":{\"S\":\"$expected_pk\"},\"SK\":{\"S\":\"METADATA\"}}" \
        --projection-expression "PK,SK" \
        --no-cli-pager 2>/dev/null || echo "ERROR")
    
    if [[ "$metadata_check" != "ERROR" ]] && [[ "$metadata_check" != "{}" ]]; then
        echo -e "${GREEN}✅ METADATA record exists: $expected_pk${NC}"
        
        # Count stage records for this journey
        stage_count=$(aws dynamodb query \
            --table-name TransformationSystem \
            --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
            --expression-attribute-values "{\":pk\":{\"S\":\"$expected_pk\"},\":sk\":{\"S\":\"STAGE#\"}}" \
            --select "COUNT" \
            --no-cli-pager 2>/dev/null | jq -r '.Count // 0' 2>/dev/null)
        
        echo -e "${GREEN}✅ STAGE records found: $stage_count${NC}"
        
        # Show stage records
        if [[ "$stage_count" -gt 0 ]]; then
            echo -e "\n${BLUE}Stage records for this journey:${NC}"
            aws dynamodb query \
                --table-name TransformationSystem \
                --key-condition-expression "PK = :pk AND begins_with(SK, :sk)" \
                --expression-attribute-values "{\":pk\":{\"S\":\"$expected_pk\"},\":sk\":{\"S\":\"STAGE#\"}}" \
                --projection-expression "SK,EntityType" \
                --no-cli-pager 2>/dev/null | \
            jq -r '.Items[]? | "  🔧 " + .SK.S + " (" + .EntityType.S + ")"' 2>/dev/null
        fi
        
    else
        echo -e "${RED}❌ METADATA record NOT found: $expected_pk${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  AWS CLI not available - cannot check DynamoDB directly${NC}"
fi

# Step 3: Test what the delete API would actually try to delete
echo -e "\n${YELLOW}3️⃣ Testing Delete API (DRY RUN)${NC}"

# Show what the API would try to delete
echo -e "${CYAN}What the delete API would attempt:${NC}"
echo -e "  Delete METADATA: PK = JOURNEY#$sample_journey_id, SK = METADATA"
echo -e "  Query for stages: PK = JOURNEY#$sample_journey_id, SK begins_with STAGE#"

# The issue: JOURNEY#JRN-XXXXX vs JOURNEY#XXXXX
wrong_pk="JOURNEY#$sample_journey_id"
echo -e "\n${RED}❌ BUG IDENTIFIED:${NC}"
echo -e "${RED}   API tries to delete: $wrong_pk${NC}"
echo -e "${GREEN}   But record exists as: $expected_pk${NC}"

# Step 4: Show the difference
echo -e "\n${YELLOW}4️⃣ ID Format Analysis${NC}"
echo -e "${CYAN}================================${NC}"
echo -e "API ID:           $sample_journey_id"
echo -e "Clean ID:         $clean_id"  
echo -e "Correct PK:       $expected_pk"
echo -e "Wrong PK:         $wrong_pk"
echo -e "${CYAN}================================${NC}"

# Step 5: Test correct deletion format
if command -v aws >/dev/null 2>&1; then
    echo -e "\n${YELLOW}5️⃣ Testing Correct Deletion Logic${NC}"
    
    # Create a test to see if the correct PK would work
    test_result=$(aws dynamodb get-item \
        --table-name TransformationSystem \
        --key "{\"PK\":{\"S\":\"$expected_pk\"},\"SK\":{\"S\":\"METADATA\"}}" \
        --projection-expression "PK" \
        --no-cli-pager 2>/dev/null || echo "ERROR")
    
    if [[ "$test_result" != "ERROR" ]] && [[ "$test_result" != "{}" ]]; then
        echo -e "${GREEN}✅ Correct PK format finds the record${NC}"
        echo -e "${BLUE}💡 Solution: The delete function needs ID cleaning${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not verify with correct PK${NC}"
    fi
fi

echo -e "\n${YELLOW}📋 Summary${NC}"
echo "============"
echo -e "${RED}🐛 BUG: Delete function uses wrong PK format${NC}"
echo -e "   • API sends: JRN-XXXXX"
echo -e "   • Delete tries: JOURNEY#JRN-XXXXX" 
echo -e "   • Should be: JOURNEY#XXXXX"
echo ""
echo -e "${BLUE}🔧 FIX NEEDED: Add ID cleaning in delete function${NC}"
echo -e "   clean_id = journey_id.replace('JRN-', '')"
echo -e "   PK = f'JOURNEY#{clean_id}'" 