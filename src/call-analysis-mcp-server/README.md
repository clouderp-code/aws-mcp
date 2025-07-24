# Call Analysis MCP Server

An AWS Labs Model Context Protocol (MCP) server that provides comprehensive tools for analyzing call transcripts stored in S3 and generating detailed analysis reports with KPIs, sentiment analysis, compliance metrics, and performance indicators.

## Overview

This MCP server enables AI assistants to process call transcripts from S3 buckets, perform sophisticated natural language analysis, and generate actionable insights for improving customer service operations. It provides automated analysis of conversation quality, agent performance, compliance adherence, and customer satisfaction.

## ✨ Features

- **📞 Transcript Processing**: Read and parse call transcripts from S3 in multiple formats (TXT, JSON, CSV, TSV)
- **🎭 Sentiment Analysis**: Comprehensive sentiment analysis for overall call, agent, and customer perspectives
- **📊 Performance KPIs**: Generate key performance indicators including customer satisfaction, agent professionalism, and efficiency metrics
- **✅ Compliance Monitoring**: Automated compliance checking for required disclosures, privacy protocols, and regulatory requirements
- **🗂️ Topic Extraction**: Identify and categorize key conversation topics and themes
- **📈 Conversation Flow Analysis**: Analyze turn-taking patterns, opening/closing quality, and conversation structure
- **📋 Batch Processing**: Process multiple transcripts simultaneously with comparative analysis
- **📱 Interactive Dashboards**: Generate HTML dashboards for visualization and reporting
- **☁️ S3 Integration**: Seamless reading from and writing to Amazon S3 buckets
- **🔒 AWS Security**: Built-in AWS credential handling and secure operations

## 🛠️ Tools

### 📞 analyze_transcript
Analyze a single call transcript from S3 and generate comprehensive analysis with KPIs.

**Parameters:**
- `s3_bucket` *(required)*: S3 bucket containing the transcript file
- `s3_key` *(required)*: S3 key path to the transcript file
- `output_bucket` *(required)*: S3 bucket for output files
- `output_prefix` *(optional)*: Prefix for output files
- `analysis_options` *(optional)*: Dictionary of analysis options to enable/disable
- `aws_region` *(optional)*: AWS region for S3 operations (default: us-east-1)

**Returns:** Analysis results with output file locations and summary metrics

**Example Usage:**
```
Analyze the call transcript at s3://my-transcripts/call_001.txt and save results to s3://my-analysis/
```

### 📊 analyze_transcript_batch
Analyze multiple call transcripts from an S3 folder and generate batch analysis report.

**Parameters:**
- `s3_bucket` *(required)*: S3 bucket containing transcript files
- `s3_prefix` *(required)*: S3 prefix/folder path containing transcripts
- `output_bucket` *(required)*: S3 bucket for output files
- `output_prefix` *(optional)*: Prefix for output files (default: batch_analysis)
- `max_files` *(optional)*: Maximum number of files to process (default: 100)
- `analysis_options` *(optional)*: Dictionary of analysis options
- `aws_region` *(optional)*: AWS region for S3 operations

**Returns:** Batch analysis results with individual and summary reports

### 📁 list_s3_transcripts
List and examine transcript files in an S3 bucket/prefix.

**Parameters:**
- `s3_bucket` *(required)*: S3 bucket name
- `s3_prefix` *(optional)*: S3 prefix/folder path
- `max_files` *(optional)*: Maximum number of files to list (default: 50)
- `aws_region` *(optional)*: AWS region

**Returns:** List of transcript files with metadata

### ⬆️ upload_analysis_results
Upload analysis content directly to S3.

**Parameters:**
- `content` *(required)*: Content to upload
- `s3_bucket` *(required)*: S3 bucket name
- `s3_key` *(required)*: S3 key for the file
- `content_type` *(optional)*: MIME type (default: application/json)
- `aws_region` *(optional)*: AWS region

