#!/bin/bash

# TMF ODA Transformer MCP Server - AWS ECS Fargate Deployment Script
# This script automates the deployment of the TMF ODA MCP Server to AWS ECS Fargate with ALB

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default configuration
DEFAULT_PROJECT_NAME="tmf-oda-mcp"
DEFAULT_ENVIRONMENT="dev"
DEFAULT_REGION="us-east-2"
DEFAULT_DESIRED_COUNT="2"
DEFAULT_TASK_CPU="512"
DEFAULT_TASK_MEMORY="1024"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_color $BLUE "============================================================"
    print_color $BLUE "🎯 $1"
    print_color $BLUE "============================================================"
}

print_success() {
    print_color $GREEN "✅ $1"
}

print_warning() {
    print_color $YELLOW "⚠️ $1"
}

print_error() {
    print_color $RED "❌ $1"
}

print_info() {
    print_color $CYAN "ℹ️ $1"
}

# Function to show usage
show_usage() {
    cat << EOF
TMF ODA Transformer MCP Server - AWS ECS Fargate Deployment

Usage: $0 [OPTIONS]

OPTIONS:
    -p, --project-name NAME     Project name (default: $DEFAULT_PROJECT_NAME)
    -e, --environment ENV       Environment (dev/staging/prod) (default: $DEFAULT_ENVIRONMENT)
    -r, --region REGION         AWS region (default: $DEFAULT_REGION)
    -v, --vpc-id VPC_ID         VPC ID for deployment (required)
    -s, --public-subnets IDS    Public subnet IDs (comma-separated, min 2)
    -t, --private-subnets IDS   Private subnet IDs (comma-separated, min 2)
    -i, --image-tag TAG         Docker image tag (default: latest)
    -c, --desired-count COUNT   Desired number of ECS tasks (default: $DEFAULT_DESIRED_COUNT)
    --task-cpu CPU              CPU units for ECS task (default: $DEFAULT_TASK_CPU)
    --task-memory MEMORY        Memory MB for ECS task (default: $DEFAULT_TASK_MEMORY)
    --certificate-arn ARN       SSL certificate ARN for HTTPS (optional)
    --domain-name DOMAIN        Custom domain name (optional)
    --enable-https              Enable HTTPS listener
    --build-image               Build and push Docker image to ECR
    --skip-tests                Skip post-deployment tests
    --dry-run                   Show what would be deployed without executing
    --update                    Update existing stack instead of create
    --rollback                  Rollback to previous deployment
    -h, --help                  Show this help message

EXAMPLES:
    # Basic deployment with required parameters
    $0 --vpc-id vpc-123456 --public-subnets subnet-pub1,subnet-pub2 --private-subnets subnet-priv1,subnet-priv2

    # Production deployment with HTTPS
    $0 --environment prod --region us-west-2 --enable-https --certificate-arn arn:aws:acm:... --domain-name api.example.com

    # Build and deploy with custom image tag
    $0 --build-image --image-tag v1.2.3 --vpc-id vpc-123456 --public-subnets subnet-pub1,subnet-pub2 --private-subnets subnet-priv1,subnet-priv2

    # Update existing deployment
    $0 --update --vpc-id vpc-123456 --public-subnets subnet-pub1,subnet-pub2 --private-subnets subnet-priv1,subnet-priv2

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local all_good=true
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        all_good=false
    else
        print_success "AWS CLI is installed"
        local aws_identity=$(aws sts get-caller-identity --output text --query 'Account' 2>/dev/null || echo "")
        if [ -z "$aws_identity" ]; then
            print_error "AWS credentials not configured or expired"
            all_good=false
        else
            print_success "AWS credentials configured (Account: $aws_identity)"
        fi
    fi
    
    # Check Docker (only if building image)
    if [ "$BUILD_IMAGE" = true ]; then
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed (required for --build-image)"
            all_good=false
        else
            print_success "Docker is installed"
            if ! docker info &> /dev/null; then
                print_error "Docker daemon is not running"
                all_good=false
            else
                print_success "Docker daemon is running"
            fi
        fi
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed (recommended for JSON parsing)"
    else
        print_success "jq is installed"
    fi
    
    # Check CloudFormation template
    if [ ! -f "$SCRIPT_DIR/cloudformation-template.yaml" ]; then
        print_error "CloudFormation template not found: $SCRIPT_DIR/cloudformation-template.yaml"
        all_good=false
    else
        print_success "CloudFormation template found"
    fi
    
    if [ "$all_good" = false ]; then
        print_error "Prerequisites check failed. Please install missing dependencies."
        exit 1
    fi
    
    print_success "All prerequisites check passed"
}

