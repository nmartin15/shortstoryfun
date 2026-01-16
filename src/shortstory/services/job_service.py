"""
Background job service.

Handles background job operations including:
- Enqueueing jobs
- Checking job status
- Retrieving job results
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

from src.shortstory.utils.errors import NotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

# Background job support (optional)
try:
    from rq_config import get_queue, get_job
    from src.shortstory.jobs import (
        generate_story_job, revise_story_job, export_story_job
    )
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False


class JobService:
    """Service for managing background jobs."""
    
    def __init__(self, flask_app: Optional['Flask'] = None):
        """
        Initialize job service.
        
        Args:
            flask_app: Optional Flask app instance for accessing config
        """
        self.flask_app = flask_app
        self._rq_available = RQ_AVAILABLE
    
    def is_background_jobs_enabled(self) -> bool:
        """
        Check if background jobs are enabled and available.
        
        Returns:
            True if background jobs are available and enabled
        """
        if not self._rq_available:
            return False
        
        if self.flask_app:
            return self.flask_app.config.get('USE_BACKGROUND_JOBS', False)
        
        # If no flask_app, try to get from current_app context
        try:
            from flask import current_app
            return current_app.config.get('USE_BACKGROUND_JOBS', False)
        except RuntimeError:
            # Not in Flask request context
            return False
    
    def enqueue_story_generation(
        self,
        idea: str,
        character: Optional[Dict[str, Any]],
        theme: Optional[str],
        genre: str = "General Fiction",
        max_word_count: int = 7500
    ) -> Dict[str, Any]:
        """
        Enqueue a story generation job.
        
        Args:
            idea: Story idea/premise
            character: Character description (optional)
            theme: Story theme (optional)
            genre: Story genre (default: "General Fiction")
            max_word_count: Maximum word count (default: 7500)
            
        Returns:
            Dict with job status:
            {
                "status": "queued",
                "job_id": str,
                "message": str
            }
            
        Raises:
            ServiceUnavailableError: If background jobs are not available
        """
        if not self.is_background_jobs_enabled():
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured."
            )
        
        queue = get_queue('default')
        job = queue.enqueue(
            generate_story_job,
            idea=idea,
            character=character,
            theme=theme,
            genre=genre,
            max_word_count=max_word_count,
            job_timeout='10m'  # 10 minute timeout for story generation
        )
        
        logger.info(f"Enqueued story generation job: {job.id}")
        
        return {
            "status": "queued",
            "job_id": job.id,
            "message": "Story generation started in background. Use /api/job/<job_id> to check status."
        }
    
    def enqueue_story_revision(
        self,
        story_id: str,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Enqueue a story revision job.
        
        Args:
            story_id: ID of the story to revise
            use_llm: Whether to use LLM for revision (default: True)
            
        Returns:
            Dict with job status:
            {
                "status": "queued",
                "job_id": str,
                "story_id": str,
                "message": str
            }
            
        Raises:
            ServiceUnavailableError: If background jobs are not available
        """
        if not self.is_background_jobs_enabled():
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured."
            )
        
        queue = get_queue('default')
        job = queue.enqueue(
            revise_story_job,
            story_id=story_id,
            use_llm=use_llm,
            job_timeout='5m'  # 5 minute timeout for revision
        )
        
        logger.info(f"Enqueued story revision job: {job.id} for story {story_id}")
        
        return {
            "status": "queued",
            "job_id": job.id,
            "story_id": story_id,
            "message": "Story revision started in background. Use /api/job/<job_id> to check status."
        }
    
    def enqueue_story_export(
        self,
        story_id: str,
        format_type: str
    ) -> Dict[str, Any]:
        """
        Enqueue a story export job.
        
        Args:
            story_id: ID of the story to export
            format_type: Export format (pdf, markdown, txt, docx, epub)
            
        Returns:
            Dict with job status:
            {
                "status": "queued",
                "job_id": str,
                "story_id": str,
                "format_type": str,
                "message": str
            }
            
        Raises:
            ServiceUnavailableError: If background jobs are not available
        """
        if not self.is_background_jobs_enabled():
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured."
            )
        
        queue = get_queue('default')
        job = queue.enqueue(
            export_story_job,
            story_id=story_id,
            format_type=format_type,
            job_timeout='2m'  # 2 minute timeout for export
        )
        
        logger.info(
            f"Enqueued story export job: {job.id} for story {story_id}, format {format_type}"
        )
        
        return {
            "status": "queued",
            "job_id": job.id,
            "story_id": story_id,
            "format_type": format_type,
            "message": "Export started in background. Use /api/job/<job_id> to check status."
        }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a background job.
        
        Args:
            job_id: Unique identifier for the background job
            
        Returns:
            Dict with job status:
            {
                "job_id": str,
                "status": str,
                "created_at": Optional[str],
                "started_at": Optional[str],
                "ended_at": Optional[str],
                "result": Optional[Any],
                "error": Optional[str],
                "story_id": Optional[str],
                "job_status": Optional[str]
            }
            
        Raises:
            NotFoundError: If job with given ID does not exist
            ServiceUnavailableError: If background jobs are not available
        """
        if not self._rq_available:
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured."
            )
        
        job = get_job(job_id)
        if job is None:
            raise NotFoundError("Job", job_id)
        
        # Get job status
        status = {
            "job_id": job_id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": None,
            "error": None
        }
        
        # Add result or error if job is finished
        if job.is_finished:
            try:
                result = job.result
                status["result"] = result
                
                # If result contains story_id, include it for convenience
                if isinstance(result, dict):
                    if "story_id" in result:
                        status["story_id"] = result["story_id"]
                    if "status" in result:
                        status["job_status"] = result["status"]
            except Exception as e:
                status["error"] = str(e)
        elif job.is_failed:
            status["error"] = str(job.exc_info) if job.exc_info else "Job failed"
        
        return status
    
    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get the result of a completed background job.
        
        Args:
            job_id: Unique identifier for the background job
            
        Returns:
            Dict with job result:
            {
                "status": str,
                "result": Any
            }
            
        Raises:
            NotFoundError: If job with given ID does not exist
            ServiceUnavailableError: If job failed or background jobs unavailable
        """
        if not self._rq_available:
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured."
            )
        
        job = get_job(job_id)
        if job is None:
            raise NotFoundError("Job", job_id)
        
        if not job.is_finished:
            return {
                "status": job.get_status(),
                "message": "Job is not finished yet. Use /api/job/<job_id> to check status."
            }
        
        if job.is_failed:
            error_msg = str(job.exc_info) if job.exc_info else "Job failed"
            raise ServiceUnavailableError("job_execution", f"Job failed: {error_msg}")
        
        try:
            result = job.result
            return {
                "status": "completed",
                "result": result
            }
        except Exception as e:
            raise ServiceUnavailableError(
                "job_result", f"Failed to retrieve job result: {str(e)}"
            )
