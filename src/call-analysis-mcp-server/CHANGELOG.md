# Changelog

All notable changes to the Call Analysis MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-XX

### Added
- Initial release of Call Analysis MCP Server
- Core transcript analysis functionality
- S3 integration for reading and writing files
- Comprehensive sentiment analysis using multiple approaches
- Performance KPI calculation and scoring
- Compliance monitoring and verification
- Conversation flow analysis
- Topic extraction and categorization
- Batch processing capabilities for multiple transcripts
- Interactive HTML dashboard generation
- Support for multiple transcript formats (JSON, CSV, TSV, plain text)
- Automated report generation in JSON and Markdown formats
- AWS credential integration with multiple authentication methods
- Comprehensive error handling and logging
- Modular architecture with separate services for different functionality

### Features
- **analyze_transcript**: Single call transcript analysis with full KPIs
- **analyze_transcript_batch**: Batch processing of multiple transcripts
- **list_s3_transcripts**: S3 file discovery and metadata retrieval  
- **upload_analysis_results**: Direct content upload to S3
- **generate_analysis_report**: Multi-format report generation
- **create_analysis_dashboard**: Interactive HTML dashboard creation

### Technical
- Built on Model Context Protocol (MCP) framework
- Pydantic models for type safety and validation
- Boto3 integration for AWS S3 operations
- Loguru for comprehensive logging
- FastMCP for server implementation
- Support for Python 3.10+

### Documentation
- Comprehensive README with usage examples
- API documentation in docstrings
- Installation and configuration guides
- Troubleshooting section
- Security considerations

[Unreleased]: https://github.com/awslabs/mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/awslabs/mcp/releases/tag/v0.1.0 