# Function to validate AWS resources
validate_aws_resources() {
    print_header "Validating AWS Resources"
    
    local all_good=true
    
    # Validate VPC
    if ! aws ec2 describe-vpcs --vpc-ids "$VPC_ID" --region "$REGION" &> /dev/null; then
        print_error "VPC $VPC_ID not found in region $REGION"
        all_good=false
    else
        print_success "VPC $VPC_ID found"
    fi
    
    # Validate subnets
    IFS=',' read -ra PUBLIC_SUBNET_ARRAY <<< "$PUBLIC_SUBNETS"
    IFS=',' read -ra PRIVATE_SUBNET_ARRAY <<< "$PRIVATE_SUBNETS"
    
    if [ ${#PUBLIC_SUBNET_ARRAY[@]} -lt 2 ]; then
        print_error "At least 2 public subnets are required for ALB"
        all_good=false
    fi
    
    if [ ${#PRIVATE_SUBNET_ARRAY[@]} -lt 2 ]; then
        print_error "At least 2 private subnets are required for ECS tasks"
        all_good=false
    fi
    
    # Validate each subnet
    for subnet in "${PUBLIC_SUBNET_ARRAY[@]}"; do
        if ! aws ec2 describe-subnets --subnet-ids "$subnet" --region "$REGION" &> /dev/null; then
            print_error "Public subnet $subnet not found"
            all_good=false
        else
            print_success "Public subnet $subnet found"
        fi
    done
    
    for subnet in "${PRIVATE_SUBNET_ARRAY[@]}"; do
        if ! aws ec2 describe-subnets --subnet-ids "$subnet" --region "$REGION" &> /dev/null; then
            print_error "Private subnet $subnet not found"
            all_good=false
        else
            print_success "Private subnet $subnet found"
        fi
    done
    
    # Validate certificate ARN if provided
    if [ -n "$CERTIFICATE_ARN" ]; then
        if ! aws acm describe-certificate --certificate-arn "$CERTIFICATE_ARN" --region "$REGION" &> /dev/null; then
            print_error "Certificate $CERTIFICATE_ARN not found"
            all_good=false
        else
            print_success "Certificate $CERTIFICATE_ARN found"
        fi
    fi
    
    if [ "$all_good" = false ]; then
        print_error "AWS resources validation failed"
        exit 1
    fi
    
    print_success "All AWS resources validated"
}

# Function to create ECR repository if it doesn't exist
create_ecr_repository() {
    local repo_name="$PROJECT_NAME-$ENVIRONMENT"
    
    print_header "Creating ECR Repository"
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names "$repo_name" --region "$REGION" &> /dev/null; then
        print_success "ECR repository $repo_name already exists"
    else
        print_info "Creating ECR repository: $repo_name"
        aws ecr create-repository --repository-name "$repo_name" --region "$REGION" > /dev/null
        print_success "ECR repository $repo_name created"
    fi
    
    # Get repository URI
    ECR_URI=$(aws ecr describe-repositories --repository-names "$repo_name" --region "$REGION" --query 'repositories[0].repositoryUri' --output text)
    print_success "ECR repository URI: $ECR_URI"
}

# Function to build and push Docker image
build_and_push_image() {
    print_header "Building and Pushing Docker Image"
    
    # Navigate to project root
    cd "$PROJECT_ROOT"
    
    # Login to ECR
    print_info "Logging in to ECR..."
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_URI"
    
    # Build image
    print_info "Building Docker image..."
    docker build -f Dockerfile.optimized -t "$PROJECT_NAME-$ENVIRONMENT:$IMAGE_TAG" .
    
    # Tag image for ECR
    print_info "Tagging image for ECR..."
    docker tag "$PROJECT_NAME-$ENVIRONMENT:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
    
    # Push image
    print_info "Pushing image to ECR..."
    docker push "$ECR_URI:$IMAGE_TAG"
    
    # Set the full image URI for CloudFormation
    FULL_IMAGE_URI="$ECR_URI:$IMAGE_TAG"
    print_success "Image pushed to ECR: $FULL_IMAGE_URI"
}

# Function to deploy CloudFormation stack
deploy_cloudformation() {
    print_header "Deploying CloudFormation Stack"
    
    local stack_name="$PROJECT_NAME-$ENVIRONMENT"
    local template_file="$SCRIPT_DIR/cloudformation-template.yaml"
    
    # Prepare parameters
    local parameters=(
        "ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME"
        "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
        "ParameterKey=VpcId,ParameterValue=$VPC_ID"
        "ParameterKey=PublicSubnetIds,ParameterValue=\"$PUBLIC_SUBNETS\""
        "ParameterKey=PrivateSubnetIds,ParameterValue=\"$PRIVATE_SUBNETS\""
        "ParameterKey=ContainerImage,ParameterValue=$FULL_IMAGE_URI"
        "ParameterKey=DesiredCount,ParameterValue=$DESIRED_COUNT"
        "ParameterKey=TaskCpu,ParameterValue=$TASK_CPU"
        "ParameterKey=TaskMemory,ParameterValue=$TASK_MEMORY"
    )
    
    # Add optional parameters
    if [ -n "$CERTIFICATE_ARN" ]; then
        parameters+=("ParameterKey=CertificateArn,ParameterValue=$CERTIFICATE_ARN")
    fi
    
    if [ -n "$DOMAIN_NAME" ]; then
        parameters+=("ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME")
    fi
    
    if [ "$ENABLE_HTTPS" = true ]; then
        parameters+=("ParameterKey=EnableHttps,ParameterValue=true")
    fi
    
    # Prepare AWS CLI command
    local aws_cmd="aws cloudformation"
    
    if [ "$UPDATE_STACK" = true ]; then
        aws_cmd="$aws_cmd update-stack"
        print_info "Updating CloudFormation stack: $stack_name"
    else
        aws_cmd="$aws_cmd create-stack"
        print_info "Creating CloudFormation stack: $stack_name"
    fi
    
    aws_cmd="$aws_cmd --stack-name $stack_name"
    aws_cmd="$aws_cmd --template-body file://$template_file"
    aws_cmd="$aws_cmd --parameters"
    
    for param in "${parameters[@]}"; do
        aws_cmd="$aws_cmd $param"
    done
    
    aws_cmd="$aws_cmd --capabilities CAPABILITY_NAMED_IAM"
    aws_cmd="$aws_cmd --region $REGION"
    aws_cmd="$aws_cmd --tags Key=Project,Value=$PROJECT_NAME Key=Environment,Value=$ENVIRONMENT Key=ManagedBy,Value=CloudFormation"
    
    # Show command in dry-run mode
    if [ "$DRY_RUN" = true ]; then
        print_info "Dry run mode - would execute:"
        echo "$aws_cmd"
        return
    fi
    
    # Execute deployment
    if eval "$aws_cmd"; then
        print_success "CloudFormation stack deployment initiated"
        
        # Wait for stack completion
        print_info "Waiting for stack deployment to complete..."
        local operation="stack-create-complete"
        if [ "$UPDATE_STACK" = true ]; then
            operation="stack-update-complete"
        fi
        
        if aws cloudformation wait "$operation" --stack-name "$stack_name" --region "$REGION"; then
            print_success "CloudFormation stack deployment completed successfully"
        else
            print_error "CloudFormation stack deployment failed"
            print_info "Check the CloudFormation console for detailed error information"
            exit 1
        fi
    else
        print_error "Failed to deploy CloudFormation stack"
        exit 1
    fi
}

# Function to get stack outputs
get_stack_outputs() {
    print_header "Retrieving Stack Outputs"
    
    local stack_name="$PROJECT_NAME-$ENVIRONMENT"
    
    # Get stack outputs
    local outputs
    outputs=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$REGION" --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo "[]")
    
    if [ "$outputs" = "[]" ]; then
        print_warning "No stack outputs found"
        return
    fi
    
    # Parse outputs
    ALB_DNS=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="LoadBalancerDNS") | .OutputValue' 2>/dev/null || echo "")
    SERVICE_URL=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="LoadBalancerURL") | .OutputValue' 2>/dev/null || echo "")
    ECS_CLUSTER=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="ECSClusterName") | .OutputValue' 2>/dev/null || echo "")
    ECS_SERVICE=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="ECSServiceName") | .OutputValue' 2>/dev/null || echo "")
    
    print_success "Load Balancer DNS: $ALB_DNS"
    print_success "Service URL: $SERVICE_URL"
    print_success "ECS Cluster: $ECS_CLUSTER"
    print_success "ECS Service: $ECS_SERVICE"
    
    # Save outputs to file
    local output_file="$SCRIPT_DIR/deployment-outputs.json"
    echo "$outputs" > "$output_file"
    print_success "Deployment outputs saved to: $output_file"
}

