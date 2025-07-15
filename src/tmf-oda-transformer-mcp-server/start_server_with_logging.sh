#!/bin/bash

# Start MCP Server with Enhanced Logging

DEBUG_FLAG=""
if [ "$1" = "--debug" ]; then
    DEBUG_FLAG="--debug"
    echo "🔍 Debug mode enabled - detailed logging will be displayed"
fi

echo "🚀 Starting TMF ODA Transformer MCP Server with Enhanced Logging..."
echo "📁 Logs will be saved to: /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/logs/"
echo "📄 Log files: mcp_server_YYYY-MM-DD.log"
echo ""

# Create logs directory if it doesn't exist
mkdir -p /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/logs

# Change to the server directory
cd /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server

# Start the server with or without debug flag
if [ -n "$DEBUG_FLAG" ]; then
    echo "🔧 Starting server on port 8000 with debug logging..."
    python3 mcp_http_server.py $DEBUG_FLAG
else
    echo "🔧 Starting server on port 8000..."
    python3 mcp_http_server.py
fi

echo "✅ Server stopped." 