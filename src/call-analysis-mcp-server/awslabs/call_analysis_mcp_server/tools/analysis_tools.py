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

"""Analysis tools for call transcripts."""

import json
import time
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ..models import (
    CallAnalysisResult, AnalysisJob, S3Location, TranscriptSegment,
    CallCharacteristics, SentimentAnalysis, ConversationFlow, KeyTopics,
    ComplianceMetrics, PerformanceKPIs, CallParticipant, SentimentType,
    BusinessIntelligenceInsights, DealRiskIndicator, ChurnRiskIndicator,
    OpportunityIndicator, AgentTrainingNeed, PipelineHealthIndicator,
    ObjectionPattern, CallQualityIssue, RiskLevel
)
from ..services.transcript_analyzer import TranscriptAnalyzer
from ..services.s3_service import S3Service
from ..services.business_intelligence import BusinessIntelligenceAnalyzer
from ..consts import DEFAULT_ANALYSIS_OPTIONS


def transcript_analyzer_tool(mcp: FastMCP) -> None:
    """Register the transcript analyzer tool."""
    
    @mcp.tool(description="Analyze a single call transcript from S3 and generate comprehensive AI-powered analysis with KPIs")
    async def analyze_transcript(
        s3_bucket: str,
        s3_key: str,
        output_bucket: str,
        output_prefix: str = "",
        analysis_options: Optional[Dict[str, bool]] = None,
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        Analyze a call transcript from S3 and upload analysis results back to S3.
        
        Args:
            s3_bucket: S3 bucket containing the transcript file
            s3_key: S3 key path to the transcript file
            output_bucket: S3 bucket for output files
            output_prefix: Prefix for output files (optional)
            analysis_options: Dictionary of analysis options to enable/disable
            aws_region: AWS region for S3 operations
            
        Returns:
            Dictionary containing analysis results and output locations
        """
        start_time = time.time()
        
        try:
            # Initialize services
            s3_service = S3Service(region=aws_region)
            analyzer = TranscriptAnalyzer()
            
            # Use default options if not provided
            if analysis_options is None:
                analysis_options = DEFAULT_ANALYSIS_OPTIONS.copy()
            
            logger.info(f"Starting analysis of transcript: s3://{s3_bucket}/{s3_key}")
            
            # Read transcript from S3
            transcript_content = s3_service.read_transcript(s3_bucket, s3_key)
            
            # Parse transcript into segments
            transcript_segments = analyzer.parse_transcript(transcript_content)
            
            # Perform comprehensive AI-powered analysis
            analysis_result = await analyzer.analyze_transcript(
                transcript_segments=transcript_segments,
                call_id=s3_key.split('/')[-1].split('.')[0],  # Extract filename as call_id
                analysis_options=analysis_options
            )
            
            # Set processing time
            analysis_result.processing_time_seconds = time.time() - start_time
            analysis_result.transcript_source = f"s3://{s3_bucket}/{s3_key}"
            
            # Generate output file paths
            base_filename = s3_key.split('/')[-1].split('.')[0]
            if output_prefix:
                json_key = f"{output_prefix}/{base_filename}_analysis.json"
                md_key = f"{output_prefix}/{base_filename}_analysis.md"
            else:
                json_key = f"{base_filename}_analysis.json"
                md_key = f"{base_filename}_analysis.md"
            
            # Upload JSON analysis results
            json_content = analysis_result.model_dump_json(indent=2)
            json_url = s3_service.upload_analysis_json(
                content=json_content,
                bucket=output_bucket,
                key=json_key
            )
            
            # Generate and upload markdown report
            md_content = analyzer.generate_markdown_report(analysis_result)
            md_url = s3_service.upload_analysis_markdown(
                content=md_content,
                bucket=output_bucket,
                key=md_key
            )
            
            logger.info(f"Analysis completed successfully. Processing time: {analysis_result.processing_time_seconds:.2f}s")
            
            return {
                "status": "success",
                "call_id": analysis_result.call_id,
                "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
                "processing_time_seconds": analysis_result.processing_time_seconds,
                "output_files": {
                    "analysis_json": {
                        "s3_url": json_url,
                        "bucket": output_bucket,
                        "key": json_key
                    },
                    "analysis_markdown": {
                        "s3_url": md_url,
                        "bucket": output_bucket,
                        "key": md_key
                    }
                },
                "summary": {
                    "overall_sentiment": analysis_result.sentiment_analysis.overall_sentiment,
                    "customer_satisfaction_score": analysis_result.performance_kpis.customer_satisfaction_score,
                    "compliance_score": analysis_result.compliance_metrics.compliance_score,
                    "call_duration_seconds": analysis_result.characteristics.total_duration_seconds,
                    "primary_topics": analysis_result.key_topics.primary_topics[:3]  # Top 3 topics
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_seconds": time.time() - start_time
            }


def batch_analysis_tool(mcp: FastMCP) -> None:
    """Register the batch analysis tool."""
    
    @mcp.tool(description="Analyze multiple call transcripts from an S3 folder and generate AI-powered batch analysis report")
    async def analyze_transcript_batch(
        s3_bucket: str,
        s3_prefix: str,
        output_bucket: str,
        output_prefix: str = "batch_analysis",
        max_files: int = 100,
        analysis_options: Optional[Dict[str, bool]] = None,
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        Analyze multiple call transcripts from an S3 folder.
        
        Args:
            s3_bucket: S3 bucket containing transcript files
            s3_prefix: S3 prefix/folder path containing transcripts
            output_bucket: S3 bucket for output files
            output_prefix: Prefix for output files
            max_files: Maximum number of files to process
            analysis_options: Dictionary of analysis options to enable/disable
            aws_region: AWS region for S3 operations
            
        Returns:
            Dictionary containing batch analysis results
        """
        start_time = time.time()
        
        try:
            # Initialize services
            s3_service = S3Service(region=aws_region)
            analyzer = TranscriptAnalyzer()
            
            # Use default options if not provided
            if analysis_options is None:
                analysis_options = DEFAULT_ANALYSIS_OPTIONS.copy()
            
            logger.info(f"Starting batch analysis of transcripts in: s3://{s3_bucket}/{s3_prefix}")
            
            # List transcript files in S3
            transcript_files = s3_service.list_transcript_files(s3_bucket, s3_prefix, max_files)
            
            if not transcript_files:
                return {
                    "status": "error",
                    "error_message": "No transcript files found in the specified S3 location"
                }
            
            # Process each transcript
            results = []
            successful_analyses = 0
            failed_analyses = 0
            
            for file_key in transcript_files:
                try:
                    logger.info(f"Processing file: {file_key}")
                    
                    # Read and analyze transcript
                    transcript_content = s3_service.read_transcript(s3_bucket, file_key)
                    transcript_segments = analyzer.parse_transcript(transcript_content)
                    
                    call_id = file_key.split('/')[-1].split('.')[0]
                    analysis_result = await analyzer.analyze_transcript(
                        transcript_segments=transcript_segments,
                        call_id=call_id,
                        analysis_options=analysis_options
                    )
                    
                    # Store individual result
                    individual_output_key = f"{output_prefix}/individual/{call_id}_analysis.json"
                    json_content = analysis_result.model_dump_json(indent=2)
                    json_url = s3_service.upload_analysis_json(
                        content=json_content,
                        bucket=output_bucket,
                        key=individual_output_key
                    )
                    
                    results.append({
                        "call_id": call_id,
                        "source_file": file_key,
                        "status": "success",
                        "analysis_url": json_url,
                        "summary": {
                            "sentiment": analysis_result.sentiment_analysis.overall_sentiment,
                            "satisfaction": analysis_result.performance_kpis.customer_satisfaction_score,
                            "compliance": analysis_result.compliance_metrics.compliance_score,
                            "duration": analysis_result.characteristics.total_duration_seconds
                        }
                    })
                    successful_analyses += 1
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_key}: {str(e)}")
                    results.append({
                        "call_id": file_key.split('/')[-1].split('.')[0],
                        "source_file": file_key,
                        "status": "error",
                        "error_message": str(e)
                    })
                    failed_analyses += 1
            
            # Generate batch summary report
            batch_summary = analyzer.generate_batch_summary(
                [r for r in results if r["status"] == "success"]
            )
            
            # Upload batch summary
            batch_summary_key = f"{output_prefix}/batch_summary.json"
            batch_summary_url = s3_service.upload_analysis_json(
                content=json.dumps(batch_summary, indent=2),
                bucket=output_bucket,
                key=batch_summary_key
            )
            
            # Generate batch report markdown
            batch_report_md = analyzer.generate_batch_report_markdown(batch_summary, results)
            batch_report_key = f"{output_prefix}/batch_report.md"
            batch_report_url = s3_service.upload_analysis_markdown(
                content=batch_report_md,
                bucket=output_bucket,
                key=batch_report_key
            )
            
            total_time = time.time() - start_time
            logger.info(f"Batch analysis completed. Processed {len(transcript_files)} files in {total_time:.2f}s")
            
            return {
                "status": "success",
                "batch_id": f"batch_{int(start_time)}",
                "processing_time_seconds": total_time,
                "files_processed": len(transcript_files),
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "output_files": {
                    "batch_summary": {
                        "s3_url": batch_summary_url,
                        "bucket": output_bucket,
                        "key": batch_summary_key
                    },
                    "batch_report": {
                        "s3_url": batch_report_url,
                        "bucket": output_bucket,
                        "key": batch_report_key
                    }
                },
                "individual_results": results[:10],  # Return first 10 for brevity
                "batch_metrics": batch_summary
            }
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_seconds": time.time() - start_time
            }


