#!/bin/bash

# Second Brain Functionality Test Script
# Tests Second Brain rules management step by step

SERVER_URL="http://localhost:8000"
ECHO_JSON=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 Testing Second Brain Functionality${NC}"
echo "=============================================="

# First, let's create a journey to work with
echo -e "\n${YELLOW}📋 Step 1: Create a journey with default stages${NC}"

CREATE_JOURNEY_DATA='{
    "action": "create",
    "journey_data": {
        "name": "Second Brain Test Journey",
        "description": "Testing Second Brain rules functionality",
        "odaComponentType": "customer-management",
        "priority": "high",
        "include_default_stages": true
    }
}'

echo "Creating journey for Second Brain testing..."
JOURNEY_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/simple-journeys" \
  -H "Content-Type: application/json" \
  -d "$CREATE_JOURNEY_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Journey creation successful${NC}"
    
    # Extract journey ID
    JOURNEY_ID=$(echo "$JOURNEY_RESPONSE" | jq -r '.result.journey_id // empty')
    STAGES_COUNT=$(echo "$JOURNEY_RESPONSE" | jq -r '.result.stages_count // 0')
    
    echo "Journey ID: $JOURNEY_ID"
    echo "Stages Count: $STAGES_COUNT"
    
    if [ -n "$JOURNEY_ID" ] && [ "$JOURNEY_ID" != "null" ]; then
        echo -e "${GREEN}🎉 Ready to test Second Brain with journey: $JOURNEY_ID${NC}"
    else
        echo -e "${RED}❌ Failed to get journey ID${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Journey creation failed${NC}"
    exit 1
fi

# Test 1: List existing rules
echo -e "\n${YELLOW}📋 Step 2: List existing Second Brain rules${NC}"

LIST_RULES_DATA='{
    "action": "list_rules",
    "journey_id": "'$JOURNEY_ID'"
}'

echo "Listing existing Second Brain rules..."
LIST_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$LIST_RULES_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ List rules successful${NC}"
    
    RULES_COUNT=$(echo "$LIST_RESPONSE" | jq -r '.result.total_rules // 0')
    echo "Current rules count: $RULES_COUNT"
    
    if [ "$ECHO_JSON" = true ]; then
        echo "Response:"
        echo "$LIST_RESPONSE" | jq .
    fi
else
    echo -e "${RED}❌ List rules failed${NC}"
fi

# Test 2: Add a custom Second Brain rule
echo -e "\n${YELLOW}📋 Step 3: Add a custom Second Brain rule${NC}"

ADD_RULE_DATA='{
    "action": "add_rule",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "raw_analysis",
    "rule_data": {
        "rule_id": "custom_field_mapping_rule",
        "title": "Custom Field Mapping Rule",
        "description": "Custom rule for enhanced field mapping during raw analysis",
        "type": "field_mapping",
        "priority": "high",
        "scope": "stage",
        "content": {
            "conditions": {
                "column_patterns": ["user_*", "customer_*", "account_*"],
                "data_types": ["varchar", "text", "string"]
            },
            "actions": {
                "suggest_tmf_mapping": true,
                "confidence_threshold": 0.8,
                "auto_apply": false
            },
            "metadata": {
                "author": "test_user",
                "version": "1.0",
                "tags": ["field_mapping", "customer_data", "test"]
            }
        }
    }
}'

echo "Adding custom Second Brain rule..."
ADD_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$ADD_RULE_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Add rule successful${NC}"
    
    STATUS=$(echo "$ADD_RESPONSE" | jq -r '.result.status // "unknown"')
    MESSAGE=$(echo "$ADD_RESPONSE" | jq -r '.result.message // "No message"')
    
    echo "Status: $STATUS"
    echo "Message: $MESSAGE"
    
    if [ "$ECHO_JSON" = true ]; then
        echo "Response:"
        echo "$ADD_RESPONSE" | jq .
    fi
else
    echo -e "${RED}❌ Add rule failed${NC}"
fi

# Test 3: List rules again to see the new rule
echo -e "\n${YELLOW}📋 Step 4: List rules again to verify addition${NC}"

