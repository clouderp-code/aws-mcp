# TMF ODA Transformer MCP Server - Tool Testing Scripts

This directory contains comprehensive shell scripts for testing and documenting all MCP (Model Context Protocol) tools available in the TMF ODA Transformer server.

## 📋 Available Scripts

### 🔍 Tool Discovery & Listing

#### `list_all_tools.sh`
**Purpose**: Lists all available MCP tools with their basic information and status
**Features**:
- Server health checks
- Tool endpoint discovery 
- Accessibility testing
- Tool categorization
- API documentation generation

**Usage**:
```bash
./list_all_tools.sh                          # Local server (localhost:8000)
./list_all_tools.sh -h 192.168.1.100 -p 9000  # Remote server
./list_all_tools.sh --host example.com --port 8080  # Remote server with long options
```

**Output**:
- Complete list of 7 MCP tools
- Tool descriptions and endpoints
- Availability status for each tool
- Quick API reference

---

### 📖 Detailed Tool Information

#### `get_tool_details.sh`
**Purpose**: Get detailed information for specific MCP tools
**Features**:
- Tool-specific parameter documentation
- Request/response examples
- Endpoint testing
- Usage guidelines

**Usage**:
```bash
./get_tool_details.sh [tool-name]               # Local server
./get_tool_details.sh raw-analysis              # Specific tool on local server
./get_tool_details.sh all                       # All tools on local server
./get_tool_details.sh -h remote-host -p 8080 journeys  # Specific tool on remote server
./get_tool_details.sh --host example.com --port 9000 all  # All tools on remote server
```

**Available Tools**:
- `raw-analysis` - Execute raw analysis stage
- `stripped-schema` - Execute schema stripping stage
- `run-jobs` - Execute any transformation stage
- `journeys` - Journey lifecycle management
- `get-job-logs` - Retrieve execution logs (legacy)
- `logs-and-reports` - Enhanced logs and reports
- `test-runner` - Validation testing
- `all` - Show details for all tools

---

### 📋 Parameter Reference

#### `show_tool_parameters.sh`
**Purpose**: Shows detailed parameter information for all MCP tools
**Features**:
- Complete parameter documentation
- Data type specifications
- Required vs optional parameters
- Validation rules
- JSON payload examples

**Usage**:
```bash
./show_tool_parameters.sh                       # Local server (localhost:8000)
./show_tool_parameters.sh -h 192.168.1.100     # Remote server (default port 8000)
./show_tool_parameters.sh --host example.com --port 3000  # Remote server with custom port
```

**Output**:
- Parameter details for all 7 tools
- Quick reference guide
- Validation guidelines
- Copy-paste examples

---

### 🧪 Comprehensive Testing

#### `test_tool_availability.sh`
**Purpose**: Comprehensive testing of all MCP tools
**Features**:
- Server connectivity tests
- Tool endpoint functionality
- Parameter validation
- Response format validation
- Integration testing
- Error handling tests
- Performance metrics
- Detailed test reporting

**Usage**:
```bash
./test_tool_availability.sh                     # Local server (localhost:8000)
./test_tool_availability.sh -h 10.0.0.50        # Remote server (default port 8000)
./test_tool_availability.sh --host staging.company.com --port 8080  # Remote staging server
```

**Test Categories**:
1. **Server Connectivity** - Basic server health and endpoint availability
2. **Tool Functionality** - Individual tool testing (OPTIONS, POST, JSON handling)
3. **Parameter Validation** - Required parameter checking and format validation
4. **Response Format** - JSON structure and status field validation
5. **Integration Scenarios** - Cross-tool functionality testing
6. **Error Handling** - 404s, invalid methods, timeouts
7. **Performance** - Response time measurements

---

## 🚀 Quick Start Guide

### 1. Check Server Status
```bash
# Local server
./list_all_tools.sh

# Remote server
./list_all_tools.sh -h your-server.com -p 8080
```

### 2. Get Tool Overview
```bash
# Local server - see all available tools and their status
./list_all_tools.sh

# Remote server - check tools on production/staging
./list_all_tools.sh --host prod-server.company.com --port 8000
```

### 3. Get Specific Tool Information
```bash
# Local server - get detailed info for a specific tool
./get_tool_details.sh raw-analysis

# Remote server - get tool info from remote environment
./get_tool_details.sh -h staging.company.com -p 8080 journeys
```

### 4. View Parameters Reference
```bash
# Local server - see parameter documentation for all tools
./show_tool_parameters.sh

# Remote server - check parameters on remote server
./show_tool_parameters.sh --host example.com --port 3000
```

### 5. Run Comprehensive Tests
```bash
# Local server - test all tools comprehensively
./test_tool_availability.sh

# Remote server - run full test suite on remote environment
./test_tool_availability.sh -h prod-server.company.com -p 8000
```

---

## 🔧 TMF ODA Transformer MCP Tools

### Execution Tools
- **`raw-analysis`** - Execute raw analysis stage of TMF ODA transformation
- **`stripped-schema`** - Execute schema stripping stage
- **`run-jobs`** - Execute any transformation stage

### Management Tools
- **`journeys`** - Comprehensive journey lifecycle management (CRUD, stages, jobs)

### Utility Tools
- **`get-job-logs`** - Retrieve detailed execution logs (legacy compatibility)
- **`logs-and-reports`** - Enhanced logs and reports management
- **`test-runner`** - Comprehensive tool validation testing

---

## 📊 Server Configuration

**Default Settings**:
- Server URL: `http://localhost:8000`
- Tools Endpoint: `http://localhost:8000/tools`

