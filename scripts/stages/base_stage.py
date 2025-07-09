"""
Base Stage Class for TMF ODA Transformation Stages

This module defines the abstract base class that all transformation stages must implement.
It provides the common interface and utilities for stage execution.
"""

import json
import boto3
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal


class BaseStage(ABC):
    """
    Abstract base class for all transformation stages.
    
    Each stage must implement the execute_step method and define its steps.
    """
    
    def __init__(self, journey_id: str, stage_id: str, job_id: str, region_name: str = None):
        """
        Initialize the stage.
        
        Args:
            journey_id: The journey ID this stage belongs to
            stage_id: The stage ID (e.g., 'raw_analysis')
            job_id: The job execution ID
            region_name: AWS region name (optional)
        """
        self.journey_id = journey_id
        self.stage_id = stage_id
        self.job_id = job_id
        
        # Auto-detect region if not provided
        if region_name is None:
            session = boto3.Session()
            region_name = session.region_name or 'us-east-2'
        
        self.region_name = region_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        self.table = self.dynamodb.Table('TransformationSystem')
        
        # Stage execution state
        self.logs = []
        self.metrics = {}
        self.artifacts = {}
    
    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Return the human-readable stage name"""
        pass
    
    @property
    @abstractmethod
    def stage_description(self) -> str:
        """Return the stage description"""
        pass
    
    @property
    @abstractmethod
    def steps(self) -> List[Dict[str, Any]]:
        """Return the list of steps for this stage"""
        pass
    
    @abstractmethod
    def execute_step(self, step_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific step of this stage.
        
        Args:
            step_id: The step ID to execute
            step_data: Step configuration data
            
        Returns:
            Dict containing step results, logs, and metrics
        """
        pass
    
    def log_info(self, message: str, step_id: str = None):
        """Log an info message"""
        self._log('INFO', message, step_id)
    
    def log_warning(self, message: str, step_id: str = None):
        """Log a warning message"""
        self._log('WARNING', message, step_id)
    
    def log_error(self, message: str, step_id: str = None):
        """Log an error message"""
        self._log('ERROR', message, step_id)
    
    def _log(self, level: str, message: str, step_id: str = None):
        """Internal logging method"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'message': message,
            'step_id': step_id,
            'stage_id': self.stage_id,
            'job_id': self.job_id
        }
        self.logs.append(log_entry)
        
        # Also print to console with emoji
        emoji = {'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌'}.get(level, '📝')
        step_prefix = f"[{step_id}] " if step_id else ""
        print(f'{emoji} {step_prefix}{message}')
    
    def set_metric(self, key: str, value: Any, step_id: str = None):
        """Set a metric value"""
        if step_id:
            if step_id not in self.metrics:
                self.metrics[step_id] = {}
            self.metrics[step_id][key] = value
        else:
            self.metrics[key] = value
    
    def add_artifact(self, name: str, data: Any, step_id: str = None):
        """Add an artifact (result data)"""
        if step_id:
            if step_id not in self.artifacts:
                self.artifacts[step_id] = {}
            self.artifacts[step_id][name] = data
        else:
            self.artifacts[name] = data
    
    def upload_logs_to_s3(self, step_id: str):
        """Upload step logs to S3"""
        try:
            logs_key = f'journeys/{self.journey_id}/stages/{self.stage_id}/executions/{self.job_id}/logs/{step_id}.json'
            
            # Filter logs for this step
            step_logs = [log for log in self.logs if log.get('step_id') == step_id]
            
            self.s3.put_object(
                Bucket='transformation-journey-logs',
                Key=logs_key,
                Body=json.dumps(step_logs, indent=2),
                ContentType='application/json'
            )
            
            self.log_info(f'Uploaded logs to S3: {logs_key}', step_id)
            
        except Exception as e:
            self.log_error(f'Failed to upload logs to S3: {str(e)}', step_id)
    
    def upload_report_to_s3(self, step_id: str, report_data: Dict[str, Any]):
        """Upload step report to S3"""
        try:
            report_key = f'journeys/{self.journey_id}/stages/{self.stage_id}/executions/{self.job_id}/reports/{step_id}.json'
            
            # Convert Decimal values to float for JSON serialization
            report_json = json.dumps(report_data, indent=2, default=self._decimal_default)
            
            self.s3.put_object(
                Bucket='transformation-journey-reports',
                Key=report_key,
                Body=report_json,
                ContentType='application/json'
            )
            
            self.log_info(f'Uploaded report to S3: {report_key}', step_id)
            
        except Exception as e:
            self.log_error(f'Failed to upload report to S3: {str(e)}', step_id)
    
    def _decimal_default(self, obj):
        """JSON serializer for Decimal objects"""
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def simulate_processing(self, step_id: str, duration_seconds: int = 2):
        """Simulate processing time (for demo purposes)"""
        import time
        self.log_info(f'Processing step: {step_id}', step_id)
        time.sleep(duration_seconds)
        self.log_info(f'Completed step: {step_id}', step_id) 