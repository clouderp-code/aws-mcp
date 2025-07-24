FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy the application code
COPY awslabs/ ./awslabs/
COPY README.md LICENSE NOTICE ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import awslabs.call_analysis_mcp_server; print('OK')" || exit 1

# Expose port (if needed for HTTP interface)
EXPOSE 8000

# Default command
CMD ["python", "-m", "awslabs.call_analysis_mcp_server.server"] 