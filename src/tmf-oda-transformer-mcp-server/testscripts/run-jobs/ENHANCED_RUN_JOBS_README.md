# Enhanced Run Jobs Tool Documentation

## Overview

The `run-jobs` tool has been significantly enhanced to provide comprehensive job management capabilities for TMF ODA transformation journeys. It now supports the full lifecycle of job management including creation, execution, monitoring, and control.

## 🚀 **Key Enhancements**

### **Action-Based Architecture**
The tool now supports multiple actions through a single endpoint:
- **`run`** - Create and execute a job (default behavior)
- **`create`** - Create a job without executing it
- **`status`** - Get job status and progress information
- **`cancel`** - Cancel a running job (planned)
- **`retry`** - Retry a failed job
- **`list`** - List jobs for a specific stage

### **Advanced Job Control**
- **Asynchronous Execution**: `wait_for_completion=false` for non-blocking job starts
- **Progress Monitoring**: `progress_callback=true` for real-time progress updates
- **Job Configuration**: Support for custom job parameters via `job_config`
- **Error Handling**: Comprehensive error reporting and recovery

### **Integration with Journey Management**
- Seamless integration with the existing journey management system
- Consistent data storage and retrieval patterns
- Support for all 6 transformation stages:
  - `raw_analysis`
  - `stripped_schema`
  - `tmf_mapping`
  - `migration_planning`
  - `data_migration`
  - `verification_validation`

## 📋 **API Reference**

### **Endpoint**
```
POST /tools/run-jobs
```

### **Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `journey_id` | string | ✅ | - | Journey ID for the transformation process |
| `stage_id` | string | ⚠️ | `raw_analysis` | Stage ID to execute (required for run, create, list actions) |
| `action` | string | ❌ | `run` | Action to perform (run, create, status, cancel, retry, list) |
| `job_id` | string | ⚠️ | `""` | Job ID (required for status, cancel, retry actions) |
| `triggered_by` | string | ❌ | `mcp-server` | Who triggered the job execution |
| `reason` | string | ❌ | `MCP Server execution` | Reason for executing the job |
| `job_config` | object | ❌ | `null` | Optional job configuration parameters |
| `wait_for_completion` | boolean | ❌ | `true` | Whether to wait for job completion |
| `progress_callback` | boolean | ❌ | `false` | Include real-time progress updates |

## 🔧 **Usage Examples**

### **1. Create and Run a Job (Default)**
```bash
curl -X POST http://localhost:8000/tools/run-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "JRN-12345",
    "stage_id": "raw_analysis",
    "action": "run",
    "triggered_by": "user",
    "reason": "Manual execution"
  }'
```

### **2. Create Job Without Execution**
```bash
curl -X POST http://localhost:8000/tools/run-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "JRN-12345",
    "stage_id": "raw_analysis",
    "action": "create",
    "wait_for_completion": false
  }'
```

### **3. Monitor Job Status**
```bash
curl -X POST http://localhost:8000/tools/run-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "JRN-12345",
    "action": "status",
    "job_id": "JOB-001-20240101120000",
    "progress_callback": true
  }'
```

### **4. Start Asynchronous Job**
```bash
curl -X POST http://localhost:8000/tools/run-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "JRN-12345",
    "stage_id": "tmf_mapping",
    "action": "run",
    "wait_for_completion": false,
    "job_config": {
      "timeout": 300,
      "priority": "high",
      "retry_attempts": 3
    }
  }'
```

### **5. List Jobs for a Stage**
```bash
curl -X POST http://localhost:8000/tools/run-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "JRN-12345",
    "stage_id": "raw_analysis",
    "action": "list"
  }'
```

### **6. Retry Failed Job**
```bash
curl -X POST http://localhost:8000/tools/run-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "JRN-12345",
    "action": "retry",
    "job_id": "JOB-001-20240101120000",
    "reason": "Retry after fixing configuration"
  }'
```

## 📊 **Response Format**

### **Successful Response**
```json
{
  "result": {
    "status": "success",
    "message": "Job JOB-001-20240101120000 completed successfully",
    "job_id": "JOB-001-20240101120000",
    "journey_id": "JRN-12345",
    "stage_id": "raw_analysis",
    "execution_status": "completed",
    "duration_seconds": 45.2,
    "timestamp": "2024-01-01T12:00:00Z",
    "job_details": {
      "status": "completed",
      "progress": 100,
      "startTime": "2024-01-01T12:00:00Z",
      "endTime": "2024-01-01T12:00:45Z"
    }
  },
  "timestamp": "2024-01-01T12:00:45.123456"
}
```

