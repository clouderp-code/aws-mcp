# TMF ODA Transformer MCP Server - AWS ECS Fargate Deployment

This directory contains comprehensive deployment automation for deploying the TMF ODA Transformer MCP Server to AWS ECS Fargate with Application Load Balancer.

## 🏗️ Architecture Overview

The deployment creates the following AWS resources:

- **ECS Fargate Cluster**: Serverless container hosting
- **Application Load Balancer (ALB)**: Internet-facing load balancer
- **Target Group**: Health checks and traffic routing
- **Security Groups**: Network security for ALB and ECS tasks
- **IAM Roles**: Task execution and application permissions
- **CloudWatch Logs**: Application logging
- **ECR Repository**: Docker image storage (optional)
- **Route53 Record**: Custom domain support (optional)

## 📋 Prerequisites

### Required Tools
- **AWS CLI v2**: For AWS resource management
- **Docker**: For building and pushing images (if using `--build-image`)
- **bash**: Unix shell for running deployment scripts
- **curl**: For testing deployments
- **jq**: JSON processing (recommended but optional)

### AWS Permissions
Your AWS credentials need permissions for:
- CloudFormation (full access)
- ECS (full access)
- EC2 (VPC, subnets, security groups)
- IAM (role creation and management)
- ElasticLoadBalancingV2 (ALB management)
- CloudWatch Logs
- ECR (if building images)
- Route53 (if using custom domains)

### AWS Resources (Required)
You need existing AWS resources:
- **VPC**: Where resources will be deployed
- **Public Subnets**: At least 2 in different AZs for ALB
- **Private Subnets**: At least 2 in different AZs for ECS tasks
- **SSL Certificate**: From ACM (optional, for HTTPS)
- **Route53 Hosted Zone**: (optional, for custom domains)

## 🚀 Quick Start

### 1. Setup Configuration

```bash
# Navigate to deployment directory
cd /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server/deploy

# Copy configuration template
cp config.env.example config.env

# Edit configuration with your AWS resource IDs
nano config.env
```

### 2. Configure Your Environment

Edit `config.env` with your specific values:

```bash
# Required: Your AWS VPC and subnet IDs
VPC_ID=vpc-0123456789abcdef0
PUBLIC_SUBNETS=subnet-0123456789abcdef0,subnet-0fedcba9876543210
PRIVATE_SUBNETS=subnet-0abcdef1234567890,subnet-0987654321fedcba0

# Optional: Customize deployment
PROJECT_NAME=tmf-oda-mcp
ENVIRONMENT=dev
REGION=us-east-2
DESIRED_COUNT=2
BUILD_IMAGE=true
```

### 3. Deploy

```bash
# Deploy with configuration file
./deploy-with-config.sh

# OR deploy with direct parameters
./deploy.sh --vpc-id vpc-xxx --public-subnets subnet-xxx,subnet-yyy --private-subnets subnet-aaa,subnet-bbb --build-image
```

### 4. Test Deployment

The deployment automatically tests the service. You can also manually test:

```bash
# Get the service URL from deployment output
SERVICE_URL="http://your-alb-dns-name"

# Test health endpoint
curl $SERVICE_URL/health

# Test tools endpoint
curl $SERVICE_URL/tools

# Run comprehensive tests
python3 ../test-http-access.py --url $SERVICE_URL
```

## 📁 File Structure

```
deploy/
├── README.md                      # This documentation
├── cloudformation-template.yaml   # AWS CloudFormation template
├── deploy.sh                      # Main deployment script
├── deploy-with-config.sh          # Configuration-based deployment
├── config.env.example             # Configuration template
└── deployment-outputs.json        # Generated after deployment
```

## 🔧 Deployment Scripts

### Main Deployment Script (`deploy.sh`)

Full-featured deployment script with comprehensive options:

```bash
./deploy.sh [OPTIONS]

# Key options:
--vpc-id VPC_ID                 # Required: VPC for deployment
--public-subnets SUBNETS        # Required: Public subnets for ALB
--private-subnets SUBNETS       # Required: Private subnets for ECS
--build-image                   # Build and push Docker image to ECR
--enable-https                  # Enable HTTPS with SSL certificate
--update                        # Update existing deployment
--dry-run                       # Show what would be deployed
--rollback                      # Rollback failed deployment
```