def business_intelligence_tool(mcp: FastMCP) -> None:
    """Register the business intelligence analysis tool."""
    
    @mcp.tool(description="Generate AI-powered business intelligence insights from call analysis results to answer management queries")
    async def generate_business_intelligence(
        analysis_s3_urls: List[str],
        output_bucket: str,
        time_period: str = "Today",
        output_key: str = "business_intelligence.json",
        aws_region: str = "us-east-1"
    ) -> Dict:
        """
        Generate business intelligence insights from multiple call analysis results.
        
        Args:
            analysis_s3_urls: List of S3 URLs containing analysis JSON files
            output_bucket: S3 bucket for output business intelligence file
            time_period: Description of time period analyzed (e.g., "Today", "This week")
            output_key: S3 key for output file
            aws_region: AWS region for S3 operations
            
        Returns:
            Dictionary containing business intelligence insights
        """
        start_time = time.time()
        
        try:
            # Initialize services
            s3_service = S3Service(region=aws_region)
            bi_analyzer = BusinessIntelligenceAnalyzer()
            
            logger.info(f"Starting business intelligence analysis for {len(analysis_s3_urls)} calls")
            
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
            
            # Generate AI-powered business intelligence insights
            bi_insights = await bi_analyzer.generate_insights(
                analysis_results=analysis_results,
                time_period=time_period
            )
            
            # Upload business intelligence results
            bi_content = bi_insights.model_dump_json(indent=2)
            bi_url = s3_service.upload_analysis_json(
                content=bi_content,
                bucket=output_bucket,
                key=output_key
            )
            
            total_time = time.time() - start_time
            logger.info(f"Business intelligence analysis completed in {total_time:.2f}s")
            
            return {
                "status": "success",
                "analysis_period": time_period,
                "calls_analyzed": len(analysis_results),
                "processing_time_seconds": total_time,
                "output_file": {
                    "s3_url": bi_url,
                    "bucket": output_bucket,
                    "key": output_key
                },
                "key_insights": {
                    "overall_quality_score": bi_insights.overall_quality_score,
                    "calls_with_issues": bi_insights.calls_with_issues,
                    "deals_at_risk": len(bi_insights.deals_at_risk),
                    "churn_risks": len(bi_insights.churn_risks),
                    "new_opportunities": len(bi_insights.new_opportunities),
                    "training_needs": len(bi_insights.agent_training_needs)
                },
                "top_priorities": bi_insights.top_priorities
            }
            
        except Exception as e:
            logger.error(f"Error in business intelligence analysis: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_seconds": time.time() - start_time
            }