### **Error Response**
```json
{
  "result": {
    "status": "error",
    "message": "Job execution failed: Stage not found",
    "journey_id": "JRN-12345",
    "stage_id": "invalid_stage",
    "error_details": "Stage invalid_stage not found in stage registry",
    "duration_seconds": 1.2,
    "timestamp": "2024-01-01T12:00:01Z"
  },
  "timestamp": "2024-01-01T12:00:01.123456"
}
```

## 🎯 **Execution Status Types**

| Status | Description |
|--------|-------------|
| `started` | Job was created and started (async mode) |
| `created` | Job was created but not executed |
| `completed` | Job executed successfully |
| `failed` | Job execution failed |
| `creation_failed` | Job creation failed |
| `in_progress` | Job is currently running |
| `pending` | Job is queued for execution |
| `cancelled` | Job was cancelled |

## 🔄 **Job Configuration Options**

The `job_config` parameter supports various options for job customization:

```json
{
  "job_config": {
    "timeout": 300,           // Job timeout in seconds
    "retry_attempts": 3,      // Number of retry attempts
    "priority": "high",       // Job priority (low, medium, high, critical)
    "parallel_execution": true, // Enable parallel step execution
    "notification_enabled": true, // Enable notifications
    "custom_parameters": {    // Stage-specific parameters
      "batch_size": 1000,
      "memory_limit": "2GB"
    }
  }
}
```

## 🧪 **Testing**

A comprehensive test script is available to verify all enhanced functionality:

```bash
cd /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/testscripts/journey-crud
./test_enhanced_run_jobs.sh
```

The test script validates:
- ✅ Job creation without execution
- ✅ Job status monitoring  
- ✅ Complete job execution
- ✅ Job listing for stages
- ✅ Asynchronous execution
- ✅ Progress monitoring
- ✅ Job configuration support
- ✅ Error handling

## 🔗 **Integration Points**

### **With Journey Management**
The enhanced run-jobs tool integrates seamlessly with:
- Journey CRUD operations
- Stage management
- Second Brain rule management
- Comprehensive logging and reporting

### **With Existing Systems**
- Compatible with existing `TransformationJobExecutor`
- Uses the same DynamoDB data model
- Maintains backward compatibility with previous API calls

## 🚦 **Migration from Old Version**

The enhanced tool maintains backward compatibility. Existing API calls will continue to work:

**Old Format (Still Supported):**
```json
{
  "journey_id": "JRN-12345",
  "stage_id": "raw_analysis",
  "triggered_by": "user",
  "reason": "Manual execution"
}
```

**New Enhanced Format:**
```json
{
  "journey_id": "JRN-12345",
  "stage_id": "raw_analysis", 
  "action": "run",
  "triggered_by": "user",
  "reason": "Manual execution",
  "wait_for_completion": true,
  "progress_callback": false
}
```

## 📈 **Performance Improvements**

- **Asynchronous Operations**: Non-blocking job execution
- **Progress Monitoring**: Real-time status updates
- **Better Error Handling**: Detailed error reporting and recovery
- **Resource Management**: Configurable timeouts and retry logic
- **Comprehensive Logging**: Enhanced debugging and monitoring

## 🔮 **Future Enhancements**

Planned features for future releases:
- **Job Cancellation**: Ability to stop running jobs
- **Job Scheduling**: Schedule jobs for future execution
- **Batch Operations**: Execute multiple jobs simultaneously
- **Job Dependencies**: Define job execution dependencies
- **Advanced Monitoring**: Real-time progress streaming
- **Job Templates**: Predefined job configurations

## 📞 **Support**

For issues or questions regarding the enhanced run-jobs tool:

1. Check the comprehensive test script results
2. Review the detailed logs in `/opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/logs/`
3. Verify journey and stage configurations
4. Ensure proper AWS credentials and permissions

---

**The enhanced run-jobs tool provides enterprise-grade job management capabilities while maintaining simplicity and backward compatibility.** 🚀 