"""
Comprehensive tests for BusinessIntelligenceAnalyzer service.

Tests deal risk assessment, churn prediction, opportunity detection,
evidence collection, and business intelligence insights generation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from awslabs.call_analysis_mcp_server.services.business_intelligence import BusinessIntelligenceAnalyzer
from awslabs.call_analysis_mcp_server.models import (
    CallAnalysisResult,
    BusinessIntelligenceInsights,
    DealRiskIndicator,
    ChurnRiskIndicator,
    OpportunityIndicator,
    TrainingNeedsIndicator,
    QualityIssue,
    TranscriptEvidence,
    DecisionEvidence,
    CallParticipant,
    SentimentType,
    RiskLevel,
    TranscriptSegment,
    CallCharacteristics,
    SentimentAnalysis,
    PerformanceKPIs
)


@pytest.fixture
def bi_analyzer():
    """Create a BusinessIntelligenceAnalyzer instance for testing."""
    return BusinessIntelligenceAnalyzer()


@pytest.fixture
def sample_call_analysis():
    """Sample call analysis result for testing."""
    return CallAnalysisResult(
        call_id="CALL_001",
        analysis_timestamp=datetime.now(),
        transcript_source="s3://bucket/call.json",
        characteristics=CallCharacteristics(
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
        ),
        sentiment_analysis=SentimentAnalysis(
            overall_sentiment=SentimentType.NEGATIVE,
            agent_sentiment=SentimentType.POSITIVE,
            customer_sentiment=SentimentType.NEGATIVE,
            sentiment_scores={'positive': 0.2, 'negative': 0.6, 'neutral': 0.2},
            sentiment_over_time=[
                {'timestamp': 0.0, 'sentiment': 'neutral', 'score': 0.1},
                {'timestamp': 60.0, 'sentiment': 'negative', 'score': -0.6}
            ],
            emotional_peaks=[
                {'timestamp': 60.0, 'intensity': 0.8, 'type': 'negative'}
            ],
            sentiment_transitions=2
        ),
        performance_kpis=PerformanceKPIs(
            customer_satisfaction_score=3.5,
            first_call_resolution=False,
            agent_professionalism_score=7.0,
            agent_knowledge_score=6.0,
            agent_empathy_score=5.5,
            call_efficiency_score=4.0,
            issue_resolution_time=300.0,
            clarity_score=6.5,
            active_listening_score=5.0
        )
    )


@pytest.fixture
def sample_transcript_segments():
    """Sample transcript segments with business intelligence indicators."""
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
            text="I'm really frustrated. This service is too expensive and not working properly.",
            duration=6.0,
            confidence=0.93
        ),
        TranscriptSegment(
            timestamp=15.0,
            speaker=CallParticipant.CUSTOMER,
            text="I'm thinking about switching to your competitor because they offer better prices.",
            duration=5.0,
            confidence=0.94
        ),
        TranscriptSegment(
            timestamp=25.0,
            speaker=CallParticipant.AGENT,
            text="I understand your concerns. Let me see what I can do to help.",
            duration=4.0,
            confidence=0.96
        ),
        TranscriptSegment(
            timestamp=35.0,
            speaker=CallParticipant.CUSTOMER,
            text="Actually, we're also looking to expand our business and might need more services.",
            duration=5.0,
            confidence=0.92
        )
    ]


class TestDealRiskAnalysis:
    """Test deal risk assessment functionality."""
    
    def test_analyze_deal_risks(self, bi_analyzer, sample_call_analysis, sample_transcript_segments):
        """Test deal risk analysis."""
        risks = bi_analyzer.analyze_deal_risks([sample_call_analysis], sample_transcript_segments)
        
        assert isinstance(risks, list)
        if len(risks) > 0:
            risk = risks[0]
            assert isinstance(risk, DealRiskIndicator)
            assert risk.account_name is not None
            assert risk.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            assert isinstance(risk.risk_factors, list)
            assert isinstance(risk.recommended_actions, list)
            assert -1.0 <= risk.win_probability_change <= 1.0
            assert isinstance(risk.evidence, DecisionEvidence)
    
    def test_price_objection_detection(self, bi_analyzer, sample_transcript_segments):
        """Test detection of price objections."""
        price_indicators = bi_analyzer._detect_price_objections(sample_transcript_segments)
        
        assert isinstance(price_indicators, list)
        assert len(price_indicators) > 0  # Should detect "too expensive"
        
        for indicator in price_indicators:
            assert isinstance(indicator, TranscriptEvidence)
            assert indicator.speaker == CallParticipant.CUSTOMER
            assert 'price' in indicator.context.lower() or 'expensive' in indicator.evidence_text.lower()
    
    def test_competitor_mentions_detection(self, bi_analyzer, sample_transcript_segments):
        """Test detection of competitor mentions."""
        competitor_indicators = bi_analyzer._detect_competitor_mentions(sample_transcript_segments)
        
        assert isinstance(competitor_indicators, list)
        assert len(competitor_indicators) > 0  # Should detect "competitor"
        
        for indicator in competitor_indicators:
            assert isinstance(indicator, TranscriptEvidence)
            assert 'competitor' in indicator.evidence_text.lower()
    
    def test_risk_level_calculation(self, bi_analyzer):
        """Test risk level calculation based on indicators."""
        # High risk scenario
        high_risk_evidence = [
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/call.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="This is way too expensive",
                context="Price objection",
                confidence_score=0.9
            ),
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/call.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="We're looking at competitors",
                context="Competitive threat",
                confidence_score=0.8
            )
        ]
        
        risk_level = bi_analyzer._calculate_risk_level(high_risk_evidence, 2.0)  # Low satisfaction
        assert risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Low risk scenario
        low_risk_evidence = []
        risk_level = bi_analyzer._calculate_risk_level(low_risk_evidence, 9.0)  # High satisfaction
        assert risk_level == RiskLevel.LOW


class TestChurnRiskAnalysis:
    """Test churn risk assessment functionality."""
    
    def test_analyze_churn_risks(self, bi_analyzer, sample_call_analysis, sample_transcript_segments):
        """Test churn risk analysis."""
        churn_risks = bi_analyzer.analyze_churn_risks([sample_call_analysis], sample_transcript_segments)
        
        assert isinstance(churn_risks, list)
        if len(churn_risks) > 0:
            risk = churn_risks[0]
            assert isinstance(risk, ChurnRiskIndicator)
            assert 0.0 <= risk.churn_probability <= 1.0
            assert risk.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            assert isinstance(risk.churn_signals, list)
            assert isinstance(risk.evidence, DecisionEvidence)
    
    def test_dissatisfaction_signals_detection(self, bi_analyzer, sample_transcript_segments):
        """Test detection of customer dissatisfaction signals."""
        signals = bi_analyzer._detect_dissatisfaction_signals(sample_transcript_segments)
        
        assert isinstance(signals, list)
        assert len(signals) > 0  # Should detect "frustrated"
        
        for signal in signals:
            assert isinstance(signal, TranscriptEvidence)
            assert signal.speaker == CallParticipant.CUSTOMER
            assert any(keyword in signal.evidence_text.lower() 
                      for keyword in ['frustrated', 'angry', 'disappointed', 'unhappy'])
    
    def test_switching_intent_detection(self, bi_analyzer, sample_transcript_segments):
        """Test detection of switching intent."""
        switching_signals = bi_analyzer._detect_switching_intent(sample_transcript_segments)
        
        assert isinstance(switching_signals, list)
        assert len(switching_signals) > 0  # Should detect "switching to your competitor"
        
        for signal in switching_signals:
            assert isinstance(signal, TranscriptEvidence)
            assert 'switch' in signal.evidence_text.lower() or 'competitor' in signal.evidence_text.lower()
    
    def test_churn_probability_calculation(self, bi_analyzer):
        """Test churn probability calculation."""
        # High churn scenario
        high_churn_evidence = [
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/call.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="I'm switching to your competitor",
                context="Switching intent",
                confidence_score=0.95
            )
        ]
        
        probability = bi_analyzer._calculate_churn_probability(high_churn_evidence, 2.0)
        assert probability >= 0.7  # Should be high
        
        # Low churn scenario
        low_churn_evidence = []
        probability = bi_analyzer._calculate_churn_probability(low_churn_evidence, 9.0)
        assert probability <= 0.3  # Should be low


class TestOpportunityDetection:
    """Test opportunity detection functionality."""
    
    def test_analyze_opportunities(self, bi_analyzer, sample_call_analysis, sample_transcript_segments):
        """Test opportunity analysis."""
        opportunities = bi_analyzer.analyze_opportunities([sample_call_analysis], sample_transcript_segments)
        
        assert isinstance(opportunities, list)
        if len(opportunities) > 0:
            opportunity = opportunities[0]
            assert isinstance(opportunity, OpportunityIndicator)
            assert opportunity.opportunity_type is not None
            assert 0.0 <= opportunity.confidence_score <= 1.0
            assert isinstance(opportunity.evidence, DecisionEvidence)
    
    def test_expansion_signals_detection(self, bi_analyzer, sample_transcript_segments):
        """Test detection of expansion signals."""
        expansion_signals = bi_analyzer._detect_expansion_signals(sample_transcript_segments)
        
        assert isinstance(expansion_signals, list)
        assert len(expansion_signals) > 0  # Should detect "expand our business"
        
        for signal in expansion_signals:
            assert isinstance(signal, TranscriptEvidence)
            assert 'expand' in signal.evidence_text.lower() or 'more services' in signal.evidence_text.lower()
    
    def test_upsell_indicators_detection(self, bi_analyzer):
        """Test detection of upsell indicators."""
        upsell_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="We're looking for additional features and premium support.",
                duration=4.0,
                confidence=0.95
            )
        ]
        
        upsell_signals = bi_analyzer._detect_upsell_indicators(upsell_segments)
        
        assert isinstance(upsell_signals, list)
        assert len(upsell_signals) > 0
        
        for signal in upsell_signals:
            assert isinstance(signal, TranscriptEvidence)
            assert any(keyword in signal.evidence_text.lower() 
                      for keyword in ['additional', 'premium', 'upgrade', 'more'])
    
    def test_cross_sell_opportunities_detection(self, bi_analyzer):
        """Test detection of cross-sell opportunities."""
        cross_sell_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="We also need marketing services and analytics tools.",
                duration=4.0,
                confidence=0.95
            )
        ]
        
        cross_sell_signals = bi_analyzer._detect_cross_sell_opportunities(cross_sell_segments)
        
        assert isinstance(cross_sell_signals, list)
        assert len(cross_sell_signals) > 0
        
        for signal in cross_sell_signals:
            assert isinstance(signal, TranscriptEvidence)
            assert 'also' in signal.evidence_text.lower() or 'need' in signal.evidence_text.lower()


class TestTrainingNeedsAnalysis:
    """Test training needs assessment functionality."""
    
    def test_analyze_training_needs(self, bi_analyzer, sample_call_analysis, sample_transcript_segments):
        """Test training needs analysis."""
        training_needs = bi_analyzer.analyze_training_needs([sample_call_analysis], sample_transcript_segments)
        
        assert isinstance(training_needs, list)
        if len(training_needs) > 0:
            need = training_needs[0]
            assert isinstance(need, TrainingNeedsIndicator)
            assert need.agent_name is not None
            assert need.skill_gap is not None
            assert need.priority_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            assert isinstance(need.evidence, DecisionEvidence)
    
    def test_empathy_skills_assessment(self, bi_analyzer, sample_call_analysis):
        """Test empathy skills assessment."""
        empathy_issues = bi_analyzer._assess_empathy_skills(sample_call_analysis)
        
        assert isinstance(empathy_issues, list)
        # Should identify empathy issues based on low empathy score (5.5)
        if len(empathy_issues) > 0:
            for issue in empathy_issues:
                assert isinstance(issue, TranscriptEvidence)
                assert 'empathy' in issue.context.lower()
    
    def test_objection_handling_assessment(self, bi_analyzer):
        """Test objection handling assessment."""
        objection_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="This is too expensive for our budget.",
                duration=3.0,
                confidence=0.95
            ),
            TranscriptSegment(
                timestamp=5.0,
                speaker=CallParticipant.AGENT,
                text="Well, that's the price.",  # Poor objection handling
                duration=2.0,
                confidence=0.95
            )
        ]
        
        objection_issues = bi_analyzer._assess_objection_handling(objection_segments)
        
        assert isinstance(objection_issues, list)
        assert len(objection_issues) > 0  # Should detect poor objection handling
        
        for issue in objection_issues:
            assert isinstance(issue, TranscriptEvidence)
            assert 'objection' in issue.context.lower()
    
    def test_product_knowledge_assessment(self, bi_analyzer, sample_call_analysis):
        """Test product knowledge assessment."""
        knowledge_issues = bi_analyzer._assess_product_knowledge(sample_call_analysis)
        
        assert isinstance(knowledge_issues, list)
        # Should identify knowledge issues based on low knowledge score (6.0)
        if len(knowledge_issues) > 0:
            for issue in knowledge_issues:
                assert isinstance(issue, TranscriptEvidence)
                assert 'knowledge' in issue.context.lower()


class TestQualityIssuesAnalysis:
    """Test quality issues detection functionality."""
    
    def test_analyze_quality_issues(self, bi_analyzer, sample_call_analysis, sample_transcript_segments):
        """Test quality issues analysis."""
        quality_issues = bi_analyzer.analyze_quality_issues([sample_call_analysis], sample_transcript_segments)
        
        assert isinstance(quality_issues, list)
        if len(quality_issues) > 0:
            issue = quality_issues[0]
            assert isinstance(issue, QualityIssue)
            assert issue.issue_type is not None
            assert issue.severity in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            assert isinstance(issue.evidence, DecisionEvidence)
    
    def test_communication_issues_detection(self, bi_analyzer, sample_call_analysis):
        """Test communication issues detection."""
        comm_issues = bi_analyzer._detect_communication_issues(sample_call_analysis)
        
        assert isinstance(comm_issues, list)
        # Should detect issues based on low clarity score (6.5)
        if len(comm_issues) > 0:
            for issue in comm_issues:
                assert isinstance(issue, TranscriptEvidence)
                assert 'communication' in issue.context.lower()
    
    def test_technical_issues_detection(self, bi_analyzer):
        """Test technical issues detection."""
        technical_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="The system keeps crashing and the application won't load.",
                duration=4.0,
                confidence=0.95
            )
        ]
        
        tech_issues = bi_analyzer._detect_technical_issues(technical_segments)
        
        assert isinstance(tech_issues, list)
        assert len(tech_issues) > 0  # Should detect "crashing" and "won't load"
        
        for issue in tech_issues:
            assert isinstance(issue, TranscriptEvidence)
            assert any(keyword in issue.evidence_text.lower() 
                      for keyword in ['crash', 'error', 'bug', 'issue'])
    
    def test_process_issues_detection(self, bi_analyzer):
        """Test process issues detection."""
        process_segments = [
            TranscriptSegment(
                timestamp=0.0,
                speaker=CallParticipant.CUSTOMER,
                text="I've been transferred three times and no one can help me.",
                duration=4.0,
                confidence=0.95
            )
        ]
        
        process_issues = bi_analyzer._detect_process_issues(process_segments)
        
        assert isinstance(process_issues, list)
        assert len(process_issues) > 0  # Should detect transfer issues
        
        for issue in process_issues:
            assert isinstance(issue, TranscriptEvidence)
            assert 'transfer' in issue.evidence_text.lower()


class TestEvidenceCollection:
    """Test evidence collection and validation."""
    
    def test_collect_evidence(self, bi_analyzer, sample_transcript_segments):
        """Test evidence collection from transcript segments."""
        keywords = ['expensive', 'frustrated']
        evidence = bi_analyzer._collect_evidence(
            sample_transcript_segments,
            keywords,
            "Price and satisfaction concerns"
        )
        
        assert isinstance(evidence, list)
        assert len(evidence) > 0
        
        for item in evidence:
            assert isinstance(item, TranscriptEvidence)
            assert item.call_id is not None
            assert item.transcript_source is not None
            assert 0.0 <= item.confidence_score <= 1.0
    
    def test_validate_evidence_quality(self, bi_analyzer):
        """Test evidence quality validation."""
        evidence = [
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/call.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="This is too expensive",
                context="Price objection",
                confidence_score=0.9
            ),
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/call.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="I love this service",
                context="Satisfaction",
                confidence_score=0.8
            )
        ]
        
        validated_evidence = bi_analyzer._validate_evidence_quality(evidence, "deal_risk")
        
        assert isinstance(validated_evidence, list)
        assert len(validated_evidence) <= len(evidence)  # May filter out contradictory evidence
    
    def test_calculate_confidence_score(self, bi_analyzer):
        """Test confidence score calculation."""
        # High confidence scenario
        high_conf_text = "I am definitely switching to your competitor next month"
        keywords = ['switch', 'competitor']
        score = bi_analyzer._calculate_confidence_score(high_conf_text, keywords)
        assert score >= 0.8
        
        # Low confidence scenario
        low_conf_text = "Maybe we could consider other options"
        score = bi_analyzer._calculate_confidence_score(low_conf_text, keywords)
        assert score <= 0.5


class TestBusinessIntelligenceIntegration:
    """Test full business intelligence analysis integration."""
    
    def test_generate_business_intelligence(self, bi_analyzer, sample_call_analysis, sample_transcript_segments):
        """Test full business intelligence generation."""
        analysis_results = [sample_call_analysis]
        
        bi_insights = bi_analyzer.generate_business_intelligence(
            analysis_results, 
            [sample_transcript_segments],
            time_period="Test Analysis"
        )
        
        assert isinstance(bi_insights, BusinessIntelligenceInsights)
        assert bi_insights.time_period == "Test Analysis"
        assert bi_insights.analysis_timestamp is not None
        assert isinstance(bi_insights.deals_at_risk, list)
        assert isinstance(bi_insights.churn_risks, list)
        assert isinstance(bi_insights.opportunities, list)
        assert isinstance(bi_insights.training_needs, list)
        assert isinstance(bi_insights.quality_issues, list)
        
        # Check evidence summary
        assert bi_insights.evidence_summary is not None
        assert bi_insights.evidence_summary.total_evidence_items >= 0
        assert 0.0 <= bi_insights.evidence_summary.analysis_confidence <= 1.0
    
    def test_prioritize_insights(self, bi_analyzer):
        """Test insight prioritization."""
        # Create mock insights with different risk levels
        risks = [
            DealRiskIndicator(
                account_name="Account A",
                agent_name="Agent 1",
                risk_level=RiskLevel.CRITICAL,
                risk_factors=['price_objection'],
                recommended_actions=['immediate_follow_up'],
                win_probability_change=-0.8,
                evidence=DecisionEvidence(
                    decision_type="deal_risk",
                    primary_evidence=[],
                    confidence_level=0.9,
                    analysis_methodology="Test"
                ),
                risk_score_breakdown={}
            ),
            DealRiskIndicator(
                account_name="Account B",
                agent_name="Agent 2",
                risk_level=RiskLevel.LOW,
                risk_factors=[],
                recommended_actions=[],
                win_probability_change=-0.1,
                evidence=DecisionEvidence(
                    decision_type="deal_risk",
                    primary_evidence=[],
                    confidence_level=0.5,
                    analysis_methodology="Test"
                ),
                risk_score_breakdown={}
            )
        ]
        
        prioritized = bi_analyzer._prioritize_insights(risks)
        
        assert isinstance(prioritized, list)
        assert len(prioritized) == len(risks)
        # Critical risk should be first
        assert prioritized[0].risk_level == RiskLevel.CRITICAL
        assert prioritized[1].risk_level == RiskLevel.LOW
    
    def test_evidence_summary_calculation(self, bi_analyzer):
        """Test evidence summary calculation."""
        all_evidence = [
            TranscriptEvidence(
                call_id="CALL_001",
                transcript_source="s3://bucket/call1.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="Test evidence 1",
                context="Test context",
                confidence_score=0.9
            ),
            TranscriptEvidence(
                call_id="CALL_002", 
                transcript_source="s3://bucket/call2.json",
                speaker=CallParticipant.CUSTOMER,
                evidence_text="Test evidence 2",
                context="Test context",
                confidence_score=0.7
            )
        ]
        
        summary = bi_analyzer._calculate_evidence_summary(all_evidence)
        
        assert summary.total_evidence_items == 2
        assert summary.calls_with_evidence == 2  # Two different call IDs
        assert 0.0 <= summary.analysis_confidence <= 1.0
        assert summary.analysis_confidence == 0.8  # Average of 0.9 and 0.7


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_analysis_results(self, bi_analyzer):
        """Test handling of empty analysis results."""
        bi_insights = bi_analyzer.generate_business_intelligence([], [], "Empty Test")
        
        assert isinstance(bi_insights, BusinessIntelligenceInsights)
        assert len(bi_insights.deals_at_risk) == 0
        assert len(bi_insights.churn_risks) == 0
        assert len(bi_insights.opportunities) == 0
        assert len(bi_insights.training_needs) == 0
        assert len(bi_insights.quality_issues) == 0
    
    def test_invalid_analysis_data(self, bi_analyzer):
        """Test handling of invalid analysis data."""
        # Analysis with missing required fields
        invalid_analysis = CallAnalysisResult(
            call_id="INVALID_CALL",
            analysis_timestamp=datetime.now(),
            transcript_source="test"
        )
        
        # Should handle gracefully without crashing
        try:
            bi_insights = bi_analyzer.generate_business_intelligence(
                [invalid_analysis], 
                [[]], 
                "Invalid Test"
            )
            assert isinstance(bi_insights, BusinessIntelligenceInsights)
        except Exception as e:
            # If it raises an exception, it should be a meaningful one
            assert "Invalid" in str(e) or "Missing" in str(e)
    
    def test_malformed_transcript_segments(self, bi_analyzer):
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
        evidence = bi_analyzer._collect_evidence(
            malformed_segments,
            ['test'],
            "Test context"
        )
        
        assert isinstance(evidence, list)
        # May be empty due to invalid data, but shouldn't crash