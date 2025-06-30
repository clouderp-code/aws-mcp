# TMF ODA Transformer MCP Server

An AWS Labs Model Context Protocol (MCP) server that provides tools for analyzing and transforming data structures for TMF ODA (TM Forum Open Digital Architecture) compliance.

## Overview

This MCP server provides specialized tools to analyze schema files and databases to determine their compatibility and transformation requirements for TMF ODA standards. It helps developers understand how their current data structures align with TMF Open Digital Architecture specifications.

## Features

- **Schema Analysis**: Discover and analyze schema files (JSON Schema, OpenAPI, etc.) for TMF ODA transformation
- **Database Analysis**: Analyze database structures and suggest TMF ODA-compliant transformations  
- **Transformation Recommendations**: Provide actionable insights for TMF ODA compliance
- **Multi-format Support**: Support for various schema and database formats

## Tools

### schema-analyzer
Discovers schema files in a workspace and analyzes them for TMF ODA transformation requirements.

**Parameters:**
- `workspace_dir`: Directory path to analyze for schema files
- `schema_format`: Optional filter for specific schema formats (json-schema, openapi, avro, etc.)
- `oda_component_type`: Target TMF ODA component type for analysis

**Returns:** Analysis report with transformation recommendations and compliance assessment.

### db-analyzer  
Connects to and analyzes database structures for TMF ODA transformation requirements.

**Parameters:**
- `connection_string`: Database connection string or configuration
- `database_type`: Type of database (postgresql, mysql, mongodb, etc.)
- `tables_filter`: Optional filter for specific tables/collections to analyze
- `oda_component_type`: Target TMF ODA component type for analysis

**Returns:** Database analysis report with schema mapping recommendations and transformation steps.

## Installation

### Using uvx (recommended)
```bash
uvx awslabs.tmf-oda-transformer-mcp-server@latest
```

### Using pip
```bash
pip install awslabs.tmf-oda-transformer-mcp-server
```

## Configuration

### Basic Configuration
```json
{
  "mcpServers": {
    "awslabs.tmf-oda-transformer-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.tmf-oda-transformer-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Advanced Configuration with Database Support
```json
{
  "mcpServers": {
    "awslabs.tmf-oda-transformer-mcp-server": {
      "command": "uvx", 
      "args": ["awslabs.tmf-oda-transformer-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO",
        "TMF_ODA_REFERENCE_PATH": "/path/to/tmf-oda-references"
      }
    }
  }
}
```

## Environment Variables

- `AWS_PROFILE`: AWS profile for accessing AWS databases (optional)
- `AWS_REGION`: AWS region for database connections (optional)  
- `TMF_ODA_REFERENCE_PATH`: Path to TMF ODA reference schemas (optional)
- `FASTMCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Usage Examples

### Analyze Schema Files
```
Please use the schema-analyzer tool to analyze all JSON schemas in my current workspace for TMF ODA Product Catalog transformation.
```

### Analyze Database Structure  
```
Use the db-analyzer to analyze my PostgreSQL database at connection string "postgresql://user:pass@localhost:5432/mydb" for TMF ODA Customer Management compatibility.
```

## TMF ODA Component Types

The server supports analysis for various TMF ODA component types:
- Product Catalog Management
- Customer Management  
- Order Management
- Service Inventory Management
- Resource Inventory Management
- Party Management
- Account Management
- Billing Management

## Security

- Database connections are established securely with proper credential handling
- Schema file analysis is performed in read-only mode
- No sensitive data is logged or transmitted
- Follows AWS security best practices for credential management

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details. 