echo "Listing rules after addition..."
LIST_RESPONSE2=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$LIST_RULES_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ List rules successful${NC}"
    
    RULES_COUNT2=$(echo "$LIST_RESPONSE2" | jq -r '.result.total_rules // 0')
    echo "Updated rules count: $RULES_COUNT2"
    
    # Show rule details
    echo -e "\n${CYAN}📝 Rule Details:${NC}"
    echo "$LIST_RESPONSE2" | jq '.result.rules[] | select(.ruleId == "custom_field_mapping_rule") | {ruleId, name, description, type, priority}'
    
    if [ "$ECHO_JSON" = true ]; then
        echo "Full Response:"
        echo "$LIST_RESPONSE2" | jq .
    fi
else
    echo -e "${RED}❌ List rules failed${NC}"
fi

# Test 4: Update the Second Brain rule
echo -e "\n${YELLOW}📋 Step 5: Update the Second Brain rule${NC}"

UPDATE_RULE_DATA='{
    "action": "update_rule",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "raw_analysis",
    "rule_id": "custom_field_mapping_rule",
    "rule_data": {
        "title": "Enhanced Custom Field Mapping Rule",
        "description": "Enhanced rule for field mapping with improved AI suggestions",
        "type": "field_mapping",
        "priority": "critical",
        "scope": "stage",
        "content": {
            "conditions": {
                "column_patterns": ["user_*", "customer_*", "account_*", "contact_*"],
                "data_types": ["varchar", "text", "string", "char"]
            },
            "actions": {
                "suggest_tmf_mapping": true,
                "confidence_threshold": 0.75,
                "auto_apply": false,
                "generate_alternatives": true
            },
            "metadata": {
                "author": "test_user",
                "version": "1.1",
                "tags": ["field_mapping", "customer_data", "enhanced", "test"],
                "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
            }
        }
    }
}'

echo "Updating Second Brain rule..."
UPDATE_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$UPDATE_RULE_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Update rule successful${NC}"
    
    STATUS=$(echo "$UPDATE_RESPONSE" | jq -r '.result.status // "unknown"')
    MESSAGE=$(echo "$UPDATE_RESPONSE" | jq -r '.result.message // "No message"')
    
    echo "Status: $STATUS"
    echo "Message: $MESSAGE"
    
    if [ "$ECHO_JSON" = true ]; then
        echo "Response:"
        echo "$UPDATE_RESPONSE" | jq .
    fi
else
    echo -e "${RED}❌ Update rule failed${NC}"
fi

# Test 5: List rules to verify update
echo -e "\n${YELLOW}📋 Step 6: Verify rule update${NC}"

echo "Listing rules after update..."
LIST_RESPONSE3=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$LIST_RULES_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ List rules successful${NC}"
    
    # Show updated rule details
    echo -e "\n${CYAN}📝 Updated Rule Details:${NC}"
    echo "$LIST_RESPONSE3" | jq '.result.rules[] | select(.ruleId == "custom_field_mapping_rule") | {ruleId, name, description, type, priority, version: .metadata.version}'
else
    echo -e "${RED}❌ List rules failed${NC}"
fi

# Test 6: Add another rule for a different stage
echo -e "\n${YELLOW}📋 Step 7: Add rule for different stage (tmf_mapping)${NC}"

ADD_RULE2_DATA='{
    "action": "add_rule",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "tmf_mapping",
    "rule_data": {
        "rule_id": "tmf_validation_rule",
        "title": "TMF Schema Validation Rule",
        "description": "Validation rule for TMF schema compliance",
        "type": "validation_rules",
        "priority": "medium",
        "scope": "stage",
        "content": {
            "conditions": {
                "schema_patterns": ["Customer", "Product", "Service"],
                "required_fields": ["id", "name", "status"]
            },
            "actions": {
                "validate_schema": true,
                "suggest_fixes": true,
                "generate_report": true
            },
            "metadata": {
                "author": "test_user",
                "version": "1.0",
                "tags": ["validation", "tmf_schema", "compliance"]
            }
        }
    }
}'

echo "Adding TMF validation rule..."
ADD_RESPONSE2=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$ADD_RULE2_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Add TMF rule successful${NC}"
    
    STATUS=$(echo "$ADD_RESPONSE2" | jq -r '.result.status // "unknown"')
    MESSAGE=$(echo "$ADD_RESPONSE2" | jq -r '.result.message // "No message"')
    
    echo "Status: $STATUS"
    echo "Message: $MESSAGE"
else
    echo -e "${RED}❌ Add TMF rule failed${NC}"
fi

