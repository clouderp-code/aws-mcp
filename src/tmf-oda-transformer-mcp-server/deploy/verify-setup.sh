#!/bin/bash

# TMF ODA Transformer MCP Server - Deployment Setup Verification
# This script verifies that all deployment files are in place and provides next steps

set -e

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

print_warning() {
    print_color $YELLOW "⚠️ $1"
}

print_info() {
    print_color $CYAN "ℹ️ $1"
}

print_header() {
    echo ""
    print_color $BLUE "============================================================"
    print_color $BLUE "🎯 $1"
    print_color $BLUE "============================================================"
}

# Function to check file existence and permissions
check_file() {
    local file_path="$1"
    local description="$2"
    local required="$3"
    
    if [ -f "$file_path" ]; then
        if [ -x "$file_path" ]; then
            print_success "$description (executable)"
        else
            print_success "$description"
        fi
        return 0
    else
        if [ "$required" = "true" ]; then
            print_error "$description - FILE MISSING"
            return 1
        else
            print_warning "$description - Optional file missing"
            return 0
        fi
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local all_good=true
    
    # Check AWS CLI
    if command -v aws &> /dev/null; then
        local aws_version=$(aws --version 2>&1 | cut -d/ -f2 | cut -d' ' -f1)
        print_success "AWS CLI installed (version: $aws_version)"
        
        # Check AWS credentials
        if aws sts get-caller-identity &> /dev/null; then
            local account_id=$(aws sts get-caller-identity --query Account --output text)
            local region=$(aws configure get region || echo "not configured")
            print_success "AWS credentials configured (Account: $account_id, Region: $region)"
        else
            print_error "AWS credentials not configured or expired"
            all_good=false
        fi
    else
        print_error "AWS CLI not installed"
        all_good=false
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker installed"
        if docker info &> /dev/null; then
            print_success "Docker daemon running"
        else
            print_warning "Docker daemon not running (required for --build-image)"
        fi
    else
        print_warning "Docker not installed (required for --build-image)"
    fi
    
    # Check other tools
    if command -v jq &> /dev/null; then
        print_success "jq installed"
    else
        print_warning "jq not installed (recommended for JSON parsing)"
    fi
    
    if command -v curl &> /dev/null; then
        print_success "curl installed"
    else
        print_warning "curl not installed (required for deployment testing)"
    fi
    
    return $all_good
}

# Function to verify deployment files
verify_deployment_files() {
    print_header "Verifying Deployment Files"
    
    local all_good=true
    
    # Check required files
    check_file "$SCRIPT_DIR/cloudformation-template.yaml" "CloudFormation template" "true" || all_good=false
    check_file "$SCRIPT_DIR/deploy.sh" "Main deployment script" "true" || all_good=false
    check_file "$SCRIPT_DIR/deploy-with-config.sh" "Configuration-based deployment script" "true" || all_good=false
    check_file "$SCRIPT_DIR/config.env.example" "Configuration template" "true" || all_good=false
    check_file "$SCRIPT_DIR/README.md" "Documentation" "true" || all_good=false
    
    # Check optional files
    check_file "$SCRIPT_DIR/config.env" "Configuration file" "false"
    check_file "$SCRIPT_DIR/deployment-outputs.json" "Deployment outputs" "false"
    
    return $all_good
}

# Function to show next steps
show_next_steps() {
    print_header "Next Steps for Deployment"
    
    print_info "To deploy the TMF ODA MCP Server to AWS ECS Fargate:"
    echo ""
    
    print_color $YELLOW "1. Configure Your Environment"
    print_info "   Copy the configuration template:"
    print_color $NC "   cd $SCRIPT_DIR"
    print_color $NC "   cp config.env.example config.env"
    echo ""
    print_info "   Edit config.env with your AWS resource IDs:"
    print_color $NC "   nano config.env"
    echo ""
    print_warning "   Required values to configure:"
    print_info "   - VPC_ID: Your VPC ID (vpc-xxxxxxxxx)"
    print_info "   - PUBLIC_SUBNETS: Public subnet IDs for ALB (comma-separated)"
    print_info "   - PRIVATE_SUBNETS: Private subnet IDs for ECS tasks (comma-separated)"
    echo ""
    
    print_color $YELLOW "2. Deploy the Service"
    print_info "   Option A - Using configuration file (recommended):"
    print_color $NC "   ./deploy-with-config.sh"
    echo ""
    print_info "   Option B - Using command line parameters:"
    print_color $NC "   ./deploy.sh --vpc-id vpc-xxx --public-subnets subnet-xxx,subnet-yyy \\"
    print_color $NC "             --private-subnets subnet-aaa,subnet-bbb --build-image"
    echo ""
    
    print_color $YELLOW "3. Test the Deployment"
    print_info "   After deployment completes, test the service:"
    print_color $NC "   curl http://your-alb-dns-name/health"
    print_color $NC "   python3 ../test-http-access.py --url http://your-alb-dns-name"
    echo ""
    
    print_color $YELLOW "4. Common Operations"
    print_info "   Update deployment:"
    print_color $NC "   ./deploy-with-config.sh --update"
    echo ""
    print_info "   Scale service:"
    print_color $NC "   ./deploy-with-config.sh --desired-count 3 --update"
    echo ""
    print_info "   Enable HTTPS (with SSL certificate):"
    print_color $NC "   # Edit config.env to set ENABLE_HTTPS=true and CERTIFICATE_ARN"
    print_color $NC "   ./deploy-with-config.sh --update"
    echo ""
    
    print_color $YELLOW "5. Monitoring and Management"
    print_info "   View logs:"
    print_color $NC "   aws logs tail /ecs/tmf-oda-mcp-dev --follow"
    echo ""
    print_info "   Check service status:"
    print_color $NC "   aws ecs describe-services --cluster tmf-oda-mcp-dev-cluster --services tmf-oda-mcp-dev-service"
    echo ""
    
    print_color $YELLOW "6. Cleanup (when needed)"
    print_info "   Delete the deployment:"
    print_color $NC "   aws cloudformation delete-stack --stack-name tmf-oda-mcp-dev"
}

