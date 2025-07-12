# TMF ODA Transformer MCP Server - Test Suite

## Overview

This directory contains comprehensive tests for all tools provided by the TMF ODA Transformer MCP Server. The tests verify that each tool works correctly and handles various scenarios including success cases, error conditions, and edge cases.

## Test Structure

### Test Files

1. **test_raw_analysis.py** - Tests for the `raw-analysis` tool
2. **test_stripped_schema.py** - Tests for the `stripped-schema` tool
3. **test_get_job_logs.py** - Tests for the `get-job-logs` tool
4. **test_run_jobs.py** - Tests for the `run-jobs` tool
5. **test_journeys.py** - Tests for the `journeys` tool
6. **test_test_runner.py** - Tests for the `test-runner` tool

### Configuration Files

- **conftest.py** - Pytest configuration and shared fixtures
- **requirements-test.txt** - Test dependencies
- **test_runner.py** - Comprehensive test runner with detailed reporting
- **verify_tools.py** - Simple tool verification script

## Tools Tested

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

### 🎯 Run Jobs Tool (`run-jobs`)

**Purpose**: Execute any specific stage of a TMF ODA transformation journey with flexible parameters.

**Tests Cover**:
- ✅ Successful job execution for multiple stage types
- ✅ Generic stage execution (raw_analysis, stripped_schema, custom stages)
- ✅ Parameter validation and default value handling
- ✅ Error handling for job startup and execution failures
- ✅ AWS role ARN configuration support
- ✅ Timing measurement and performance tracking
- ✅ Job ID format validation and result message formatting
- ✅ Concurrent execution simulation
- ✅ Custom stage support and error debugging

**Test Cases**: 18+ comprehensive test scenarios

### 📊 Journeys Tool (`journeys`)

**Purpose**: Comprehensive journey management with full CRUD operations.

**Tests Cover**:
- ✅ Journey creation and management
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Stage information retrieval
- ✅ Job history tracking
- ✅ Status and progress monitoring
- ✅ Comprehensive error handling
- ✅ Data validation and sanitization

**Test Cases**: 20+ comprehensive test scenarios

### 🧪 Test Runner Tool (`test-runner`)

**Purpose**: Run comprehensive verification tests for all TMF ODA transformer tools.

**Tests Cover**:
- ✅ Tool import verification
- ✅ Parameter validation testing
- ✅ Error handling verification
- ✅ Integration testing
- ✅ Performance validation
- ✅ Comprehensive reporting

**Test Cases**: 15+ comprehensive test scenarios

## Test Features

### Mocking and Fixtures

- **AWS Services**: Mock S3, EC2, IAM for safe testing
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
python -m pytest tests/test_raw_analysis.py -v
python -m pytest tests/test_stripped_schema.py -v
python -m pytest tests/test_get_job_logs.py -v
python -m pytest tests/test_run_jobs.py -v
python -m pytest tests/test_journeys.py -v
python -m pytest tests/test_test_runner.py -v

# Test specific scenarios
python -m pytest tests/test_raw_analysis.py::TestRawAnalysis::test_raw_analysis_success -v
```

## Test Results

The test suite verifies **90+ individual test cases** covering:

### Functionality Verification ✅

- **Job Execution**: Multi-stage transformation pipeline execution
- **Journey Management**: Full CRUD operations with status tracking
- **AWS Integration**: S3 log retrieval, IAM role assumption, resource management
- **Error Handling**: Comprehensive error scenarios and recovery mechanisms
- **Performance**: Timing measurement and resource usage validation
- **Security**: Input validation, sanitization, and secure credential handling

### Core Components Tested ✅

- **Transformation Pipeline**: Raw analysis → Stripped schema → Custom stages
- **Job Management**: Execution, monitoring, logging, and status tracking
- **Journey Lifecycle**: Creation, execution, monitoring, and completion
- **AWS Services**: S3 integration, IAM authentication, resource management
- **Validation**: Input validation, parameter checking, and error handling
- **Reporting**: Comprehensive result formatting and status reporting

### Integration Testing ✅

- **Tool Interaction**: Multi-tool workflow execution
- **AWS Services**: Real AWS service integration (mocked for testing)
- **Error Propagation**: Proper error handling across tool boundaries
- **State Management**: Journey state consistency and persistence
- **Performance**: Resource usage and timing validation

## Quality Assurance

### Code Coverage

The test suite provides comprehensive coverage of:

- **✅ Core Tool Functions**: All 6 tools fully tested
- **✅ Error Handling**: All error scenarios covered
- **✅ Input Validation**: All parameter validation paths tested
- **✅ Integration Points**: All AWS service interactions tested
- **✅ Edge Cases**: Boundary conditions and unusual scenarios

### Test Categories

1. **Unit Tests**: Individual tool functionality
2. **Integration Tests**: Multi-tool workflows
3. **Error Tests**: Comprehensive error handling
4. **Performance Tests**: Timing and resource usage
5. **Security Tests**: Input validation and sanitization
6. **Regression Tests**: Prevent functionality breakage

### Test Execution

The tests are designed to:

- **Run Independently**: Each test is self-contained
- **Mock External Dependencies**: Safe testing without real AWS resources
- **Provide Clear Feedback**: Detailed success/failure reporting
- **Execute Quickly**: Efficient test execution for rapid development
- **Scale Appropriately**: Handle both small and large test suites

## Maintenance

### Adding New Tests

When adding new tests, follow these guidelines:

1. **Test Structure**: Use the existing test patterns and fixtures
2. **Mocking**: Mock external dependencies appropriately
3. **Documentation**: Document test purpose and expected behavior
4. **Coverage**: Ensure comprehensive coverage of new functionality
5. **Integration**: Test integration with existing tools and workflows

### Test Data

- **Fixtures**: Use the shared fixtures in `conftest.py`
- **Mock Data**: Create realistic mock data for testing
- **Test Scenarios**: Cover both success and failure cases
- **Edge Cases**: Test boundary conditions and unusual inputs

The test suite ensures the TMF ODA Transformer MCP Server is reliable, secure, and ready for production use. 