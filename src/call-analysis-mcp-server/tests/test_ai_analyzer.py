"""
Comprehensive tests for AIAnalyzer service.

Tests OpenAI integration, AI-powered analysis, fallback mechanisms,
and enhanced sentiment/business intelligence features.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List, Dict, Any

from awslabs.call_analysis_mcp_server.services.ai_analyzer import AIAnalyzer
from awslabs.call_analysis_mcp_server.models import (
    TranscriptSegment,
    CallParticipant,
    SentimentType,
    TranscriptEvidence,
    DecisionEvidence,
    RiskLevel
)


@pytest.fixture
def ai_analyzer():
    """Create an AIAnalyzer instance for testing."""
    return AIAnalyzer()


@pytest.fixture
def sample_transcript_segments():
    """Sample transcript segments for testing."""
    return [
        TranscriptSegment(
            timestamp=0.0,
            speaker=CallParticipant.AGENT,
            text="Thank you for calling. How can I help you today?",
            duration=3.0,
            confidence=0.95
        ),
        TranscriptSegment(
            timestamp=5.0,
            speaker=CallParticipant.CUSTOMER,
            text="I'm really frustrated with your service. It's not working and it's too expensive.",
            duration=6.0,
            confidence=0.93
        ),
        TranscriptSegment(
            timestamp=15.0,
            speaker=CallParticipant.CUSTOMER,
            text="I'm considering switching to your competitor because they have better prices.",
            duration=5.0,
            confidence=0.94
        ),
        TranscriptSegment(
            timestamp=25.0,
            speaker=CallParticipant.AGENT,
            text="I completely understand your frustration. Let me see what I can do to help resolve this.",
            duration=6.0,
            confidence=0.96
        )
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "sentiment": "negative",
                        "confidence": 0.85,
                        "key_themes": ["pricing concerns", "service issues", "competitive threat"],
                        "risk_indicators": [
                            {
                                "type": "churn_risk",
                                "severity": "high",
                                "evidence": "Customer mentioned switching to competitor",
                                "confidence": 0.9
                            }
                        ],
                        "opportunities": [],
                        "training_needs": [
                            {
                                "skill": "empathy",
                                "reason": "Agent response showed good empathy",
                                "priority": "medium"
                            }
                        ]
                    })
                }
            }
        ]
    }


class TestInitialization:
    """Test AIAnalyzer initialization."""
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    def test_initialization_with_api_key(self, mock_openai):
        """Test initialization with OpenAI API key."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        analyzer = AIAnalyzer()
        
        assert analyzer.client == mock_client
        assert analyzer.api_available is True
        mock_openai.assert_called_once_with(api_key='test-key')
    
    @patch.dict('os.environ', {}, clear=True)
    def test_initialization_without_api_key(self):
        """Test initialization without OpenAI API key."""
        analyzer = AIAnalyzer()
        
        assert analyzer.client is None
        assert analyzer.api_available is False
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    def test_initialization_with_connection_error(self, mock_openai):
        """Test initialization when OpenAI connection fails."""
        mock_openai.side_effect = Exception("Connection failed")
        
        analyzer = AIAnalyzer()
        
        assert analyzer.client is None
        assert analyzer.api_available is False


