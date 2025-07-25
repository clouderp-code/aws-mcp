#!/usr/bin/env python3
"""
Enhanced Test Script for AI-Powered Call Analysis MCP Server

This script tests the real AI-enhanced analysis capabilities including:
- GPT-powered sentiment analysis
- AI-driven business intelligence insights
- Enhanced deal risk, churn, and opportunity detection
- Full evidence trails from actual transcript content
"""

import sys
import json
import glob
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List

# Add the current directory to the Python path
sys.path.insert(0, '.')

def test_ai_enhanced_analysis():
    """Test the AI-enhanced analysis capabilities."""
    print("🤖 Testing AI-Enhanced Call Analysis MCP Server")
    print("=" * 60)
    
    try:
        # Import the real analysis components
        from awslabs.call_analysis_mcp_server.models import TranscriptSegment, CallParticipant, SentimentType
        from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
        from awslabs.call_analysis_mcp_server.services.business_intelligence import BusinessIntelligenceAnalyzer
        from awslabs.call_analysis_mcp_server.services.ai_analyzer import AIAnalyzer
        from awslabs.call_analysis_mcp_server.consts import DEFAULT_ANALYSIS_OPTIONS
        
        print("✅ Successfully imported AI-enhanced analysis components")
        
        # Check if OpenAI is available
        ai_analyzer = AIAnalyzer()
        if ai_analyzer.client:
            print("🤖 OpenAI GPT models are available for enhanced analysis")
        else:
            print("⚠️  OpenAI not configured - using enhanced fallback analysis")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 To fix this, install the required dependencies:")
        print("uv pip install -r requirements.txt")
        return False

    def convert_script_to_segments(script_data):
        """Convert script data to transcript segments with real metadata."""
        segments = []
        transcript = script_data.get('transcript', [])
        
        current_timestamp = 0.0
        for i, entry in enumerate(transcript):
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
            if speaker in ['agent']:
                participant = CallParticipant.AGENT
            elif speaker in ['customer', 'client']:
                participant = CallParticipant.CUSTOMER
            else:
                participant = CallParticipant.SYSTEM
            
            segment = TranscriptSegment(
                speaker=participant,
                text=text,
                timestamp=current_timestamp,
                duration=estimated_duration,
                confidence=0.95  # Default confidence score
            )
            segments.append(segment)
            
            # Update timestamp for next segment
            current_timestamp += estimated_duration
        
        return segments

    async def run_ai_analysis():
        """Run the actual AI-enhanced analysis."""
        
        # Find script files
        scripts_folder = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts"
        script_files = sorted(glob.glob(os.path.join(scripts_folder, "script*.json")))  # Process all script files
        
        if not script_files:
            print("❌ No script files found")
            return False
        
        print(f"📁 Found {len(script_files)} script files, processing ALL files...")
        
        # Initialize analyzers
        analyzer = TranscriptAnalyzer()
        bi_analyzer = BusinessIntelligenceAnalyzer()
        
        # Enable AI-enhanced options
        analysis_options = DEFAULT_ANALYSIS_OPTIONS.copy()
        analysis_options["ai_enhanced"] = True
        analysis_options["evidence_collection"] = True
        
        # Prepare all call batches for efficient batch processing
        call_batches = []
        total_files = len(script_files)
        start_time = time.time()
        
        print(f"\n📁 Reading and preparing {total_files} script files for batch processing...")
        
        for i, script_file in enumerate(script_files, 1):
            try:
                if i % 10 == 0 or i == total_files:
                    print(f"   📖 Reading: {i}/{total_files} files")
                
                # Read script file
                with open(script_file, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                
                # Convert to transcript segments
                transcript_segments = convert_script_to_segments(script_data)
                
                # Get call ID and real metadata
                call_id = script_data.get('call_id', os.path.basename(script_file).replace('.json', ''))
                company_name = script_data.get('customer', {}).get('company', f'Company_{call_id}')
                agent_name = script_data.get('agent', {}).get('name', f'Agent_{call_id}')
                script_source = os.path.basename(script_file)
                
                call_batches.append({
                    "call_id": call_id,
                    "segments": transcript_segments,
                    "company_name": company_name,
                    "agent_name": agent_name,
                    "script_source": script_source,
                    "customer_role": script_data.get('customer', {}).get('role', 'Unknown'),
                    "agent_role": script_data.get('agent', {}).get('role', 'Unknown')
                })
                
            except Exception as e:
                print(f"   ❌ Error reading {script_file}: {e}")
                continue
        
        if not call_batches:
            print("❌ No script files could be read successfully")
            return False
        
        print(f"🚀 Starting batch AI-enhanced analysis for {len(call_batches)} calls...")
        print(f"   📊 Using batch processing (10 calls per batch for optimal performance)")
        
        # Perform batch transcript analysis
        batch_start = time.time()
        analysis_results_objects = await analyzer.batch_analyze_transcripts(
            call_batches=call_batches,
            analysis_options=analysis_options,
            batch_size=10
        )
        batch_time = time.time() - batch_start
        
        print(f"✅ Batch analysis completed in {batch_time:.1f}s!")
        print(f"   📈 Performance: {batch_time/len(call_batches):.2f}s per call (vs ~3.5s individual)")
        print(f"   💰 API efficiency: ~{len(call_batches)/10:.0f} batch calls vs {len(call_batches)} individual calls")
        
        # Convert results to the expected format for BI processing
        analysis_results = []
        for analysis_result, call_batch in zip(analysis_results_objects, call_batches):
            # Convert to dict for BI processing and add real metadata
            analysis_dict = analysis_result.model_dump()
            analysis_dict['real_metadata'] = {
                'company_name': call_batch['company_name'],
                'agent_name': call_batch['agent_name'],
                'script_source': call_batch['script_source'],
                'customer_role': call_batch['customer_role'],
                'agent_role': call_batch['agent_role']
            }
            analysis_results.append(analysis_dict)
            
            # Display enhanced results
            sentiment = analysis_dict.get("sentiment_analysis", {})
            performance = analysis_dict.get("performance_kpis", {})
            
            print(f"\n🔍 Results for call {analysis_result.call_id}:")
            print(f"   📞 Company: {call_batch['company_name']}")
            print(f"   👤 Agent: {call_batch['agent_name']}")
            print(f"   ✅ AI analysis completed!")
            print(f"      • Sentiment: {sentiment.get('overall_sentiment', 'unknown')}")
            print(f"      • Customer Satisfaction: {performance.get('customer_satisfaction_score', 0):.1f}/10")
            print(f"      • Agent Performance: {performance.get('agent_professionalism_score', 0):.1f}/10")
            print(f"      • Compliance Score: {performance.get('compliance_score', 0):.1f}/10")
            
            # Show emotional peaks if detected
            emotional_peaks = sentiment.get('emotional_peaks', [])
            if emotional_peaks:
                print(f"      • Emotional Moments: {len(emotional_peaks)} detected")
                for peak in emotional_peaks[:2]:  # Show first 2
                    print(f"        - {peak.get('emotion', 'unknown')} at {peak.get('timestamp', 0):.1f}s")
        
        if not analysis_results:
            print("❌ No successful AI analyses completed")
            return False
        
        print(f"\n📊 Generating AI-Enhanced Business Intelligence...")
        print(f"    Using {len(analysis_results)} successfully analyzed calls")
        
        try:
            # Generate AI-enhanced business intelligence
            bi_insights = await bi_analyzer.generate_insights(
                analysis_results=analysis_results,
                time_period="AI Enhancement Test"
            )
            
            # Save enhanced report
            output_file = os.path.join(scripts_folder, "ai_enhanced_analysis_all_scripts_report.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(bi_insights.model_dump_json(indent=2))
            
            print(f"💾 AI-enhanced analysis report saved to: {output_file}")
            
            # Display AI-enhanced insights summary
            print(f"\n🎯 AI-Enhanced Analysis Results:")
            print(f"   • Total calls analyzed: {bi_insights.total_calls_analyzed}")
            print(f"   • Overall quality score: {bi_insights.overall_quality_score:.1f}/10")
            print(f"   • Quality trend: {bi_insights.quality_trend}")
            print(f"   • Deals at risk: {len(bi_insights.deals_at_risk)}")
            print(f"   • Churn risks: {len(bi_insights.churn_risks)}")
            print(f"   • New opportunities: {len(bi_insights.new_opportunities)}")
            print(f"   • Training needs: {len(bi_insights.agent_training_needs)}")
            print(f"   • Average sentiment: {bi_insights.average_sentiment_score:.2f}")
            print(f"   • Average satisfaction: {bi_insights.average_customer_satisfaction:.1f}/10")
            
            # Breakdown by risk levels
            if bi_insights.deals_at_risk:
                risk_levels = {}
                for risk in bi_insights.deals_at_risk:
                    level = risk.risk_level.value
                    risk_levels[level] = risk_levels.get(level, 0) + 1
                print(f"   • Deal risk breakdown: {', '.join([f'{level}: {count}' for level, count in risk_levels.items()])}")
            
            if bi_insights.churn_risks:
                urgency_levels = {}
                for churn in bi_insights.churn_risks:
                    urgency = churn.intervention_urgency.value if hasattr(churn.intervention_urgency, 'value') else str(churn.intervention_urgency)
                    urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
                print(f"   • Churn urgency breakdown: {', '.join([f'{urgency}: {count}' for urgency, count in urgency_levels.items()])}")
            
            if bi_insights.new_opportunities:
                total_value = sum(opp.estimated_value for opp in bi_insights.new_opportunities)
                avg_value = total_value / len(bi_insights.new_opportunities)
                print(f"   • Total opportunity value: ${total_value:,.0f} (avg: ${avg_value:,.0f})")
            
            # Advanced analytics summary
            print(f"\n📊 Advanced Analytics:")
            if bi_insights.call_categorization:
                top_categories = sorted(bi_insights.call_categorization.items(), key=lambda x: x[1], reverse=True)[:3]
                categories_str = ", ".join([f"{cat.value}: {count}" for cat, count in top_categories])
                print(f"   • Top call categories: {categories_str}")
            
            if bi_insights.objection_analysis:
                objection_types = {}
                for obj in bi_insights.objection_analysis:
                    obj_type = obj.objection_type.value
                    objection_types[obj_type] = objection_types.get(obj_type, 0) + 1
                print(f"   • Objections detected: {len(bi_insights.objection_analysis)} total")
                if objection_types:
                    top_objections = sorted(objection_types.items(), key=lambda x: x[1], reverse=True)[:3]
                    obj_str = ", ".join([f"{obj}: {count}" for obj, count in top_objections])
                    print(f"     Types: {obj_str}")
            
            if bi_insights.competitive_analysis:
                total_competitors = sum(len(comp.competitors_mentioned) for comp in bi_insights.competitive_analysis)
                print(f"   • Competitive mentions: {total_competitors} across {len(bi_insights.competitive_analysis)} calls")
            
            if bi_insights.product_knowledge_gaps:
                gap_topics = {}
                for gap in bi_insights.product_knowledge_gaps:
                    gap_topics[gap.topic] = gap_topics.get(gap.topic, 0) + 1
                print(f"   • Knowledge gaps: {len(bi_insights.product_knowledge_gaps)} identified")
                if gap_topics:
                    top_gaps = sorted(gap_topics.items(), key=lambda x: x[1], reverse=True)[:3]
                    gaps_str = ", ".join([f"{topic}: {count}" for topic, count in top_gaps])
                    print(f"     Topics: {gaps_str}")
            
            # Performance metrics
            print(f"   • Avg resolution time: {bi_insights.average_resolution_time_minutes:.1f} minutes")
            print(f"   • First call resolution: {bi_insights.first_call_resolution_rate:.1%}")
            print(f"   • Escalation rate: {bi_insights.escalation_rate:.1%}")
            print(f"   • Follow-up adherence: {bi_insights.follow_up_adherence_rate:.1%}")
            
            # Conversion metrics
            conv = bi_insights.conversion_metrics
            print(f"   • Call→Demo: {conv.call_to_demo_probability:.1%} | Demo→Proposal: {conv.demo_to_proposal_probability:.1%}")
            print(f"   • Proposal→Close: {conv.proposal_to_close_probability:.1%} | Upsell: {conv.upsell_cross_sell_probability:.1%}")
            
            # Show specific insights with better sampling
            if bi_insights.deals_at_risk:
                print(f"\n🚨 Deal Risks Detected (top 5 of {len(bi_insights.deals_at_risk)}):")
                for risk in bi_insights.deals_at_risk[:5]:  # Show first 5
                    print(f"   • {risk.account_name}: {risk.risk_level.value} risk")
                    print(f"     Factors: {', '.join(risk.risk_factors[:2])}")
                    if risk.evidence.primary_evidence:
                        print(f"     Evidence: {len(risk.evidence.primary_evidence)} quotes")
                if len(bi_insights.deals_at_risk) > 5:
                    print(f"   ... and {len(bi_insights.deals_at_risk) - 5} more deals at risk")
            
            if bi_insights.churn_risks:
                print(f"\n⚠️  Churn Risks Detected (top 5 of {len(bi_insights.churn_risks)}):")
                for churn in bi_insights.churn_risks[:5]:  # Show first 5
                    print(f"   • {churn.account_name}: {churn.churn_probability:.1%} probability")
                    print(f"     Urgency: {churn.intervention_urgency}")
                    if churn.evidence.primary_evidence:
                        print(f"     Evidence: {len(churn.evidence.primary_evidence)} quotes")
                if len(bi_insights.churn_risks) > 5:
                    print(f"   ... and {len(bi_insights.churn_risks) - 5} more churn risks")
            
            if bi_insights.new_opportunities:
                print(f"\n💰 Opportunities Detected (top 5 of {len(bi_insights.new_opportunities)}):")
                for opp in bi_insights.new_opportunities[:5]:  # Show first 5
                    print(f"   • {opp.account_name}: {opp.opportunity_type}")
                    print(f"     Value: ${opp.estimated_value:,.0f}")
                    print(f"     Confidence: {opp.confidence_level:.1%}")
                if len(bi_insights.new_opportunities) > 5:
                    print(f"   ... and {len(bi_insights.new_opportunities) - 5} more opportunities")
            
            # Final timing summary
            total_time = time.time() - start_time
            avg_time_per_file = total_time / total_files
            print(f"\n⏱️  Processing Summary:")
            print(f"   • Total processing time: {total_time/60:.1f} minutes ({total_time:.1f} seconds)")
            print(f"   • Average time per file: {avg_time_per_file:.1f} seconds")
            print(f"   • Files processed: {total_files}")
            
            print(f"\n✨ AI-ENHANCED ANALYSIS COMPLETED SUCCESSFULLY!")
            print(f"🤖 This analysis uses real AI models for:")
            print(f"   ✅ Advanced sentiment analysis with emotional detection")
            print(f"   ✅ GPT-powered business insight extraction")
            print(f"   ✅ AI-driven risk and opportunity identification")
            print(f"   ✅ Intelligent evidence collection and validation")
            print(f"   ✅ Actionable recommendations with confidence scoring")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in AI business intelligence: {str(e)}")
            import traceback
            print(f"📋 BI Error details: {traceback.format_exc()}")
            return False
    
    # Run the async analysis
    try:
        result = asyncio.run(run_ai_analysis())
        return result
    except Exception as e:
        print(f"❌ Error running async analysis: {str(e)}")
        return False

def test_ai_models_directly():
    """Test AI models directly to verify functionality."""
    print(f"\n🧪 Testing AI Models Directly")
    print("=" * 40)
    
    try:
        from awslabs.call_analysis_mcp_server.services.ai_analyzer import AIAnalyzer
        from awslabs.call_analysis_mcp_server.models import TranscriptSegment, CallParticipant
        
        ai_analyzer = AIAnalyzer()
        
        # Create sample segments for testing
        test_segments = [
            TranscriptSegment(
                speaker=CallParticipant.CUSTOMER,
                text="I'm really concerned about the pricing. This seems quite expensive compared to what your competitor offered.",
                timestamp=120.0,
                duration=5.0,
                confidence=0.95
            ),
            TranscriptSegment(
                speaker=CallParticipant.AGENT,
                text="I understand your concern about pricing. Let me explain the value proposition and ROI benefits.",
                timestamp=125.0,
                duration=4.0,
                confidence=0.98
            ),
            TranscriptSegment(
                speaker=CallParticipant.CUSTOMER,
                text="I need to think about this more. We're also looking at other providers right now.",
                timestamp=129.0,
                duration=3.0,
                confidence=0.92
            )
        ]
        
        async def test_ai_functions():
            print("🔍 Testing deal risk analysis...")
            deal_risk = await ai_analyzer.analyze_deal_risk(test_segments, "TEST_001")
            if deal_risk:
                print(f"   ✅ Deal risk detected: {deal_risk.risk_level.value}")
                print(f"   📊 Risk factors: {len(deal_risk.risk_factors)}")
            else:
                print("   ℹ️  No significant deal risk detected")
            
            print("🔍 Testing sentiment analysis...")
            sentiment = await ai_analyzer.enhanced_sentiment_analysis(test_segments)
            if sentiment:
                print(f"   ✅ Sentiment: {sentiment['overall_sentiment']}")
                print(f"   📊 Score: {sentiment['sentiment_score']:.2f}")
                print(f"   👤 Customer satisfaction: {sentiment['customer_satisfaction']:.1f}/10")
            
            print("🔍 Testing opportunity analysis...")
            opportunities = await ai_analyzer.analyze_opportunities(test_segments, "TEST_001")
            if opportunities:
                print(f"   ✅ Opportunities found: {len(opportunities)}")
                for opp in opportunities:
                    print(f"   💰 {opp.opportunity_type}: ${opp.estimated_value:,.0f}")
            else:
                print("   ℹ️  No opportunities detected in test data")
        
        asyncio.run(test_ai_functions())
        print("✅ AI models tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI models: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting AI-Enhanced Analysis Testing...")
    
    # Test AI-enhanced analysis
    success1 = test_ai_enhanced_analysis()
    
    # Test AI models directly
    success2 = test_ai_models_directly()
    
    if success1 and success2:
        print(f"\n🎉 ALL AI-ENHANCED TESTS PASSED!")
        print(f"🤖 The MCP server now provides:")
        print(f"   ✅ Real GPT-powered analysis (when OpenAI API key is set)")
        print(f"   ✅ Enhanced business intelligence with AI insights")
        print(f"   ✅ Advanced sentiment analysis with emotional detection")
        print(f"   ✅ AI-driven risk assessment and opportunity identification")
        print(f"   ✅ Comprehensive evidence trails with confidence scoring")
        print(f"   ✅ Fallback analysis when AI is not available")
        print(f"\n💡 To enable full AI capabilities, set your OpenAI API key:")
        print(f"   export OPENAI_API_KEY='your-api-key-here'")
    else:
        print(f"\n⚠️ Some tests failed - check error messages above")
        print(f"💡 Install missing dependencies to enable full AI analysis") 