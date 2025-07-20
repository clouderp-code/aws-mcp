#!/bin/bash

# Test script to verify the delete fix works
set -e

SERVER_URL="${1:-http://localhost:8000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Delete Fix${NC}"
echo "====================="

# Step 1: Get current journey count
echo -e "\n${YELLOW}1️⃣ Getting current journey count${NC}"

api_response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
    -H "Content-Type: application/json" \
    -d '{"action": "list", "limit": 1000, "include_stages": false}')

total_before=$(echo "$api_response" | jq -r '.result.total_journeys // 0' 2>/dev/null)
echo -e "${CYAN}Journeys before delete: $total_before${NC}"

if [[ "$total_before" -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  No journeys to test deletion${NC}"
    exit 0
fi

# Get a sample journey ID
sample_journey_id=$(echo "$api_response" | jq -r '.result.journeys[0]?.journeyId // empty' 2>/dev/null)
echo -e "${CYAN}Sample journey to delete: $sample_journey_id${NC}"

# Step 2: Check DynamoDB record count before
if command -v aws >/dev/null 2>&1; then
    echo -e "\n${YELLOW}2️⃣ Checking DynamoDB record count before deletion${NC}"
    
    dynamodb_before=$(aws dynamodb scan \
        --table-name TransformationSystem \
        --select "COUNT" \
        --no-cli-pager 2>/dev/null | jq -r '.Count // 0' 2>/dev/null)
    
    echo -e "${CYAN}DynamoDB records before: $dynamodb_before${NC}"
    
    # Check specific journey records
    clean_id="${sample_journey_id#JRN-}"
    journey_records_before=$(aws dynamodb query \
        --table-name TransformationSystem \
        --key-condition-expression "PK = :pk" \
        --expression-attribute-values "{\":pk\":{\"S\":\"JOURNEY#$clean_id\"}}" \
        --select "COUNT" \
        --no-cli-pager 2>/dev/null | jq -r '.Count // 0' 2>/dev/null)
    
    echo -e "${CYAN}Records for journey $sample_journey_id: $journey_records_before${NC}"
fi

# Step 3: Delete the journey
echo -e "\n${YELLOW}3️⃣ Testing deletion of: $sample_journey_id${NC}"

delete_response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
    -H "Content-Type: application/json" \
    -d "{\"action\": \"delete\", \"journey_id\": \"$sample_journey_id\"}")

delete_status=$(echo "$delete_response" | jq -r '.result.status // .status // "unknown"' 2>/dev/null)

if [[ "$delete_status" == "success" ]]; then
    echo -e "${GREEN}✅ Delete API returned success${NC}"
else
    echo -e "${RED}❌ Delete API failed: $delete_status${NC}"
    echo "Response: $delete_response"
    exit 1
fi

# Step 4: Verify deletion worked
echo -e "\n${YELLOW}4️⃣ Verifying deletion worked${NC}"

# Check API count
sleep 2  # Brief pause for consistency

api_response_after=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
    -H "Content-Type: application/json" \
    -d '{"action": "list", "limit": 1000, "include_stages": false}')

total_after=$(echo "$api_response_after" | jq -r '.result.total_journeys // 0' 2>/dev/null)
echo -e "${CYAN}Journeys after delete: $total_after${NC}"

api_count_reduced=$((total_before - total_after))
echo -e "${CYAN}API count reduction: $api_count_reduced${NC}"

# Check DynamoDB
if command -v aws >/dev/null 2>&1; then
    dynamodb_after=$(aws dynamodb scan \
        --table-name TransformationSystem \
        --select "COUNT" \
        --no-cli-pager 2>/dev/null | jq -r '.Count // 0' 2>/dev/null)
    
    echo -e "${CYAN}DynamoDB records after: $dynamodb_after${NC}"
    
    dynamodb_reduction=$((dynamodb_before - dynamodb_after))
    echo -e "${CYAN}DynamoDB reduction: $dynamodb_reduction records${NC}"
    
    # Check specific journey records (should be 0)
    journey_records_after=$(aws dynamodb query \
        --table-name TransformationSystem \
        --key-condition-expression "PK = :pk" \
        --expression-attribute-values "{\":pk\":{\"S\":\"JOURNEY#$clean_id\"}}" \
        --select "COUNT" \
        --no-cli-pager 2>/dev/null | jq -r '.Count // 0' 2>/dev/null)
    
    echo -e "${CYAN}Records for deleted journey: $journey_records_after${NC}"
fi

# Step 5: Results Analysis
echo -e "\n${YELLOW}5️⃣ Results Analysis${NC}"
echo "===================="

if [[ "$api_count_reduced" -eq 1 ]]; then
    echo -e "${GREEN}✅ API count correctly reduced by 1${NC}"
else
    echo -e "${RED}❌ API count issue: reduced by $api_count_reduced (expected 1)${NC}"
fi

if command -v aws >/dev/null 2>&1; then
    if [[ "$journey_records_after" -eq 0 ]]; then
        echo -e "${GREEN}✅ Journey records completely removed from DynamoDB${NC}"
    else
        echo -e "${RED}❌ Journey records still exist: $journey_records_after${NC}"
    fi
    
    if [[ "$dynamodb_reduction" -gt 0 ]]; then
        echo -e "${GREEN}✅ DynamoDB records actually deleted: $dynamodb_reduction${NC}"
        echo -e "${BLUE}💡 Expected reduction: 7 records (1 metadata + 6 stages)${NC}"
        
        if [[ "$dynamodb_reduction" -eq 7 ]]; then
            echo -e "${GREEN}🎉 PERFECT! Deleted exactly 7 records as expected${NC}"
        fi
    else
        echo -e "${RED}❌ No DynamoDB records were actually deleted${NC}"
    fi
fi

echo -e "\n${BLUE}📋 Fix Verification Summary${NC}"
echo "=========================="
echo -e "Journey tested: $sample_journey_id"
echo -e "API count change: $api_count_reduced"
if command -v aws >/dev/null 2>&1; then
    echo -e "DynamoDB records deleted: $dynamodb_reduction"
    echo -e "Journey records remaining: $journey_records_after"
    
    if [[ "$journey_records_after" -eq 0 ]] && [[ "$dynamodb_reduction" -gt 0 ]]; then
        echo -e "\n${GREEN}🎉 DELETE FIX VERIFIED WORKING! 🎉${NC}"
    else
        echo -e "\n${RED}❌ Delete fix still has issues${NC}"
    fi
fi 