"""
Comprehensive tests for call analysis data models.

Tests Pydantic models, enums, validation, and data structures
used throughout the Call Analysis MCP Server.
"""

import pytest
from datetime import datetime
from typing import Dict, List
from pydantic import ValidationError

from awslabs.call_analysis_mcp_server.models import (
    SentimentType,
    CallParticipant,
    RiskLevel,
    TranscriptEvidence,
    DecisionEvidence,
    CallCharacteristics,
    SentimentAnalysis,
    TranscriptSegment,
    CallAnalysisResult,
    BusinessIntelligenceInsights,
    # Import other models as needed
)


class TestEnums:
    """Test enum types."""
    
    def test_sentiment_type_enum(self):
        """Test SentimentType enum values."""
        assert SentimentType.POSITIVE == "positive"
        assert SentimentType.NEGATIVE == "negative"
        assert SentimentType.NEUTRAL == "neutral"
        
        # Test enum membership
        assert "positive" in SentimentType
        assert "invalid" not in SentimentType
    
    def test_call_participant_enum(self):
        """Test CallParticipant enum values."""
        assert CallParticipant.AGENT == "agent"
        assert CallParticipant.CUSTOMER == "customer"
        assert CallParticipant.SYSTEM == "system"
    
    def test_risk_level_enum(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"


class TestTranscriptEvidence:
    """Test TranscriptEvidence model."""
    
    def test_valid_transcript_evidence(self):
        """Test creating valid transcript evidence."""
        evidence = TranscriptEvidence(
            call_id="CALL_001",
            transcript_source="s3://bucket/transcript.json",
            speaker=CallParticipant.CUSTOMER,
            timestamp=120.5,
            evidence_text="I'm really unhappy with the service",
            context="Customer expressing dissatisfaction",
            confidence_score=0.85
        )
        
        assert evidence.call_id == "CALL_001"
        assert evidence.speaker == CallParticipant.CUSTOMER
        assert evidence.timestamp == 120.5
        assert evidence.confidence_score == 0.85
    
    def test_confidence_score_validation(self):
        """Test confidence score validation (0-1 range)."""
        # Valid confidence scores
        for score in [0.0, 0.5, 1.0]:
            evidence = TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/transcript.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="Test text",
                context="Test context",
                confidence_score=score
            )
            assert evidence.confidence_score == score
        
        # Invalid confidence scores
        with pytest.raises(ValidationError):
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/transcript.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="Test text",
                context="Test context",
                confidence_score=1.5  # > 1.0
            )
        
        with pytest.raises(ValidationError):
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/transcript.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="Test text",
                context="Test context",
                confidence_score=-0.1  # < 0.0
            )
    
    def test_optional_timestamp(self):
        """Test that timestamp is optional."""
        evidence = TranscriptEvidence(
            call_id="CALL_001",
            transcript_source="s3://bucket/transcript.json",
            speaker=CallParticipant.CUSTOMER,
            evidence_text="Test text",
            context="Test context",
            confidence_score=0.8
        )
        assert evidence.timestamp is None


class TestDecisionEvidence:
    """Test DecisionEvidence model."""
    
    def test_valid_decision_evidence(self):
        """Test creating valid decision evidence."""
        primary_evidence = [
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/transcript.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="This is too expensive",
                context="Price objection",
                confidence_score=0.9
            )
        ]
        
        decision = DecisionEvidence(
            decision_type="deal_risk",
            primary_evidence=primary_evidence,
            confidence_level=0.85,
            analysis_methodology="Analyzed customer sentiment and price objections"
        )
        
        assert decision.decision_type == "deal_risk"
        assert len(decision.primary_evidence) == 1
        assert decision.confidence_level == 0.85
        assert len(decision.supporting_evidence) == 0  # Default empty list
    
    def test_confidence_level_validation(self):
        """Test confidence level validation."""
        primary_evidence = [
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/transcript.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="Test",
                context="Test",
                confidence_score=0.8
            )
        ]
        
        # Valid confidence levels
        for level in [0.0, 0.5, 1.0]:
            decision = DecisionEvidence(
                decision_type="test",
                primary_evidence=primary_evidence,
                confidence_level=level,
                analysis_methodology="Test"
            )
            assert decision.confidence_level == level
        
        # Invalid confidence levels
        with pytest.raises(ValidationError):
            DecisionEvidence(
                decision_type="test",
                primary_evidence=primary_evidence,
                confidence_level=1.5,  # > 1.0
                analysis_methodology="Test"
            )