### Configuration-Based Deployment (`deploy-with-config.sh`)

Simplified deployment using configuration file:

```bash
# Use default config.env
./deploy-with-config.sh

# Use custom config file
./deploy-with-config.sh production.env

# Override config with additional options
./deploy-with-config.sh config.env --desired-count 3 --update
```

## ⚙️ Configuration Options

### Basic Configuration

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `PROJECT_NAME` | Project name for resource naming | `tmf-oda-mcp` | No |
| `ENVIRONMENT` | Environment (dev/staging/prod) | `dev` | No |
| `REGION` | AWS region | `us-east-2` | No |
| `VPC_ID` | VPC ID for deployment | - | **Yes** |
| `PUBLIC_SUBNETS` | Public subnet IDs (comma-separated) | - | **Yes** |
| `PRIVATE_SUBNETS` | Private subnet IDs (comma-separated) | - | **Yes** |

### Container Configuration

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `IMAGE_TAG` | Docker image tag | `latest` | Any tag |
| `DESIRED_COUNT` | Number of ECS tasks | `2` | 1-100 |
| `TASK_CPU` | CPU units for tasks | `512` | 256, 512, 1024, 2048, 4096 |
| `TASK_MEMORY` | Memory in MB | `1024` | 512-8192 |

### HTTPS Configuration

| Parameter | Description | Default | Required for HTTPS |
|-----------|-------------|---------|-------------------|
| `ENABLE_HTTPS` | Enable HTTPS listener | `false` | - |
| `CERTIFICATE_ARN` | SSL certificate ARN | - | **Yes** (if HTTPS) |
| `DOMAIN_NAME` | Custom domain name | - | No |

### Deployment Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `BUILD_IMAGE` | Build and push image to ECR | `false` |
| `SKIP_TESTS` | Skip post-deployment tests | `false` |
| `UPDATE_STACK` | Update existing stack | `false` |

## 🌍 Environment Examples

### Development Environment

```bash
# config.env for development
PROJECT_NAME=tmf-oda-mcp
ENVIRONMENT=dev
REGION=us-east-2
VPC_ID=vpc-dev123
PUBLIC_SUBNETS=subnet-devpub1,subnet-devpub2
PRIVATE_SUBNETS=subnet-devpriv1,subnet-devpriv2
DESIRED_COUNT=1
TASK_CPU=256
TASK_MEMORY=512
BUILD_IMAGE=true
ENABLE_HTTPS=false
```

### Production Environment

```bash
# config.env for production
PROJECT_NAME=tmf-oda-mcp
ENVIRONMENT=prod
REGION=us-west-2
VPC_ID=vpc-prod456
PUBLIC_SUBNETS=subnet-prodpub1,subnet-prodpub2
PRIVATE_SUBNETS=subnet-prodpriv1,subnet-prodpriv2
DESIRED_COUNT=3
TASK_CPU=1024
TASK_MEMORY=2048
BUILD_IMAGE=true
ENABLE_HTTPS=true
CERTIFICATE_ARN=arn:aws:acm:us-west-2:123456789012:certificate/abcd1234-...
DOMAIN_NAME=api.example.com
```

## 🔄 Common Operations

### Initial Deployment

```bash
# 1. Configure environment
cp config.env.example config.env
# Edit config.env with your values

# 2. Deploy
./deploy-with-config.sh
```

### Update Existing Deployment

```bash
# Update with new image
./deploy-with-config.sh --build-image --update

# Scale service
./deploy-with-config.sh --desired-count 5 --update

# Update configuration
# Edit config.env, then:
./deploy-with-config.sh --update
```

### Enable HTTPS

```bash
# 1. Request SSL certificate in AWS Certificate Manager
aws acm request-certificate --domain-name api.example.com

# 2. Update config.env
ENABLE_HTTPS=true
CERTIFICATE_ARN=arn:aws:acm:region:account:certificate/cert-id
DOMAIN_NAME=api.example.com

# 3. Update deployment
./deploy-with-config.sh --update
```