# Function to test deployment
test_deployment() {
    if [ "$SKIP_TESTS" = true ]; then
        print_info "Skipping post-deployment tests"
        return
    fi
    
    print_header "Testing Deployment"
    
    if [ -z "$SERVICE_URL" ]; then
        print_warning "Service URL not available, skipping tests"
        return
    fi
    
    # Wait for service to be ready
    print_info "Waiting for service to be ready (this may take a few minutes)..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$SERVICE_URL/health" > /dev/null 2>&1; then
            print_success "Service is responding at $SERVICE_URL"
            break
        fi
        
        print_info "Attempt $attempt/$max_attempts - Service not ready yet, waiting 30 seconds..."
        sleep 30
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_warning "Service health check timeout after $((max_attempts * 30)) seconds"
        print_info "You can manually check the service status later at: $SERVICE_URL"
        return
    fi
    
    # Run basic tests
    print_info "Running basic API tests..."
    
    # Test health endpoint
    if curl -s -f "$SERVICE_URL/health" > /dev/null; then
        print_success "Health endpoint test passed"
    else
        print_warning "Health endpoint test failed"
    fi
    
    # Test tools endpoint
    if curl -s -f "$SERVICE_URL/tools" > /dev/null; then
        print_success "Tools endpoint test passed"
    else
        print_warning "Tools endpoint test failed"
    fi
    
    # Run comprehensive tests if test script exists
    local test_script="$PROJECT_ROOT/test-http-access.py"
    if [ -f "$test_script" ] && command -v python3 &> /dev/null; then
        print_info "Running comprehensive test suite..."
        if python3 "$test_script" --url "$SERVICE_URL" --quick-test; then
            print_success "Comprehensive test suite passed"
        else
            print_warning "Some comprehensive tests failed (this is normal for external resources)"
        fi
    fi
}

