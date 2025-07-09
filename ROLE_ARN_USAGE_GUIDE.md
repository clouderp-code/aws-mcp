# TMF ODA Transformer Role ARN Usage Guide

This guide explains how to use the TMF ODA Transformer system from outside AWS by assuming an IAM role.

## Overview

The TMF ODA Transformer system now supports two deployment scenarios:

1. **EC2 Instance** - Uses instance roles (original functionality)
2. **External Machines** - Uses role ARN assumption (new functionality)

## Prerequisites for External Machines

### 1. AWS Credentials

You need AWS credentials that can assume the target role. Set them using one of these methods:

```bash
# Option 1: AWS Profile
export AWS_PROFILE="your-profile-name"

# Option 2: Environment Variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # Optional

# Option 3: AWS CLI Default Profile
aws configure
```

### 2. IAM Role Setup

Create an IAM role with the following trust policy to allow your credentials to assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR-ACCOUNT:user/YOUR-USERNAME"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Attach this permission policy to the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/TransformationSystem*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::transformation-journey-logs",
        "arn:aws:s3:::transformation-journey-logs/*",
        "arn:aws:s3:::transformation-journey-reports",
        "arn:aws:s3:::transformation-journey-reports/*"
      ]
    }
  ]
}
```

## Configuration Examples

### 1. MCP Server Configuration

Configure your MCP server to use role ARN:

```json
{
  "mcpServers": {
    "awslabs.tmf-oda-transformer-mcp-server": {
      "command": "uvx", 
      "args": ["awslabs.tmf-oda-transformer-mcp-server@latest"],
      "env": {
        "AWS_ROLE_ARN": "arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 2. Command Line Usage

Set the environment variable and run commands:

```bash
# Set the role ARN
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole"
export AWS_REGION="us-east-1"

# Run setup scripts
cd scripts
python setup_dynamodb.py

# Run transformation jobs
python job_executor.py --journey-id JRN-SAMPLE-001 --stage-id raw_analysis

# Test the role ARN functionality
python test_role_arn.py --role-arn $AWS_ROLE_ARN --region $AWS_REGION
```

## Testing the Setup

### 1. Basic Role ARN Test

```bash
cd scripts
python test_role_arn.py --role-arn "arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole" --region us-east-1
```

### 2. Setup Infrastructure

```bash
# Test and setup DynamoDB and S3
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole"
python setup_dynamodb.py
```

### 3. Test MCP Tools

Start your MCP server with the role ARN configuration and test:

```bash
# Test raw analysis tool
mcp_awslabs_tmf-oda-transformer-mcp-server_raw-analysis journey_id=JRN-SAMPLE-001

# Test stripped schema tool
mcp_awslabs_tmf-oda-transformer-mcp-server_stripped-schema journey_id=JRN-SAMPLE-001

# Test job logs retrieval
mcp_awslabs_tmf-oda-transformer-mcp-server_get-job-logs journey_id=JRN-SAMPLE-001 stage_name=raw_analysis job_id=JOB-001-20250101120000 step_name=schema_parsing
```

## Troubleshooting

### Common Issues

1. **Role Assumption Failed**
   ```
   Error: Role assumption failed: AccessDenied - User: arn:aws:iam::123456789012:user/username is not authorized to perform: sts:AssumeRole
   ```
   - Check that your user has permission to assume the role
   - Verify the role's trust policy includes your user/credentials

2. **DynamoDB Access Denied**
   ```
   Error: User: arn:aws:sts::123456789012:assumed-role/TMF-ODA-TransformerRole/TMF-ODA-Transformer-20250101120000 is not authorized to perform: dynamodb:PutItem
   ```
   - Check that the role has the required DynamoDB permissions
   - Verify the resource ARN matches your table name

3. **S3 Access Denied**
   ```
   Error: Access Denied when uploading to S3
   ```
   - Check that the role has the required S3 permissions
   - Verify the bucket names exist and are accessible

### Debug Mode

Enable verbose logging to see detailed role assumption information:

```bash
# Set debug logging
export FASTMCP_LOG_LEVEL="DEBUG"

# Run with verbose output
python test_role_arn.py --role-arn "arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole" --verbose
```

## Migration from Instance Roles

If you're migrating from EC2 instance roles to external machines:

1. **No code changes required** - The system automatically detects the configuration
2. **Environment variables** - Add `AWS_ROLE_ARN` to your environment
3. **Remove AWS_PROFILE** - If you were using profiles, you can remove them
4. **Test thoroughly** - Use the test script to validate functionality

## Advanced Usage

### Role Chaining

You can chain roles if needed:

```bash
# First assume a role that can assume the target role
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/IntermediateRole"

# Then configure the final role in your application
export FINAL_ROLE_ARN="arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole"
```

### Region-Specific Roles

Use different roles for different regions:

```bash
# US East
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole-US-East"
export AWS_REGION="us-east-1"

# EU West
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/TMF-ODA-TransformerRole-EU-West"
export AWS_REGION="eu-west-1"
```

## Security Best Practices

1. **Least Privilege** - Only grant the minimum permissions required
2. **Role Session Duration** - Use short-lived sessions (default 1 hour)
3. **MFA Requirement** - Consider requiring MFA for role assumption
4. **Regular Rotation** - Rotate credentials regularly
5. **Audit Logging** - Enable CloudTrail to audit role assumptions

## Support

For issues with role ARN functionality:

1. Run the test script with `--verbose` flag
2. Check the AWS CloudTrail logs for role assumption events
3. Verify your IAM permissions and trust policies
4. Test with AWS CLI: `aws sts assume-role --role-arn YOUR_ROLE_ARN --role-session-name test` 