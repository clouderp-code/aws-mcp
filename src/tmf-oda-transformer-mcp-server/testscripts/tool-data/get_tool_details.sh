#!/bin/bash

# TMF ODA Transformer MCP Server - Tool Details Script
# This script gets detailed information for specific MCP tools

set -e

# Configuration
SERVER_URL="http://localhost:8000"
TOOLS_ENDPOINT="$SERVER_URL/tools"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}${BOLD}🔍 $1${NC}"
    echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_usage() {
    echo -e "${CYAN}Usage: $0 [tool-name]${NC}"
    echo ""
    echo -e "${BOLD}Available tools:${NC}"
    echo -e "  • ${CYAN}raw-analysis${NC} - Execute raw analysis stage"
    echo -e "  • ${CYAN}stripped-schema${NC} - Execute schema stripping stage"
    echo -e "  • ${CYAN}run-jobs${NC} - Execute any transformation stage"
    echo -e "  • ${CYAN}journeys${NC} - Journey lifecycle management"
    echo -e "  • ${CYAN}get-job-logs${NC} - Retrieve execution logs"
    echo -e "  • ${CYAN}logs-and-reports${NC} - Enhanced logs and reports"
    echo -e "  • ${CYAN}test-runner${NC} - Validation testing"
    echo -e "  • ${CYAN}all${NC} - Show details for all tools"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 raw-analysis"
    echo -e "  $0 journeys"
    echo -e "  $0 all"
}

get_raw_analysis_details() {
    echo -e "${BOLD}🔧 raw-analysis Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Execute raw analysis stage of TMF ODA transformation journey"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/raw-analysis${NC}"
    echo ""
    echo -e "${BOLD}Parameters:${NC}"
    echo -e "  • ${CYAN}journey_id${NC} (required): Journey ID for the transformation process"
    echo -e "  • ${CYAN}stage_id${NC} (optional): Stage ID to execute (default: 'raw_analysis')"
    echo -e "  • ${CYAN}triggered_by${NC} (optional): Who triggered the job (default: 'mcp-server')"
    echo -e "  • ${CYAN}reason${NC} (optional): Reason for executing (default: 'MCP Server execution')"
    echo ""
    echo -e "${BOLD}Example Request:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/raw-analysis \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"journey_id\": \"JRN-SAMPLE-001\",${NC}"
    echo -e "${CYAN}    \"stage_id\": \"raw_analysis\",${NC}"
    echo -e "${CYAN}    \"triggered_by\": \"test-script\",${NC}"
    echo -e "${CYAN}    \"reason\": \"Testing raw analysis functionality\"${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
    echo -e "${BOLD}Response Format:${NC}"
    echo -e "  • ${CYAN}status${NC}: 'success' or 'error'"
    echo -e "  • ${CYAN}message${NC}: Status message"
    echo -e "  • ${CYAN}job_id${NC}: Generated job ID"
    echo -e "  • ${CYAN}duration_seconds${NC}: Execution time"
    echo ""
}

get_stripped_schema_details() {
    echo -e "${BOLD}🔧 stripped-schema Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Execute schema stripping stage of TMF ODA transformation"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/stripped-schema${NC}"
    echo ""
    echo -e "${BOLD}Parameters:${NC}"
    echo -e "  • ${CYAN}journey_id${NC} (required): Journey ID for the transformation process"
    echo -e "  • ${CYAN}stage_id${NC} (optional): Stage ID to execute (default: 'stripped_schema')"
    echo -e "  • ${CYAN}triggered_by${NC} (optional): Who triggered the job (default: 'mcp-server')"
    echo -e "  • ${CYAN}reason${NC} (optional): Reason for executing (default: 'MCP Server execution')"
    echo ""
    echo -e "${BOLD}Example Request:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/stripped-schema \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"journey_id\": \"JRN-SAMPLE-001\",${NC}"
    echo -e "${CYAN}    \"stage_id\": \"stripped_schema\"${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
}

