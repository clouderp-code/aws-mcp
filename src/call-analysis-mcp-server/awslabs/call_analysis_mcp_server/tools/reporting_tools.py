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

"""Reporting tools for analysis results."""

import json
from typing import Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ..services.s3_service import S3Service
from ..services.report_generator import ReportGenerator


def generate_report_tool(mcp: FastMCP) -> None:
    """Register the report generator tool."""
    
    @mcp.tool(description="Generate comprehensive analysis reports from S3 analysis results")
    def generate_analysis_report(
        analysis_s3_urls: List[str],
        output_bucket: str,
        output_key: str,
        report_type: str = "executive_summary",
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        Generate comprehensive reports from multiple analysis results.
        
        Args:
            analysis_s3_urls: List of S3 URLs containing analysis JSON files
            report_type: Type of report (executive_summary, detailed, comparison)
            output_bucket: S3 bucket for output report
            output_key: S3 key for output report
            aws_region: AWS region
            
        Returns:
            Dictionary containing report generation results
        """
        try:
            s3_service = S3Service(region=aws_region)
            report_generator = ReportGenerator()
            
            # Read all analysis results
            analysis_results = []
            for s3_url in analysis_s3_urls:
                try:
                    # Parse S3 URL
                    if s3_url.startswith("s3://"):
                        parts = s3_url[5:].split("/", 1)
                        bucket = parts[0]
                        key = parts[1]
                    else:
                        raise ValueError(f"Invalid S3 URL format: {s3_url}")
                    
                    # Read analysis result
                    content = s3_service.read_transcript(bucket, key)
                    analysis_data = json.loads(content)
                    analysis_results.append(analysis_data)
                    
                except Exception as e:
                    logger.warning(f"Could not read analysis from {s3_url}: {str(e)}")
                    continue
            
            if not analysis_results:
                return {
                    "status": "error",
                    "error_message": "No valid analysis results could be loaded"
                }
            
            # Generate report based on type
            if report_type == "executive_summary":
                report_content = report_generator.generate_executive_summary(analysis_results)
            elif report_type == "detailed":
                report_content = report_generator.generate_detailed_report(analysis_results)
            elif report_type == "comparison":
                report_content = report_generator.generate_comparison_report(analysis_results)
            else:
                return {
                    "status": "error",
                    "error_message": f"Unknown report type: {report_type}"
                }
            
            # Upload report
            if output_key.endswith(".json"):
                content_type = "application/json"
                upload_content = json.dumps(report_content, indent=2)
            else:
                content_type = "text/markdown"
                upload_content = report_content if isinstance(report_content, str) else json.dumps(report_content, indent=2)
            
            s3_url = s3_service.upload_file_content(
                content=upload_content,
                bucket=output_bucket,
                key=output_key,
                content_type=content_type
            )
            
            return {
                "status": "success",
                "report_type": report_type,
                "analysis_files_processed": len(analysis_results),
                "output_file": {
                    "s3_url": s3_url,
                    "bucket": output_bucket,
                    "key": output_key
                },
                "report_summary": {
                    "total_calls_analyzed": len(analysis_results),
                    "average_duration": sum(r.get("characteristics", {}).get("total_duration_seconds", 0) for r in analysis_results) / len(analysis_results),
                    "average_satisfaction": sum(r.get("performance_kpis", {}).get("customer_satisfaction_score", 0) for r in analysis_results) / len(analysis_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }


def create_dashboard_tool(mcp: FastMCP) -> None:
    """Register the dashboard creator tool."""
    
    @mcp.tool(description="Create interactive dashboard from analysis results")
    def create_analysis_dashboard(
        analysis_s3_urls: List[str],
        output_bucket: str,
        dashboard_title: str = "Call Analysis Dashboard",
        output_key: str = "dashboard.html",
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        Create an interactive HTML dashboard from analysis results.
        
        Args:
            analysis_s3_urls: List of S3 URLs containing analysis JSON files
            dashboard_title: Title for the dashboard
            output_bucket: S3 bucket for output dashboard
            output_key: S3 key for output dashboard
            aws_region: AWS region
            
        Returns:
            Dictionary containing dashboard creation results
        """
        try:
            s3_service = S3Service(region=aws_region)
            report_generator = ReportGenerator()
            
            # Read all analysis results
            analysis_results = []
            for s3_url in analysis_s3_urls:
                try:
                    # Parse S3 URL
                    if s3_url.startswith("s3://"):
                        parts = s3_url[5:].split("/", 1)
                        bucket = parts[0]
                        key = parts[1]
                    else:
                        raise ValueError(f"Invalid S3 URL format: {s3_url}")
                    
                    # Read analysis result
                    content = s3_service.read_transcript(bucket, key)
                    analysis_data = json.loads(content)
                    analysis_results.append(analysis_data)
                    
                except Exception as e:
                    logger.warning(f"Could not read analysis from {s3_url}: {str(e)}")
                    continue
            
            if not analysis_results:
                return {
                    "status": "error",
                    "error_message": "No valid analysis results could be loaded"
                }
            
            # Generate dashboard HTML
            dashboard_html = report_generator.generate_dashboard_html(
                analysis_results=analysis_results,
                title=dashboard_title
            )
            
            # Upload dashboard
            s3_url = s3_service.upload_file_content(
                content=dashboard_html,
                bucket=output_bucket,
                key=output_key,
                content_type="text/html"
            )
            
            # Calculate dashboard metrics
            total_calls = len(analysis_results)
            avg_satisfaction = sum(r.get("performance_kpis", {}).get("customer_satisfaction_score", 0) for r in analysis_results) / total_calls
            sentiment_distribution = {}
            for result in analysis_results:
                sentiment = result.get("sentiment_analysis", {}).get("overall_sentiment", "unknown")
                sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
            
            return {
                "status": "success",
                "dashboard_title": dashboard_title,
                "analysis_files_processed": total_calls,
                "output_file": {
                    "s3_url": s3_url,
                    "bucket": output_bucket,
                    "key": output_key,
                    "public_url": f"https://{output_bucket}.s3.{aws_region}.amazonaws.com/{output_key}"
                },
                "dashboard_metrics": {
                    "total_calls": total_calls,
                    "average_satisfaction": round(avg_satisfaction, 2),
                    "sentiment_distribution": sentiment_distribution,
                    "compliance_pass_rate": sum(1 for r in analysis_results if r.get("compliance_metrics", {}).get("compliance_score", 0) >= 7.0) / total_calls
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            } 