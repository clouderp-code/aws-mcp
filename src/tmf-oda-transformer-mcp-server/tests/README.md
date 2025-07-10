# TMF ODA Transformer MCP Server - Test Suite

## Overview

This directory contains comprehensive tests for all tools provided by the TMF ODA Transformer MCP Server. The tests verify that each tool works correctly and handles various scenarios including success cases, error conditions, and edge cases.

## Test Structure

### Test Files

1. **test_schema_analyzer.py** - Tests for the `schema-analyzer` tool
2. **test_db_analyzer.py** - Tests for the `db-analyzer` tool  
3. **test_raw_analysis.py** - Tests for the `raw-analysis` tool
4. **test_stripped_schema.py** - Tests for the `stripped-schema` tool
5. **test_get_job_logs.py** - Tests for the `get-job-logs` tool

### Configuration Files

- **conftest.py** - Pytest configuration and shared fixtures
- **requirements-test.txt** - Test dependencies
- **test_runner.py** - Comprehensive test runner with detailed reporting
- **verify_tools.py** - Simple tool verification script

## Tools Tested

### 🔍 Schema Analyzer Tool (`schema-analyzer`)

**Purpose**: Discover and analyze schema files for TMF ODA transformation requirements.

**Tests Cover**:
- ✅ Successful schema analysis with valid workspace
- ✅ Analysis with specific format filters (JSON Schema, OpenAPI, etc.)
- ✅ Error handling for empty/invalid workspace directories
- ✅ Validation of ODA component types
- ✅ Handling of timeout scenarios
- ✅ Summary statistics calculation
- ✅ Performance timing measurement

**Test Cases**: 15+ comprehensive test scenarios

### 🗄️ Database Analyzer Tool (`db-analyzer`)

**Purpose**: Connect to and analyze database structures for TMF ODA transformation requirements.

**Tests Cover**:
- ✅ Successful database analysis for PostgreSQL, MySQL, MongoDB
- ✅ Table filtering functionality
- ✅ Connection string validation
- ✅ Database type validation
- ✅ Error handling for connection failures
- ✅ Security considerations (password sanitization)
- ✅ Compliance scoring and reporting

**Test Cases**: 17+ comprehensive test scenarios

### ⚡ Raw Analysis Tool (`raw-analysis`)

**Purpose**: Execute raw analysis stage of TMF ODA transformation journey.

**Tests Cover**:
- ✅ Successful job execution
- ✅ Parameter validation (journey ID, stage ID)
- ✅ AWS role ARN handling
- ✅ Job timing measurement
- ✅ Error handling and recovery
- ✅ TransformationJobExecutor integration
- ✅ Result message formatting

**Test Cases**: 12+ comprehensive test scenarios

### 🔧 Stripped Schema Tool (`stripped-schema`)

**Purpose**: Execute stripped schema stage of TMF ODA transformation journey.

**Tests Cover**:
- ✅ Successful schema stripping execution
- ✅ Parameter validation
- ✅ Sequential execution after raw analysis
- ✅ Custom stage ID handling
- ✅ Error recovery mechanisms
- ✅ Job execution monitoring

**Test Cases**: 14+ comprehensive test scenarios

### 📋 Get Job Logs Tool (`get-job-logs`)

**Purpose**: Retrieve execution logs for specific job steps from S3 storage.

**Tests Cover**:
- ✅ Successful log retrieval from S3
- ✅ AWS role ARN authentication
- ✅ Handling of missing logs (NoSuchKey)
- ✅ JSON parsing and validation
- ✅ S3 key format verification
- ✅ Large log file handling
- ✅ Empty log file scenarios

**Test Cases**: 13+ comprehensive test scenarios

## Test Features

### Mocking and Fixtures

- **AWS Services**: Mock S3, EC2, IAM for safe testing
- **Database Connections**: Mock various database types
- **File Systems**: Temporary directories and file creation
- **Time/Date**: Consistent timing for reproducible tests
- **Context Objects**: Mock MCP context for error handling

### Error Scenarios Tested

- ✅ Invalid input parameters
- ✅ Missing required fields
- ✅ Network failures
- ✅ AWS service errors
- ✅ File system errors
- ✅ JSON parsing errors
- ✅ Timeout scenarios
- ✅ Memory and resource constraints

### Validation Testing

- ✅ Input sanitization
- ✅ Parameter type checking
- ✅ Range and format validation
- ✅ Security considerations
- ✅ Resource limits
- ✅ Performance thresholds

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

### Running All Tests

```bash
# Using pytest
python -m pytest tests/ -v

# Using our test runner
python tests/test_runner.py

# Quick verification
python verify_tools.py
```

### Running Specific Tests

```bash
# Test individual tools
python -m pytest tests/test_schema_analyzer.py -v
python -m pytest tests/test_db_analyzer.py -v
python -m pytest tests/test_raw_analysis.py -v
python -m pytest tests/test_stripped_schema.py -v
python -m pytest tests/test_get_job_logs.py -v

# Test specific scenarios
python -m pytest tests/test_schema_analyzer.py::TestSchemaAnalyzer::test_schema_analyzer_success -v
```

## Test Results

The test suite verifies **71+ individual test cases** covering:

### Functionality Verification ✅

- **Schema Discovery**: File scanning, format detection, validation
- **Database Analysis**: Connection testing, schema extraction, compliance checking  
- **Job Execution**: Stage management, error handling, result reporting
- **Log Management**: S3 integration, retrieval, parsing, formatting
- **AWS Integration**: Credential handling, role assumption, service interaction

### Quality Assurance ✅

- **Input Validation**: All parameters validated for type, format, and range
- **Error Handling**: Graceful failure modes with meaningful error messages
- **Performance**: Timing measurement and resource usage monitoring
- **Security**: Credential sanitization, secure connection handling
- **Reliability**: Timeout handling, retry mechanisms, state management

### Edge Cases ✅

- **Empty/Invalid Inputs**: Comprehensive validation testing
- **Network Issues**: Connection failures, timeout scenarios
- **Resource Limits**: Large files, memory constraints, processing limits
- **Concurrent Access**: Multiple job execution, resource conflicts
- **Data Corruption**: Invalid JSON, malformed schemas, broken connections

## Test Coverage

The test suite provides comprehensive coverage of:

- **Happy Path Scenarios**: 25+ successful execution tests
- **Error Conditions**: 30+ error handling tests  
- **Edge Cases**: 15+ boundary condition tests
- **Integration Points**: AWS services, file systems, databases

## Benefits

This comprehensive test suite ensures:

1. **Reliability**: All tools work correctly under various conditions
2. **Maintainability**: Changes can be validated quickly
3. **Documentation**: Tests serve as usage examples
4. **Quality**: High confidence in tool functionality
5. **Debugging**: Clear error messages and failure modes

## Future Enhancements

- **Performance Testing**: Load testing with large datasets
- **Integration Testing**: End-to-end workflow testing
- **Security Testing**: Penetration testing and vulnerability assessment
- **Stress Testing**: High concurrency and resource exhaustion scenarios 