def local_scripts_analysis_tool(mcp: FastMCP) -> None:
    """Register the local scripts analysis tool."""
    
    @mcp.tool(description="Analyze local script files from transcripts folder and generate AI-enhanced business intelligence report with evidence trails")
    async def analyze_local_scripts(
        scripts_folder: str = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts",
        script_pattern: str = "script*.json",
        output_file: str = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/local_analysis_report.json",
        time_period: str = "Current Script Collection",
        max_scripts: int = 50,
        analysis_options: Optional[Dict[str, bool]] = None
    ) -> Dict:
        """
        Analyze local script files and generate enhanced business intelligence report.
        
        Args:
            scripts_folder: Path to folder containing script files
            script_pattern: File pattern to match (e.g., "script*.json")
            output_file: Path for output analysis report
            time_period: Description of time period for the analysis
            max_scripts: Maximum number of scripts to process
            analysis_options: Dictionary of analysis options to enable/disable
            
        Returns:
            Dictionary containing analysis results and business intelligence insights
        """
        start_time = time.time()
        
        try:
            # Initialize services
            analyzer = TranscriptAnalyzer()
            bi_analyzer = BusinessIntelligenceAnalyzer()
            
            # Use default options if not provided
            if analysis_options is None:
                analysis_options = DEFAULT_ANALYSIS_OPTIONS.copy()
                analysis_options["evidence_collection"] = True  # Enable evidence collection
            
            logger.info(f"Starting local scripts analysis in: {scripts_folder}")
            
            # Find script files
            script_pattern_full = os.path.join(scripts_folder, script_pattern)
            script_files = sorted(glob.glob(script_pattern_full))[:max_scripts]
            
            if not script_files:
                return {
                    "status": "error",
                    "error_message": f"No script files found matching pattern: {script_pattern_full}"
                }
            
            logger.info(f"Found {len(script_files)} script files to process")
            
            # Process each script
            analysis_results = []
            successful_analyses = 0
            failed_analyses = 0
            
            for script_file in script_files:
                try:
                    logger.info(f"Processing script: {script_file}")
                    
                    # Read script file
                    with open(script_file, 'r', encoding='utf-8') as f:
                        script_data = json.load(f)
                    
                    # Convert script to transcript segments
                    transcript_segments = _convert_script_to_segments(script_data)
                    
                    # Get call ID
                    call_id = script_data.get('call_id', os.path.basename(script_file).replace('.json', ''))
                    
                    # Perform comprehensive AI-powered analysis
                    analysis_result = await analyzer.analyze_transcript(
                        transcript_segments=transcript_segments,
                        call_id=call_id,
                        analysis_options=analysis_options
                    )
                    
                    # Set metadata
                    analysis_result.transcript_source = script_file
                    analysis_result.processing_time_seconds = time.time() - start_time
                    
                    # Convert to dictionary for BI analysis
                    analysis_dict = analysis_result.model_dump()
                    analysis_results.append(analysis_dict)
                    
                    successful_analyses += 1
                    logger.info(f"Successfully analyzed {call_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing script {script_file}: {str(e)}")
                    failed_analyses += 1
                    continue
            
            if not analysis_results:
                return {
                    "status": "error",
                    "error_message": "No scripts could be successfully analyzed"
                }
            
            # Generate AI-powered business intelligence insights with evidence trails
            logger.info("Generating AI-powered business intelligence insights...")
            bi_insights = await bi_analyzer.generate_insights(
                analysis_results=analysis_results,
                time_period=time_period
            )
            
            # Save enhanced BI report to file
            bi_content = bi_insights.model_dump_json(indent=2)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(bi_content)
            
            total_time = time.time() - start_time
            logger.info(f"Local scripts analysis completed in {total_time:.2f}s")
            
            return {
                "status": "success",
                "analysis_period": time_period,
                "scripts_processed": len(script_files),
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "processing_time_seconds": total_time,
                "output_file": output_file,
                "key_insights": {
                    "overall_quality_score": bi_insights.overall_quality_score,
                    "calls_with_issues": bi_insights.calls_with_issues,
                    "deals_at_risk": len(bi_insights.deals_at_risk),
                    "churn_risks": len(bi_insights.churn_risks),
                    "new_opportunities": len(bi_insights.new_opportunities),
                    "training_needs": len(bi_insights.agent_training_needs),
                    "total_evidence_items": bi_insights.evidence_summary.get("total_evidence_items", 0),
                    "analysis_confidence": bi_insights.analysis_confidence
                },
                "top_priorities": bi_insights.top_priorities,
                "evidence_summary": bi_insights.evidence_summary,
                "review_recommendations": bi_insights.review_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in local scripts analysis: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_seconds": time.time() - start_time
            }