get_run_jobs_details() {
    echo -e "${BOLD}🎯 run-jobs Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Execute any transformation stage in the TMF ODA pipeline"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/run-jobs${NC}"
    echo ""
    echo -e "${BOLD}Parameters:${NC}"
    echo -e "  • ${CYAN}journey_id${NC} (required): Journey ID for the transformation process"
    echo -e "  • ${CYAN}stage_id${NC} (required): Stage ID to execute"
    echo -e "  • ${CYAN}triggered_by${NC} (optional): Who triggered the job (default: 'mcp-server')"
    echo -e "  • ${CYAN}reason${NC} (optional): Reason for executing (default: 'MCP Server execution')"
    echo ""
    echo -e "${BOLD}Available Stages:${NC}"
    echo -e "  • ${CYAN}raw_analysis${NC} - Initial schema analysis"
    echo -e "  • ${CYAN}stripped_schema${NC} - Schema stripping and cleaning"
    echo -e "  • ${CYAN}data_mapping${NC} - Data mapping and transformation"
    echo -e "  • ${CYAN}compliance_validation${NC} - TMF compliance validation"
    echo -e "  • ${CYAN}business_rules${NC} - Business rules application"
    echo -e "  • ${CYAN}integration_testing${NC} - Integration testing"
    echo ""
    echo -e "${BOLD}Example Request:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/run-jobs \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"journey_id\": \"JRN-SAMPLE-001\",${NC}"
    echo -e "${CYAN}    \"stage_id\": \"data_mapping\"${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
}

get_journeys_details() {
    echo -e "${BOLD}📊 journeys Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Comprehensive journey lifecycle management (CRUD, stages, jobs)"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/journeys${NC}"
    echo ""
    echo -e "${BOLD}Core Actions:${NC}"
    echo ""
    echo -e "${BOLD}Journey CRUD:${NC}"
    echo -e "  • ${CYAN}list/read${NC} - List all journeys or get specific journey details"
    echo -e "  • ${CYAN}create${NC} - Create a new journey"
    echo -e "  • ${CYAN}update${NC} - Update existing journey"
    echo -e "  • ${CYAN}delete${NC} - Delete journey and associated data"
    echo ""
    echo -e "${BOLD}Stage Management:${NC}"
    echo -e "  • ${CYAN}list_stages${NC} - List stages for a journey"
    echo -e "  • ${CYAN}add_stage${NC} - Add a new stage to journey"
    echo -e "  • ${CYAN}update_stage${NC} - Update existing stage"
    echo -e "  • ${CYAN}delete_stage${NC} - Delete stage from journey"
    echo ""
    echo -e "${BOLD}Job Management:${NC}"
    echo -e "  • ${CYAN}list_jobs${NC} - List job executions"
    echo -e "  • ${CYAN}get_job${NC} - Get job details"
    echo -e "  • ${CYAN}run_job${NC} - Execute job for stage"
    echo -e "  • ${CYAN}cancel_job${NC} - Cancel running job"
    echo ""
    echo -e "${BOLD}Common Parameters:${NC}"
    echo -e "  • ${CYAN}action${NC} (required): Action to perform"
    echo -e "  • ${CYAN}journey_id${NC}: Journey ID (required for most actions)"
    echo -e "  • ${CYAN}job_id${NC}: Job ID (for job operations)"
    echo -e "  • ${CYAN}stage_id${NC}: Stage ID (for stage operations)"
    echo ""
    echo -e "${BOLD}Example - Create Journey:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/journeys \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"action\": \"create\",${NC}"
    echo -e "${CYAN}    \"journey_data\": {${NC}"
    echo -e "${CYAN}      \"name\": \"Test Journey\",${NC}"
    echo -e "${CYAN}      \"description\": \"Testing TMF transformation\",${NC}"
    echo -e "${CYAN}      \"odaComponentType\": \"customer-management\"${NC}"
    echo -e "${CYAN}    }${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
    echo -e "${BOLD}Example - Run Job:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/journeys \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"action\": \"run_job\",${NC}"
    echo -e "${CYAN}    \"journey_id\": \"JRN-SAMPLE-001\",${NC}"
    echo -e "${CYAN}    \"stage_id\": \"raw_analysis\"${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
}

