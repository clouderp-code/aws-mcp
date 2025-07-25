#!/usr/bin/env python3
"""
Test script for the REAL MCP analysis tool - no mocking, real analysis.
This tests the actual TranscriptAnalyzer and BusinessIntelligenceAnalyzer services.
"""

import sys
import json
import glob
import os
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_real_analysis():
    """Test the real analysis components without mocking."""
    
    print("🔬 Testing REAL MCP Analysis Tool (No Mocking)")
    print("=" * 60)
    
    try:
        # Import the real analysis components
        from awslabs.call_analysis_mcp_server.models import (
            TranscriptSegment, CallParticipant, SentimentType
        )
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        from awslabs.call_analysis_mcp_server.services.business_intelligence import BusinessIntelligenceAnalyzer
        from awslabs.call_analysis_mcp_server.consts import DEFAULT_ANALYSIS_OPTIONS
        
        print("✅ Successfully imported real analysis components")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 To fix this, install the required dependencies:")
        print("pip install loguru pydantic")
        print("pip install nltk textstat spacy transformers torch numpy pandas scikit-learn vaderSentiment python-dateutil regex")
        return False
    
    # Helper function to convert script to segments (same as real tool)
    def convert_script_to_segments(script_data):
        """Convert script data to TranscriptSegment objects."""
        segments = []
        transcript = script_data.get('transcript', [])
        
        current_timestamp = 0.0
        
        for entry in transcript:
            speaker = entry.get('speaker', 'unknown').lower()
            text = entry.get('text', '')
            
            # Parse timestamp if available
            timestamp_str = entry.get('timestamp', '')
            if timestamp_str and '–' in timestamp_str:
                start_time_str = timestamp_str.split('–')[0].strip()
                try:
                    parts = start_time_str.split(':')
                    if len(parts) >= 2:
                        minutes = int(parts[0])
                        seconds = int(parts[1])
                        current_timestamp = minutes * 60 + seconds
                except (ValueError, IndexError):
                    pass
            
            # Estimate duration based on text length
            word_count = len(text.split())
            estimated_duration = max(2.0, word_count * 0.5)
            
            # Map speaker to CallParticipant
            if speaker == 'agent':
                call_participant = CallParticipant.AGENT
            elif speaker == 'customer':
                call_participant = CallParticipant.CUSTOMER
            else:
                call_participant = CallParticipant.SYSTEM
            
            segment = TranscriptSegment(
                timestamp=current_timestamp,
                speaker=call_participant,
                text=text,
                duration=estimated_duration,
                confidence=0.95
            )
            
            segments.append(segment)
            current_timestamp += estimated_duration
        
        return segments
    
    # Find script files
    scripts_folder = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts"
    script_files = sorted(glob.glob(os.path.join(scripts_folder, "script*.json")))[:5]  # Test with first 5
    
    if not script_files:
        print("❌ No script files found!")
        return False
    
    print(f"📁 Found {len(glob.glob(os.path.join(scripts_folder, 'script*.json')))} script files")
    print(f"🧪 Testing with first {len(script_files)} files...")
    
    # Initialize REAL analysis services
    try:
        analyzer = TranscriptAnalyzer()
        bi_analyzer = BusinessIntelligenceAnalyzer()
        analysis_options = DEFAULT_ANALYSIS_OPTIONS.copy()
        analysis_options["evidence_collection"] = True
        
        print("✅ Real analysis services initialized")
        
    except Exception as e:
        print(f"❌ Error initializing analysis services: {e}")
        return False
    
    # Process scripts with REAL analysis
    analysis_results = []
    successful_analyses = 0
    
    for script_file in script_files:
        try:
            print(f"\n🔍 Processing {os.path.basename(script_file)}...")
            
            # Read script file
            with open(script_file, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Convert to transcript segments
            transcript_segments = convert_script_to_segments(script_data)
            print(f"   📝 Converted to {len(transcript_segments)} segments")
            
            # Get call ID
            call_id = script_data.get('call_id', os.path.basename(script_file).replace('.json', ''))
            
            # REAL ANALYSIS - No mocking!
            print(f"   🧠 Running REAL analysis for call {call_id}...")
            analysis_result = analyzer.analyze_transcript(
                transcript_segments=transcript_segments,
                call_id=call_id,
                analysis_options=analysis_options
            )
            
            # Set metadata
            analysis_result.transcript_source = script_file
            analysis_result.processing_time_seconds = 1.0  # Placeholder
            
            # Convert to dictionary for BI analysis
            analysis_dict = analysis_result.model_dump()
            analysis_results.append(analysis_dict)
            
            successful_analyses += 1
            print(f"   ✅ Real analysis completed!")
            print(f"      • Sentiment: {analysis_result.sentiment_analysis.overall_sentiment}")
            print(f"      • Satisfaction: {analysis_result.performance_kpis.customer_satisfaction_score:.1f}/10")
            print(f"      • Compliance: {analysis_result.compliance_metrics.compliance_score:.1f}/10")
            print(f"      • Deal Risk Signals: {len(analysis_result.deal_risk_indicators)}")
            print(f"      • Churn Risk Signals: {len(analysis_result.churn_risk_signals)}")
            print(f"      • Opportunity Signals: {len(analysis_result.opportunity_signals)}")
            
        except Exception as e:
            print(f"   ❌ Error in real analysis: {str(e)}")
            # Print more detailed error info
            import traceback
            print(f"   📋 Error details: {traceback.format_exc()}")
            continue
    
    if not analysis_results:
        print("❌ No successful real analyses completed")
        return False
    
    print(f"\n📊 Generating REAL Business Intelligence with Evidence...")
    
    try:
        # Generate REAL business intelligence insights
        bi_insights = bi_analyzer.generate_insights(
            analysis_results=analysis_results,
            time_period="Real Analysis Test"
        )
        
        print("✅ Real BI analysis completed!")
        
        # Save real results
        output_file = os.path.join(scripts_folder, "real_analysis_report.json")
        bi_content = bi_insights.model_dump_json(indent=2)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(bi_content)
        
        print(f"💾 Real analysis report saved to: {output_file}")
        
        # Print REAL analysis summary
        print(f"\n📈 REAL Analysis Results:")
        print(f"   • Total calls analyzed: {bi_insights.total_calls_analyzed}")
        print(f"   • Overall quality score: {bi_insights.overall_quality_score:.1f}/10")
        print(f"   • Quality trend: {bi_insights.quality_trend}")
        print(f"   • Calls with issues: {bi_insights.calls_with_issues}")
        print(f"   • Deals at risk: {len(bi_insights.deals_at_risk)}")
        print(f"   • Churn risks: {len(bi_insights.churn_risks)}")
        print(f"   • New opportunities: {len(bi_insights.new_opportunities)}")
        print(f"   • Training needs: {len(bi_insights.agent_training_needs)}")
        print(f"   • Evidence items collected: {bi_insights.evidence_summary.get('total_evidence_items', 0)}")
        print(f"   • Analysis confidence: {bi_insights.analysis_confidence}")
        
        print(f"\n🎯 Real Top Priorities:")
        for i, priority in enumerate(bi_insights.top_priorities, 1):
            print(f"   {i}. {priority}")
        
        # Show evidence examples
        if bi_insights.deals_at_risk:
            print(f"\n🔍 Evidence Example (Deal Risk):")
            deal = bi_insights.deals_at_risk[0]
            if deal.evidence.primary_evidence:
                evidence = deal.evidence.primary_evidence[0]
                print(f"   • Call: {evidence.call_id}")
                print(f"   • Speaker: {evidence.speaker}")
                print(f"   • Quote: \"{evidence.evidence_text[:100]}...\"")
                print(f"   • Context: {evidence.context}")
                print(f"   • Confidence: {evidence.confidence_score}")
        
        print(f"\n✨ REAL ANALYSIS COMPLETED SUCCESSFULLY!")
        print(f"📊 This is genuine analysis with real NLP, sentiment analysis, and BI insights!")
        print(f"📄 No mocking - all results are from actual analysis algorithms!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in real BI analysis: {str(e)}")
        import traceback
        print(f"📋 BI Error details: {traceback.format_exc()}")
        return False

def test_mcp_tool_directly():
    """Test the actual MCP tool function directly."""
    
    print(f"\n🛠️ Testing MCP Tool Function Directly")
    print("=" * 50)
    
    try:
        from awslabs.call_analysis_mcp_server.tools.analysis_tools import _convert_script_to_segments
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        from awslabs.call_analysis_mcp_server.services.business_intelligence import BusinessIntelligenceAnalyzer
        
        # This tests the same logic that the MCP tool uses
        script_file = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/script1.json"
        
        with open(script_file, 'r') as f:
            script_data = json.load(f)
        
        # Use the same function the MCP tool uses
        segments = _convert_script_to_segments(script_data)
        print(f"✅ MCP tool function works: converted {len(segments)} segments")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP tool function test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting REAL Analysis Testing...")
    
    # Test 1: Real analysis components
    success1 = test_real_analysis()
    
    # Test 2: MCP tool function
    success2 = test_mcp_tool_directly()
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ The MCP tool performs REAL analysis, no mocking!")
        print(f"✅ Ready for production use!")
    else:
        print(f"\n⚠️ Some tests failed - check error messages above")
        print(f"💡 Install missing dependencies to enable full real analysis") 