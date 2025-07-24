# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Transcript analyzer service for call analysis."""

import re
import json
from datetime import datetime
from typing import List, Dict, Any

from loguru import logger

from ..models import (
    CallAnalysisResult, TranscriptSegment, CallCharacteristics,
    SentimentAnalysis, ConversationFlow, KeyTopics, ComplianceMetrics,
    PerformanceKPIs, CallParticipant, SentimentType
)
from ..consts import (
    COMPLIANCE_KEYWORDS, PERFORMANCE_INDICATORS, COMMON_CALL_TOPICS,
    SCORING_WEIGHTS, DEFAULT_SILENCE_THRESHOLD_SECONDS
)


class TranscriptAnalyzer:
    """Service for analyzing call transcripts and generating comprehensive reports."""
    
    def __init__(self):
        """Initialize the transcript analyzer."""
        self.sentiment_analyzer = None
        self.topic_analyzer = None
        logger.info("Transcript analyzer initialized")
    
    def parse_transcript(self, transcript_content: str) -> List[TranscriptSegment]:
        """Parse transcript content into structured segments.
        
        Args:
            transcript_content: Raw transcript text
            
        Returns:
            List of transcript segments
        """
        segments = []
        
        # Try to parse different transcript formats
        if transcript_content.strip().startswith('{') or transcript_content.strip().startswith('['):
            # JSON format
            segments = self._parse_json_transcript(transcript_content)
        elif '\t' in transcript_content or ',' in transcript_content:
            # CSV/TSV format
            segments = self._parse_csv_transcript(transcript_content)
        else:
            # Plain text format
            segments = self._parse_text_transcript(transcript_content)
        
        logger.info(f"Parsed transcript into {len(segments)} segments")
        return segments
    
    def _parse_json_transcript(self, content: str) -> List[TranscriptSegment]:
        """Parse JSON format transcript."""
        try:
            data = json.loads(content)
            segments = []
            
            if isinstance(data, list):
                for item in data:
                    segments.append(TranscriptSegment(
                        timestamp=item.get('timestamp', 0.0),
                        speaker=CallParticipant(item.get('speaker', 'agent').lower()),
                        text=item.get('text', ''),
                        duration=item.get('duration', 1.0),
                        confidence=item.get('confidence')
                    ))
            
            return segments
        except Exception as e:
            logger.warning(f"Error parsing JSON transcript: {str(e)}")
            return []
    
    def _parse_csv_transcript(self, content: str) -> List[TranscriptSegment]:
        """Parse CSV/TSV format transcript."""
        segments = []
        lines = content.strip().split('\n')
        
        for i, line in enumerate(lines[1:], 1):  # Skip header
            try:
                parts = line.split('\t') if '\t' in line else line.split(',')
                if len(parts) >= 3:
                    segments.append(TranscriptSegment(
                        timestamp=float(parts[0]) if parts[0].replace('.', '').isdigit() else i * 10.0,
                        speaker=CallParticipant(parts[1].lower() if parts[1].lower() in ['agent', 'customer'] else 'agent'),
                        text=parts[2].strip('"'),
                        duration=float(parts[3]) if len(parts) > 3 and parts[3].replace('.', '').isdigit() else 5.0,
                        confidence=float(parts[4]) if len(parts) > 4 and parts[4].replace('.', '').isdigit() else None
                    ))
            except Exception as e:
                logger.warning(f"Error parsing line {i}: {str(e)}")
                continue
        
        return segments
    
    def _parse_text_transcript(self, content: str) -> List[TranscriptSegment]:
        """Parse plain text transcript."""
        segments = []
        lines = content.strip().split('\n')
        current_time = 0.0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to detect speaker patterns
            speaker_match = re.match(r'^(Agent|Customer|Rep|Caller):\s*(.+)', line, re.IGNORECASE)
            if speaker_match:
                speaker = 'agent' if speaker_match.group(1).lower() in ['agent', 'rep'] else 'customer'
                text = speaker_match.group(2)
            else:
                # Default to agent if no speaker detected
                speaker = 'agent'
                text = line
            
            # Estimate duration based on text length
            duration = max(2.0, len(text.split()) / 3.0)  # Assume ~3 words per second
            
            segments.append(TranscriptSegment(
                timestamp=current_time,
                speaker=CallParticipant(speaker),
                text=text,
                duration=duration,
                confidence=None
            ))
            
            current_time += duration + 1.0  # Add pause between segments
        
        return segments
    
    def analyze_transcript(
        self,
        transcript_segments: List[TranscriptSegment],
        call_id: str,
        analysis_options: Dict[str, bool]
    ) -> CallAnalysisResult:
        """Perform comprehensive analysis of transcript segments.
        
        Args:
            transcript_segments: Parsed transcript segments
            call_id: Unique identifier for the call
            analysis_options: Analysis options to enable/disable
            
        Returns:
            Complete analysis result
        """
        logger.info(f"Starting analysis for call {call_id}")
        
        # Calculate basic characteristics
        characteristics = self._analyze_characteristics(transcript_segments)
        
        # Perform sentiment analysis
        sentiment_analysis = self._analyze_sentiment(transcript_segments) if analysis_options.get('sentiment_analysis', True) else None
        
        # Analyze conversation flow
        conversation_flow = self._analyze_conversation_flow(transcript_segments) if analysis_options.get('detailed_flow_analysis', True) else None
        
        # Extract key topics
        key_topics = self._extract_topics(transcript_segments) if analysis_options.get('topic_extraction', True) else None
        
        # Check compliance
        compliance_metrics = self._check_compliance(transcript_segments) if analysis_options.get('compliance_check', True) else None
        
        # Calculate performance KPIs
        performance_kpis = self._calculate_performance_kpis(transcript_segments, sentiment_analysis) if analysis_options.get('performance_metrics', True) else None
        
        # Generate summary and recommendations
        executive_summary = self._generate_executive_summary(characteristics, sentiment_analysis, performance_kpis, compliance_metrics)
        recommendations = self._generate_recommendations(sentiment_analysis, performance_kpis, compliance_metrics)
        action_items = self._generate_action_items(performance_kpis, compliance_metrics)
        
        result = CallAnalysisResult(
            call_id=call_id,
            analysis_timestamp=datetime.now(),
            transcript_source="",  # Will be set by calling code
            transcript_segments=transcript_segments,
            characteristics=characteristics,
            sentiment_analysis=sentiment_analysis,
            conversation_flow=conversation_flow,
            key_topics=key_topics,
            compliance_metrics=compliance_metrics,
            performance_kpis=performance_kpis,
            executive_summary=executive_summary,
            recommendations=recommendations,
            action_items=action_items,
            processing_time_seconds=0.0  # Will be set by calling code
        )
        
        logger.info(f"Analysis completed for call {call_id}")
        return result
    
    def _analyze_characteristics(self, segments: List[TranscriptSegment]) -> CallCharacteristics:
        """Analyze basic call characteristics."""
        total_duration = sum(s.duration for s in segments)
        agent_duration = sum(s.duration for s in segments if s.speaker == CallParticipant.AGENT)
        customer_duration = sum(s.duration for s in segments if s.speaker == CallParticipant.CUSTOMER)
        
        total_words = sum(len(s.text.split()) for s in segments)
        agent_words = sum(len(s.text.split()) for s in segments if s.speaker == CallParticipant.AGENT)
        customer_words = sum(len(s.text.split()) for s in segments if s.speaker == CallParticipant.CUSTOMER)
        
        # Simple interruption detection
        interruptions_by_agent = 0
        interruptions_by_customer = 0
        
        for i in range(1, len(segments)):
            prev_speaker = segments[i-1].speaker
            curr_speaker = segments[i].speaker
            if prev_speaker != curr_speaker and segments[i-1].duration < 3.0:  # Quick turn-taking
                if curr_speaker == CallParticipant.AGENT:
                    interruptions_by_agent += 1
                else:
                    interruptions_by_customer += 1
        
        return CallCharacteristics(
            total_duration_seconds=total_duration,
            agent_talk_time_seconds=agent_duration,
            customer_talk_time_seconds=customer_duration,
            silence_duration_seconds=max(0, total_duration - agent_duration - customer_duration),
            agent_talk_ratio=agent_duration / total_duration if total_duration > 0 else 0,
            customer_talk_ratio=customer_duration / total_duration if total_duration > 0 else 0,
            total_words=total_words,
            agent_words=agent_words,
            customer_words=customer_words,
            interruptions_by_agent=interruptions_by_agent,
            interruptions_by_customer=interruptions_by_customer,
            speaking_rate_agent_wpm=(agent_words / (agent_duration / 60)) if agent_duration > 0 else 0,
            speaking_rate_customer_wpm=(customer_words / (customer_duration / 60)) if customer_duration > 0 else 0
        )
    
    def _analyze_sentiment(self, segments: List[TranscriptSegment]) -> SentimentAnalysis:
        """Analyze sentiment using basic keyword-based approach."""
        
        # Combine all text for overall analysis
        all_text = ' '.join(s.text for s in segments).lower()
        agent_text = ' '.join(s.text for s in segments if s.speaker == CallParticipant.AGENT).lower()
        customer_text = ' '.join(s.text for s in segments if s.speaker == CallParticipant.CUSTOMER).lower()
        
        def simple_sentiment_score(text: str) -> Dict[str, float]:
            positive_words = len([word for word in PERFORMANCE_INDICATORS['positive_phrases'] if word in text])
            negative_words = len([word for word in PERFORMANCE_INDICATORS['negative_phrases'] if word in text])
            
            total_sentiment_words = positive_words + negative_words
            if total_sentiment_words == 0:
                return {'positive': 0.5, 'negative': 0.3, 'neutral': 0.7}
            
            pos_score = positive_words / total_sentiment_words
            neg_score = negative_words / total_sentiment_words
            neu_score = 1.0 - pos_score - neg_score
            
            return {'positive': pos_score, 'negative': neg_score, 'neutral': neu_score}
        
        overall_scores = simple_sentiment_score(all_text)
        
        # Determine overall sentiment
        if overall_scores['positive'] > overall_scores['negative']:
            overall_sentiment = SentimentType.POSITIVE
        elif overall_scores['negative'] > overall_scores['positive']:
            overall_sentiment = SentimentType.NEGATIVE
        else:
            overall_sentiment = SentimentType.NEUTRAL
        
        # Simple agent/customer sentiment
        agent_sentiment = SentimentType.POSITIVE if 'thank' in agent_text or 'help' in agent_text else SentimentType.NEUTRAL
        customer_sentiment = SentimentType.NEGATIVE if any(word in customer_text for word in ['frustrated', 'angry', 'upset']) else SentimentType.NEUTRAL
        
        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            agent_sentiment=agent_sentiment,
            customer_sentiment=customer_sentiment,
            sentiment_scores=overall_scores,
            sentiment_over_time=[],  # Simplified for now
            emotional_peaks=[],     # Simplified for now
            sentiment_transitions=0  # Simplified for now
        )
    
    def _analyze_conversation_flow(self, segments: List[TranscriptSegment]) -> ConversationFlow:
        """Analyze conversation flow and structure."""
        
        # Calculate turn-taking frequency
        speaker_changes = sum(1 for i in range(1, len(segments)) if segments[i].speaker != segments[i-1].speaker)
        turn_taking_frequency = len(segments) / speaker_changes if speaker_changes > 0 else 0
        
        # Simple opening/closing quality assessment
        opening_text = ' '.join(s.text for s in segments[:3]).lower()
        closing_text = ' '.join(s.text for s in segments[-3:]).lower()
        
        opening_score = 8.0 if any(phrase in opening_text for phrase in ['thank you for calling', 'how can I help']) else 5.0
        closing_score = 8.0 if any(phrase in closing_text for phrase in ['thank you', 'have a great day', 'anything else']) else 5.0
        
        return ConversationFlow(
            turn_taking_frequency=turn_taking_frequency,
            conversation_segments=[],  # Simplified for now
            opening_quality_score=opening_score,
            closing_quality_score=closing_score,
            topic_changes=0,  # Simplified for now
            agenda_adherence_score=7.0  # Default score
        )
    
    def _extract_topics(self, segments: List[TranscriptSegment]) -> KeyTopics:
        """Extract key topics and themes."""
        
        all_text = ' '.join(s.text for s in segments).lower()
        
        # Simple topic detection based on keywords
        detected_topics = []
        for topic, keywords in COMMON_CALL_TOPICS.items():
            if any(keyword in all_text for keyword in keywords):
                detected_topics.append(topic.replace('_', ' ').title())
        
        # Extract common words as keywords
        words = all_text.split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only consider longer words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        top_keywords = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return KeyTopics(
            primary_topics=detected_topics[:3] if detected_topics else ['General Inquiry'],
            secondary_topics=detected_topics[3:] if len(detected_topics) > 3 else [],
            keywords_frequency=top_keywords,
            named_entities=[],  # Simplified for now
            business_intent='Customer Support' if 'support' in all_text else 'General Inquiry',
            call_outcome='Resolved' if any(word in all_text for word in ['resolved', 'fixed', 'solved']) else 'In Progress'
        )
    
    def _check_compliance(self, segments: List[TranscriptSegment]) -> ComplianceMetrics:
        """Check compliance requirements."""
        
        all_text = ' '.join(s.text for s in segments).lower()
        
        # Check for required disclosures
        disclosures_made = []
        missing_disclosures = []
        
        for disclosure_type, keywords in COMPLIANCE_KEYWORDS.items():
            if any(keyword in all_text for keyword in keywords):
                disclosures_made.append(disclosure_type.replace('_', ' ').title())
            else:
                missing_disclosures.append(disclosure_type.replace('_', ' ').title())
        
        # Simple compliance scoring
        total_checks = len(COMPLIANCE_KEYWORDS)
        passed_checks = len(disclosures_made)
        compliance_score = (passed_checks / total_checks) * 10 if total_checks > 0 else 7.0
        
        return ComplianceMetrics(
            compliance_score=compliance_score,
            required_disclosures_made=disclosures_made,
            missing_disclosures=missing_disclosures,
            escalation_offered=any(word in all_text for word in ['escalate', 'supervisor', 'manager']),
            hold_time_appropriate=True,  # Simplified for now
            privacy_compliance='privacy' in all_text,
            security_compliance='secure' in all_text or 'security' in all_text
        )
    
    def _calculate_performance_kpis(self, segments: List[TranscriptSegment], sentiment: SentimentAnalysis) -> PerformanceKPIs:
        """Calculate performance KPIs."""
        
        agent_text = ' '.join(s.text for s in segments if s.speaker == CallParticipant.AGENT).lower()
        all_text = ' '.join(s.text for s in segments).lower()
        
        # Calculate various scores based on keyword presence
        empathy_score = 8.0 if any(phrase in agent_text for phrase in PERFORMANCE_INDICATORS['empathy_phrases']) else 5.0
        professionalism_score = 8.0 if any(phrase in agent_text for phrase in PERFORMANCE_INDICATORS['professionalism_phrases']) else 6.0
        
        # Customer satisfaction estimation
        if sentiment and sentiment.customer_sentiment == SentimentType.POSITIVE:
            customer_satisfaction = 8.5
        elif sentiment and sentiment.customer_sentiment == SentimentType.NEGATIVE:
            customer_satisfaction = 4.0
        else:
            customer_satisfaction = 6.5
        
        # Issue resolution detection
        resolution_keywords = ['resolved', 'fixed', 'solved', 'completed', 'done']
        first_call_resolution = any(keyword in all_text for keyword in resolution_keywords)
        
        total_duration = sum(s.duration for s in segments)
        
        return PerformanceKPIs(
            customer_satisfaction_score=customer_satisfaction,
            first_call_resolution=first_call_resolution,
            agent_professionalism_score=professionalism_score,
            agent_knowledge_score=7.0,  # Default score
            agent_empathy_score=empathy_score,
            call_efficiency_score=8.0 if total_duration < 600 else 6.0,  # 10 minutes threshold
            issue_resolution_time=total_duration,
            clarity_score=7.5,  # Default score
            active_listening_score=7.0   # Default score
        )
    
    def _generate_executive_summary(self, characteristics, sentiment, performance, compliance) -> str:
        """Generate executive summary."""
        duration_mins = characteristics.total_duration_seconds / 60
        
        summary = f"Call Duration: {duration_mins:.1f} minutes. "
        
        if sentiment:
            summary += f"Overall sentiment was {sentiment.overall_sentiment.value}. "
        
        if performance:
            summary += f"Customer satisfaction score: {performance.customer_satisfaction_score:.1f}/10. "
            if performance.first_call_resolution:
                summary += "Issue was resolved on first call. "
        
        if compliance:
            summary += f"Compliance score: {compliance.compliance_score:.1f}/10. "
        
        return summary
    
    def _generate_recommendations(self, sentiment, performance, compliance) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        if performance and performance.customer_satisfaction_score < 7.0:
            recommendations.append("Focus on improving customer satisfaction through better active listening and empathy")
        
        if compliance and compliance.compliance_score < 7.0:
            recommendations.append("Ensure all required disclosures are made during calls")
        
        if sentiment and sentiment.customer_sentiment == SentimentType.NEGATIVE:
            recommendations.append("Implement additional de-escalation techniques for upset customers")
        
        if not recommendations:
            recommendations.append("Continue current approach, performance is meeting expectations")
        
        return recommendations
    
    def _generate_action_items(self, performance, compliance) -> List[str]:
        """Generate action items."""
        action_items = []
        
        if compliance and len(compliance.missing_disclosures) > 0:
            action_items.append(f"Address missing disclosures: {', '.join(compliance.missing_disclosures)}")
        
        if performance and not performance.first_call_resolution:
            action_items.append("Follow up with customer to ensure issue resolution")
        
        return action_items
    
    def generate_markdown_report(self, analysis: CallAnalysisResult) -> str:
        """Generate markdown report from analysis results."""
        
        md_content = f"""# Call Analysis Report - {analysis.call_id}

**Analysis Date:** {analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Call Duration:** {analysis.characteristics.total_duration_seconds / 60:.1f} minutes  
**Processing Time:** {analysis.processing_time_seconds:.2f} seconds

## Executive Summary

{analysis.executive_summary}

## Key Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Customer Satisfaction | {analysis.performance_kpis.customer_satisfaction_score:.1f}/10 | {'✅ Good' if analysis.performance_kpis.customer_satisfaction_score >= 7 else '⚠️ Needs Improvement'} |
| Compliance Score | {analysis.compliance_metrics.compliance_score:.1f}/10 | {'✅ Pass' if analysis.compliance_metrics.compliance_score >= 7 else '❌ Fail'} |
| Agent Professionalism | {analysis.performance_kpis.agent_professionalism_score:.1f}/10 | {'✅ Good' if analysis.performance_kpis.agent_professionalism_score >= 7 else '⚠️ Needs Improvement'} |
| First Call Resolution | {'Yes' if analysis.performance_kpis.first_call_resolution else 'No'} | {'✅' if analysis.performance_kpis.first_call_resolution else '❌'} |

## Conversation Analysis

**Overall Sentiment:** {analysis.sentiment_analysis.overall_sentiment.value.title()}  
**Agent Talk Ratio:** {analysis.characteristics.agent_talk_ratio:.1%}  
**Customer Talk Ratio:** {analysis.characteristics.customer_talk_ratio:.1%}  

## Key Topics Discussed

{chr(10).join(f'- {topic}' for topic in analysis.key_topics.primary_topics)}

## Recommendations

{chr(10).join(f'- {rec}' for rec in analysis.recommendations)}

## Action Items

{chr(10).join(f'- {item}' for item in analysis.action_items)}

---
*Generated by Call Analysis MCP Server v{analysis.analysis_version}*
"""
        
        return md_content
    
    def generate_batch_summary(self, successful_results: List[Dict]) -> Dict:
        """Generate batch analysis summary."""
        if not successful_results:
            return {}
        
        total_calls = len(successful_results)
        avg_satisfaction = sum(r['summary']['satisfaction'] for r in successful_results) / total_calls
        avg_compliance = sum(r['summary']['compliance'] for r in successful_results) / total_calls
        avg_duration = sum(r['summary']['duration'] for r in successful_results) / total_calls
        
        sentiment_counts = {}
        for result in successful_results:
            sentiment = result['summary']['sentiment']
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        return {
            'total_calls_analyzed': total_calls,
            'average_customer_satisfaction': round(avg_satisfaction, 2),
            'average_compliance_score': round(avg_compliance, 2),
            'average_call_duration_minutes': round(avg_duration / 60, 2),
            'sentiment_distribution': sentiment_counts,
            'high_satisfaction_calls': sum(1 for r in successful_results if r['summary']['satisfaction'] >= 8.0),
            'compliance_failures': sum(1 for r in successful_results if r['summary']['compliance'] < 7.0)
        }
    
    def generate_batch_report_markdown(self, batch_summary: Dict, results: List[Dict]) -> str:
        """Generate batch analysis markdown report."""
        
        md_content = f"""# Batch Call Analysis Report

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Calls Processed:** {batch_summary.get('total_calls_analyzed', 0)}

## Summary Statistics

| Metric | Value |
|--------|-------|
| Average Customer Satisfaction | {batch_summary.get('average_customer_satisfaction', 0):.1f}/10 |
| Average Compliance Score | {batch_summary.get('average_compliance_score', 0):.1f}/10 |
| Average Call Duration | {batch_summary.get('average_call_duration_minutes', 0):.1f} minutes |
| High Satisfaction Calls | {batch_summary.get('high_satisfaction_calls', 0)} |
| Compliance Failures | {batch_summary.get('compliance_failures', 0)} |

## Sentiment Distribution

{chr(10).join(f'- **{sentiment.title()}:** {count} calls' for sentiment, count in batch_summary.get('sentiment_distribution', {}).items())}

## Individual Call Results

| Call ID | Status | Satisfaction | Compliance | Duration |
|---------|--------|-------------|------------|----------|
{chr(10).join(f"| {r['call_id']} | {r['status']} | {r.get('summary', {}).get('satisfaction', 'N/A')} | {r.get('summary', {}).get('compliance', 'N/A')} | {r.get('summary', {}).get('duration', 0)/60:.1f}m |" for r in results[:20])}

---
*Generated by Call Analysis MCP Server*
"""
        
        return md_content 