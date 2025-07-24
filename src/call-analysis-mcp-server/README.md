# Call Analysis MCP Server

An AWS Labs Model Context Protocol (MCP) server for comprehensive call transcript analysis and KPI generation. This server provides AI-powered analysis of customer service calls with full evidence trails for transparency and validation.

## 🎯 Overview

The Call Analysis MCP Server enables AI assistants to:
- Read call transcripts from S3 buckets
- Perform detailed sentiment and topic analysis  
- Generate compliance and performance KPIs
- Create comprehensive analysis reports in JSON and Markdown formats
- Upload analysis results back to S3 for UI display
- Batch process multiple transcripts
- Generate interactive dashboards
- **NEW: Provide full evidence trails for every business decision**

## ✨ Key Features

### Core Analysis Capabilities
- **Sentiment Analysis**: Multi-layered sentiment detection (overall, agent, customer)
- **Performance KPIs**: Customer satisfaction, agent professionalism, call efficiency
- **Compliance Monitoring**: Required disclosures, privacy adherence, escalation protocols
- **Topic Extraction**: Business intent, key themes, named entity recognition
- **Conversation Flow**: Turn-taking analysis, agenda adherence, communication quality

### Business Intelligence with Evidence Trails
- **Deal Risk Assessment**: Identify at-risk deals with supporting transcript evidence
- **Churn Prediction**: Early warning signals with exact customer quotes
- **Opportunity Detection**: Upsell/cross-sell signals with expansion indicators
- **Agent Training Needs**: Performance gaps with specific conversation examples
- **Pipeline Health**: Stage-by-stage analysis with conversion evidence
- **Objection Patterns**: Recurring objections with successful response examples
- **Quality Issues**: Technical and process problems with occurrence evidence

### Advanced Analytics
- **Batch Processing**: Analyze multiple calls simultaneously
- **Interactive Dashboards**: Web-based visualization with drill-down capabilities
- **Comparative Analysis**: Cross-call insights and trend identification
- **Evidence Validation**: Full transparency with confidence scoring

## 🔧 MCP Tools

### Core Analysis Tools

#### `analyze_transcript`
Analyze a single call transcript from S3 and generate comprehensive analysis.

**Parameters:**
- `s3_bucket` (string): S3 bucket containing the transcript file
- `s3_key` (string): S3 key path to the transcript file  
- `output_bucket` (string): S3 bucket for output files
- `output_prefix` (string, optional): Prefix for output files
- `analysis_options` (object, optional): Dictionary of analysis options
- `aws_region` (string, optional): AWS region (default: "us-east-1")

**Returns:** Analysis results with S3 URLs for JSON and Markdown outputs

#### `analyze_transcript_batch`
Analyze multiple call transcripts from an S3 folder.

**Parameters:**
- `s3_bucket` (string): S3 bucket containing transcript files
- `s3_prefix` (string): S3 prefix/folder path containing transcripts
- `output_bucket` (string): S3 bucket for output files
- `output_prefix` (string, optional): Prefix for output files
- `max_files` (integer, optional): Maximum number of files to process
- `analysis_options` (object, optional): Dictionary of analysis options
- `aws_region` (string, optional): AWS region

**Returns:** Batch analysis results with individual and summary reports

#### `generate_business_intelligence` ⭐ NEW
Generate business intelligence insights from call analysis results with full evidence trails.

**Parameters:**
- `analysis_s3_urls` (array): List of S3 URLs containing analysis JSON files
- `time_period` (string, optional): Description of time period analyzed
- `output_bucket` (string): S3 bucket for output business intelligence file
- `output_key` (string, optional): S3 key for output file
- `aws_region` (string, optional): AWS region

**Returns:** Business intelligence insights with supporting evidence from transcripts

### S3 Operations Tools

#### `list_s3_transcripts`
List and read transcript files from S3.

**Parameters:**
- `s3_bucket` (string): S3 bucket containing transcripts
- `s3_prefix` (string, optional): S3 prefix to filter files
- `max_files` (integer, optional): Maximum files to return
- `aws_region` (string, optional): AWS region

#### `upload_analysis_results`
Upload analysis results directly to S3.

**Parameters:**
- `content` (string): Analysis content to upload
- `s3_bucket` (string): Target S3 bucket
- `s3_key` (string): Target S3 key
- `content_type` (string, optional): MIME type
- `aws_region` (string, optional): AWS region

### Reporting Tools

#### `generate_analysis_report`
Generate comprehensive analysis reports from S3 analysis results.

