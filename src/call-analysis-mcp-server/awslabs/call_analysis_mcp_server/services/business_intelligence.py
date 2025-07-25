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
    TranscriptEvidence, DecisionEvidence, CallParticipant, TranscriptSegment,
    CallCategory, ObjectionType, ObjectionAnalysis, ResolutionMetrics,
    CompetitiveAnalysis, ProductKnowledgeGap, FollowUpAnalysis,
    ConversionMetrics
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
        print(f"🚀 Starting business intelligence analysis for {len(analysis_results)} calls...")
        
        # Basic metrics
        total_calls = len(analysis_results)
        print(f"   📊 Processing {total_calls} call analysis results...")
        
        # Quality assessment
        print(f"   🔍 Analyzing quality metrics...")
        quality_metrics = self._analyze_quality_metrics(analysis_results)
        print(f"   ✅ Quality analysis complete - Overall score: {quality_metrics['overall_score']:.2f}")
        
        # Risk and opportunity identification with AI-enhanced evidence
        print(f"   🔍 Analyzing deal risks with AI...")
        deals_at_risk = await self._identify_deals_at_risk_with_ai_evidence(analysis_results)
        print(f"   🔍 Analyzing churn risks with AI...")
        churn_risks = await self._identify_churn_risks_with_ai_evidence(analysis_results)
        print(f"   🔍 Analyzing opportunities with AI...")
        opportunities = await self._identify_opportunities_with_ai_evidence(analysis_results)
        
        # Performance insights with evidence
        print(f"   📈 Analyzing training needs...")
        training_needs = self._identify_training_needs_with_evidence(analysis_results)
        print(f"   📊 Analyzing pipeline health...")
        pipeline_health = self._analyze_pipeline_health_with_evidence(analysis_results)
        print(f"   🗣️ Analyzing objection patterns...")
        objection_patterns = self._analyze_objection_patterns_with_evidence(analysis_results)
        print(f"   ✅ Performance insights complete")
        
        # Quality issues with evidence
        print(f"   🔍 Identifying quality issues...")
        quality_issues = self._identify_quality_issues_with_evidence(analysis_results)
        
        # Aggregate metrics
        print(f"   📊 Calculating aggregate metrics...")
        aggregate_metrics = self._calculate_aggregate_metrics(analysis_results)
        
        # Advanced analytics
        print(f"   📊 Generating advanced analytics...")
        call_categorization = self._analyze_call_categorization(analysis_results)
        print(f"      ➤ Call categorization complete")
        objection_analysis = self._analyze_objections_detailed(analysis_results)
        print(f"      ➤ Detailed objection analysis complete")
        resolution_metrics = self._calculate_resolution_metrics(analysis_results)
        print(f"      ➤ Resolution metrics calculated")
        competitive_analysis = self._analyze_competitive_landscape(analysis_results)
        print(f"      ➤ Competitive analysis complete")
        product_knowledge_gaps = self._identify_product_knowledge_gaps(analysis_results)
        print(f"      ➤ Product knowledge gaps identified")
        follow_up_analysis = self._analyze_follow_up_adherence(analysis_results)
        print(f"      ➤ Follow-up adherence analyzed")
        pipeline_health_detailed = self._analyze_pipeline_health_detailed(analysis_results)
        print(f"      ➤ Detailed pipeline health analyzed")
        conversion_metrics = self._calculate_conversion_metrics(analysis_results)
        print(f"   ✅ Advanced analytics complete")
        
        # Generate actionable insights
        print(f"   🎯 Generating actionable insights...")
        top_priorities = self._generate_top_priorities(
            deals_at_risk, churn_risks, training_needs, quality_issues
        )
        success_indicators = self._identify_success_indicators(analysis_results)
        improvement_areas = self._identify_improvement_areas(
            quality_metrics, training_needs, objection_patterns
        )
        print(f"   ✅ Actionable insights generated")
        
        # Calculate evidence summary and confidence
        print(f"   📋 Calculating evidence summary and confidence...")
        evidence_summary = self._calculate_evidence_summary(
            deals_at_risk, churn_risks, opportunities, training_needs, objection_patterns, quality_issues
        )
        analysis_confidence = self._calculate_analysis_confidence(evidence_summary, total_calls)
        review_recommendations = self._generate_review_recommendations(analysis_confidence, evidence_summary)
        print(f"   ✅ Evidence summary complete")
        
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
            review_recommendations=review_recommendations,
            
            # Advanced analytics
            call_categorization=call_categorization,
            objection_analysis=objection_analysis,
            resolution_metrics=resolution_metrics,
            competitive_analysis=competitive_analysis,
            product_knowledge_gaps=product_knowledge_gaps,
            follow_up_analysis=follow_up_analysis,
            pipeline_health=pipeline_health_detailed,
            conversion_metrics=conversion_metrics,
            
            # Performance metrics
            average_resolution_time_minutes=resolution_metrics.get("average_resolution_time", 0.0),
            escalation_rate=resolution_metrics.get("escalation_rate", 0.0),
            follow_up_adherence_rate=resolution_metrics.get("follow_up_adherence_rate", 0.0)
        )
        
        print(f"🎉 Business intelligence analysis complete!")
        print(f"   📊 Generated insights for {total_calls} calls")
        print(f"   🎯 Identified {len(deals_at_risk)} deals at risk, {len(churn_risks)} churn risks, {len(opportunities)} opportunities")
        logger.info(f"Business intelligence analysis completed successfully for {total_calls} calls")
        
        return insights
    
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
            
            # Map stage_name to simplified stage values and calculate metrics
            stage_mapping = {
                "Discovery": "prospect",
                "Demo Scheduled": "qualified", 
                "Pricing Discussion": "proposal",
                "Decision Pending": "negotiation"
            }
            
            # Calculate progression probability based on conversion rate and health
            stage_progression_probability = max(0.0, min(1.0, data["conversion"]))
            
            # Calculate deal velocity score based on stage duration (inverse relationship)
            max_duration = 30.0  # Assume 30 days is maximum healthy duration
            deal_velocity_score = max(0.0, min(1.0, 1.0 - (data["avg_duration"] / max_duration)))
            
            # Calculate engagement level based on number of deals and calls
            total_calls = len(data["calls"])
            engagement_level = max(0.0, min(1.0, min(data["deals"] / 10.0, total_calls / 20.0)))
            
            # Calculate next steps clarity based on health status
            next_steps_clarity_map = {
                "healthy": 0.9,
                "neutral": 0.7,
                "at-risk": 0.4,
                "stalled": 0.2
            }
            next_steps_clarity = next_steps_clarity_map.get(health_status, 0.5)
            
            pipeline_health.append(PipelineHealthIndicator(
                stage=stage_mapping.get(stage_name, "prospect"),
                stage_progression_probability=stage_progression_probability,
                deal_velocity_score=deal_velocity_score,
                engagement_level=engagement_level,
                next_steps_clarity=next_steps_clarity
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
            "fcr_rate": fcr_count / total_calls,  # Rate between 0-1, not percentage
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
        """Identify deals at risk using AI-powered batch analysis with enhanced evidence."""
        
        total_calls = len(analysis_results)
        print(f"     📈 Starting batch deal risk analysis for {total_calls} calls")
        
        # Prepare call batches for AI analysis
        call_batches = []
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
            
            call_batches.append({
                "call_id": call_id,
                "segments": transcript_segments,
                "account_name": company_name,
                "agent_name": agent_name,
                "transcript_source": script_source
            })
        
        # Use batch AI analyzer for improved performance (10 calls per batch)
        at_risk_deals = await self.ai_analyzer.batch_analyze_deal_risks(call_batches, batch_size=10)
        
        print(f"     ✅ Batch deal risk analysis complete: {len(at_risk_deals)} at-risk deals found")
        return at_risk_deals
    
    async def _identify_churn_risks_with_ai_evidence(self, analysis_results: List[Dict]) -> List[ChurnRiskIndicator]:
        """Identify churn risks using AI-powered analysis with enhanced evidence."""
        
        total_calls = len(analysis_results)
        print(f"     🔄 Starting batch churn risk analysis for {total_calls} calls")
        
        # Prepare call batches for AI analysis
        call_batches = []
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
            
            call_batches.append({
                "call_id": call_id,
                "segments": transcript_segments,
                "account_name": company_name,
                "agent_name": agent_name,
                "transcript_source": script_source
            })
        
        # Use batch AI analyzer for improved performance (10 calls per batch)
        churn_risks = await self.ai_analyzer.batch_analyze_churn_risks(call_batches, batch_size=10)
        
        print(f"     ✅ Batch churn risk analysis complete: {len(churn_risks)} churn risks found")
        return churn_risks
    
    async def _identify_opportunities_with_ai_evidence(self, analysis_results: List[Dict]) -> List[OpportunityIndicator]:
        """Identify opportunities using AI-powered analysis with enhanced evidence."""
        
        total_calls = len(analysis_results)
        print(f"     💰 Starting batch opportunity analysis for {total_calls} calls")
        
        # Prepare call batches for AI analysis
        call_batches = []
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
            
            call_batches.append({
                "call_id": call_id,
                "segments": transcript_segments,
                "account_name": company_name,
                "agent_name": agent_name,
                "transcript_source": script_source
            })
        
        # Use batch AI analyzer for improved performance (10 calls per batch)
        opportunities = await self.ai_analyzer.batch_analyze_opportunities(call_batches, batch_size=10)
        
        print(f"     ✅ Batch opportunity analysis complete: {len(opportunities)} opportunities found")
        return opportunities 
    
    # Advanced Analytics Methods
    
    def _analyze_call_categorization(self, analysis_results: List[Dict]) -> Dict[CallCategory, int]:
        """Analyze and categorize calls based on content."""
        categorization = {}
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            categories = self._categorize_call(segments)
            
            for category in categories:
                categorization[category] = categorization.get(category, 0) + 1
        
        return categorization
    
    def _categorize_call(self, segments: List[Dict]) -> List[CallCategory]:
        """Categorize a single call based on transcript content."""
        transcript_text = " ".join([seg.get("text", "").lower() for seg in segments])
        categories = []
        
        # Define keyword patterns for each category
        patterns = {
            CallCategory.TECHNICAL_COMPLAINT: [
                "not working", "broken", "error", "bug", "issue", "problem", "outage", "down"
            ],
            CallCategory.PRICE_OBJECTION: [
                "expensive", "cost", "price", "budget", "cheaper", "discount", "reduce"
            ],
            CallCategory.NEW_BUSINESS_INQUIRY: [
                "interested in", "looking for", "want to buy", "quote", "proposal", "new customer"
            ],
            CallCategory.SETUP_INQUIRY: [
                "setup", "install", "configure", "how to", "getting started", "onboarding"
            ],
            CallCategory.BILLING_INQUIRY: [
                "bill", "invoice", "payment", "charge", "refund", "credit"
            ],
            CallCategory.FEATURE_REQUEST: [
                "feature", "add", "enhancement", "improvement", "would like", "missing"
            ],
            CallCategory.CANCELLATION_REQUEST: [
                "cancel", "terminate", "end service", "disconnect", "stop", "quit"
            ],
            CallCategory.UPSELL_OPPORTUNITY: [
                "upgrade", "additional", "more", "expand", "grow", "increase"
            ]
        }
        
        for category, keywords in patterns.items():
            if any(keyword in transcript_text for keyword in keywords):
                categories.append(category)
        
        return categories if categories else [CallCategory.SUPPORT_REQUEST]
    
    def _analyze_objections_detailed(self, analysis_results: List[Dict]) -> List[ObjectionAnalysis]:
        """Analyze detailed objections and responses."""
        objections = []
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            call_id = result.get("call_id", "Unknown")
            
            call_objections = self._extract_objections_from_call(segments, call_id)
            objections.extend(call_objections)
        
        return objections
    
    def _extract_objections_from_call(self, segments: List[Dict], call_id: str) -> List[ObjectionAnalysis]:
        """Extract objections from a single call."""
        objections = []
        
        # Look for objection patterns
        objection_patterns = {
            ObjectionType.PRICE: ["too expensive", "can't afford", "budget", "cheaper"],
            ObjectionType.COMPETITOR: ["competitor", "other option", "comparing"],
            ObjectionType.FEATURE_MISSING: ["doesn't have", "missing", "need"],
            ObjectionType.TIMING: ["not ready", "later", "timing"]
        }
        
        for i, segment in enumerate(segments):
            text = segment.get("text", "").lower()
            speaker = segment.get("speaker", "unknown")
            
            if speaker == "customer":
                for obj_type, keywords in objection_patterns.items():
                    if any(keyword in text for keyword in keywords):
                        # Find agent response
                        agent_response = ""
                        if i + 1 < len(segments) and segments[i + 1].get("speaker") == "agent":
                            agent_response = segments[i + 1].get("text", "")
                        
                        # Create evidence
                        evidence = DecisionEvidence(
                            decision_type="objection_analysis",
                            primary_evidence=[
                                TranscriptEvidence(
                                    call_id=call_id,
                                    transcript_source=f"{call_id}.json",
                                    speaker=CallParticipant.CUSTOMER,
                                    timestamp=segment.get("timestamp", 0.0),
                                    evidence_text=segment.get("text", ""),
                                    context=f"Customer objection: {obj_type.value}",
                                    confidence_score=0.8
                                )
                            ],
                            confidence_level=0.7,
                            analysis_methodology="Keyword-based objection detection"
                        )
                        
                        objections.append(ObjectionAnalysis(
                            objection_type=obj_type,
                            objection_text=segment.get("text", ""),
                            agent_response=agent_response,
                            response_effectiveness=self._evaluate_response_effectiveness(agent_response),
                            resolution_status="handled" if agent_response else "unresolved",
                            evidence=evidence
                        ))
        
        return objections
    
    def _evaluate_response_effectiveness(self, response: str) -> float:
        """Evaluate how effective an agent's response to an objection was."""
        if not response:
            return 0.0
        
        response_lower = response.lower()
        positive_indicators = [
            "understand", "appreciate", "let me", "help", "solution", "benefit", "value"
        ]
        
        score = sum(1 for indicator in positive_indicators if indicator in response_lower)
        return min(score / len(positive_indicators), 1.0)
    
    def _calculate_resolution_metrics(self, analysis_results: List[Dict]) -> Dict[str, float]:
        """Calculate resolution and efficiency metrics."""
        total_calls = len(analysis_results)
        if total_calls == 0:
            return {}
        
        total_duration = 0
        resolution_times = []
        first_call_resolutions = 0
        escalations = 0
        follow_ups_scheduled = 0
        follow_ups_adhered = 0
        
        for result in analysis_results:
            # Call duration (estimate from segments)
            segments = result.get("transcript_segments", [])
            if segments:
                duration = segments[-1].get("timestamp", 0) + segments[-1].get("duration", 0)
                total_duration += duration / 60  # Convert to minutes
            
            # Analyze for resolution indicators
            transcript_text = " ".join([seg.get("text", "").lower() for seg in segments])
            
            # First call resolution (look for resolution indicators)
            if any(phrase in transcript_text for phrase in [
                "resolved", "fixed", "solved", "completed", "done"
            ]):
                first_call_resolutions += 1
            
            # Escalation (look for escalation indicators)
            if any(phrase in transcript_text for phrase in [
                "escalate", "supervisor", "manager", "transfer"
            ]):
                escalations += 1
            
            # Follow-up analysis
            if any(phrase in transcript_text for phrase in [
                "follow up", "call back", "contact you", "schedule"
            ]):
                follow_ups_scheduled += 1
                # Assume 80% adherence for demo purposes
                if hash(result.get("call_id", "")) % 10 < 8:
                    follow_ups_adhered += 1
        
        return {
            "average_call_duration": total_duration / total_calls if total_calls > 0 else 0,
            "average_resolution_time": sum(resolution_times) / len(resolution_times) if resolution_times else 0,
            "first_call_resolution_rate": first_call_resolutions / total_calls,
            "escalation_rate": escalations / total_calls,
            "follow_up_adherence_rate": follow_ups_adhered / follow_ups_scheduled if follow_ups_scheduled > 0 else 0
        }
    
    def _analyze_competitive_landscape(self, analysis_results: List[Dict]) -> List[CompetitiveAnalysis]:
        """Analyze competitive mentions and positioning."""
        competitive_analyses = []
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            transcript_text = " ".join([seg.get("text", "") for seg in segments])
            
            # Look for competitor mentions
            competitors = self._identify_competitors(transcript_text)
            if competitors:
                competitive_analyses.append(CompetitiveAnalysis(
                    competitors_mentioned=competitors,
                    competitive_advantages_highlighted=self._extract_advantages(transcript_text),
                    competitive_weaknesses_exposed=self._extract_weaknesses(transcript_text),
                    positioning_effectiveness=self._evaluate_positioning(transcript_text),
                    win_probability_vs_competitor=self._calculate_win_probability(transcript_text)
                ))
        
        return competitive_analyses
    
    def _identify_competitors(self, text: str) -> List[str]:
        """Identify competitor mentions in transcript."""
        competitor_keywords = [
            "competitor", "other provider", "alternative", "competition",
            "verizon", "at&t", "comcast", "spectrum", "fiber", "cable"
        ]
        mentioned = []
        text_lower = text.lower()
        
        for keyword in competitor_keywords:
            if keyword in text_lower:
                mentioned.append(keyword.title())
        
        return list(set(mentioned))
    
    def _extract_advantages(self, text: str) -> List[str]:
        """Extract competitive advantages mentioned."""
        advantage_patterns = [
            "better", "faster", "more reliable", "cheaper", "superior", "advantage"
        ]
        advantages = []
        text_lower = text.lower()
        
        for pattern in advantage_patterns:
            if pattern in text_lower:
                advantages.append(f"Highlighted: {pattern}")
        
        return advantages
    
    def _extract_weaknesses(self, text: str) -> List[str]:
        """Extract competitive weaknesses exposed."""
        weakness_patterns = [
            "problem with", "issue with", "slow", "expensive", "unreliable"
        ]
        weaknesses = []
        text_lower = text.lower()
        
        for pattern in weakness_patterns:
            if pattern in text_lower:
                weaknesses.append(f"Exposed: {pattern}")
        
        return weaknesses
    
    def _evaluate_positioning(self, text: str) -> float:
        """Evaluate positioning effectiveness."""
        positive_indicators = [
            "advantage", "benefit", "value", "superior", "better"
        ]
        text_lower = text.lower()
        score = sum(1 for indicator in positive_indicators if indicator in text_lower)
        return min(score / 10, 1.0)
    
    def _calculate_win_probability(self, text: str) -> float:
        """Calculate win probability against competitors."""
        positive_signals = ["interested", "prefer", "like", "impressed"]
        negative_signals = ["concerned", "worried", "doubt", "hesitant"]
        
        text_lower = text.lower()
        positive_count = sum(1 for signal in positive_signals if signal in text_lower)
        negative_count = sum(1 for signal in negative_signals if signal in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        return positive_count / (positive_count + negative_count)
    
    def _identify_product_knowledge_gaps(self, analysis_results: List[Dict]) -> List[ProductKnowledgeGap]:
        """Identify product knowledge gaps in agent responses."""
        gaps = []
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            call_id = result.get("call_id", "Unknown")
            
            call_gaps = self._extract_knowledge_gaps(segments, call_id)
            gaps.extend(call_gaps)
        
        return gaps
    
    def _extract_knowledge_gaps(self, segments: List[Dict], call_id: str) -> List[ProductKnowledgeGap]:
        """Extract knowledge gaps from a single call."""
        gaps = []
        
        uncertainty_phrases = [
            "i'm not sure", "let me check", "i don't know", "i'll find out",
            "i need to verify", "i'm not certain"
        ]
        
        for segment in segments:
            if segment.get("speaker") == "agent":
                text = segment.get("text", "").lower()
                if any(phrase in text for phrase in uncertainty_phrases):
                    evidence = DecisionEvidence(
                        decision_type="knowledge_gap",
                        primary_evidence=[
                            TranscriptEvidence(
                                call_id=call_id,
                                transcript_source=f"{call_id}.json",
                                speaker=CallParticipant.AGENT,
                                timestamp=segment.get("timestamp", 0.0),
                                evidence_text=segment.get("text", ""),
                                context="Agent knowledge uncertainty",
                                confidence_score=0.8
                            )
                        ],
                        confidence_level=0.7,
                        analysis_methodology="Uncertainty phrase detection"
                    )
                    
                    gaps.append(ProductKnowledgeGap(
                        topic=self._categorize_knowledge_topic(text),
                        severity=RiskLevel.MEDIUM,
                        agent_response_quality=0.3,
                        customer_question=self._find_preceding_question(segments, segment),
                        recommended_training=f"Training on {self._categorize_knowledge_topic(text)}",
                        evidence=evidence
                    ))
        
        return gaps
    
    def _categorize_knowledge_topic(self, text: str) -> str:
        """Categorize the knowledge topic based on text content."""
        topics = {
            "pricing": ["price", "cost", "fee", "charge"],
            "technical": ["technical", "setup", "configure", "install"],
            "features": ["feature", "capability", "function"],
            "policy": ["policy", "terms", "conditions", "contract"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return "general"
    
    def _find_preceding_question(self, segments: List[Dict], current_segment: Dict) -> str:
        """Find the customer question that preceded the agent's uncertain response."""
        current_timestamp = current_segment.get("timestamp", 0)
        
        # Look for the most recent customer segment
        for segment in reversed(segments):
            if (segment.get("speaker") == "customer" and 
                segment.get("timestamp", 0) < current_timestamp):
                return segment.get("text", "")
        
        return "Unknown question"
    
    def _analyze_follow_up_adherence(self, analysis_results: List[Dict]) -> List[FollowUpAnalysis]:
        """Analyze follow-up commitments and adherence."""
        follow_ups = []
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            transcript_text = " ".join([seg.get("text", "") for seg in segments])
            
            if any(phrase in transcript_text.lower() for phrase in [
                "follow up", "call back", "contact you", "schedule", "send"
            ]):
                follow_ups.append(FollowUpAnalysis(
                    follow_up_promised=True,
                    follow_up_timeline=self._extract_timeline(transcript_text),
                    follow_up_type=self._classify_follow_up_type(transcript_text),
                    commitment_specificity=self._evaluate_commitment_specificity(transcript_text),
                    adherence_likelihood=self._predict_adherence_likelihood(transcript_text)
                ))
        
        return follow_ups
    
    def _extract_timeline(self, text: str) -> str:
        """Extract follow-up timeline from text."""
        timeline_patterns = [
            "tomorrow", "next week", "in a few days", "by friday", "end of week"
        ]
        text_lower = text.lower()
        
        for pattern in timeline_patterns:
            if pattern in text_lower:
                return pattern
        
        return "unspecified"
    
    def _classify_follow_up_type(self, text: str) -> str:
        """Classify the type of follow-up promised."""
        if "call" in text.lower():
            return "call"
        elif "email" in text.lower():
            return "email"
        elif "demo" in text.lower():
            return "demo"
        elif "proposal" in text.lower():
            return "proposal"
        else:
            return "unspecified"
    
    def _evaluate_commitment_specificity(self, text: str) -> float:
        """Evaluate how specific the follow-up commitment is."""
        specific_indicators = [
            "specific time", "exact date", "calendar", "schedule", "appointment"
        ]
        text_lower = text.lower()
        score = sum(1 for indicator in specific_indicators if indicator in text_lower)
        return min(score / 3, 1.0)
    
    def _predict_adherence_likelihood(self, text: str) -> float:
        """Predict likelihood of follow-up adherence."""
        commitment_indicators = [
            "will", "promise", "definitely", "absolutely", "committed"
        ]
        text_lower = text.lower()
        score = sum(1 for indicator in commitment_indicators if indicator in text_lower)
        return min(0.5 + (score * 0.2), 1.0)
    
    def _analyze_pipeline_health_detailed(self, analysis_results: List[Dict]) -> List[PipelineHealthIndicator]:
        """Analyze detailed pipeline health indicators."""
        pipeline_indicators = []
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            transcript_text = " ".join([seg.get("text", "") for seg in segments])
            
            stage = self._determine_pipeline_stage(transcript_text)
            
            pipeline_indicators.append(PipelineHealthIndicator(
                stage=stage,
                stage_progression_probability=self._calculate_progression_probability(transcript_text, stage),
                deal_velocity_score=self._calculate_deal_velocity(transcript_text),
                engagement_level=self._measure_engagement_level(segments),
                next_steps_clarity=self._evaluate_next_steps_clarity(transcript_text)
            ))
        
        return pipeline_indicators
    
    def _determine_pipeline_stage(self, text: str) -> str:
        """Determine the pipeline stage based on conversation content."""
        stage_keywords = {
            "prospect": ["interested", "learning", "considering"],
            "qualified": ["budget", "decision maker", "timeline"],
            "demo": ["demonstration", "show", "features"],
            "proposal": ["quote", "proposal", "pricing"],
            "negotiation": ["terms", "contract", "negotiate"],
            "closed": ["agreement", "signed", "purchased"]
        }
        
        text_lower = text.lower()
        for stage, keywords in stage_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return stage
        
        return "prospect"
    
    def _calculate_progression_probability(self, text: str, current_stage: str) -> float:
        """Calculate probability of progressing to next stage."""
        positive_signals = ["interested", "yes", "sounds good", "when", "how"]
        negative_signals = ["not sure", "maybe later", "thinking", "hesitant"]
        
        text_lower = text.lower()
        positive_count = sum(1 for signal in positive_signals if signal in text_lower)
        negative_count = sum(1 for signal in negative_signals if signal in text_lower)
        
        base_probability = 0.5
        adjustment = (positive_count - negative_count) * 0.1
        
        return max(0.0, min(1.0, base_probability + adjustment))
    
    def _calculate_deal_velocity(self, text: str) -> float:
        """Calculate deal velocity score based on urgency indicators."""
        urgency_indicators = ["urgent", "quickly", "asap", "soon", "deadline"]
        delay_indicators = ["slow", "later", "waiting", "delay"]
        
        text_lower = text.lower()
        urgency_score = sum(1 for indicator in urgency_indicators if indicator in text_lower)
        delay_score = sum(1 for indicator in delay_indicators if indicator in text_lower)
        
        return max(0.0, min(1.0, 0.5 + (urgency_score - delay_score) * 0.2))
    
    def _measure_engagement_level(self, segments: List[Dict]) -> float:
        """Measure customer engagement level based on conversation dynamics."""
        if not segments:
            return 0.0
        
        customer_segments = [seg for seg in segments if seg.get("speaker") == "customer"]
        if not customer_segments:
            return 0.0
        
        # Calculate engagement based on response length and frequency
        total_words = sum(len(seg.get("text", "").split()) for seg in customer_segments)
        avg_response_length = total_words / len(customer_segments)
        
        # Normalize to 0-1 scale (assuming 20 words is high engagement)
        return min(avg_response_length / 20, 1.0)
    
    def _evaluate_next_steps_clarity(self, text: str) -> float:
        """Evaluate clarity of next steps discussed."""
        clarity_indicators = [
            "next step", "action item", "will do", "schedule", "plan to"
        ]
        text_lower = text.lower()
        score = sum(1 for indicator in clarity_indicators if indicator in text_lower)
        return min(score / 3, 1.0)
    
    def _calculate_conversion_metrics(self, analysis_results: List[Dict]) -> ConversionMetrics:
        """Calculate conversion rate metrics."""
        total_calls = len(analysis_results)
        if total_calls == 0:
            return ConversionMetrics(
                call_to_demo_probability=0.0,
                demo_to_proposal_probability=0.0,
                proposal_to_close_probability=0.0,
                upsell_cross_sell_probability=0.0,
                retention_probability=0.0
            )
        
        # Analyze conversion indicators
        demo_requests = 0
        proposals_discussed = 0
        closes_attempted = 0
        upsell_opportunities = 0
        retention_discussions = 0
        
        for result in analysis_results:
            segments = result.get("transcript_segments", [])
            transcript_text = " ".join([seg.get("text", "") for seg in segments]).lower()
            
            if any(phrase in transcript_text for phrase in ["demo", "demonstration", "show"]):
                demo_requests += 1
            
            if any(phrase in transcript_text for phrase in ["proposal", "quote", "pricing"]):
                proposals_discussed += 1
            
            if any(phrase in transcript_text for phrase in ["purchase", "buy", "close", "agreement"]):
                closes_attempted += 1
            
            if any(phrase in transcript_text for phrase in ["upgrade", "additional", "more"]):
                upsell_opportunities += 1
            
            if any(phrase in transcript_text for phrase in ["cancel", "switch", "retention"]):
                retention_discussions += 1
        
        # Ensure all probabilities are properly bounded between 0 and 1
        return ConversionMetrics(
            call_to_demo_probability=min(1.0, max(0.0, demo_requests / total_calls)),
            demo_to_proposal_probability=min(1.0, max(0.0, proposals_discussed / max(demo_requests, 1))),
            proposal_to_close_probability=min(1.0, max(0.0, closes_attempted / max(proposals_discussed, 1))),
            upsell_cross_sell_probability=min(1.0, max(0.0, upsell_opportunities / total_calls)),
            retention_probability=min(1.0, max(0.0, 1.0 - (retention_discussions / total_calls))) if retention_discussions > 0 else 0.9
        )