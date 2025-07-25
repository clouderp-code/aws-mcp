#!/usr/bin/env python3
"""
Demonstration script for local scripts analysis functionality.
This shows how the MCP tool will process script files and generate enhanced BI reports.
"""

import json
import glob
import os
from datetime import datetime
from typing import Dict, List

def convert_script_to_segments(script_data: Dict) -> List[Dict]:
    """Convert script data to transcript segments."""
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
        
        segment = {
            "timestamp": current_timestamp,
            "speaker": speaker,
            "text": text,
            "duration": estimated_duration,
            "confidence": 0.95
        }
        
        segments.append(segment)
        current_timestamp += estimated_duration
    
    return segments

def analyze_script_mock(script_data: Dict, segments: List[Dict]) -> Dict:
    """Create a mock analysis result for a script."""
    call_id = script_data.get('call_id', 'UNKNOWN')
    
    # Extract key information
    transcript_text = ' '.join([seg['text'] for seg in segments])
    customer_segments = [seg for seg in segments if seg['speaker'] == 'customer']
    agent_segments = [seg for seg in segments if seg['speaker'] == 'agent']
    
    # Mock analysis based on text content
    analysis = {
        "call_id": call_id,
        "analysis_timestamp": datetime.now().isoformat(),
        "transcript_source": f"script_{call_id}.json",
        "transcript_segments": segments,
        "characteristics": {
            "total_duration_seconds": sum(seg['duration'] for seg in segments),
            "agent_talk_ratio": len(agent_segments) / len(segments) if segments else 0,
            "customer_talk_ratio": len(customer_segments) / len(segments) if segments else 0,
            "total_words": len(transcript_text.split()),
            "agent_words": sum(len(seg['text'].split()) for seg in agent_segments),
            "customer_words": sum(len(seg['text'].split()) for seg in customer_segments)
        },
        "sentiment_analysis": {
            "overall_sentiment": "positive" if any(word in transcript_text.lower() for word in ["good", "great", "excellent", "perfect"]) else "neutral",
            "customer_sentiment": "positive" if any(word in ' '.join([seg['text'] for seg in customer_segments]).lower() for word in ["good", "great", "thanks"]) else "neutral",
            "agent_sentiment": "positive"
        },
        "performance_kpis": {
            "customer_satisfaction_score": 8.0 if "thanks" in transcript_text.lower() else 6.5,
            "agent_professionalism_score": 8.5,
            "compliance_score": 8.0
        },
        "key_topics": {
            "primary_topics": [],
            "keywords_frequency": {}
        }
    }
    
    # Detect business signals
    text_lower = transcript_text.lower()
    
    # Deal risk indicators
    deal_risk_signals = []
    if any(word in text_lower for word in ["expensive", "cost", "price", "budget"]):
        deal_risk_signals.append("Price concerns raised")
    if any(word in text_lower for word in ["competitor", "alternative", "compare"]):
        deal_risk_signals.append("Competitor mentioned")
    
    # Churn risk signals
    churn_risk_signals = []
    if any(word in text_lower for word in ["switch", "cancel", "terminate", "frustrated"]):
        churn_risk_signals.append("Mentioned switching providers")
    if any(word in text_lower for word in ["renewal", "contract", "expire"]):
        churn_risk_signals.append("Contract renewal discussion")
    
    # Opportunity signals
    opportunity_signals = []
    if any(word in text_lower for word in ["upgrade", "expand", "additional", "more"]):
        opportunity_signals.append("Expansion interest")
    if any(word in text_lower for word in ["premium", "enterprise", "advanced"]):
        opportunity_signals.append("Premium service interest")
    
    # Training flags
    training_flags = []
    if analysis["characteristics"]["agent_talk_ratio"] > 0.8:
        training_flags.append("Excessive talking")
    
    # Quality issues
    quality_issues = []
    if analysis["characteristics"]["total_duration_seconds"] > 600:  # > 10 minutes
        quality_issues.append("Long call duration")
    
    analysis.update({
        "deal_risk_indicators": deal_risk_signals,
        "churn_risk_signals": churn_risk_signals,
        "opportunity_signals": opportunity_signals,
        "training_flags": training_flags,
        "quality_issues": quality_issues
    })
    
    return analysis

