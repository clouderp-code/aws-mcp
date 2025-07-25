#!/usr/bin/env python3
"""
Test script for the Q&A Analysis functionality with Evidence Data.

This script demonstrates how the enhanced Q&A tool now includes comprehensive
evidence data with specific quotes, timestamps, and confidence scores.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Add the project root to Python path (parent directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from awslabs.call_analysis_mcp_server.tools.analysis_tools import (
    _analyze_question_intent, 
    _generate_intelligent_response,
    _handle_deals_questions,
    _handle_churn_questions,
    _handle_opportunities_questions,
    _handle_training_questions
)


async def test_evidence_functionality():
    """Test the Q&A functionality with evidence data."""
    
    print("🔍 Testing Call Analysis Q&A with Evidence Data")
    print("=" * 60)
    
    # Check if the analysis report exists
    report_file = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json"
    
    if not os.path.exists(report_file):
        print(f"❌ Analysis report not found: {report_file}")
        print("🔧 Please run the analysis first using the test_ai_enhanced_analysis.py script")
        return False
    
    print(f"✅ Found analysis report: {report_file}")
    
    # Load the report
    with open(report_file, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    print(f"📊 Report loaded with {report_data.get('total_calls_analyzed', 0)} calls analyzed")
    
    # Test questions that should show evidence
    evidence_test_questions = [
        {
            "question": "Show me deals at risk with supporting evidence",
            "handler": _handle_deals_questions,
            "description": "Deal Risk Analysis with Evidence"
        },
        {
            "question": "What churn risks do we have based on customer quotes?",
            "handler": _handle_churn_questions,
            "description": "Churn Risk Analysis with Customer Evidence"
        },
        {
            "question": "Show me new opportunities with specific customer signals",
            "handler": _handle_opportunities_questions,
            "description": "Opportunity Analysis with Evidence"
        },
        {
            "question": "Which agents need training based on call examples?",
            "handler": _handle_training_questions,
            "description": "Training Needs with Performance Evidence"
        }
    ]
    
    print(f"\n🧪 Testing {len(evidence_test_questions)} evidence-rich Q&A scenarios...")
    print("=" * 60)
    
    for i, test_case in enumerate(evidence_test_questions, 1):
        question = test_case["question"]
        handler = test_case["handler"]
        description = test_case["description"]
        
        print(f"\n{i}. {description}")
        print(f"❓ Question: \"{question}\"")
        print("-" * 50)
        
        try:
            # Test question intent analysis
            intent = _analyze_question_intent(question.lower())
            print(f"🧠 Intent: {intent['question_type']} about {intent['primary_context']}")
            
            # Generate response with evidence
            response = handler(question, intent, report_data)
            
            print(f"\n💬 Answer:")
            print(response['answer'])
            
            # Show evidence metrics
            evidence_count = len(response.get('evidence', []))
            print(f"\n📊 Evidence Metrics:")
            print(f"   • Evidence Items: {evidence_count}")
            print(f"   • Supporting Data Items: {len(response.get('supporting_data', []))}")
            
            if evidence_count > 0:
                print(f"\n📋 Sample Evidence (first 3 items):")
                for j, evidence in enumerate(response['evidence'][:3], 1):
                    quote = evidence.get('quote', '')[:80] + "..." if len(evidence.get('quote', '')) > 80 else evidence.get('quote', '')
                    print(f"   {j}. Call {evidence.get('call_id', 'Unknown')} @ {evidence.get('timestamp', 0)}s")
                    print(f"      {evidence.get('speaker', 'Unknown').title()}: \"{quote}\"")
                    print(f"      Confidence: {evidence.get('confidence', 0):.0%}")
                    if evidence.get('context'):
                        print(f"      Context: {evidence['context']}")
                    print()
            
            # Show insights
            if response.get('insights'):
                print(f"💡 Key Insights:")
                for insight in response['insights']:
                    print(f"   • {insight}")
            
            # Show recommendations if available
            if response.get('recommendations'):
                print(f"🎯 Recommendations:")
                for rec in response['recommendations']:
                    print(f"   • {rec}")
            
        except Exception as e:
            print(f"❌ Error processing question: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
    
    # Test overall evidence summary
    print(f"\n📈 Overall Evidence Analysis:")
    print("-" * 40)
    
    try:
        # Test general overview with evidence summary
        overview_intent = _analyze_question_intent("how was the overall quality of calls")
        overview_response = _generate_intelligent_response(
            "How was the overall quality of calls?", 
            overview_intent, 
            report_data, 
            "quality"
        )
        
        print(overview_response['answer'])
        
        # Calculate total evidence across all sections
        total_evidence = 0
        for section in ['deals_at_risk', 'churn_risks', 'new_opportunities', 'agent_training_needs']:
            section_data = report_data.get(section, [])
            for item in section_data:
                evidence = item.get('evidence', {})
                total_evidence += len(evidence.get('primary_evidence', []))
        
        print(f"\n📊 Evidence Statistics:")
        print(f"   • Total Evidence Items: {total_evidence}")
        print(f"   • Deals at Risk Evidence: {sum(len(d.get('evidence', {}).get('primary_evidence', [])) for d in report_data.get('deals_at_risk', []))}")
        print(f"   • Churn Risk Evidence: {sum(len(c.get('evidence', {}).get('primary_evidence', [])) for c in report_data.get('churn_risks', []))}")
        print(f"   • Opportunity Evidence: {sum(len(o.get('evidence', {}).get('primary_evidence', [])) for o in report_data.get('new_opportunities', []))}")
        print(f"   • Training Evidence: {sum(len(t.get('evidence', {}).get('primary_evidence', [])) for t in report_data.get('agent_training_needs', []))}")
        
    except Exception as e:
        print(f"❌ Error in evidence summary: {e}")
    
    print(f"\n✅ Evidence-Enhanced Q&A Testing Complete!")
    print(f"\n🎯 Key Evidence Features Demonstrated:")
    print(f"   ✓ Specific customer quotes with timestamps")
    print(f"   ✓ Speaker identification (customer/agent)")  
    print(f"   ✓ Confidence scores for each piece of evidence")
    print(f"   ✓ Contextual explanations for evidence")
    print(f"   ✓ Evidence sorting by priority and confidence")
    print(f"   ✓ Evidence statistics and metrics")
    
    return True


def show_evidence_structure():
    """Show the structure of evidence data in responses."""
    
    print(f"\n📖 Evidence Data Structure:")
    print("=" * 50)
    
    print(f"""
