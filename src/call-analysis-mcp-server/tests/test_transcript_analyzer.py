"""
Comprehensive tests for TranscriptAnalyzer service.

Tests transcript parsing, sentiment analysis, KPI calculation,
and performance metrics generation.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from awslabs.call_analysis_mcp_server.services.transcript_analyzer import TranscriptAnalyzer
from awslabs.call_analysis_mcp_server.models import (
    TranscriptSegment,
    CallParticipant,
    SentimentType,
    CallAnalysisResult,
    CallCharacteristics,
    SentimentAnalysis,
    PerformanceKPIs,
    ComplianceMetrics,
    ConversationFlow,
    KeyTopics
)


@pytest.fixture
def transcript_analyzer():
    """Create a TranscriptAnalyzer instance for testing."""
    return TranscriptAnalyzer()


@pytest.fixture
def sample_json_transcript():
    """Sample JSON transcript for testing."""
    return json.dumps({
        "call_id": "TEST_CALL_001",
        "transcript": [
            {
                "speaker": "agent",
                "text": "Thank you for calling. How can I help you today?",
                "timestamp": "00:00",
                "duration": 4.5
            },
            {
                "speaker": "customer", 
                "text": "I'm having issues with my billing. I'm frustrated with the service.",
                "timestamp": "00:05",
                "duration": 6.2
            },
            {
                "speaker": "agent",
                "text": "I understand your frustration. Let me look into your account immediately.",
                "timestamp": "00:12",
                "duration": 5.8
            },
            {
                "speaker": "customer",
                "text": "Thank you, I appreciate your help.",
                "timestamp": "00:18", 
                "duration": 3.1
            }
        ]
    })


@pytest.fixture
def sample_csv_transcript():
    """Sample CSV transcript for testing."""
    return """timestamp,speaker,text,duration
0.0,agent,"Thank you for calling. How can I help you today?",4.5
5.0,customer,"I'm having issues with my billing. I'm frustrated with the service.",6.2
12.0,agent,"I understand your frustration. Let me look into your account immediately.",5.8
18.0,customer,"Thank you, I appreciate your help.",3.1"""


@pytest.fixture
def sample_text_transcript():
    """Sample plain text transcript for testing."""
    return """[00:00] Agent: Thank you for calling. How can I help you today?
