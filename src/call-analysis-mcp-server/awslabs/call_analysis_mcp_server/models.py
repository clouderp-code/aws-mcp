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