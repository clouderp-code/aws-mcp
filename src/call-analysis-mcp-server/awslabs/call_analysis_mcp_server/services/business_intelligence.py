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

"""Business intelligence analyzer for generating actionable insights from call data."""

import re
from datetime import datetime
from typing import List, Dict, Any

from loguru import logger

from ..models import (
    BusinessIntelligenceInsights, DealRiskIndicator, ChurnRiskIndicator,
    OpportunityIndicator, AgentTrainingNeed, PipelineHealthIndicator,
    ObjectionPattern, CallQualityIssue, RiskLevel, SentimentType,
    TranscriptEvidence, DecisionEvidence, CallParticipant, TranscriptSegment
)
from .ai_analyzer import AIAnalyzer


class BusinessIntelligenceAnalyzer:
    """Service for generating business intelligence insights from call analysis data with full evidence trails."""
    
    def __init__(self):
        """Initialize the business intelligence analyzer."""
        self.ai_analyzer = AIAnalyzer()  # Initialize AI-powered analyzer
        logger.info("Business intelligence analyzer initialized with AI capabilities and evidence tracking")
    
    async def generate_insights(
        self,
        analysis_results: List[Dict[str, Any]],
        time_period: str = "Today"
    ) -> BusinessIntelligenceInsights:
        """
        Generate comprehensive business intelligence insights from analysis results with full evidence trails.
        
        Args:
            analysis_results: List of call analysis result dictionaries
            time_period: Description of the time period analyzed
            
        Returns:
            BusinessIntelligenceInsights object with actionable insights and supporting evidence
        """
        logger.info(f"Generating business intelligence insights with evidence for {len(analysis_results)} calls")
        
        # Basic metrics
        total_calls = len(analysis_results)
        
        # Quality assessment
        quality_metrics = self._analyze_quality_metrics(analysis_results)
        
        # Risk and opportunity identification with AI-enhanced evidence
        deals_at_risk = await self._identify_deals_at_risk_with_ai_evidence(analysis_results)
        churn_risks = await self._identify_churn_risks_with_ai_evidence(analysis_results)
        opportunities = await self._identify_opportunities_with_ai_evidence(analysis_results)
        
        # Performance insights with evidence
        training_needs = self._identify_training_needs_with_evidence(analysis_results)
        pipeline_health = self._analyze_pipeline_health_with_evidence(analysis_results)
        objection_patterns = self._analyze_objection_patterns_with_evidence(analysis_results)
        
        # Quality issues with evidence
        quality_issues = self._identify_quality_issues_with_evidence(analysis_results)
        
        # Aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(analysis_results)
        
        # Generate actionable insights
        top_priorities = self._generate_top_priorities(
            deals_at_risk, churn_risks, training_needs, quality_issues
        )
        success_indicators = self._identify_success_indicators(analysis_results)
        improvement_areas = self._identify_improvement_areas(
            quality_metrics, training_needs, objection_patterns
        )
        
        # Calculate evidence summary and confidence
        evidence_summary = self._calculate_evidence_summary(
            deals_at_risk, churn_risks, opportunities, training_needs, objection_patterns, quality_issues
        )
        analysis_confidence = self._calculate_analysis_confidence(evidence_summary, total_calls)
        review_recommendations = self._generate_review_recommendations(analysis_confidence, evidence_summary)
        
        return BusinessIntelligenceInsights(
            analysis_period=time_period,
            total_calls_analyzed=total_calls,
            analysis_timestamp=datetime.now(),
            
            overall_quality_score=quality_metrics["overall_score"],
            quality_trend=quality_metrics["trend"],
            calls_with_issues=quality_metrics["calls_with_issues"],
            calls_with_issues_percentage=quality_metrics["issues_percentage"],
            
            deals_at_risk=deals_at_risk,
            churn_risks=churn_risks,
            new_opportunities=opportunities,
            
            agent_training_needs=training_needs,
            pipeline_health=pipeline_health,
            recurring_objections=objection_patterns,
            
            call_quality_issues=quality_issues,
            
            average_sentiment_score=aggregate_metrics["avg_sentiment"],
            average_customer_satisfaction=aggregate_metrics["avg_satisfaction"],
            first_call_resolution_rate=aggregate_metrics["fcr_rate"],
            average_call_duration=aggregate_metrics["avg_duration"],
            
            top_priorities=top_priorities,
            success_indicators=success_indicators,
            areas_for_improvement=improvement_areas,
            
            evidence_summary=evidence_summary,
            analysis_confidence=analysis_confidence,
            review_recommendations=review_recommendations
        )
    
    def _extract_transcript_evidence(
        self,
        result: Dict[str, Any],
        keywords: List[str],
        speaker_filter: str = None,
        context: str = ""
    ) -> List[TranscriptEvidence]:
        """Extract evidence from transcript segments based on keywords."""
        
        evidence_list = []
        call_id = result.get("call_id", "Unknown")
        transcript_source = result.get("transcript_source", "Unknown")
        transcript_segments = result.get("transcript_segments", [])
        
        for segment in transcript_segments:
            segment_text = segment.get("text", "").lower()
            segment_speaker = segment.get("speaker", "unknown")
            
            # Check if any keywords match and speaker filter (if specified)
            if speaker_filter and segment_speaker != speaker_filter:
                continue
                
            for keyword in keywords:
                if keyword.lower() in segment_text:
                    evidence = TranscriptEvidence(
                        call_id=call_id,
                        transcript_source=transcript_source,
                        speaker=CallParticipant(segment_speaker) if segment_speaker in ["agent", "customer"] else CallParticipant.SYSTEM,
                        timestamp=segment.get("timestamp"),
                        evidence_text=segment.get("text", ""),
                        context=context or f"Contains keyword '{keyword}'",
                        confidence_score=0.8  # Base confidence, could be enhanced with NLP scoring
                    )
                    evidence_list.append(evidence)
                    break  # Only add once per segment
        
        return evidence_list
    
    def _create_decision_evidence(
        self,
        evidence_list: List[TranscriptEvidence],
        decision_type: str,
        methodology: str
    ) -> DecisionEvidence:
        """Create a DecisionEvidence object from a list of transcript evidence."""
        
        if not evidence_list:
            return DecisionEvidence(
                decision_type=decision_type,
                primary_evidence=[],
                supporting_evidence=[],
                confidence_level=0.1,
                analysis_methodology=methodology
            )
        
        # Sort evidence by confidence and take strongest as primary
        sorted_evidence = sorted(evidence_list, key=lambda x: x.confidence_score, reverse=True)
        primary_count = min(3, len(sorted_evidence))  # Top 3 as primary evidence
        
        primary_evidence = sorted_evidence[:primary_count]
        supporting_evidence = sorted_evidence[primary_count:]
        
        # Calculate overall confidence
        if primary_evidence:
            confidence_level = sum(e.confidence_score for e in primary_evidence) / len(primary_evidence)
        else:
            confidence_level = 0.1
        
        return DecisionEvidence(
            decision_type=decision_type,
            primary_evidence=primary_evidence,
            supporting_evidence=supporting_evidence,
            confidence_level=confidence_level,
            analysis_methodology=methodology
        )
    
    def _analyze_quality_metrics(self, analysis_results: List[Dict]) -> Dict[str, Any]:
        """Analyze overall call quality metrics."""
        
        quality_scores = []
        issues_count = 0
        
        for result in analysis_results:
            # Calculate overall quality score from components
            performance = result.get("performance_kpis", {})
            compliance = result.get("compliance_metrics", {})
            
            satisfaction = performance.get("customer_satisfaction_score", 5.0)
            compliance_score = compliance.get("compliance_score", 5.0)
            
            overall_quality = (satisfaction + compliance_score) / 2
            quality_scores.append(overall_quality)
            
            # Count calls with issues
            if overall_quality < 6.0:
                issues_count += 1
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        issues_percentage = (issues_count / len(analysis_results)) * 100 if analysis_results else 0
        
        # Simple trend analysis (placeholder - could be enhanced with historical data)
        trend = "stable"
        if avg_quality >= 8.0:
            trend = "improving"
        elif avg_quality < 6.0:
            trend = "declining"
        
        return {
            "overall_score": round(avg_quality, 1),
            "trend": trend,
            "calls_with_issues": issues_count,
            "issues_percentage": round(issues_percentage, 1)
        }
    
    def _identify_deals_at_risk_with_evidence(self, analysis_results: List[Dict]) -> List[DealRiskIndicator]:
        """Identify deals that may be at risk based on call analysis with supporting evidence."""
        
        at_risk_deals = []
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            sentiment = result.get("sentiment_analysis", {})
            performance = result.get("performance_kpis", {})
            topics = result.get("key_topics", {})
            
            # Risk indicators
            risk_factors = []
            risk_level = RiskLevel.LOW
            evidence_list = []
            risk_scores = {}
            
            # Check sentiment with evidence
            if sentiment.get("customer_sentiment") == "negative":
                risk_factors.append("Negative customer sentiment")
                risk_level = RiskLevel.MEDIUM
                risk_scores["sentiment"] = 0.7
                
                # Find evidence of negative sentiment
                sentiment_evidence = self._extract_transcript_evidence(
                    result, 
                    ["frustrated", "disappointed", "unhappy", "concerned", "worried"],
                    speaker_filter="customer",
                    context="Customer expressed negative sentiment"
                )
                evidence_list.extend(sentiment_evidence)
            
            # Check satisfaction with evidence
            satisfaction = performance.get("customer_satisfaction_score", 10)
            if satisfaction < 5.0:
                risk_factors.append("Low customer satisfaction")
                risk_level = RiskLevel.HIGH
                risk_scores["satisfaction"] = 0.9
                
                # Find evidence of satisfaction issues
                satisfaction_evidence = self._extract_transcript_evidence(
                    result,
                    ["not satisfied", "disappointed", "expected better", "not meeting"],
                    speaker_filter="customer",
                    context="Customer expressed dissatisfaction"
                )
                evidence_list.extend(satisfaction_evidence)
            
            # Check for price objections with evidence
            keywords = topics.get("keywords_frequency", {})
            if any(word in keywords for word in ["expensive", "cost", "price", "budget"]):
                risk_factors.append("Price concerns raised")
                if risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                risk_scores["pricing"] = 0.6
                
                # Find evidence of price objections
                price_evidence = self._extract_transcript_evidence(
                    result,
                    ["too expensive", "can't afford", "budget", "cost", "price", "cheaper"],
                    speaker_filter="customer",
                    context="Customer expressed price concerns"
                )
                evidence_list.extend(price_evidence)
            
            # Check for competitor mentions with evidence
            primary_topics = topics.get("primary_topics", [])
            if any("competitor" in topic.lower() for topic in primary_topics):
                risk_factors.append("Competitor mentioned")
                risk_level = RiskLevel.MEDIUM
                risk_scores["competition"] = 0.5
                
                # Find evidence of competitor mentions
                competitor_evidence = self._extract_transcript_evidence(
                    result,
                    ["competitor", "other provider", "alternative", "comparing", "switch"],
                    context="Customer mentioned competitors or alternatives"
                )
                evidence_list.extend(competitor_evidence)
            
            # Only flag if there are actual risk factors
            if risk_factors:
                # Create decision evidence
                decision_evidence = self._create_decision_evidence(
                    evidence_list,
                    "deal_risk_assessment",
                    "Analyzed customer sentiment, satisfaction scores, price objections, and competitor mentions"
                )
                
                # Estimate win probability change
                win_prob_change = -0.1 * len(risk_factors)
                
                at_risk_deals.append(DealRiskIndicator(
                    account_name=f"Account_{call_id}",
                    agent_name=f"Agent_{call_id}",
                    risk_level=risk_level,
                    risk_factors=risk_factors,
                    recommended_actions=self._generate_risk_mitigation_actions(risk_factors),
                    win_probability_change=win_prob_change,
                    account_value=15000.0,  # Placeholder value
                    evidence=decision_evidence,
                    risk_score_breakdown=risk_scores
                ))
        
        return at_risk_deals[:5]  # Return top 5 at-risk deals
    
    def _identify_churn_risks_with_evidence(self, analysis_results: List[Dict]) -> List[ChurnRiskIndicator]:
        """Identify accounts at risk of churning with supporting evidence."""
        
        churn_risks = []
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            sentiment = result.get("sentiment_analysis", {})
            topics = result.get("key_topics", {})
            
            # Churn risk signals
            risk_signals = []
            churn_probability = 0.1  # Base probability
            evidence_list = []
            timeline = []
            
            # Check for churn-related phrases with evidence
            keywords = topics.get("keywords_frequency", {})
            if any(word in keywords for word in ["switch", "cancel", "terminate", "frustrated"]):
                risk_signals.append("Mentioned switching providers")
                churn_probability += 0.3
                
                # Find evidence of switching intentions
                switch_evidence = self._extract_transcript_evidence(
                    result,
                    ["switch", "cancel", "terminate", "end contract", "frustrated"],
                    speaker_filter="customer",
                    context="Customer expressed intention to switch or cancel"
                )
                evidence_list.extend(switch_evidence)
                
                # Add to timeline
                for evidence in switch_evidence:
                    timeline.append({
                        "timestamp": evidence.timestamp or 0,
                        "signal": "switch_intention",
                        "evidence": evidence.evidence_text[:100] + "..."
                    })
            
            if any(word in keywords for word in ["renewal", "contract", "expire"]):
                risk_signals.append("Contract renewal discussion")
                churn_probability += 0.2
                
                # Find evidence of renewal concerns
                renewal_evidence = self._extract_transcript_evidence(
                    result,
                    ["renewal", "contract", "expire", "renew", "extend"],
                    context="Customer discussed contract renewal"
                )
                evidence_list.extend(renewal_evidence)
            
            # Check customer sentiment with evidence
            if sentiment.get("customer_sentiment") == "negative":
                risk_signals.append("Negative customer sentiment")
                churn_probability += 0.2
                
                # Find evidence of negative sentiment (already implemented above)
                sentiment_evidence = self._extract_transcript_evidence(
                    result,
                    ["frustrated", "disappointed", "unhappy", "unsatisfied"],
                    speaker_filter="customer",
                    context="Customer expressed negative sentiment"
                )
                evidence_list.extend(sentiment_evidence)
            
            # Only flag if churn probability is significant
            if churn_probability > 0.3:
                urgency = RiskLevel.HIGH if churn_probability > 0.6 else RiskLevel.MEDIUM
                
                # Create decision evidence
                decision_evidence = self._create_decision_evidence(
                    evidence_list,
                    "churn_risk_assessment",
                    "Analyzed customer language for churn signals, renewal discussions, and sentiment"
                )
                
                churn_risks.append(ChurnRiskIndicator(
                    account_name=f"Account_{call_id}",
                    churn_probability=min(churn_probability, 1.0),
                    risk_signals=risk_signals,
                    intervention_urgency=urgency,
                    recommended_actions=self._generate_retention_actions(risk_signals),
                    account_value_at_risk=18000.0,  # Placeholder value
                    evidence=decision_evidence,
                    churn_indicators_timeline=timeline
                ))
        
        return churn_risks[:3]  # Return top 3 churn risks
    
    def _identify_opportunities_with_evidence(self, analysis_results: List[Dict]) -> List[OpportunityIndicator]:
        """Identify new business opportunities with supporting evidence."""
        
        opportunities = []
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            topics = result.get("key_topics", {})
            sentiment = result.get("sentiment_analysis", {})
            
            # Look for opportunity signals with evidence
            keywords = topics.get("keywords_frequency", {})
            opportunity_signals = []
            evidence_list = []
            signal_strengths = {}
            
            if any(word in keywords for word in ["upgrade", "expand", "additional", "more"]):
                opportunity_signals.append("Expansion interest")
                signal_strengths["expansion"] = 0.8
                
                # Find evidence of expansion interest
                expansion_evidence = self._extract_transcript_evidence(
                    result,
                    ["upgrade", "expand", "additional", "more", "grow", "increase"],
                    speaker_filter="customer",
                    context="Customer expressed interest in expansion or upgrades"
                )
                evidence_list.extend(expansion_evidence)
            
            if any(word in keywords for word in ["premium", "enterprise", "advanced"]):
                opportunity_signals.append("Premium service interest")
                signal_strengths["premium"] = 0.7
                
                # Find evidence of premium interest
                premium_evidence = self._extract_transcript_evidence(
                    result,
                    ["premium", "enterprise", "advanced", "high-end", "top tier"],
                    speaker_filter="customer",
                    context="Customer expressed interest in premium services"
                )
                evidence_list.extend(premium_evidence)
            
            if any(word in keywords for word in ["new", "location", "office", "site"]):
                opportunity_signals.append("Multi-location opportunity")
                signal_strengths["multi_location"] = 0.6
                
                # Find evidence of multi-location needs
                location_evidence = self._extract_transcript_evidence(
                    result,
                    ["new location", "office", "site", "branch", "facility"],
                    speaker_filter="customer",
                    context="Customer mentioned new locations or facilities"
                )
                evidence_list.extend(location_evidence)
            
            # Only create opportunity if there are positive signals
            if opportunity_signals and sentiment.get("overall_sentiment") != "negative":
                # Create decision evidence
                decision_evidence = self._create_decision_evidence(
                    evidence_list,
                    "opportunity_identification",
                    "Analyzed customer language for expansion signals, premium interest, and growth indicators"
                )
                
                # Estimate opportunity value based on signals
                base_value = 15000
                value_multiplier = len(opportunity_signals) * 0.5
                estimated_value = base_value * (1 + value_multiplier)
                
                opportunities.append(OpportunityIndicator(
                    account_name=f"Account_{call_id}",
                    opportunity_type="upsell" if "upgrade" in str(opportunity_signals) else "expansion",
                    estimated_value=estimated_value,
                    confidence_level=decision_evidence.confidence_level,
                    next_steps=[
                        "Schedule follow-up call",
                        "Send detailed proposal",
                        "Arrange product demo"
                    ],
                    timeline="30-45 days",
                    evidence=decision_evidence,
                    opportunity_signals_strength=signal_strengths
                ))
        
        return opportunities[:5]  # Return top 5 opportunities
    
    def _identify_training_needs_with_evidence(self, analysis_results: List[Dict]) -> List[AgentTrainingNeed]:
        """Identify agent training needs with supporting evidence."""
        
        # Group by agent (simplified - using call_id as proxy)
        agent_performance = {}
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            agent_name = f"Agent_{call_id}"
            performance = result.get("performance_kpis", {})
            characteristics = result.get("characteristics", {})
            
            if agent_name not in agent_performance:
                agent_performance[agent_name] = {
                    "scores": [],
                    "issues": [],
                    "talk_ratios": [],
                    "evidence": [],
                    "results": []
                }
            
            # Collect performance data
            agent_performance[agent_name]["scores"].append({
                "satisfaction": performance.get("customer_satisfaction_score", 5.0),
                "professionalism": performance.get("agent_professionalism_score", 5.0),
                "empathy": performance.get("agent_empathy_score", 5.0)
            })
            
            talk_ratio = characteristics.get("agent_talk_ratio", 0.5)
            agent_performance[agent_name]["talk_ratios"].append(talk_ratio)
            agent_performance[agent_name]["results"].append(result)
            
            # Identify issues with evidence
            if talk_ratio > 0.8:
                agent_performance[agent_name]["issues"].append("Excessive talking")
                
                # Find evidence of excessive talking
                talking_evidence = self._extract_transcript_evidence(
                    result,
                    ["let me explain", "as I was saying", "listen", "hold on"],
                    speaker_filter="agent",
                    context=f"Agent talk ratio was {talk_ratio:.1%}, indicating excessive talking"
                )
                agent_performance[agent_name]["evidence"].extend(talking_evidence)
            
            if performance.get("active_listening_score", 5.0) < 6.0:
                agent_performance[agent_name]["issues"].append("Poor active listening")
                
                # Find evidence of poor listening
                listening_evidence = self._extract_transcript_evidence(
                    result,
                    ["what?", "sorry", "can you repeat", "I didn't catch"],
                    speaker_filter="agent",
                    context="Agent demonstrated poor active listening skills"
                )
                agent_performance[agent_name]["evidence"].extend(listening_evidence)
        
        # Generate training recommendations with evidence
        training_needs = []
        for agent_name, data in agent_performance.items():
            if data["scores"]:
                avg_satisfaction = sum(s["satisfaction"] for s in data["scores"]) / len(data["scores"])
                avg_empathy = sum(s["empathy"] for s in data["scores"]) / len(data["scores"])
                
                skill_gaps = []
                performance_examples = []
                improvement_opportunities = []
                
                if avg_satisfaction < 6.0:
                    skill_gaps.append("Customer satisfaction")
                    
                    # Find specific examples of satisfaction issues
                    for result in data["results"]:
                        examples = self._extract_transcript_evidence(
                            result,
                            ["not helping", "waste of time", "not satisfied"],
                            speaker_filter="customer",
                            context="Customer expressed dissatisfaction with agent performance"
                        )
                        performance_examples.extend(examples)
                
                if avg_empathy < 6.0:
                    skill_gaps.append("Empathy and rapport building")
                    
                    # Find opportunities where empathy could have helped
                    for result in data["results"]:
                        examples = self._extract_transcript_evidence(
                            result,
                            ["understand", "sorry to hear", "I feel", "that's frustrating"],
                            speaker_filter="agent",
                            context="Opportunity for improved empathy response"
                        )
                        improvement_opportunities.extend(examples)
                
                if "Excessive talking" in data["issues"]:
                    skill_gaps.append("Active listening")
                
                if skill_gaps:
                    priority = RiskLevel.HIGH if avg_satisfaction < 5.0 else RiskLevel.MEDIUM
                    
                    # Create decision evidence
                    decision_evidence = self._create_decision_evidence(
                        data["evidence"],
                        "training_need_assessment",
                        f"Analyzed performance scores, talk ratios, and conversation patterns"
                    )
                    
                    training_needs.append(AgentTrainingNeed(
                        agent_name=agent_name,
                        skill_gaps=skill_gaps,
                        performance_metrics={
                            "satisfaction": avg_satisfaction,
                            "empathy": avg_empathy
                        },
                        training_priority=priority,
                        recommended_training=[
                            "Active listening workshop",
                            "Customer empathy training",
                            "Consultative selling techniques"
                        ],
                        improvement_potential=0.7,
                        evidence=decision_evidence,
                        performance_examples=performance_examples,
                        improvement_opportunities=improvement_opportunities
                    ))
        
        return training_needs[:3]  # Return top 3 training needs
    
    def _analyze_pipeline_health_with_evidence(self, analysis_results: List[Dict]) -> List[PipelineHealthIndicator]:
        """Analyze pipeline health by stage with supporting evidence."""
        
        # Simplified pipeline analysis
        stages = {
            "Discovery": {"deals": 0, "avg_duration": 15, "conversion": 0.7, "calls": []},
            "Demo Scheduled": {"deals": 0, "avg_duration": 10, "conversion": 0.6, "calls": []},
            "Pricing Discussion": {"deals": 0, "avg_duration": 8, "conversion": 0.5, "calls": []},
            "Decision Pending": {"deals": 0, "avg_duration": 12, "conversion": 0.8, "calls": []}
        }
        
        # Categorize calls by stage (simplified logic)
        for result in analysis_results:
            topics = result.get("key_topics", {})
            keywords = topics.get("keywords_frequency", {})
            call_id = result.get("call_id", "Unknown")
            
            if any(word in keywords for word in ["demo", "demonstration", "show"]):
                stages["Demo Scheduled"]["deals"] += 1
                stages["Demo Scheduled"]["calls"].append(call_id)
            elif any(word in keywords for word in ["price", "cost", "quote", "proposal"]):
                stages["Pricing Discussion"]["deals"] += 1
                stages["Pricing Discussion"]["calls"].append(call_id)
            elif any(word in keywords for word in ["decision", "approval", "review"]):
                stages["Decision Pending"]["deals"] += 1
                stages["Decision Pending"]["calls"].append(call_id)
            else:
                stages["Discovery"]["deals"] += 1
                stages["Discovery"]["calls"].append(call_id)
        
        pipeline_health = []
        for stage_name, data in stages.items():
            health_status = "healthy"
            issues = []
            actions = []
            issue_evidence = []
            
            if data["deals"] == 0:
                health_status = "stalled"
                issues.append("No active deals in stage")
                actions.append("Increase lead generation")
            elif data["conversion"] < 0.5:
                health_status = "at-risk"
                issues.append("Low conversion rate")
                actions.append("Review qualification criteria")
                
                # Find evidence of conversion issues in this stage
                for result in analysis_results:
                    if result.get("call_id") in data["calls"]:
                        evidence = self._extract_transcript_evidence(
                            result,
                            ["not ready", "need to think", "not convinced", "hesitant"],
                            context=f"Evidence of conversion challenges in {stage_name} stage"
                        )
                        issue_evidence.extend(evidence)
            
            pipeline_health.append(PipelineHealthIndicator(
                stage_name=stage_name,
                total_deals=data["deals"],
                health_status=health_status,
                average_stage_duration=data["avg_duration"],
                conversion_rate=data["conversion"],
                key_issues=issues,
                recommended_actions=actions,
                representative_calls=data["calls"][:5],  # First 5 calls as examples
                issue_evidence=issue_evidence
            ))
        
        return pipeline_health
    
    def _analyze_objection_patterns_with_evidence(self, analysis_results: List[Dict]) -> List[ObjectionPattern]:
        """Analyze recurring objection patterns with evidence examples."""
        
        objection_data = {}
        total_calls = len(analysis_results)
        
        for result in analysis_results:
            topics = result.get("key_topics", {})
            keywords = topics.get("keywords_frequency", {})
            
            # Common objection patterns with evidence collection
            objections_to_check = {
                "Too expensive": ["expensive", "cost", "price", "budget"],
                "Competitor comparison": ["competitor", "alternative", "compare"],
                "Timing concerns": ["time", "busy", "schedule", "timing"]
            }
            
            for objection_type, objection_keywords in objections_to_check.items():
                if any(word in keywords for word in objection_keywords):
                    if objection_type not in objection_data:
                        objection_data[objection_type] = {
                            "count": 0,
                            "examples": [],
                            "successful_responses": []
                        }
                    
                    objection_data[objection_type]["count"] += 1
                    
                    # Collect examples of this objection
                    examples = self._extract_transcript_evidence(
                        result,
                        objection_keywords,
                        speaker_filter="customer",
                        context=f"Customer raised '{objection_type}' objection"
                    )
                    objection_data[objection_type]["examples"].extend(examples)
                    
                    # Look for successful agent responses
                    responses = self._extract_transcript_evidence(
                        result,
                        ["value", "roi", "benefit", "save", "worth"],
                        speaker_filter="agent",
                        context=f"Agent response to '{objection_type}' objection"
                    )
                    objection_data[objection_type]["successful_responses"].extend(responses)
        
        objection_patterns = []
        for objection, data in objection_data.items():
            frequency_pct = (data["count"] / total_calls) * 100
            
            if frequency_pct >= 10:  # Only include objections in 10%+ of calls
                objection_patterns.append(ObjectionPattern(
                    objection_text=objection,
                    frequency=data["count"],
                    frequency_percentage=frequency_pct,
                    impact_on_conversion=-0.2,  # Estimated impact
                    suggested_responses=self._get_objection_responses(objection),
                    training_materials_needed=[f"{objection} handling guide", "Objection response scripts"],
                    example_objections=data["examples"][:3],  # Top 3 examples
                    successful_responses=data["successful_responses"][:2]  # Top 2 successful responses
                ))
        
        return objection_patterns
    
    def _identify_quality_issues_with_evidence(self, analysis_results: List[Dict]) -> List[CallQualityIssue]:
        """Identify technical and process quality issues with evidence."""
        
        issue_data = {}
        total_calls = len(analysis_results)
        
        for result in analysis_results:
            characteristics = result.get("characteristics", {})
            
            # Long silences
            silence_duration = characteristics.get("silence_duration_seconds", 0)
            if silence_duration > 30:
                issue_type = "Long silences"
                if issue_type not in issue_data:
                    issue_data[issue_type] = {"count": 0, "examples": []}
                issue_data[issue_type]["count"] += 1
                
                # Create evidence for long silences
                evidence = TranscriptEvidence(
                    call_id=result.get("call_id", "Unknown"),
                    transcript_source=result.get("transcript_source", "Unknown"),
                    speaker=CallParticipant.SYSTEM,
                    timestamp=None,
                    evidence_text=f"Total silence duration: {silence_duration} seconds (threshold: 30s)",
                    context="Excessive silence detected during call",
                    confidence_score=0.9
                )
                issue_data[issue_type]["examples"].append(evidence)
            
            # Too much agent talk time
            agent_ratio = characteristics.get("agent_talk_ratio", 0.5)
            if agent_ratio > 0.8:
                issue_type = "Agent excessive talking"
                if issue_type not in issue_data:
                    issue_data[issue_type] = {"count": 0, "examples": []}
                issue_data[issue_type]["count"] += 1
                
                # Create evidence for excessive talking
                evidence = TranscriptEvidence(
                    call_id=result.get("call_id", "Unknown"),
                    transcript_source=result.get("transcript_source", "Unknown"),
                    speaker=CallParticipant.AGENT,
                    timestamp=None,
                    evidence_text=f"Agent talk ratio: {agent_ratio:.1%} (threshold: 80%)",
                    context="Agent dominated conversation, poor listening",
                    confidence_score=0.9
                )
                issue_data[issue_type]["examples"].append(evidence)
            
            # Interruptions
            interruptions = characteristics.get("interruptions_by_agent", 0)
            if interruptions > 3:
                issue_type = "Frequent interruptions"
                if issue_type not in issue_data:
                    issue_data[issue_type] = {"count": 0, "examples": []}
                issue_data[issue_type]["count"] += 1
                
                # Create evidence for interruptions
                evidence = TranscriptEvidence(
                    call_id=result.get("call_id", "Unknown"),
                    transcript_source=result.get("transcript_source", "Unknown"),
                    speaker=CallParticipant.AGENT,
                    timestamp=None,
                    evidence_text=f"Agent interruptions: {interruptions} times (threshold: 3)",
                    context="Agent frequently interrupted customer",
                    confidence_score=0.8
                )
                issue_data[issue_type]["examples"].append(evidence)
        
        quality_issues = []
        for issue_type, data in issue_data.items():
            affected_percentage = (data["count"] / total_calls) * 100
            
            if data["count"] > 0:
                severity = RiskLevel.HIGH if affected_percentage > 20 else RiskLevel.MEDIUM
                
                quality_issues.append(CallQualityIssue(
                    issue_type=issue_type,
                    frequency=data["count"],
                    affected_calls_percentage=affected_percentage,
                    impact_severity=severity,
                    root_causes=self._get_issue_root_causes(issue_type),
                    recommended_solutions=self._get_issue_solutions(issue_type),
                    example_occurrences=data["examples"][:3]  # Top 3 examples
                ))
        
        return quality_issues
    
    def _calculate_evidence_summary(
        self,
        deals_at_risk: List[DealRiskIndicator],
        churn_risks: List[ChurnRiskIndicator],
        opportunities: List[OpportunityIndicator],
        training_needs: List[AgentTrainingNeed],
        objection_patterns: List[ObjectionPattern],
        quality_issues: List[CallQualityIssue]
    ) -> Dict[str, int]:
        """Calculate summary statistics for evidence collected."""
        
        total_evidence = 0
        calls_referenced = set()
        
        # Count evidence from each category
        for deal in deals_at_risk:
            total_evidence += len(deal.evidence.primary_evidence) + len(deal.evidence.supporting_evidence)
            for evidence in deal.evidence.primary_evidence + deal.evidence.supporting_evidence:
                calls_referenced.add(evidence.call_id)
        
        for churn in churn_risks:
            total_evidence += len(churn.evidence.primary_evidence) + len(churn.evidence.supporting_evidence)
            for evidence in churn.evidence.primary_evidence + churn.evidence.supporting_evidence:
                calls_referenced.add(evidence.call_id)
        
        for opp in opportunities:
            total_evidence += len(opp.evidence.primary_evidence) + len(opp.evidence.supporting_evidence)
            for evidence in opp.evidence.primary_evidence + opp.evidence.supporting_evidence:
                calls_referenced.add(evidence.call_id)
        
        for training in training_needs:
            total_evidence += len(training.evidence.primary_evidence) + len(training.evidence.supporting_evidence)
            total_evidence += len(training.performance_examples) + len(training.improvement_opportunities)
            for evidence in training.evidence.primary_evidence + training.evidence.supporting_evidence:
                calls_referenced.add(evidence.call_id)
        
        for objection in objection_patterns:
            total_evidence += len(objection.example_objections) + len(objection.successful_responses)
            for evidence in objection.example_objections + objection.successful_responses:
                calls_referenced.add(evidence.call_id)
        
        for issue in quality_issues:
            total_evidence += len(issue.example_occurrences)
            for evidence in issue.example_occurrences:
                calls_referenced.add(evidence.call_id)
        
        return {
            "total_evidence_items": total_evidence,
            "calls_with_evidence": len(calls_referenced),
            "deal_risk_evidence": sum(len(d.evidence.primary_evidence) + len(d.evidence.supporting_evidence) for d in deals_at_risk),
            "churn_risk_evidence": sum(len(c.evidence.primary_evidence) + len(c.evidence.supporting_evidence) for c in churn_risks),
            "opportunity_evidence": sum(len(o.evidence.primary_evidence) + len(o.evidence.supporting_evidence) for o in opportunities),
            "training_evidence": sum(len(t.evidence.primary_evidence) + len(t.evidence.supporting_evidence) for t in training_needs),
            "objection_examples": sum(len(obj.example_objections) for obj in objection_patterns),
            "quality_issue_examples": sum(len(q.example_occurrences) for q in quality_issues)
        }
    
    def _calculate_analysis_confidence(self, evidence_summary: Dict[str, int], total_calls: int) -> float:
        """Calculate overall confidence in the analysis based on evidence quality."""
        
        total_evidence = evidence_summary.get("total_evidence_items", 0)
        calls_with_evidence = evidence_summary.get("calls_with_evidence", 0)
        
        if total_calls == 0:
            return 0.0
        
        # Base confidence on evidence coverage
        evidence_coverage = calls_with_evidence / total_calls
        evidence_density = min(total_evidence / total_calls, 5.0) / 5.0  # Cap at 5 evidence items per call
        
        # Weighted average of coverage and density
        confidence = (evidence_coverage * 0.7) + (evidence_density * 0.3)
        
        return round(confidence, 2)
    
    def _generate_review_recommendations(
        self, 
        analysis_confidence: float, 
        evidence_summary: Dict[str, int]
    ) -> List[str]:
        """Generate recommendations for human review based on evidence quality."""
        
        recommendations = []
        
        if analysis_confidence < 0.5:
            recommendations.append("Low confidence analysis - recommend human review of all insights")
        
        if evidence_summary.get("deal_risk_evidence", 0) < 2:
            recommendations.append("Limited evidence for deal risk assessments - validate with additional data")
        
        if evidence_summary.get("total_evidence_items", 0) < 10:
            recommendations.append("Sparse evidence overall - consider expanding analysis criteria")
        
        if analysis_confidence >= 0.8:
            recommendations.append("High confidence analysis - insights are well-supported by evidence")
        
        if not recommendations:
            recommendations.append("Analysis appears well-supported - spot check key insights")
        
        return recommendations
    
    def _calculate_aggregate_metrics(self, analysis_results: List[Dict]) -> Dict[str, float]:
        """Calculate aggregate metrics across all calls."""
        
        total_calls = len(analysis_results)
        if total_calls == 0:
            return {
                "avg_sentiment": 0.0,
                "avg_satisfaction": 0.0,
                "fcr_rate": 0.0,
                "avg_duration": 0.0
            }
        
        sentiment_scores = []
        satisfaction_scores = []
        fcr_count = 0
        durations = []
        
        for result in analysis_results:
            # Sentiment (convert to numeric)
            sentiment = result.get("sentiment_analysis", {}).get("overall_sentiment", "neutral")
            sentiment_score = {"positive": 0.8, "neutral": 0.5, "negative": 0.2}.get(sentiment, 0.5)
            sentiment_scores.append(sentiment_score)
            
            # Satisfaction
            performance = result.get("performance_kpis", {})
            satisfaction = performance.get("customer_satisfaction_score", 5.0)
            satisfaction_scores.append(satisfaction)
            
            # First call resolution
            if performance.get("first_call_resolution", False):
                fcr_count += 1
            
            # Duration
            characteristics = result.get("characteristics", {})
            duration = characteristics.get("total_duration_seconds", 300) / 60  # Convert to minutes
            durations.append(duration)
        
        return {
            "avg_sentiment": sum(sentiment_scores) / len(sentiment_scores),
            "avg_satisfaction": sum(satisfaction_scores) / len(satisfaction_scores),
            "fcr_rate": (fcr_count / total_calls) * 100,
            "avg_duration": sum(durations) / len(durations)
        }
    
    def _generate_top_priorities(
        self,
        deals_at_risk: List[DealRiskIndicator],
        churn_risks: List[ChurnRiskIndicator],
        training_needs: List[AgentTrainingNeed],
        quality_issues: List[CallQualityIssue]
    ) -> List[str]:
        """Generate top 3 priority actions."""
        
        priorities = []
        
        if len(deals_at_risk) > 2:
            priorities.append(f"Address {len(deals_at_risk)} deals at risk - implement immediate recovery actions")
        
        if len(churn_risks) > 1:
            priorities.append(f"Prevent churn for {len(churn_risks)} at-risk accounts - schedule retention calls")
        
        high_priority_training = [t for t in training_needs if t.training_priority == RiskLevel.HIGH]
        if high_priority_training:
            priorities.append(f"Urgent training needed for {len(high_priority_training)} agents")
        
        critical_quality_issues = [q for q in quality_issues if q.impact_severity == RiskLevel.HIGH]
        if critical_quality_issues:
            priorities.append(f"Fix critical quality issues affecting {sum(q.frequency for q in critical_quality_issues)} calls")
        
        # Fill remaining slots with general improvements
        if len(priorities) < 3:
            if training_needs:
                priorities.append("Implement agent training program")
            if quality_issues:
                priorities.append("Address call quality issues")
            if not priorities:
                priorities.append("Maintain current performance levels")
        
        return priorities[:3]
    
    def _identify_success_indicators(self, analysis_results: List[Dict]) -> List[str]:
        """Identify positive trends and successes."""
        
        successes = []
        total_calls = len(analysis_results)
        
        # High satisfaction rate
        high_satisfaction_count = sum(
            1 for r in analysis_results
            if r.get("performance_kpis", {}).get("customer_satisfaction_score", 0) >= 8.0
        )
        if high_satisfaction_count / total_calls > 0.6:
            successes.append(f"{(high_satisfaction_count/total_calls)*100:.0f}% of calls achieved high customer satisfaction")
        
        # Good compliance
        compliant_calls = sum(
            1 for r in analysis_results
            if r.get("compliance_metrics", {}).get("compliance_score", 0) >= 8.0
        )
        if compliant_calls / total_calls > 0.8:
            successes.append(f"Strong compliance performance in {(compliant_calls/total_calls)*100:.0f}% of calls")
        
        # Positive sentiment
        positive_sentiment_count = sum(
            1 for r in analysis_results
            if r.get("sentiment_analysis", {}).get("overall_sentiment") == "positive"
        )
        if positive_sentiment_count / total_calls > 0.5:
            successes.append(f"Positive sentiment achieved in {(positive_sentiment_count/total_calls)*100:.0f}% of calls")
        
        return successes[:3]
    
    def _identify_improvement_areas(
        self,
        quality_metrics: Dict,
        training_needs: List[AgentTrainingNeed],
        objection_patterns: List[ObjectionPattern]
    ) -> List[str]:
        """Identify key areas needing improvement."""
        
        improvements = []
        
        if quality_metrics["overall_score"] < 7.0:
            improvements.append("Overall call quality needs improvement")
        
        if len(training_needs) > 0:
            improvements.append("Agent skills development required")
        
        if len(objection_patterns) > 0:
            top_objection = max(objection_patterns, key=lambda x: x.frequency_percentage)
            improvements.append(f"Address recurring '{top_objection.objection_text}' objections")
        
        return improvements[:3]
    
    def _generate_risk_mitigation_actions(self, risk_factors: List[str]) -> List[str]:
        """Generate specific actions to mitigate deal risks."""
        actions = []
        
        if "Negative customer sentiment" in risk_factors:
            actions.append("Schedule immediate customer relationship review")
        if "Price concerns raised" in risk_factors:
            actions.append("Provide detailed ROI analysis and value justification")
        if "Competitor mentioned" in risk_factors:
            actions.append("Send competitive differentiation materials")
        
        return actions if actions else ["Schedule follow-up call to address concerns"]
    
    def _generate_retention_actions(self, risk_signals: List[str]) -> List[str]:
        """Generate retention actions for churn risks."""
        actions = []
        
        if "Mentioned switching providers" in risk_signals:
            actions.append("Immediate retention call with senior manager")
        if "Contract renewal discussion" in risk_signals:
            actions.append("Prepare renewal incentive package")
        if "Negative customer sentiment" in risk_signals:
            actions.append("Assign dedicated customer success manager")
        
        return actions if actions else ["Schedule retention consultation"]
    
    def _get_objection_responses(self, objection: str) -> List[str]:
        """Get suggested responses for common objections."""
        responses = {
            "Too expensive": [
                "Focus on ROI and total cost of ownership",
                "Offer flexible payment terms",
                "Compare cost of inaction"
            ],
            "Competitor comparison": [
                "Highlight unique differentiators",
                "Provide customer success stories",
                "Offer side-by-side feature comparison"
            ],
            "Timing concerns": [
                "Understand urgency drivers",
                "Offer phased implementation",
                "Highlight cost of delay"
            ]
        }
        return responses.get(objection, ["Acknowledge concern and provide evidence"])
    
    def _get_issue_root_causes(self, issue_type: str) -> List[str]:
        """Get root causes for quality issues."""
        causes = {
            "Long silences": ["Technical difficulties", "Agent hesitation", "System delays"],
            "Agent excessive talking": ["Poor listening skills", "Over-explaining", "Nervousness"],
            "Frequent interruptions": ["Impatience", "Poor active listening", "Time pressure"]
        }
        return causes.get(issue_type, ["Unknown cause"])
    
    def _get_issue_solutions(self, issue_type: str) -> List[str]:
        """Get solutions for quality issues."""
        solutions = {
            "Long silences": ["Technical training", "System upgrades", "Confidence building"],
            "Agent excessive talking": ["Active listening training", "Question techniques", "Pause training"],
            "Frequent interruptions": ["Patience training", "Listening skills workshop", "Time management"]
        }
        return solutions.get(issue_type, ["General training"])
    
    # AI-Enhanced Analysis Methods
    
    async def _identify_deals_at_risk_with_ai_evidence(self, analysis_results: List[Dict]) -> List[DealRiskIndicator]:
        """Identify deals at risk using AI-powered analysis with enhanced evidence."""
        
        at_risk_deals = []
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            segments = result.get("transcript_segments", [])
            real_metadata = result.get("real_metadata", {})
            
            if not segments:
                continue
            
            # Extract real metadata
            company_name = real_metadata.get("company_name", f"Account_{call_id}")
            agent_name = real_metadata.get("agent_name", f"Agent_{call_id}")
            script_source = real_metadata.get("script_source", f"{call_id}.json")
            
            # Convert to TranscriptSegment objects for AI analysis
            transcript_segments = []
            for seg in segments:
                if isinstance(seg, dict):
                    transcript_segments.append(TranscriptSegment(
                        speaker=CallParticipant(seg.get("speaker", "unknown")),
                        text=seg.get("text", ""),
                        timestamp=seg.get("timestamp", 0.0),
                        duration=seg.get("duration", 1.0),
                        confidence=seg.get("confidence", 0.95)
                    ))
                else:
                    transcript_segments.append(seg)
            
            # Use AI analyzer to detect deal risks with real metadata
            ai_deal_risk = await self.ai_analyzer.analyze_deal_risk(
                transcript_segments, call_id, 
                account_name=company_name, 
                agent_name=agent_name, 
                transcript_source=script_source
            )
            
            if ai_deal_risk:
                at_risk_deals.append(ai_deal_risk)
        
        return at_risk_deals
    
    async def _identify_churn_risks_with_ai_evidence(self, analysis_results: List[Dict]) -> List[ChurnRiskIndicator]:
        """Identify churn risks using AI-powered analysis with enhanced evidence."""
        
        churn_risks = []
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            segments = result.get("transcript_segments", [])
            real_metadata = result.get("real_metadata", {})
            
            if not segments:
                continue
            
            # Extract real metadata
            company_name = real_metadata.get("company_name", f"Account_{call_id}")
            agent_name = real_metadata.get("agent_name", f"Agent_{call_id}")
            script_source = real_metadata.get("script_source", f"{call_id}.json")
            
            # Convert to TranscriptSegment objects for AI analysis
            transcript_segments = []
            for seg in segments:
                if isinstance(seg, dict):
                    transcript_segments.append(TranscriptSegment(
                        speaker=CallParticipant(seg.get("speaker", "unknown")),
                        text=seg.get("text", ""),
                        timestamp=seg.get("timestamp", 0.0),
                        duration=seg.get("duration", 1.0),
                        confidence=seg.get("confidence", 0.95)
                    ))
                else:
                    transcript_segments.append(seg)
            
            # Use AI analyzer to detect churn risks with real metadata
            ai_churn_risk = await self.ai_analyzer.analyze_churn_risk(
                transcript_segments, call_id,
                account_name=company_name,
                agent_name=agent_name,
                transcript_source=script_source
            )
            
            if ai_churn_risk:
                churn_risks.append(ai_churn_risk)
        
        return churn_risks
    
    async def _identify_opportunities_with_ai_evidence(self, analysis_results: List[Dict]) -> List[OpportunityIndicator]:
        """Identify opportunities using AI-powered analysis with enhanced evidence."""
        
        opportunities = []
        
        for result in analysis_results:
            call_id = result.get("call_id", "Unknown")
            segments = result.get("transcript_segments", [])
            
            if not segments:
                continue
            
            # Convert to TranscriptSegment objects for AI analysis
            transcript_segments = []
            for seg in segments:
                if isinstance(seg, dict):
                    transcript_segments.append(TranscriptSegment(
                        speaker=CallParticipant(seg.get("speaker", "unknown")),
                        text=seg.get("text", ""),
                        timestamp=seg.get("timestamp", 0.0),
                        duration=seg.get("duration", 1.0),
                        confidence=seg.get("confidence", 0.95)
                    ))
                else:
                    transcript_segments.append(seg)
            
            # Use AI analyzer to detect opportunities
            ai_opportunities = await self.ai_analyzer.analyze_opportunities(transcript_segments, call_id)
            
            opportunities.extend(ai_opportunities)
        
        return opportunities 