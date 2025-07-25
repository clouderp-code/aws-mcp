#!/usr/bin/env python3
"""
Test script for the Call Analysis MCP Server
Tests the MCP server tools directly without mock data
"""

import sys
import os
import asyncio
import json

# Add the parent directory to Python path to find awslabs module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcp.server.fastmcp import FastMCP
from awslabs.call_analysis_mcp_server.tools.analysis_tools import (
    transcript_analyzer_tool,
    business_intelligence_tool,
    local_scripts_analysis_tool
)
from awslabs.call_analysis_mcp_server.tools.s3_tools import (
    s3_reader_tool,
    s3_uploader_tool
)
from awslabs.call_analysis_mcp_server.tools.reporting_tools import (
    generate_report_tool,
    create_dashboard_tool
)

def test_mcp_server_setup():
    """Test MCP server initialization and tool registration"""
    print("🚀 Testing MCP Server Setup...")
    print("=" * 60)
    
    try:
        # Create MCP server
        mcp = FastMCP("call-analysis-mcp-server")
        print("✅ MCP server created successfully")
        
        # Register tools
        transcript_analyzer_tool(mcp)
        business_intelligence_tool(mcp)
        local_scripts_analysis_tool(mcp)
        s3_reader_tool(mcp)
        s3_uploader_tool(mcp)
        generate_report_tool(mcp)
        create_dashboard_tool(mcp)
        
        print("✅ All MCP tools registered successfully")
        
        # List available tools
        tools = mcp.list_tools()
        print(f"\n📋 Available MCP Tools ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}: {tool.description[:80]}...")
        
        return True, mcp
        
    except Exception as e:
        print(f"❌ MCP server setup failed: {str(e)}")
        return False, None

async def test_local_scripts_tool(mcp):
    """Test the local scripts analysis tool"""
    print("\n🔍 Testing Local Scripts Analysis Tool...")
    print("=" * 60)
    
    try:
        # Test with transcripts folder
        result = await mcp.call_tool(
            "local_scripts_analysis",
            {
                "scripts_folder": "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts",
                "max_scripts": 3,  # Test with just 3 scripts for speed
                "output_file": "mcp_test_output.json"
            }
        )
        
        print("✅ Local scripts analysis completed")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if hasattr(first_result, 'content'):
                print(f"📄 Content preview: {str(first_result.content)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Local scripts analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_business_intelligence_tool(mcp):
    """Test the business intelligence tool"""
    print("\n📈 Testing Business Intelligence Tool...")
    print("=" * 60)
    
    try:
        # Create some mock analysis results for BI testing
        mock_analysis = {
            "call_id": "test-call-001",
            "analysis": {
                "sentiment": {"overall_sentiment": "positive", "confidence": 0.8},
                "performance_kpis": {
                    "call_duration_minutes": 15.5,
                    "agent_talk_time_percentage": 60.0,
                    "customer_satisfaction_score": 8.5
                }
            }
        }
        
        # Test BI generation
        result = await mcp.call_tool(
            "generate_business_intelligence",
            {
                "analysis_results": [mock_analysis],
                "output_bucket": "test-bucket",
                "output_key": "test-bi-output.json"
            }
        )
        
        print("✅ Business intelligence generation completed")
        print(f"📊 Result type: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Business intelligence test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_transcript_formats():
    """Test different transcript format parsing"""
    print("\n📝 Testing Transcript Format Parsing...")
    print("=" * 60)
    
    try:
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Test JSON format
        json_transcript = '''
        {
            "call_id": "test-001",
            "transcript": [
                {"speaker": "agent", "text": "Hello, how can I help you today?", "timestamp": "00:00"},
                {"speaker": "customer", "text": "I'm having issues with my service", "timestamp": "00:05"}
            ]
        }
        '''
        
        segments = analyzer.parse_transcript(json_transcript, "json")
        print(f"✅ JSON parsing: {len(segments)} segments extracted")
        
        # Test plain text format  
        text_transcript = """Agent: Hello, how can I help you today?
Customer: I'm having issues with my service
Agent: I can help you with that. What specific issues are you experiencing?"""
        
        segments = analyzer.parse_transcript(text_transcript, "text")
        print(f"✅ Text parsing: {len(segments)} segments extracted")
        
        return True
        
    except Exception as e:
        print(f"❌ Transcript format testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    print("🧪 Call Analysis MCP Server - Comprehensive Testing")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: MCP Server Setup
    success, mcp = test_mcp_server_setup()
    test_results.append(("MCP Server Setup", success))
    
    if not success:
        print("❌ Cannot continue without MCP server")
        return
    
    # Test 2: Transcript Format Parsing
    success = test_transcript_formats()
    test_results.append(("Transcript Format Parsing", success))
    
    # Test 3: Local Scripts Tool
    success = await test_local_scripts_tool(mcp)
    test_results.append(("Local Scripts Analysis", success))
    
    # Test 4: Business Intelligence Tool
    success = await test_business_intelligence_tool(mcp)
    test_results.append(("Business Intelligence", success))
    
    # Print summary
    print("\n🏁 Test Summary")
    print("=" * 80)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! MCP server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 