### Monitoring and Troubleshooting

```bash
# View CloudFormation stack
aws cloudformation describe-stacks --stack-name tmf-oda-mcp-dev

# View ECS service status
aws ecs describe-services --cluster tmf-oda-mcp-dev-cluster --services tmf-oda-mcp-dev-service

# View application logs
aws logs tail /ecs/tmf-oda-mcp-dev --follow

# Check load balancer health
aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names tmf-oda-mcp-dev-tg --query 'TargetGroups[0].TargetGroupArn' --output text)
```

### Rollback Deployment

```bash
# Automatic rollback for failed updates
./deploy.sh --rollback

# Manual rollback via CloudFormation
aws cloudformation cancel-update-stack --stack-name tmf-oda-mcp-dev
```

### Cleanup/Deletion

```bash
# Delete CloudFormation stack (removes all resources)
aws cloudformation delete-stack --stack-name tmf-oda-mcp-dev

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name tmf-oda-mcp-dev
```

## 🔐 Security Considerations

### IAM Permissions
The deployment creates IAM roles with minimal required permissions:
- **Task Execution Role**: Pull images, write logs
- **Task Role**: Access DynamoDB, S3, CloudWatch for application functionality

### Network Security
- **ECS tasks** run in private subnets (no direct internet access)
- **Load balancer** in public subnets accepts internet traffic
- **Security groups** restrict traffic to necessary ports only
- **HTTPS** recommended for production deployments

### Data Security
- Application connects to DynamoDB and S3 with IAM roles
- CloudWatch logs retention configurable (default: 30 days)
- Container images stored in private ECR repositories

## 📊 Monitoring and Observability

### CloudWatch Integration
- **Application logs**: `/ecs/tmf-oda-mcp-{environment}`
- **Container insights**: Enabled for detailed metrics
- **Health checks**: ALB monitors application health

### Metrics Available
- ECS task CPU and memory utilization
- Load balancer request metrics
- Application response times
- Error rates and status codes

### Alerting Setup (Manual)
Consider setting up CloudWatch alarms for:
- High CPU/memory usage
- Failed health checks
- High error rates
- Response time degradation

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check ECS service events
aws ecs describe-services --cluster CLUSTER_NAME --services SERVICE_NAME

# Check task definition and logs
aws logs tail /ecs/PROJECT-ENVIRONMENT --since 1h
```

#### 2. Health Check Failures
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn TARGET_GROUP_ARN

# Test health endpoint directly (if accessible)
curl http://task-ip:8000/health
```

#### 3. Image Pull Errors
- Verify ECR repository exists and image is pushed
- Check task execution role has ECR permissions
- Ensure image URI is correct in task definition

#### 4. Network Connectivity Issues
- Verify security group rules
- Check subnet routing tables
- Ensure NAT Gateway for private subnets (if accessing internet)

### Debug Commands

```bash
# Get detailed stack events
aws cloudformation describe-stack-events --stack-name STACK_NAME

# Connect to running task (if enabled)
aws ecs execute-command --cluster CLUSTER_NAME --task TASK_ARN --interactive --command "/bin/bash"

# View detailed service configuration
aws ecs describe-services --cluster CLUSTER_NAME --services SERVICE_NAME --query 'services[0]'
```

## 🔗 Related Documentation

- [AWS ECS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/userguide/what-is-fargate.html)
- [Application Load Balancer Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [TMF ODA Transformer MCP Server Documentation](../README.md)

## 🤝 Support

For deployment issues:
1. Check this README for common solutions
2. Review CloudFormation stack events
3. Check ECS service events and logs
4. Verify AWS resource configurations
5. Test with `--dry-run` to validate parameters

## 📝 Notes

- **First deployment** takes 5-10 minutes
- **Updates** typically take 2-5 minutes
- **ECR repositories** are created automatically when using `--build-image`
- **SSL certificates** must be in the same region as the deployment
- **Custom domains** require Route53 hosted zone management
- **Costs** depend on instance size, count, and data transfer 