def generate_enhanced_bi_report(analysis_results: List[Dict], time_period: str = "Script Collection Analysis") -> Dict:
    """Generate enhanced business intelligence report with evidence trails."""
    
    total_calls = len(analysis_results)
    
    # Calculate quality metrics
    quality_scores = [result.get("performance_kpis", {}).get("customer_satisfaction_score", 6.0) for result in analysis_results]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    calls_with_issues = sum(1 for score in quality_scores if score < 6.0)
    
    # Identify deals at risk with evidence
    deals_at_risk = []
    for result in analysis_results:
        if result.get("deal_risk_indicators"):
            risk_evidence = []
            segments = result.get("transcript_segments", [])
            
            # Find evidence for price concerns
            for segment in segments:
                if any(word in segment["text"].lower() for word in ["expensive", "cost", "price", "budget"]):
                    risk_evidence.append({
                        "call_id": result["call_id"],
                        "transcript_source": result["transcript_source"],
                        "speaker": segment["speaker"],
                        "timestamp": segment["timestamp"],
                        "evidence_text": segment["text"],
                        "context": "Customer expressed price concerns",
                        "confidence_score": 0.9
                    })
                    break
            
            if risk_evidence:
                deals_at_risk.append({
                    "account_name": f"Account_{result['call_id']}",
                    "agent_name": f"Agent_{result['call_id']}",
                    "risk_level": "medium",
                    "risk_factors": result["deal_risk_indicators"],
                    "recommended_actions": [
                        "Provide detailed ROI analysis",
                        "Schedule follow-up call"
                    ],
                    "win_probability_change": -0.15,
                    "account_value": 25000.0,
                    "evidence": {
                        "decision_type": "deal_risk_assessment",
                        "primary_evidence": risk_evidence,
                        "supporting_evidence": [],
                        "confidence_level": 0.85,
                        "analysis_methodology": "Analyzed customer language for price objections and concerns"
                    },
                    "risk_score_breakdown": {"pricing": 0.6}
                })
    
    # Identify churn risks with evidence
    churn_risks = []
    for result in analysis_results:
        if result.get("churn_risk_signals"):
            churn_evidence = []
            segments = result.get("transcript_segments", [])
            
            for segment in segments:
                if any(word in segment["text"].lower() for word in ["switch", "cancel", "terminate"]):
                    churn_evidence.append({
                        "call_id": result["call_id"],
                        "transcript_source": result["transcript_source"],
                        "speaker": segment["speaker"],
                        "timestamp": segment["timestamp"],
                        "evidence_text": segment["text"],
                        "context": "Customer expressed switching intention",
                        "confidence_score": 0.95
                    })
                    break
            
            if churn_evidence:
                churn_risks.append({
                    "account_name": f"Account_{result['call_id']}",
                    "churn_probability": 0.7,
                    "risk_signals": result["churn_risk_signals"],
                    "intervention_urgency": "high",
                    "recommended_actions": [
                        "Immediate retention call",
                        "Prepare incentive package"
                    ],
                    "account_value_at_risk": 30000.0,
                    "evidence": {
                        "decision_type": "churn_risk_assessment",
                        "primary_evidence": churn_evidence,
                        "supporting_evidence": [],
                        "confidence_level": 0.9,
                        "analysis_methodology": "Analyzed customer language for churn signals and switching intent"
                    },
                    "churn_indicators_timeline": [
                        {
                            "timestamp": churn_evidence[0]["timestamp"],
                            "signal": "switch_intention",
                            "evidence": churn_evidence[0]["evidence_text"][:100] + "..."
                        }
                    ]
                })
    
    # Generate opportunities with evidence
    opportunities = []
    for result in analysis_results:
        if result.get("opportunity_signals"):
            opp_evidence = []
            segments = result.get("transcript_segments", [])
            
            for segment in segments:
                if any(word in segment["text"].lower() for word in ["upgrade", "expand", "additional", "more"]):
                    opp_evidence.append({
                        "call_id": result["call_id"],
                        "transcript_source": result["transcript_source"],
                        "speaker": segment["speaker"],
                        "timestamp": segment["timestamp"],
                        "evidence_text": segment["text"],
                        "context": "Customer expressed expansion interest",
                        "confidence_score": 0.8
                    })
                    break
            
            if opp_evidence:
                opportunities.append({
                    "account_name": f"Account_{result['call_id']}",
                    "opportunity_type": "expansion",
                    "estimated_value": 40000.0,
                    "confidence_level": 0.75,
                    "next_steps": [
                        "Send expansion proposal",
                        "Schedule technical consultation"
                    ],
                    "timeline": "30-45 days",
                    "evidence": {
                        "decision_type": "opportunity_identification",
                        "primary_evidence": opp_evidence,
                        "supporting_evidence": [],
                        "confidence_level": 0.75,
                        "analysis_methodology": "Analyzed customer language for expansion signals and growth indicators"
                    },
                    "opportunity_signals_strength": {"expansion": 0.8}
                })
    
    # Calculate evidence summary
    total_evidence = (
        sum(len(deal.get("evidence", {}).get("primary_evidence", [])) for deal in deals_at_risk) +
        sum(len(churn.get("evidence", {}).get("primary_evidence", [])) for churn in churn_risks) +
        sum(len(opp.get("evidence", {}).get("primary_evidence", [])) for opp in opportunities)
    )
    
    calls_with_evidence = len(set(
        [deal["evidence"]["primary_evidence"][0]["call_id"] for deal in deals_at_risk if deal.get("evidence", {}).get("primary_evidence")] +
        [churn["evidence"]["primary_evidence"][0]["call_id"] for churn in churn_risks if churn.get("evidence", {}).get("primary_evidence")] +
        [opp["evidence"]["primary_evidence"][0]["call_id"] for opp in opportunities if opp.get("evidence", {}).get("primary_evidence")]
    ))
    
    analysis_confidence = min(0.9, calls_with_evidence / total_calls) if total_calls > 0 else 0.5
    
    # Generate enhanced BI report
    bi_report = {
        "analysis_period": time_period,
        "total_calls_analyzed": total_calls,
        "analysis_timestamp": datetime.now().isoformat(),
        
        "overall_quality_summary": {
            "overall_quality_score": round(avg_quality, 1),
            "quality_trend": "stable",
            "calls_with_issues": calls_with_issues,
            "calls_with_issues_percentage": round((calls_with_issues / total_calls) * 100, 1) if total_calls > 0 else 0,
            "average_sentiment_score": round(sum(1 if r.get("sentiment_analysis", {}).get("overall_sentiment") == "positive" else 0.5 for r in analysis_results) / total_calls, 2) if total_calls > 0 else 0.5,
            "average_customer_satisfaction": round(avg_quality, 1),
            "first_call_resolution_rate": 75.0,
            "average_call_duration": round(sum(r.get("characteristics", {}).get("total_duration_seconds", 300) for r in analysis_results) / total_calls / 60, 1) if total_calls > 0 else 5.0
        },
        
        "deals_at_risk": deals_at_risk,
        "churn_risks": churn_risks,
        "new_opportunities": opportunities,
        
        "agent_training_needs": [
            {
                "agent_name": f"Agent_{result['call_id']}",
                "skill_gaps": result["training_flags"],
                "performance_metrics": {
                    "satisfaction": result.get("performance_kpis", {}).get("customer_satisfaction_score", 6.0),
                    "talk_time_ratio": result.get("characteristics", {}).get("agent_talk_ratio", 0.5)
                },
                "training_priority": "medium",
                "recommended_training": ["Active listening workshop"],
                "improvement_potential": 0.7
            }
            for result in analysis_results if result.get("training_flags")
        ],
        
        "recurring_objections": [
            {
                "objection_text": "Too expensive",
                "frequency": len([r for r in analysis_results if "Price concerns raised" in r.get("deal_risk_indicators", [])]),
                "frequency_percentage": round((len([r for r in analysis_results if "Price concerns raised" in r.get("deal_risk_indicators", [])]) / total_calls) * 100, 1) if total_calls > 0 else 0,
                "impact_on_conversion": -0.2,
                "suggested_responses": ["Focus on ROI", "Compare cost of inaction"],
                "training_materials_needed": ["ROI calculation tools"]
            }
        ],
        
        "call_quality_issues": [
            {
                "issue_type": issue,
                "frequency": len([r for r in analysis_results if issue in r.get("quality_issues", [])]),
                "affected_calls_percentage": round((len([r for r in analysis_results if issue in r.get("quality_issues", [])]) / total_calls) * 100, 1) if total_calls > 0 else 0,
                "impact_severity": "medium",
                "root_causes": ["Process inefficiencies"],
                "recommended_solutions": ["Process optimization"]
            }
            for issue in set(issue for result in analysis_results for issue in result.get("quality_issues", []))
        ],
        
        "top_priorities": [
            f"Address {len(deals_at_risk)} deals at risk - implement recovery actions",
            f"Prevent churn for {len(churn_risks)} at-risk accounts",
            f"Pursue {len(opportunities)} new opportunities"
        ],
        
        "success_indicators": [
            f"{round((sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) >= 7.0) / total_calls) * 100, 0)}% of calls achieved good satisfaction" if total_calls > 0 else "No satisfaction data",
            "Strong engagement in expansion discussions"
        ],
        
        "areas_for_improvement": [
            "Address pricing objections with value proposition",
            "Improve call efficiency and duration management"
        ],
        
        "evidence_summary": {
            "total_evidence_items": total_evidence,
            "calls_with_evidence": calls_with_evidence,
            "deal_risk_evidence": sum(len(deal.get("evidence", {}).get("primary_evidence", [])) for deal in deals_at_risk),
            "churn_risk_evidence": sum(len(churn.get("evidence", {}).get("primary_evidence", [])) for churn in churn_risks),
            "opportunity_evidence": sum(len(opp.get("evidence", {}).get("primary_evidence", [])) for opp in opportunities)
        },
        
        "analysis_confidence": round(analysis_confidence, 2),
        
        "review_recommendations": [
            "High confidence analysis - insights are well-supported by evidence" if analysis_confidence >= 0.8 else "Medium confidence analysis - review key insights",
            "Evidence trails provide full transparency for validation"
        ]
    }
    
    return bi_report

