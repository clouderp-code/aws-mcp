#!/bin/bash

# Test script to verify cleanup logic works correctly before real cleanup
set -e

SERVER_URL="${1:-http://localhost:8000}"
TIMEOUT=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Cleanup Script Logic Safely${NC}"
echo "====================================="

# Test journey listing and ID extraction
echo -e "\n${YELLOW}📋 Testing Journey Listing and ID Extraction${NC}"

# Make the actual API call
echo "Making request to journeys tool..."
response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
    -H "Content-Type: application/json" \
    -d '{"action": "list", "limit": 10, "include_stages": true}' \
    --connect-timeout $TIMEOUT \
    --max-time $TIMEOUT 2>&1)

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ API call successful${NC}"
    
    # Check response structure
    status=$(echo "$response" | jq -r '.result.status // .status // "unknown"' 2>/dev/null)
    echo "Status: $status"
    
    if [[ "$status" == "success" ]]; then
        # Test journey ID extraction with validation
        echo -e "\n${BLUE}Testing journey ID extraction...${NC}"
        
        journey_ids=$(echo "$response" | jq -r '.result.journeys[]?.journeyId // .journeys[]?.journeyId // .result.journeys[]?.journey_id // .journeys[]?.journey_id // empty' 2>/dev/null)
        
        echo "Raw journey IDs extracted:"
        echo "$journey_ids"
        
        # Clean and validate journey IDs
        echo -e "\n${BLUE}Cleaning and validating journey IDs...${NC}"
        valid_count=0
        invalid_count=0
        
        while IFS= read -r journey_id; do
            # Trim whitespace and validate format
            journey_id=$(echo "$journey_id" | tr -d '\n\r\t ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            
            if [[ -n "$journey_id" ]]; then
                if [[ "$journey_id" =~ ^JRN- ]]; then
                    echo -e "${GREEN}  ✅ Valid: $journey_id${NC}"
                    valid_count=$((valid_count + 1))
                else
                    echo -e "${RED}  ❌ Invalid format: '$journey_id'${NC}"
                    invalid_count=$((invalid_count + 1))
                fi
            fi
        done <<< "$journey_ids"
        
        echo -e "\n${BLUE}Validation Results:${NC}"
        echo -e "  Valid journey IDs: ${GREEN}$valid_count${NC}"
        echo -e "  Invalid entries: ${RED}$invalid_count${NC}"
        
        if [[ $valid_count -gt 0 ]] && [[ $invalid_count -eq 0 ]]; then
            echo -e "\n${GREEN}🎉 Journey ID extraction works correctly!${NC}"
            echo -e "${GREEN}✅ Safe to proceed with cleanup script${NC}"
            
            # Show first few journey IDs that would be deleted
            echo -e "\n${YELLOW}First 5 journey IDs that would be processed:${NC}"
            echo "$journey_ids" | head -5 | while IFS= read -r journey_id; do
                journey_id=$(echo "$journey_id" | tr -d '\n\r\t ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [[ -n "$journey_id" ]] && [[ "$journey_id" =~ ^JRN- ]]; then
                    echo "  - $journey_id"
                fi
            done
            
        else
            echo -e "\n${RED}❌ Journey ID extraction has issues!${NC}"
            echo -e "${RED}Do NOT run cleanup script until this is fixed${NC}"
        fi
        
    else
        error_msg=$(echo "$response" | jq -r '.result.message // .message // "Unknown error"' 2>/dev/null)
        echo -e "${RED}❌ API returned error: $error_msg${NC}"
    fi
    
else
    echo -e "${RED}❌ API call failed: $response${NC}"
fi

# Test deletion JSON formatting
echo -e "\n${YELLOW}📋 Testing Deletion JSON Formatting${NC}"

test_journey_id="JRN-TEST123456"
delete_json="{\"action\": \"delete\", \"journey_id\": \"$test_journey_id\"}"

echo "Testing JSON format for deletion:"
echo "$delete_json" | jq . 2>/dev/null

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Deletion JSON format is valid${NC}"
else
    echo -e "${RED}❌ Deletion JSON format is invalid${NC}"
fi

echo -e "\n${BLUE}🏁 Safety Test Complete${NC}"
echo "=============================" 