class TestCallCharacteristics:
    """Test CallCharacteristics model."""
    
    def test_valid_call_characteristics(self):
        """Test creating valid call characteristics."""
        characteristics = CallCharacteristics(
            total_duration_seconds=600.0,
            agent_talk_time_seconds=360.0,
            customer_talk_time_seconds=240.0,
            silence_duration_seconds=0.0,
            agent_talk_ratio=0.6,
            customer_talk_ratio=0.4,
            total_words=150,
            agent_words=90,
            customer_words=60,
            interruptions_by_agent=2,
            interruptions_by_customer=1,
            speaking_rate_agent_wpm=150.0,
            speaking_rate_customer_wpm=120.0
        )
        
        assert characteristics.total_duration_seconds == 600.0
        assert characteristics.agent_talk_ratio == 0.6
        assert characteristics.customer_talk_ratio == 0.4
        assert characteristics.total_words == 150
        assert characteristics.interruptions_by_agent == 2
    
    def test_calculated_ratios(self):
        """Test that talk ratios are calculated correctly."""
        characteristics = CallCharacteristics(
            total_duration_seconds=100.0,
            agent_talk_time_seconds=70.0,
            customer_talk_time_seconds=30.0,
            silence_duration_seconds=0.0,
            agent_talk_ratio=0.7,  # 70/100
            customer_talk_ratio=0.3,  # 30/100
            total_words=100,
            agent_words=70,
            customer_words=30,
            interruptions_by_agent=0,
            interruptions_by_customer=0,
            speaking_rate_agent_wpm=120.0,
            speaking_rate_customer_wpm=120.0
        )
        
        # Verify the ratios match the time proportions
        assert abs(characteristics.agent_talk_ratio - 0.7) < 0.01
        assert abs(characteristics.customer_talk_ratio - 0.3) < 0.01


class TestSentimentAnalysis:
    """Test SentimentAnalysis model."""
    
    def test_valid_sentiment_analysis(self):
        """Test creating valid sentiment analysis."""
        sentiment = SentimentAnalysis(
            overall_sentiment=SentimentType.POSITIVE,
            agent_sentiment=SentimentType.POSITIVE,
            customer_sentiment=SentimentType.NEUTRAL,
            sentiment_scores={
                "positive": 0.7,
                "negative": 0.1,
                "neutral": 0.2
            },
            sentiment_over_time=[
                {"timestamp": 0.0, "sentiment": "neutral", "score": 0.5},
                {"timestamp": 60.0, "sentiment": "positive", "score": 0.7}
            ]
        )
        
        assert sentiment.overall_sentiment == SentimentType.POSITIVE
        assert sentiment.agent_sentiment == SentimentType.POSITIVE
        assert sentiment.customer_sentiment == SentimentType.NEUTRAL
        assert len(sentiment.sentiment_scores) == 3
        assert len(sentiment.sentiment_over_time) == 2
    
    def test_sentiment_enum_validation(self):
        """Test that sentiment fields validate enum values."""
        # Valid sentiment types
        sentiment = SentimentAnalysis(
            overall_sentiment=SentimentType.NEGATIVE,
            agent_sentiment=SentimentType.POSITIVE,
            customer_sentiment=SentimentType.NEUTRAL,
            sentiment_scores={},
            sentiment_over_time=[]
        )
        assert sentiment.overall_sentiment == SentimentType.NEGATIVE
        
        # Invalid sentiment type should raise ValidationError
        with pytest.raises(ValidationError):
            SentimentAnalysis(
                overall_sentiment="invalid_sentiment",  # Not a valid SentimentType
                agent_sentiment=SentimentType.POSITIVE,
                customer_sentiment=SentimentType.NEUTRAL,
                sentiment_scores={},
                sentiment_over_time=[]
            )


