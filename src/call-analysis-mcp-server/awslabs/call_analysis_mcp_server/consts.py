# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Constants for Call Analysis MCP Server."""

# Application name
CALL_ANALYSIS_MCP_SERVER_APPLICATION_NAME = "Call Analysis MCP Server"

# Analysis configuration
DEFAULT_ANALYSIS_OPTIONS = {
    "sentiment_analysis": True,
    "topic_extraction": True,
    "compliance_check": True,
    "performance_metrics": True,
    "detailed_flow_analysis": True
}

# File formats
SUPPORTED_TRANSCRIPT_FORMATS = [".txt", ".json", ".csv", ".tsv"]
OUTPUT_ANALYSIS_JSON = "analysis.json"
OUTPUT_ANALYSIS_MD = "analysis.md"

# S3 configuration
DEFAULT_S3_REGION = "us-east-1"
MAX_TRANSCRIPT_SIZE_MB = 100
MAX_CONCURRENT_JOBS = 10

# Analysis thresholds and scoring
SENTIMENT_CONFIDENCE_THRESHOLD = 0.7
TOPIC_RELEVANCE_THRESHOLD = 0.5
COMPLIANCE_PASS_THRESHOLD = 7.0
CUSTOMER_SATISFACTION_THRESHOLD = 6.0

# NLP model configurations
DEFAULT_SENTIMENT_MODEL = "vader"
DEFAULT_NER_MODEL = "en_core_web_sm"
DEFAULT_TOPIC_MODEL_COMPONENTS = 10

# Time-based analysis
DEFAULT_SILENCE_THRESHOLD_SECONDS = 2.0
LONG_PAUSE_THRESHOLD_SECONDS = 5.0
RAPID_SPEECH_THRESHOLD_WPM = 200
SLOW_SPEECH_THRESHOLD_WPM = 100

# Compliance keywords and phrases
COMPLIANCE_KEYWORDS = {
    "privacy_disclosures": [
        "privacy policy", "data protection", "personal information",
        "privacy rights", "data usage", "information security"
    ],
    "escalation_phrases": [
        "speak to supervisor", "escalate", "manager", "complaint",
        "speak to someone else", "higher authority"
    ],
    "hold_notifications": [
        "place you on hold", "brief hold", "one moment please",
        "please hold", "hold for a moment"
    ],
    "call_recording": [
        "call may be recorded", "recorded for quality", "recording this call",
        "call is being recorded", "quality and training purposes"
    ]
}

# Performance indicators
PERFORMANCE_INDICATORS = {
    "positive_phrases": [
        "thank you", "appreciate", "helpful", "great service",
        "excellent", "satisfied", "resolved", "understand"
    ],
    "negative_phrases": [
        "frustrated", "disappointed", "unhappy", "poor service",
        "terrible", "awful", "worst", "angry", "upset"
    ],
    "empathy_phrases": [
        "I understand", "I can imagine", "I'm sorry to hear",
        "that must be frustrating", "I can help with that"
    ],
    "professionalism_phrases": [
        "please", "thank you", "sir", "madam", "certainly",
        "absolutely", "my pleasure", "you're welcome"
    ]
}

# Topic categories
COMMON_CALL_TOPICS = {
    "technical_support": [
        "technical issue", "not working", "error", "problem",
        "troubleshoot", "fix", "repair", "malfunction"
    ],
    "billing_inquiry": [
        "bill", "billing", "charge", "payment", "invoice",
        "fee", "cost", "price", "refund", "credit"
    ],
    "account_management": [
        "account", "profile", "settings", "password", "login",
        "access", "update", "change", "modify"
    ],
    "product_information": [
        "product", "service", "feature", "how to", "information",
        "details", "specifications", "options"
    ]
}

# Analysis scoring weights
SCORING_WEIGHTS = {
    "sentiment_weight": 0.25,
    "compliance_weight": 0.20,
    "efficiency_weight": 0.20,
    "professionalism_weight": 0.15,
    "resolution_weight": 0.20
}

# Output templates
MARKDOWN_TEMPLATE_SECTIONS = [
    "executive_summary",
    "call_overview",
    "performance_metrics",
    "sentiment_analysis",
    "compliance_assessment",
    "key_topics",
    "recommendations",
    "detailed_analysis"
] 