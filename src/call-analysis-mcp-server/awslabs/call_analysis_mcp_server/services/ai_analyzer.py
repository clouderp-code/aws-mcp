"""
AI-Powered Analysis Service using GPT models for advanced business intelligence.
"""
import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from loguru import logger
from pydantic import BaseModel, Field

from ..models import (
    TranscriptSegment, CallParticipant, SentimentType, RiskLevel,
    DealRiskIndicator, ChurnRiskIndicator, OpportunityIndicator,
    TranscriptEvidence, DecisionEvidence
)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")


class AIAnalysisPrompts:
    """Structured prompts for GPT-powered analysis."""
    
    DEAL_RISK_ANALYSIS = """
    Analyze this sales call transcript for deal risks. Look for:
    - Price objections or concerns
    - Competitor mentions
    - Hesitation or uncertainty
    - Budget constraints
    - Decision-making delays
    - Lack of urgency
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON containing:
    {{
        "risk_level": "low|medium|high",
        "risk_factors": ["specific risk factor 1", "risk factor 2"],
        "win_probability_change": -0.XX (negative number 0 to -1),
        "account_value": estimated_value_number,
        "recommended_actions": ["specific action 1", "action 2"],
        "evidence_quotes": [
            {{"speaker": "customer|agent", "text": "exact quote", "timestamp": XX.X, "risk_context": "why this indicates risk"}}
        ]
    }}
    """
    
    CHURN_RISK_ANALYSIS = """
    Analyze this customer call for churn risk signals:
    - Mentions of switching providers
    - Dissatisfaction with service
    - Contract renewal concerns
    - Price complaints
    - Service quality issues
    - Competitor comparisons
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON:
    {{
        "churn_probability": 0.XX (0 to 1),
        "risk_signals": ["signal 1", "signal 2"],
        "intervention_urgency": "low|medium|high",
        "account_value_at_risk": estimated_value,
        "recommended_actions": ["action 1", "action 2"],
        "evidence_quotes": [
            {{"speaker": "customer|agent", "text": "exact quote", "timestamp": XX.X, "churn_context": "why this indicates churn risk"}}
        ]
    }}
    """
    
    OPPORTUNITY_ANALYSIS = """
    Identify upsell, cross-sell, and expansion opportunities:
    - Interest in additional services
    - Growing business needs
    - Budget availability mentions
    - Future project discussions
    - Positive sentiment about current services
    - Expansion plans
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON:
    {{
        "opportunity_type": "upsell|cross_sell|expansion|renewal",
        "estimated_value": dollar_amount,
        "confidence_level": 0.XX (0 to 1),
        "timeline": "time estimate",
        "next_steps": ["step 1", "step 2"],
        "evidence_quotes": [
            {{"speaker": "customer|agent", "text": "exact quote", "timestamp": XX.X, "opportunity_context": "why this indicates opportunity"}}
        ]
    }}
    """
    
    SENTIMENT_ANALYSIS = """
    Provide detailed sentiment analysis of this call:
    - Overall call sentiment
    - Customer sentiment progression
    - Agent performance assessment
    - Key emotional moments
    - Satisfaction indicators
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON:
    {{
        "overall_sentiment": "positive|neutral|negative",
        "sentiment_score": 0.XX (-1 to 1),
        "customer_satisfaction": X.X (1 to 10),
        "agent_performance": X.X (1 to 10),
        "emotional_moments": [
            {{"timestamp": XX.X, "emotion": "emotion type", "context": "what happened", "impact": "positive|negative"}}
        ],
        "improvement_suggestions": ["suggestion 1", "suggestion 2"]
    }}
    """


