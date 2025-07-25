#!/usr/bin/env python3
"""
LangGraph Example: Call Analysis Business Intelligence Agent

This example demonstrates how to use the Call Analysis MCP tools
to answer business intelligence questions about call quality, deals,
training needs, and opportunities.
"""

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import Annotated, Dict, Any, List
import json

# Import your MCP connector (adjust path as needed)
# from your_mcp_path import MCPHTTPComponent

class CallAnalysisState:
    """State for the Call Analysis agent"""
    def __init__(self):
        self.messages: List[Dict] = []
        self.analysis_data_available: bool = False
        self.last_question: str = ""
        self.context_type: str = "auto"
        self.results: Dict = {}

class CallAnalysisAgent:
    """Call Analysis Business Intelligence Agent using MCP tools"""
    
    def __init__(self, mcp_connector):
        self.mcp = mcp_connector
        self.context_mapping = {
            "quality": ["quality", "satisfaction", "performance", "agent"],
            "deals": ["risk", "deals", "close", "win", "pipeline"],
            "churn": ["churn", "leave", "cancel", "retention"],
            "opportunities": ["opportunity", "upsell", "expansion", "revenue"],
            "training": ["training", "coaching", "skills", "objection"],
            "pipeline": ["pipeline", "forecast", "conversion", "velocity"],
            "auto": ["general", "overall", "summary"]
        }
    
    def determine_context_type(self, question: str) -> str:
        """Determine the appropriate context type based on the question"""
        question_lower = question.lower()
        
        for context, keywords in self.context_mapping.items():
            if any(keyword in question_lower for keyword in keywords):
                return context
        
        return "auto"
    
    async def check_data_availability(self, state: CallAnalysisState) -> Dict:
        """Check if analysis data is available"""
        try:
            result = await self.mcp.call_tool(
                "ask-analysis-question",
                {
                    "question": "How many calls were analyzed in the latest report?",
                    "context_type": "auto"
                }
            )
            
            if "error" not in result:
                state.analysis_data_available = True
                return {"status": "data_available", "result": result}
            else:
                state.analysis_data_available = False
                return {"status": "no_data", "error": result}
                
        except Exception as e:
            state.analysis_data_available = False
            return {"status": "error", "error": str(e)}
    
    async def generate_analysis(self, state: CallAnalysisState) -> Dict:
        """Generate fresh analysis if needed"""
        try:
            result = await self.mcp.call_tool(
                "analyze-local-scripts",
                {
                    "time_period": "Current Analysis Period",
                    "max_scripts": 50
                }
            )
            
            if "error" not in result:
                state.analysis_data_available = True
                return {"status": "analysis_generated", "result": result}
            else:
                return {"status": "generation_failed", "error": result}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def answer_question(self, state: CallAnalysisState, question: str) -> Dict:
        """Answer business intelligence questions using MCP tools"""
        try:
            # Determine context type
            context_type = self.determine_context_type(question)
            state.context_type = context_type
            state.last_question = question
            
            # Call the ask-analysis-question tool
            result = await self.mcp.call_tool(
                "ask-analysis-question",
                {
                    "question": question,
                    "context_type": context_type
                }
            )
            
            if "error" not in result:
                # Parse the result to extract key information
                analysis_result = self._parse_analysis_result(result)
                state.results = analysis_result
                return {
                    "status": "success",
                    "question": question,
                    "context_type": context_type,
                    "result": analysis_result
                }
            else:
                return {"status": "error", "error": result}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _parse_analysis_result(self, raw_result: str) -> Dict:
        """Parse the analysis result into structured format"""
        try:
            # Try to parse as JSON first
            if isinstance(raw_result, str):
                try:
                    parsed = json.loads(raw_result)
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # If not JSON, extract key information from text
            result = {
                "raw_response": raw_result,
                "summary": self._extract_summary(raw_result),
                "metrics": self._extract_metrics(raw_result),
                "evidence": self._extract_evidence(raw_result),
                "recommendations": self._extract_recommendations(raw_result)
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to parse result: {str(e)}", "raw_result": raw_result}
    
    def _extract_summary(self, text: str) -> str:
        """Extract executive summary from response"""
        lines = text.split('\n')
        for line in lines:
            if 'summary' in line.lower() or 'analysis' in line.lower():
                return line.strip()
        return text[:200] + "..." if len(text) > 200 else text
    
    def _extract_metrics(self, text: str) -> List[str]:
        """Extract key metrics from response"""
        metrics = []
        lines = text.split('\n')
        for line in lines:
            if '•' in line or any(char.isdigit() for char in line):
                if any(keyword in line.lower() for keyword in ['score', 'rate', 'count', 'total', '%']):
                    metrics.append(line.strip())
        return metrics[:5]  # Top 5 metrics
    
    def _extract_evidence(self, text: str) -> List[str]:
        """Extract evidence/quotes from response"""
        evidence = []
        lines = text.split('\n')
        for line in lines:
            if '"' in line or any(keyword in line.lower() for keyword in ['quote', 'said', 'mentioned']):
                evidence.append(line.strip())
        return evidence[:3]  # Top 3 evidence items
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from response"""
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'immediate', 'action']):
                recommendations.append(line.strip())
        return recommendations[:3]  # Top 3 recommendations

# Business Intelligence Question Handler
class BIQuestionHandler:
    """Handles common business intelligence questions"""
    
    def __init__(self, agent: CallAnalysisAgent):
        self.agent = agent
        
        # Predefined questions that executives commonly ask
        self.common_questions = {
            "call_quality": "How was the overall quality of today's calls?",
            "deals_at_risk": "Were there any deals at risk based on today's conversations?",
            "pipeline_health": "Show me pipeline health based on this week's calls",
            "training_needs": "Which reps need training based on recent call behavior?",
            "churn_risks": "Are there churn risks in today's inbound calls?",
            "opportunities": "Any probable new opportunities from today's calls?",
            "objections": "Any recurring objections we should address?"
        }
    
    async def handle_quality_question(self, state: CallAnalysisState) -> Dict:
        """Handle call quality questions"""
        return await self.agent.answer_question(state, self.common_questions["call_quality"])
    
    async def handle_deals_question(self, state: CallAnalysisState) -> Dict:
        """Handle deal risk questions"""
        return await self.agent.answer_question(state, self.common_questions["deals_at_risk"])
    
    async def handle_pipeline_question(self, state: CallAnalysisState) -> Dict:
        """Handle pipeline health questions"""
        return await self.agent.answer_question(state, self.common_questions["pipeline_health"])
    
    async def handle_training_question(self, state: CallAnalysisState) -> Dict:
        """Handle training needs questions"""
        return await self.agent.answer_question(state, self.common_questions["training_needs"])
    
    async def handle_churn_question(self, state: CallAnalysisState) -> Dict:
        """Handle churn risk questions"""
        return await self.agent.answer_question(state, self.common_questions["churn_risks"])
    
    async def handle_opportunities_question(self, state: CallAnalysisState) -> Dict:
        """Handle opportunity questions"""
        return await self.agent.answer_question(state, self.common_questions["opportunities"])
    
    async def handle_objections_question(self, state: CallAnalysisState) -> Dict:
        """Handle objections questions"""
        return await self.agent.answer_question(state, self.common_questions["objections"])
    
    async def handle_custom_question(self, state: CallAnalysisState, question: str) -> Dict:
        """Handle custom questions"""
        return await self.agent.answer_question(state, question)

# LangGraph Workflow Definition
def create_call_analysis_workflow(mcp_connector):
    """Create a LangGraph workflow for call analysis"""
    
    agent = CallAnalysisAgent(mcp_connector)
    handler = BIQuestionHandler(agent)
    
    # Define the workflow graph
    workflow = StateGraph(CallAnalysisState)
    
    # Define nodes
    async def start_node(state: CallAnalysisState) -> Dict:
        """Starting node - check data availability"""
        return await agent.check_data_availability(state)
    
    async def ensure_data_node(state: CallAnalysisState) -> Dict:
        """Ensure analysis data is available"""
        if not state.analysis_data_available:
            return await agent.generate_analysis(state)
        return {"status": "data_ready"}
    
    async def route_question_node(state: CallAnalysisState) -> Dict:
        """Route questions to appropriate handlers"""
        # This would be called with user input
        # For demo, we'll handle all common questions
        return {"status": "ready_for_questions"}
    
    # Add nodes to the graph
    workflow.add_node("start", start_node)
    workflow.add_node("ensure_data", ensure_data_node)
    workflow.add_node("route_question", route_question_node)
    
    # Add question handler nodes
    workflow.add_node("handle_quality", handler.handle_quality_question)
    workflow.add_node("handle_deals", handler.handle_deals_question)
    workflow.add_node("handle_pipeline", handler.handle_pipeline_question)
    workflow.add_node("handle_training", handler.handle_training_question)
    workflow.add_node("handle_churn", handler.handle_churn_question)
    workflow.add_node("handle_opportunities", handler.handle_opportunities_question)
    workflow.add_node("handle_objections", handler.handle_objections_question)
    
    # Define edges
    workflow.add_edge("start", "ensure_data")
    workflow.add_edge("ensure_data", "route_question")
    
    # Conditional edges for routing
    def route_by_question_type(state: CallAnalysisState) -> str:
        """Route to appropriate question handler"""
        # This would analyze the user's question and route accordingly
        # For demo purposes, return different handlers
        return "handle_quality"  # Default
    
    workflow.add_conditional_edges(
        "route_question",
        route_by_question_type,
        {
            "handle_quality": "handle_quality",
            "handle_deals": "handle_deals", 
            "handle_pipeline": "handle_pipeline",
            "handle_training": "handle_training",
            "handle_churn": "handle_churn",
            "handle_opportunities": "handle_opportunities",
            "handle_objections": "handle_objections"
        }
    )
    
    # All handlers end the workflow
    for handler_name in ["handle_quality", "handle_deals", "handle_pipeline", 
                        "handle_training", "handle_churn", "handle_opportunities", "handle_objections"]:
        workflow.add_edge(handler_name, END)
    
    # Set entry point
    workflow.set_entry_point("start")
    
    return workflow.compile()

# Example usage
async def demo_call_analysis():
    """Demonstrate the call analysis agent"""
    
    # Initialize MCP connector (you'll need to provide your actual connector)
    # mcp_connector = MCPHTTPComponent(base_url="http://18.191.87.212:8000")
    # await mcp_connector.connect()
    
    # For demo, we'll simulate the workflow
    print("🤖 Call Analysis Business Intelligence Agent Demo")
    print("=" * 50)
    
    # Create workflow
    # workflow = create_call_analysis_workflow(mcp_connector)
    
    # Initialize state
    state = CallAnalysisState()
    
    # Simulate running the workflow for each question type
    demo_questions = [
        ("Call Quality", "How was the overall quality of today's calls?"),
        ("Deal Risk", "Were there any deals at risk based on today's conversations?"),
        ("Pipeline Health", "Show me pipeline health based on this week's calls"),
        ("Training Needs", "Which reps need training based on recent call behavior?"),
        ("Churn Risk", "Are there churn risks in today's inbound calls?"),
        ("Opportunities", "Any probable new opportunities from today's calls?"),
        ("Objections", "Any recurring objections we should address?")
    ]
    
    for category, question in demo_questions:
        print(f"\n📊 {category} Analysis:")
        print(f"Question: {question}")
        print("Expected MCP Tool Call:")
        
        # Determine context type
        agent = CallAnalysisAgent(None)  # None for demo
        context = agent.determine_context_type(question)
        
        tool_call = {
            "tool": "ask-analysis-question",
            "arguments": {
                "question": question,
                "context_type": context
            }
        }
        
        print(f"```json")
        print(json.dumps(tool_call, indent=2))
        print(f"```")
        
        print(f"Context Type: {context}")
        print("Response Format: Executive Summary → Key Metrics → Evidence → Recommendations")
        print("-" * 40)

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_call_analysis()) 