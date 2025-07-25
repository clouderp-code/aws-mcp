# Call Analysis MCP HTTP Server

This HTTP server exposes the Call Analysis MCP server functionality via REST API and MCP HTTP transport protocol, following the same pattern as the TMF MCP HTTP server.

## 🚀 Starting the Server

### Basic Usage
```bash
cd /opt/mycode/aws-mcp/src/call-analysis-mcp-server
python mcp_http_server.py
```

### With Options
```bash
# Custom port
python mcp_http_server.py --port 8080

# Debug mode  
python mcp_http_server.py --debug

# Custom host and port
python mcp_http_server.py --host 127.0.0.1 --port 8080
```

**Default Configuration:**
- Host: `0.0.0.0` (all interfaces)
- Port: `8001` (different from TMF server on 8000)
- Log Level: `INFO` (use `--debug` for `DEBUG`)

## 📡 API Endpoints

### Health & Info Endpoints
- `GET /` - Server information and status
- `GET /health` - Health check endpoint
- `GET /tools` - List all available tools with schemas

### REST API Endpoints
- `POST /tools/{tool_name}` - Call specific tool directly via REST

### MCP Protocol Endpoints
- `POST /mcp/server/initialize` - Initialize MCP session (legacy)
- `POST /mcp/server/ping` - Ping server (legacy)
- `POST /mcp/tools/list` - List tools (legacy MCP format)
- `POST /mcp/tools/call` - Call tool (legacy MCP format)

### Unified MCP Endpoints (for LangGraph)
- `POST /mcp/request` - Unified MCP request endpoint (handles all MCP methods)
- `POST /mcp/notification` - MCP notification endpoint

## 🔧 Available Tools

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `analyze-transcript` | Analyze single call transcript from S3 | `s3_bucket`, `s3_key`, `output_bucket` |
| `analyze-transcript-batch` | Batch analysis of multiple transcripts | `s3_bucket`, `s3_prefix`, `output_bucket` |
| `generate-business-intelligence` | Generate management insights | `analysis_s3_urls`, `output_bucket` |
| `analyze-local-scripts` | Analyze local script files | `scripts_folder`, `script_pattern` |
| `ask-analysis-question` | Q&A with evidence-backed answers | `question`, `context_type` |
| `read-s3-transcript` | Read transcript files from S3 | `s3_bucket`, `s3_key` |
| `upload-to-s3` | Upload analysis results to S3 | `content`, `s3_bucket`, `s3_key` |
| `generate-report` | Generate markdown reports | `analysis_result`, `report_type` |
| `create-dashboard` | Create interactive dashboards | `analysis_data`, `dashboard_title` |

## 💬 Using the Q&A Tool

### REST API Example
```bash
curl -X POST http://localhost:8001/tools/ask-analysis-question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How was the overall quality of today'\''s calls?",
    "context_type": "quality"
  }'
```

### MCP Protocol Example (Legacy)
```bash
curl -X POST http://localhost:8001/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "ask-analysis-question",
      "arguments": {
        "question": "Are there any deals at risk?",
        "context_type": "deals"
      }
    }
  }'
```

### Unified MCP Protocol Example (for LangGraph)
```bash
curl -X POST http://localhost:8001/mcp/request \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "ask-analysis-question",
      "arguments": {
        "question": "Are there any deals at risk?",
        "context_type": "deals"
      }
    }
  }'
```

### Sample Questions
- **Quality**: "How was the overall quality of today's calls?"
- **Deal Risk**: "Were there any deals at risk based on today's conversations?"
- **Churn Risk**: "Are there churn risks in today's inbound calls?"
- **Opportunities**: "Any probable new opportunities from today's calls?"
- **Training**: "Which reps need training based on recent call behavior?"
- **Pipeline**: "Show me pipeline health based on this week's calls"

## 📊 Response Format

### Q&A Tool Response
```json
{
  "status": "success",
  "question": "How was the overall quality of today's calls?",
  "answer": "**Call Quality Analysis:** ...",
  "key_metrics": {
    "quality_score": 3.7,
    "evidence_items": 15
  },
  "evidence": [
    {
      "account": "Zenith Corp",
      "call_id": "CHR-2025-001",
      "speaker": "customer",
      "timestamp": 6.5,
      "quote": "We've had three outages this month...",
      "context": "Indicates dissatisfaction...",
      "confidence": 0.8
    }
  ],
  "insights": ["Quality score is below acceptable threshold"],
  "recommendations": ["Immediate intervention required"]
}
```

## 🔍 Testing the Server

### Check if Server is Running
```bash
curl http://localhost:8001/health
```

### List Available Tools
```bash
curl http://localhost:8001/tools
```

### Test Q&A Functionality
```bash
curl -X POST http://localhost:8001/tools/ask-analysis-question \
  -H "Content-Type: application/json" \
  -d '{"question": "How many calls were analyzed?"}'
```

## 📝 Logging

Logs are saved to `logs/` directory:
- `server_YYYY-MM-DD.log` - Server operations log
- `uvicorn.log` - HTTP server access log

## 🔄 Comparison with TMF Server

| Feature | TMF Server | Call Analysis Server |
|---------|------------|---------------------|
| **Port** | 8000 | 8001 |
| **Focus** | TMF ODA Transformation | AI Call Analysis |
| **Tools** | 6 transformation tools | 9 analysis tools |
| **Main Use** | Schema transformation | Business intelligence |
| **Evidence** | No | Yes (with customer quotes) |

## 🚀 Integration Examples

### Python Client
```python
import aiohttp
import asyncio

async def ask_question(question: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8001/tools/ask-analysis-question',
            json={'question': question}
        ) as response:
            return await response.json()

# Usage
result = asyncio.run(ask_question("How was call quality today?"))
print(result['result']['answer'])
```

### JavaScript/Node.js Client
```javascript
const axios = require('axios');

async function askQuestion(question) {
    const response = await axios.post(
        'http://localhost:8001/tools/ask-analysis-question',
        { question }
    );
    return response.data;
}

// Usage
askQuestion("Are there any deals at risk?")
    .then(result => console.log(result.result.answer));
```

## 🎯 Use Cases

1. **Management Dashboard**: Real-time Q&A about call performance
2. **Automated Reports**: Scheduled queries for daily/weekly insights  
3. **Alert Systems**: Monitor for deal risks and churn indicators
4. **Training Tools**: Identify coaching opportunities
5. **API Integration**: Embed call insights into existing systems

## 🔧 Troubleshooting

### Server Won't Start
- Check port 8001 is available: `lsof -i :8001`
- Verify Python environment: `python --version`
- Check imports: `python -c "import uvicorn, fastapi"`

### Tool Errors
- Ensure analysis reports exist for Q&A tools
- Check AWS credentials for S3 tools
- Verify file paths for local script analysis

### Performance Tips
- Use batch endpoints for multiple files
- Enable caching for repeated Q&A queries
- Monitor memory usage with large datasets 