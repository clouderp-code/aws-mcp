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

"""Schema analysis service for TMF ODA Transformer."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from loguru import logger

from ..models import (
    TMFODAComponentType,
    SchemaFormat,
    SchemaAnalysisReport,
    SchemaAnalysisResult,
    AnalysisStatus,
    SchemaFile,
    SchemaAnalysisIssue,
    TransformationRecommendation,
    ComplianceLevel,
)
from ..consts import (
    ERROR_NO_SCHEMAS_FOUND,
    ERROR_SCHEMA_ANALYSIS_FAILED,
    DEFAULT_ANALYSIS_TIMEOUT,
)
from ..utils import discover_schema_files, analyze_schema_file


class SchemaAnalysisService:
    """Service for schema analysis operations."""

    def __init__(self):
        """Initialize the schema analysis service."""
        self.timeout = DEFAULT_ANALYSIS_TIMEOUT

    async def analyze_workspace(
        self,
        workspace_dir: str,
        oda_component_type: TMFODAComponentType,
        schema_format: Optional[SchemaFormat] = None
    ) -> SchemaAnalysisReport:
        """Analyze schema files in a workspace directory.
        
        Args:
            workspace_dir: Directory path to analyze
            oda_component_type: Target TMF ODA component type
            schema_format: Optional schema format filter
            
        Returns:
            SchemaAnalysisReport: Complete analysis report
            
        Raises:
            ValueError: If no schemas found or analysis fails
        """
        logger.info(f'Starting schema analysis for workspace: {workspace_dir}')
        
        analysis_start = datetime.now()
        
        try:
            # Discover schema files
            schema_files = await discover_schema_files(workspace_dir, schema_format)
            
            if not schema_files:
                raise ValueError(ERROR_NO_SCHEMAS_FOUND)
            
            logger.info(f'Found {len(schema_files)} schema files to analyze')
            
            # Analyze each schema file
            analysis_results = await self._analyze_schema_files(schema_files, oda_component_type)
            
            # Calculate summary statistics
            summary_stats = self._calculate_summary_statistics(analysis_results)
            
            # Determine overall analysis status
            analysis_status = self._determine_analysis_status(analysis_results, len(schema_files))
            
            # Build analysis report
            analysis_end = datetime.now()
            duration = (analysis_end - analysis_start).total_seconds()
            
            report = SchemaAnalysisReport(
                workspace_dir=workspace_dir,
                oda_component_type=oda_component_type,
                schema_format_filter=schema_format,
                total_files_found=len(schema_files),
                total_files_analyzed=len(analysis_results),
                analysis_status=analysis_status,
                analysis_timestamp=analysis_start,
                analysis_duration=duration,
                results=analysis_results,
                summary=summary_stats
            )
            
            logger.success(f'Schema analysis completed in {duration:.2f}s')
            return report
            
        except Exception as e:
            logger.error(f'Schema analysis failed: {str(e)}')
            raise ValueError(f'{ERROR_SCHEMA_ANALYSIS_FAILED}: {str(e)}')

    def _create_safe_schema_report(
        self,
        workspace_dir: str,
        oda_component_type: TMFODAComponentType,
        schema_format: Optional[SchemaFormat],
        analysis_start: datetime,
        schema_files: List[str] = None,
        analysis_results: List[SchemaAnalysisResult] = None,
        error: Optional[str] = None
    ) -> SchemaAnalysisReport:
        """Create a schema analysis report with safe defaults to prevent validation errors."""
        
        # Use safe defaults
        schema_files = schema_files or []
        analysis_results = analysis_results or []
        analysis_end = datetime.now()
        duration = (analysis_end - analysis_start).total_seconds()
        
        # Determine status based on results and error
        if error:
            analysis_status = AnalysisStatus.FAILED
        elif len(analysis_results) == len(schema_files) and len(schema_files) > 0:
            analysis_status = AnalysisStatus.SUCCESS
        elif len(analysis_results) > 0:
            analysis_status = AnalysisStatus.PARTIAL_SUCCESS
        else:
            analysis_status = AnalysisStatus.FAILED
        
        # Calculate safe summary stats
        summary_stats = self._calculate_summary_statistics(analysis_results)
        
        return SchemaAnalysisReport(
            workspace_dir=workspace_dir,
            oda_component_type=oda_component_type,
            schema_format_filter=schema_format,
            total_files_found=len(schema_files),
            total_files_analyzed=len(analysis_results),
            analysis_status=analysis_status,
            analysis_timestamp=analysis_start,
            analysis_duration=duration,
            results=analysis_results,
            summary=summary_stats
        )

    async def _analyze_schema_files(
        self, 
        schema_files: List[str], 
        oda_component_type: TMFODAComponentType
    ) -> List[SchemaAnalysisResult]:
        """Analyze multiple schema files concurrently.
        
        Args:
            schema_files: List of schema file paths
            oda_component_type: Target TMF ODA component type
            
        Returns:
            List[SchemaAnalysisResult]: Analysis results for successfully analyzed files
        """
        analysis_results = []
        
        # Process files concurrently with a reasonable limit
        semaphore = asyncio.Semaphore(5)  # Limit concurrent analyses
        
        async def analyze_single_file(file_path: str) -> Optional[SchemaAnalysisResult]:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        analyze_schema_file(file_path, oda_component_type),
                        timeout=self.timeout
                    )
                    return result
                except asyncio.TimeoutError:
                    logger.warning(f'Analysis timeout for file: {file_path}')
                    return None
                except Exception as e:
                    logger.error(f'Analysis failed for file {file_path}: {str(e)}')
                    return None
        
        # Run analyses concurrently
        tasks = [analyze_single_file(file_path) for file_path in schema_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        for result in results:
            if isinstance(result, SchemaAnalysisResult):
                analysis_results.append(result)
        
        return analysis_results

    def _calculate_summary_statistics(self, results: List[SchemaAnalysisResult]) -> Dict[str, Any]:
        """Calculate summary statistics from analysis results.
        
        Args:
            results: List of analysis results
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        if not results:
            return {
                'average_compliance_score': 0.0,
                'compliance_distribution': {},
                'total_issues': 0,
                'total_recommendations': 0,
                'average_analysis_duration': 0.0
            }
        
        # Calculate averages
        total_score = sum(result.compliance_score for result in results)
        avg_compliance_score = total_score / len(results)
        
        total_duration = sum(result.analysis_duration for result in results)
        avg_duration = total_duration / len(results)
        
        # Count compliance levels
        compliance_distribution = {}
        for result in results:
            level = result.compliance_level.value
            compliance_distribution[level] = compliance_distribution.get(level, 0) + 1
        
        # Count issues and recommendations
        total_issues = sum(len(result.issues) for result in results)
        total_recommendations = sum(len(result.recommendations) for result in results)
        
        return {
            'average_compliance_score': round(avg_compliance_score, 2),
            'compliance_distribution': compliance_distribution,
            'total_issues': total_issues,
            'total_recommendations': total_recommendations,
            'average_analysis_duration': round(avg_duration, 2)
        }

    def _determine_analysis_status(self, results: List[SchemaAnalysisResult], total_files: int) -> AnalysisStatus:
        """Determine overall analysis status.
        
        Args:
            results: List of analysis results
            total_files: Total number of files attempted
            
        Returns:
            AnalysisStatus: Overall analysis status
        """
        if not results:
            return AnalysisStatus.FAILED
        
        analyzed_count = len(results)
        
        if analyzed_count == total_files:
            return AnalysisStatus.SUCCESS
        elif analyzed_count > 0:
            return AnalysisStatus.PARTIAL_SUCCESS
        else:
            return AnalysisStatus.FAILED

    async def validate_schema_format(self, file_path: str) -> Optional[SchemaFormat]:
        """Validate and detect schema format from file.
        
        Args:
            file_path: Path to schema file
            
        Returns:
            Optional[SchemaFormat]: Detected schema format or None
        """
        # This would contain logic to detect schema format
        # For now, return a simple detection based on file extension
        from pathlib import Path
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.json']:
            return SchemaFormat.JSON_SCHEMA
        elif file_ext in ['.yaml', '.yml']:
            return SchemaFormat.YAML_SCHEMA
        elif file_ext in ['.avsc']:
            return SchemaFormat.AVRO
        elif file_ext in ['.proto']:
            return SchemaFormat.PROTOBUF
        else:
            return None

    async def get_schema_recommendations(
        self, 
        schema_file: SchemaFile,
        oda_component_type: TMFODAComponentType
    ) -> List[TransformationRecommendation]:
        """Get transformation recommendations for a schema file.
        
        Args:
            schema_file: Schema file information
            oda_component_type: Target TMF ODA component type
            
        Returns:
            List[TransformationRecommendation]: List of recommendations
        """
        recommendations = []
        
        # Basic recommendations based on TMF ODA patterns
        recommendations.extend([
            TransformationRecommendation(
                category='Data Model',
                priority='HIGH',
                title='Implement TMF Entity Base Structure',
                description='Add standard TMF entity fields (id, href, @type, @baseType)',
                impact='Improves API consistency and TMF compliance',
                effort='MINIMAL'
            ),
            TransformationRecommendation(
                category='Validation',
                priority='MEDIUM',
                title='Add TMF Standard Patterns',
                description='Implement TMF standard validation patterns for common fields',
                impact='Ensures data consistency across TMF components',
                effort='MODERATE'
            )
        ])
        
        # Add component-specific recommendations
        if oda_component_type == TMFODAComponentType.CUSTOMER_MANAGEMENT:
            recommendations.append(
                TransformationRecommendation(
                    category='Customer Data',
                    priority='HIGH',
                    title='Implement Customer Party Structure',
                    description='Align customer data with TMF Customer Management specifications',
                    impact='Enables proper customer data management',
                    effort='SIGNIFICANT'
                )
            )
        
        return recommendations

    # Internal methods that tests expect to mock
    async def _discover_schema_files(self, workspace_dir: str, schema_format: Optional[SchemaFormat] = None) -> List[str]:
        """Discover schema files (mock-able for tests)."""
        return await discover_schema_files(workspace_dir, schema_format)

    async def _analyze_schema_file(self, file_path: str, schema_format: SchemaFormat, oda_component_type: TMFODAComponentType) -> SchemaAnalysisResult:
        """Analyze a schema file (mock-able for tests)."""
        return await analyze_schema_file(file_path, oda_component_type) 