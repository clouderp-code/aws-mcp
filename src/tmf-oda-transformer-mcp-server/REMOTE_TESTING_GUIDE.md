# Remote Testing Guide for TMF ODA MCP Server

This guide explains how to test the TMF ODA MCP Server from another machine using the updated `test-external-access.py` script.

## 🌐 Overview

The test script now supports both local and remote Docker connections:
- **Local mode**: Tests Docker container on the same machine
- **Remote mode**: Tests Docker container on a remote machine via SSH

## 🔧 Prerequisites

### On the Target Machine (where Docker is running)
1. **Docker container running**: `tmf-oda-mcp-server` container must be running
2. **Port 8000 exposed**: Container should expose port 8000 (already configured)
3. **SSH server running**: SSH daemon must be running and accessible
4. **Network access**: SSH port (22 or custom) must be accessible from external machines

### On the Client Machine (where you run the test)
1. **Python 3.7+**: Required to run the test script
2. **SSH client**: `ssh` command must be available
3. **Network connectivity**: Must be able to reach the target machine

## 🚀 Usage Examples

### 1. Test Local Docker Container
```bash
python3 test-external-access.py
```

### 2. Test Remote Docker Container (Basic)
```bash
python3 test-external-access.py --host 18.191.87.212
```

### 3. Test Remote with Custom SSH Port
```bash
python3 test-external-access.py --host 18.191.87.212 --port 2222
```

### 4. Test Remote with Specific SSH User
```bash
python3 test-external-access.py --host 18.191.87.212 --user root
```

### 5. Test Remote with Custom Container Name
```bash
python3 test-external-access.py --host 18.191.87.212 --container my-tmf-container
```

### 6. Complete Remote Example
```bash
python3 test-external-access.py \
  --host 18.191.87.212 \
  --port 22 \
  --user root \
  --container tmf-oda-mcp-server
```

## 📋 Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--host` | Remote host IP or hostname | None (local mode) | `--host 192.168.1.100` |
| `--port` | SSH port for remote connection | 22 | `--port 2222` |
| `--user` | SSH username | Current user | `--user myuser` |
| `--container` | Docker container name | `tmf-oda-mcp-server` | `--container my-container` |

## 🔍 What the Script Tests

The script runs comprehensive tests including:

1. **Network Connectivity** (Remote mode only)
   - TCP connectivity test
   - SSH connection verification

2. **Container Status**
   - Docker container running check
   - Container communication test

3. **Python Environment**
   - Python version check
   - TMF ODA module imports
   - All 6 tools import verification

4. **Tool Validation**
   - Parameter validation for all 6 tools
   - Error handling verification

5. **Comprehensive Workflow**
   - Full test runner execution
   - Performance metrics collection

6. **Performance Metrics**
   - Import timing
   - Test execution timing

## 🌐 Example: Testing from Another Machine

### Step 1: Copy the test script to your machine
```bash
# Download or copy test-external-access.py to your local machine
wget https://your-server/test-external-access.py
# or
scp user@target-machine:/path/to/test-external-access.py .
```

### Step 2: Ensure SSH access
```bash
# Test SSH connection first
ssh root@18.191.87.212 "echo 'SSH connection works'"
```

### Step 3: Run the remote test
```bash
python3 test-external-access.py --host 18.191.87.212 --user root
```

## 📊 Expected Output

The script provides colored output showing:
- 🔗 Connection mode (Local/Remote)
- 🌐 Remote host information
- ✅ Successful tests (green)
- ❌ Failed tests (red)
- ⚠️ Warnings (yellow)
- 📊 Test statistics and performance metrics

Example output:
```
🚀 TMF ODA Transformer MCP Server - External Testing Suite
======================================================================
🕐 Started at: 2025-07-10 20:30:00

🔗 Connection mode: Remote
🌐 Remote host: 18.191.87.212:22
👤 SSH user: root

============================================================
🎯 Network Connectivity Test
============================================================
🔍 Testing connection to 18.191.87.212:22...
✅ Network connectivity OK
✅ SSH connection working

============================================================
🎯 Container Status Check
============================================================
✅ Container 'tmf-oda-mcp-server' is running
✅ Container communication working

[... continued test output ...]
```

## 🔧 Troubleshooting

### SSH Connection Issues
```bash
# Test SSH connectivity manually
ssh -v root@18.191.87.212

# Check SSH key authentication
ssh -i ~/.ssh/id_rsa root@18.191.87.212

# Test with password authentication
ssh -o PasswordAuthentication=yes root@18.191.87.212
```

### Docker Access Issues
```bash
# Verify Docker is running on remote host
ssh root@18.191.87.212 "docker ps"

# Check container status
ssh root@18.191.87.212 "docker ps -f name=tmf-oda-mcp-server"
```

### Network Issues
```bash
# Test port connectivity
telnet 18.191.87.212 22

# Test with specific port
nc -zv 18.191.87.212 22
```

### Firewall Issues
On the target machine, ensure SSH port is open:
```bash
# Check firewall status
sudo ufw status

# Allow SSH if needed
sudo ufw allow 22/tcp
```

## 🌐 REST API Integration

The script also provides examples for creating REST API wrappers:

```python
# Flask wrapper for HTTP access
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/tmf-oda/<tool_name>', methods=['POST'])
def call_tmf_tool(tool_name):
    try:
        parameters = request.json
        # Use remote connection for Docker commands
        result, error = call_tmf_oda_tool_remote(tool_name, parameters)
        
        if error:
            return jsonify({"error": error}), 500
        
        return jsonify({"result": json.loads(result)}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

## 📁 Results

The script saves detailed test results to a timestamped JSON file:
- **Local mode**: `external_test_results_local_YYYYMMDD_HHMMSS.json`
- **Remote mode**: `external_test_results_remote_YYYYMMDD_HHMMSS.json`

## 🎯 Success Criteria

A successful test run will show:
- ✅ All connectivity tests passed
- ✅ Container is running and accessible
- ✅ Python environment properly configured
- ✅ All 6 TMF ODA tools working correctly
- ✅ Validation and workflow tests passing

## 🔐 Security Considerations

1. **SSH Keys**: Use SSH key authentication instead of passwords
2. **Firewall**: Only open necessary ports (22 for SSH, 8000 for container)
3. **User Access**: Use dedicated service account instead of root when possible
4. **Network**: Consider VPN or private networks for production environments 