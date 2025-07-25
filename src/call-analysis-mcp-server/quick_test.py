#!/usr/bin/env python3
"""
Quick verification test for Call Analysis MCP Server
Tests basic functionality without long-running operations
"""

import sys
import os
import asyncio
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core modules can be imported"""
    print("🔍 Testing Core Imports...")
    try:
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        from awslabs.call_analysis_mcp_server.services.business_intelligence import BusinessIntelligenceAnalyzer
        from awslabs.call_analysis_mcp_server.services.ai_analyzer import AIAnalyzer
        from awslabs.call_analysis_mcp_server.models import CallAnalysisResult, BusinessIntelligenceInsights
        print("✅ All core services imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_transcript_parsing():
    """Test basic transcript parsing"""
    print("\n📝 Testing Transcript Parsing...")
    try:
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Test with simple JSON transcript (array format)
        test_transcript = [
            {"speaker": "agent", "text": "Hello, how can I help you?", "timestamp": 0.0, "confidence": 0.95},
            {"speaker": "customer", "text": "I need help with billing", "timestamp": 5.0, "confidence": 0.95}
        ]
        
        segments = analyzer.parse_transcript(json.dumps(test_transcript))
        print(f"✅ Parsed {len(segments)} segments from test transcript")
        return True
        
    except Exception as e:
        print(f"❌ Transcript parsing failed: {e}")
        return False

async def test_mcp_tools():
    """Test MCP tool registration"""
    print("\n🔧 Testing MCP Tool Registration...")
    try:
        from mcp.server.fastmcp import FastMCP
        from awslabs.call_analysis_mcp_server.tools.analysis_tools import (
            transcript_analyzer_tool,
            business_intelligence_tool,
            local_scripts_analysis_tool
        )
        
        mcp = FastMCP("quick-test-server")
        
        # Register tools
        transcript_analyzer_tool(mcp)
        business_intelligence_tool(mcp) 
        local_scripts_analysis_tool(mcp)
        
        tools = await mcp.list_tools()
        print(f"✅ Successfully registered {len(tools)} MCP tools")
        
        for tool in tools:
            print(f"   - {tool.name}")
            
        return True
        
    except Exception as e:
        print(f"❌ MCP tool registration failed: {e}")
        return False

def test_ai_initialization():
    """Test AI analyzer initialization"""
    print("\n🤖 Testing AI Analyzer...")
    try:
        from awslabs.call_analysis_mcp_server.services.ai_analyzer import AIAnalyzer
        
        ai_analyzer = AIAnalyzer()
        
        if ai_analyzer.client:
            print("✅ AI analyzer initialized with OpenAI client")
        else:
            print("⚠️  AI analyzer initialized without OpenAI (API key missing)")
            
        return True
        
    except Exception as e:
        print(f"❌ AI analyzer initialization failed: {e}")
        return False

async def test_quick_analysis():
    """Test quick analysis on a small sample"""
    print("\n⚡ Testing Quick Analysis...")
    try:
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        
        analyzer = TranscriptAnalyzer()
        
        # Create test transcript segments (array format)
        test_transcript = [
            {"speaker": "agent", "text": "Thank you for calling. How can I assist you today?", "timestamp": 0.0, "confidence": 0.95},
            {"speaker": "customer", "text": "I'm frustrated with the service outage yesterday", "timestamp": 8.0, "confidence": 0.95},
            {"speaker": "agent", "text": "I apologize for the inconvenience. Let me check your account", "timestamp": 15.0, "confidence": 0.95}
        ]
        
        segments = analyzer.parse_transcript(json.dumps(test_transcript))
        
        # Run basic analysis
        result = await analyzer.analyze_transcript(
            transcript_segments=segments,
            call_id="quick-test-002",
            analysis_options={"sentiment": True, "kpis": True, "compliance": True}
        )
        
        print(f"✅ Analysis completed for call {result.call_id}")
        print(f"   - Sentiment: {result.sentiment_analysis.overall_sentiment}")
        print(f"   - KPIs calculated: {len(result.performance_kpis.__dict__)} metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all quick tests"""
    print("⚡ Call Analysis MCP Server - Quick Verification")
    print("=" * 60)
    
    tests = [
        ("Core Imports", test_imports()),
        ("Transcript Parsing", test_transcript_parsing()),
        ("MCP Tool Registration", await test_mcp_tools()),
        ("AI Initialization", test_ai_initialization()),
        ("Quick Analysis", await test_quick_analysis())
    ]
    
    print("\n" + "=" * 60)
    print("🏁 Quick Test Results:")
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Summary: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All quick tests passed! Server is ready for full testing.")
        print("\n💡 Next steps:")
        print("   - Run 'python test_real_analysis.py' for comprehensive testing")
        print("   - Run 'python test_ai_enhanced_analysis.py' for AI-powered analysis")
    else:
        print("⚠️  Some tests failed. Check dependencies and configuration.")

if __name__ == "__main__":
    asyncio.run(main()) 