def _convert_script_to_segments(script_data: Dict) -> List[TranscriptSegment]:
        """Convert script data to transcript segments."""
        segments = []
        transcript = script_data.get('transcript', [])
        
        # Default values for missing data
        default_duration = 5.0  # 5 seconds per segment
        current_timestamp = 0.0
        
        for i, entry in enumerate(transcript):
            speaker = entry.get('speaker', 'unknown').lower()
            text = entry.get('text', '')
            
            # Parse timestamp if available
            timestamp_str = entry.get('timestamp', '')
            if timestamp_str and '–' in timestamp_str:
                # Extract start time from timestamp like "00:30 – 01:15"
                start_time_str = timestamp_str.split('–')[0].strip()
                try:
                    # Convert MM:SS to seconds
                    parts = start_time_str.split(':')
                    if len(parts) >= 2:
                        minutes = int(parts[0])
                        seconds = int(parts[1])
                        current_timestamp = minutes * 60 + seconds
                except (ValueError, IndexError):
                    pass
            
            # Estimate duration based on text length
            word_count = len(text.split())
            estimated_duration = max(2.0, word_count * 0.5)  # ~2 words per second
            
            # Map speaker to CallParticipant
            if speaker in ['agent']:
                call_participant = CallParticipant.AGENT
            elif speaker in ['customer']:
                call_participant = CallParticipant.CUSTOMER
            else:
                call_participant = CallParticipant.SYSTEM
            
            segment = TranscriptSegment(
                timestamp=current_timestamp,
                speaker=call_participant,
                text=text,
                duration=estimated_duration,
                confidence=0.95  # Assume high confidence for script data
            )
            
            segments.append(segment)
            current_timestamp += estimated_duration
        
        return segments 