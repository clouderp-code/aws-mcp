"""
AI-Powered Analysis Service using GPT models for advanced business intelligence.
"""
import asyncio
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
            {{
                "text": "exact quote from transcript",
                "speaker": "customer|agent",
                "timestamp": 0.0,
                "risk_context": "why this indicates risk"
            }}
        ]
    }}
    """

    # New batch analysis prompts
    BATCH_DEAL_RISK_ANALYSIS = """
    Analyze these {num_calls} sales call transcripts for deal risks. For each call, look for:
    - Price objections or concerns
    - Competitor mentions
    - Hesitation or uncertainty
    - Budget constraints
    - Decision-making delays
    - Lack of urgency
    
    Call transcripts:
    {batch_transcript_text}
    
    Respond with JSON containing an array of analyses, one for each call in order:
    {{
        "analyses": [
            {{
                "call_id": "call_id_1",
                "risk_level": "low|medium|high",
                "risk_factors": ["specific risk factor 1", "risk factor 2"],
                "win_probability_change": -0.XX (negative number 0 to -1),
                "account_value": estimated_value_number,
                "recommended_actions": ["specific action 1", "action 2"],
                "evidence_quotes": [
                    {{
                        "text": "exact quote from transcript",
                        "speaker": "customer|agent",
                        "timestamp": 0.0,
                        "risk_context": "why this indicates risk"
                    }}
                ]
            }}
        ]
    }}
    """

    BATCH_CHURN_RISK_ANALYSIS = """
    Analyze these {num_calls} customer call transcripts for churn risks. For each call, look for:
    - Dissatisfaction indicators
    - Competitive threats
    - Service complaints
    - Relationship degradation
    - Support escalations
    - Cancellation mentions
    
    Call transcripts:
    {batch_transcript_text}
    
    Respond with JSON containing an array of analyses, one for each call in order:
    {{
        "analyses": [
            {{
                "call_id": "call_id_1",
                "churn_probability": 0.XX (0-1 scale),
                "churn_indicators": ["indicator 1", "indicator 2"],
                "retention_actions": ["action 1", "action 2"],
                "satisfaction_level": "high|medium|low",
                "relationship_health": "strong|stable|at-risk|critical",
                "evidence_quotes": [
                    {{
                        "text": "exact quote from transcript",
                        "speaker": "customer|agent",
                        "timestamp": 0.0,
                        "churn_context": "why this indicates churn risk"
                    }}
                ]
            }}
        ]
    }}
    """

    BATCH_OPPORTUNITY_ANALYSIS = """
    Analyze these {num_calls} sales call transcripts for opportunities. For each call, look for:
    - Upsell/cross-sell opportunities
    - Expansion possibilities
    - Unmet needs
    - Growing requirements
    - Budget availability
    - Positive engagement
    
    Call transcripts:
    {batch_transcript_text}
    
    Respond with JSON containing an array of analyses, one for each call in order:
    {{
        "analyses": [
            {{
                "call_id": "call_id_1",
                "opportunity_type": "upsell|cross-sell|expansion|new_product",
                "opportunity_value": estimated_value_number,
                "confidence_score": 0.XX (0-1 scale),
                "urgency": "high|medium|low",
                "recommended_approach": ["approach 1", "approach 2"],
                "evidence_quotes": [
                    {{
                        "text": "exact quote from transcript",
                        "speaker": "customer|agent", 
                        "timestamp": 0.0,
                        "opportunity_context": "why this indicates opportunity"
                    }}
                ]
            }}
        ]
    }}
    """
    
    CHURN_RISK_ANALYSIS = """
    Analyze this customer call transcript for churn risks. Look for:
    - Dissatisfaction indicators
    - Competitive threats  
    - Service complaints
    - Relationship degradation
    - Support escalations
    - Cancellation mentions
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON containing:
    {{
        "churn_probability": 0.XX (0-1 scale),
        "churn_indicators": ["indicator 1", "indicator 2"],
        "retention_actions": ["action 1", "action 2"],
        "satisfaction_level": "high|medium|low",
        "relationship_health": "strong|stable|at-risk|critical",
        "evidence_quotes": [
            {{
                "text": "exact quote from transcript",
                "speaker": "customer|agent",
                "timestamp": 0.0,
                "churn_context": "why this indicates churn risk"
            }}
        ]
    }}
    """

    OPPORTUNITY_ANALYSIS = """
    Analyze this sales call transcript for opportunities. Look for:
    - Upsell/cross-sell opportunities
    - Expansion possibilities
    - Unmet needs
    - Growing requirements
    - Budget availability
    - Positive engagement
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON containing:
    {{
        "opportunity_type": "upsell|cross-sell|expansion|new_product",
        "estimated_value": estimated_value_number,
        "confidence_level": 0.XX (0-1 scale),
        "timeline": "immediate|short-term|medium-term|long-term",
        "next_steps": ["step 1", "step 2"],
        "evidence_quotes": [
            {{
                "text": "exact quote from transcript",
                "speaker": "customer|agent",
                "timestamp": 0.0,
                "opportunity_context": "why this indicates opportunity"
            }}
        ]
    }}
    """

    SENTIMENT_ANALYSIS = """
    Analyze the sentiment and emotional tone of this call transcript. Look for:
    - Overall customer sentiment
    - Agent performance indicators
    - Emotional moments and tone changes
    - Customer satisfaction signals
    - Areas for improvement
    
    Transcript segments:
    {transcript_text}
    
    Respond with JSON containing:
    {{
        "overall_sentiment": "positive|neutral|negative",
        "sentiment_score": X.X (-1.0 to 1.0 scale),
        "customer_satisfaction": X.X (1.0 to 10.0 scale),
        "agent_performance": X.X (1.0 to 10.0 scale),
        "emotional_moments": [
            {{
                "timestamp": 0.0,
                "emotion": "frustrated|excited|confused|satisfied",
                "intensity": "low|medium|high",
                "context": "what triggered this emotion"
            }}
        ],
        "improvement_suggestions": ["suggestion 1", "suggestion 2"]
    }}
    """

    BATCH_SENTIMENT_ANALYSIS = """
    Analyze the sentiment and emotional tone for these {num_calls} call transcripts. For each call, look for:
    - Overall customer sentiment
    - Agent performance indicators  
    - Emotional moments and tone changes
    - Customer satisfaction signals
    - Areas for improvement
    
    Call transcripts:
    {batch_transcript_text}
    
    Respond with JSON containing an array of analyses, one for each call in order:
    {{
        "analyses": [
            {{
                "call_id": "call_id_1",
                "overall_sentiment": "positive|neutral|negative",
                "sentiment_score": X.X (-1.0 to 1.0 scale),
                "customer_satisfaction": X.X (1.0 to 10.0 scale),
                "agent_performance": X.X (1.0 to 10.0 scale),
                "emotional_moments": [
                    {{
                        "timestamp": 0.0,
                        "emotion": "frustrated|excited|confused|satisfied",
                        "intensity": "low|medium|high",
                        "context": "what triggered this emotion"
                    }}
                ],
                "improvement_suggestions": ["suggestion 1", "suggestion 2"]
            }}
        ]
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
    
    async def _call_gpt(self, prompt: str, max_tokens: int = 1000, timeout: int = 30) -> Optional[Dict]:
        """Call GPT model and return parsed JSON response with timeout."""
        if not self.client:
            logger.warning("GPT not available, using fallback analysis")
            return None
        
        logger.debug(f"Calling GPT with {len(prompt)} character prompt")
        try:
            # Use asyncio.wait_for to add timeout control
            def make_gpt_call():
                return self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert business analyst. Provide accurate, actionable insights based on call transcripts. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.2
                )
            
            response = await asyncio.wait_for(
                asyncio.to_thread(make_gpt_call), 
                timeout=timeout
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try multiple JSON extraction and parsing methods
            json_data = None
            
            # Method 1: Extract JSON block
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    json_content = json_match.group()
                    # Clean common JSON issues
                    json_content = re.sub(r',\s*}', '}', json_content)  # Remove trailing commas
                    json_content = re.sub(r',\s*]', ']', json_content)  # Remove trailing commas in arrays
                    json_data = json.loads(json_content)
                except json.JSONDecodeError:
                    pass
            
            # Method 2: Try parsing the whole content directly
            if json_data is None:
                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError:
                    pass
            
            # Method 3: Try extracting JSON between triple backticks (improved for batch responses)
            if json_data is None:
                # Look for markdown code blocks containing JSON
                if '```' in content:
                    # Find all potential code blocks
                    code_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                    for block in code_blocks:
                        try:
                            block = block.strip()
                            
                            # More aggressive JSON cleaning for large responses
                            block = re.sub(r',\s*}', '}', block)      # Remove trailing commas before }
                            block = re.sub(r',\s*]', ']', block)      # Remove trailing commas before ]
                            block = re.sub(r'}\s*,\s*]', '}]', block) # Fix },] patterns
                            block = re.sub(r'"\s*,\s*}', '"}', block) # Fix "...",} patterns
                            
                            # Handle incomplete responses - try to find complete JSON structures
                            if not block.endswith('}') and not block.endswith(']'):
                                # Try to find the last complete object/array
                                brace_count = 0
                                last_complete_pos = -1
                                for i, char in enumerate(block):
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            last_complete_pos = i + 1
                                
                                if last_complete_pos > 0:
                                    block = block[:last_complete_pos]
                            
                            # If it doesn't start with {, try to find the JSON object within it
                            if not block.startswith('{'):
                                json_match = re.search(r'\{.*\}', block, re.DOTALL)
                                if json_match:
                                    block = json_match.group()
                            
                            if block.startswith('{'):
                                json_data = json.loads(block)
                                if json_data:
                                    break
                        except json.JSONDecodeError as e:
                            logger.debug(f"JSON parsing attempt failed: {e}")
                            continue
            
            if json_data:
                logger.debug(f"Successfully parsed GPT response JSON")
                return json_data
            else:
                # More detailed error logging to help debug
                logger.warning(f"Failed to parse JSON from GPT response. Content length: {len(content)}")
                logger.debug(f"Raw GPT response: {content[:500]}...")
                
                # Check if response looks like it was truncated
                if content.endswith('...') or len(content) >= max_tokens * 4:  # Rough estimate
                    logger.warning("GPT response may have been truncated. Consider increasing max_tokens.")
                
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"GPT analysis timed out after {timeout}s, using fallback")
            return None
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
        logger.info(f"Starting AI deal risk analysis for call {call_id}")
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 50:  # Skip very short transcripts
            logger.info(f"Skipping deal risk analysis for {call_id} - transcript too short")
            return None
        
        logger.info(f"Calling GPT for deal risk analysis of {call_id}")
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
            analysis_methodology="GPT-4o analysis of customer language and sentiment" if gpt_result else "Keyword-based risk detection"
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
        logger.info(f"Starting AI churn risk analysis for call {call_id}")
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 50:
            logger.info(f"Skipping churn risk analysis for {call_id} - transcript too short")
            return None
        
        logger.info(f"Calling GPT for churn risk analysis of {call_id}")
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
        logger.info(f"Starting AI opportunity analysis for call {call_id}")
        transcript_text = self._prepare_transcript_text(segments)
        
        if len(transcript_text.strip()) < 50:
            logger.info(f"Skipping opportunity analysis for {call_id} - transcript too short")
            return []
        
        logger.info(f"Calling GPT for opportunity analysis of {call_id}")
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
    
    # New batch analysis methods for improved performance
    async def batch_analyze_deal_risks(self, call_batches: List[Dict], batch_size: int = 10) -> List[DealRiskIndicator]:
        """Analyze deal risks for multiple calls in batches for improved performance."""
        all_deal_risks = []
        
        for i in range(0, len(call_batches), batch_size):
            batch = call_batches[i:i + batch_size]
            logger.info(f"Processing deal risk batch {i//batch_size + 1} with {len(batch)} calls")
            
            # Prepare batch transcript text
            batch_transcript_parts = []
            call_metadata = []
            
            for call_data in batch:
                call_id = call_data["call_id"]
                segments = call_data["segments"]
                transcript_text = self._prepare_transcript_text(segments)
                
                if len(transcript_text.strip()) < 50:
                    continue  # Skip very short transcripts
                
                batch_transcript_parts.append(f"CALL_ID: {call_id}\n{transcript_text}\n---")
                call_metadata.append(call_data)
            
            if not batch_transcript_parts:
                continue
                
            # Make single API call for the batch
            batch_transcript_text = "\n".join(batch_transcript_parts)
            prompt = AIAnalysisPrompts.BATCH_DEAL_RISK_ANALYSIS.format(
                num_calls=len(call_metadata),
                batch_transcript_text=batch_transcript_text
            )
            
            gpt_result = await self._call_gpt(prompt, max_tokens=6000, timeout=45)
            
            if gpt_result and "analyses" in gpt_result:
                # Process each analysis result
                for j, analysis in enumerate(gpt_result["analyses"]):
                    if j >= len(call_metadata):
                        break
                        
                    call_data = call_metadata[j]
                    call_id = call_data["call_id"]
                    
                    if analysis.get("risk_level") == "low" and not analysis.get("risk_factors"):
                        continue  # Skip low risk calls with no factors
                    
                    # Create evidence from quotes
                    evidence_list = []
                    for quote in analysis.get("evidence_quotes", []):
                        evidence_list.append(TranscriptEvidence(
                            call_id=call_id,
                            transcript_source=call_data.get("transcript_source", f"{call_id}.json"),
                            speaker=CallParticipant.CUSTOMER if quote.get("speaker") == "customer" else CallParticipant.AGENT,
                            timestamp=quote.get("timestamp", 0.0),
                            evidence_text=quote.get("text", ""),
                            context=quote.get("risk_context", "Deal risk indicator"),
                            confidence_score=0.8
                        ))
                    
                    decision_evidence = DecisionEvidence(
                        decision_type="deal_risk_assessment",
                        primary_evidence=evidence_list,
                        confidence_level=0.7,
                        analysis_methodology="Batch GPT-4o analysis of customer language and sentiment"
                    )
                    
                    deal_risk = DealRiskIndicator(
                        account_name=call_data.get("account_name", f"Account_{call_id}"),
                        agent_name=call_data.get("agent_name", f"Agent_{call_id}"),
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
                    
                    all_deal_risks.append(deal_risk)
        
        return all_deal_risks
    
    async def batch_analyze_churn_risks(self, call_batches: List[Dict], batch_size: int = 10) -> List[ChurnRiskIndicator]:
        """Analyze churn risks for multiple calls in batches for improved performance."""
        all_churn_risks = []
        
        for i in range(0, len(call_batches), batch_size):
            batch = call_batches[i:i + batch_size]
            logger.info(f"Processing churn risk batch {i//batch_size + 1} with {len(batch)} calls")
            
            # Prepare batch transcript text
            batch_transcript_parts = []
            call_metadata = []
            
            for call_data in batch:
                call_id = call_data["call_id"]
                segments = call_data["segments"]
                transcript_text = self._prepare_transcript_text(segments)
                
                if len(transcript_text.strip()) < 50:
                    continue  # Skip very short transcripts
                
                batch_transcript_parts.append(f"CALL_ID: {call_id}\n{transcript_text}\n---")
                call_metadata.append(call_data)
            
            if not batch_transcript_parts:
                continue
                
            # Make single API call for the batch
            batch_transcript_text = "\n".join(batch_transcript_parts)
            prompt = AIAnalysisPrompts.BATCH_CHURN_RISK_ANALYSIS.format(
                num_calls=len(call_metadata),
                batch_transcript_text=batch_transcript_text
            )
            
            gpt_result = await self._call_gpt(prompt, max_tokens=6000, timeout=45)
            
            if gpt_result and "analyses" in gpt_result:
                # Process each analysis result
                for j, analysis in enumerate(gpt_result["analyses"]):
                    if j >= len(call_metadata):
                        break
                        
                    call_data = call_metadata[j]
                    call_id = call_data["call_id"]
                    
                    if analysis.get("churn_probability", 0) < 0.3:
                        continue  # Skip low churn probability calls
                    
                    # Create evidence from quotes
                    evidence_list = []
                    for quote in analysis.get("evidence_quotes", []):
                        evidence_list.append(TranscriptEvidence(
                            call_id=call_id,
                            transcript_source=call_data.get("transcript_source", f"{call_id}.json"),
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
                        analysis_methodology="Batch GPT-4o analysis of customer satisfaction and retention signals"
                    )
                    
                    # Map intervention urgency to RiskLevel enum values
                    urgency_map = {"high": RiskLevel.HIGH, "medium": RiskLevel.MEDIUM, "low": RiskLevel.LOW}
                    intervention_urgency = urgency_map.get(analysis.get("urgency", "medium"), RiskLevel.MEDIUM)
                    
                    # Create churn timeline
                    churn_timeline = [
                        {"timestamp": 0.0, "signal": "Initial assessment", "severity": analysis["churn_probability"]},
                        {"timestamp": len(call_data["segments"]) * 30, "signal": "Call completion", "severity": analysis["churn_probability"]}
                    ]
                    
                    churn_risk = ChurnRiskIndicator(
                        account_name=call_data.get("account_name", f"Account_{call_id}"),
                        churn_probability=analysis["churn_probability"],
                        risk_signals=analysis["churn_indicators"],
                        intervention_urgency=intervention_urgency,
                        recommended_actions=analysis["retention_actions"],
                        account_value_at_risk=call_data.get("account_value"),
                        evidence=decision_evidence,
                        churn_indicators_timeline=churn_timeline
                    )
                    
                    all_churn_risks.append(churn_risk)
        
        return all_churn_risks
    
    async def batch_analyze_opportunities(self, call_batches: List[Dict], batch_size: int = 10) -> List[OpportunityIndicator]:
        """Analyze opportunities for multiple calls in batches for improved performance."""
        all_opportunities = []
        
        for i in range(0, len(call_batches), batch_size):
            batch = call_batches[i:i + batch_size]
            logger.info(f"Processing opportunity batch {i//batch_size + 1} with {len(batch)} calls")
            
            # Prepare batch transcript text
            batch_transcript_parts = []
            call_metadata = []
            
            for call_data in batch:
                call_id = call_data["call_id"]
                segments = call_data["segments"]
                transcript_text = self._prepare_transcript_text(segments)
                
                if len(transcript_text.strip()) < 50:
                    continue  # Skip very short transcripts
                
                batch_transcript_parts.append(f"CALL_ID: {call_id}\n{transcript_text}\n---")
                call_metadata.append(call_data)
            
            if not batch_transcript_parts:
                continue
                
            # Make single API call for the batch
            batch_transcript_text = "\n".join(batch_transcript_parts)
            prompt = AIAnalysisPrompts.BATCH_OPPORTUNITY_ANALYSIS.format(
                num_calls=len(call_metadata),
                batch_transcript_text=batch_transcript_text
            )
            
            gpt_result = await self._call_gpt(prompt, max_tokens=6000, timeout=45)
            
            if gpt_result and "analyses" in gpt_result:
                # Process each analysis result
                for j, analysis in enumerate(gpt_result["analyses"]):
                    if j >= len(call_metadata):
                        break
                        
                    call_data = call_metadata[j]
                    call_id = call_data["call_id"]
                    
                    if analysis.get("confidence_score", 0) < 0.3:
                        continue  # Skip low confidence opportunities
                    
                    # Create evidence from quotes
                    evidence_list = []
                    for quote in analysis.get("evidence_quotes", []):
                        evidence_list.append(TranscriptEvidence(
                            call_id=call_id,
                            transcript_source=call_data.get("transcript_source", f"{call_id}.json"),
                            speaker=CallParticipant.CUSTOMER if quote.get("speaker") == "customer" else CallParticipant.AGENT,
                            timestamp=quote.get("timestamp", 0.0),
                            evidence_text=quote.get("text", ""),
                            context=quote.get("opportunity_context", "Business opportunity indicator"),
                            confidence_score=0.7
                        ))
                    
                    decision_evidence = DecisionEvidence(
                        decision_type="opportunity_identification",
                        primary_evidence=evidence_list,
                        confidence_level=analysis["confidence_score"],
                        analysis_methodology="Batch AI analysis of expansion signals and customer language"
                    )
                    
                    # Handle estimated_value conversion - ensure it's never None
                    estimated_value = analysis.get("opportunity_value", 0.0)
                    if estimated_value is None:
                        estimated_value = 0.0
                    elif isinstance(estimated_value, str):
                        if estimated_value.lower() in ['unknown', 'none', '']:
                            estimated_value = 0.0
                        else:
                            try:
                                estimated_value = float(estimated_value)
                            except (ValueError, TypeError):
                                estimated_value = 0.0
                    elif not isinstance(estimated_value, (int, float)):
                        estimated_value = 0.0
                    
                    # Create opportunity signals strength breakdown
                    confidence = analysis["confidence_score"]
                    opportunity_signals = {
                        "customer_interest": confidence * 0.8,
                        "budget_availability": confidence * 0.6,
                        "timeline_urgency": confidence * 0.5,
                        "expansion_potential": confidence * 0.7
                    }
                    
                    opportunity = OpportunityIndicator(
                        account_name=call_data.get("account_name", f"Account_{call_id}"),
                        opportunity_type=analysis["opportunity_type"],
                        estimated_value=estimated_value,
                        confidence_level=confidence,
                        next_steps=analysis["recommended_approach"],
                        timeline=analysis.get("urgency", "medium"),
                        evidence=decision_evidence,
                        opportunity_signals_strength=opportunity_signals
                    )
                    
                    all_opportunities.append(opportunity)
        
        return all_opportunities 

    async def batch_sentiment_analysis(self, call_batches: List[Dict], batch_size: int = 10) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple calls in batches for improved performance."""
        all_sentiment_analyses = []
        
        for i in range(0, len(call_batches), batch_size):
            batch = call_batches[i:i + batch_size]
            logger.info(f"Processing sentiment batch {i//batch_size + 1} with {len(batch)} calls")
            
            # Prepare batch transcript text
            batch_transcript_parts = []
            call_metadata = []
            
            for call_data in batch:
                call_id = call_data["call_id"]
                segments = call_data["segments"]
                transcript_text = self._prepare_transcript_text(segments)
                
                if len(transcript_text.strip()) < 20: # Minimum length for sentiment analysis
                    continue
                
                batch_transcript_parts.append(f"CALL_ID: {call_id}\n{transcript_text}\n---")
                call_metadata.append(call_data)
            
            if not batch_transcript_parts:
                continue
                
            # Make single API call for the batch
            batch_transcript_text = "\n".join(batch_transcript_parts)
            prompt = AIAnalysisPrompts.BATCH_SENTIMENT_ANALYSIS.format(
                num_calls=len(call_metadata),
                batch_transcript_text=batch_transcript_text
            )
            
            gpt_result = await self._call_gpt(prompt, max_tokens=6000, timeout=45)
            
            if gpt_result and "analyses" in gpt_result:
                # Process each analysis result
                for j, analysis in enumerate(gpt_result["analyses"]):
                    if j >= len(call_metadata):
                        break
                        
                    call_data = call_metadata[j]
                    call_id = call_data["call_id"]
                    
                    sentiment_analysis = {
                        "call_id": call_id,
                        "overall_sentiment": analysis.get("overall_sentiment", "neutral"),
                        "sentiment_score": analysis.get("sentiment_score", 0.0),
                        "customer_satisfaction": analysis.get("customer_satisfaction", 5.0),
                        "agent_performance": analysis.get("agent_performance", 5.0),
                        "emotional_moments": analysis.get("emotional_moments", []),
                        "improvement_suggestions": analysis.get("improvement_suggestions", [])
                    }
                    all_sentiment_analyses.append(sentiment_analysis)
        
        return all_sentiment_analyses 