# Function to show resource requirements
show_resource_requirements() {
    print_header "AWS Resource Requirements"
    
    print_warning "Before deploying, ensure you have these AWS resources:"
    echo ""
    
    print_info "Required Resources:"
    print_info "🌐 VPC: A VPC where resources will be deployed"
    print_info "🔗 Public Subnets: At least 2 in different AZs (for Application Load Balancer)"
    print_info "🔒 Private Subnets: At least 2 in different AZs (for ECS tasks)"
    echo ""
    
    print_info "Optional Resources (for advanced features):"
    print_info "🔐 SSL Certificate: From AWS Certificate Manager (for HTTPS)"
    print_info "🌍 Route53 Hosted Zone: For custom domain names"
    echo ""
    
    print_info "How to find your resource IDs:"
    print_color $NC "# List VPCs"
    print_color $NC "aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,Tags[?Key==\`Name\`].Value|[0]]' --output table"
    echo ""
    print_color $NC "# List subnets in a VPC"
    print_color $NC "aws ec2 describe-subnets --filters 'Name=vpc-id,Values=vpc-xxxxxxxxx' \\"
    print_color $NC "  --query 'Subnets[*].[SubnetId,AvailabilityZone,CidrBlock,Tags[?Key==\`Name\`].Value|[0]]' --output table"
    echo ""
    print_color $NC "# List SSL certificates"
    print_color $NC "aws acm list-certificates --query 'CertificateSummaryList[*].[CertificateArn,DomainName]' --output table"
}

# Function to estimate costs
show_cost_estimate() {
    print_header "Estimated AWS Costs"
    
    print_info "Monthly cost estimates for different configurations:"
    echo ""
    
    print_color $YELLOW "💰 Development Environment (1 task, 256 CPU, 512 MB):"
    print_info "   ECS Fargate: ~$10-15/month"
    print_info "   Application Load Balancer: ~$16/month"
    print_info "   CloudWatch Logs: ~$1-5/month"
    print_info "   Total: ~$27-36/month"
    echo ""
    
    print_color $YELLOW "💰 Production Environment (3 tasks, 1024 CPU, 2048 MB):"
    print_info "   ECS Fargate: ~$90-120/month"
    print_info "   Application Load Balancer: ~$16/month"
    print_info "   CloudWatch Logs: ~$5-15/month"
    print_info "   Total: ~$111-151/month"
    echo ""
    
    print_warning "Note: Costs may vary based on:"
    print_info "   - Data transfer (inbound/outbound)"
    print_info "   - Log retention and volume"
    print_info "   - Additional AWS services usage"
    print_info "   - Regional pricing differences"
}

# Main function
main() {
    print_color $PURPLE "🚀 TMF ODA Transformer MCP Server - Deployment Setup Verification"
    print_color $PURPLE "================================================================"
    
    local overall_status=true
    
    # Check prerequisites
    if ! check_prerequisites; then
        overall_status=false
    fi
    
    # Verify deployment files
    if ! verify_deployment_files; then
        overall_status=false
    fi
    
    # Show resource requirements
    show_resource_requirements
    
    # Show cost estimates
    show_cost_estimate
    
    # Show next steps
    show_next_steps
    
    # Final status
    print_header "Setup Verification Complete"
    
    if [ "$overall_status" = true ]; then
        print_success "🎉 Deployment setup is ready!"
        print_success "All required files are in place and prerequisites are met."
        print_info "Follow the Next Steps above to deploy your TMF ODA MCP Server."
    else
        print_error "⚠️ Setup has issues that need to be resolved."
        print_info "Please address the errors above before proceeding with deployment."
    fi
    
    echo ""
    print_info "📚 For detailed documentation, see: README.md"
    print_info "🆘 For help: ./deploy.sh --help"
}

# Run main function
main "$@" 