### 📋 generate_analysis_report
Generate comprehensive reports from multiple analysis results.

**Parameters:**
- `analysis_s3_urls` *(required)*: List of S3 URLs containing analysis JSON files
- `report_type` *(optional)*: Type of report (executive_summary, detailed, comparison)
- `output_bucket` *(required)*: S3 bucket for output report
- `output_key` *(required)*: S3 key for output report
- `aws_region` *(optional)*: AWS region

### 📱 create_analysis_dashboard
Create interactive HTML dashboard from analysis results.

**Parameters:**
- `analysis_s3_urls` *(required)*: List of S3 URLs containing analysis JSON files
- `dashboard_title` *(optional)*: Title for the dashboard
- `output_bucket` *(required)*: S3 bucket for output dashboard
- `output_key` *(optional)*: S3 key for output dashboard (default: dashboard.html)
- `aws_region` *(optional)*: AWS region

## 📋 Analysis Output

The server generates two main output files for each analyzed call:

### analysis.json
Complete structured analysis data including:
- **Call Characteristics**: Duration, talk time ratios, word counts, speaking rates
- **Sentiment Analysis**: Overall, agent, and customer sentiment with confidence scores
- **Performance KPIs**: Customer satisfaction, agent professionalism, resolution metrics
- **Compliance Metrics**: Required disclosures, privacy compliance, escalation protocols
- **Conversation Flow**: Turn-taking patterns, opening/closing quality scores
- **Key Topics**: Primary themes, named entities, business intent
- **Recommendations**: Actionable insights for improvement
- **Action Items**: Specific follow-up tasks identified

### analysis.md
Human-readable markdown report with:
- Executive summary of the call
- Key metrics dashboard
- Conversation analysis highlights
- Compliance assessment
- Performance recommendations
- Visual indicators for quick assessment

## 🔧 Installation

### Prerequisites

- Python 3.10 or higher
- AWS credentials configured (AWS CLI, IAM roles, or environment variables)
- Access to S3 buckets for reading transcripts and writing results

### Setup

