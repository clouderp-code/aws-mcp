#!/usr/bin/env python3
"""
Test script for Call Analysis MCP HTTP Server
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any

# Global variable for base URL (will be set based on detected port)
base_url = "http://localhost:8000"


async def test_server_endpoints():
    """Test the HTTP server endpoints."""
    
    global base_url
    
    print("🧪 Testing Call Analysis MCP HTTP Server")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data['status']}")
                    print(f"   Tools available: {data['tools_available']}")
                else:
                    print(f"❌ Health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 2: Server info
        print("\n2. Testing root endpoint...")
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Server info: {data['service']}")
                    print(f"   Version: {data['version']}")
                    print(f"   Tools count: {data['tools_count']}")
                else:
                    print(f"❌ Server info failed: {response.status}")
        except Exception as e:
            print(f"❌ Server info error: {e}")
        
        # Test 3: Tools list
        print("\n3. Testing tools list endpoint...")
        try:
            async with session.get(f"{base_url}/tools") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Tools list retrieved: {data['count']} tools")
                    for tool in data['tools'][:3]:  # Show first 3
                        print(f"   - {tool['name']}: {tool['description'][:60]}...")
                else:
                    print(f"❌ Tools list failed: {response.status}")
        except Exception as e:
            print(f"❌ Tools list error: {e}")
        
        # Test 4: MCP tools/list endpoint
        print("\n4. Testing MCP tools/list endpoint...")
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            async with session.post(f"{base_url}/mcp/tools/list", json=mcp_request) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    tools = result.get('tools', [])
                    print(f"✅ MCP tools list: {len(tools)} tools")
                    for tool in tools[:3]:  # Show first 3
                        print(f"   - {tool['name']}: {tool['description'][:60]}...")
                else:
                    print(f"❌ MCP tools list failed: {response.status}")
        except Exception as e:
            print(f"❌ MCP tools list error: {e}")
        
        # Test 5: Ask analysis question (if report exists)
        print("\n5. Testing Q&A functionality...")
        try:
            question_request = {
                "question": "How was the overall quality of today's calls?",
                "context_type": "quality"
            }
            async with session.post(f"{base_url}/tools/ask-analysis-question", json=question_request) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    if result.get('status') == 'success':
                        print(f"✅ Q&A test successful")
                        print(f"   Question: {result['question']}")
                        answer = result['answer'][:100] + "..." if len(result['answer']) > 100 else result['answer']
                        print(f"   Answer: {answer}")
                        print(f"   Evidence items: {len(result.get('evidence', []))}")
                    else:
                        print(f"🟡 Q&A test returned error: {result.get('error_message', 'Unknown error')}")
                else:
                    print(f"❌ Q&A test failed: {response.status}")
        except Exception as e:
            print(f"❌ Q&A test error: {e}")
        
        # Test 6: MCP tool call (legacy endpoint)
        print("\n6. Testing MCP tool call (legacy endpoint)...")
        try:
            mcp_tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "ask-analysis-question",
                    "arguments": {
                        "question": "Are there any deals at risk?",
                        "context_type": "deals"
                    }
                }
            }
            async with session.post(f"{base_url}/mcp/tools/call", json=mcp_tool_request) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        print(f"✅ MCP tool call successful")
                        content = data['result'].get('content', [])
                        if content:
                            result_text = content[0].get('text', '')
                            if len(result_text) > 200:
                                result_text = result_text[:200] + "..."
                            print(f"   Result preview: {result_text}")
                    else:
                        error = data.get('error', {})
                        print(f"🟡 MCP tool call returned error: {error.get('message', 'Unknown error')}")
                else:
                    print(f"❌ MCP tool call failed: {response.status}")
        except Exception as e:
            print(f"❌ MCP tool call error: {e}")
        
        # Test 7: Unified MCP request endpoint (for langgraph connector)
        print("\n7. Testing unified MCP request endpoint...")
        try:
            # Test tools/list via unified endpoint
            unified_list_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
                "params": {}
            }
            async with session.post(f"{base_url}/mcp/request", json=unified_list_request) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        tools = data['result'].get('tools', [])
                        print(f"✅ Unified MCP tools/list: {len(tools)} tools")
                    else:
                        error = data.get('error', {})
                        print(f"🟡 Unified MCP tools/list error: {error.get('message', 'Unknown error')}")
                else:
                    print(f"❌ Unified MCP tools/list failed: {response.status}")
        except Exception as e:
            print(f"❌ Unified MCP tools/list error: {e}")
        
        # Test 8: Unified MCP tool call
        print("\n8. Testing unified MCP tool call...")
        try:
            unified_call_request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "ask-analysis-question",
                    "arguments": {
                        "question": "Which reps need training?",
                        "context_type": "training"
                    }
                }
            }
            async with session.post(f"{base_url}/mcp/request", json=unified_call_request) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        print(f"✅ Unified MCP tool call successful")
                        content = data['result'].get('content', [])
                        if content:
                            result_text = content[0].get('text', '')
                            if len(result_text) > 150:
                                result_text = result_text[:150] + "..."
                            print(f"   Result preview: {result_text}")
                    else:
                        error = data.get('error', {})
                        print(f"🟡 Unified MCP tool call error: {error.get('message', 'Unknown error')}")
                else:
                    print(f"❌ Unified MCP tool call failed: {response.status}")
        except Exception as e:
            print(f"❌ Unified MCP tool call error: {e}")
        
        # Test 9: MCP notification endpoint
        print("\n9. Testing MCP notification endpoint...")
        try:
            notification_request = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            async with session.post(f"{base_url}/mcp/notification", json=notification_request) as response:
                if response.status == 200:
                    print(f"✅ MCP notification acknowledged")
                else:
                    print(f"❌ MCP notification failed: {response.status}")
        except Exception as e:
            print(f"❌ MCP notification error: {e}")
        
    print(f"\n✅ HTTP Server Testing Complete!")
    print(f"🌐 Server is running at: {base_url}")
    print(f"📖 API Documentation: {base_url}/docs")
    print(f"🔧 Available endpoints:")
    print(f"   - GET  /health - Health check")
    print(f"   - GET  /tools - List tools")
    print(f"   - POST /tools/{{tool_name}} - Call specific tool via REST")
    print(f"   - POST /mcp/tools/list - MCP tools list (legacy)")
    print(f"   - POST /mcp/tools/call - MCP tool call (legacy)")
    print(f"   - POST /mcp/request - Unified MCP request (for langgraph)")
    print(f"   - POST /mcp/notification - MCP notifications")


def check_server_running():
    """Check if the server is running."""
    import socket
    
    # Check both possible ports (8000 and 8001)
    for port in [8000, 8001]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                print(f"✅ Found server running on port {port}")
                return port
        except:
            continue
    return False


async def main():
    """Main test function."""
    
    print("🔍 Checking if Call Analysis MCP HTTP Server is running...")
    
    server_port = check_server_running()
    if not server_port:
        print("❌ Server is not running on port 8000 or 8001")
        print("🚀 Start the server first with:")
        print("   cd /opt/mycode/aws-mcp/src/call-analysis-mcp-server")
        print("   python mcp_http_server.py --port 8000")
        print("   # or on default port 8001:")
        print("   python mcp_http_server.py")
        return
    
    print("✅ Server is running, starting tests...")
    
    # Update base_url to use detected port
    import asyncio
    global base_url
    base_url = f"http://localhost:{server_port}"
    
    try:
        await test_server_endpoints()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 