**Parameters:**
- `analysis_s3_urls` (array): List of S3 URLs with analysis results
- `report_type` (string, optional): Type of report to generate
- `output_bucket` (string): S3 bucket for report output
- `output_key` (string): S3 key for report file
- `aws_region` (string, optional): AWS region

#### `create_analysis_dashboard`
Create interactive HTML dashboards from analysis results.

**Parameters:**
- `analysis_s3_urls` (array): List of S3 URLs with analysis results
- `dashboard_title` (string, optional): Dashboard title
- `output_bucket` (string): S3 bucket for dashboard output
- `output_key` (string): S3 key for dashboard HTML file
- `aws_region` (string, optional): AWS region

## 📊 Analysis Output Formats

### Individual Call Analysis (`analysis.json`)
```json
{
  "call_id": "CALL_20250121_001",
  "analysis_timestamp": "2025-01-21T10:30:00Z",
  "transcript_source": "s3://transcripts/call.txt",
  "characteristics": {
    "total_duration_seconds": 420,
    "agent_talk_ratio": 0.65,
    "customer_talk_ratio": 0.35
  },
  "sentiment_analysis": {
    "overall_sentiment": "positive",
    "customer_sentiment": "neutral",
    "agent_sentiment": "positive"
  },
  "performance_kpis": {
    "customer_satisfaction_score": 8.5,
    "agent_professionalism_score": 9.0,
    "compliance_score": 8.8
  }
}
```

### Business Intelligence with Evidence (`business_intelligence.json`) ⭐ NEW
```json
{
  "deals_at_risk": [
    {
      "account_name": "StarNet Solutions",
      "risk_factors": ["Price concerns raised"],
      "evidence": {
        "primary_evidence": [
          {
            "call_id": "CALL_20250721_001",
            "transcript_source": "s3://transcripts/starnet_call.txt",
            "speaker": "customer",
            "timestamp": 284.5,
            "evidence_text": "I'm concerned about the cost. This seems quite expensive.",
            "context": "Customer expressed price concerns",
            "confidence_score": 0.9
          }
        ],
        "confidence_level": 0.83,
        "analysis_methodology": "Analyzed customer sentiment and price objections"
      }
    }
  ],
  "evidence_summary": {
    "total_evidence_items": 45,
    "calls_with_evidence": 28,
    "analysis_confidence": 0.79
  }
}
```

### Human-Readable Report (`analysis.md`)
```markdown
# Call Analysis Report

## Executive Summary
- **Overall Quality Score**: 8.2/10
- **Customer Satisfaction**: 8.5/10
- **Compliance Score**: 8.8/10

## Key Findings
- Positive customer sentiment maintained throughout call
- Agent demonstrated strong product knowledge
- All required disclosures completed

## Evidence References
- Price concern at 4:44: "This seems quite expensive for what we're getting"
- Customer satisfaction at 6:23: "I appreciate your help with this"

## Recommendations
1. Address pricing objections with ROI analysis
2. Continue excellent customer service approach
```

## 🏗️ Architecture

```
call-analysis-mcp-server/
├── awslabs/call_analysis_mcp_server/
│   ├── server.py              # Main MCP server entry point
│   ├── models.py              # Pydantic data models with evidence support
│   ├── consts.py              # Configuration constants
│   ├── tools/                 # MCP tool implementations
│   │   ├── analysis_tools.py  # Core analysis tools
│   │   ├── s3_tools.py        # S3 operations
│   │   └── reporting_tools.py # Report generation
│   └── services/              # Business logic services
│       ├── s3_service.py      # S3 integration
│       ├── transcript_analyzer.py    # NLP analysis engine
│       ├── business_intelligence.py # BI insights with evidence
│       └── report_generator.py      # Report creation
```

## ⚡ Quick Start

```bash
# 1. Navigate to project directory
cd /opt/mycode/aws-mcp/src/call-analysis-mcp-server

# 2. Create virtual environment with uv
uv venv
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Download NLTK data
python -c "import nltk; nltk.download(['punkt', 'stopwords', 'vader_lexicon', 'averaged_perceptron_tagger'])"

# 5. Install package
uv pip install -e .

# 6. Test real analysis
python test_real_analysis.py
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) installed (`pip install uv`)
- AWS account with S3 access
- AWS credentials configured (AWS CLI, IAM roles, or environment variables)

### Installation

1. **Clone or navigate to the project directory**
```bash
cd /opt/mycode/aws-mcp/src/call-analysis-mcp-server
```

2. **Create and activate virtual environment with uv**
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# OR
.venv\Scripts\activate     # On Windows
```

3. **Install dependencies**

