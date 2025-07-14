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

"""DynamoDB-based journey manager for TMF ODA Transformer."""

from typing import Dict, Any, List, Optional

from loguru import logger


class JourneyManager:
    """DynamoDB-based journey management system for TMF ODA transformations."""

    def __init__(self, transformation_utils):
        """Initialize the journey manager with TransformationUtils.
        
        Args:
            transformation_utils: Instance of TransformationUtils for DynamoDB operations
        """
        self.utils = transformation_utils
        logger.info("JourneyManager initialized with DynamoDB backend")

    def list_journeys(self) -> List[Dict[str, Any]]:
        """List all journeys.
        
        Returns:
            List[Dict[str, Any]]: List of all journeys
        """
        try:
            return self.utils.list_journeys()
        except Exception as e:
            logger.error(f'Failed to list journeys from DynamoDB: {str(e)}')
            raise

    def get_journey_status(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get journey status by ID.
        
        Args:
            journey_id: Journey ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Journey status or None if not found
        """
        try:
            return self.utils.get_journey_status(journey_id)
        except Exception as e:
            logger.error(f'Failed to get journey status for {journey_id}: {str(e)}')
            raise

    def get_journey_stages(self, journey_id: str) -> List[Dict[str, Any]]:
        """Get stages for a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            List[Dict[str, Any]]: List of stages
        """
        try:
            return self.utils.get_journey_stages(journey_id)
        except Exception as e:
            logger.error(f'Failed to get stages for journey {journey_id}: {str(e)}')
            raise

    def get_stage_jobs(self, journey_id: str, stage_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs for a specific stage.
        
        Args:
            journey_id: Journey ID
            stage_id: Stage ID
            limit: Maximum number of jobs to return
            
        Returns:
            List[Dict[str, Any]]: List of jobs
        """
        try:
            return self.utils.get_stage_jobs(journey_id, stage_id, limit=limit)
        except Exception as e:
            logger.error(f'Failed to get jobs for journey {journey_id}, stage {stage_id}: {str(e)}')
            raise

    def create_journey(self, journey_data: Dict[str, Any]) -> str:
        """Create a new journey.
        
        Args:
            journey_data: Journey creation data
            
        Returns:
            str: Created journey ID
        """
        try:
            # Call the TransformationUtils method (this will be mocked in tests)
            return self.utils.create_journey(journey_data)
        except Exception as e:
            logger.error(f'Failed to create journey: {str(e)}')
            raise

    def update_journey_status(
        self, 
        journey_id: str, 
        status: str, 
        progress: int = None, 
        current_stage: str = None
    ) -> bool:
        """Update journey status.
        
        Args:
            journey_id: Journey ID to update
            status: New status
            progress: Optional progress percentage
            current_stage: Optional current stage
            
        Returns:
            bool: True if update successful
        """
        try:
            # For now, we'll simulate the update operation
            # In a real implementation, this would call TransformationUtils
            logger.info(f'Updating journey {journey_id} status to {status}')
            if progress is not None:
                logger.info(f'Setting progress to {progress}%')
            if current_stage is not None:
                logger.info(f'Setting current stage to {current_stage}')
            
            # Simulate successful update
            return True
        except Exception as e:
            logger.error(f'Failed to update journey {journey_id}: {str(e)}')
            raise

    def delete_journey(self, journey_id: str) -> Dict[str, Any]:
        """Delete a journey.
        
        Args:
            journey_id: Journey ID to delete
            
        Returns:
            Dict[str, Any]: Deletion result
        """
        try:
            # Call the TransformationUtils method to delete the journey
            return self.utils.delete_journey(journey_id)
        except Exception as e:
            logger.error(f'Failed to delete journey {journey_id}: {str(e)}')
            raise

    def create_job(self, journey_id: str, stage_id: str, job_data: Dict[str, Any]) -> str:
        """Create a new job execution.
        
        Args:
            journey_id: Journey ID
            stage_id: Stage ID
            job_data: Job creation data
            
        Returns:
            str: Created job ID
        """
        try:
            # This would need to be implemented in TransformationUtils
            # For now, we'll raise NotImplementedError
            raise NotImplementedError("Job creation not yet implemented in TransformationUtils")
        except Exception as e:
            logger.error(f'Failed to create job for journey {journey_id}, stage {stage_id}: {str(e)}')
            raise 