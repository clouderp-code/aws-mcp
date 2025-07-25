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
from typing import Dict, List, Optional, Any

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
            
            # Prepare call batches for efficient processing
            call_batches = []
            failed_reads = []
            
            logger.info(f"📁 Reading {len(transcript_files)} transcript files...")
            for file_key in transcript_files:
                try:
                    # Read and parse transcript
                    transcript_content = s3_service.read_transcript(s3_bucket, file_key)
                    transcript_segments = analyzer.parse_transcript(transcript_content)
                    call_id = file_key.split('/')[-1].split('.')[0]
                    
                    call_batches.append({
                        "call_id": call_id,
                        "segments": transcript_segments,
                        "s3_key": file_key,
                        "transcript_source": f"s3://{s3_bucket}/{file_key}"
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading file {file_key}: {str(e)}")
                    failed_reads.append({
                        "call_id": file_key.split('/')[-1].split('.')[0],
                        "source_file": file_key,
                        "status": "read_error",
                        "error_message": str(e)
                    })
            
            if not call_batches:
                return {
                    "status": "error",
                    "error_message": "No transcripts could be read successfully",
                    "failed_reads": failed_reads
                }
            
            # Perform batch analysis for improved performance  
            logger.info(f"🚀 Processing {len(call_batches)} transcripts using batch analysis...")
            analysis_results = await analyzer.batch_analyze_transcripts(
                call_batches=call_batches,
                analysis_options=analysis_options,
                batch_size=10  # Process 10 at a time
            )
            
            # Upload individual results and prepare summary
            results = []
            successful_analyses = 0
            failed_analyses = len(failed_reads)
            
            logger.info(f"📤 Uploading {len(analysis_results)} analysis results...")
            for analysis_result in analysis_results:
                try:
                    # Store individual result  
                    individual_output_key = f"{output_prefix}/individual/{analysis_result.call_id}_analysis.json"
                    json_content = analysis_result.model_dump_json(indent=2)
                    json_url = s3_service.upload_analysis_json(
                        content=json_content,
                        bucket=output_bucket,
                        key=individual_output_key
                    )
                    
                    # Find corresponding source file
                    source_file = next((b["s3_key"] for b in call_batches if b["call_id"] == analysis_result.call_id), "unknown")
                    
                    results.append({
                        "call_id": analysis_result.call_id,
                        "source_file": source_file,
                        "status": "success",
                        "analysis_url": json_url,
                        "summary": {
                            "sentiment": analysis_result.sentiment_analysis.overall_sentiment if analysis_result.sentiment_analysis else "unknown",
                            "satisfaction": analysis_result.performance_kpis.customer_satisfaction_score if analysis_result.performance_kpis else 0,
                            "compliance": analysis_result.compliance_metrics.compliance_score if analysis_result.compliance_metrics else 0,
                            "duration": analysis_result.characteristics.total_duration_seconds
                        }
                    })
                    successful_analyses += 1
                    
                except Exception as e:
                    logger.error(f"Error uploading results for {analysis_result.call_id}: {str(e)}")
                    results.append({
                        "call_id": analysis_result.call_id,
                        "source_file": "unknown",
                        "status": "upload_error",
                        "error_message": str(e)
                    })
                    failed_analyses += 1
            
            # Add read failures to results
            results.extend(failed_reads)
            
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

def qa_analysis_tool(mcp: FastMCP) -> None:
    """Register the Q&A analysis tool for business intelligence insights."""
    
    @mcp.tool(description="Ask natural language questions about call analysis and business intelligence reports to get specific insights")
    async def ask_analysis_question(
        question: str,
        report_file_path: str = "/opt/mycode/aws-mcp/src/call-analysis-mcp-server/transcripts/ai_enhanced_analysis_all_scripts_report.json",
        context_type: str = "auto"
    ) -> Dict:
        """
        Ask natural language questions about call analysis and get intelligent answers.
        
        Args:
            question: Natural language question about the call analysis data
            report_file_path: Path to the business intelligence report JSON file
            context_type: Type of context to focus on (auto, quality, deals, churn, opportunities, training, pipeline)
            
        Returns:
            Dictionary containing the answer with supporting data and insights
        """
        start_time = time.time()
        
        try:
            # Load the business intelligence report
            if not os.path.exists(report_file_path):
                return {
                    "status": "error",
                    "error_message": f"Report file not found: {report_file_path}",
                    "suggestion": "Run analyze_local_scripts first to generate the report"
                }
            
            with open(report_file_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            logger.info(f"Loaded BI report with {report_data.get('total_calls_analyzed', 0)} calls")
            
            # Analyze the question to determine intent and context
            question_analysis = _analyze_question_intent(question.lower())
            
            # Generate intelligent response based on question type
            if context_type == "auto":
                context_type = question_analysis["primary_context"]
            
            response = _generate_intelligent_response(question, question_analysis, report_data, context_type)
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "question": question,
                "answer": response["answer"],
                "key_metrics": response["metrics"],
                "supporting_data": response["supporting_data"],
                "insights": response["insights"],
                "recommendations": response.get("recommendations", []),
                "context_analyzed": context_type,
                "question_type": question_analysis["question_type"],
                "report_metadata": {
                    "analysis_period": report_data.get("analysis_period", "Unknown"),
                    "total_calls": report_data.get("total_calls_analyzed", 0),
                    "analysis_timestamp": report_data.get("analysis_timestamp", "Unknown")
                },
                "processing_time_seconds": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "processing_time_seconds": time.time() - start_time
            }


def _analyze_question_intent(question: str) -> Dict[str, str]:
    """Analyze the question to determine intent and primary context."""
    
    # Question type patterns
    question_patterns = {
        "overview": ["overall", "how was", "general", "summary", "today", "this week"],
        "metrics": ["how many", "what percentage", "count", "number of", "score"],
        "comparison": ["compare", "vs", "versus", "better", "worse", "difference"],
        "drill_down": ["show me", "list", "details", "specific", "which", "who"],
        "trend": ["trend", "trending", "improving", "declining", "change"],
        "recommendation": ["what should", "recommend", "suggest", "next steps", "action"]
    }
    
    # Context patterns
    context_patterns = {
        "quality": ["quality", "performance", "score", "satisfaction"],
        "deals": ["deals", "risk", "at risk", "win", "lose", "probability"],
        "churn": ["churn", "retention", "leaving", "switch", "cancel"],
        "opportunities": ["opportunities", "upsell", "cross-sell", "expansion", "growth"],
        "training": ["training", "coach", "improve", "skills", "agents", "reps"],
        "pipeline": ["pipeline", "health", "stage", "conversion", "funnel"],
        "objections": ["objections", "concerns", "pushback", "resistance"]
    }
    
    # Determine question type
    question_type = "overview"
    for q_type, patterns in question_patterns.items():
        if any(pattern in question for pattern in patterns):
            question_type = q_type
            break
    
    # Determine primary context
    primary_context = "quality"
    context_scores = {}
    for context, patterns in context_patterns.items():
        score = sum(1 for pattern in patterns if pattern in question)
        if score > 0:
            context_scores[context] = score
    
    if context_scores:
        primary_context = max(context_scores, key=context_scores.get)
    
    return {
        "question_type": question_type,
        "primary_context": primary_context,
        "context_scores": context_scores
    }


def _generate_intelligent_response(question: str, question_analysis: Dict, report_data: Dict, context_type: str) -> Dict:
    """Generate an intelligent response based on the question and report data."""
    
    response = {
        "answer": "",
        "metrics": {},
        "supporting_data": [],
        "insights": []
    }
    
    # Extract key metrics from report
    total_calls = report_data.get("total_calls_analyzed", 0)
    quality_score = report_data.get("overall_quality_score", 0)
    quality_trend = report_data.get("quality_trend", "unknown")
    
    # Context-specific responses
    if context_type == "quality":
        response.update(_handle_quality_questions(question, question_analysis, report_data))
    elif context_type == "deals":
        response.update(_handle_deals_questions(question, question_analysis, report_data))
    elif context_type == "churn":
        response.update(_handle_churn_questions(question, question_analysis, report_data))
    elif context_type == "opportunities":
        response.update(_handle_opportunities_questions(question, question_analysis, report_data))
    elif context_type == "training":
        response.update(_handle_training_questions(question, question_analysis, report_data))
    elif context_type == "pipeline":
        response.update(_handle_pipeline_questions(question, question_analysis, report_data))
    else:
        # General overview response with evidence summary
        total_evidence_items = 0
        evidence_confidence_sum = 0
        evidence_count = 0
        
        # Collect evidence statistics from all sections
        for section in ['deals_at_risk', 'churn_risks', 'new_opportunities', 'agent_training_needs']:
            section_data = report_data.get(section, [])
            for item in section_data:
                evidence = item.get('evidence', {})
                primary_evidence = evidence.get('primary_evidence', [])
                total_evidence_items += len(primary_evidence)
                for ev in primary_evidence:
                    evidence_confidence_sum += ev.get('confidence_score', 0)
                    evidence_count += 1
        
        avg_evidence_confidence = evidence_confidence_sum / evidence_count if evidence_count > 0 else 0
        
        response["answer"] = f"""Based on the analysis of {total_calls} calls:

**Overall Quality**: {quality_score:.1f}/10 (trend: {quality_trend})
**At-Risk Deals**: {len(report_data.get('deals_at_risk', []))} identified
**Churn Risks**: {len(report_data.get('churn_risks', []))} accounts at risk
**New Opportunities**: {len(report_data.get('new_opportunities', []))} potential opportunities
**Training Needs**: {len(report_data.get('agent_training_needs', []))} areas identified

**📋 Evidence Summary**: {total_evidence_items} supporting quotes analyzed (avg confidence: {avg_evidence_confidence:.0%})

The analysis shows {"concerning patterns" if quality_score < 5 else "stable performance" if quality_score < 7 else "strong performance"} with specific areas requiring attention."""

        response["metrics"] = {
            "total_calls": total_calls,
            "quality_score": quality_score,
            "deals_at_risk_count": len(report_data.get('deals_at_risk', [])),
            "churn_risks_count": len(report_data.get('churn_risks', [])),
            "opportunities_count": len(report_data.get('new_opportunities', [])),
            "total_evidence_items": total_evidence_items,
            "evidence_confidence": avg_evidence_confidence
        }
        
        response["evidence"] = []  # Overview doesn't include specific evidence
    
    return response


def _handle_quality_questions(question: str, question_analysis: Dict, report_data: Dict) -> Dict:
    """Handle quality-related questions."""
    quality_score = report_data.get("overall_quality_score", 0)
    quality_trend = report_data.get("quality_trend", "unknown")
    calls_with_issues = report_data.get("calls_with_issues", 0)
    issues_percentage = report_data.get("calls_with_issues_percentage", 0)
    
    answer = f"""**Call Quality Analysis:**

• Overall Quality Score: **{quality_score:.1f}/10** (trend: {quality_trend})
• Calls with Issues: **{calls_with_issues}** ({issues_percentage:.1f}% of total calls)
• Quality Trend: **{quality_trend.title()}**

{"🔴 **ATTENTION NEEDED**: Quality score is below acceptable threshold (5.0)" if quality_score < 5 else "🟡 **MONITOR**: Quality score could be improved" if quality_score < 7 else "🟢 **GOOD**: Quality score is within acceptable range"}"""
    
    # Add specific quality insights
    insights = []
    if quality_score < 5:
        insights.append("Immediate intervention required - quality is critically low")
        insights.append("Consider additional training and monitoring for all agents")
    elif quality_score < 7:
        insights.append("Quality improvement initiatives should be implemented")
        insights.append("Focus on specific training areas identified in the analysis")
    
    if quality_trend == "declining":
        insights.append("Declining trend indicates systemic issues that need immediate attention")
    
    return {
        "answer": answer,
        "metrics": {
            "quality_score": quality_score,
            "quality_trend": quality_trend,
            "calls_with_issues": calls_with_issues,
            "issues_percentage": issues_percentage
        },
        "insights": insights
    }


def _handle_deals_questions(question: str, question_analysis: Dict, report_data: Dict) -> Dict:
    """Handle deal risk related questions."""
    deals_at_risk = report_data.get("deals_at_risk", [])
    total_deals = len(deals_at_risk)
    
    if total_deals == 0:
        return {
            "answer": "✅ **Good News**: No deals were identified as at-risk in the analyzed calls.",
            "metrics": {"deals_at_risk_count": 0},
            "insights": ["All deals appear to be progressing normally"],
            "evidence": []
        }
    
    # Analyze risk levels and collect evidence
    risk_levels = {}
    total_value = 0
    high_risk_deals = []
    evidence_data = []
    
    for deal in deals_at_risk:
        risk_level = deal.get("risk_level", "unknown")
        risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        account_value = deal.get("account_value", 0) or 0
        total_value += account_value
        
        # Extract evidence
        evidence = deal.get("evidence", {})
        primary_evidence = evidence.get("primary_evidence", [])
        
        deal_info = {
            "account": deal.get("account_name", "Unknown"),
            "agent": deal.get("agent_name", "Unknown"),
            "value": account_value,
            "factors": deal.get("risk_factors", []),
            "evidence": primary_evidence
        }
        
        if risk_level == "high":
            high_risk_deals.append(deal_info)
        
        # Collect all evidence for response
        for ev in primary_evidence:
            evidence_data.append({
                "account": deal.get("account_name", "Unknown"),
                "call_id": ev.get("call_id", "Unknown"),
                "speaker": ev.get("speaker", "unknown"),
                "timestamp": ev.get("timestamp", 0),
                "quote": ev.get("evidence_text", ""),
                "context": ev.get("context", ""),
                "confidence": ev.get("confidence_score", 0),
                "risk_level": risk_level
            })
    
    answer = f"""**Deal Risk Analysis:**

• Total At-Risk Deals: **{total_deals}**
• High Risk: **{risk_levels.get('high', 0)}** | Medium Risk: **{risk_levels.get('medium', 0)}** | Low Risk: **{risk_levels.get('low', 0)}**
• Total Value at Risk: **${total_value:,.2f}**

{"🔴 **CRITICAL**: Multiple high-risk deals require immediate attention" if risk_levels.get('high', 0) > 2 else "🟡 **MONITOR**: Some deals need attention" if total_deals > 0 else "🟢 **STABLE**: Deal pipeline looks healthy"}"""
    
    if high_risk_deals:
        answer += "\n\n**High Priority Deals:**\n"
        for deal in high_risk_deals[:3]:  # Show top 3
            answer += f"• **{deal['account']}** (Agent: {deal['agent']}) - ${deal['value']:,.0f}\n"
            answer += f"  Risk factors: {', '.join(deal['factors'][:2])}\n"
            
            # Add evidence for this deal
            if deal['evidence']:
                answer += f"  📝 Evidence:\n"
                for ev in deal['evidence'][:2]:  # Show top 2 pieces of evidence
                    quote = ev.get('evidence_text', '')[:80] + "..." if len(ev.get('evidence_text', '')) > 80 else ev.get('evidence_text', '')
                    timestamp = ev.get('timestamp', 0)
                    speaker = ev.get('speaker', 'unknown').title()
                    confidence = ev.get('confidence_score', 0)
                    answer += f"    • {speaker} @ {timestamp}s: \"{quote}\" (confidence: {confidence:.0%})\n"
    
    # Add comprehensive evidence section
    if evidence_data:
        answer += f"\n\n**📋 Supporting Evidence ({len(evidence_data)} quotes):**\n"
        # Show top evidence by confidence and risk level
        sorted_evidence = sorted(evidence_data, key=lambda x: (x['risk_level'] == 'high', x['confidence']), reverse=True)
        for i, ev in enumerate(sorted_evidence[:5], 1):  # Show top 5
            quote = ev['quote'][:100] + "..." if len(ev['quote']) > 100 else ev['quote']
            risk_emoji = "🔴" if ev['risk_level'] == "high" else "🟡" if ev['risk_level'] == "medium" else "🟢"
            answer += f"{i}. {risk_emoji} **{ev['account']}** ({ev['call_id']}) - {ev['speaker'].title()} @ {ev['timestamp']}s\n"
            answer += f"   \"{quote}\" (confidence: {ev['confidence']:.0%})\n"
            if ev['context']:
                answer += f"   💡 {ev['context']}\n"
            answer += "\n"
    
    insights = []
    if risk_levels.get('high', 0) > 0:
        insights.append(f"{risk_levels['high']} deals need immediate intervention")
    if total_value > 50000:
        insights.append(f"High financial impact - ${total_value:,.0f} total value at risk")
    if evidence_data:
        avg_confidence = sum(ev['confidence'] for ev in evidence_data) / len(evidence_data)
        insights.append(f"Evidence confidence: {avg_confidence:.0%} (based on {len(evidence_data)} quotes)")
    
    return {
        "answer": answer,
        "metrics": {
            "deals_at_risk_count": total_deals,
            "high_risk_count": risk_levels.get('high', 0),
            "total_value_at_risk": total_value,
            "evidence_items": len(evidence_data)
        },
        "supporting_data": high_risk_deals[:5],
        "insights": insights,
        "evidence": evidence_data[:10]  # Return top 10 evidence items
    }


def _handle_churn_questions(question: str, question_analysis: Dict, report_data: Dict) -> Dict:
    """Handle churn risk related questions."""
    churn_risks = report_data.get("churn_risks", [])
    total_churn_risks = len(churn_risks)
    
    if total_churn_risks == 0:
        return {
            "answer": "✅ **Good News**: No significant churn risks were identified in the analyzed calls.",
            "metrics": {"churn_risks_count": 0},
            "insights": ["Customer retention appears stable"],
            "evidence": []
        }
    
    # Analyze churn probabilities and urgency, collect evidence
    high_prob_churn = []
    urgent_interventions = []
    total_value_at_risk = 0
    evidence_data = []
    
    for churn in churn_risks:
        churn_prob = churn.get("churn_probability", 0)
        urgency = churn.get("intervention_urgency", "medium")
        account_value = churn.get("account_value_at_risk", 0) or 0
        total_value_at_risk += account_value
        
        # Extract evidence
        evidence = churn.get("evidence", {})
        primary_evidence = evidence.get("primary_evidence", [])
        
        churn_info = {
            "account": churn.get("account_name", "Unknown"),
            "probability": churn_prob,
            "signals": churn.get("risk_signals", []),
            "value": account_value,
            "evidence": primary_evidence
        }
        
        if churn_prob > 0.7:  # High probability
            high_prob_churn.append(churn_info)
        
        if urgency in ["high", "critical"]:
            urgent_interventions.append({
                "account": churn.get("account_name", "Unknown"),
                "urgency": urgency,
                "actions": churn.get("recommended_actions", []),
                "evidence": primary_evidence
            })
        
        # Collect all evidence for response
        for ev in primary_evidence:
            evidence_data.append({
                "account": churn.get("account_name", "Unknown"),
                "call_id": ev.get("call_id", "Unknown"),
                "speaker": ev.get("speaker", "unknown"),
                "timestamp": ev.get("timestamp", 0),
                "quote": ev.get("evidence_text", ""),
                "context": ev.get("context", ""),
                "confidence": ev.get("confidence_score", 0),
                "churn_probability": churn_prob,
                "urgency": urgency
            })
    
    answer = f"""**Churn Risk Analysis:**

• Total Accounts at Risk: **{total_churn_risks}**
• High Probability Churn: **{len(high_prob_churn)}**
• Urgent Interventions Needed: **{len(urgent_interventions)}**
• Total Annual Value at Risk: **${total_value_at_risk:,.2f}**

{"🔴 **CRITICAL**: Multiple accounts likely to churn - immediate action required" if len(high_prob_churn) > 2 else "🟡 **MONITOR**: Some retention risks identified" if total_churn_risks > 0 else "🟢 **STABLE**: Low churn risk"}"""
    
    if urgent_interventions:
        answer += "\n\n**Immediate Action Required:**\n"
        for intervention in urgent_interventions[:3]:
            answer += f"• **{intervention['account']}** - {intervention['actions'][0] if intervention['actions'] else 'Contact immediately'}\n"
            
            # Add evidence for urgent interventions
            if intervention['evidence']:
                answer += f"  📝 Evidence:\n"
                for ev in intervention['evidence'][:2]:  # Show top 2 pieces of evidence
                    quote = ev.get('evidence_text', '')[:80] + "..." if len(ev.get('evidence_text', '')) > 80 else ev.get('evidence_text', '')
                    timestamp = ev.get('timestamp', 0)
                    speaker = ev.get('speaker', 'unknown').title()
                    confidence = ev.get('confidence_score', 0)
                    answer += f"    • {speaker} @ {timestamp}s: \"{quote}\" (confidence: {confidence:.0%})\n"
    
    # Add comprehensive evidence section
    if evidence_data:
        answer += f"\n\n**📋 Supporting Evidence ({len(evidence_data)} quotes):**\n"
        # Show top evidence by urgency and churn probability
        sorted_evidence = sorted(evidence_data, key=lambda x: (x['urgency'] == 'critical', x['urgency'] == 'high', x['churn_probability'], x['confidence']), reverse=True)
        for i, ev in enumerate(sorted_evidence[:5], 1):  # Show top 5
            quote = ev['quote'][:100] + "..." if len(ev['quote']) > 100 else ev['quote']
            urgency_emoji = "🔴" if ev['urgency'] in ['critical', 'high'] else "🟡"
            answer += f"{i}. {urgency_emoji} **{ev['account']}** ({ev['call_id']}) - {ev['speaker'].title()} @ {ev['timestamp']}s\n"
            answer += f"   \"{quote}\" (confidence: {ev['confidence']:.0%}, churn risk: {ev['churn_probability']:.0%})\n"
            if ev['context']:
                answer += f"   💡 {ev['context']}\n"
            answer += "\n"
    
    insights = []
    if len(high_prob_churn) > 0:
        insights.append(f"{len(high_prob_churn)} accounts have >70% churn probability")
    if total_value_at_risk > 100000:
        insights.append(f"Significant revenue at risk - ${total_value_at_risk:,.0f} annually")
    if evidence_data:
        avg_confidence = sum(ev['confidence'] for ev in evidence_data) / len(evidence_data)
        insights.append(f"Evidence confidence: {avg_confidence:.0%} (based on {len(evidence_data)} customer quotes)")
    
    return {
        "answer": answer,
        "metrics": {
            "churn_risks_count": total_churn_risks,
            "high_probability_count": len(high_prob_churn),
            "urgent_interventions": len(urgent_interventions),
            "value_at_risk": total_value_at_risk,
            "evidence_items": len(evidence_data)
        },
        "supporting_data": high_prob_churn[:5],
        "insights": insights,
        "evidence": evidence_data[:10]  # Return top 10 evidence items
    }


def _handle_opportunities_questions(question: str, question_analysis: Dict, report_data: Dict) -> Dict:
    """Handle opportunity related questions."""
    opportunities = report_data.get("new_opportunities", [])
    total_opportunities = len(opportunities)
    
    if total_opportunities == 0:
        return {
            "answer": "📊 **No new opportunities were identified** in the analyzed calls. Consider reviewing call quality and agent training on opportunity identification.",
            "metrics": {"opportunities_count": 0},
            "insights": ["May indicate missed opportunities or need for better discovery techniques"],
            "evidence": []
        }
    
    # Analyze opportunities and collect evidence
    total_value = 0
    high_confidence = []
    by_type = {}
    evidence_data = []
    
    for opp in opportunities:
        value = opp.get("estimated_value", 0) or 0
        total_value += value
        confidence = opp.get("confidence_level", 0)
        opp_type = opp.get("opportunity_type", "unknown")
        
        by_type[opp_type] = by_type.get(opp_type, 0) + 1
        
        # Extract evidence
        evidence = opp.get("evidence", {})
        primary_evidence = evidence.get("primary_evidence", [])
        
        opp_info = {
            "account": opp.get("account_name", "Unknown"),
            "type": opp_type,
            "value": value,
            "confidence": confidence,
            "timeline": opp.get("timeline", "unknown"),
            "evidence": primary_evidence
        }
        
        if confidence > 0.7:
            high_confidence.append(opp_info)
        
        # Collect all evidence for response
        for ev in primary_evidence:
            evidence_data.append({
                "account": opp.get("account_name", "Unknown"),
                "call_id": ev.get("call_id", "Unknown"),
                "speaker": ev.get("speaker", "unknown"),
                "timestamp": ev.get("timestamp", 0),
                "quote": ev.get("evidence_text", ""),
                "context": ev.get("context", ""),
                "confidence": ev.get("confidence_score", 0),
                "opportunity_type": opp_type,
                "estimated_value": value,
                "opportunity_confidence": confidence
            })
    
    answer = f"""**Opportunity Analysis:**

• Total Opportunities: **{total_opportunities}**
• High Confidence (>70%): **{len(high_confidence)}**
• Estimated Total Value: **${total_value:,.2f}**

**Opportunity Types:**"""
    
    for opp_type, count in by_type.items():
        answer += f"\n• {opp_type.replace('_', ' ').title()}: **{count}**"
    
    if high_confidence:
        answer += "\n\n**High Priority Opportunities:**\n"
        for opp in sorted(high_confidence, key=lambda x: x['value'], reverse=True)[:3]:
            answer += f"• **{opp['account']}** - {opp['type'].replace('_', ' ').title()} (${opp['value']:,.0f}, {opp['confidence']:.0%} confidence)\n"
            
            # Add evidence for this opportunity
            if opp['evidence']:
                answer += f"  📝 Evidence:\n"
                for ev in opp['evidence'][:2]:  # Show top 2 pieces of evidence
                    quote = ev.get('evidence_text', '')[:80] + "..." if len(ev.get('evidence_text', '')) > 80 else ev.get('evidence_text', '')
                    timestamp = ev.get('timestamp', 0)
                    speaker = ev.get('speaker', 'unknown').title()
                    confidence = ev.get('confidence_score', 0)
                    answer += f"    • {speaker} @ {timestamp}s: \"{quote}\" (confidence: {confidence:.0%})\n"
    
    # Add comprehensive evidence section
    if evidence_data:
        answer += f"\n\n**📋 Supporting Evidence ({len(evidence_data)} quotes):**\n"
        # Show top evidence by opportunity value and confidence
        sorted_evidence = sorted(evidence_data, key=lambda x: (x['estimated_value'], x['opportunity_confidence'], x['confidence']), reverse=True)
        for i, ev in enumerate(sorted_evidence[:5], 1):  # Show top 5
            quote = ev['quote'][:100] + "..." if len(ev['quote']) > 100 else ev['quote']
            value_emoji = "💰" if ev['estimated_value'] > 5000 else "💵"
            answer += f"{i}. {value_emoji} **{ev['account']}** ({ev['call_id']}) - {ev['speaker'].title()} @ {ev['timestamp']}s\n"
            answer += f"   \"{quote}\" (confidence: {ev['confidence']:.0%})\n"
            answer += f"   💡 {ev['opportunity_type'].replace('_', ' ').title()} opportunity: ${ev['estimated_value']:,.0f} (success: {ev['opportunity_confidence']:.0%})\n"
            if ev['context']:
                answer += f"   📝 {ev['context']}\n"
            answer += "\n"
    
    insights = []
    if len(high_confidence) > 0:
        insights.append(f"{len(high_confidence)} opportunities have high success probability")
    if total_value > 50000:
        insights.append(f"Significant revenue potential - ${total_value:,.0f} total opportunity value")
    if evidence_data:
        avg_confidence = sum(ev['confidence'] for ev in evidence_data) / len(evidence_data)
        insights.append(f"Evidence confidence: {avg_confidence:.0%} (based on {len(evidence_data)} opportunity signals)")
    
    return {
        "answer": answer,
        "metrics": {
            "opportunities_count": total_opportunities,
            "high_confidence_count": len(high_confidence),
            "total_value": total_value,
            "opportunity_types": by_type,
            "evidence_items": len(evidence_data)
        },
        "supporting_data": high_confidence[:5],
        "insights": insights,
        "evidence": evidence_data[:10]  # Return top 10 evidence items
    }


def _handle_training_questions(question: str, question_analysis: Dict, report_data: Dict) -> Dict:
    """Handle training need related questions."""
    training_needs = report_data.get("agent_training_needs", [])
    total_needs = len(training_needs)
    
    if total_needs == 0:
        return {
            "answer": "✅ **Good Performance**: No specific training needs were identified in the analyzed calls.",
            "metrics": {"training_needs_count": 0},
            "insights": ["Agent performance appears to be meeting standards"],
            "evidence": []
        }
    
    # Analyze training needs and collect evidence
    by_skill = {}
    high_priority = []
    agents_needing_training = set()
    evidence_data = []
    
    for need in training_needs:
        skill = need.get("skill_area", "unknown")
        priority = need.get("priority", "medium")
        agent = need.get("agent_name", "Unknown")
        
        by_skill[skill] = by_skill.get(skill, 0) + 1
        agents_needing_training.add(agent)
        
        # Extract evidence
        evidence = need.get("evidence", {})
        primary_evidence = evidence.get("primary_evidence", [])
        
        training_info = {
            "agent": agent,
            "skill": skill,
            "urgency": need.get("urgency", "medium"),
            "specific_gaps": need.get("specific_gaps", []),
            "evidence": primary_evidence
        }
        
        if priority == "high":
            high_priority.append(training_info)
        
        # Collect all evidence for response
        for ev in primary_evidence:
            evidence_data.append({
                "agent": agent,
                "call_id": ev.get("call_id", "Unknown"),
                "speaker": ev.get("speaker", "unknown"),
                "timestamp": ev.get("timestamp", 0),
                "quote": ev.get("evidence_text", ""),
                "context": ev.get("context", ""),
                "confidence": ev.get("confidence_score", 0),
                "skill_area": skill,
                "priority": priority
            })
    
    answer = f"""**Training Needs Analysis:**

• Total Training Needs: **{total_needs}**
• Agents Requiring Training: **{len(agents_needing_training)}**
• High Priority Items: **{len(high_priority)}**

**Skills Needing Development:**"""
    
    for skill, count in sorted(by_skill.items(), key=lambda x: x[1], reverse=True):
        answer += f"\n• {skill.replace('_', ' ').title()}: **{count}** agents"
    
    if high_priority:
        answer += "\n\n**High Priority Training:**\n"
        for item in high_priority[:3]:
            answer += f"• **{item['agent']}** - {item['skill'].replace('_', ' ').title()} (urgent: {item['urgency']})\n"
            
            # Add evidence for this training need
            if item['evidence']:
                answer += f"  📝 Evidence:\n"
                for ev in item['evidence'][:2]:  # Show top 2 pieces of evidence
                    quote = ev.get('evidence_text', '')[:80] + "..." if len(ev.get('evidence_text', '')) > 80 else ev.get('evidence_text', '')
                    timestamp = ev.get('timestamp', 0)
                    speaker = ev.get('speaker', 'unknown').title()
                    confidence = ev.get('confidence_score', 0)
                    answer += f"    • {speaker} @ {timestamp}s: \"{quote}\" (confidence: {confidence:.0%})\n"
    
    # Add comprehensive evidence section
    if evidence_data:
        answer += f"\n\n**📋 Supporting Evidence ({len(evidence_data)} examples):**\n"
        # Show top evidence by priority and confidence
        sorted_evidence = sorted(evidence_data, key=lambda x: (x['priority'] == 'high', x['confidence']), reverse=True)
        for i, ev in enumerate(sorted_evidence[:5], 1):  # Show top 5
            quote = ev['quote'][:100] + "..." if len(ev['quote']) > 100 else ev['quote']
            priority_emoji = "🔴" if ev['priority'] == 'high' else "🟡"
            answer += f"{i}. {priority_emoji} **{ev['agent']}** ({ev['call_id']}) - {ev['speaker'].title()} @ {ev['timestamp']}s\n"
            answer += f"   \"{quote}\" (confidence: {ev['confidence']:.0%})\n"
            answer += f"   📚 Training area: {ev['skill_area'].replace('_', ' ').title()}\n"
            if ev['context']:
                answer += f"   💡 {ev['context']}\n"
            answer += "\n"
    
    insights = []
    if len(high_priority) > 0:
        insights.append(f"{len(high_priority)} high-priority training needs require immediate attention")
    if len(agents_needing_training) > len(training_needs) * 0.5:
        insights.append("Multiple agents need training - consider team-wide sessions")
    if evidence_data:
        avg_confidence = sum(ev['confidence'] for ev in evidence_data) / len(evidence_data)
        insights.append(f"Evidence confidence: {avg_confidence:.0%} (based on {len(evidence_data)} performance examples)")
    
    # Generate recommendations
    recommendations = []
    if "objection_handling" in by_skill:
        recommendations.append("Schedule objection handling workshop for affected agents")
    if "product_knowledge" in by_skill:
        recommendations.append("Arrange product deep-dive training sessions")
    if len(high_priority) > 2:
        recommendations.append("Prioritize individual coaching for high-priority cases")
    
    return {
        "answer": answer,
        "metrics": {
            "training_needs_count": total_needs,
            "agents_count": len(agents_needing_training),
            "high_priority_count": len(high_priority),
            "skill_gaps": by_skill,
            "evidence_items": len(evidence_data)
        },
        "supporting_data": high_priority[:5],
        "insights": insights,
        "recommendations": recommendations,
        "evidence": evidence_data[:10]  # Return top 10 evidence items
    }


def _handle_pipeline_questions(question: str, question_analysis: Dict, report_data: Dict) -> Dict:
    """Handle pipeline health related questions."""
    pipeline_health = report_data.get("pipeline_health", [])
    
    if not pipeline_health:
        return {
            "answer": "📊 **Pipeline data not available** in the current analysis report.",
            "metrics": {"pipeline_stages": 0},
            "insights": ["Pipeline health analysis may not be included in this report type"]
        }
    
    # Analyze pipeline stages
    total_stages = len(pipeline_health)
    healthy_stages = 0
    at_risk_stages = 0
    stage_summary = []
    
    for stage in pipeline_health:
        stage_name = stage.get("stage", "unknown")
        progression_prob = stage.get("stage_progression_probability", 0)
        velocity_score = stage.get("deal_velocity_score", 0)
        engagement = stage.get("engagement_level", 0)
        
        avg_health = (progression_prob + velocity_score + engagement) / 3
        
        if avg_health > 0.7:
            healthy_stages += 1
            health_status = "Healthy"
        elif avg_health > 0.4:
            health_status = "At Risk"
            at_risk_stages += 1
        else:
            health_status = "Critical"
            at_risk_stages += 1
        
        stage_summary.append({
            "stage": stage_name,
            "health_status": health_status,
            "progression_probability": progression_prob,
            "velocity_score": velocity_score,
            "engagement_level": engagement
        })
    
    answer = f"""**Pipeline Health Analysis:**

• Total Stages Analyzed: **{total_stages}**
• Healthy Stages: **{healthy_stages}**
• At-Risk Stages: **{at_risk_stages}**

**Stage-by-Stage Health:**"""
    
    for stage in stage_summary:
        health_emoji = "🟢" if stage["health_status"] == "Healthy" else "🟡" if stage["health_status"] == "At Risk" else "🔴"
        answer += f"\n{health_emoji} **{stage['stage']}**: {stage['health_status']}"
        answer += f" (Progression: {stage['progression_probability']:.1%}, Velocity: {stage['velocity_score']:.1%})"
    
    insights = []
    if at_risk_stages > healthy_stages:
        insights.append("Pipeline health is concerning - multiple stages need attention")
    if healthy_stages == total_stages:
        insights.append("Pipeline appears healthy across all stages")
    
    return {
        "answer": answer,
        "metrics": {
            "total_stages": total_stages,
            "healthy_stages": healthy_stages,
            "at_risk_stages": at_risk_stages
        },
        "supporting_data": stage_summary,
        "insights": insights
    } 