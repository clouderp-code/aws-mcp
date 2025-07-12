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

"""Test utility functions for TMF ODA Transformer."""

from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock

from loguru import logger
from mcp.server.fastmcp import Context

from ..models import TMFODAComponentType, DatabaseType, SchemaFormat


async def run_test_imports(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test that all tools can be imported successfully."""
    test_start = datetime.now()
    
    try:
        # Test imports one by one to identify specific failures
        imports_tested = []
        
        # Test server tools
        try:
            from ..tools import (
                schema_analyzer_tool,
                db_analyzer_tool,
                raw_analysis_tool,
                stripped_schema_tool,
                get_job_logs_tool,
                test_runner_tool,
                journeys_tool,
                run_jobs_tool
            )
            imports_tested.append(('Server Tools', True, 'All 8 tools imported successfully'))
        except Exception as e:
            imports_tested.append(('Server Tools', False, f'Import failed: {str(e)}'))
        
        # Test models
        try:
            from ..models import (
                TMFODAComponentType,
                DatabaseType,
                SchemaFormat,
                ComplianceLevel
            )
            imports_tested.append(('Models', True, 'All model classes imported successfully'))
        except Exception as e:
            imports_tested.append(('Models', False, f'Import failed: {str(e)}'))
        
        # Test services
        try:
            from ..services import (
                SchemaAnalysisService,
                DatabaseAnalysisService,
                JourneyService,
                ValidationService
            )
            imports_tested.append(('Services', True, 'All service classes imported successfully'))
        except Exception as e:
            imports_tested.append(('Services', False, f'Import failed: {str(e)}'))
        
        # Test managers
        try:
            from ..managers import (
                JourneyManager,
                FallbackJourneyManager
            )
            imports_tested.append(('Managers', True, 'All manager classes imported successfully'))
        except Exception as e:
            imports_tested.append(('Managers', False, f'Import failed: {str(e)}'))
        
        # Test scripts (optional)
        try:
            from ..scripts.job_executor import TransformationJobExecutor
            imports_tested.append(('Scripts', True, 'TransformationJobExecutor imported successfully'))
        except Exception as e:
            imports_tested.append(('Scripts', False, f'Import failed: {str(e)}'))
        
        # Test constants
        try:
            from ..consts import (
                TMF_ODA_COMPONENT_TYPES,
                SUPPORTED_DATABASE_TYPES,
                SUPPORTED_SCHEMA_FORMATS
            )
            imports_tested.append(('Constants', True, f'{len(TMF_ODA_COMPONENT_TYPES)} component types, {len(SUPPORTED_DATABASE_TYPES)} DB types, {len(SUPPORTED_SCHEMA_FORMATS)} schema formats'))
        except Exception as e:
            imports_tested.append(('Constants', False, f'Constants not available: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        # Check if all imports passed
        all_passed = all(result[1] for result in imports_tested)
        passed_count = sum(1 for result in imports_tested if result[1])
        
        return {
            'test_name': 'Import Verification',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'imports_tested': len(imports_tested),
                'imports_passed': passed_count,
                'results': imports_tested
            },
            'message': f'✅ All imports successful' if all_passed else f'❌ {len(imports_tested) - passed_count}/{len(imports_tested)} imports failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Import Verification',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Import test failed: {str(e)}'
        }


async def run_validation_tests(ctx: Context, include_performance: bool = False) -> List[Dict[str, Any]]:
    """Run validation tests for various tools."""
    validation_tests = []
    
    # Test schema analyzer validation
    test_result = await _test_schema_analyzer_validation(ctx, include_performance)
    validation_tests.append(test_result)
    
    # Test database analyzer validation
    test_result = await _test_db_analyzer_validation(ctx, include_performance)
    validation_tests.append(test_result)
    
    # Test raw analysis validation
    test_result = await _test_raw_analysis_validation(ctx, include_performance)
    validation_tests.append(test_result)
    
    # Test stripped schema validation
    test_result = await _test_stripped_schema_validation(ctx, include_performance)
    validation_tests.append(test_result)
    
    # Test get job logs validation
    test_result = await _test_get_job_logs_validation(ctx, include_performance)
    validation_tests.append(test_result)
    
    return validation_tests


async def _test_schema_analyzer_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test schema analyzer tool validation."""
    test_start = datetime.now()
    
    try:
        from ..tools.analysis_tools import schema_analyzer_tool
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty workspace validation
        try:
            await schema_analyzer_tool(
                ctx=mock_ctx,
                workspace_dir="",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
            validation_tests.append(('Empty workspace', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty workspace', True, 'Correctly validates empty workspace'))
        except Exception as e:
            validation_tests.append(('Empty workspace', False, f'Unexpected error: {str(e)}'))
        
        # Test invalid workspace validation
        try:
            await schema_analyzer_tool(
                ctx=mock_ctx,
                workspace_dir="/non/existent/path",
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                schema_format=None
            )
            validation_tests.append(('Invalid workspace', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Invalid workspace', True, 'Correctly validates invalid workspace'))
        except Exception as e:
            validation_tests.append(('Invalid workspace', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Schema Analyzer Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Schema Analyzer Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Schema analyzer test failed: {str(e)}'
        }


async def _test_db_analyzer_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test database analyzer tool validation."""
    test_start = datetime.now()
    
    try:
        from ..tools.analysis_tools import db_analyzer_tool
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty connection string validation
        try:
            await db_analyzer_tool(
                ctx=mock_ctx,
                connection_string="",
                database_type=DatabaseType.POSTGRESQL,
                oda_component_type=TMFODAComponentType.CUSTOMER_MANAGEMENT,
                tables_filter=None
            )
            validation_tests.append(('Empty connection string', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty connection string', True, 'Correctly validates empty connection string'))
        except Exception as e:
            validation_tests.append(('Empty connection string', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Database Analyzer Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Database Analyzer Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Database analyzer test failed: {str(e)}'
        }


async def _test_raw_analysis_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test raw analysis tool validation."""
    test_start = datetime.now()
    
    try:
        from ..tools.execution_tools import raw_analysis_tool
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty journey ID validation
        try:
            await raw_analysis_tool(
                ctx=mock_ctx,
                journey_id="",
                stage_id="raw_analysis",
                triggered_by="test",
                reason="test"
            )
            validation_tests.append(('Empty journey ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty journey ID', True, 'Correctly validates empty journey ID'))
        except Exception as e:
            validation_tests.append(('Empty journey ID', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Raw Analysis Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Raw Analysis Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Raw analysis test failed: {str(e)}'
        }


async def _test_stripped_schema_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test stripped schema tool validation."""
    test_start = datetime.now()
    
    try:
        from ..tools.execution_tools import stripped_schema_tool
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty journey ID validation
        try:
            await stripped_schema_tool(
                ctx=mock_ctx,
                journey_id="",
                stage_id="stripped_schema",
                triggered_by="test",
                reason="test"
            )
            validation_tests.append(('Empty journey ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty journey ID', True, 'Correctly validates empty journey ID'))
        except Exception as e:
            validation_tests.append(('Empty journey ID', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Stripped Schema Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Stripped Schema Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Stripped schema test failed: {str(e)}'
        }


async def _test_get_job_logs_validation(ctx: Context, include_performance: bool = False) -> Dict[str, Any]:
    """Test get job logs tool validation."""
    test_start = datetime.now()
    
    try:
        from ..tools.utility_tools import get_job_logs_tool
        
        mock_ctx = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        validation_tests = []
        
        # Test empty journey ID validation
        try:
            await get_job_logs_tool(
                ctx=mock_ctx,
                journey_id="",
                stage_name="raw_analysis",
                job_id="JOB-001-20240101120000",
                step_name="schema_parsing"
            )
            validation_tests.append(('Empty journey ID', False, 'Should have raised ValueError'))
        except ValueError:
            validation_tests.append(('Empty journey ID', True, 'Correctly validates empty journey ID'))
        except Exception as e:
            validation_tests.append(('Empty journey ID', False, f'Unexpected error: {str(e)}'))
        
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        all_passed = all(result[1] for result in validation_tests)
        passed_count = sum(1 for result in validation_tests if result[1])
        
        return {
            'test_name': 'Get Job Logs Validation',
            'passed': all_passed,
            'duration_seconds': test_duration if include_performance else None,
            'details': {
                'validations_tested': len(validation_tests),
                'validations_passed': passed_count,
                'results': validation_tests
            },
            'message': f'✅ All validations passed' if all_passed else f'❌ {len(validation_tests) - passed_count}/{len(validation_tests)} validations failed'
        }
        
    except Exception as e:
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()
        
        return {
            'test_name': 'Get Job Logs Validation',
            'passed': False,
            'duration_seconds': test_duration if include_performance else None,
            'details': {'error': str(e)},
            'message': f'❌ Get job logs test failed: {str(e)}'
        }


def generate_test_recommendations(test_results: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on test results."""
    recommendations = []
    
    failed_tests = [test for test in test_results if not test['passed']]
    
    if not failed_tests:
        recommendations.append("🎉 All tests passed! Your TMF ODA MCP Server is fully operational.")
        recommendations.append("💡 Consider running periodic tests to ensure continued reliability.")
    else:
        recommendations.append(f"⚠️ {len(failed_tests)} test(s) failed. Review the detailed results above.")
        
        if any('Import' in test['test_name'] for test in failed_tests):
            recommendations.append("🔧 Import failures detected. Check Python path and dependencies.")
        
        if any('Validation' in test['test_name'] for test in failed_tests):
            recommendations.append("🔍 Validation failures detected. Review tool parameter handling.")
    
    return recommendations


def generate_next_steps(status: str, test_results: List[Dict[str, Any]]) -> List[str]:
    """Generate next steps based on overall test status."""
    if status == 'success':
        return [
            "✅ All systems operational - ready for production use",
            "📝 You can now use all TMF ODA transformer tools with confidence",
            "🔄 Run this test periodically to ensure continued reliability"
        ]
    elif status == 'partial_success':
        return [
            "⚠️ Some tests failed - investigate specific issues",
            "🔧 Fix failing components before production use",
            "🧪 Re-run tests after applying fixes"
        ]
    else:
        return [
            "❌ Multiple test failures - requires immediate attention",
            "🔍 Review detailed error messages and fix critical issues",
            "🛠️ Consider reinstalling dependencies or checking configuration"
        ]


def calculate_performance_metrics(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate performance metrics from test results."""
    durations = [test.get('duration_seconds', 0) for test in test_results if test.get('duration_seconds')]
    
    if not durations:
        return {'note': 'No performance data collected'}
    
    return {
        'total_test_duration': sum(durations),
        'average_test_duration': sum(durations) / len(durations),
        'fastest_test': min(durations),
        'slowest_test': max(durations),
        'tests_with_timing': len(durations)
    } 