get_logs_and_reports_details() {
    echo -e "${BOLD}📝 logs-and-reports Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Enhanced logs and reports management with search and analysis"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/logs-and-reports${NC}"
    echo ""
    echo -e "${BOLD}Log Operations:${NC}"
    echo -e "  • ${CYAN}get_job_logs${NC} - Get logs for a specific job"
    echo -e "  • ${CYAN}add_log_entry${NC} - Add a log entry to a job"
    echo -e "  • ${CYAN}search_logs${NC} - Search through logs with filters"
    echo -e "  • ${CYAN}get_logs_by_level${NC} - Get logs filtered by level (error, warning, info)"
    echo -e "  • ${CYAN}export_job_logs${NC} - Export job logs to file"
    echo ""
    echo -e "${BOLD}Report Operations:${NC}"
    echo -e "  • ${CYAN}get_job_reports${NC} - Get reports for a specific job"
    echo -e "  • ${CYAN}create_job_report${NC} - Create custom job report"
    echo -e "  • ${CYAN}generate_summary_report${NC} - Generate comprehensive job summary"
    echo -e "  • ${CYAN}generate_performance_report${NC} - Generate performance analysis"
    echo ""
    echo -e "${BOLD}Common Parameters:${NC}"
    echo -e "  • ${CYAN}action${NC} (required): Action to perform"
    echo -e "  • ${CYAN}journey_id${NC}: Journey ID"
    echo -e "  • ${CYAN}job_id${NC}: Job ID"
    echo -e "  • ${CYAN}stage_name${NC}: Stage name"
    echo -e "  • ${CYAN}log_level${NC}: Log level filter"
    echo ""
    echo -e "${BOLD}Example - Get Job Logs:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/logs-and-reports \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"action\": \"get_job_logs\",${NC}"
    echo -e "${CYAN}    \"journey_id\": \"JRN-SAMPLE-001\",${NC}"
    echo -e "${CYAN}    \"job_id\": \"JOB-12345\"${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
}

get_test_runner_details() {
    echo -e "${BOLD}🧪 test-runner Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Comprehensive tool validation testing for all MCP tools"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/test-runner${NC}"
    echo ""
    echo -e "${BOLD}Test Types:${NC}"
    echo -e "  • ${CYAN}quick${NC} - Basic functionality tests (faster execution)"
    echo -e "  • ${CYAN}comprehensive${NC} - Full test suite including all validation tests"
    echo -e "  • ${CYAN}imports${NC} - Import verification tests only"
    echo -e "  • ${CYAN}validation${NC} - Parameter validation tests only"
    echo -e "  • ${CYAN}performance${NC} - Performance and timing tests only"
    echo ""
    echo -e "${BOLD}Parameters:${NC}"
    echo -e "  • ${CYAN}test_type${NC} (optional): Type of tests to run (default: 'quick')"
    echo -e "  • ${CYAN}include_performance${NC} (optional): Include performance timing (default: false)"
    echo ""
    echo -e "${BOLD}Example Request:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/test-runner \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"test_type\": \"comprehensive\",${NC}"
    echo -e "${CYAN}    \"include_performance\": true${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
    echo -e "${BOLD}Response Format:${NC}"
    echo -e "  • ${CYAN}status${NC}: Overall test status"
    echo -e "  • ${CYAN}tests_passed${NC}: Number of tests passed"
    echo -e "  • ${CYAN}tests_failed${NC}: Number of tests failed"
    echo -e "  • ${CYAN}success_rate${NC}: Success percentage"
    echo -e "  • ${CYAN}test_results${NC}: Detailed test results array"
    echo ""
}

get_get_job_logs_details() {
    echo -e "${BOLD}📋 get-job-logs Tool${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Description:${NC}"
    echo -e "  Retrieve detailed execution logs (legacy compatibility)"
    echo ""
    echo -e "${BOLD}Endpoint:${NC} ${CYAN}$TOOLS_ENDPOINT/get-job-logs${NC}"
    echo ""
    echo -e "${BOLD}Parameters:${NC}"
    echo -e "  • ${CYAN}journey_id${NC} (required): Journey ID"
    echo -e "  • ${CYAN}job_id${NC} (required): Job ID"
    echo -e "  • ${CYAN}stage_name${NC} (optional): Filter by stage name"
    echo -e "  • ${CYAN}log_level${NC} (optional): Filter by log level"
    echo ""
    echo -e "${BOLD}Example Request:${NC}"
    echo -e "${CYAN}curl -X POST $TOOLS_ENDPOINT/get-job-logs \\${NC}"
    echo -e "${CYAN}  -H 'Content-Type: application/json' \\${NC}"
    echo -e "${CYAN}  -d '{${NC}"
    echo -e "${CYAN}    \"journey_id\": \"JRN-SAMPLE-001\",${NC}"
    echo -e "${CYAN}    \"job_id\": \"JOB-12345\"${NC}"
    echo -e "${CYAN}  }'${NC}"
    echo ""
    echo -e "${YELLOW}💡 Note: For new applications, consider using 'logs-and-reports' tool instead${NC}"
    echo ""
}