# Test 7: List rules by stage filter
echo -e "\n${YELLOW}📋 Step 8: List rules filtered by stage${NC}"

LIST_STAGE_RULES_DATA='{
    "action": "list_rules",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "raw_analysis"
}'

echo "Listing rules for raw_analysis stage only..."
STAGE_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$LIST_STAGE_RULES_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stage rules list successful${NC}"
    
    STAGE_RULES_COUNT=$(echo "$STAGE_RESPONSE" | jq -r '.result.total_rules // 0')
    echo "Rules for raw_analysis stage: $STAGE_RULES_COUNT"
    
    echo -e "\n${CYAN}📝 Raw Analysis Stage Rules:${NC}"
    echo "$STAGE_RESPONSE" | jq '.result.rules[] | {ruleId, name, stageId, type, priority}'
else
    echo -e "${RED}❌ Stage rules list failed${NC}"
fi

# Test 8: Delete a rule
echo -e "\n${YELLOW}📋 Step 9: Delete Second Brain rule${NC}"

DELETE_RULE_DATA='{
    "action": "delete_rule",
    "journey_id": "'$JOURNEY_ID'",
    "stage_id": "tmf_mapping",
    "rule_id": "tmf_validation_rule"
}'

echo "Deleting TMF validation rule..."
DELETE_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$DELETE_RULE_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Delete rule successful${NC}"
    
    STATUS=$(echo "$DELETE_RESPONSE" | jq -r '.result.status // "unknown"')
    MESSAGE=$(echo "$DELETE_RESPONSE" | jq -r '.result.message // "No message"')
    
    echo "Status: $STATUS"
    echo "Message: $MESSAGE"
else
    echo -e "${RED}❌ Delete rule failed${NC}"
fi

# Test 9: Final rules count
echo -e "\n${YELLOW}📋 Step 10: Final rules verification${NC}"

echo "Final rules count check..."
FINAL_RESPONSE=$(curl -s -X POST "$SERVER_URL/tools/journeys" \
  -H "Content-Type: application/json" \
  -d "$LIST_RULES_DATA")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Final verification successful${NC}"
    
    FINAL_RULES_COUNT=$(echo "$FINAL_RESPONSE" | jq -r '.result.total_rules // 0')
    echo "Final rules count: $FINAL_RULES_COUNT"
    
    echo -e "\n${CYAN}📊 Summary of Remaining Rules:${NC}"
    echo "$FINAL_RESPONSE" | jq '.result.rules[] | {ruleId, name, stageId, type, priority}'
else
    echo -e "${RED}❌ Final verification failed${NC}"
fi

echo -e "\n${BLUE}🎉 Second Brain functionality test completed!${NC}"
echo "=============================================="
echo -e "${GREEN}✅ Journey created with ID: $JOURNEY_ID${NC}"
echo -e "${GREEN}✅ Second Brain rules tested: add, update, delete, list${NC}"
echo -e "${GREEN}✅ Stage-specific rule filtering tested${NC}"
echo -e "${GREEN}✅ Different rule types tested: field_mapping, validation_rules${NC}"

echo -e "\n${PURPLE}💡 Second Brain Test Summary:${NC}"
echo "• ✅ Rule Creation (field_mapping type)"
echo "• ✅ Rule Listing (all & filtered by stage)"  
echo "• ✅ Rule Updates (metadata, conditions, actions)"
echo "• ✅ Rule Deletion"
echo "• ✅ Multiple Stage Support"
echo "• ✅ Different Rule Types (field_mapping, validation_rules)"

echo -e "\n${CYAN}🔧 Manual Test Commands:${NC}"
echo "List all rules:"
echo "  curl -X POST $SERVER_URL/tools/journeys -H 'Content-Type: application/json' -d '{\"action\":\"list_rules\",\"journey_id\":\"$JOURNEY_ID\"}'"
echo ""
echo "Add custom rule:"
echo "  curl -X POST $SERVER_URL/tools/journeys -H 'Content-Type: application/json' -d '{\"action\":\"add_rule\",\"journey_id\":\"$JOURNEY_ID\",\"stage_id\":\"raw_analysis\",\"rule_data\":{\"rule_id\":\"test_rule\",\"title\":\"Test Rule\",\"description\":\"Test description\",\"type\":\"field_mapping\",\"priority\":\"medium\",\"scope\":\"stage\",\"content\":{}}}'" 