**Starting the Server**:
```bash
python -m awslabs.tmf_oda_transformer_mcp_server.mcp_http_server
```

---

## 🌐 Remote Execution Support

All scripts now support connecting to remote MCP servers using host and port parameters.

### Command Line Options

Each script accepts the following options:
- `-h, --host HOST` - MCP server host (default: localhost)
- `-p, --port PORT` - MCP server port (default: 8000)
- `--help` - Show usage information

### Remote Execution Examples

#### Basic Remote Connection
```bash
# Connect to remote server on different host
./list_all_tools.sh -h 192.168.1.100 -p 9000
./get_tool_details.sh --host example.com --port 8080
./show_tool_parameters.sh -h remote-server.local -p 3000
./test_tool_availability.sh --host 10.0.0.50 --port 8000
```

#### Specific Tool Details on Remote Server
```bash
# Get details for specific tools on remote servers
./get_tool_details.sh -h 192.168.1.100 -p 9000 journeys
./get_tool_details.sh --host example.com --port 8080 raw-analysis
```

#### Production Environment Testing
```bash
# Test production server
./test_tool_availability.sh --host prod-server.company.com --port 443

# Test staging environment
./list_all_tools.sh -h staging-env.company.com -p 8080
```

### Usage Help
```bash
# Get help for any script
./list_all_tools.sh --help
./get_tool_details.sh --help
./show_tool_parameters.sh --help
./test_tool_availability.sh --help
```

### Remote Connection Benefits
- **Development**: Test against different environments
- **CI/CD**: Integrate with automated testing pipelines
- **Debugging**: Troubleshoot remote deployments
- **Monitoring**: Health check remote MCP servers
- **Multi-environment**: Test staging, production, and development servers

---

## 🛠️ Prerequisites

### Required Tools
- `curl` - For HTTP requests
- `jq` - For JSON parsing
- `bash` - Shell environment

### Installation (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install curl jq
```

### Installation (macOS)
```bash
brew install curl jq
```

---

## 📚 Example Usage Scenarios

### Scenario 1: New Developer Setup
```bash
# 1. Check if server is running and tools are available
./list_all_tools.sh

# 2. Get familiar with available tools
./get_tool_details.sh all

# 3. Run quick tests to verify everything works
./test_tool_availability.sh
```

### Scenario 2: Debugging Tool Issues
```bash
# 1. Test specific tool that's having issues
./get_tool_details.sh journeys

# 2. Check parameter requirements
./show_tool_parameters.sh

# 3. Run comprehensive tests
./test_tool_availability.sh
```

### Scenario 3: Integration Testing
```bash
# 1. Verify all tools are accessible
./list_all_tools.sh

# 2. Run full test suite before deployment
./test_tool_availability.sh
```

---

## 🔍 Troubleshooting

### Common Issues

#### Server Not Running
```bash
# Error: MCP server is not accessible
# Solution: Start the server
python -m awslabs.tmf_oda_transformer_mcp_server.mcp_http_server
```

#### Tools Not Accessible
```bash
# Check server status first
curl -s http://localhost:8000

# Verify tools endpoint
curl -s http://localhost:8000/tools
```

#### Permission Issues
```bash
# Make scripts executable
chmod +x *.sh
```

### Debug Commands
```bash
# Test specific tool manually
curl -X POST http://localhost:8000/tools/raw-analysis \
  -H 'Content-Type: application/json' \
  -d '{"journey_id": "TEST-001"}'

# Check server logs
# (Refer to your server startup logs)
```

---

## 📊 Test Results Interpretation

### Success Rates
- **90%+**: Excellent - Ready for production
- **70-89%**: Good - Minor issues to address
- **<70%**: Critical issues - Requires investigation

### Common Test Failures
1. **Connectivity Issues** - Server not running or network problems
2. **Parameter Validation** - Missing required parameters
3. **Response Format** - JSON structure issues
4. **Performance** - Slow response times (>5 seconds)

---

## 🔄 Script Maintenance

### Updating Server URL
Edit the configuration section in each script:
```bash
SERVER_URL="http://your-server:port"
TOOLS_ENDPOINT="$SERVER_URL/tools"
```

### Adding New Tools
When new tools are added to the MCP server:
1. Update tool lists in all scripts
2. Add tool-specific parameter documentation
3. Add test cases for new tools

---

## 📞 Support

For issues with these testing scripts:
1. Check server logs for detailed error information
2. Verify all prerequisites are installed
3. Ensure MCP server is running and accessible
4. Review the troubleshooting section above

For TMF ODA Transformer specific issues:
- Refer to the main project documentation
- Check server configuration and AWS credentials
- Review journey and job management guides

---

## ✅ Script Summary

| Script | Purpose | Output | Time |
|--------|---------|--------|------|
| `list_all_tools.sh` | Tool discovery & overview | Tool list with status | ~30s |
| `get_tool_details.sh` | Detailed tool documentation | Comprehensive tool info | ~10s |
| `show_tool_parameters.sh` | Parameter reference | Complete parameter docs | ~5s |
| `test_tool_availability.sh` | Comprehensive testing | Full test report | ~2-5min |

**Total Testing Time**: ~3-6 minutes for complete MCP server validation

All scripts are designed to be:
- ✅ **Self-contained** - No external dependencies beyond curl/jq
- ✅ **Error-resilient** - Handle server issues gracefully
- ✅ **Informative** - Provide clear, actionable output
- ✅ **Fast** - Complete testing in under 5 minutes 