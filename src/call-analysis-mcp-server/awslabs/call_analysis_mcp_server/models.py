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

"""Data models for call analysis and KPI generation."""

from datetime import datetime
from typing import Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field


class SentimentType(str, Enum):
    """Sentiment analysis types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class CallParticipant(str, Enum):
    """Call participants."""
    AGENT = "agent"
    CUSTOMER = "customer"
    SYSTEM = "system"


class RiskLevel(str, Enum):
    """Risk level indicators."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# NEW: Evidence and Reference Models

class TranscriptEvidence(BaseModel):
    """Evidence from transcript supporting a specific insight."""
    
    call_id: str = Field(description="Call identifier")
    transcript_source: str = Field(description="S3 location or source of transcript")
    speaker: CallParticipant = Field(description="Who said this")
    timestamp: Optional[float] = Field(description="Timestamp in call (seconds)")
    evidence_text: str = Field(description="Actual text from transcript")
    context: str = Field(description="Why this text supports the insight")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in this evidence (0-1)")


class DecisionEvidence(BaseModel):
    """Collection of evidence supporting a business decision."""
    
    decision_type: str = Field(description="Type of decision (risk, opportunity, training_need, etc.)")
    primary_evidence: List[TranscriptEvidence] = Field(description="Main evidence supporting this decision")
    supporting_evidence: List[TranscriptEvidence] = Field(default=[], description="Additional supporting evidence")
    confidence_level: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence in decision")
    analysis_methodology: str = Field(description="How this decision was reached")


