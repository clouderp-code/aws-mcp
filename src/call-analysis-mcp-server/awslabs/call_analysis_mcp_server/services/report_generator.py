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

"""Report generator service for creating comprehensive analysis reports."""

import json
from datetime import datetime
from typing import List, Dict, Any

from loguru import logger


class ReportGenerator:
    """Service for generating comprehensive analysis reports and dashboards."""
    
    def __init__(self):
        """Initialize the report generator."""
        logger.info("Report generator initialized")
    
    def generate_executive_summary(self, analysis_results: List[Dict]) -> Dict:
        """Generate executive summary from multiple analysis results.
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Executive summary dictionary
        """
        if not analysis_results:
            return {"error": "No analysis results provided"}
        
        total_calls = len(analysis_results)
        
        # Calculate aggregate metrics
        avg_satisfaction = sum(
            r.get("performance_kpis", {}).get("customer_satisfaction_score", 0) 
            for r in analysis_results
        ) / total_calls
        
        avg_compliance = sum(
            r.get("compliance_metrics", {}).get("compliance_score", 0) 
            for r in analysis_results
        ) / total_calls
        
        avg_duration = sum(
            r.get("characteristics", {}).get("total_duration_seconds", 0) 
            for r in analysis_results
        ) / total_calls
        
        # Count resolutions
        resolved_calls = sum(
            1 for r in analysis_results 
            if r.get("performance_kpis", {}).get("first_call_resolution", False)
        )
        
        # Sentiment distribution
        sentiment_counts = {}
        for result in analysis_results:
            sentiment = result.get("sentiment_analysis", {}).get("overall_sentiment", "unknown")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Top topics
        topic_counts = {}
        for result in analysis_results:
            topics = result.get("key_topics", {}).get("primary_topics", [])
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "report_type": "executive_summary",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_calls_analyzed": total_calls,
                "average_customer_satisfaction": round(avg_satisfaction, 2),
                "average_compliance_score": round(avg_compliance, 2),
                "average_call_duration_minutes": round(avg_duration / 60, 2),
                "first_call_resolution_rate": round(resolved_calls / total_calls * 100, 1),
                "sentiment_distribution": sentiment_counts,
                "top_topics": [{"topic": topic, "frequency": count} for topic, count in top_topics]
            },
            "insights": [
                f"Analyzed {total_calls} calls with average satisfaction of {avg_satisfaction:.1f}/10",
                f"Compliance score averaging {avg_compliance:.1f}/10 across all calls",
                f"First call resolution achieved in {resolved_calls}/{total_calls} calls ({resolved_calls/total_calls*100:.1f}%)",
                f"Most common topic: {top_topics[0][0] if top_topics else 'N/A'}"
            ]
        }
    
    def generate_detailed_report(self, analysis_results: List[Dict]) -> str:
        """Generate detailed markdown report.
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Detailed markdown report
        """
        if not analysis_results:
            return "# Error\n\nNo analysis results provided."
        
        total_calls = len(analysis_results)
        
        # Calculate metrics
        avg_satisfaction = sum(
            r.get("performance_kpis", {}).get("customer_satisfaction_score", 0) 
            for r in analysis_results
        ) / total_calls
        
        avg_compliance = sum(
            r.get("compliance_metrics", {}).get("compliance_score", 0) 
            for r in analysis_results
        ) / total_calls
        
        # Generate markdown content
        md_content = f"""# Detailed Call Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Calls Analyzed:** {total_calls}

## Executive Summary

This report provides a comprehensive analysis of {total_calls} call transcripts, examining customer satisfaction, compliance adherence, agent performance, and key conversation themes.

### Key Findings

- **Average Customer Satisfaction:** {avg_satisfaction:.1f}/10
- **Average Compliance Score:** {avg_compliance:.1f}/10
- **Calls Meeting Satisfaction Threshold (≥7.0):** {sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) >= 7.0)}
- **Calls Meeting Compliance Threshold (≥7.0):** {sum(1 for r in analysis_results if r.get('compliance_metrics', {}).get('compliance_score', 0) >= 7.0)}

## Performance Analysis

### Customer Satisfaction Distribution

| Range | Count | Percentage |
|-------|-------|------------|
| 9.0-10.0 | {sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) >= 9.0)} | {sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) >= 9.0)/total_calls*100:.1f}% |
| 8.0-8.9 | {sum(1 for r in analysis_results if 8.0 <= r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) < 9.0)} | {sum(1 for r in analysis_results if 8.0 <= r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) < 9.0)/total_calls*100:.1f}% |
| 7.0-7.9 | {sum(1 for r in analysis_results if 7.0 <= r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) < 8.0)} | {sum(1 for r in analysis_results if 7.0 <= r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) < 8.0)/total_calls*100:.1f}% |
| Below 7.0 | {sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) < 7.0)} | {sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('customer_satisfaction_score', 0) < 7.0)/total_calls*100:.1f}% |

### Agent Performance Metrics

- **Average Professionalism Score:** {sum(r.get('performance_kpis', {}).get('agent_professionalism_score', 0) for r in analysis_results) / total_calls:.1f}/10
- **Average Empathy Score:** {sum(r.get('performance_kpis', {}).get('agent_empathy_score', 0) for r in analysis_results) / total_calls:.1f}/10
- **Average Knowledge Score:** {sum(r.get('performance_kpis', {}).get('agent_knowledge_score', 0) for r in analysis_results) / total_calls:.1f}/10

## Compliance Analysis

### Overall Compliance Performance

- **Average Compliance Score:** {avg_compliance:.1f}/10
- **Calls Passing Compliance (≥7.0):** {sum(1 for r in analysis_results if r.get('compliance_metrics', {}).get('compliance_score', 0) >= 7.0)}/{total_calls}
- **Compliance Pass Rate:** {sum(1 for r in analysis_results if r.get('compliance_metrics', {}).get('compliance_score', 0) >= 7.0)/total_calls*100:.1f}%

## Recommendations

Based on the analysis of {total_calls} calls, here are the key recommendations:

1. **Customer Satisfaction:** {'Focus on improving satisfaction scores through enhanced training' if avg_satisfaction < 7.0 else 'Maintain current high satisfaction levels'}
2. **Compliance:** {'Implement additional compliance training and monitoring' if avg_compliance < 7.0 else 'Continue current compliance practices'}
3. **Agent Development:** Focus on areas with lowest scores for targeted improvement

## Individual Call Performance

| Call ID | Satisfaction | Compliance | Duration | Sentiment |
|---------|-------------|------------|----------|-----------|
"""
        
        # Add individual call data
        for i, result in enumerate(analysis_results[:20]):  # Limit to first 20 for readability
            call_id = result.get('call_id', f'Call_{i+1}')
            satisfaction = result.get('performance_kpis', {}).get('customer_satisfaction_score', 0)
            compliance = result.get('compliance_metrics', {}).get('compliance_score', 0)
            duration = result.get('characteristics', {}).get('total_duration_seconds', 0) / 60
            sentiment = result.get('sentiment_analysis', {}).get('overall_sentiment', 'unknown')
            
            md_content += f"| {call_id} | {satisfaction:.1f} | {compliance:.1f} | {duration:.1f}m | {sentiment} |\n"
        
        md_content += f"""
---
*Report generated by Call Analysis MCP Server on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return md_content
    
    def generate_comparison_report(self, analysis_results: List[Dict]) -> Dict:
        """Generate comparison report showing trends and patterns.
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Comparison report dictionary
        """
        if len(analysis_results) < 2:
            return {"error": "Need at least 2 analysis results for comparison"}
        
        # Sort by timestamp if available
        sorted_results = sorted(
            analysis_results, 
            key=lambda x: x.get('analysis_timestamp', ''),
            reverse=True
        )
        
        # Compare first half vs second half
        mid_point = len(sorted_results) // 2
        recent_calls = sorted_results[:mid_point]
        older_calls = sorted_results[mid_point:]
        
        def calculate_avg(results, metric_path):
            total = 0
            count = 0
            for r in results:
                value = r
                for key in metric_path:
                    value = value.get(key, {}) if isinstance(value, dict) else 0
                if isinstance(value, (int, float)):
                    total += value
                    count += 1
            return total / count if count > 0 else 0
        
        recent_satisfaction = calculate_avg(recent_calls, ['performance_kpis', 'customer_satisfaction_score'])
        older_satisfaction = calculate_avg(older_calls, ['performance_kpis', 'customer_satisfaction_score'])
        
        recent_compliance = calculate_avg(recent_calls, ['compliance_metrics', 'compliance_score'])
        older_compliance = calculate_avg(older_calls, ['compliance_metrics', 'compliance_score'])
        
        return {
            "report_type": "comparison",
            "generated_at": datetime.now().isoformat(),
            "comparison_periods": {
                "recent_calls": {
                    "count": len(recent_calls),
                    "avg_satisfaction": round(recent_satisfaction, 2),
                    "avg_compliance": round(recent_compliance, 2)
                },
                "older_calls": {
                    "count": len(older_calls),
                    "avg_satisfaction": round(older_satisfaction, 2),
                    "avg_compliance": round(older_compliance, 2)
                }
            },
            "trends": {
                "satisfaction_change": round(recent_satisfaction - older_satisfaction, 2),
                "compliance_change": round(recent_compliance - older_compliance, 2),
                "satisfaction_trend": "improving" if recent_satisfaction > older_satisfaction else "declining",
                "compliance_trend": "improving" if recent_compliance > older_compliance else "declining"
            }
        }
    
    def generate_dashboard_html(self, analysis_results: List[Dict], title: str = "Call Analysis Dashboard") -> str:
        """Generate interactive HTML dashboard.
        
        Args:
            analysis_results: List of analysis result dictionaries
            title: Dashboard title
            
        Returns:
            HTML dashboard content
        """
        if not analysis_results:
            return "<html><body><h1>Error: No analysis results provided</h1></body></html>"
        
        total_calls = len(analysis_results)
        
        # Calculate summary stats
        avg_satisfaction = sum(
            r.get("performance_kpis", {}).get("customer_satisfaction_score", 0) 
            for r in analysis_results
        ) / total_calls
        
        avg_compliance = sum(
            r.get("compliance_metrics", {}).get("compliance_score", 0) 
            for r in analysis_results
        ) / total_calls
        
        # Sentiment distribution
        sentiment_counts = {}
        for result in analysis_results:
            sentiment = result.get("sentiment_analysis", {}).get("overall_sentiment", "unknown")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .chart-container {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .chart-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2d3436;
        }}
        .table-container {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #74b9ff;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .sentiment-bar {{
            display: inline-block;
            height: 20px;
            margin: 2px;
            border-radius: 3px;
            color: white;
            padding: 2px 8px;
            font-size: 0.8em;
        }}
        .positive {{ background-color: #00b894; }}
        .negative {{ background-color: #e17055; }}
        .neutral {{ background-color: #636e72; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #f0f0f0;
            color: #636e72;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_calls}</div>
                <div class="stat-label">Total Calls Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{avg_satisfaction:.1f}</div>
                <div class="stat-label">Avg Customer Satisfaction</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{avg_compliance:.1f}</div>
                <div class="stat-label">Avg Compliance Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(1 for r in analysis_results if r.get('performance_kpis', {}).get('first_call_resolution', False))}</div>
                <div class="stat-label">First Call Resolutions</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Sentiment Distribution</div>
            <div>
"""
        
        # Add sentiment bars
        for sentiment, count in sentiment_counts.items():
            percentage = (count / total_calls) * 100
            html_content += f'<div class="sentiment-bar {sentiment.lower()}">{sentiment.title()}: {count} ({percentage:.1f}%)</div>'
        
        html_content += f"""
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Call Performance Summary</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Call ID</th>
                            <th>Satisfaction</th>
                            <th>Compliance</th>
                            <th>Duration (min)</th>
                            <th>Sentiment</th>
                            <th>Resolution</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Add call data rows
        for i, result in enumerate(analysis_results[:50]):  # Limit for performance
            call_id = result.get('call_id', f'Call_{i+1}')
            satisfaction = result.get('performance_kpis', {}).get('customer_satisfaction_score', 0)
            compliance = result.get('compliance_metrics', {}).get('compliance_score', 0)
            duration = result.get('characteristics', {}).get('total_duration_seconds', 0) / 60
            sentiment = result.get('sentiment_analysis', {}).get('overall_sentiment', 'unknown')
            resolution = 'Yes' if result.get('performance_kpis', {}).get('first_call_resolution', False) else 'No'
            
            html_content += f"""
                        <tr>
                            <td>{call_id}</td>
                            <td>{satisfaction:.1f}/10</td>
                            <td>{compliance:.1f}/10</td>
                            <td>{duration:.1f}</td>
                            <td><span class="sentiment-bar {sentiment.lower()}">{sentiment.title()}</span></td>
                            <td>{resolution}</td>
                        </tr>
"""
        
        html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Dashboard generated by Call Analysis MCP Server</p>
            <p>Analyzing call transcripts to improve customer experience and agent performance</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content 