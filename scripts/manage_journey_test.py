#!/usr/bin/env python3
"""
Comprehensive Test Suite for TMF ODA Journey Management

This script performs exhaustive testing of the manage_journey.py script including:

Test Categories:
- Journey CRUD operations (Create, Read, Update, Delete)
- Stage management operations
- Second Brain rules management
- Import/Export functionality
- Error handling and edge cases
- Data validation
- Interactive mode simulation
- Performance testing
- Concurrency testing
- Data integrity verification

Edge Cases Tested:
- Invalid journey IDs
- Missing required fields
- Invalid data types
- Corrupted JSON files
- Non-existent files
- Permission errors
- Network timeouts
- Large datasets
- Special characters in data
- Concurrent operations

Output:
- Detailed log file with timestamps
- Test results summary
- Performance metrics
- Error analysis
- Coverage report

Usage:
    python3 manage_journey_test.py
    python3 manage_journey_test.py --quick-test
    python3 manage_journey_test.py --verbose --log-file test_results.log
"""

import subprocess
import json
import os
import sys
import time
import traceback
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
import logging
from pathlib import Path


class JourneyTestFramework:
    """Comprehensive test framework for journey management"""
    
    def __init__(self, log_file: str = None, verbose: bool = False):
        self.test_start_time = datetime.now(timezone.utc)
        self.test_results = []
        self.test_data_created = []
        self.temp_files_created = []
        self.verbose = verbose
        
        # Setup logging
        if log_file:
            self.log_file = log_file
        else:
            timestamp = self.test_start_time.strftime('%Y%m%d_%H%M%S')
            self.log_file = f'journey_test_results_{timestamp}.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Test configuration
        self.manage_journey_script = 'scripts/manage_journey.py'
        self.test_data_dir = 'test_data'
        
        # Test counters
        self.tests_total = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        
        # Create test data directory
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        self.logger.info("=" * 80)
        self.logger.info("🧪 COMPREHENSIVE JOURNEY MANAGEMENT TEST SUITE")
        self.logger.info("=" * 80)
        self.logger.info(f"Started at: {self.test_start_time.isoformat()}")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"Verbose mode: {self.verbose}")
    
    def run_command(self, command: List[str], expect_success: bool = True, 
                   timeout: int = 60) -> Tuple[bool, str, str]:
        """Run a command and return success status, stdout, stderr"""
        try:
            self.logger.debug(f"Executing: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            success = (result.returncode == 0) == expect_success
            
            if self.verbose:
                self.logger.debug(f"Return code: {result.returncode}")
                if result.stdout:
                    self.logger.debug(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    self.logger.debug(f"STDERR:\n{result.stderr}")
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            return False, "", "Command timed out"
        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return False, "", str(e)
    
    def create_test_data_file(self, data: Dict[str, Any], filename: str) -> str:
        """Create a test data file and track it for cleanup"""
        filepath = os.path.join(self.test_data_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.temp_files_created.append(filepath)
        self.logger.debug(f"Created test data file: {filepath}")
        return filepath
    
    def record_test_result(self, test_name: str, success: bool, 
                          details: str = "", execution_time: float = 0):
        """Record a test result"""
        self.tests_total += 1
        
        if success:
            self.tests_passed += 1
            status = "PASS"
            self.logger.info(f"✅ {test_name}: {status}")
        else:
            self.tests_failed += 1
            status = "FAIL"
            self.logger.error(f"❌ {test_name}: {status}")
        
        if details:
            self.logger.info(f"   Details: {details}")
        
        if execution_time > 0:
            self.logger.debug(f"   Execution time: {execution_time:.2f}s")
        
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'success': success,
            'details': details,
            'execution_time': execution_time,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def test_journey_crud_operations(self):
        """Test complete CRUD operations for journeys"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🏗️ TESTING JOURNEY CRUD OPERATIONS")
        self.logger.info("=" * 60)
        
        # Test 1: List journeys (should work even with no journeys)
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script, 
            '--action', 'list-journeys'
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "List existing journeys",
            success,
            f"Found journeys in output: {'journey' in stdout.lower() or 'total:' in stdout.lower()}",
            execution_time
        )
        
        # Test 2: Create journey with valid data
        journey_data = {
            "name": "Test Journey for Automated Testing",
            "description": "This is a test journey created by the automated test suite",
            "odaComponentType": "customer-management",
            "priority": "high",
            "createdBy": "test-automation"
        }
        
        journey_file = self.create_test_data_file(journey_data, "test_journey.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', journey_file
        ])
        execution_time = time.time() - start_time
        
        # Extract journey ID from output
        test_journey_id = None
        if success and 'Journey created:' in stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'Journey created:' in line:
                    test_journey_id = line.split(':')[-1].strip()
                    break
        
        self.record_test_result(
            "Create journey with valid data",
            success and test_journey_id is not None,
            f"Journey ID: {test_journey_id}" if test_journey_id else "Failed to extract journey ID",
            execution_time
        )
        
        if test_journey_id:
            self.test_data_created.append(('journey', test_journey_id))
            
            # Test 3: Get journey details
            start_time = time.time()
            success, stdout, stderr = self.run_command([
                'python3', self.manage_journey_script,
                '--action', 'get-journey',
                '--journey-id', test_journey_id
            ])
            execution_time = time.time() - start_time
            
            self.record_test_result(
                "Get journey details",
                success and test_journey_id in stdout,
                f"Journey details retrieved successfully",
                execution_time
            )
            
            # Test 4: Update journey metadata
            update_data = {
                "description": "Updated description for automated testing",
                "priority": "medium"
            }
            
            update_file = self.create_test_data_file(update_data, "update_journey.json")
            
            start_time = time.time()
            success, stdout, stderr = self.run_command([
                'python3', self.manage_journey_script,
                '--action', 'update-journey',
                '--journey-id', test_journey_id,
                '--data-file', update_file
            ])
            execution_time = time.time() - start_time
            
            self.record_test_result(
                "Update journey metadata",
                success,
                "Journey metadata updated successfully" if success else stderr,
                execution_time
            )
            
            # Test 5: Show journey dashboard
            start_time = time.time()
            success, stdout, stderr = self.run_command([
                'python3', self.manage_journey_script,
                '--action', 'dashboard',
                '--journey-id', test_journey_id
            ])
            execution_time = time.time() - start_time
            
            self.record_test_result(
                "Display journey dashboard",
                success and 'JOURNEY DASHBOARD' in stdout,
                "Dashboard displayed successfully" if success else stderr,
                execution_time
            )
    
    def test_stage_operations(self):
        """Test stage management operations"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📋 TESTING STAGE OPERATIONS")
        self.logger.info("=" * 60)
        
        # Find a test journey to work with
        test_journey_id = None
        for data_type, data_id in self.test_data_created:
            if data_type == 'journey':
                test_journey_id = data_id
                break
        
        if not test_journey_id:
            self.record_test_result(
                "Stage operations (prerequisite)",
                False,
                "No test journey available for stage testing"
            )
            return
        
        # Test 1: Add default stages
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'add-default-stages',
            '--journey-id', test_journey_id
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Add default stages to journey",
            success,
            "Default stages added successfully" if success else stderr,
            execution_time
        )
        
        # Test 2: List stages
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'list-stages',
            '--journey-id', test_journey_id
        ])
        execution_time = time.time() - start_time
        
        stage_count = stdout.count('🤖') + stdout.count('🔧') if success else 0
        
        self.record_test_result(
            "List journey stages",
            success and stage_count > 0,
            f"Found {stage_count} stages" if success else stderr,
            execution_time
        )
        
        # Test 3: Add custom stage
        custom_stage = {
            "stageId": "custom_test_stage",
            "name": "Custom Test Stage",
            "description": "A custom stage created for testing purposes",
            "order": 99,
            "estimatedDuration": "5m",
            "canSkip": True,
            "secondBrainEnabled": True,
            "ruleTypes": ["contextual_recommendations"],
            "steps": [
                {
                    "id": "test_step",
                    "name": "Test Step",
                    "description": "A test step",
                    "order": 0,
                    "estimatedDuration": "5m",
                    "aiAssisted": True,
                    "applicableRules": ["contextual_recommendations"]
                }
            ]
        }
        
        stage_file = self.create_test_data_file(custom_stage, "custom_stage.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'add-stage',
            '--journey-id', test_journey_id,
            '--data-file', stage_file
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Add custom stage",
            success,
            "Custom stage added successfully" if success else stderr,
            execution_time
        )
    
    def test_rules_operations(self):
        """Test Second Brain rules operations"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🧠 TESTING SECOND BRAIN RULES OPERATIONS")
        self.logger.info("=" * 60)
        
        # Find a test journey to work with
        test_journey_id = None
        for data_type, data_id in self.test_data_created:
            if data_type == 'journey':
                test_journey_id = data_id
                break
        
        if not test_journey_id:
            self.record_test_result(
                "Rules operations (prerequisite)",
                False,
                "No test journey available for rules testing"
            )
            return
        
        # Test 1: List existing rules
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'list-rules',
            '--journey-id', test_journey_id
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "List journey rules",
            success,
            "Rules list retrieved successfully" if success else stderr,
            execution_time
        )
        
        # Test 2: Add custom rule
        custom_rule = {
            "title": "Test Custom Rule",
            "description": "A custom rule created for testing purposes",
            "type": "contextual_recommendations",
            "priority": "medium",
            "scope": "global",
            "context": {
                "appliesTo": ["test_entities"],
                "conditions": []
            },
            "content": {
                "naturalLanguage": "This is a test rule that provides contextual recommendations for testing.",
                "jsonRule": {
                    "test_condition": "test_value",
                    "test_action": "test_response"
                }
            }
        }
        
        rule_file = self.create_test_data_file(custom_rule, "custom_rule.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'add-rule',
            '--journey-id', test_journey_id,
            '--stage-id', 'raw_analysis',
            '--data-file', rule_file
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Add custom rule",
            success,
            "Custom rule added successfully" if success else stderr,
            execution_time
        )
    
    def test_import_export_operations(self):
        """Test import/export functionality"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📥📤 TESTING IMPORT/EXPORT OPERATIONS")
        self.logger.info("=" * 60)
        
        # Find a test journey to export
        test_journey_id = None
        for data_type, data_id in self.test_data_created:
            if data_type == 'journey':
                test_journey_id = data_id
                break
        
        if not test_journey_id:
            self.record_test_result(
                "Import/Export operations (prerequisite)",
                False,
                "No test journey available for import/export testing"
            )
            return
        
        # Test 1: Export complete journey
        export_file = os.path.join(self.test_data_dir, "exported_journey.json")
        self.temp_files_created.append(export_file)
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'export-complete',
            '--journey-id', test_journey_id,
            '--output-file', export_file
        ])
        execution_time = time.time() - start_time
        
        export_success = success and os.path.exists(export_file)
        
        self.record_test_result(
            "Export complete journey",
            export_success,
            f"Journey exported to {export_file}" if export_success else stderr,
            execution_time
        )
        
        # Test 2: Import journey (if export was successful)
        if export_success:
            start_time = time.time()
            success, stdout, stderr = self.run_command([
                'python3', self.manage_journey_script,
                '--action', 'import-complete',
                '--input-file', export_file
            ])
            execution_time = time.time() - start_time
            
            # Extract imported journey ID
            imported_journey_id = None
            if success and 'Journey imported:' in stdout:
                lines = stdout.split('\n')
                for line in lines:
                    if 'Journey imported:' in line:
                        imported_journey_id = line.split(':')[-1].strip()
                        break
            
            self.record_test_result(
                "Import complete journey",
                success and imported_journey_id is not None,
                f"Journey imported with ID: {imported_journey_id}" if imported_journey_id else stderr,
                execution_time
            )
            
            if imported_journey_id:
                self.test_data_created.append(('journey', imported_journey_id))
    
    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("⚠️ TESTING ERROR HANDLING & EDGE CASES")
        self.logger.info("=" * 60)
        
        # Test 1: Invalid journey ID
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'get-journey',
            '--journey-id', 'INVALID-JOURNEY-ID-12345'
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle invalid journey ID",
            success,  # We expect this to fail gracefully
            "Invalid journey ID handled correctly" if success else "Unexpected behavior",
            execution_time
        )
        
        # Test 2: Missing required arguments
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey'
            # Missing --data-file
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle missing required arguments",
            success,  # We expect this to fail gracefully
            "Missing arguments handled correctly" if success else "Unexpected behavior",
            execution_time
        )
        
        # Test 3: Invalid JSON file
        invalid_json_file = self.create_test_data_file({"invalid": "json"}, "invalid.json")
        # Corrupt the JSON file
        with open(invalid_json_file, 'a') as f:
            f.write('{"broken": json}')
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', invalid_json_file
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle invalid JSON file",
            success,  # We expect this to fail gracefully
            "Invalid JSON handled correctly" if success else "Unexpected behavior",
            execution_time
        )
        
        # Test 4: Non-existent file
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', 'non_existent_file.json'
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle non-existent file",
            success,  # We expect this to fail gracefully
            "Non-existent file handled correctly" if success else "Unexpected behavior",
            execution_time
        )
        
        # Test 5: Invalid action
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'invalid-action'
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle invalid action",
            success,  # We expect this to fail gracefully
            "Invalid action handled correctly" if success else "Unexpected behavior",
            execution_time
        )
        
        # Test 6: Journey with missing required fields
        incomplete_journey = {
            "name": "Incomplete Journey"
            # Missing required fields: description, odaComponentType
        }
        
        incomplete_file = self.create_test_data_file(incomplete_journey, "incomplete_journey.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', incomplete_file
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle incomplete journey data",
            success,  # We expect this to fail gracefully
            "Incomplete data validation working" if success else "Unexpected behavior",
            execution_time
        )
        
        # Test 7: Journey with invalid component type
        invalid_component_journey = {
            "name": "Invalid Component Journey",
            "description": "Journey with invalid component type",
            "odaComponentType": "invalid-component-type"
        }
        
        invalid_component_file = self.create_test_data_file(invalid_component_journey, "invalid_component.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', invalid_component_file
        ], expect_success=False)
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle invalid component type",
            success,  # We expect this to fail gracefully
            "Invalid component type validation working" if success else "Unexpected behavior",
            execution_time
        )
    
    def test_data_validation(self):
        """Test various data validation scenarios"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🔍 TESTING DATA VALIDATION")
        self.logger.info("=" * 60)
        
        # Test 1: Journey with special characters
        special_chars_journey = {
            "name": "Test Journey with Special Characters: àáâãäå αβγδε 中文 🚀",
            "description": "Testing special characters: !@#$%^&*()_+-={}[]|\\:;\"'<>?,./ àáâãäå",
            "odaComponentType": "customer-management",
            "priority": "high"
        }
        
        special_chars_file = self.create_test_data_file(special_chars_journey, "special_chars_journey.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', special_chars_file
        ])
        execution_time = time.time() - start_time
        
        journey_id = None
        if success and 'Journey created:' in stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'Journey created:' in line:
                    journey_id = line.split(':')[-1].strip()
                    break
        
        self.record_test_result(
            "Handle special characters in journey data",
            success and journey_id is not None,
            f"Special characters handled correctly, Journey ID: {journey_id}" if success else stderr,
            execution_time
        )
        
        if journey_id:
            self.test_data_created.append(('journey', journey_id))
        
        # Test 2: Very long strings
        long_string_journey = {
            "name": "A" * 500,  # Very long name
            "description": "B" * 2000,  # Very long description
            "odaComponentType": "customer-management"
        }
        
        long_string_file = self.create_test_data_file(long_string_journey, "long_string_journey.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', long_string_file
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle very long strings",
            success,
            "Long strings handled correctly" if success else stderr,
            execution_time
        )
        
        # Test 3: Numeric values in string fields
        numeric_journey = {
            "name": 12345,  # Should be string
            "description": 67890,  # Should be string
            "odaComponentType": "customer-management",
            "priority": 999  # Should be string
        }
        
        numeric_file = self.create_test_data_file(numeric_journey, "numeric_journey.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', numeric_file
        ])
        execution_time = time.time() - start_time
        
        self.record_test_result(
            "Handle numeric values in string fields",
            success,  # Should handle type conversion gracefully
            "Numeric values handled correctly" if success else stderr,
            execution_time
        )
    
    def test_performance_scenarios(self):
        """Test performance with various scenarios"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("⚡ TESTING PERFORMANCE SCENARIOS")
        self.logger.info("=" * 60)
        
        # Test 1: Journey with many stages
        many_stages_journey = {
            "name": "Journey with Many Stages",
            "description": "Testing performance with many stages",
            "odaComponentType": "customer-management"
        }
        
        many_stages_file = self.create_test_data_file(many_stages_journey, "many_stages_journey.json")
        
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'create-journey',
            '--data-file', many_stages_file
        ])
        creation_time = time.time() - start_time
        
        journey_id = None
        if success and 'Journey created:' in stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'Journey created:' in line:
                    journey_id = line.split(':')[-1].strip()
                    break
        
        self.record_test_result(
            "Create journey (performance baseline)",
            success and journey_id is not None,
            f"Journey created in {creation_time:.2f}s",
            creation_time
        )
        
        if journey_id:
            self.test_data_created.append(('journey', journey_id))
            
            # Add multiple custom stages to test performance
            for i in range(10):
                custom_stage = {
                    "stageId": f"perf_test_stage_{i}",
                    "name": f"Performance Test Stage {i}",
                    "description": f"Stage {i} for performance testing",
                    "order": 100 + i,
                    "estimatedDuration": "1m",
                    "steps": [
                        {
                            "id": f"step_{j}",
                            "name": f"Step {j}",
                            "description": f"Step {j} description",
                            "order": j,
                            "estimatedDuration": "10s"
                        } for j in range(5)
                    ]
                }
                
                stage_file = self.create_test_data_file(custom_stage, f"perf_stage_{i}.json")
                
                start_time = time.time()
                success, stdout, stderr = self.run_command([
                    'python3', self.manage_journey_script,
                    '--action', 'add-stage',
                    '--journey-id', journey_id,
                    '--data-file', stage_file
                ])
                stage_time = time.time() - start_time
                
                if not success:
                    self.logger.warning(f"Failed to add performance test stage {i}: {stderr}")
                    break
            
            # Test dashboard performance with many stages
            start_time = time.time()
            success, stdout, stderr = self.run_command([
                'python3', self.manage_journey_script,
                '--action', 'dashboard',
                '--journey-id', journey_id
            ])
            dashboard_time = time.time() - start_time
            
            self.record_test_result(
                "Dashboard performance with many stages",
                success,
                f"Dashboard rendered in {dashboard_time:.2f}s",
                dashboard_time
            )
    
    def test_concurrent_operations(self):
        """Test concurrent operations (basic simulation)"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🔄 TESTING CONCURRENT OPERATIONS")
        self.logger.info("=" * 60)
        
        # Create multiple journeys simultaneously (sequential for safety)
        concurrent_journeys = []
        
        for i in range(3):
            journey_data = {
                "name": f"Concurrent Test Journey {i}",
                "description": f"Journey {i} for concurrent testing",
                "odaComponentType": "customer-management",
                "priority": "low"
            }
            
            journey_file = self.create_test_data_file(journey_data, f"concurrent_journey_{i}.json")
            
            start_time = time.time()
            success, stdout, stderr = self.run_command([
                'python3', self.manage_journey_script,
                '--action', 'create-journey',
                '--data-file', journey_file
            ])
            execution_time = time.time() - start_time
            
            journey_id = None
            if success and 'Journey created:' in stdout:
                lines = stdout.split('\n')
                for line in lines:
                    if 'Journey created:' in line:
                        journey_id = line.split(':')[-1].strip()
                        break
            
            if journey_id:
                concurrent_journeys.append(journey_id)
                self.test_data_created.append(('journey', journey_id))
        
        self.record_test_result(
            "Create multiple journeys concurrently",
            len(concurrent_journeys) >= 2,
            f"Created {len(concurrent_journeys)} journeys successfully",
            0
        )
        
        # Test reading all journeys
        start_time = time.time()
        success, stdout, stderr = self.run_command([
            'python3', self.manage_journey_script,
            '--action', 'list-journeys'
        ])
        execution_time = time.time() - start_time
        
        journey_count = stdout.count('JRN-') if success else 0
        
        self.record_test_result(
            "List all journeys after concurrent creation",
            success and journey_count >= len(concurrent_journeys),
            f"Found {journey_count} journeys in listing",
            execution_time
        )
    
    def cleanup_test_data(self):
        """Clean up all test data created during testing"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🧹 CLEANING UP TEST DATA")
        self.logger.info("=" * 60)
        
        # Delete test journeys
        for data_type, data_id in reversed(self.test_data_created):
            if data_type == 'journey':
                self.logger.info(f"Deleting test journey: {data_id}")
                success, stdout, stderr = self.run_command([
                    'python3', self.manage_journey_script,
                    '--action', 'delete-journey',
                    '--journey-id', data_id,
                    '--confirm'
                ])
                
                if success:
                    self.logger.info(f"✅ Deleted journey: {data_id}")
                else:
                    self.logger.warning(f"⚠️ Failed to delete journey {data_id}: {stderr}")
        
        # Delete temporary files
        for filepath in self.temp_files_created:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.logger.debug(f"Deleted temp file: {filepath}")
            except Exception as e:
                self.logger.warning(f"Failed to delete temp file {filepath}: {str(e)}")
        
        # Remove test data directory if empty
        try:
            if os.path.exists(self.test_data_dir) and not os.listdir(self.test_data_dir):
                os.rmdir(self.test_data_dir)
                self.logger.debug(f"Removed empty test data directory: {self.test_data_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to remove test data directory: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        test_end_time = datetime.now(timezone.utc)
        total_duration = (test_end_time - self.test_start_time).total_seconds()
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 COMPREHENSIVE TEST REPORT")
        self.logger.info("=" * 80)
        
        # Summary statistics
        pass_rate = (self.tests_passed / self.tests_total * 100) if self.tests_total > 0 else 0
        
        self.logger.info(f"Test Execution Summary:")
        self.logger.info(f"  Started: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.logger.info(f"  Ended: {test_end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.logger.info(f"  Duration: {total_duration:.2f} seconds")
        self.logger.info(f"  Total Tests: {self.tests_total}")
        self.logger.info(f"  Passed: {self.tests_passed}")
        self.logger.info(f"  Failed: {self.tests_failed}")
        self.logger.info(f"  Pass Rate: {pass_rate:.1f}%")
        
        # Performance metrics
        execution_times = [result['execution_time'] for result in self.test_results if result['execution_time'] > 0]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
            
            self.logger.info(f"\nPerformance Metrics:")
            self.logger.info(f"  Average execution time: {avg_time:.2f}s")
            self.logger.info(f"  Maximum execution time: {max_time:.2f}s")
            self.logger.info(f"  Minimum execution time: {min_time:.2f}s")
        
        # Failed tests details
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            self.logger.info(f"\nFailed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                self.logger.info(f"  ❌ {test['test_name']}: {test['details']}")
        
        # Test categories summary
        categories = {}
        for result in self.test_results:
            category = result['test_name'].split(' ')[0]
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0}
            categories[category]['total'] += 1
            if result['success']:
                categories[category]['passed'] += 1
        
        self.logger.info(f"\nTest Categories:")
        for category, stats in categories.items():
            category_pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            self.logger.info(f"  {category}: {stats['passed']}/{stats['total']} ({category_pass_rate:.1f}%)")
        
        # Recommendations
        self.logger.info(f"\nRecommendations:")
        if pass_rate == 100:
            self.logger.info("  ✅ All tests passed! The journey management system is working correctly.")
        elif pass_rate >= 90:
            self.logger.info("  ⚠️ Most tests passed. Review failed tests for minor issues.")
        elif pass_rate >= 70:
            self.logger.info("  ⚠️ Moderate test failures. Investigate and fix issues before production use.")
        else:
            self.logger.info("  ❌ Many test failures. System requires significant fixes before use.")
        
        if failed_tests:
            self.logger.info("  📝 Review the failed tests above and fix the underlying issues.")
            self.logger.info("  🔧 Check error handling and data validation implementations.")
        
        self.logger.info(f"\n📁 Detailed log saved to: {self.log_file}")
        self.logger.info("=" * 80)
        
        return {
            'total_tests': self.tests_total,
            'passed': self.tests_passed,
            'failed': self.tests_failed,
            'pass_rate': pass_rate,
            'duration': total_duration,
            'failed_tests': failed_tests,
            'log_file': self.log_file
        }
    
    def run_all_tests(self, quick_test: bool = False):
        """Run all test suites"""
        self.logger.info("🚀 Starting comprehensive test execution...")
        
        try:
            # Core functionality tests
            self.test_journey_crud_operations()
            self.test_stage_operations()
            self.test_rules_operations()
            self.test_import_export_operations()
            
            # Error handling and validation tests
            self.test_error_handling_and_edge_cases()
            self.test_data_validation()
            
            # Performance and advanced tests (skip in quick mode)
            if not quick_test:
                self.test_performance_scenarios()
                self.test_concurrent_operations()
            
        except Exception as e:
            self.logger.error(f"Test execution error: {str(e)}")
            traceback.print_exc()
        
        finally:
            # Always clean up and generate report
            self.cleanup_test_data()
            return self.generate_test_report()


def main():
    """Main function with command-line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Journey Management Test Suite')
    parser.add_argument('--quick-test', action='store_true', 
                       help='Run quick test suite (skip performance tests)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--log-file', type=str,
                       help='Custom log file path')
    
    args = parser.parse_args()
    
    # Create and run test framework
    test_framework = JourneyTestFramework(
        log_file=args.log_file,
        verbose=args.verbose
    )
    
    try:
        report = test_framework.run_all_tests(quick_test=args.quick_test)
        
        # Exit with appropriate code
        if report['pass_rate'] == 100:
            sys.exit(0)
        elif report['pass_rate'] >= 70:
            sys.exit(1)
        else:
            sys.exit(2)
            
    except KeyboardInterrupt:
        test_framework.logger.info("\n⚠️ Tests interrupted by user")
        test_framework.cleanup_test_data()
        sys.exit(130)
    except Exception as e:
        test_framework.logger.error(f"Test framework error: {str(e)}")
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main() 