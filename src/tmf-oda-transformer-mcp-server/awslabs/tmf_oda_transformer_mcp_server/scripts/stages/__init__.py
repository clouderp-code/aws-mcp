"""
TMF ODA Transformation Stages Package

This package contains all transformation stage implementations.
Each stage is responsible for a specific part of the transformation process.
"""

from .base_stage import BaseStage
from .raw_analysis import RawAnalysisStage
from .stripped_schema import StrippedSchemaStage

# Registry of all available stages
STAGE_REGISTRY = {
    'raw_analysis': RawAnalysisStage,
    'stripped_schema': StrippedSchemaStage,
}

def get_stage_class(stage_id: str):
    """Get the stage class for a given stage ID"""
    return STAGE_REGISTRY.get(stage_id)

def list_available_stages():
    """List all available stage IDs"""
    return list(STAGE_REGISTRY.keys()) 