[00:05] Customer: I'm having issues with my billing. I'm frustrated with the service.
[00:12] Agent: I understand your frustration. Let me look into your account immediately.
[00:18] Customer: Thank you, I appreciate your help."""


@pytest.fixture
def sample_segments():
    """Sample transcript segments for testing."""
    return [
        TranscriptSegment(
            timestamp=0.0,
            speaker=CallParticipant.AGENT,
            text="Thank you for calling. How can I help you today?",
            duration=4.5,
            confidence=0.95
        ),
        TranscriptSegment(
            timestamp=5.0,
            speaker=CallParticipant.CUSTOMER,
            text="I'm having issues with my billing. I'm frustrated with the service.",
            duration=6.2,
            confidence=0.92
        ),
        TranscriptSegment(
            timestamp=12.0,
            speaker=CallParticipant.AGENT,
            text="I understand your frustration. Let me look into your account immediately.",
            duration=5.8,
            confidence=0.94
        ),
        TranscriptSegment(
            timestamp=18.0,
            speaker=CallParticipant.CUSTOMER,
            text="Thank you, I appreciate your help.",
            duration=3.1,
            confidence=0.96
        )
    ]


class TestTranscriptParsing:
    """Test transcript parsing functionality."""
    
    def test_parse_json_transcript(self, transcript_analyzer, sample_json_transcript):
        """Test parsing JSON format transcript."""
        segments = transcript_analyzer.parse_transcript(sample_json_transcript, "json")
        
        assert len(segments) == 4
        assert segments[0].speaker == CallParticipant.AGENT
        assert segments[1].speaker == CallParticipant.CUSTOMER
        assert "help you today" in segments[0].text
        assert "billing" in segments[1].text
    
    def test_parse_csv_transcript(self, transcript_analyzer, sample_csv_transcript):
        """Test parsing CSV format transcript."""
        segments = transcript_analyzer.parse_transcript(sample_csv_transcript, "csv")
        
        assert len(segments) == 4
        assert segments[0].speaker == CallParticipant.AGENT
        assert segments[1].speaker == CallParticipant.CUSTOMER
        assert segments[0].timestamp == 0.0
        assert segments[1].timestamp == 5.0
    
    def test_parse_text_transcript(self, transcript_analyzer, sample_text_transcript):
        """Test parsing plain text format transcript."""
        segments = transcript_analyzer.parse_transcript(sample_text_transcript, "text")
        
        assert len(segments) >= 2  # Should extract at least 2 segments
        # Check that speakers are properly identified
        speakers = [seg.speaker for seg in segments]
        assert CallParticipant.AGENT in speakers
        assert CallParticipant.CUSTOMER in speakers
    
    def test_parse_invalid_json(self, transcript_analyzer):
        """Test handling of invalid JSON."""
        invalid_json = '{"invalid": json'
        
        with pytest.raises(Exception):  # Should raise some parsing exception
            transcript_analyzer.parse_transcript(invalid_json, "json")
    
    def test_auto_format_detection(self, transcript_analyzer, sample_json_transcript):
        """Test automatic format detection."""
        # Should detect JSON format automatically
        segments = transcript_analyzer.parse_transcript(sample_json_transcript)
        
        assert len(segments) > 0
        assert isinstance(segments[0], TranscriptSegment)
    
    def test_empty_transcript(self, transcript_analyzer):
        """Test handling of empty transcript."""
        segments = transcript_analyzer.parse_transcript("", "text")
        assert len(segments) == 0
        
        segments = transcript_analyzer.parse_transcript("{}", "json")
        assert len(segments) == 0


class TestCallCharacteristics:
    """Test call characteristics calculation."""
    
    def test_calculate_characteristics(self, transcript_analyzer, sample_segments):
        """Test calculation of call characteristics."""
        characteristics = transcript_analyzer.calculate_call_characteristics(sample_segments)
        
        assert isinstance(characteristics, CallCharacteristics)
        assert characteristics.total_duration_seconds > 0
        assert characteristics.agent_talk_time_seconds > 0
        assert characteristics.customer_talk_time_seconds > 0
        assert characteristics.total_words > 0
        
        # Check ratios are reasonable
        assert 0 <= characteristics.agent_talk_ratio <= 1
        assert 0 <= characteristics.customer_talk_ratio <= 1
        
        # Check word counts
        assert characteristics.agent_words > 0
        assert characteristics.customer_words > 0
        assert characteristics.agent_words + characteristics.customer_words == characteristics.total_words
    
    def test_speaking_rates(self, transcript_analyzer, sample_segments):
        """Test speaking rate calculations."""
        characteristics = transcript_analyzer.calculate_call_characteristics(sample_segments)
        
        assert characteristics.speaking_rate_agent_wpm > 0
        assert characteristics.speaking_rate_customer_wpm > 0
        # Reasonable speaking rates (typically 100-200 WPM)
        assert 50 <= characteristics.speaking_rate_agent_wpm <= 300
        assert 50 <= characteristics.speaking_rate_customer_wpm <= 300
    
    def test_empty_segments(self, transcript_analyzer):
        """Test characteristics calculation with empty segments."""
        characteristics = transcript_analyzer.calculate_call_characteristics([])
        
        assert characteristics.total_duration_seconds == 0
        assert characteristics.total_words == 0
        assert characteristics.agent_talk_ratio == 0
        assert characteristics.customer_talk_ratio == 0


class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""
    
    @patch('awslabs.call_analysis_mcp_server.services.transcript_analyzer.SentimentIntensityAnalyzer')
    def test_analyze_sentiment(self, mock_vader, transcript_analyzer, sample_segments):
        """Test sentiment analysis with mocked VADER."""
        # Mock VADER analyzer
        mock_analyzer = Mock()
        mock_analyzer.polarity_scores.side_effect = [
            {'compound': 0.5, 'pos': 0.6, 'neu': 0.3, 'neg': 0.1},  # Positive
            {'compound': -0.4, 'pos': 0.1, 'neu': 0.3, 'neg': 0.6},  # Negative
            {'compound': 0.3, 'pos': 0.5, 'neu': 0.4, 'neg': 0.1},  # Positive
            {'compound': 0.2, 'pos': 0.4, 'neu': 0.5, 'neg': 0.1}   # Neutral
        ]
        mock_vader.return_value = mock_analyzer
        
        sentiment = transcript_analyzer.analyze_sentiment(sample_segments)
        
        assert isinstance(sentiment, SentimentAnalysis)
        assert sentiment.overall_sentiment in [SentimentType.POSITIVE, SentimentType.NEGATIVE, SentimentType.NEUTRAL]
        assert sentiment.agent_sentiment in [SentimentType.POSITIVE, SentimentType.NEGATIVE, SentimentType.NEUTRAL]
        assert sentiment.customer_sentiment in [SentimentType.POSITIVE, SentimentType.NEGATIVE, SentimentType.NEUTRAL]
        
        # Check sentiment scores
        assert 'positive' in sentiment.sentiment_scores
        assert 'negative' in sentiment.sentiment_scores
        assert 'neutral' in sentiment.sentiment_scores
        
        # Check sentiment over time
        assert len(sentiment.sentiment_over_time) > 0
    
    def test_sentiment_classification(self, transcript_analyzer):
        """Test sentiment classification logic."""
        # Test different compound scores
        assert transcript_analyzer._classify_sentiment(0.6) == SentimentType.POSITIVE
        assert transcript_analyzer._classify_sentiment(-0.6) == SentimentType.NEGATIVE
        assert transcript_analyzer._classify_sentiment(0.0) == SentimentType.NEUTRAL
        assert transcript_analyzer._classify_sentiment(0.05) == SentimentType.NEUTRAL  # Borderline
    
    def test_emotional_peaks_detection(self, transcript_analyzer):
        """Test detection of emotional peaks."""
        # Mock sentiment scores with some peaks
        sentiment_data = [
            {'timestamp': 0.0, 'compound': 0.1},
            {'timestamp': 5.0, 'compound': -0.8},  # Negative peak
            {'timestamp': 10.0, 'compound': 0.2},
            {'timestamp': 15.0, 'compound': 0.9},  # Positive peak
            {'timestamp': 20.0, 'compound': 0.0}
        ]
        
        peaks = transcript_analyzer._detect_emotional_peaks(sentiment_data)
        
        assert len(peaks) >= 1  # Should detect at least one peak
        for peak in peaks:
            assert 'timestamp' in peak
            assert 'intensity' in peak
            assert 'type' in peak


class TestPerformanceKPIs:
    """Test performance KPI calculations."""
    
    def test_calculate_performance_kpis(self, transcript_analyzer, sample_segments):
        """Test calculation of performance KPIs."""
        # Mock sentiment analysis result
        mock_sentiment = SentimentAnalysis(
            overall_sentiment=SentimentType.POSITIVE,
            agent_sentiment=SentimentType.POSITIVE,
            customer_sentiment=SentimentType.NEUTRAL,
            sentiment_scores={'positive': 0.6, 'negative': 0.2, 'neutral': 0.2},
            sentiment_over_time=[],
            emotional_peaks=[],
            sentiment_transitions=1
        )
        
        # Mock characteristics
        mock_characteristics = CallCharacteristics(
            total_duration_seconds=300.0,
            agent_talk_time_seconds=180.0,
            customer_talk_time_seconds=120.0,
            silence_duration_seconds=0.0,
            agent_talk_ratio=0.6,
            customer_talk_ratio=0.4,
            total_words=150,
            agent_words=90,
            customer_words=60,
            interruptions_by_agent=1,
            interruptions_by_customer=0,
            speaking_rate_agent_wpm=150.0,
            speaking_rate_customer_wpm=120.0
        )
        
        kpis = transcript_analyzer.calculate_performance_kpis(
            sample_segments, mock_sentiment, mock_characteristics
        )
        
        assert isinstance(kpis, PerformanceKPIs)
        assert 0 <= kpis.customer_satisfaction_score <= 10
        assert 0 <= kpis.agent_professionalism_score <= 10
        assert 0 <= kpis.call_efficiency_score <= 10
        assert 0 <= kpis.clarity_score <= 10
        assert kpis.issue_resolution_time > 0
    
    def test_customer_satisfaction_calculation(self, transcript_analyzer):
        """Test customer satisfaction score calculation."""
        # Positive sentiment should yield high satisfaction
        positive_sentiment = SentimentAnalysis(
            overall_sentiment=SentimentType.POSITIVE,
            agent_sentiment=SentimentType.POSITIVE,
            customer_sentiment=SentimentType.POSITIVE,
            sentiment_scores={'positive': 0.8, 'negative': 0.1, 'neutral': 0.1},
            sentiment_over_time=[],
            emotional_peaks=[],
            sentiment_transitions=0
        )
        
        score = transcript_analyzer._calculate_customer_satisfaction(positive_sentiment, [])
        assert score >= 7.0  # Should be high for positive sentiment
        
        # Negative sentiment should yield low satisfaction
        negative_sentiment = SentimentAnalysis(
            overall_sentiment=SentimentType.NEGATIVE,
            agent_sentiment=SentimentType.NEUTRAL,
            customer_sentiment=SentimentType.NEGATIVE,
            sentiment_scores={'positive': 0.1, 'negative': 0.8, 'neutral': 0.1},
            sentiment_over_time=[],
            emotional_peaks=[],
            sentiment_transitions=0
        )
        
        score = transcript_analyzer._calculate_customer_satisfaction(negative_sentiment, [])
        assert score <= 5.0  # Should be low for negative sentiment


class TestComplianceAnalysis:
    """Test compliance metrics analysis."""
    
    def test_analyze_compliance(self, transcript_analyzer, sample_segments):
        """Test compliance analysis."""
        compliance = transcript_analyzer.analyze_compliance(sample_segments)
        
        assert isinstance(compliance, ComplianceMetrics)
        assert 0 <= compliance.compliance_score <= 10
        assert isinstance(compliance.required_disclosures_made, list)
        assert isinstance(compliance.missing_disclosures, list)
        assert isinstance(compliance.escalation_offered, bool)
        assert isinstance(compliance.privacy_compliance, bool)
    
    def test_disclosure_detection(self, transcript_analyzer):
        """Test detection of required disclosures."""
        # Create segments with disclosure language
        disclosure_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.AGENT,
                text="This call may be recorded for quality and training purposes.",
                duration=3.0,
                confidence=0.95
            ),
            TranscriptSegment(
                timestamp=5.0,
                speaker=CallParticipant.AGENT,
                text="I need to verify your identity. Can you provide your account number?",
                duration=4.0,
                confidence=0.95
            )
        ]
        
        compliance = transcript_analyzer.analyze_compliance(disclosure_segments)
        
        # Should detect recording disclosure
        disclosures_text = ' '.join(compliance.required_disclosures_made).lower()
        assert any(keyword in disclosures_text for keyword in ['record', 'quality', 'training'])


class TestConversationFlow:
    """Test conversation flow analysis."""
    
    def test_analyze_conversation_flow(self, transcript_analyzer, sample_segments):
        """Test conversation flow analysis."""
        flow = transcript_analyzer.analyze_conversation_flow(sample_segments)
        
        assert isinstance(flow, ConversationFlow)
        assert flow.turn_taking_frequency > 0
        assert 0 <= flow.opening_quality_score <= 10
        assert 0 <= flow.closing_quality_score <= 10
        assert 0 <= flow.agenda_adherence_score <= 10
        assert flow.topic_changes >= 0
        assert isinstance(flow.conversation_segments, list)
    
    def test_opening_quality_assessment(self, transcript_analyzer):
        """Test opening quality assessment."""
        # Good opening
        good_opening = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.AGENT,
                text="Thank you for calling. My name is John. How can I help you today?",
                duration=4.0,
                confidence=0.95
            )
        ]
        
        score = transcript_analyzer._assess_opening_quality(good_opening)
        assert score >= 7.0  # Should be high for good opening
        
        # Poor opening
        poor_opening = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.AGENT,
                text="Yeah, what do you want?",
                duration=2.0,
                confidence=0.95
            )
        ]
        
        score = transcript_analyzer._assess_opening_quality(poor_opening)
        assert score <= 5.0  # Should be low for poor opening


class TestKeyTopicsExtraction:
    """Test key topics and themes extraction."""
    
    def test_extract_key_topics(self, transcript_analyzer, sample_segments):
        """Test key topics extraction."""
        topics = transcript_analyzer.extract_key_topics(sample_segments)
        
        assert isinstance(topics, KeyTopics)
        assert isinstance(topics.primary_topics, list)
        assert isinstance(topics.secondary_topics, list)
        assert isinstance(topics.keywords_frequency, dict)
        assert isinstance(topics.named_entities, list)
    
    def test_business_intent_detection(self, transcript_analyzer):
        """Test business intent detection."""
        # Support call
        support_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="I'm having trouble with my account login.",
                duration=3.0,
                confidence=0.95
            )
        ]
        
        topics = transcript_analyzer.extract_key_topics(support_segments)
        assert topics.business_intent is not None
        
        # Sales call
        sales_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="I'm interested in upgrading my plan.",
                duration=3.0,
                confidence=0.95
            )
        ]
        
        topics = transcript_analyzer.extract_key_topics(sales_segments)
        assert topics.business_intent is not None
    
    @patch('awslabs.call_analysis_mcp_server.services.transcript_analyzer.word_tokenize')
    @patch('awslabs.call_analysis_mcp_server.services.transcript_analyzer.pos_tag')
    def test_keyword_extraction(self, mock_pos_tag, mock_tokenize, transcript_analyzer):
        """Test keyword extraction with mocked NLTK."""
        mock_tokenize.return_value = ['billing', 'issue', 'account', 'help']
        mock_pos_tag.return_value = [
            ('billing', 'NN'), ('issue', 'NN'), ('account', 'NN'), ('help', 'VB')
        ]
        
        text = "I have a billing issue with my account and need help"
        keywords = transcript_analyzer._extract_keywords(text)
        
        assert isinstance(keywords, dict)
        assert len(keywords) > 0


class TestFullAnalysisIntegration:
    """Test full analysis integration."""
    
    @pytest.mark.asyncio
    async def test_analyze_transcript_full(self, transcript_analyzer, sample_segments):
        """Test full transcript analysis."""
        analysis_options = {
            "sentiment_analysis": True,
            "performance_metrics": True,
            "compliance_check": True,
            "conversation_flow": True,
            "topic_extraction": True
        }
        
        result = await transcript_analyzer.analyze_transcript(
            transcript_segments=sample_segments,
            call_id="TEST_CALL_001",
            analysis_options=analysis_options
        )
        
        assert isinstance(result, CallAnalysisResult)
        assert result.call_id == "TEST_CALL_001"
        assert result.analysis_timestamp is not None
        assert result.characteristics is not None
        assert result.sentiment_analysis is not None
        assert result.performance_kpis is not None
        assert result.compliance_metrics is not None
        assert result.conversation_flow is not None
        assert result.key_topics is not None
    
    @pytest.mark.asyncio
    async def test_analyze_transcript_minimal_options(self, transcript_analyzer, sample_segments):
        """Test analysis with minimal options."""
        analysis_options = {
            "sentiment_analysis": False,
            "performance_metrics": False,
            "compliance_check": False,
            "conversation_flow": False,
            "topic_extraction": False
        }
        
        result = await transcript_analyzer.analyze_transcript(
            transcript_segments=sample_segments,
            call_id="TEST_CALL_002",
            analysis_options=analysis_options
        )
        
        assert isinstance(result, CallAnalysisResult)
        assert result.call_id == "TEST_CALL_002"
        assert result.characteristics is not None  # Always calculated
        
        # Optional components should be None or default
        # (depending on implementation)
    
    def test_error_handling(self, transcript_analyzer):
        """Test error handling in analysis."""
        # Test with invalid segments
        invalid_segments = [
            TranscriptSegment(
                timestamp=-1.0,  # Invalid timestamp
                speaker=CallParticipant.AGENT,
                text="",  # Empty text
                duration=0.0,
                confidence=0.0
            )
        ]
        
        # Should handle gracefully without crashing
        characteristics = transcript_analyzer.calculate_call_characteristics(invalid_segments)
        assert isinstance(characteristics, CallCharacteristics)