class TestSentimentAnalysis:
    """Test AI-powered sentiment analysis."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_enhance_sentiment_analysis_with_ai(self, mock_openai, ai_analyzer, sample_transcript_segments):
        """Test AI-enhanced sentiment analysis."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "overall_sentiment": "negative",
            "confidence": 0.85,
            "customer_sentiment": "frustrated",
            "agent_sentiment": "empathetic",
            "sentiment_progression": [
                {"timestamp": 0, "sentiment": "neutral"},
                {"timestamp": 5, "sentiment": "negative"},
                {"timestamp": 25, "sentiment": "slightly_negative"}
            ],
            "emotional_peaks": [
                {"timestamp": 5, "emotion": "frustration", "intensity": 0.8}
            ]
        })
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Reinitialize with mocked client
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        enhanced_sentiment = await ai_analyzer.enhance_sentiment_analysis(sample_transcript_segments)
        
        assert enhanced_sentiment is not None
        assert "overall_sentiment" in enhanced_sentiment
        assert "confidence" in enhanced_sentiment
        assert enhanced_sentiment["overall_sentiment"] == "negative"
        assert enhanced_sentiment["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_enhance_sentiment_analysis_fallback(self, ai_analyzer, sample_transcript_segments):
        """Test sentiment analysis fallback when AI is unavailable."""
        # Ensure AI is unavailable
        ai_analyzer.client = None
        ai_analyzer.api_available = False
        
        enhanced_sentiment = await ai_analyzer.enhance_sentiment_analysis(sample_transcript_segments)
        
        assert enhanced_sentiment is not None
        assert "overall_sentiment" in enhanced_sentiment
        assert "confidence" in enhanced_sentiment
        # Fallback should still provide reasonable results
        assert enhanced_sentiment["overall_sentiment"] in ["positive", "negative", "neutral"]
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_sentiment_analysis_api_error(self, mock_openai, ai_analyzer, sample_transcript_segments):
        """Test handling of API errors during sentiment analysis."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_openai.return_value = mock_client
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        # Should fallback gracefully when API fails
        enhanced_sentiment = await ai_analyzer.enhance_sentiment_analysis(sample_transcript_segments)
        
        assert enhanced_sentiment is not None
        assert "overall_sentiment" in enhanced_sentiment


class TestRiskAssessment:
    """Test AI-powered risk assessment."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_assess_deal_risk_with_ai(self, mock_openai, ai_analyzer, sample_transcript_segments):
        """Test AI-powered deal risk assessment."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "risk_level": "high",
            "risk_factors": [
                "price_objection",
                "competitive_threat"
            ],
            "risk_indicators": [
                {
                    "factor": "pricing_concerns",
                    "evidence": "Customer mentioned service is 'too expensive'",
                    "severity": 0.8,
                    "timestamp": 5.0
                },
                {
                    "factor": "competitive_comparison",
                    "evidence": "Customer considering switching to competitor",
                    "severity": 0.9,
                    "timestamp": 15.0
                }
            ],
            "win_probability_change": -0.6,
            "recommended_actions": [
                "immediate_price_negotiation",
                "competitive_positioning_discussion"
            ],
            "confidence": 0.88
        })
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        risk_assessment = await ai_analyzer.assess_deal_risk_with_ai(sample_transcript_segments)
        
        assert risk_assessment is not None
        assert "risk_level" in risk_assessment
        assert "risk_factors" in risk_assessment
        assert "risk_indicators" in risk_assessment
        assert risk_assessment["risk_level"] == "high"
        assert len(risk_assessment["risk_factors"]) == 2
        assert len(risk_assessment["risk_indicators"]) == 2
    
    @pytest.mark.asyncio
    async def test_assess_deal_risk_fallback(self, ai_analyzer, sample_transcript_segments):
        """Test deal risk assessment fallback."""
        ai_analyzer.client = None
        ai_analyzer.api_available = False
        
        risk_assessment = await ai_analyzer.assess_deal_risk_with_ai(sample_transcript_segments)
        
        assert risk_assessment is not None
        assert "risk_level" in risk_assessment
        assert "confidence" in risk_assessment
        # Fallback should detect risk keywords
        assert risk_assessment["risk_level"] in ["low", "medium", "high", "critical"]


class TestChurnPrediction:
    """Test AI-powered churn prediction."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_predict_churn_risk_with_ai(self, mock_openai, ai_analyzer, sample_transcript_segments):
        """Test AI-powered churn prediction."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "churn_probability": 0.75,
            "churn_signals": [
                "frustration_expressed",
                "competitor_mention",
                "price_sensitivity"
            ],
            "churn_indicators": [
                {
                    "signal": "frustration",
                    "evidence": "Customer expressed frustration with service",
                    "strength": 0.7,
                    "timestamp": 5.0
                },
                {
                    "signal": "switching_intent",
                    "evidence": "Mentioned considering competitor",
                    "strength": 0.9,
                    "timestamp": 15.0
                }
            ],
            "retention_strategies": [
                "immediate_retention_call",
                "service_improvement_plan",
                "pricing_review"
            ],
            "confidence": 0.82
        })
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        churn_prediction = await ai_analyzer.predict_churn_risk_with_ai(sample_transcript_segments)
        
        assert churn_prediction is not None
        assert "churn_probability" in churn_prediction
        assert "churn_signals" in churn_prediction
        assert "churn_indicators" in churn_prediction
        assert 0.0 <= churn_prediction["churn_probability"] <= 1.0
        assert len(churn_prediction["churn_signals"]) == 3
    
    @pytest.mark.asyncio
    async def test_predict_churn_risk_fallback(self, ai_analyzer, sample_transcript_segments):
        """Test churn prediction fallback."""
        ai_analyzer.client = None
        ai_analyzer.api_available = False
        
        churn_prediction = await ai_analyzer.predict_churn_risk_with_ai(sample_transcript_segments)
        
        assert churn_prediction is not None
        assert "churn_probability" in churn_prediction
        assert 0.0 <= churn_prediction["churn_probability"] <= 1.0


class TestOpportunityDetection:
    """Test AI-powered opportunity detection."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_detect_opportunities_with_ai(self, mock_openai, ai_analyzer):
        """Test AI-powered opportunity detection."""
        opportunity_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="We're expanding our business and will need additional services next quarter.",
                duration=4.0,
                confidence=0.95
            ),
            TranscriptSegment(
                timestamp=10.0,
                speaker=CallParticipant.CUSTOMER,
                text="We're also interested in premium support and advanced analytics.",
                duration=4.0,
                confidence=0.93
            )
        ]
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "opportunities": [
                {
                    "type": "expansion",
                    "description": "Customer expanding business and needs more services",
                    "evidence": "We're expanding our business and will need additional services",
                    "potential_value": "high",
                    "timeline": "next_quarter",
                    "confidence": 0.9,
                    "timestamp": 0.0
                },
                {
                    "type": "upsell",
                    "description": "Interest in premium support and analytics",
                    "evidence": "interested in premium support and advanced analytics",
                    "potential_value": "medium",
                    "timeline": "near_term",
                    "confidence": 0.8,
                    "timestamp": 10.0
                }
            ],
            "recommended_actions": [
                "schedule_expansion_discussion",
                "prepare_premium_service_proposal"
            ],
            "overall_confidence": 0.85
        })
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        opportunities = await ai_analyzer.detect_opportunities_with_ai(opportunity_segments)
        
        assert opportunities is not None
        assert "opportunities" in opportunities
        assert len(opportunities["opportunities"]) == 2
        assert opportunities["opportunities"][0]["type"] == "expansion"
        assert opportunities["opportunities"][1]["type"] == "upsell"
    
    @pytest.mark.asyncio
    async def test_detect_opportunities_fallback(self, ai_analyzer):
        """Test opportunity detection fallback."""
        opportunity_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="We need more services and are expanding.",
                duration=3.0,
                confidence=0.95
            )
        ]
        
        ai_analyzer.client = None
        ai_analyzer.api_available = False
        
        opportunities = await ai_analyzer.detect_opportunities_with_ai(opportunity_segments)
        
        assert opportunities is not None
        assert "opportunities" in opportunities
        # Fallback should detect keyword-based opportunities
        if len(opportunities["opportunities"]) > 0:
            assert any("expand" in str(opp) for opp in opportunities["opportunities"])