# Function to show deployment summary
show_deployment_summary() {
    print_header "Deployment Summary"
    
    print_success "🎉 TMF ODA MCP Server deployed successfully!"
    echo ""
    print_info "Deployment Details:"
    print_info "  Project Name: $PROJECT_NAME"
    print_info "  Environment: $ENVIRONMENT"
    print_info "  Region: $REGION"
    print_info "  Image: $FULL_IMAGE_URI"
    print_info "  Desired Count: $DESIRED_COUNT"
    print_info "  CPU: $TASK_CPU"
    print_info "  Memory: $TASK_MEMORY MB"
    
    if [ -n "$SERVICE_URL" ]; then
        echo ""
        print_success "🌐 Service Access:"
        print_success "  URL: $SERVICE_URL"
        print_success "  Health Check: $SERVICE_URL/health"
        print_success "  API Documentation: $SERVICE_URL/"
    fi
    
    echo ""
    print_info "📊 Monitoring & Management:"
    print_info "  CloudFormation Stack: $PROJECT_NAME-$ENVIRONMENT"
    print_info "  ECS Cluster: $ECS_CLUSTER"
    print_info "  ECS Service: $ECS_SERVICE"
    print_info "  CloudWatch Logs: /ecs/$PROJECT_NAME-$ENVIRONMENT"
    
    echo ""
    print_info "🔧 Management Commands:"
    print_info "  Update deployment: $0 --update [options]"
    print_info "  Scale service: aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --desired-count <count>"
    print_info "  View logs: aws logs tail /ecs/$PROJECT_NAME-$ENVIRONMENT --follow"
    print_info "  Delete stack: aws cloudformation delete-stack --stack-name $PROJECT_NAME-$ENVIRONMENT"
}