class TestTranscriptSegment:
    """Test TranscriptSegment model."""
    
    def test_valid_transcript_segment(self):
        """Test creating valid transcript segment."""
        segment = TranscriptSegment(
            timestamp=120.5,
            speaker=CallParticipant.AGENT,
            text="How can I help you today?",
            duration=3.2,
            confidence=0.95
        )
        
        assert segment.timestamp == 120.5
        assert segment.speaker == CallParticipant.AGENT
        assert segment.text == "How can I help you today?"
        assert segment.duration == 3.2
        assert segment.confidence == 0.95
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence scores
        for confidence in [0.0, 0.5, 1.0]:
            segment = TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.AGENT,
                text="Test",
                duration=1.0,
                confidence=confidence
            )
            assert segment.confidence == confidence
        
        # Invalid confidence scores
        with pytest.raises(ValidationError):
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.AGENT,
                text="Test",
                duration=1.0,
                confidence=1.5  # > 1.0
            )


class TestModelIntegration:
    """Test model integration and complex scenarios."""
    
    def test_evidence_with_multiple_sources(self):
        """Test decision evidence with multiple transcript sources."""
        evidence1 = TranscriptEvidence(
            call_id="CALL_001",
            transcript_source="s3://bucket/call1.json",
            speaker=CallParticipant.CUSTOMER,
            evidence_text="This is too expensive",
            context="Price concern",
            confidence_score=0.9
        )
        
        evidence2 = TranscriptEvidence(
            call_id="CALL_002", 
            transcript_source="s3://bucket/call2.json",
            speaker=CallParticipant.CUSTOMER,
            evidence_text="We're looking at competitors",
            context="Competitive threat",
            confidence_score=0.8
        )
        
        decision = DecisionEvidence(
            decision_type="deal_risk",
            primary_evidence=[evidence1],
            supporting_evidence=[evidence2],
            confidence_level=0.85,
            analysis_methodology="Multiple price and competitive signals"
        )
        
        assert len(decision.primary_evidence) == 1
        assert len(decision.supporting_evidence) == 1
        assert decision.primary_evidence[0].call_id == "CALL_001"
        assert decision.supporting_evidence[0].call_id == "CALL_002"
    
    def test_json_serialization(self):
        """Test that models can be serialized to JSON."""
        evidence = TranscriptEvidence(
            call_id="CALL_001",
            transcript_source="s3://bucket/transcript.json",
            speaker=CallParticipant.CUSTOMER,
            evidence_text="Test text",
            context="Test context",
            confidence_score=0.8
        )
        
        # Should be able to serialize to dict
        evidence_dict = evidence.model_dump()
        assert evidence_dict["call_id"] == "CALL_001"
        assert evidence_dict["speaker"] == "customer"  # Enum serialized as string
        assert evidence_dict["confidence_score"] == 0.8
        
        # Should be able to serialize to JSON string
        json_str = evidence.model_dump_json()
        assert "CALL_001" in json_str
        assert "customer" in json_str
    
    def test_model_reconstruction(self):
        """Test that models can be reconstructed from dict."""
        original_data = {
            "call_id": "CALL_001",
            "transcript_source": "s3://bucket/transcript.json",
            "speaker": "customer",
            "evidence_text": "Test text",
            "context": "Test context",
            "confidence_score": 0.8
        }
        
        evidence = TranscriptEvidence(**original_data)
        assert evidence.call_id == "CALL_001"
        assert evidence.speaker == CallParticipant.CUSTOMER
        assert evidence.confidence_score == 0.8
        
        # Round trip test
        reconstructed_data = evidence.model_dump()
        evidence2 = TranscriptEvidence(**reconstructed_data)
        assert evidence2.call_id == evidence.call_id
        assert evidence2.speaker == evidence.speaker
        assert evidence2.confidence_score == evidence.confidence_score