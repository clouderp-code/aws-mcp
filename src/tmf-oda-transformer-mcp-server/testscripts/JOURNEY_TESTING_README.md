# Journey Tool Testing Scripts

This directory contains comprehensive test scripts for your TMF ODA Transformer MCP Server journey tools with **enhanced testing for automatic default stage creation**.

## 📋 Available Scripts

### 1. `test_journey_endpoints.sh` - Comprehensive Test Suite with Default Stages Testing

A complete test suite that includes **comprehensive testing for the new journey creation functionality with automatic default six stages**.

**NEW COMPREHENSIVE TESTING FEATURES:**
- 🆕 **Journey creation with automatic default six stages**
- 🔍 **Verification of journey metadata and stage configuration**
- ✅ **Comprehensive testing of default stages**: `raw_analysis`, `stripped_schema`, `tmf_mapping`, `migration_planning`, `data_migration`, `verification_validation`
- 🎯 **Verification that journeys without custom stages get defaults automatically**
- 🚫 **Verification that journeys with custom stages do NOT get defaults**
- 🔧 **Enhanced add_default_stages testing with stage verification**

**Enhanced Functions:**
- `create_journey_and_verify()`: Creates journey and verifies default stages
- `verify_journey_stages()`: Verifies journey has correct six stages
- `verify_journey_metadata()`: Verifies journey metadata matches expectations
- `test_add_default_stages()`: Comprehensive testing of add_default_stages action

**Features:**
- Tests all 51 journey and logs endpoints
- Comprehensive error handling tests
- Backward compatibility tests
- Color-coded output with detailed formatting
- Test result summary with pass/fail counts
- Detailed JSON response parsing
- **NEW**: Automatic verification of default stage creation
- **NEW**: Metadata validation for created journeys
- **NEW**: Stage count and ID verification

**Usage:**
```bash
# Test against localhost (default)
./test_journey_endpoints.sh

# Test against specific server
./test_journey_endpoints.sh http://your-server-ip:8000

# Test against remote server
./test_journey_endpoints.sh http://18.191.87.212:8000
```

### 2. `quick_test_journeys.sh` - Quick Testing

A streamlined script for testing the most common journey operations.

**Features:**
- Tests 8 most common operations
- Quick health check
- Simplified output format
- Fast execution (10-second timeout)
- Perfect for quick validation

**Usage:**
```bash
# Quick test against localhost
./quick_test_journeys.sh

# Quick test against specific server
./quick_test_journeys.sh http://your-server-ip:8000
```

## 🎯 The Six Default Stages

When creating a journey with metadata only (no custom stages), the system automatically creates these six stages:

### 1. **raw_analysis** - Raw Input Analysis
- Schema parsing, relationship discovery, data type analysis
- Estimated duration: 15 minutes
- Steps: schema_parsing, relationship_discovery, data_type_analysis, business_rules_extraction

### 2. **stripped_schema** - Create Stripped Document
- Schema stripping, core structure extraction, simplification
- Estimated duration: 12 minutes
- Steps: schema_stripping, core_structure_extraction, data_model_simplification

### 3. **tmf_mapping** - TMF Schema Mapping
- TMF API matching, attribute mapping, relationship mapping
- Estimated duration: 20 minutes
- Steps: tmf_api_matching, attribute_mapping, relationship_mapping, api_coverage_analysis, gap_identification

### 4. **migration_planning** - Data Migration Planning
- Migration strategy, ETL scripts, validation rules
- Estimated duration: 18 minutes
- Steps: migration_strategy_planning, etl_script_generation, data_validation_rules, rollback_procedures

### 5. **data_migration** - Data Migration
- Dataset selection, data transfer, compliance testing
- Estimated duration: 25 minutes
- Steps: candidate_dataset_selection, data_transfer, tmf_api_compliance_test, mark_completion

### 6. **verification_validation** - Verification & Validation
- Mapping validation, compliance checks, final reporting
- Estimated duration: 22 minutes
- Steps: mapping_validation, api_compliance_check, data_integrity_verification, performance_assessment, final_report_generation

## 🧪 Test Categories

### Journey CRUD Operations (Enhanced)
- ✅ List all journeys
- ✅ **Create journey with default stages** (NEW - comprehensive verification)
- ✅ **Create journey with custom stages** (NEW - verifies no defaults created)
- ✅ **Verify journey metadata** (NEW - validates name, description, component type)
- ✅ Update journey
- ✅ Delete journey

### Stage Management (Enhanced)
- ✅ List stages
- ✅ **Verify stage count and IDs** (NEW - validates all 6 default stages)
- ✅ Add custom stage
- ✅ Update stage
- ✅ Delete stage
- ✅ **Add default TMF ODA stages with verification** (NEW - comprehensive testing)

### Rules Management
- ✅ List rules
- ✅ Add rule
- ✅ Update rule
- ✅ Delete rule

### Job Management
- ✅ List jobs
- ✅ Get job details
- ✅ Run job
- ✅ Cancel job
- ✅ Update job status
- ✅ Retry job
- ✅ Get job metrics
- ✅ Get job timeline
- ✅ Batch cancel jobs

### Interactive Features
- ✅ Dashboard
- ✅ Journey summary

### Logs and Reports
- ✅ Get job logs
- ✅ Add log entry
- ✅ Search logs
- ✅ Get logs by level
- ✅ Export job logs
- ✅ Get error summary
- ✅ Generate summary report
- ✅ Analyze job performance