class CallCharacteristics(BaseModel):
    """Characteristics of a call transcript."""
    
    total_duration_seconds: float = Field(description="Total call duration in seconds")
    agent_talk_time_seconds: float = Field(description="Agent talk time in seconds")
    customer_talk_time_seconds: float = Field(description="Customer talk time in seconds")
    silence_duration_seconds: float = Field(description="Total silence duration in seconds")
    
    agent_talk_ratio: float = Field(description="Ratio of agent talk time to total duration")
    customer_talk_ratio: float = Field(description="Ratio of customer talk time to total duration")
    
    total_words: int = Field(description="Total number of words spoken")
    agent_words: int = Field(description="Number of words spoken by agent")
    customer_words: int = Field(description="Number of words spoken by customer")
    
    interruptions_by_agent: int = Field(description="Number of times agent interrupted customer")
    interruptions_by_customer: int = Field(description="Number of times customer interrupted agent")
    
    speaking_rate_agent_wpm: float = Field(description="Agent speaking rate in words per minute")
    speaking_rate_customer_wpm: float = Field(description="Customer speaking rate in words per minute")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis results."""
    
    overall_sentiment: SentimentType = Field(description="Overall call sentiment")
    agent_sentiment: SentimentType = Field(description="Agent sentiment")
    customer_sentiment: SentimentType = Field(description="Customer sentiment")
    
    sentiment_scores: Dict[str, float] = Field(description="Detailed sentiment scores (positive, negative, neutral)")
    sentiment_over_time: List[Dict[str, Union[float, str]]] = Field(description="Sentiment changes throughout the call")
    
    emotional_peaks: List[Dict[str, Union[float, str]]] = Field(description="Moments of high emotional intensity")
    sentiment_transitions: int = Field(description="Number of sentiment changes during the call")


class ConversationFlow(BaseModel):
    """Analysis of conversation flow and structure."""
    
    turn_taking_frequency: float = Field(description="Average time between speaker changes")
    conversation_segments: List[Dict[str, Union[str, float]]] = Field(description="Identified conversation segments")
    
    opening_quality_score: float = Field(0.0, ge=0.0, le=10.0, description="Quality of call opening (0-10)")
    closing_quality_score: float = Field(0.0, ge=0.0, le=10.0, description="Quality of call closing (0-10)")
    
    topic_changes: int = Field(description="Number of topic transitions")
    agenda_adherence_score: float = Field(0.0, ge=0.0, le=10.0, description="How well the call followed an agenda (0-10)")


class KeyTopics(BaseModel):
    """Key topics and themes identified in the call."""
    
    primary_topics: List[str] = Field(description="Main topics discussed")
    secondary_topics: List[str] = Field(description="Secondary topics mentioned")
    
    keywords_frequency: Dict[str, int] = Field(description="Frequency of important keywords")
    named_entities: List[Dict[str, str]] = Field(description="Named entities (people, organizations, locations)")
    
    business_intent: Optional[str] = Field(description="Primary business intent of the call")
    call_outcome: Optional[str] = Field(description="Outcome or resolution of the call")


class ComplianceMetrics(BaseModel):
    """Compliance and quality metrics."""
    
    compliance_score: float = Field(0.0, ge=0.0, le=10.0, description="Overall compliance score (0-10)")
    
    required_disclosures_made: List[str] = Field(description="Required disclosures that were made")
    missing_disclosures: List[str] = Field(description="Required disclosures that were missed")
    
    escalation_offered: bool = Field(description="Whether escalation was offered when appropriate")
    hold_time_appropriate: bool = Field(description="Whether hold times were appropriate")
    
    privacy_compliance: bool = Field(description="Whether privacy requirements were met")
    security_compliance: bool = Field(description="Whether security protocols were followed")


class PerformanceKPIs(BaseModel):
    """Key Performance Indicators for the call."""
    
    # Customer satisfaction indicators
    customer_satisfaction_score: float = Field(0.0, ge=0.0, le=10.0, description="Estimated customer satisfaction (0-10)")
    first_call_resolution: bool = Field(description="Whether issue was resolved on first call")
    
    # Agent performance
    agent_professionalism_score: float = Field(0.0, ge=0.0, le=10.0, description="Agent professionalism score (0-10)")
    agent_knowledge_score: float = Field(0.0, ge=0.0, le=10.0, description="Agent knowledge demonstration score (0-10)")
    agent_empathy_score: float = Field(0.0, ge=0.0, le=10.0, description="Agent empathy score (0-10)")
    
    # Efficiency metrics
    call_efficiency_score: float = Field(0.0, ge=0.0, le=10.0, description="Call efficiency score (0-10)")
    issue_resolution_time: float = Field(description="Time to resolve the issue in seconds")
    
    # Communication quality
    clarity_score: float = Field(0.0, ge=0.0, le=10.0, description="Communication clarity score (0-10)")
    active_listening_score: float = Field(0.0, ge=0.0, le=10.0, description="Active listening demonstration score (0-10)")


class TranscriptSegment(BaseModel):
    """A segment of the call transcript."""
    
    timestamp: float = Field(description="Timestamp of the segment in seconds")
    speaker: CallParticipant = Field(description="Who is speaking")
    text: str = Field(description="The spoken text")
    duration: float = Field(description="Duration of this segment in seconds")
    confidence: Optional[float] = Field(description="Transcription confidence score")


# ENHANCED BUSINESS INTELLIGENCE MODELS WITH EVIDENCE

class DealRiskIndicator(BaseModel):
    """Deal at risk identification with supporting evidence."""
    
    account_name: str = Field(description="Account/company name")
    agent_name: str = Field(description="Agent handling the account")
    risk_level: RiskLevel = Field(description="Risk level assessment")
    risk_factors: List[str] = Field(description="Specific risk factors identified")
    recommended_actions: List[str] = Field(description="Suggested remediation actions")
    win_probability_change: float = Field(description="Change in win probability (-1.0 to 1.0)")
    account_value: Optional[float] = Field(description="Value of account at risk")
    
    # Evidence trail
    evidence: DecisionEvidence = Field(description="Supporting evidence from transcripts")
    risk_score_breakdown: Dict[str, float] = Field(description="Detailed scoring for each risk factor")


class ChurnRiskIndicator(BaseModel):
    """Customer churn risk assessment with evidence."""
    
    account_name: str = Field(description="Account/company name")
    churn_probability: float = Field(0.0, ge=0.0, le=1.0, description="Probability of churn (0-1)")
    risk_signals: List[str] = Field(description="Phrases/behaviors indicating churn risk")
    intervention_urgency: RiskLevel = Field(description="Urgency level for intervention")
    recommended_actions: List[str] = Field(description="Recommended retention actions")
    account_value_at_risk: Optional[float] = Field(description="Annual value at risk")
    
    # Evidence trail
    evidence: DecisionEvidence = Field(description="Supporting evidence from transcripts")
    churn_indicators_timeline: List[Dict[str, Union[str, float]]] = Field(description="Timeline of churn signals")


class OpportunityIndicator(BaseModel):
    """New business opportunity identification with evidence."""
    
    account_name: str = Field(description="Account/company name")
    opportunity_type: str = Field(description="Type of opportunity (upsell, cross-sell, new)")
    estimated_value: float = Field(description="Estimated opportunity value")
    confidence_level: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in opportunity (0-1)")
    next_steps: List[str] = Field(description="Recommended next steps")
    timeline: Optional[str] = Field(description="Expected timeline for opportunity")
    
    # Evidence trail
    evidence: DecisionEvidence = Field(description="Supporting evidence from transcripts")
    opportunity_signals_strength: Dict[str, float] = Field(description="Strength of each opportunity signal")


class ObjectionPattern(BaseModel):
    """Recurring objection analysis with evidence."""
    
    objection_text: str = Field(description="The objection phrase or theme")
    frequency: int = Field(description="Number of times this objection appeared")
    frequency_percentage: float = Field(description="Percentage of total calls with this objection")
    impact_on_conversion: float = Field(description="Impact on conversion rate (-1.0 to 1.0)")
    suggested_responses: List[str] = Field(description="Recommended response strategies")
    training_materials_needed: List[str] = Field(description="Training resources to address this objection")
    
    # Evidence trail
    example_objections: List[TranscriptEvidence] = Field(description="Actual objection examples from transcripts")
    successful_responses: List[TranscriptEvidence] = Field(default=[], description="Examples of successful objection handling")


class AgentTrainingNeed(BaseModel):
    """Agent training requirement identification with evidence."""
    
    agent_name: str = Field(description="Agent requiring training")
    skill_gaps: List[str] = Field(description="Identified skill gaps")
    performance_metrics: Dict[str, float] = Field(description="Current performance scores")
    training_priority: RiskLevel = Field(description="Priority level for training")
    recommended_training: List[str] = Field(description="Specific training recommendations")
    improvement_potential: float = Field(0.0, ge=0.0, le=1.0, description="Potential for improvement (0-1)")
    
    # Evidence trail
    evidence: DecisionEvidence = Field(description="Supporting evidence from transcripts")
    performance_examples: List[TranscriptEvidence] = Field(description="Specific examples of performance issues")
    improvement_opportunities: List[TranscriptEvidence] = Field(description="Moments where better skills would have helped")



class CallQualityIssue(BaseModel):
    """Call quality problem identification with evidence."""
    
    issue_type: str = Field(description="Type of quality issue")
    frequency: int = Field(description="Number of occurrences")
    affected_calls_percentage: float = Field(description="Percentage of calls affected")
    impact_severity: RiskLevel = Field(description="Impact severity level")
    root_causes: List[str] = Field(description="Identified root causes")
    recommended_solutions: List[str] = Field(description="Suggested solutions")
    
    # Evidence trail
    example_occurrences: List[TranscriptEvidence] = Field(description="Specific examples of this quality issue")


# Advanced Analytics Models
class CallCategory(str, Enum):
    """Call categorization types."""
    TECHNICAL_COMPLAINT = "technical_complaint"
    PRICE_OBJECTION = "price_objection"
    NEW_BUSINESS_INQUIRY = "new_business_inquiry"
    SETUP_INQUIRY = "setup_inquiry"
    BILLING_INQUIRY = "billing_inquiry"
    FEATURE_REQUEST = "feature_request"
    CANCELLATION_REQUEST = "cancellation_request"
    SUPPORT_REQUEST = "support_request"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    RETENTION_CALL = "retention_call"


class ObjectionType(str, Enum):
    """Types of customer objections."""
    PRICE = "price"
    COMPETITOR = "competitor"
    FEATURE_MISSING = "feature_missing"
    TIMING = "timing"
    BUDGET = "budget"
    DECISION_MAKER = "decision_maker"
    TRUST = "trust"
    COMPLEXITY = "complexity"


class ObjectionAnalysis(BaseModel):
    """Analysis of customer objections."""
    objection_type: ObjectionType
    objection_text: str
    agent_response: str
    response_effectiveness: float = Field(ge=0, le=1, description="0-1 scale")
    resolution_status: str  # handled, unresolved, escalated
    evidence: DecisionEvidence


class ResolutionMetrics(BaseModel):
    """Call resolution and efficiency metrics."""
    call_duration_minutes: float
    resolution_time_minutes: Optional[float]
    first_call_resolution: bool
    escalation_required: bool
    follow_up_scheduled: bool
    customer_effort_score: float = Field(ge=1, le=5, description="1-5 scale")


class CompetitiveAnalysis(BaseModel):
    """Competitive positioning analysis."""
    competitors_mentioned: List[str]
    competitive_advantages_highlighted: List[str]
    competitive_weaknesses_exposed: List[str]
    positioning_effectiveness: float = Field(ge=0, le=1, description="0-1 scale")
    win_probability_vs_competitor: float = Field(ge=0, le=1, description="0-1 scale")


class ProductKnowledgeGap(BaseModel):
    """Product knowledge gaps identified."""
    topic: str
    severity: RiskLevel
    agent_response_quality: float = Field(ge=0, le=1, description="0-1 scale")
    customer_question: str
    recommended_training: str
    evidence: DecisionEvidence


class FollowUpAnalysis(BaseModel):
    """Follow-up adherence and effectiveness."""
    follow_up_promised: bool
    follow_up_timeline: Optional[str]
    follow_up_type: str  # call, email, demo, proposal
    commitment_specificity: float = Field(ge=0, le=1, description="0-1 scale")
    adherence_likelihood: float = Field(ge=0, le=1, description="0-1 scale")


class PipelineHealthIndicator(BaseModel):
    """Pipeline health metrics."""
    stage: str  # prospect, qualified, demo, proposal, negotiation, closed
    stage_progression_probability: float = Field(ge=0, le=1, description="0-1 scale")
    deal_velocity_score: float = Field(ge=0, le=1, description="0-1 scale")
    engagement_level: float = Field(ge=0, le=1, description="0-1 scale")
    next_steps_clarity: float = Field(ge=0, le=1, description="0-1 scale")


class ConversionMetrics(BaseModel):
    """Conversion rate analysis."""
    call_to_demo_probability: float = Field(ge=0, le=1, description="0-1 scale")
    demo_to_proposal_probability: float = Field(ge=0, le=1, description="0-1 scale")
    proposal_to_close_probability: float = Field(ge=0, le=1, description="0-1 scale")
    upsell_cross_sell_probability: float = Field(ge=0, le=1, description="0-1 scale")
    retention_probability: float = Field(ge=0, le=1, description="0-1 scale")


class BusinessIntelligenceInsights(BaseModel):
    """Comprehensive business intelligence insights from call analysis with full evidence trails."""
    
    # Time period and scope
    analysis_period: str = Field(description="Time period analyzed (e.g., 'Today', 'This week')")
    total_calls_analyzed: int = Field(description="Total number of calls in analysis")
    analysis_timestamp: datetime = Field(description="When this analysis was generated")
    
    # Overall quality summary
    overall_quality_score: float = Field(0.0, ge=0.0, le=10.0, description="Overall call quality score")
    quality_trend: str = Field(description="Quality trend (improving, declining, stable)")
    calls_with_issues: int = Field(description="Number of calls with quality issues")
    calls_with_issues_percentage: float = Field(description="Percentage of calls with issues")
    
    # Risk and opportunity identification (now with evidence)
    deals_at_risk: List[DealRiskIndicator] = Field(description="Deals identified as at-risk with evidence")
    churn_risks: List[ChurnRiskIndicator] = Field(description="Accounts at risk of churning with evidence")
    new_opportunities: List[OpportunityIndicator] = Field(description="New business opportunities with evidence")
    
    # Performance insights (now with evidence)
    agent_training_needs: List[AgentTrainingNeed] = Field(description="Agents requiring training with evidence")
    pipeline_health: List[PipelineHealthIndicator] = Field(description="Pipeline stage health with supporting data")
    recurring_objections: List[ObjectionPattern] = Field(description="Common objection patterns with examples")
    
    # Quality issues (now with evidence)
    call_quality_issues: List[CallQualityIssue] = Field(description="Technical and process quality issues with examples")
    
    # Aggregate metrics
    average_sentiment_score: float = Field(description="Average sentiment across all calls")
    average_customer_satisfaction: float = Field(description="Average customer satisfaction score")
    first_call_resolution_rate: float = Field(description="Percentage of calls resolved on first contact")
    average_call_duration: float = Field(description="Average call duration in minutes")
    
    # Actionable insights
    top_priorities: List[str] = Field(description="Top 3 priority actions based on analysis")
    success_indicators: List[str] = Field(description="Positive trends and successes")
    areas_for_improvement: List[str] = Field(description="Key areas needing attention")
    
    # Evidence metadata
    evidence_summary: Dict[str, int] = Field(
        description="Summary of evidence collected (e.g., total evidence items, calls referenced)"
    )
    
    # Advanced Analytics
    call_categorization: Dict[CallCategory, int] = Field(
        default_factory=dict, description="Distribution of call categories"
    )
    objection_analysis: List[ObjectionAnalysis] = Field(
        default=[], description="Detailed objection analysis"
    )
    resolution_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Resolution efficiency metrics"
    )
    competitive_analysis: List[CompetitiveAnalysis] = Field(
        default=[], description="Competitive positioning analysis"
    )
    product_knowledge_gaps: List[ProductKnowledgeGap] = Field(
        default=[], description="Product knowledge gaps identified"
    )
    follow_up_analysis: List[FollowUpAnalysis] = Field(
        default=[], description="Follow-up commitment analysis"
    )
    pipeline_health: List[PipelineHealthIndicator] = Field(
        default=[], description="Pipeline health indicators"
    )
    conversion_metrics: ConversionMetrics = Field(
        default_factory=lambda: ConversionMetrics(
            call_to_demo_probability=0.0,
            demo_to_proposal_probability=0.0,
            proposal_to_close_probability=0.0,
            upsell_cross_sell_probability=0.0,
            retention_probability=0.0
        ),
        description="Conversion rate analysis"
    )
    
    # Performance Metrics
    average_resolution_time_minutes: float = Field(0.0, description="Average resolution time across calls")
    first_call_resolution_rate: float = Field(0.0, ge=0.0, le=1.0, description="First call resolution rate")
    escalation_rate: float = Field(0.0, ge=0.0, le=1.0, description="Rate of calls requiring escalation")
    follow_up_adherence_rate: float = Field(0.0, ge=0.0, le=1.0, description="Follow-up commitment adherence rate")
    
    # Quality assurance
    analysis_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence in analysis")
    review_recommendations: List[str] = Field(
        description="Recommendations for human review based on evidence quality"
    )


class CallAnalysisResult(BaseModel):
    """Complete analysis result for a call transcript."""
    
    # Metadata
    call_id: str = Field(description="Unique identifier for the call")
    analysis_timestamp: datetime = Field(description="When the analysis was performed")
    transcript_source: str = Field(description="Source location of the transcript")
    
    # Transcript data
    transcript_segments: List[TranscriptSegment] = Field(description="Segmented transcript")
    
    # Analysis results
    characteristics: CallCharacteristics = Field(description="Call characteristics and metrics")
    sentiment_analysis: SentimentAnalysis = Field(description="Sentiment analysis results")
    conversation_flow: ConversationFlow = Field(description="Conversation flow analysis")
    key_topics: KeyTopics = Field(description="Key topics and themes")
    compliance_metrics: ComplianceMetrics = Field(description="Compliance and quality metrics")
    performance_kpis: PerformanceKPIs = Field(description="Key performance indicators")
    
    # Business intelligence flags
    deal_risk_indicators: List[str] = Field(default=[], description="Deal risk signals detected")
    churn_risk_signals: List[str] = Field(default=[], description="Customer churn risk signals")
    opportunity_signals: List[str] = Field(default=[], description="Business opportunity signals")
    training_flags: List[str] = Field(default=[], description="Agent training needs identified")
    quality_issues: List[str] = Field(default=[], description="Call quality issues detected")
    
    # Summary
    executive_summary: str = Field(description="Executive summary of the call")
    recommendations: List[str] = Field(description="Recommendations for improvement")
    action_items: List[str] = Field(description="Action items identified from the call")
    
    # Technical metadata
    analysis_version: str = Field(default="1.0", description="Version of the analysis algorithm")
    processing_time_seconds: float = Field(description="Time taken to process the analysis")


class S3Location(BaseModel):
    """S3 location specification."""
    
    bucket: str = Field(description="S3 bucket name")
    key: str = Field(description="S3 object key")
    region: Optional[str] = Field(description="AWS region")


class AnalysisJob(BaseModel):
    """Analysis job configuration."""
    
    job_id: str = Field(description="Unique job identifier")
    transcript_location: S3Location = Field(description="Location of input transcript")
    output_location: S3Location = Field(description="Location for output files")
    
    created_at: datetime = Field(description="Job creation timestamp")
    started_at: Optional[datetime] = Field(description="Job start timestamp")
    completed_at: Optional[datetime] = Field(description="Job completion timestamp")
    
    status: str = Field(default="pending", description="Job status")
    error_message: Optional[str] = Field(description="Error message if job failed")
    
    analysis_options: Dict[str, bool] = Field(
        default_factory=lambda: {
            "sentiment_analysis": True,
            "topic_extraction": True,
            "compliance_check": True,
            "performance_metrics": True,
            "detailed_flow_analysis": True
        },
        description="Analysis options to enable/disable"
    ) 