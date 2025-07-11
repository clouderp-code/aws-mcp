#!/bin/bash

# TMF ODA Transformer MCP Server - Deployment with Configuration File
# This script loads configuration from config.env and executes the deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_success() {
    print_color $GREEN "✅ $1"
}

print_error() {
    print_color $RED "❌ $1"
}

print_info() {
    print_color $BLUE "ℹ️ $1"
}

# Function to show usage
show_usage() {
    cat << EOF
TMF ODA Transformer MCP Server - Deployment with Configuration File

Usage: $0 [CONFIG_FILE] [ADDITIONAL_OPTIONS]

ARGUMENTS:
    CONFIG_FILE         Path to configuration file (default: config.env)

ADDITIONAL_OPTIONS:
    Any additional options will be passed to deploy.sh and override config file values

EXAMPLES:
    # Deploy using default config.env
    $0

    # Deploy using custom config file
    $0 production.env

    # Deploy with config file and override specific options
    $0 config.env --desired-count 3 --update

    # Deploy with config file and enable dry-run
    $0 config.env --dry-run

SETUP:
    1. Copy config.env.example to config.env
    2. Edit config.env with your AWS resource IDs
    3. Run this script: $0

EOF
}

# Function to load configuration
load_configuration() {
    local config_file="$1"
    
    if [ ! -f "$config_file" ]; then
        print_error "Configuration file not found: $config_file"
        print_info "Please copy config.env.example to $config_file and customize it"
        exit 1
    fi
    
    print_info "Loading configuration from: $config_file"
    
    # Source the configuration file
    set -a  # Automatically export all variables
    source "$config_file"
    set +a  # Stop auto-exporting
    
    print_success "Configuration loaded successfully"
    
    # Validate required configuration
    local missing_config=false
    
    if [ -z "$VPC_ID" ]; then
        print_error "VPC_ID is required in configuration"
        missing_config=true
    fi
    
    if [ -z "$PUBLIC_SUBNETS" ]; then
        print_error "PUBLIC_SUBNETS is required in configuration"
        missing_config=true
    fi
    
    if [ -z "$PRIVATE_SUBNETS" ]; then
        print_error "PRIVATE_SUBNETS is required in configuration"
        missing_config=true
    fi
    
    if [ "$missing_config" = true ]; then
        print_error "Required configuration values are missing"
        print_info "Please check your configuration file: $config_file"
        exit 1
    fi
    
    print_success "Configuration validation passed"
}

# Function to build deploy command
build_deploy_command() {
    local deploy_cmd="$SCRIPT_DIR/deploy.sh"
    
    # Add configuration parameters
    [ -n "$PROJECT_NAME" ] && deploy_cmd="$deploy_cmd --project-name '$PROJECT_NAME'"
    [ -n "$ENVIRONMENT" ] && deploy_cmd="$deploy_cmd --environment '$ENVIRONMENT'"
    [ -n "$REGION" ] && deploy_cmd="$deploy_cmd --region '$REGION'"
    [ -n "$VPC_ID" ] && deploy_cmd="$deploy_cmd --vpc-id '$VPC_ID'"
    [ -n "$PUBLIC_SUBNETS" ] && deploy_cmd="$deploy_cmd --public-subnets '$PUBLIC_SUBNETS'"
    [ -n "$PRIVATE_SUBNETS" ] && deploy_cmd="$deploy_cmd --private-subnets '$PRIVATE_SUBNETS'"
    [ -n "$IMAGE_TAG" ] && deploy_cmd="$deploy_cmd --image-tag '$IMAGE_TAG'"
    [ -n "$DESIRED_COUNT" ] && deploy_cmd="$deploy_cmd --desired-count '$DESIRED_COUNT'"
    [ -n "$TASK_CPU" ] && deploy_cmd="$deploy_cmd --task-cpu '$TASK_CPU'"
    [ -n "$TASK_MEMORY" ] && deploy_cmd="$deploy_cmd --task-memory '$TASK_MEMORY'"
    [ -n "$CERTIFICATE_ARN" ] && deploy_cmd="$deploy_cmd --certificate-arn '$CERTIFICATE_ARN'"
    [ -n "$DOMAIN_NAME" ] && deploy_cmd="$deploy_cmd --domain-name '$DOMAIN_NAME'"
    
    # Add boolean flags
    [ "$ENABLE_HTTPS" = "true" ] && deploy_cmd="$deploy_cmd --enable-https"
    [ "$BUILD_IMAGE" = "true" ] && deploy_cmd="$deploy_cmd --build-image"
    [ "$SKIP_TESTS" = "true" ] && deploy_cmd="$deploy_cmd --skip-tests"
    [ "$UPDATE_STACK" = "true" ] && deploy_cmd="$deploy_cmd --update"
    
    echo "$deploy_cmd"
}

# Main execution
main() {
    print_color $BLUE "🚀 TMF ODA Transformer MCP Server - Deployment with Configuration"
    print_color $BLUE "================================================================"
    
    # Default config file
    local config_file="$SCRIPT_DIR/config.env"
    
    # Check if first argument is help
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    # If first argument doesn't start with '-', treat it as config file
    if [ $# -gt 0 ] && [[ "$1" != -* ]]; then
        config_file="$1"
        shift  # Remove config file from arguments
    fi
    
    # Load configuration
    load_configuration "$config_file"
    
    # Build deploy command
    local deploy_cmd
    deploy_cmd=$(build_deploy_command)
    
    # Add any additional command line arguments
    if [ $# -gt 0 ]; then
        deploy_cmd="$deploy_cmd $*"
        print_info "Additional options: $*"
    fi
    
    # Show configuration summary
    print_info "Deployment Configuration:"
    print_info "  Project: $PROJECT_NAME"
    print_info "  Environment: $ENVIRONMENT"
    print_info "  Region: $REGION"
    print_info "  VPC: $VPC_ID"
    print_info "  Public Subnets: $PUBLIC_SUBNETS"
    print_info "  Private Subnets: $PRIVATE_SUBNETS"
    print_info "  Image Tag: $IMAGE_TAG"
    print_info "  Desired Count: $DESIRED_COUNT"
    print_info "  CPU: $TASK_CPU, Memory: $TASK_MEMORY"
    [ "$ENABLE_HTTPS" = "true" ] && print_info "  HTTPS: Enabled"
    [ "$BUILD_IMAGE" = "true" ] && print_info "  Build Image: Yes"
    
    echo ""
    print_info "Executing deployment command..."
    
    # Make deploy.sh executable
    chmod +x "$SCRIPT_DIR/deploy.sh"
    
    # Execute the deployment
    eval "$deploy_cmd"
}

# Run main function with all arguments
main "$@" 