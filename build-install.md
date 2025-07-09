# Set Up Development Environment

## Install prerequisites
pip install uv pre-commit

## Install Python 3.12+ if needed
uv python install 3.12.3

## Install pre-commit hooks
pre-commit install

# Install Dependencies

## Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Unix/macOS

## Install the package in development mode
uv pip install -e ".[dev]"
uv pip install -e .
uv pip install -e . --group dev

# Check Your Installation
## Check if the package is installed
python -c "import awslabs.tmf_oda_transformer_mcp_server; print('Package installed successfully')"

## Check if dev tools are available
pytest --version
ruff --version

# Run the Server from Source

## Direct Python execution
python -m awslabs.mysql_mcp_server.server --resource_arn <Your Resource ARN> --secret_arn <Your Secret ARN> --database <Your Database> --region <Your Region> --readonly True

## Using UV to run directly
uv --directory /path/to/mysql-mcp-server/awslabs/mysql_mcp_server run server.py --resource_arn <Your Resource ARN> --secret_arn <Your Secret ARN> --database <Your Database> --region <Your Region> --readonly True

## Using the installed entry point
awslabs.mysql-mcp-server --resource_arn <Your Resource ARN> --secret_arn <Your Secret ARN> --database <Your Database> --region <Your Region> --readonly True

# Testing Your Changes

## Run tests

uv run pytest
uv run --frozen pytest --cov --cov-branch --cov-report=term-missing
## Test the server manually
cd /opt/mycode/aws-mcp/src/tmf-oda-transformer-mcp-server
python -m awslabs.tmf_oda_transformer_mcp_server.server

## Use MCP Inspector for debugging
npx @modelcontextprotocol/inspector \
  uv \
  --directory /absolute/path/to/mcp/src/mysql-mcp-server/awslabs/mysql_mcp_server \
  run \
  server.py
