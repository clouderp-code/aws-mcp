#!/bin/bash

echo "🚀 TMF ODA Transformer MCP Server - Direct Test Execution"
echo "============================================================="

# Set up paths
PROJECT_ROOT="/opt/mycode/aws-mcp"
SERVER_DIR="$PROJECT_ROOT/src/tmf-oda-transformer-mcp-server"
VENV_PATH="$PROJECT_ROOT/venv"

echo "📁 Project Root: $PROJECT_ROOT"
echo "📁 Server Directory: $SERVER_DIR"
echo "📁 Virtual Environment: $VENV_PATH"
echo ""

# Function to check if virtual environment exists
check_venv() {
    if [ -d "$VENV_PATH" ]; then
        echo "✅ Virtual environment found"
        return 0
    else
        echo "❌ Virtual environment not found at $VENV_PATH"
        return 1
    fi
}

# Function to create virtual environment if needed
create_venv() {
    echo "🔧 Creating virtual environment..."
    cd "$PROJECT_ROOT"
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully"
        return 0
    else
        echo "❌ Failed to create virtual environment"
        return 1
    fi
}

# Function to activate virtual environment and install dependencies
setup_environment() {
    echo "🔧 Setting up environment..."
    source "$VENV_PATH/bin/activate"
    
    # Install basic dependencies
    pip install --quiet pydantic loguru boto3 botocore
    
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully"
        return 0
    else
        echo "❌ Failed to install dependencies"
        return 1
    fi
}

# Function to run the quick test
run_quick_test() {
    echo "🧪 Running Quick Test..."
    cd "$SERVER_DIR"
    source "$VENV_PATH/bin/activate"
    
    python3 quick_test.py
    return $?
}

# Function to run comprehensive verification
run_verification() {
    echo "🔍 Running Comprehensive Verification..."
    cd "$SERVER_DIR"
    source "$VENV_PATH/bin/activate"
    
    python3 verify_tools.py
    return $?
}

# Function to check file structure
check_structure() {
    echo "📋 Checking File Structure..."
    
    files_to_check=(
        "$SERVER_DIR/awslabs/tmf_oda_transformer_mcp_server/server.py"
        "$SERVER_DIR/awslabs/tmf_oda_transformer_mcp_server/models.py"
        "$SERVER_DIR/awslabs/tmf_oda_transformer_mcp_server/consts.py"
        "$SERVER_DIR/awslabs/tmf_oda_transformer_mcp_server/scripts/__init__.py"
        "$SERVER_DIR/awslabs/tmf_oda_transformer_mcp_server/scripts/job_executor.py"
        "$SERVER_DIR/tests/conftest.py"
        "$SERVER_DIR/tests/test_schema_analyzer.py"
        "$SERVER_DIR/verify_tools.py"
        "$SERVER_DIR/quick_test.py"
    )
    
    missing_files=()
    for file in "${files_to_check[@]}"; do
        if [ -f "$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (MISSING)"
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "✅ All files found!"
        return 0
    else
        echo "❌ ${#missing_files[@]} file(s) missing"
        return 1
    fi
}

# Function to test Python imports
test_imports() {
    echo "📦 Testing Python Imports..."
    cd "$SERVER_DIR"
    source "$VENV_PATH/bin/activate"
    
    python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))

try:
    print('  Testing server imports...')
    from awslabs.tmf_oda_transformer_mcp_server.server import schema_analyzer_tool
    print('  ✅ Server imports successful')
    
    print('  Testing model imports...')
    from awslabs.tmf_oda_transformer_mcp_server.models import TMFODAComponentType
    print('  ✅ Model imports successful')
    
    print('  Testing script imports...')
    from awslabs.tmf_oda_transformer_mcp_server.scripts import TransformationJobExecutor
    print('  ✅ Script imports successful')
    
    print('✅ All imports successful!')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"
    return $?
}

# Main execution
main() {
    echo "🚀 Starting TMF ODA MCP Server Tests..."
    echo ""
    
    # Check/create virtual environment
    if ! check_venv; then
        if ! create_venv; then
            echo "❌ Cannot proceed without virtual environment"
            exit 1
        fi
    fi
    
    # Setup environment
    if ! setup_environment; then
        echo "❌ Environment setup failed"
        exit 1
    fi
    
    echo ""
    echo "=" * 50
    echo "🧪 RUNNING TESTS"
    echo "=" * 50
    
    # Run tests
    tests_passed=0
    total_tests=4
    
    echo ""
    echo "Test 1/4: File Structure Check"
    if check_structure; then
        ((tests_passed++))
    fi
    
    echo ""
    echo "Test 2/4: Python Imports"
    if test_imports; then
        ((tests_passed++))
    fi
    
    echo ""
    echo "Test 3/4: Quick Test"
    if run_quick_test; then
        ((tests_passed++))
    fi
    
    echo ""
    echo "Test 4/4: Comprehensive Verification"
    if run_verification; then
        ((tests_passed++))
    fi
    
    # Summary
    echo ""
    echo "=" * 50
    echo "🎯 FINAL SUMMARY"
    echo "=" * 50
    echo "Tests passed: $tests_passed/$total_tests"
    echo "Success rate: $(( tests_passed * 100 / total_tests ))%"
    
    if [ $tests_passed -eq $total_tests ]; then
        echo ""
        echo "🎉 ALL TESTS PASSED!"
        echo "✅ TMF ODA Transformer MCP Server is fully functional!"
        exit 0
    else
        echo ""
        echo "⚠️  Some tests failed. Check the output above for details."
        exit 1
    fi
}

# Make sure we're in the right directory
cd "$PROJECT_ROOT" || {
    echo "❌ Cannot access project directory: $PROJECT_ROOT"
    exit 1
}

# Run main function
main "$@" 