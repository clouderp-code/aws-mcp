# Environment Configuration Guide

The TMF ODA Transformer now supports configuration via `.env` files for easier and more secure credential management.

## Credential Priority Order

The system automatically detects and uses credentials in this priority order:

1. **Instance Role** (EC2/ECS/Lambda) - Automatically detected
2. **Environment Variables** - Manually set in shell
3. **Role ARN Assumption** - From environment variables or .env file  
4. **AWS Profile** - From .env file or environment
5. **Default Credential Chain** - AWS CLI, environment, instance metadata

## Setting up .env Configuration

### Step 1: Install Dependencies

```bash
pip install python-dotenv
# OR install all script dependencies:
pip install -r scripts/requirements.txt
```

### Step 2: Create .env File

Copy the template and customize:

```bash
cp scripts/aws-config.template .env
# Edit .env with your settings
```

### Step 3: Configure for Your Environment

#### For EC2 Instances (Instance Roles)
```env
AWS_REGION=us-east-1
# Leave AWS_ROLE_ARN commented out - instance role will be used automatically
```

#### For External Machines (Role ARN)
```env
AWS_REGION=us-east-1
AWS_ROLE_ARN=arn:aws:iam::764119721991:role/AssumableExternalAccessRole
```

#### For Development (AWS Profiles)
```env
AWS_REGION=us-east-1
AWS_PROFILE=myprofile
```

## File Locations

The system searches for `.env` files in this order:
1. Current directory: `./.env`
2. Scripts directory: `./scripts/.env`
3. Parent directory: `../.env`
4. Project root: `/opt/mycode/aws-mcp/.env`

## Usage Examples

### Using .env file (recommended)
```bash
# Create .env file with your settings
echo "AWS_REGION=us-east-1" > .env
echo "AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ROLE" >> .env

# Run commands - settings loaded automatically
python3 scripts/manage-transformation.py list
```

### Using environment variables (temporary)
```bash
# Set for current session only
export AWS_REGION=us-east-1
export AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ROLE

python3 scripts/manage-transformation.py list
```

### Override via command line
```bash
# Environment variables override .env settings
AWS_REGION=us-west-2 python3 scripts/manage-transformation.py list
```

## Security Notes

- **Never commit .env files to version control**
- Use `.env` for local development only
- For production, prefer environment variables or instance roles
- Role ARN credentials are cached for 1 hour and auto-renewed

## Troubleshooting

### "python-dotenv not found"
```bash
pip install python-dotenv
```

### "Region not set"
```bash
# Add to .env file:
echo "AWS_REGION=us-east-1" >> .env
```

### "Role assumption failed"
- Verify your AWS credentials have permission to assume the role
- Check that the role ARN is correct
- Ensure the role's trust policy allows your account/user

### "ResourceNotFoundException"
- Verify the AWS region matches where your DynamoDB table exists
- Check that the role has permissions to access DynamoDB and S3 