class TestTrainingAnalysis:
    """Test AI-powered training needs analysis."""
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI')
    async def test_analyze_training_needs_with_ai(self, mock_openai, ai_analyzer, sample_transcript_segments):
        """Test AI-powered training needs analysis."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "training_needs": [
                {
                    "skill": "objection_handling",
                    "priority": "high",
                    "evidence": "Did not effectively address price objection",
                    "improvement_suggestion": "Provide value-based selling training",
                    "confidence": 0.8
                },
                {
                    "skill": "empathy",
                    "priority": "medium",
                    "evidence": "Good empathetic response to customer frustration",
                    "improvement_suggestion": "Continue current approach",
                    "confidence": 0.7
                }
            ],
            "strengths": [
                "empathetic_communication",
                "professional_demeanor"
            ],
            "overall_performance_score": 7.2,
            "confidence": 0.75
        })
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        training_analysis = await ai_analyzer.analyze_training_needs_with_ai(sample_transcript_segments)
        
        assert training_analysis is not None
        assert "training_needs" in training_analysis
        assert "strengths" in training_analysis
        assert len(training_analysis["training_needs"]) == 2
        assert training_analysis["training_needs"][0]["skill"] == "objection_handling"
    
    @pytest.mark.asyncio
    async def test_analyze_training_needs_fallback(self, ai_analyzer, sample_transcript_segments):
        """Test training needs analysis fallback."""
        ai_analyzer.client = None
        ai_analyzer.api_available = False
        
        training_analysis = await ai_analyzer.analyze_training_needs_with_ai(sample_transcript_segments)
        
        assert training_analysis is not None
        assert "training_needs" in training_analysis
        # Fallback should identify basic training needs


class TestFallbackMechanisms:
    """Test fallback mechanisms when AI is unavailable."""
    
    def test_fallback_sentiment_analysis(self, ai_analyzer, sample_transcript_segments):
        """Test fallback sentiment analysis using rule-based approach."""
        sentiment = ai_analyzer._fallback_sentiment_analysis(sample_transcript_segments)
        
        assert sentiment is not None
        assert "overall_sentiment" in sentiment
        assert "confidence" in sentiment
        assert sentiment["overall_sentiment"] in ["positive", "negative", "neutral"]
        assert 0.0 <= sentiment["confidence"] <= 1.0
    
    def test_fallback_risk_assessment(self, ai_analyzer, sample_transcript_segments):
        """Test fallback risk assessment using keyword detection."""
        risk_assessment = ai_analyzer._fallback_risk_assessment(sample_transcript_segments)
        
        assert risk_assessment is not None
        assert "risk_level" in risk_assessment
        assert "risk_factors" in risk_assessment
        assert risk_assessment["risk_level"] in ["low", "medium", "high", "critical"]
        
        # Should detect risk keywords in sample segments
        risk_text = " ".join([segment.text for segment in sample_transcript_segments])
        if any(keyword in risk_text.lower() for keyword in ["expensive", "competitor", "frustrated"]):
            assert risk_assessment["risk_level"] != "low"
    
    def test_fallback_churn_prediction(self, ai_analyzer, sample_transcript_segments):
        """Test fallback churn prediction using keyword analysis."""
        churn_prediction = ai_analyzer._fallback_churn_prediction(sample_transcript_segments)
        
        assert churn_prediction is not None
        assert "churn_probability" in churn_prediction
        assert "churn_signals" in churn_prediction
        assert 0.0 <= churn_prediction["churn_probability"] <= 1.0
        
        # Should detect churn signals in sample segments
        if any("competitor" in segment.text.lower() for segment in sample_transcript_segments):
            assert churn_prediction["churn_probability"] > 0.5
    
    def test_fallback_opportunity_detection(self, ai_analyzer):
        """Test fallback opportunity detection using keyword analysis."""
        opportunity_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="We're expanding and need more services.",
                duration=3.0,
                confidence=0.95
            )
        ]
        
        opportunities = ai_analyzer._fallback_opportunity_detection(opportunity_segments)
        
        assert opportunities is not None
        assert "opportunities" in opportunities
        # Should detect expansion keywords
        if len(opportunities["opportunities"]) > 0:
            opportunity_texts = [str(opp) for opp in opportunities["opportunities"]]
            assert any("expand" in text.lower() for text in opportunity_texts)
    
    def test_fallback_training_analysis(self, ai_analyzer, sample_transcript_segments):
        """Test fallback training analysis using basic performance indicators."""
        training_analysis = ai_analyzer._fallback_training_analysis(sample_transcript_segments)
        
        assert training_analysis is not None
        assert "training_needs" in training_analysis
        assert "overall_performance_score" in training_analysis
        assert isinstance(training_analysis["training_needs"], list)
        assert 0.0 <= training_analysis["overall_performance_score"] <= 10.0


class TestUtilityMethods:
    """Test utility methods and helper functions."""
    
    def test_extract_text_for_analysis(self, ai_analyzer, sample_transcript_segments):
        """Test text extraction for AI analysis."""
        extracted_text = ai_analyzer._extract_text_for_analysis(sample_transcript_segments)
        
        assert isinstance(extracted_text, str)
        assert len(extracted_text) > 0
        assert "Thank you for calling" in extracted_text
        assert "frustrated" in extracted_text
    
    def test_parse_ai_response(self, ai_analyzer):
        """Test AI response parsing."""
        # Valid JSON response
        valid_response = '{"sentiment": "negative", "confidence": 0.8}'
        parsed = ai_analyzer._parse_ai_response(valid_response)
        
        assert parsed is not None
        assert parsed["sentiment"] == "negative"
        assert parsed["confidence"] == 0.8
        
        # Invalid JSON response
        invalid_response = 'Not a JSON response'
        parsed = ai_analyzer._parse_ai_response(invalid_response)
        
        assert parsed is None
    
    def test_validate_ai_response(self, ai_analyzer):
        """Test AI response validation."""
        # Valid response
        valid_response = {
            "sentiment": "negative",
            "confidence": 0.8,
            "key_themes": ["pricing"]
        }
        
        is_valid = ai_analyzer._validate_ai_response(valid_response, "sentiment")
        assert is_valid is True
        
        # Invalid response (missing required fields)
        invalid_response = {
            "sentiment": "negative"
            # Missing confidence
        }
        
        is_valid = ai_analyzer._validate_ai_response(invalid_response, "sentiment")
        assert is_valid is False
    
    def test_calculate_confidence_score(self, ai_analyzer):
        """Test confidence score calculation."""
        # High confidence scenario
        high_conf_indicators = ["definitely", "absolutely", "certain"]
        score = ai_analyzer._calculate_confidence_score("I am definitely switching", high_conf_indicators)
        assert score >= 0.8
        
        # Low confidence scenario
        low_conf_indicators = ["maybe", "possibly", "might"]
        score = ai_analyzer._calculate_confidence_score("I might consider it", low_conf_indicators)
        assert score <= 0.6
    
    def test_keyword_matching(self, ai_analyzer):
        """Test keyword matching functionality."""
        text = "This service is too expensive and I'm frustrated with the poor quality"
        
        price_keywords = ["expensive", "cost", "price", "money"]
        matches = ai_analyzer._find_keyword_matches(text, price_keywords)
        assert "expensive" in matches
        
        emotion_keywords = ["frustrated", "angry", "upset"]
        matches = ai_analyzer._find_keyword_matches(text, emotion_keywords)
        assert "frustrated" in matches
    
    def test_extract_evidence_from_segments(self, ai_analyzer, sample_transcript_segments):
        """Test evidence extraction from transcript segments."""
        keywords = ["expensive", "frustrated", "competitor"]
        evidence = ai_analyzer._extract_evidence_from_segments(
            sample_transcript_segments, 
            keywords, 
            "Test context"
        )
        
        assert isinstance(evidence, list)
        assert len(evidence) > 0
        
        for item in evidence:
            assert isinstance(item, TranscriptEvidence)
            assert item.call_id is not None
            assert item.speaker in [CallParticipant.AGENT, CallParticipant.CUSTOMER]
            assert 0.0 <= item.confidence_score <= 1.0


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, ai_analyzer, sample_transcript_segments):
        """Test handling of API timeouts."""
        # Mock client with timeout
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=TimeoutError("API timeout"))
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        # Should fallback gracefully on timeout
        result = await ai_analyzer.enhance_sentiment_analysis(sample_transcript_segments)
        
        assert result is not None
        assert "overall_sentiment" in result
    
    @pytest.mark.asyncio
    async def test_invalid_api_response_handling(self, ai_analyzer, sample_transcript_segments):
        """Test handling of invalid API responses."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        ai_analyzer.client = mock_client
        ai_analyzer.api_available = True
        
        # Should fallback when response is invalid
        result = await ai_analyzer.enhance_sentiment_analysis(sample_transcript_segments)
        
        assert result is not None
        assert "overall_sentiment" in result
    
    def test_empty_segments_handling(self, ai_analyzer):
        """Test handling of empty transcript segments."""
        empty_segments = []
        
        # Should handle gracefully without crashing
        sentiment = ai_analyzer._fallback_sentiment_analysis(empty_segments)
        assert sentiment is not None
        assert sentiment["overall_sentiment"] == "neutral"
        
        risk = ai_analyzer._fallback_risk_assessment(empty_segments)
        assert risk is not None
        assert risk["risk_level"] == "low"
    
    def test_malformed_segments_handling(self, ai_analyzer):
        """Test handling of malformed transcript segments."""
        malformed_segments = [
            TranscriptSegment(
                timestamp=-1.0,  # Invalid timestamp
                speaker=CallParticipant.AGENT,
                text="",  # Empty text
                duration=0.0,
                confidence=2.0  # Invalid confidence > 1.0
            )
        ]
        
        # Should handle gracefully
        extracted_text = ai_analyzer._extract_text_for_analysis(malformed_segments)
        assert isinstance(extracted_text, str)
        
        evidence = ai_analyzer._extract_evidence_from_segments(
            malformed_segments, 
            ["test"], 
            "Test context"
        )
        assert isinstance(evidence, list)