### Error Handling
- ✅ Missing required parameters
- ✅ Invalid actions
- ✅ Service exceptions

## 🎯 Enhanced Test Scenarios

### 1. Journey Creation with Default Stages
```bash
# Creates journey with metadata only
# Automatically creates 6 default stages
# Verifies all stages are created correctly
```

**Test Data:**
```json
{
  "name": "Test Customer Management Journey",
  "description": "Comprehensive test journey for customer management transformation with default stages",
  "oda_component_type": "customer-management",
  "source_type": "database",
  "priority": "high"
}
```

**Expected Results:**
- ✅ Journey created successfully
- ✅ `default_stages_created: true`
- ✅ `stages_count: 6`
- ✅ All 6 default stages verified: `raw_analysis`, `stripped_schema`, `tmf_mapping`, `migration_planning`, `data_migration`, `verification_validation`

### 2. Journey Creation with Custom Stages
```bash
# Creates journey with custom stages specified
# Does NOT create default stages
# Respects user-provided stage configuration
```

**Test Data:**
```json
{
  "name": "Custom Stages Journey",
  "description": "Journey with custom stages instead of defaults",
  "oda_component_type": "order-management",
  "source_type": "api",
  "priority": "low",
  "stages": ["custom_stage_1", "custom_stage_2"]
}
```

**Expected Results:**
- ✅ Journey created successfully
- ✅ `default_stages_created: false`
- ✅ Only custom stages present (no defaults)

### 3. Add Default Stages to Existing Journey
```bash
# Adds default stages to existing journey
# Verifies exactly 6 stages are added
# Confirms all stage IDs are correct
```

**Expected Results:**
- ✅ 6 stages added
- ✅ All default stage IDs present
- ✅ Complete stage verification passed

## 🔧 Prerequisites

- `curl` command-line tool
- `jq` for JSON parsing (optional but recommended)
- Running MCP server on specified port

## 📊 Understanding Enhanced Output

### Journey Creation Success
```
✅ SUCCESS: Create new journey with default stages completed successfully
✅ Default stages creation verified (6 stages created)
✅ Journey created successfully
  Journey ID: JRN-A1B2C3D4E5F6
  Default stages created: true
  Stages count: 6
✅ Correct number of stages (6)
    ✅ Stage raw_analysis: Raw Input Analysis
    ✅ Stage stripped_schema: Create Stripped Document
    ✅ Stage tmf_mapping: TMF Schema Mapping
    ✅ Stage migration_planning: Data Migration Planning
    ✅ Stage data_migration: Data Migration
    ✅ Stage verification_validation: Verification & Validation
✅ All six default stages verified successfully
```

### Metadata Verification Success
```
  Metadata verification:
    ✅ Name: Test Customer Management Journey
    ✅ Description: Comprehensive test journey for customer management transformation with default stages
    ✅ ODA Component Type: customer-management
```

### Add Default Stages Success
```
Stages before adding defaults: 0
✅ Add default stages completed successfully
  Stages added: 6
  Added stages:
    - raw_analysis
    - stripped_schema
    - tmf_mapping
    - migration_planning
    - data_migration
    - verification_validation
✅ Correct number of default stages added (6)
```

### Error Indicators
```
❌ ERROR: Some default stages are missing
❌ Incorrect number of stages found: 4 (expected 6)
❌ Name mismatch: expected 'Test Journey', got 'Different Name'
```

## 🐛 Common Issues

1. **Connection Refused**: Make sure your MCP server is running
2. **Timeout**: Increase timeout values in the scripts if needed
3. **JSON Parse Error**: Some responses may not be valid JSON (script handles this gracefully)
4. **Stage Verification Failures**: Check if journey creation properly includes default stages
5. **Metadata Mismatches**: Verify journey data is being stored correctly

## 🚀 Running Against Your Server

Since your server is running on `http://0.0.0.0:8000`, you can test with:

```bash
# Quick test
./quick_test_journeys.sh http://localhost:8000

# Full test suite with default stages testing
./test_journey_endpoints.sh http://localhost:8000
```

## 📈 Expected Results

The enhanced test suite will validate:
- ✅ **Journey creation with automatic default stages**
- ✅ **Metadata preservation and validation**
- ✅ **Stage count and ID verification**
- ✅ **Custom stages vs default stages behavior**
- ✅ **Add default stages functionality**

Some operations may still fail due to:
- Unimplemented methods in specific services
- Known issues being worked on
- Missing test data for certain scenarios

The scripts will clearly indicate which tests pass/fail and provide detailed verification results.

## 🔄 Continuous Testing

Use these scripts during development to:
- Validate new journey creation functionality
- Test default stage creation
- Verify metadata handling
- Test stage management operations
- Validate error handling
- Performance testing with different timeouts

## 🎉 Happy Testing!

These enhanced scripts provide comprehensive testing for the new journey creation functionality with automatic default stages. The detailed verification ensures that journeys are created correctly with all expected stages and metadata.

**Key Benefits:**
- 🎯 **Automatic validation** of default stage creation
- 📋 **Comprehensive verification** of journey metadata
- 🔍 **Detailed stage-by-stage validation**
- ✅ **Clear pass/fail indicators** for all tests
- 🚀 **Enhanced confidence** in journey creation functionality 