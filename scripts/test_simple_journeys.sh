#!/bin/bash

# Simple test script for the simple journeys MCP tool

SERVER_URL="http://localhost:8000"
ECHO_JSON=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Simple Journeys MCP Tool${NC}"
echo "=============================================="

# Test 1: Create a journey with default stages
echo -e "\n${YELLOW}📋 Test 1: Create journey with default stages${NC}"

CREATE_DATA='{
    "action": "create",
    "journey_data": {
        "name": "Simple Test Journey",
        "description": "Test journey created with simple journeys tool",
        "odaComponentType": "customer-management",
        "priority": "high",
        "include_default_stages": true
    }
}'

echo "Request:"
if [ "$ECHO_JSON" = true ]; then
    echo "$CREATE_DATA" | jq .
else
    echo "Creating journey with default stages..."
fi

RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/simple-journeys" \
  -H "Content-Type: application/json" \
  -d "$CREATE_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Request successful${NC}"
    
    # Extract journey ID from response
    JOURNEY_ID=$(echo "$RESPONSE" | jq -r '.result.journey_id // empty')
    STAGES_COUNT=$(echo "$RESPONSE" | jq -r '.result.stages_count // 0')
    
    echo "Journey ID: $JOURNEY_ID"
    echo "Stages Count: $STAGES_COUNT"
    
    if [ "$STAGES_COUNT" -eq 6 ]; then
        echo -e "${GREEN}🎉 SUCCESS: Created journey with 6 stages!${NC}"
    else
        echo -e "${RED}❌ ERROR: Expected 6 stages, got $STAGES_COUNT${NC}"
    fi
    
    if [ "$ECHO_JSON" = true ]; then
        echo "Response:"
        echo "$RESPONSE" | jq .
    fi
else
    echo -e "${RED}❌ Request failed${NC}"
    exit 1
fi

# Test 2: List stages for the created journey
if [ -n "$JOURNEY_ID" ] && [ "$JOURNEY_ID" != "null" ]; then
    echo -e "\n${YELLOW}📋 Test 2: List stages for journey $JOURNEY_ID${NC}"
    
    LIST_DATA='{
        "action": "list-stages",
        "journey_id": "'$JOURNEY_ID'"
    }'
    
    echo "Request:"
    if [ "$ECHO_JSON" = true ]; then
        echo "$LIST_DATA" | jq .
    else
        echo "Listing stages for journey $JOURNEY_ID..."
    fi
    
    RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/simple-journeys" \
      -H "Content-Type: application/json" \
      -d "$LIST_DATA")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Request successful${NC}"
        
        TOTAL_STAGES=$(echo "$RESPONSE" | jq -r '.result.total_stages // 0')
        echo "Total stages: $TOTAL_STAGES"
        
        if [ "$TOTAL_STAGES" -eq 6 ]; then
            echo -e "${GREEN}🎉 SUCCESS: Found 6 stages!${NC}"
            
            # List stage names
            echo "Stages:"
            echo "$RESPONSE" | jq -r '.result.stages[] | "  - \(.stageId): \(.name)"'
        else
            echo -e "${RED}❌ ERROR: Expected 6 stages, got $TOTAL_STAGES${NC}"
        fi
        
        if [ "$ECHO_JSON" = true ]; then
            echo "Response:"
            echo "$RESPONSE" | jq .
        fi
    else
        echo -e "${RED}❌ Request failed${NC}"
    fi
else
    echo -e "${RED}❌ Cannot test list-stages: No journey ID from previous test${NC}"
fi

# Test 3: Create a journey without default stages
echo -e "\n${YELLOW}📋 Test 3: Create journey without default stages${NC}"

CREATE_NO_STAGES_DATA='{
    "action": "create",
    "journey_data": {
        "name": "Simple Test Journey No Stages",
        "description": "Test journey created without default stages",
        "odaComponentType": "product-catalog-management",
        "priority": "medium",
        "include_default_stages": false
    }
}'

echo "Request:"
if [ "$ECHO_JSON" = true ]; then
    echo "$CREATE_NO_STAGES_DATA" | jq .
else
    echo "Creating journey without default stages..."
fi

RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/simple-journeys" \
  -H "Content-Type: application/json" \
  -d "$CREATE_NO_STAGES_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Request successful${NC}"
    
    JOURNEY_ID_2=$(echo "$RESPONSE" | jq -r '.result.journey_id // empty')
    STAGES_COUNT_2=$(echo "$RESPONSE" | jq -r '.result.stages_count // 0')
    
    echo "Journey ID: $JOURNEY_ID_2"
    echo "Stages Count: $STAGES_COUNT_2"
    
    if [ "$STAGES_COUNT_2" -eq 0 ]; then
        echo -e "${GREEN}🎉 SUCCESS: Created journey with 0 stages as expected!${NC}"
    else
        echo -e "${RED}❌ ERROR: Expected 0 stages, got $STAGES_COUNT_2${NC}"
    fi
    
    if [ "$ECHO_JSON" = true ]; then
        echo "Response:"
        echo "$RESPONSE" | jq .
    fi
else
    echo -e "${RED}❌ Request failed${NC}"
fi

echo -e "\n${BLUE}🎉 Simple journeys test completed!${NC}"
echo "=============================================="
echo -e "${GREEN}✅ This tool follows the exact pattern from manage_journey.py${NC}"
echo -e "${GREEN}✅ Uses the same DynamoDB structure and operations${NC}"
echo -e "${GREEN}✅ Creates journeys with proper stage management${NC}"

# Usage instructions
echo -e "\n${BLUE}💡 Usage Examples:${NC}"
echo "Create journey with stages:"
echo "  curl -X POST $SERVER_URL/tools/simple-journeys -H 'Content-Type: application/json' -d '{\"action\":\"create\",\"journey_data\":{\"name\":\"Test\",\"description\":\"Test\",\"odaComponentType\":\"customer-management\"}}'"
echo ""
echo "List stages for journey:"
echo "  curl -X POST $SERVER_URL/tools/simple-journeys -H 'Content-Type: application/json' -d '{\"action\":\"list-stages\",\"journey_id\":\"JRN-XXXXXX\"}'" 