1. **Clone and navigate to the server directory:**
   ```bash
   cd /opt/mycode/aws-mcp/src/call-analysis-mcp-server
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Configure AWS credentials** (one of the following):
   ```bash
   # Using AWS CLI
   aws configure
   
   # Using environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   
   # Using IAM roles (recommended for EC2/ECS)
   # No additional configuration needed
   ```

4. **Run the server:**
   ```bash
   python -m awslabs.call_analysis_mcp_server.server
   ```

## 🎯 Usage Examples

### Single Call Analysis
```
analyze_transcript(
    s3_bucket="my-call-transcripts",
    s3_key="calls/2024/01/call_12345.txt",
    output_bucket="my-analysis-results",
    output_prefix="analyzed/2024/01"
)
```

### Batch Analysis
```
analyze_transcript_batch(
    s3_bucket="my-call-transcripts", 
    s3_prefix="calls/2024/01/",
    output_bucket="my-analysis-results",
    output_prefix="batch_jan_2024",
    max_files=50
)
```

### Create Dashboard
```
create_analysis_dashboard(
    analysis_s3_urls=[
        "s3://my-analysis-results/call_001_analysis.json",
        "s3://my-analysis-results/call_002_analysis.json"
    ],
    dashboard_title="January 2024 Call Analysis",
    output_bucket="my-dashboards",
    output_key="jan_2024_dashboard.html"
)
```

## 📊 Supported Transcript Formats

### JSON Format
```json
[
    {
        "timestamp": 0.0,
        "speaker": "agent",
        "text": "Thank you for calling customer service...",
        "duration": 3.5,
        "confidence": 0.95
    },
    {
        "timestamp": 3.5,
        "speaker": "customer", 
        "text": "Hi, I need help with my account",
        "duration": 2.8,
        "confidence": 0.92
    }
]
```

### CSV/TSV Format
```csv
timestamp,speaker,text,duration,confidence
0.0,agent,"Thank you for calling customer service",3.5,0.95
3.5,customer,"Hi, I need help with my account",2.8,0.92
```

### Plain Text Format
```
Agent: Thank you for calling customer service. How can I help you today?
Customer: Hi, I need help with my account. I can't log in.
Agent: I'd be happy to help you with that. Can you provide your account number?
```

## 📈 Analysis Metrics

### Customer Satisfaction Indicators
- Overall satisfaction score (0-10)
- Sentiment analysis (positive/negative/neutral)
- First call resolution detection
- Issue escalation tracking

### Agent Performance Metrics
- Professionalism score
- Empathy demonstration
- Knowledge assessment
- Communication clarity
- Active listening indicators

### Compliance Monitoring
- Required disclosure verification
- Privacy protocol adherence
- Hold time appropriateness
- Escalation procedures
- Security compliance

### Conversation Quality
- Opening and closing quality scores
- Turn-taking analysis
- Interruption patterns
- Speaking rate assessment
- Silence and pause analysis

## 🔧 Configuration

### Environment Variables

- `AWS_REGION`: AWS region for S3 operations (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use for credentials
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Analysis Options

Customize analysis by passing `analysis_options` dictionary:

```python
analysis_options = {
    "sentiment_analysis": True,      # Enable sentiment analysis
    "topic_extraction": True,        # Enable topic extraction  
    "compliance_check": True,        # Enable compliance monitoring
    "performance_metrics": True,     # Enable performance KPIs
    "detailed_flow_analysis": True   # Enable conversation flow analysis
}
```

## 🏗️ Architecture

The server is organized into modular components:

```
awslabs/call_analysis_mcp_server/
├── server.py              # Main MCP server entry point
├── models.py               # Pydantic data models
├── consts.py              # Configuration constants
├── tools/                 # MCP tool implementations
│   ├── analysis_tools.py  # Core analysis tools
│   ├── s3_tools.py       # S3 operation tools
│   └── reporting_tools.py # Report generation tools
├── services/              # Business logic services
│   ├── s3_service.py     # S3 integration service
│   ├── transcript_analyzer.py  # NLP analysis engine
│   └── report_generator.py     # Report generation service
└── utils/                 # Utility functions
```

## 🔒 Security Considerations

- **AWS Credentials**: Use IAM roles when possible, avoid hardcoded credentials
- **S3 Permissions**: Ensure proper bucket policies and access controls
- **Data Privacy**: Consider encryption at rest and in transit for sensitive call data
- **Access Logging**: Enable CloudTrail for audit trails of S3 operations
- **Network Security**: Use VPC endpoints for S3 access when appropriate

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=awslabs.call_analysis_mcp_server

# Run specific test categories
pytest -m "not live"  # Skip tests requiring AWS resources
```

## 🔍 Troubleshooting

### Common Issues

**AWS Credentials Not Found**
```
Solution: Configure AWS credentials using aws configure or environment variables
```

**S3 Access Denied**
```
Solution: Verify bucket permissions and IAM policies allow s3:GetObject and s3:PutObject
```

**Large File Processing**
```
Solution: Files larger than 100MB are skipped. Consider splitting large transcripts
```

**Memory Issues with Batch Processing**
```
Solution: Reduce max_files parameter or process in smaller batches
```

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python -m awslabs.call_analysis_mcp_server.server
```

## 📚 API Reference

Detailed API documentation is available in the source code docstrings. Key classes:

- `CallAnalysisResult`: Complete analysis output model
- `TranscriptAnalyzer`: Core NLP analysis engine  
- `S3Service`: S3 operations wrapper
- `ReportGenerator`: Report and dashboard creation

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation and examples
- Review troubleshooting section above

---

*Built with ❤️ by AWS Labs for the Model Context Protocol ecosystem* 