**Option A: Full Installation (Recommended)**
```bash
uv pip install -r requirements.txt
```

**Option B: Minimal Installation**
```bash
uv pip install -r requirements-minimal.txt
```

4. **Download NLTK data (required for text analysis)**
```bash
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords') 
nltk.download('vader_lexicon')
nltk.download('averaged_perceptron_tagger')
print('✅ NLTK data downloaded successfully!')
"
```

5. **Install the package in development mode**
```bash
uv pip install -e .
```

6. **Configure AWS credentials**
```bash
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 🧪 Testing Real Analysis

Verify the installation with real (non-mocked) analysis:

```bash
# Test real analysis capabilities
python test_real_analysis.py
```

This will:
- ✅ Process local script files with **real NLP analysis**
- ✅ Generate **real business intelligence** with evidence trails
- ✅ Create analysis reports with **actual sentiment analysis**
- ✅ Demonstrate **full transparency** with evidence extraction

### Running the Server

**Ensure your virtual environment is activated:**
```bash
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

**Standalone execution:**
```bash
python -m awslabs.call_analysis_mcp_server.server
```

**With custom configuration:**
```bash
export LOG_LEVEL=DEBUG
export AWS_REGION=us-west-2
python -m awslabs.call_analysis_mcp_server.server
```

**Deactivate virtual environment when done:**
```bash
deactivate
```

### Docker Support

**Build the image:**
```bash
docker build -t call-analysis-mcp-server .
```

**Run the container:**
```bash
docker run -e AWS_ACCESS_KEY_ID=your-key \
           -e AWS_SECRET_ACCESS_KEY=your-secret \
           -p 8000:8000 \
           call-analysis-mcp-server
```

## 📋 Usage Examples

### Single Call Analysis
```python
# Via MCP client
result = await client.call_tool(
    "analyze_transcript",
    s3_bucket="my-call-transcripts",
    s3_key="calls/2024/call_001.txt",
    output_bucket="my-analysis-results"
)
```

### Batch Analysis with Business Intelligence
```python
# 1. Process multiple calls
batch_result = await client.call_tool(
    "analyze_transcript_batch",
    s3_bucket="my-call-transcripts", 
    s3_prefix="calls/2024/january/",
    output_bucket="my-analysis-results",
    output_prefix="january_batch"
)

# 2. Generate business intelligence with evidence
bi_result = await client.call_tool(
    "generate_business_intelligence",
    analysis_s3_urls=[
        "s3://my-analysis-results/call_001_analysis.json",
        "s3://my-analysis-results/call_002_analysis.json",
        # ... more analysis files
    ],
    time_period="January 2024",
    output_bucket="my-bi-insights",
    output_key="january_business_intelligence.json"
)
```

### Dashboard Generation
```python
# Create interactive dashboard
dashboard_result = await client.call_tool(
    "create_analysis_dashboard",
    analysis_s3_urls=analysis_urls,
    dashboard_title="Q1 Call Analysis Dashboard",
    output_bucket="my-dashboards",
    output_key="q1_dashboard.html"
)
```

## 📁 Supported Transcript Formats

### JSON Format (Recommended)
```json
{
  "call_id": "CALL_001",
  "segments": [
    {
      "timestamp": 0.0,
      "speaker": "agent",
      "text": "Hello, thank you for calling support.",
      "duration": 3.5
    },
    {
      "timestamp": 3.5,
      "speaker": "customer", 
      "text": "Hi, I'm having an issue with my service.",
      "duration": 2.8
    }
  ]
}
```

### CSV/TSV Format
```csv
timestamp,speaker,text,duration
0.0,agent,"Hello, thank you for calling support.",3.5
3.5,customer,"Hi, I'm having an issue with my service.",2.8
```

### Plain Text Format
```
[00:00] Agent: Hello, thank you for calling support.
[00:03] Customer: Hi, I'm having an issue with my service.
[00:06] Agent: I'd be happy to help you with that.
```

## 📈 Analysis Metrics

### Performance KPIs
- **Customer Satisfaction Score** (0-10): Estimated based on language and sentiment
- **Agent Professionalism Score** (0-10): Professional language and behavior
- **Call Efficiency Score** (0-10): Issue resolution effectiveness
- **Compliance Score** (0-10): Adherence to required protocols

### Quality Metrics
- **Talk-to-Listen Ratio**: Agent vs customer speaking time
- **Interruption Frequency**: Speaker overlap analysis
- **Silence Duration**: Extended pauses and their impact
- **Speaking Rate**: Words per minute analysis

