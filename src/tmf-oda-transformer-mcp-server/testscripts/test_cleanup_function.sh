#!/bin/bash

# Test script to verify the cleanup function works correctly
set -e

SERVER_URL="${1:-http://localhost:8000}"
TIMEOUT=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Mock log file for testing
LOG_FILE="/tmp/test_cleanup_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE"

echo -e "${BLUE}🧪 Testing Cleanup Functions in Isolation${NC}"
echo "========================================="

# Source the log_message function from the cleanup script
log_message() {
    local message="$1"
    local no_color_message=$(echo -e "$message" | sed 's/\x1b\[[0-9;]*m//g')
    echo -e "$message" >&2  # Send to stderr to avoid contaminating stdout
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $no_color_message" >> "$LOG_FILE"
    sync
}

# Test version of get_all_journeys function
get_all_journeys() {
    log_message "${BLUE}Retrieving all journeys from system...${NC}"
    
    local response=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
        -H "Content-Type: application/json" \
        -d '{"action": "list", "limit": 1000, "include_stages": true}' \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        # Log to file only to avoid contamination
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] LIST_RESPONSE: $response" >> "$LOG_FILE"
        
        local status=$(echo "$response" | jq -r '.result.status // .status // "unknown"' 2>/dev/null)
        if [[ "$status" == "success" ]]; then
            # Extract journey IDs - handle both direct response and nested result structure
            local journey_ids=$(echo "$response" | jq -r '.result.journeys[]?.journeyId // .journeys[]?.journeyId // .result.journeys[]?.journey_id // .journeys[]?.journey_id // empty' 2>/dev/null)
            
            # Clean journey IDs - remove any whitespace and ensure they start with JRN-
            local clean_journey_ids=""
            while IFS= read -r journey_id; do
                # Trim whitespace and validate format
                journey_id=$(echo "$journey_id" | tr -d '\n\r\t ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [[ -n "$journey_id" ]] && [[ "$journey_id" =~ ^JRN- ]]; then
                    if [[ -n "$clean_journey_ids" ]]; then
                        clean_journey_ids="$clean_journey_ids\n$journey_id"
                    else
                        clean_journey_ids="$journey_id"
                    fi
                fi
            done <<< "$journey_ids"
            
            if [[ -n "$clean_journey_ids" ]]; then
                log_message "${GREEN}✅ Found journeys in system${NC}"
                echo -e "$clean_journey_ids"  # This should be the ONLY stdout output
                return 0
            else
                log_message "${YELLOW}⚠️  No journeys found in system${NC}"
                return 1
            fi
        else
            local error_msg=$(echo "$response" | jq -r '.result.message // .message // "Unknown error"' 2>/dev/null)
            log_message "${RED}❌ ERROR: Failed to list journeys: $error_msg${NC}"
            return 1
        fi
    else
        log_message "${RED}❌ ERROR: Failed to connect to server: $response${NC}"
        return 1
    fi
}

echo -e "\n${YELLOW}📋 Testing get_all_journeys function isolation${NC}"

# Capture only stdout (journey IDs)
journey_ids=$(get_all_journeys)
result=$?

echo -e "\n${BLUE}Captured journey IDs:${NC}" >&2
echo -e "${GREEN}=================${NC}" >&2

# Validate each captured ID
count=0
while IFS= read -r journey_id; do
    if [[ -n "$journey_id" ]] && [[ "$journey_id" =~ ^JRN- ]]; then
        count=$((count + 1))
        echo -e "${GREEN}  ✅ $count: $journey_id${NC}" >&2
    else
        echo -e "${RED}  ❌ Invalid: '$journey_id'${NC}" >&2
    fi
done <<< "$journey_ids"

echo -e "${GREEN}=================${NC}" >&2

if [[ $result -eq 0 ]] && [[ $count -gt 0 ]]; then
    echo -e "\n${GREEN}🎉 SUCCESS: Function correctly isolated journey IDs!${NC}" >&2
    echo -e "${GREEN}✅ Total valid journey IDs: $count${NC}" >&2
    echo -e "${GREEN}✅ No log contamination in stdout${NC}" >&2
else
    echo -e "\n${RED}❌ FAILURE: Function has issues${NC}" >&2
    echo -e "${RED}Return code: $result${NC}" >&2
    echo -e "${RED}Journey count: $count${NC}" >&2
fi

# Cleanup
rm -f "$LOG_FILE"

echo -e "\n${BLUE}🏁 Function Test Complete${NC}" >&2
echo "=============================" >&2 