#!/usr/bin/env python3
"""
Test script for the Q&A Analysis functionality.

This script demonstrates how to use the new ask_analysis_question MCP tool
to get intelligent answers about call analysis data.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from awslabs.call_analysis_mcp_server.tools.analysis_tools import qa_analysis_tool
from mcp.server.fastmcp import FastMCP


async def test_qa_functionality():
    """Test the Q&A functionality with various question types."""
    
    print("🤖 Testing Call Analysis Q&A Functionality")
    print("=" * 50)
    
    # Create a mock MCP instance for testing
    mcp = FastMCP("test_qa")
    
    # Register the Q&A tool
    qa_analysis_tool(mcp)
    
    # Get the ask_analysis_question function directly for testing
    from awslabs.call_analysis_mcp_server.tools.analysis_tools import _analyze_question_intent, _generate_intelligent_response
    
    # Test questions to demonstrate functionality
    test_questions = [
        {
            "question": "How was the overall quality of today's calls?",
            "description": "Overall quality assessment"
        },
        {
            "question": "Were there any deals at risk based on today's conversations?", 
            "description": "Deal risk identification"
        },
        {
            "question": "Show me pipeline health based on this week's calls.",
            "description": "Pipeline health analysis"
        },
        {
            "question": "Which reps need training based on recent call behavior?",
            "description": "Training needs identification"
        },
        {
            "question": "Are there churn risks in today's inbound calls?",
            "description": "Churn risk detection"
        },
        {
            "question": "Any probable new opportunities from today's calls?",
            "description": "Opportunity identification"
        },
        {
            "question": "Any recurring objections we should address?",
            "description": "Objection pattern analysis"
        }
    ]
    
    # Check if the analysis report exists
    report_file = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
    
    if not os.path.exists(report_file):
        print(f"❌ Analysis report not found: {report_file}")
        print("🔧 Please run the analysis first using the test_ai_enhanced_analysis.py script")
        return False
    
    print(f"✅ Found analysis report: {report_file}")
    print(f"📊 Loading business intelligence data...")
    
    # Load the report to show summary
    with open(report_file, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    print(f"\n📈 Report Summary:")
    print(f"   • Calls Analyzed: {report_data.get('total_calls_analyzed', 0)}")
    print(f"   • Analysis Period: {report_data.get('analysis_period', 'Unknown')}")
    print(f"   • Quality Score: {report_data.get('overall_quality_score', 0):.1f}/10")
    print(f"   • Deals at Risk: {len(report_data.get('deals_at_risk', []))}")
    print(f"   • Churn Risks: {len(report_data.get('churn_risks', []))}")
    print(f"   • Opportunities: {len(report_data.get('new_opportunities', []))}")
    
    print(f"\n🤔 Testing Q&A Functionality with {len(test_questions)} sample questions...")
    print("=" * 50)
    
    # Test each question
    for i, test_case in enumerate(test_questions, 1):
        question = test_case["question"]
        description = test_case["description"]
        
        print(f"\n{i}. {description}")
        print(f"❓ Question: \"{question}\"")
        
        try:
            # Test question intent analysis
            intent = _analyze_question_intent(question.lower())
            print(f"🧠 AI Analysis: {intent['question_type']} question about {intent['primary_context']}")
            
            # Generate response (simulate the MCP tool call)
            response = _generate_intelligent_response(question, intent, report_data, intent['primary_context'])
            
            print(f"💬 Answer:")
            print(f"{response['answer']}")
            
            if response.get('insights'):
                print(f"💡 Key Insights:")
                for insight in response['insights'][:2]:  # Show first 2
                    print(f"   • {insight}")
            
            if response.get('recommendations'):
                print(f"🎯 Recommendations:")
                for rec in response['recommendations'][:2]:  # Show first 2
                    print(f"   • {rec}")
            
        except Exception as e:
            print(f"❌ Error processing question: {e}")
        
        print("-" * 40)
    
    print(f"\n✅ Q&A Functionality Test Complete!")
    print(f"\n🚀 How to Use the MCP Tool:")
    print(f"   1. Make sure your MCP server is running")
    print(f"   2. Use the 'ask_analysis_question' tool with your questions")
    print(f"   3. The tool will automatically detect question type and context")
    print(f"   4. Get intelligent answers with supporting data and insights")
    
    return True


def show_mcp_usage_examples():
    """Show examples of how to use the MCP tool."""
    
    print(f"\n📖 MCP Tool Usage Examples:")
    print("=" * 50)
    
    examples = [
        {
            "name": "Basic Quality Question",
            "tool_call": {
                "tool": "ask_analysis_question",
                "parameters": {
                    "question": "How was the overall quality of today's calls?"
                }
            }
        },
        {
            "name": "Specific Deal Risk Query",
            "tool_call": {
                "tool": "ask_analysis_question", 
                "parameters": {
                    "question": "Show me high-risk deals that need immediate attention",
                    "context_type": "deals"
                }
            }
        },
        {
            "name": "Training Needs Analysis",
            "tool_call": {
                "tool": "ask_analysis_question",
                "parameters": {
                    "question": "Which agents need training and in what areas?",
                    "context_type": "training"
                }
            }
        },
        {
            "name": "Custom Report Path",
            "tool_call": {
                "tool": "ask_analysis_question",
                "parameters": {
                    "question": "Are there any churn risks?",
                    "report_file_path": "/path/to/your/custom/report.json"
                }
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}:")
        print(f"   Tool: {example['tool_call']['tool']}")
        print(f"   Parameters:")
        for key, value in example['tool_call']['parameters'].items():
            print(f"     - {key}: \"{value}\"")
    
    print(f"\n🎯 Context Types Available:")
    contexts = ["auto", "quality", "deals", "churn", "opportunities", "training", "pipeline", "objections"]
    for context in contexts:
        print(f"   • {context}")
    
    print(f"\n📝 Question Types Supported:")
    types = ["overview", "metrics", "drill_down", "comparison", "trend", "recommendation"]
    for q_type in types:
        print(f"   • {q_type}")


async def main():
    """Main test function."""
    
    try:
        success = await test_qa_functionality()
        
        if success:
            show_mcp_usage_examples()
            
            print(f"\n🎉 Q&A Tool is ready to use!")
            print(f"💡 Try asking questions about your call analysis data through the MCP interface")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 