# Call Analysis MCP Server - Test Suite

## Overview

This directory contains comprehensive tests for the Call Analysis MCP Server, covering all components from data models to end-to-end integration testing.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                    # Pytest configuration
├── README.md                     # This file
├── test_models.py                # Data model tests
├── test_transcript_analyzer.py   # Transcript analysis service tests
├── test_business_intelligence.py # Business intelligence service tests
├── test_ai_analyzer.py           # AI analyzer service tests
├── test_mcp_tools.py             # MCP tools tests
├── test_s3_service.py            # S3 service tests
├── test_http_server.py           # HTTP server endpoint tests
└── test_integration.py           # End-to-end integration tests
```

## Test Categories

### Unit Tests (Fast)
- **test_models.py**: Tests Pydantic models, enums, validation
- **test_transcript_analyzer.py**: Tests transcript parsing, sentiment analysis, KPIs
- **test_business_intelligence.py**: Tests risk assessment, churn prediction, opportunities
- **test_ai_analyzer.py**: Tests OpenAI integration and fallback mechanisms
- **test_s3_service.py**: Tests S3 operations with mocked AWS services

### Integration Tests (Medium)
- **test_mcp_tools.py**: Tests MCP tool implementations and protocol compliance
- **test_http_server.py**: Tests FastAPI HTTP server endpoints

### End-to-End Tests (Slow)
- **test_integration.py**: Tests complete workflows from input to output

## Running Tests

### Install Dependencies
```bash
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout

# Install project dependencies
pip install -r requirements.txt
```

### Run All Tests
```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=awslabs.call_analysis_mcp_server --cov-report=html
```

### Run Specific Test Categories
```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests that don't require external services
pytest -m "not ai and not s3"

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestTranscriptEvidence::test_valid_transcript_evidence
```

### Run Tests with Different Verbosity
```bash
# Minimal output
pytest -q

# Verbose output
pytest -v

# Very verbose output
pytest -vv

# Show test durations
pytest --durations=10
```

## Test Markers

Tests are marked with the following categories:

- `@pytest.mark.unit`: Fast, isolated unit tests
- `@pytest.mark.integration`: Integration tests that may be slower
- `@pytest.mark.ai`: Tests requiring OpenAI API (set OPENAI_API_KEY)
- `@pytest.mark.s3`: Tests requiring AWS S3 (set AWS credentials)
- `@pytest.mark.slow`: Tests that take significant time
- `@pytest.mark.performance`: Performance-specific tests

## Environment Setup

### Required Environment Variables
```bash
# For AI tests (optional)
export OPENAI_API_KEY="your-openai-api-key"

# For S3 tests (optional, tests use mocks by default)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# For testing
export TESTING="true"
export LOG_LEVEL="DEBUG"
```

### Mock vs Real Services

By default, tests use mocked external services:
- S3 operations are mocked using `unittest.mock`
- OpenAI API calls are mocked
- AWS credentials are not required for standard test runs

To run tests against real services:
```bash
# Run with real S3 (requires AWS credentials)
pytest -m s3 --real-s3

# Run with real OpenAI (requires API key)
pytest -m ai --real-ai
```

## Test Data

### Fixtures Available
- `sample_transcript_content`: Standard JSON transcript
- `sample_transcript_segments`: Parsed transcript segments
- `sample_call_analysis_result`: Complete analysis result
- `mock_s3_environment`: Mocked S3 client and environment
- `mock_openai_environment`: Mocked OpenAI client
- `temp_directory`: Temporary directory for file operations

### Test Data Factory
Use `TestDataFactory` to create custom test data:
```python
def test_custom_transcript(test_data_factory):
    segments = test_data_factory.create_transcript_segments(count=10)
    business_transcript = test_data_factory.create_business_transcript()
```

## Writing New Tests

### Test File Structure
```python
"""
Brief description of what this test module covers.
"""

import pytest
from unittest.mock import Mock, patch
# ... other imports

class TestComponentName:
    """Test a specific component or functionality."""
    
    def test_specific_feature(self, fixture_name):
        """Test a specific feature with descriptive name."""
        # Arrange
        # Act
        # Assert
        pass
    
    @pytest.mark.asyncio
    async def test_async_feature(self):
        """Test async functionality."""
        # Use async/await
        pass
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "expected1"),
        ("input2", "expected2"),
    ])
    def test_parametrized_feature(self, input, expected):
        """Test with multiple input/output combinations."""
        pass
```

### Best Practices

1. **Descriptive Names**: Use clear, descriptive test names
2. **AAA Pattern**: Arrange, Act, Assert
3. **Single Responsibility**: Each test should test one thing
4. **Independent Tests**: Tests should not depend on each other
5. **Use Fixtures**: Leverage shared fixtures for common setup
6. **Mock External Services**: Mock S3, OpenAI, etc. by default
7. **Test Edge Cases**: Include error conditions and edge cases
8. **Performance Considerations**: Mark slow tests appropriately

### Example Test
```python
class TestTranscriptAnalyzer:
    """Test transcript analysis functionality."""
    
    def test_parse_json_transcript(self, sample_transcript_content):
        """Test parsing a valid JSON transcript."""
        # Arrange
        analyzer = TranscriptAnalyzer()
        
        # Act
        segments = analyzer.parse_transcript(sample_transcript_content)
        
        # Assert
        assert len(segments) == 4
        assert segments[0].speaker == CallParticipant.AGENT
        assert "help you today" in segments[0].text
    
    @pytest.mark.asyncio
    async def test_analyze_transcript_with_options(self, sample_transcript_segments):
        """Test transcript analysis with specific options."""
        # Arrange
        analyzer = TranscriptAnalyzer()
        options = {"sentiment_analysis": True, "performance_metrics": True}
        
        # Act
        result = await analyzer.analyze_transcript(
            transcript_segments=sample_transcript_segments,
            call_id="TEST_001",
            analysis_options=options
        )
        
        # Assert
        assert isinstance(result, CallAnalysisResult)
        assert result.call_id == "TEST_001"
        assert result.sentiment_analysis is not None
        assert result.performance_kpis is not None
```

## Coverage Requirements

- **Minimum Coverage**: 80% overall
- **Critical Components**: 90%+ coverage for core services
- **Models**: 95%+ coverage for data models
- **Integration**: Focus on happy path and major error cases

## Continuous Integration

Tests are designed to run in CI/CD environments:
- No external dependencies by default
- Fast execution (most tests < 1 second)
- Clear pass/fail criteria
- Comprehensive error reporting

## Debugging Tests

### Running Individual Tests
```bash
# Run with pdb debugger
pytest --pdb tests/test_models.py::TestTranscriptEvidence::test_confidence_score_validation

# Run with print statements visible
pytest -s tests/test_transcript_analyzer.py

# Run with full traceback
pytest --tb=long
```

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Missing Dependencies**: Install test requirements
3. **Async Issues**: Use `@pytest.mark.asyncio` for async tests
4. **Mock Issues**: Check that patches are applied correctly
5. **Fixture Scope**: Understand fixture scopes (function, class, module, session)

## Performance Testing

Performance tests are included but marked separately:
```bash
# Run performance tests
pytest -m performance

# Run with memory profiling
pytest --profile tests/test_integration.py
```

## Contributing

When adding new functionality:
1. Write tests first (TDD approach)
2. Ensure good coverage of new code
3. Add appropriate markers
4. Update this README if needed
5. Run full test suite before submitting

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Pydantic Testing](https://pydantic-docs.helpmanual.io/usage/testing/)