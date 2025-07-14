#!/bin/bash

# =============================================================================
# Quick Journey Tool Test Script
# =============================================================================
# This script tests the most common journey operations in a simple format
# Usage: ./quick_test_journeys.sh [SERVER_URL]
# Default SERVER_URL: http://localhost:8000
# =============================================================================

# Configuration
SERVER_URL="${1:-http://localhost:8000}"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}🚀 Quick Journey Tool Test${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${BLUE}Server: $SERVER_URL${NC}"
echo -e "${CYAN}========================================${NC}"

# Function to run a test
run_test() {
    local name="$1"
    local endpoint="$2"
    local data="$3"
    
    echo -e "\n${YELLOW}🔍 Testing: $name${NC}"
    echo -e "${BLUE}   Endpoint: $endpoint${NC}"
    
    local response=$(curl -s -X POST "$SERVER_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT 2>&1)
    
    if [[ $? -eq 0 ]]; then
        # Pretty print JSON response
        echo -e "${GREEN}   ✅ Response:${NC}"
        echo "$response" | jq . 2>/dev/null || echo "   $response"
        
        # Check status (look in both top level and result.status)
        local status=$(echo "$response" | jq -r '.status // .result.status // "unknown"' 2>/dev/null)
        if [[ "$status" == "success" ]]; then
            echo -e "${GREEN}   ✅ Status: SUCCESS${NC}"
        elif [[ "$status" == "error" ]]; then
            echo -e "${RED}   ❌ Status: ERROR${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Status: UNKNOWN${NC}"
        fi
    else
        echo -e "${RED}   ❌ Request failed: $response${NC}"
    fi
}

# =============================================================================
# QUICK TESTS
# =============================================================================

# 1. Health Check
echo -e "\n${CYAN}🏥 Health Check${NC}"
health_response=$(curl -s -X GET "$SERVER_URL/health" --connect-timeout $TIMEOUT --max-time $TIMEOUT 2>&1)
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Server is healthy${NC}"
else
    echo -e "${RED}❌ Server health check failed${NC}"
    exit 1
fi

# 2. List All Journeys
run_test "List All Journeys" "/tools/journeys" '{
    "action": "read",
    "journey_id": "",
    "include_stages": true,
    "include_job_history": true,
    "limit": 10
}'

# 3. Get Journey Dashboard
run_test "Journey Dashboard" "/tools/journeys" '{
    "action": "dashboard",
    "journey_id": "JRN-TEST-001"
}'

# 4. List Journey Stages
run_test "List Journey Stages" "/tools/journeys" '{
    "action": "list_stages",
    "journey_id": "JRN-TEST-001"
}'

# 5. Run a Job
run_test "Run Job" "/tools/journeys" '{
    "action": "run_job",
    "journey_id": "JRN-TEST-001",
    "stage_id": "raw_analysis",
    "triggered_by": "quick-test",
    "reason": "Quick test execution"
}'

# 6. Get Job Metrics
run_test "Get Job Metrics" "/tools/journeys" '{
    "action": "get_job_metrics",
    "journey_id": "JRN-TEST-001",
    "job_id": "JOB-001-20240101120000"
}'

# 7. Search Logs
run_test "Search Logs" "/tools/logs-and-reports" '{
    "action": "search_logs",
    "journey_id": "JRN-TEST-001",
    "search_query": "schema parsing"
}'

# 8. Get Error Summary
run_test "Get Error Summary" "/tools/logs-and-reports" '{
    "action": "get_error_summary",
    "journey_id": "JRN-TEST-001",
    "job_id": "JOB-001-20240101120000"
}'

echo -e "\n${CYAN}========================================${NC}"
echo -e "${GREEN}🎉 Quick tests completed!${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${BLUE}💡 For comprehensive testing, run:${NC}"
echo -e "${YELLOW}   ./test_journey_endpoints.sh${NC}"
echo -e "${CYAN}========================================${NC}" 