class AIAnalyzer:
    """AI-powered analysis service using GPT models."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI analyzer with OpenAI API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("AI analyzer initialized with OpenAI GPT models")
        else:
            self.client = None
            logger.warning("AI analyzer initialized in fallback mode (no OpenAI)")
    
    def _prepare_transcript_text(self, segments: List[TranscriptSegment]) -> str:
        """Prepare transcript text for GPT analysis."""
        transcript_lines = []
        for segment in segments:
            timestamp = f"{segment.timestamp:.1f}s" if segment.timestamp else "0.0s"
            speaker = segment.speaker.value if hasattr(segment.speaker, 'value') else str(segment.speaker)
            transcript_lines.append(f"[{timestamp}] {speaker}: {segment.text}")
        return "\n".join(transcript_lines)
    
    async def _call_gpt(self, prompt: str, max_tokens: int = 1000) -> Optional[Dict]:
        """Call GPT model and return parsed JSON response."""
        if not self.client:
            logger.warning("GPT not available, using fallback analysis")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst. Provide accurate, actionable insights based on call transcripts. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            # Extract JSON from response (in case there's additional text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"GPT analysis error: {str(e)}")
            return None
    
    def _fallback_deal_risk_analysis(self, segments: List[TranscriptSegment]) -> Dict:
        """Fallback analysis when GPT is not available."""
        transcript_text = " ".join([seg.text.lower() for seg in segments])
        
        # Simple keyword-based risk detection
        risk_keywords = ["expensive", "cost", "price", "budget", "competitor", "think about", "delay", "wait"]
        risk_count = sum(1 for keyword in risk_keywords if keyword in transcript_text)
        
        risk_level = "high" if risk_count >= 3 else "medium" if risk_count >= 2 else "low"
        
        return {
            "risk_level": risk_level,
            "risk_factors": [f"Keyword detected: {kw}" for kw in risk_keywords if kw in transcript_text][:3],
            "win_probability_change": -0.1 * risk_count,
            "account_value": 25000.0,
            "recommended_actions": ["Review pricing strategy", "Address customer concerns"],
            "evidence_quotes": []
        }
    
    async def analyze_deal_risk(self, segments: List[TranscriptSegment], call_id: str, account_name: str = None, agent_name: str = None, transcript_source: str = None) -> Optional[DealRiskIndicator]:
        """Analyze deal risk using AI."""
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 50:  # Skip very short transcripts
            return None
        
        prompt = AIAnalysisPrompts.DEAL_RISK_ANALYSIS.format(transcript_text=transcript_text)
        gpt_result = await self._call_gpt(prompt)
        
        # Use GPT result or fallback
        analysis = gpt_result if gpt_result else self._fallback_deal_risk_analysis(segments)
        
        if analysis.get("risk_level") == "low" and not analysis.get("risk_factors"):
            return None  # No significant risk detected
        
        # Create evidence from quotes
        evidence_list = []
        for quote in analysis.get("evidence_quotes", []):
            evidence_list.append(TranscriptEvidence(
                call_id=call_id,
                transcript_source=transcript_source or f"{call_id}.json",
                speaker=CallParticipant.CUSTOMER if quote.get("speaker") == "customer" else CallParticipant.AGENT,
                timestamp=quote.get("timestamp", 0.0),
                evidence_text=quote.get("text", ""),
                context=quote.get("risk_context", "Deal risk indicator"),
                confidence_score=0.8
            ))
        
        decision_evidence = DecisionEvidence(
            decision_type="deal_risk_assessment",
            primary_evidence=evidence_list,
            confidence_level=0.7 if gpt_result else 0.4,
            analysis_methodology="GPT-4 analysis of customer language and sentiment" if gpt_result else "Keyword-based risk detection"
        )
        
        return DealRiskIndicator(
            account_name=account_name or f"Account_{call_id}",
            agent_name=agent_name or f"Agent_{call_id}",
            risk_level=RiskLevel(analysis["risk_level"]),
            risk_factors=analysis["risk_factors"],
            recommended_actions=analysis["recommended_actions"],
            win_probability_change=analysis["win_probability_change"],
            account_value=analysis.get("account_value"),
            evidence=decision_evidence,
            risk_score_breakdown={
                "pricing": 0.3 if "price" in str(analysis["risk_factors"]).lower() else 0.1,
                "competition": 0.4 if "competitor" in str(analysis["risk_factors"]).lower() else 0.1,
                "satisfaction": 0.2,
                "urgency": 0.3 if "delay" in str(analysis["risk_factors"]).lower() else 0.1
            }
        )
    
    async def analyze_churn_risk(self, segments: List[TranscriptSegment], call_id: str, account_name: str = None, agent_name: str = None, transcript_source: str = None) -> Optional[ChurnRiskIndicator]:
        """Analyze churn risk using AI."""
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 50:
            return None
        
        prompt = AIAnalysisPrompts.CHURN_RISK_ANALYSIS.format(transcript_text=transcript_text)
        gpt_result = await self._call_gpt(prompt)
        
        # Fallback analysis
        if not gpt_result:
            transcript_lower = transcript_text.lower()
            churn_keywords = ["switch", "cancel", "leave", "dissatisfied", "competitor", "unhappy"]
            churn_signals = [kw for kw in churn_keywords if kw in transcript_lower]
            
            if not churn_signals:
                return None
            
            gpt_result = {
                "churn_probability": 0.3 + 0.1 * len(churn_signals),
                "risk_signals": [f"Mentioned: {signal}" for signal in churn_signals],
                "intervention_urgency": "medium",
                "account_value_at_risk": 20000.0,
                "recommended_actions": ["Retention call", "Address concerns"],
                "evidence_quotes": []
            }
        
        if gpt_result["churn_probability"] < 0.2:
            return None  # Low churn risk
        
        # Create evidence
        evidence_list = []
        for quote in gpt_result.get("evidence_quotes", []):
            evidence_list.append(TranscriptEvidence(
                call_id=call_id,
                transcript_source=transcript_source or f"{call_id}.json",
                speaker=CallParticipant.CUSTOMER if quote.get("speaker") == "customer" else CallParticipant.AGENT,
                timestamp=quote.get("timestamp", 0.0),
                evidence_text=quote.get("text", ""),
                context=quote.get("churn_context", "Churn risk indicator"),
                confidence_score=0.8
            ))
        
        decision_evidence = DecisionEvidence(
            decision_type="churn_risk_assessment",
            primary_evidence=evidence_list,
            confidence_level=0.7,
            analysis_methodology="AI analysis of customer satisfaction and retention signals"
        )
        
        # Convert intervention urgency to RiskLevel enum
        urgency_map = {"low": RiskLevel.LOW, "medium": RiskLevel.MEDIUM, "high": RiskLevel.HIGH}
        intervention_urgency = urgency_map.get(gpt_result["intervention_urgency"].lower(), RiskLevel.MEDIUM)
        
        # Handle account value at risk - convert to float or None
        account_value = gpt_result.get("account_value_at_risk")
        if isinstance(account_value, str) and account_value.lower() in ['unknown', 'none', '']:
            account_value = None
        elif account_value is not None:
            try:
                account_value = float(account_value)
            except (ValueError, TypeError):
                account_value = None
        
        # Create churn indicators timeline
        churn_timeline = [
            {"timestamp": 0.0, "signal": "Initial assessment", "severity": gpt_result["churn_probability"]},
            {"timestamp": len(segments) * 30, "signal": "Call completion", "severity": gpt_result["churn_probability"]}
        ]
        
        return ChurnRiskIndicator(
            account_name=account_name or f"Account_{call_id}",
            churn_probability=gpt_result["churn_probability"],
            risk_signals=gpt_result["risk_signals"],
            intervention_urgency=intervention_urgency,
            recommended_actions=gpt_result["recommended_actions"],
            account_value_at_risk=account_value,
            evidence=decision_evidence,
            churn_indicators_timeline=churn_timeline
        )
    
    async def analyze_opportunities(self, segments: List[TranscriptSegment], call_id: str, account_name: str = None, agent_name: str = None, transcript_source: str = None) -> List[OpportunityIndicator]:
        """Analyze expansion opportunities using AI."""
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 50:
            return []
        
        prompt = AIAnalysisPrompts.OPPORTUNITY_ANALYSIS.format(transcript_text=transcript_text)
        gpt_result = await self._call_gpt(prompt)
        
        # Fallback analysis
        if not gpt_result:
            transcript_lower = transcript_text.lower()
            opportunity_keywords = ["expand", "additional", "more", "upgrade", "interested", "future", "grow"]
            found_keywords = [kw for kw in opportunity_keywords if kw in transcript_lower]
            
            if not found_keywords:
                return []
            
            gpt_result = {
                "opportunity_type": "expansion",
                "estimated_value": 15000.0,
                "confidence_level": 0.5,
                "timeline": "3-6 months",
                "next_steps": ["Follow-up call", "Send proposal"],
                "evidence_quotes": []
            }
        
        if gpt_result.get("confidence_level", 0) < 0.3:
            return []
        
        # Create evidence
        evidence_list = []
        for quote in gpt_result.get("evidence_quotes", []):
            evidence_list.append(TranscriptEvidence(
                call_id=call_id,
                transcript_source=transcript_source or f"{call_id}.json",
                speaker=CallParticipant.CUSTOMER if quote.get("speaker") == "customer" else CallParticipant.AGENT,
                timestamp=quote.get("timestamp", 0.0),
                evidence_text=quote.get("text", ""),
                context=quote.get("opportunity_context", "Business opportunity indicator"),
                confidence_score=0.7
            ))
        
        decision_evidence = DecisionEvidence(
            decision_type="opportunity_identification",
            primary_evidence=evidence_list,
            confidence_level=gpt_result["confidence_level"],
            analysis_methodology="AI analysis of expansion signals and customer language"
        )
        
        # Handle estimated_value conversion
        estimated_value = gpt_result["estimated_value"]
        if isinstance(estimated_value, str):
            if estimated_value.lower() in ['unknown', 'none', '']:
                estimated_value = 0.0
            else:
                try:
                    estimated_value = float(estimated_value)
                except (ValueError, TypeError):
                    estimated_value = 0.0
        
        # Create opportunity signals strength breakdown
        opportunity_signals = {
            "customer_interest": gpt_result["confidence_level"] * 0.8,
            "budget_availability": gpt_result["confidence_level"] * 0.6,
            "timeline_urgency": gpt_result["confidence_level"] * 0.5,
            "expansion_potential": gpt_result["confidence_level"] * 0.7
        }
        
        opportunity = OpportunityIndicator(
            account_name=account_name or f"Account_{call_id}",
            opportunity_type=gpt_result["opportunity_type"],
            estimated_value=estimated_value,
            confidence_level=gpt_result["confidence_level"],
            next_steps=gpt_result["next_steps"],
            timeline=gpt_result["timeline"],
            evidence=decision_evidence,
            opportunity_signals_strength=opportunity_signals
        )
        
        return [opportunity]
    
    async def enhanced_sentiment_analysis(self, segments: List[TranscriptSegment]) -> Dict[str, Any]:
        """Perform enhanced sentiment analysis using AI."""
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 20:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "customer_satisfaction": 5.0,
                "agent_performance": 5.0,
                "emotional_moments": [],
                "improvement_suggestions": []
            }
        
        prompt = AIAnalysisPrompts.SENTIMENT_ANALYSIS.format(transcript_text=transcript_text)
        gpt_result = await self._call_gpt(prompt)
        
        # Fallback sentiment analysis
        if not gpt_result:
            positive_words = ["great", "excellent", "happy", "satisfied", "good", "thank you"]
            negative_words = ["bad", "terrible", "unhappy", "disappointed", "problem", "issue"]
            
            text_lower = transcript_text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            sentiment_score = (positive_count - negative_count) / max(len(segments), 1)
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            gpt_result = {
                "overall_sentiment": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral",
                "sentiment_score": sentiment_score,
                "customer_satisfaction": 5.0 + sentiment_score * 3,
                "agent_performance": 6.0,
                "emotional_moments": [],
                "improvement_suggestions": ["Continue current approach"] if sentiment_score > 0 else ["Focus on customer concerns"]
            }
        
        return gpt_result 