test_tool_endpoint() {
    local tool_name="$1"
    local endpoint_url="$TOOLS_ENDPOINT/$tool_name"
    
    echo -e "${BLUE}🧪 Testing $tool_name endpoint...${NC}"
    
    # Test with OPTIONS method to check if endpoint exists
    local response=$(curl -s -X OPTIONS "$endpoint_url" \
        --connect-timeout 5 \
        --max-time 10 \
        -w "%{http_code}" \
        2>/dev/null || echo "000")
    
    if [[ "$response" =~ [0-9]{3}$ ]]; then
        local http_code="${response: -3}"
        if [ "$http_code" != "000" ] && [ "$http_code" != "404" ]; then
            print_success "Endpoint is accessible (HTTP $http_code)"
        else
            print_warning "Endpoint not found or not accessible (HTTP $http_code)"
        fi
    else
        print_warning "Unable to test endpoint connectivity"
    fi
    echo ""
}

show_tool_details() {
    local tool_name="$1"
    
    case "$tool_name" in
        "raw-analysis")
            get_raw_analysis_details
            test_tool_endpoint "$tool_name"
            ;;
        "stripped-schema")
            get_stripped_schema_details
            test_tool_endpoint "$tool_name"
            ;;
        "run-jobs")
            get_run_jobs_details
            test_tool_endpoint "$tool_name"
            ;;
        "journeys")
            get_journeys_details
            test_tool_endpoint "$tool_name"
            ;;
        "logs-and-reports")
            get_logs_and_reports_details
            test_tool_endpoint "$tool_name"
            ;;
        "test-runner")
            get_test_runner_details
            test_tool_endpoint "$tool_name"
            ;;
        "get-job-logs")
            get_get_job_logs_details
            test_tool_endpoint "$tool_name"
            ;;
        "all")
            get_raw_analysis_details
            echo ""
            get_stripped_schema_details
            echo ""
            get_run_jobs_details
            echo ""
            get_journeys_details
            echo ""
            get_logs_and_reports_details
            echo ""
            get_test_runner_details
            echo ""
            get_get_job_logs_details
            ;;
        *)
            print_error "Unknown tool: $tool_name"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main() {
    local tool_name="${1:-}"
    
    if [ -z "$tool_name" ]; then
        print_header "TMF ODA TRANSFORMER MCP TOOLS - USAGE"
        show_usage
        exit 1
    fi
    
    print_header "TMF ODA TRANSFORMER MCP TOOL DETAILS"
    
    echo -e "${BLUE}🔍 Tool Details for: ${BOLD}$tool_name${NC}"
    echo -e "${BLUE}Server URL: $SERVER_URL${NC}"
    echo -e "${BLUE}Generated: $(date)${NC}"
    echo ""
    
    show_tool_details "$tool_name"
    
    if [ "$tool_name" != "all" ]; then
        echo ""
        print_header "ADDITIONAL INFORMATION"
        
        echo -e "${CYAN}📚 Related Scripts:${NC}"
        echo -e "  • ${CYAN}./list_all_tools.sh${NC} - List all available tools"
        echo -e "  • ${CYAN}./show_tool_parameters.sh${NC} - Show parameter details for all tools"
        echo -e "  • ${CYAN}./test_tool_availability.sh${NC} - Test tool accessibility"
        echo ""
        
        echo -e "${YELLOW}💡 Quick Test Command:${NC}"
        echo -e "  ${CYAN}curl -X POST $TOOLS_ENDPOINT/$tool_name -H 'Content-Type: application/json' -d '{}'${NC}"
    fi
    
    echo ""
}

# Run main function
main "$@" 