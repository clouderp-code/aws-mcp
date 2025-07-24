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
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ..models import (
    CallAnalysisResult, AnalysisJob, S3Location, TranscriptSegment,
    CallCharacteristics, SentimentAnalysis, ConversationFlow, KeyTopics,
    ComplianceMetrics, PerformanceKPIs, CallParticipant, SentimentType
)
from ..services.transcript_analyzer import TranscriptAnalyzer
from ..services.s3_service import S3Service
from ..consts import DEFAULT_ANALYSIS_OPTIONS


def transcript_analyzer_tool(mcp: FastMCP) -> None:
    """Register the transcript analyzer tool."""
    
    @mcp.tool(description="Analyze a single call transcript from S3 and generate comprehensive analysis with KPIs")
    def analyze_transcript(
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
            
            # Perform comprehensive analysis
            analysis_result = analyzer.analyze_transcript(
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
    
    @mcp.tool(description="Analyze multiple call transcripts from an S3 folder and generate batch analysis report")
    def analyze_transcript_batch(
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
                    analysis_result = analyzer.analyze_transcript(
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