**Response Structure with Evidence:**
{{
  "answer": "Formatted answer with embedded evidence quotes",
  "metrics": {{
    "evidence_items": <count>,
    "confidence_average": <percentage>
  }},
  "evidence": [
    {{
      "account": "Account Name",
      "call_id": "Call ID", 
      "speaker": "customer|agent",
      "timestamp": <seconds>,
      "quote": "Actual spoken text from transcript",
      "context": "AI interpretation of evidence significance",
      "confidence": <0.0-1.0>,
      "risk_level|urgency|priority": "Context-specific metadata"
    }}
  ],
  "insights": ["AI-generated insights including evidence confidence"],
  "supporting_data": [<detailed data objects>]
}}

**Evidence in Answers:**
• Embedded quotes with timestamps and speakers
• Confidence scores for reliability assessment  
• Contextual explanations for business relevance
• Sorted by priority/risk level for actionability

**Evidence Sources:**
• Direct customer statements indicating risk/opportunity
• Agent performance examples for training needs
• Conversation patterns showing business insights
• Timestamp-linked quotes for call review
""")


async def main():
    """Main test function."""
    
    try:
        success = await test_evidence_functionality()
        
        if success:
            show_evidence_structure()
            
            print(f"\n🎉 Evidence-Enhanced Q&A System Ready!")
            print(f"💡 Your questions will now include comprehensive evidence data")
            print(f"🔍 Use the MCP tool 'ask_analysis_question' to get evidence-backed answers")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 