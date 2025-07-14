# Journey Tool Testing Scripts

This directory contains two comprehensive test scripts for your TMF ODA Transformer MCP Server journey tools.

## 📋 Available Scripts

### 1. `test_journey_endpoints.sh` - Comprehensive Test Suite

A complete test suite that mirrors all the pytest test cases from `test_journeys.py`.

**Features:**
- Tests all 39 journey and logs endpoints
- Comprehensive error handling tests
- Backward compatibility tests
- Color-coded output with detailed formatting
- Test result summary with pass/fail counts
- Detailed JSON response parsing

**Usage:**
```bash
# Test against localhost (default)
./test_journey_endpoints.sh

# Test against specific server
./test_journey_endpoints.sh http://your-server-ip:8000

# Test against remote server
./test_journey_endpoints.sh http://18.191.87.212:8000
```

### 2. `quick_test_journeys.sh` - Quick Testing

A streamlined script for testing the most common journey operations.

**Features:**
- Tests 8 most common operations
- Quick health check
- Simplified output format
- Fast execution (10-second timeout)
- Perfect for quick validation

**Usage:**
```bash
# Quick test against localhost
./quick_test_journeys.sh

# Quick test against specific server
./quick_test_journeys.sh http://your-server-ip:8000
```

## 🧪 Test Categories

### Journey CRUD Operations
- ✅ List all journeys
- ✅ Create journey
- ✅ Update journey
- ✅ Delete journey

### Stage Management
- ✅ List stages
- ✅ Add custom stage
- ✅ Update stage
- ✅ Delete stage
- ✅ Add default TMF ODA stages

### Rules Management
- ✅ List rules
- ✅ Add rule
- ✅ Update rule
- ✅ Delete rule

### Job Management
- ✅ List jobs
- ✅ Get job details
- ✅ Run job
- ✅ Cancel job
- ✅ Update job status
- ✅ Retry job
- ✅ Get job metrics
- ✅ Get job timeline
- ✅ Batch cancel jobs

### Interactive Features
- ✅ Dashboard
- ✅ Journey summary

### Logs and Reports
- ✅ Get job logs
- ✅ Add log entry
- ✅ Search logs
- ✅ Get logs by level
- ✅ Export job logs
- ✅ Get error summary
- ✅ Generate summary report
- ✅ Analyze job performance

### Error Handling
- ✅ Missing required parameters
- ✅ Invalid actions
- ✅ Service exceptions

## 🎯 Sample Test Data

The scripts use realistic test data:

```json
{
  "journey_id": "JRN-TEST-001",
  "job_id": "JOB-001-20240101120000",
  "stage_id": "raw_analysis",
  "rule_id": "RULE-001"
}
```

## 🔧 Prerequisites

- `curl` command-line tool
- `jq` for JSON parsing (optional but recommended)
- Running MCP server on specified port

## 📊 Understanding Output

### Success Response
```
✅ SUCCESS: List all journeys completed successfully
```

### Error Response
```
❌ ERROR: Create new journey failed: create_journey method not implemented
```

### Response Format
All responses include:
- `status`: "success" or "error"
- `operation`: The specific operation performed
- `duration_seconds`: How long the operation took
- `timestamp`: When the operation was performed

## 🐛 Common Issues

1. **Connection Refused**: Make sure your MCP server is running
2. **Timeout**: Increase timeout values in the scripts if needed
3. **JSON Parse Error**: Some responses may not be valid JSON (script handles this gracefully)

## 🚀 Running Against Your Server

Since your server is running on `http://0.0.0.0:8000`, you can test with:

```bash
# Quick test
./quick_test_journeys.sh http://localhost:8000

# Full test suite
./test_journey_endpoints.sh http://localhost:8000
```

## 📈 Expected Results

Based on your pytest test file, some operations are expected to fail due to:
- Unimplemented methods (create_journey, update_journey, etc.)
- Known issues (duplicate keyword arguments)
- Missing test data

The scripts will clearly indicate which tests pass/fail and why.

## 🔄 Continuous Testing

Use these scripts during development to:
- Validate new features
- Test error handling
- Verify backward compatibility
- Performance testing with different timeouts

## 🎉 Happy Testing!

These scripts provide a comprehensive way to test your journey tool functionality through simple curl commands with human-readable output. 