### Business Intelligence with Evidence ⭐ NEW
- **Deal Risk Indicators**: Specific quotes showing price concerns, competitor mentions
- **Churn Risk Signals**: Exact phrases indicating dissatisfaction or switching intent
- **Opportunity Signals**: Customer statements about expansion, upgrades, or growth
- **Training Needs**: Performance examples with improvement opportunities
- **Objection Patterns**: Common objections with successful response examples

## ⚙️ Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1                    # AWS region for S3 operations
AWS_PROFILE=default                     # AWS profile to use

# Server Configuration  
LOG_LEVEL=INFO                          # Logging level (DEBUG, INFO, WARN, ERROR)
MCP_SERVER_PORT=8000                    # Server port (default: varies)

# Analysis Configuration
DEFAULT_SENTIMENT_ANALYSIS=true         # Enable sentiment analysis
DEFAULT_TOPIC_EXTRACTION=true           # Enable topic extraction
DEFAULT_COMPLIANCE_CHECK=true           # Enable compliance monitoring
```

### Analysis Options
```python
analysis_options = {
    "sentiment_analysis": True,          # Analyze emotional tone
    "topic_extraction": True,            # Extract key themes
    "compliance_check": True,            # Monitor compliance
    "performance_metrics": True,         # Calculate KPIs
    "detailed_flow_analysis": True,      # Analyze conversation flow
    "evidence_collection": True         # NEW: Collect evidence trails
}
```

## 🔒 Security Considerations

- **Data Privacy**: All transcript data remains in your AWS account
- **Access Control**: Uses your AWS IAM permissions for S3 access
- **Encryption**: Supports S3 server-side encryption
- **Audit Trail**: Full logging of all analysis operations
- **Evidence Transparency**: Complete visibility into analysis decisions

## 🧪 Testing

Run the test suite:
```bash
# Install test dependencies
uv pip install -e ".[test]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=awslabs.call_analysis_mcp_server

# Test real analysis (no mocking)
python test_real_analysis.py
```

## 🐛 Troubleshooting

### Common Issues

**Virtual Environment Issues**
```
command not found: uv
```
**Solution:** Install uv first: `pip install uv`

**Module Not Found Error**
```
ModuleNotFoundError: No module named 'boto3'
```
**Solution:** Activate virtual environment and install dependencies:
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

**NLTK Data Missing**
```
LookupError: Resource 'vader_lexicon' not found
```
**Solution:** Download NLTK data:
```bash
python -c "import nltk; nltk.download(['punkt', 'stopwords', 'vader_lexicon', 'averaged_perceptron_tagger'])"
```

**AWS Credentials Error**
```
NoCredentialsError: Unable to locate credentials
```
**Solution:** Configure AWS credentials using `aws configure` or environment variables.

**S3 Access Denied**
```
ClientError: Access Denied
```
**Solution:** Ensure your AWS credentials have S3 read/write permissions for the specified buckets.

**Transcript Format Error**
```
TranscriptParsingError: Unable to parse transcript format
```
**Solution:** Verify your transcript follows one of the supported formats (JSON, CSV, or plain text).

**Evidence Collection Issues**
```
Low confidence analysis - limited evidence found
```
**Solution:** Check transcript quality and ensure speaker labels are correctly formatted.

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python -m awslabs.call_analysis_mcp_server.server
```

## 📚 API Reference

### Core Classes

#### `CallAnalysisResult`
Complete analysis result for a single call with performance metrics, sentiment analysis, and business intelligence flags.

#### `BusinessIntelligenceInsights` ⭐ NEW
Comprehensive business intelligence with evidence trails, including deal risks, churn predictions, opportunities, and quality issues.

#### `TranscriptEvidence` ⭐ NEW
Evidence from transcript supporting a specific insight with call ID, speaker, timestamp, and confidence score.

#### `DecisionEvidence` ⭐ NEW
Collection of evidence supporting a business decision with methodology and confidence level.

### Service Classes

#### `TranscriptAnalyzer`
Core analysis engine for processing call transcripts and extracting insights.

#### `BusinessIntelligenceAnalyzer` ⭐ NEW
Advanced analyzer for generating business intelligence with full evidence trails.

#### `S3Service`
Service for all S3 operations including reading transcripts and uploading results.

#### `ReportGenerator`
Service for creating formatted reports and interactive dashboards.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions, issues, or contributions:

- **Documentation**: Check this README and inline code documentation
- **Issues**: Report bugs or request features via GitHub issues
- **AWS Support**: For AWS-specific questions, consult AWS documentation

---

**AWS Labs MCP Server Collection** | **Call Analysis MCP Server v1.0.0** 