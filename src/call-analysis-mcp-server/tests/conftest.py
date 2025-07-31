"""
Shared pytest configuration and fixtures for Call Analysis MCP Server tests.

Provides common fixtures, test utilities, and configuration
used across all test modules.
"""

import pytest
import json
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Generator

import sys
import logging

# Add the project root to Python path for imports
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import models and services for shared fixtures
from awslabs.call_analysis_mcp_server.models import (
    TranscriptSegment,
    CallParticipant,
    SentimentType,
    CallAnalysisResult,
    BusinessIntelligenceInsights,
    CallCharacteristics,
    SentimentAnalysis,
    PerformanceKPIs,
    ComplianceMetrics,
    ConversationFlow,
    KeyTopics,
    RiskLevel
)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Set up logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may be slow)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "ai: mark test as requiring AI/OpenAI (may need API key)"
    )
    config.addinivalue_line(
        "markers", "s3: mark test as requiring S3 operations (may need AWS credentials)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Mark integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        
        # Mark unit tests
        if any(name in item.nodeid for name in ["test_models", "test_transcript_analyzer", "test_business_intelligence"]):
            item.add_marker(pytest.mark.unit)
        
        # Mark AI tests
        if "ai" in item.nodeid.lower() or "openai" in item.nodeid.lower():
            item.add_marker(pytest.mark.ai)
        
        # Mark S3 tests
        if "s3" in item.nodeid.lower():
            item.add_marker(pytest.mark.s3)


# Shared fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_transcript_content():
    """Standard transcript content for testing."""
    return json.dumps({
        "call_id": "TEST_CALL_001",
        "metadata": {
            "date": "2024-01-15",
            "agent": "John Doe",
            "customer": "Test Customer",
            "duration": 300
        },
        "transcript": [
            {
                "speaker": "agent",
                "text": "Thank you for calling. How can I help you today?",
                "timestamp": "00:00",
                "duration": 4.5,
                "confidence": 0.95
            },
            {
                "speaker": "customer",
                "text": "I'm having issues with my billing. I'm frustrated with the service.",
                "timestamp": "00:05",
                "duration": 6.2,
                "confidence": 0.93
            },
            {
                "speaker": "agent",
                "text": "I understand your frustration. Let me look into your account immediately.",
                "timestamp": "00:12",
                "duration": 5.8,
                "confidence": 0.94
            },
            {
                "speaker": "customer",
                "text": "Thank you, I appreciate your help.",
                "timestamp": "00:18",
                "duration": 3.1,
                "confidence": 0.96
            }
        ]
    })


@pytest.fixture
def sample_transcript_segments():
    """Standard transcript segments for testing."""
    return [
        TranscriptSegment(
            timestamp=0.0,
            speaker=CallParticipant.AGENT,
            text="Thank you for calling. How can I help you today?",
            duration=4.5,
            confidence=0.95
        ),
        TranscriptSegment(
            timestamp=5.0,
            speaker=CallParticipant.CUSTOMER,
            text="I'm having issues with my billing. I'm frustrated with the service.",
            duration=6.2,
            confidence=0.93
        ),
        TranscriptSegment(
            timestamp=12.0,
            speaker=CallParticipant.AGENT,
            text="I understand your frustration. Let me look into your account immediately.",
            duration=5.8,
            confidence=0.94
        ),
        TranscriptSegment(
            timestamp=18.0,
            speaker=CallParticipant.CUSTOMER,
            text="Thank you, I appreciate your help.",
            duration=3.1,
            confidence=0.96
        )
    ]


@pytest.fixture
def sample_call_characteristics():
    """Standard call characteristics for testing."""
    return CallCharacteristics(
        total_duration_seconds=300.0,
        agent_talk_time_seconds=180.0,
        customer_talk_time_seconds=120.0,
        silence_duration_seconds=0.0,
        agent_talk_ratio=0.6,
        customer_talk_ratio=0.4,
        total_words=150,
        agent_words=90,
        customer_words=60,
        interruptions_by_agent=1,
        interruptions_by_customer=0,
        speaking_rate_agent_wpm=150.0,
        speaking_rate_customer_wpm=120.0
    )


@pytest.fixture
def sample_sentiment_analysis():
    """Standard sentiment analysis for testing."""
    return SentimentAnalysis(
        overall_sentiment=SentimentType.NEUTRAL,
        agent_sentiment=SentimentType.POSITIVE,
        customer_sentiment=SentimentType.NEGATIVE,
        sentiment_scores={
            'positive': 0.4,
            'negative': 0.3,
            'neutral': 0.3
        },
        sentiment_over_time=[
            {'timestamp': 0.0, 'sentiment': 'neutral', 'score': 0.1},
            {'timestamp': 5.0, 'sentiment': 'negative', 'score': -0.3},
            {'timestamp': 12.0, 'sentiment': 'positive', 'score': 0.2},
            {'timestamp': 18.0, 'sentiment': 'positive', 'score': 0.4}
        ],
        emotional_peaks=[
            {'timestamp': 5.0, 'intensity': 0.7, 'type': 'negative'}
        ],
        sentiment_transitions=2
    )


@pytest.fixture
def sample_performance_kpis():
    """Standard performance KPIs for testing."""
    return PerformanceKPIs(
        customer_satisfaction_score=7.5,
        first_call_resolution=True,
        agent_professionalism_score=8.5,
        agent_knowledge_score=8.0,
        agent_empathy_score=7.8,
        call_efficiency_score=7.2,
        issue_resolution_time=300.0,
        clarity_score=8.0,
        active_listening_score=7.5
    )


@pytest.fixture
def sample_call_analysis_result(
    sample_call_characteristics,
    sample_sentiment_analysis,
    sample_performance_kpis
):
    """Complete call analysis result for testing."""
    return CallAnalysisResult(
        call_id="TEST_CALL_001",
        analysis_timestamp=datetime.now(),
        transcript_source="s3://test-bucket/call.json",
        characteristics=sample_call_characteristics,
        sentiment_analysis=sample_sentiment_analysis,
        performance_kpis=sample_performance_kpis,
        compliance_metrics=ComplianceMetrics(
            compliance_score=8.5,
            required_disclosures_made=["recording_disclosure"],
            missing_disclosures=[],
            escalation_offered=False,
            hold_time_appropriate=True,
            privacy_compliance=True,
            security_compliance=True
        ),
        conversation_flow=ConversationFlow(
            turn_taking_frequency=6.0,
            conversation_segments=[],
            opening_quality_score=8.0,
            closing_quality_score=7.5,
            topic_changes=1,
            agenda_adherence_score=8.0
        ),
        key_topics=KeyTopics(
            primary_topics=["billing", "support"],
            secondary_topics=["account"],
            keywords_frequency={"billing": 2, "help": 1, "account": 1},
            named_entities=[],
            business_intent="support",
            call_outcome="resolved"
        ),
        processing_time_seconds=2.5
    )


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing."""
    mock_client = Mock()
    
    # Standard mock responses
    mock_client.get_object.return_value = {
        'Body': Mock()
    }
    mock_client.put_object.return_value = {}
    mock_client.list_objects_v2.return_value = {
        'Contents': [
            {
                'Key': 'transcript1.json',
                'Size': 1024,
                'LastModified': datetime.now()
            },
            {
                'Key': 'transcript2.json',
                'Size': 2048,
                'LastModified': datetime.now()
            }
        ]
    }
    mock_client.head_object.return_value = {
        'ContentLength': 1024,
        'LastModified': datetime.now(),
        'ContentType': 'application/json'
    }
    mock_client.delete_object.return_value = {}
    mock_client.generate_presigned_url.return_value = 'https://test-bucket.s3.amazonaws.com/file.json?signature=test'
    
    return mock_client


@pytest.fixture
def mock_s3_environment(mock_s3_client):
    """Mock S3 environment with patched boto3."""
    with patch('boto3.client', return_value=mock_s3_client):
        yield mock_s3_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    
    # Standard mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = json.dumps({
        "sentiment": "positive",
        "confidence": 0.8,
        "key_themes": ["customer_service", "problem_resolution"],
        "risk_indicators": [],
        "opportunities": [],
        "training_needs": []
    })
    
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    
    return mock_client


@pytest.fixture
def mock_openai_environment(mock_openai_client):
    """Mock OpenAI environment with API key."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        with patch('awslabs.call_analysis_mcp_server.services.ai_analyzer.OpenAI', return_value=mock_openai_client):
            yield mock_openai_client


@pytest.fixture
def temp_directory():
    """Temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_script_files(temp_directory, sample_transcript_content):
    """Create sample script files for testing."""
    script_files = []
    
    for i in range(3):
        script_path = os.path.join(temp_directory, f"script{i+1}.json")
        
        # Modify call_id for each script
        script_data = json.loads(sample_transcript_content)
        script_data["call_id"] = f"SCRIPT_TEST_{i+1:03d}"
        
        with open(script_path, 'w') as f:
            json.dump(script_data, f, indent=2)
        
        script_files.append(script_path)
    
    return script_files


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging functionality."""
    with patch('awslabs.call_analysis_mcp_server.services.transcript_analyzer.logger') as mock_log:
        yield mock_log


# Test utilities
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_transcript_segments(count: int = 5, speakers: List[str] = None) -> List[TranscriptSegment]:
        """Create test transcript segments."""
        if speakers is None:
            speakers = ["agent", "customer"]
        
        segments = []
        current_time = 0.0
        
        for i in range(count):
            speaker = CallParticipant(speakers[i % len(speakers)])
            text = f"This is test segment {i+1} from {speaker.value}."
            duration = 3.0 + (i * 0.5)
            
            segments.append(TranscriptSegment(
                timestamp=current_time,
                speaker=speaker,
                text=text,
                duration=duration,
                confidence=0.9 + (i * 0.01)
            ))
            
            current_time += duration + 1.0
        
        return segments
    
    @staticmethod
    def create_business_transcript() -> str:
        """Create a business-focused transcript with risk indicators."""
        return json.dumps({
            "call_id": "BUSINESS_TEST_001",
            "transcript": [
                {
                    "speaker": "agent",
                    "text": "Thank you for calling. How can I help you today?",
                    "timestamp": "00:00"
                },
                {
                    "speaker": "customer",
                    "text": "I'm concerned about the pricing. Your competitor offers 30% less.",
                    "timestamp": "00:05"
                },
                {
                    "speaker": "customer",
                    "text": "We're expanding next quarter and need additional services.",
                    "timestamp": "00:15"
                },
                {
                    "speaker": "customer",
                    "text": "If we can't resolve the price issue, we might have to switch.",
                    "timestamp": "00:25"
                },
                {
                    "speaker": "agent",
                    "text": "I understand your concerns. Let me see what we can do for you.",
                    "timestamp": "00:35"
                }
            ]
        })


@pytest.fixture
def test_data_factory():
    """Test data factory fixture."""
    return TestDataFactory


# Async test utilities
@pytest.fixture
def async_test_timeout():
    """Timeout for async tests."""
    return 30.0  # 30 seconds


def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Set test-specific environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'


def pytest_runtest_teardown(item):
    """Teardown after each test run."""
    # Clean up test environment variables
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


# Markers for parametrized tests
@pytest.fixture(params=[
    SentimentType.POSITIVE,
    SentimentType.NEGATIVE,
    SentimentType.NEUTRAL
])
def sentiment_type(request):
    """Parametrized sentiment types for testing."""
    return request.param


@pytest.fixture(params=[
    CallParticipant.AGENT,
    CallParticipant.CUSTOMER,
    CallParticipant.SYSTEM
])
def call_participant(request):
    """Parametrized call participants for testing."""
    return request.param


@pytest.fixture(params=[
    RiskLevel.LOW,
    RiskLevel.MEDIUM,
    RiskLevel.HIGH,
    RiskLevel.CRITICAL
])
def risk_level(request):
    """Parametrized risk levels for testing."""
    return request.param


# Performance testing fixtures
@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    import time
    import psutil
    import threading
    
    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
            self.peak_memory = None
            self._monitoring = False
            self._monitor_thread = None
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = self.start_memory
            self._monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_memory)
            self._monitor_thread.start()
        
        def stop(self):
            self.end_time = time.time()
            self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join()
        
        def _monitor_memory(self):
            while self._monitoring:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                self.peak_memory = max(self.peak_memory, current_memory)
                time.sleep(0.1)
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
        
        @property
        def memory_used(self):
            if self.start_memory and self.end_memory:
                return self.end_memory - self.start_memory
            return None
    
    return PerformanceTracker()


# Configuration for test reporting
@pytest.fixture(autouse=True)
def configure_test_logging(caplog):
    """Configure logging for tests."""
    caplog.set_level(logging.WARNING, logger='botocore')
    caplog.set_level(logging.WARNING, logger='urllib3')
    caplog.set_level(logging.INFO, logger='awslabs.call_analysis_mcp_server')