def main():
    """Main demonstration function."""
    print("🔍 Local Scripts Analysis Demonstration")
    print("=" * 50)
    
    # Find script files
    scripts_folder = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts"
    script_files = sorted(glob.glob(os.path.join(scripts_folder, "script*.json")))[:10]  # Process first 10 files
    
    print(f"📁 Found {len(glob.glob(os.path.join(scripts_folder, 'script*.json')))} script files")
    print(f"📊 Processing first {len(script_files)} files for demonstration...")
    
    # Process scripts
    analysis_results = []
    
    for script_file in script_files:
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Convert to segments
            segments = convert_script_to_segments(script_data)
            
            # Perform mock analysis
            analysis = analyze_script_mock(script_data, segments)
            analysis_results.append(analysis)
            
            print(f"✅ Processed {os.path.basename(script_file)}: {len(segments)} segments")
            
        except Exception as e:
            print(f"❌ Error processing {script_file}: {str(e)}")
    
    print(f"\n📈 Generating Enhanced Business Intelligence Report...")
    
    # Generate enhanced BI report
    bi_report = generate_enhanced_bi_report(analysis_results, "Local Scripts Demonstration")
    
    # Save to file
    output_file = os.path.join(scripts_folder, "local_analysis_demo_report.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bi_report, f, indent=2)
    
    print(f"✅ Enhanced BI report saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 Analysis Summary:")
    print(f"   • Total calls analyzed: {bi_report['total_calls_analyzed']}")
    print(f"   • Overall quality score: {bi_report['overall_quality_summary']['overall_quality_score']}/10")
    print(f"   • Deals at risk: {len(bi_report['deals_at_risk'])}")
    print(f"   • Churn risks: {len(bi_report['churn_risks'])}")
    print(f"   • New opportunities: {len(bi_report['new_opportunities'])}")
    print(f"   • Evidence items collected: {bi_report['evidence_summary']['total_evidence_items']}")
    print(f"   • Analysis confidence: {bi_report['analysis_confidence']}")
    
    print(f"\n🎯 Top Priorities:")
    for i, priority in enumerate(bi_report['top_priorities'], 1):
        print(f"   {i}. {priority}")
    
    print(f"\n✨ This demonstrates the complete workflow of the MCP tool!")
    print(f"📄 Review the generated report for full evidence trails and insights.")

if __name__ == "__main__":
    main() 