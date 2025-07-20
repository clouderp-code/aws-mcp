#!/bin/bash

# Test script to verify the cleanup script parsing works correctly
# This simulates the JSON response that caused the issue

set -e

# Test JSON response that matches what the server actually returns
TEST_JSON='{
  "result": {
    "status": "success", 
    "message": "Retrieved 3 journeys (total: 3)",
    "journeys": [
      {"journeyId": "JRN-TEST001", "name": "Test Journey 1"},
      {"journeyId": "JRN-TEST002", "name": "Test Journey 2"},
      {"journeyId": "JRN-TEST003", "name": "Test Journey 3"}
    ],
    "total_journeys": 3
  }
}'

echo "Testing JSON parsing logic from cleanup script..."
echo
echo "Test JSON:"
echo "$TEST_JSON" | jq .
echo

# Test status extraction
echo "Testing status extraction:"
status=$(echo "$TEST_JSON" | jq -r '.result.status // .status // "unknown"' 2>/dev/null)
echo "Extracted status: $status"

# Test journey ID extraction  
echo "Testing journey ID extraction:"
journey_ids=$(echo "$TEST_JSON" | jq -r '.result.journeys[]?.journeyId // .journeys[]?.journeyId // .result.journeys[]?.journey_id // .journeys[]?.journey_id // empty' 2>/dev/null)
echo "Extracted journey IDs:"
echo "$journey_ids"

# Count journeys
count=0
while IFS= read -r journey_id; do
    if [[ -n "$journey_id" ]]; then
        count=$((count + 1))
        echo "$count. $journey_id"
    fi
done <<< "$journey_ids"

echo
echo "Total journeys found: $count"

if [[ $count -eq 3 && "$status" == "success" ]]; then
    echo "✅ Parsing logic works correctly!"
    exit 0
else
    echo "❌ Parsing logic failed!"
    exit 1
fi 