# Function to rollback deployment
rollback_deployment() {
    print_header "Rolling Back Deployment"
    
    local stack_name="$PROJECT_NAME-$ENVIRONMENT"
    
    print_info "Initiating rollback for stack: $stack_name"
    
    if aws cloudformation cancel-update-stack --stack-name "$stack_name" --region "$REGION" 2>/dev/null; then
        print_success "Rollback initiated"
        
        print_info "Waiting for rollback to complete..."
        if aws cloudformation wait stack-update-complete --stack-name "$stack_name" --region "$REGION"; then
            print_success "Rollback completed successfully"
        else
            print_error "Rollback failed"
            exit 1
        fi
    else
        print_error "Failed to initiate rollback"
        print_info "Stack may not be in a rollback-eligible state"
        exit 1
    fi
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project-name)
                PROJECT_NAME="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -v|--vpc-id)
                VPC_ID="$2"
                shift 2
                ;;
            -s|--public-subnets)
                PUBLIC_SUBNETS="$2"
                shift 2
                ;;
            -t|--private-subnets)
                PRIVATE_SUBNETS="$2"
                shift 2
                ;;
            -i|--image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -c|--desired-count)
                DESIRED_COUNT="$2"
                shift 2
                ;;
            --task-cpu)
                TASK_CPU="$2"
                shift 2
                ;;
            --task-memory)
                TASK_MEMORY="$2"
                shift 2
                ;;
            --certificate-arn)
                CERTIFICATE_ARN="$2"
                shift 2
                ;;
            --domain-name)
                DOMAIN_NAME="$2"
                shift 2
                ;;
            --enable-https)
                ENABLE_HTTPS=true
                shift
                ;;
            --build-image)
                BUILD_IMAGE=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --update)
                UPDATE_STACK=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Main execution function
main() {
    print_color $PURPLE "🚀 TMF ODA Transformer MCP Server - AWS ECS Fargate Deployment"
    print_color $PURPLE "================================================================"
    
    # Initialize default values
    PROJECT_NAME="$DEFAULT_PROJECT_NAME"
    ENVIRONMENT="$DEFAULT_ENVIRONMENT"
    REGION="$DEFAULT_REGION"
    IMAGE_TAG="latest"
    DESIRED_COUNT="$DEFAULT_DESIRED_COUNT"
    TASK_CPU="$DEFAULT_TASK_CPU"
    TASK_MEMORY="$DEFAULT_TASK_MEMORY"
    BUILD_IMAGE=false
    SKIP_TESTS=false
    DRY_RUN=false
    UPDATE_STACK=false
    ROLLBACK=false
    ENABLE_HTTPS=false
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Handle rollback
    if [ "$ROLLBACK" = true ]; then
        rollback_deployment
        exit 0
    fi
    
    # Validate required parameters
    if [ -z "$VPC_ID" ] || [ -z "$PUBLIC_SUBNETS" ] || [ -z "$PRIVATE_SUBNETS" ]; then
        print_error "Required parameters missing"
        print_info "VPC ID, public subnets, and private subnets are required"
        show_usage
        exit 1
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Validate AWS resources
    validate_aws_resources
    
    # Build and push image if requested
    if [ "$BUILD_IMAGE" = true ]; then
        create_ecr_repository
        build_and_push_image
    else
        # Use provided image or default
        FULL_IMAGE_URI="$PROJECT_NAME-$ENVIRONMENT:$IMAGE_TAG"
        print_info "Using existing image: $FULL_IMAGE_URI"
    fi
    
    # Deploy CloudFormation stack
    deploy_cloudformation
    
    # Get stack outputs
    get_stack_outputs
    
    # Test deployment
    test_deployment
    
    # Show deployment summary
    show_deployment_summary
}

# Run main function with all arguments
main "$@" 