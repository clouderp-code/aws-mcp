# Simple Journeys Solution

## Overview

This solution creates a **simple, clean journeys MCP tool** that follows the **exact same pattern** as the working `manage_journey.py` script. Instead of trying to fix the complex dual-storage architecture, we've created a new tool that directly replicates the successful approach.

## Why This Approach?

The original complex solution had multiple issues:
- **Dual storage systems** (DynamoDB + local JSON) that needed synchronization
- **Complex inheritance hierarchies** with multiple managers
- **Mixed async/sync patterns** causing execution issues
- **Over-engineered architecture** that was hard to debug

The **simple solution** follows the proven pattern from `manage_journey.py`:
- **Single DynamoDB storage** with clear, simple structure
- **Direct, straightforward operations** without complex abstractions
- **Proven data model** that already works in production
- **Easy to understand and maintain**

## Files Created

### 1. `simple_journeys_tool.py`
- **`SimpleJourneysService`**: Replicates the exact DynamoDB operations from `manage_journey.py`
- **`SimpleJourneysTool`**: MCP tool wrapper with simple interface
- **Key Methods**:
  - `create_journey_complete()`: Creates journey with optional default stages
  - `add_default_stages_complete()`: Adds the 6 default TMF stages
  - `list_stages()`: Lists stages for a journey
  - `add_stage()`: Adds individual stages

### 2. `test_simple_journeys.sh`
- **Simple curl-based test script** that validates the tool
- **Three test scenarios**:
  1. Create journey with 6 default stages
  2. List stages for the created journey
  3. Create journey without default stages
- **Color-coded output** for easy result interpretation

## DynamoDB Structure

The tool uses the **exact same DynamoDB structure** as `manage_journey.py`:

```
Journey Metadata:
- PK: JOURNEY#{journey_id}
- SK: METADATA
- Data: {journeyId, name, description, status, ...}

Stage Definitions:
- PK: JOURNEY#{journey_id}
- SK: STAGE#{order:02d}#{stage_id}
- GSI1PK: JOURNEY#{journey_id}#STAGES
- GSI1SK: {order:02d}
- Data: {stageId, name, description, order, ...}
```

## Default Stages

The tool creates the standard 6 TMF ODA transformation stages:

1. **`raw_analysis`**: Raw Input Analysis
2. **`stripped_schema`**: Create Stripped Document  
3. **`tmf_mapping`**: TMF Schema Mapping
4. **`data_migration`**: Data Migration Planning
5. **`data_migration`**: Data Migration Execution
6. **`verification_validation`**: Verification & Validation

## Usage

### Start the Server
```bash
cd /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server
./start_server_with_logging.sh
```

### Run Tests
```bash
cd /opt/mycode/aws-mcp/scripts
./test_simple_journeys.sh
```

### API Examples

**Create Journey with Default Stages:**
```bash
curl -X POST http://localhost:8000/tools/simple-journeys \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "journey_data": {
      "name": "Test Journey",
      "description": "Test journey for validation",
      "odaComponentType": "customer-management",
      "priority": "high",
      "include_default_stages": true
    }
  }'
```

**List Stages for Journey:**
```bash
curl -X POST http://localhost:8000/tools/simple-journeys \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list-stages",
    "journey_id": "JRN-XXXXXXXXXX"
  }'
```

## Expected Results

✅ **Journey Creation**: Should return `"stages_count": 6`  
✅ **Stage Listing**: Should return 6 stages with proper data  
✅ **Clean Architecture**: Simple, maintainable code  
✅ **Proven Pattern**: Uses the same approach as working `manage_journey.py`

## Benefits

1. **Reliability**: Uses proven DynamoDB operations
2. **Simplicity**: Clean, straightforward architecture
3. **Maintainability**: Easy to understand and extend
4. **Consistency**: Matches existing working patterns
5. **Testability**: Simple curl-based testing

## Testing

The test script validates:
- ✅ Journey creation with default stages
- ✅ Stage listing functionality
- ✅ Journey creation without stages
- ✅ Proper response structures
- ✅ Error handling

This approach provides a **reliable, simple solution** that directly addresses the requirements without the complexity of the previous dual-storage architecture. 