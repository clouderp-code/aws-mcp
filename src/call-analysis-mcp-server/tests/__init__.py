"""
Call Analysis MCP Server Test Suite

This package contains comprehensive tests for all components of the
Call Analysis MCP Server, including unit tests, integration tests,
and end-to-end workflow testing.

Test Categories:
- Unit Tests: Fast, isolated tests for individual components
- Integration Tests: Tests for component interactions
- End-to-End Tests: Complete workflow testing

Usage:
    # Run all tests
    pytest

    # Run specific category
    pytest -m unit
    pytest -m integration
    
    # Run with coverage
    pytest --cov=awslabs.call_analysis_mcp_server
"""

__version__ = "1.0.0"
__author__ = "AWS Labs"