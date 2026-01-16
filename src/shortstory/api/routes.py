"""
Flask route handlers for the Short Story API.

This module contains all route handlers for the application, extracted from app.py
to improve code organization and maintainability.
"""

import re
import uuid
import logging
import time
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from flask import Flask
    from flask_limiter import Limiter

from flask import render_template, request, jsonify, current_app

# Import monitoring utilities (optional)
try:
    from src.shortstory.utils.monitoring import (
        track_story_generation,
        track_active_story_generations,
        track_background_job
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    track_story_generation = None  # type: ignore
    track_active_story_generations = None  # type: ignore
    track_background_job = None  # type: ignore
from src.shortstory.genres import get_available_genres, get_genre_config
from src.shortstory.templates import (
    get_templates_for_genre, get_all_templates, get_available_template_genres
)
from src.shortstory.utils import check_distinctiveness, MAX_WORD_COUNT
from src.shortstory.utils.story_builder import build_story_data
from src.shortstory.memorability_scorer import get_memorability_scorer
from src.shortstory.utils.errors import ValidationError, NotFoundError, ServiceUnavailableError
from src.shortstory.exports import export_story_from_dict
from src.shortstory.api.helpers import (
    word_count_response,
    build_canonical_story_response,
    get_story_body,
    get_story_text,
    get_story_repository,
    get_pipeline,
    validate_story_id,
    get_story_or_404,
)
from src.shortstory.services import (
    StoryValidationService,
    StoryExportService,
    JobService,
    StoryService,
    StoryGenerationService,
    StoryRevisionService,
)

# Background job support (optional)
try:
    from rq_config import get_queue, get_job
    from src.shortstory.jobs import (
        generate_story_job, revise_story_job, export_story_job
    )
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize services (singleton instances)
_validation_service = StoryValidationService()
_export_service = StoryExportService()
_job_service = JobService(flask_app=None)  # Will use current_app context
_story_service = StoryService(
    repository=None,  # Will use get_story_repository()
    pipeline_factory=get_pipeline
)
_generation_service = StoryGenerationService(
    repository=None,  # Will use get_story_repository()
    pipeline_factory=get_pipeline
)
_revision_service = StoryRevisionService(
    repository=None,  # Will use get_story_repository()
    pipeline_factory=get_pipeline
)


def _get_genre_for_error_tracking(validated: Optional[Dict[str, Any]] = None) -> str:
    """
    Extract genre from validated data or request for error tracking.
    
    Args:
        validated: Validated input dict (optional)
        
    Returns:
        Genre string or "unknown" if not available
    """
    if validated and isinstance(validated, dict):
        return validated.get("genre", "unknown")
    try:
        data = request.get_json() or {}
        return data.get('genre', 'unknown')
    except Exception:
        return "unknown"

def register_routes(flask_app: 'Flask', limiter_instance: 'Limiter') -> None:
    """
    Register all application routes.

    This function registers all routes with the Flask app instance,
    using the provided limiter for rate limiting. Routes access
    app extensions (limiter, repository) via current_app context.

    Args:
        flask_app: Flask application instance
        limiter_instance: Limiter instance for rate limiting
    """

    @flask_app.route('/')
    def index():
        """
        Render the main application page.

        Returns:
            Rendered HTML template with available genres
        """
        return render_template('index.html', genres=get_available_genres())

    @flask_app.route('/api/health')
    def health():
        """
        Health check endpoint.

        Returns:
            JSON response with status "ok" indicating the service is running
        """
        return jsonify({"status": "ok"})

    @flask_app.route('/api/genres', methods=['GET'])
    def get_genres():
        """
        Get list of available story genres.

        Returns:
            JSON response with list of available genre names
        """
        return jsonify({"genres": get_available_genres()})

    @flask_app.route('/api/generate', methods=['POST'])
    @limiter_instance.limit(lambda: current_app.config["GENERATE_RATE_LIMIT"])
    def generate_story():
        """
        Generate a new short story from user input.

        Request Body (JSON):
            - idea (str, required): Story premise/idea
            - character (dict, optional): Character description
            - theme (str, optional): Story theme
            - genre (str, optional): Story genre (default: "General Fiction")
            - background (bool, optional): Use background job if available

        Returns:
            JSON response with generated story in canonical format:
            {
                "id": str,
                "body": str,
                "text": str,
                "word_count": int,
                "max_words": int,
                "metadata": {...}
            }

        Raises:
            ValidationError: If required fields are missing or invalid
            ServiceUnavailableError: If AI generation service is unavailable
        """
        generation_start_time = time.time()
        try:
            data = request.get_json() or {}
            use_background = data.get('background', False)
            
            # Validate input using service
            validated = _validation_service.validate_generation_input(
                idea=data.get('idea'),
                character=data.get('character'),
                theme=data.get('theme'),
                genre=data.get('genre', 'General Fiction')
            )
            
            idea = validated["idea"]
            character = validated["character"]
            theme = validated["theme"]
            genre = validated["genre"]

            # Check if background jobs are enabled and requested
            # Update job service with current app context
            _job_service.flask_app = current_app
            if _job_service.is_background_jobs_enabled() and use_background:
                # Enqueue background job using service
                max_word_count = data.get('max_word_count', MAX_WORD_COUNT)
                result = _job_service.enqueue_story_generation(
                    idea=idea,
                    character=character,
                    theme=theme,
                    genre=genre,
                    max_word_count=max_word_count
                )
                logger.info(f"Enqueued story generation job: {result['job_id']}")
                return jsonify(result), 202  # Accepted

            # Synchronous generation using service
            # Track active story generations
            if MONITORING_AVAILABLE and track_active_story_generations:
                with track_active_story_generations():
                    story_data = _generation_service.generate_story(
                        idea=idea,
                        character=character,
                        theme=theme,
                        genre=genre,
                        max_word_count=data.get('max_word_count', MAX_WORD_COUNT)
                    )
            else:
                story_data = _generation_service.generate_story(
                    idea=idea,
                    character=character,
                    theme=theme,
                    genre=genre,
                    max_word_count=data.get('max_word_count', MAX_WORD_COUNT)
                )

            # Track story generation metrics
            generation_duration = time.time() - generation_start_time
            word_count = story_data.get('word_count', 0)
            if MONITORING_AVAILABLE and track_story_generation:
                track_story_generation(
                    genre=genre,
                    duration=generation_duration,
                    word_count=word_count,
                    status='success'
                )

            # Return canonical response format
            return jsonify(build_canonical_story_response(story_data))
        except ValidationError:
            # Re-raise validation errors to be handled by error handler
            raise
        except ServiceUnavailableError:
            # Re-raise service errors to be handled by error handler
            raise
        except (ConnectionError, TimeoutError) as e:
            error_msg = str(e)
            logger.warning(f"Network error during story generation: {error_msg}")
            # Track failed story generation
            generation_duration = time.time() - generation_start_time
            genre = _get_genre_for_error_tracking(validated if 'validated' in locals() else None)
            if MONITORING_AVAILABLE and track_story_generation:
                track_story_generation(
                    genre=genre,
                    duration=generation_duration,
                    word_count=0,
                    status='error'
                )
            raise ServiceUnavailableError(
                "network",
                "Network error occurred. Please check your connection and try again."
            )
        except KeyError as e:
            error_msg = str(e)
            logger.error(
                f"Missing required field during story generation: {error_msg}",
                exc_info=True)
            # Track failed story generation
            generation_duration = time.time() - generation_start_time
            genre = _get_genre_for_error_tracking(validated if 'validated' in locals() else None)
            if MONITORING_AVAILABLE and track_story_generation:
                track_story_generation(
                    genre=genre,
                    duration=generation_duration,
                    word_count=0,
                    status='error'
                )
            raise ValidationError(
                f"Missing required field: {error_msg}. Please check your story parameters.",
                details={"field": error_msg, "original_error": error_msg}
            )
        except ValueError as e:
            error_msg = str(e)
            # Track failed story generation
            generation_duration = time.time() - generation_start_time
            genre = _get_genre_for_error_tracking(validated if 'validated' in locals() else None)
            if MONITORING_AVAILABLE and track_story_generation:
                track_story_generation(
                    genre=genre,
                    duration=generation_duration,
                    word_count=0,
                    status='error'
                )
            if "premise" in error_msg.lower() or "validation" in error_msg.lower():
                raise ValidationError(
                    f"Validation error: {error_msg}. Please refine your story idea or character description.",
                    details={
                        "field": "premise",
                        "original_error": error_msg})
            raise ValidationError(
                f"Invalid input: {error_msg}. Please check your story parameters.",
                details={"original_error": error_msg}
            )
        except Exception as e:
            error_msg = str(e)
            # Track failed story generation
            generation_duration = time.time() - generation_start_time
            genre = _get_genre_for_error_tracking(validated if 'validated' in locals() else None)
            if MONITORING_AVAILABLE and track_story_generation:
                track_story_generation(
                    genre=genre,
                    duration=generation_duration,
                    word_count=0,
                    status='error'
                )
            # Check for common API errors
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                logger.warning(f"API error during story generation: {error_msg}")
                raise ServiceUnavailableError(
                    "ai_generation",
                    "AI generation service error. The app will use template-based generation. Check your API configuration if you expected AI generation."
                )
            # Re-raise to be handled by generic error handler
            logger.error(
                f"Unexpected error during story generation: {error_msg}",
                exc_info=True)
            raise

    @flask_app.route('/api/story/<story_id>', methods=['GET'])
    @limiter_instance.limit(lambda: current_app.config["GET_STORY_RATE_LIMIT"])
    def get_story(story_id: str):
        """
        Get a story by ID.

        Args:
            story_id: Unique identifier for the story

        Returns:
            JSON response with story in canonical format

        Raises:
            NotFoundError: If story with given ID does not exist
        """
        # Get story using service (includes word count recalculation)
        story = _story_service.get_story(story_id)
        # Return canonical response format (pass story_id from URL in case
        # it's not in story dict)
        return jsonify(
            build_canonical_story_response(
                story, story_id=story_id))

    @flask_app.route('/api/story/<story_id>', methods=['PUT'])
    @limiter_instance.limit(lambda: current_app.config["UPDATE_STORY_RATE_LIMIT"])
    def update_story(story_id: str):
        """
        Update a story's body text.

        Request Body (JSON):
            - body (str, required): New story body text
            - text (str, optional): Legacy field name for body

        Args:
            story_id: Unique identifier for the story

        Returns:
            JSON response with updated story in canonical format

        Raises:
            NotFoundError: If story with given ID does not exist
            ValidationError: If body is missing or exceeds word limit
        """
        data = request.get_json() or {}
        
        # Validate request body structure
        if not isinstance(data, dict):
            raise ValidationError(
                "Request body must be a JSON object.",
                details={"field": "body", "type": type(data).__name__}
            )
        
        # Support both 'body' (new format) and 'text' (legacy/backward compatibility)
        body_text = data.get('body') or data.get('text', '')
        
        # Update story using service (includes validation)
        story = _story_service.update_story_body(story_id, body_text)
        
        # Return canonical response format
        return jsonify(build_canonical_story_response(story))

    @flask_app.route('/api/validate', methods=['POST'])
    @limiter_instance.limit(lambda: current_app.config["VALIDATE_RATE_LIMIT"])
    def validate_text():
        """
        Validate story text for word count and distinctiveness.

        Request Body (JSON):
            - text (str, required): Text to validate
            - include_memorability (bool, optional): Include memorability score

        Returns:
            JSON response with validation results:
            {
                "word_count": int,
                "max_words": int,
                "remaining_words": int,
                "is_valid": bool,
                "distinctiveness": {...},
                "memorability": {...} (if requested)
            }

        Raises:
            ValidationError: If text field is missing
        """
        data = request.get_json()
        if not data or 'text' not in data:
            raise ValidationError(
                "Text content is required for validation.",
                details={"field": "text"}
            )

        # Validate text structure using service
        _validation_service.validate_story_body(data['text'])

        # Get request-scoped pipeline instance for word count validation
        pipeline = get_pipeline()
        word_count, is_valid = pipeline.word_validator.validate(
            data['text'], raise_error=False)
        response = {
            **word_count_response(word_count),
            "is_valid": is_valid,
            "distinctiveness": check_distinctiveness(data['text'])
        }

        # Optionally include memorability score if requested
        if data.get('include_memorability', False):
            scorer = get_memorability_scorer()
            character = data.get('character')
            outline = data.get('outline')
            premise = data.get('premise')
            response['memorability'] = scorer.score_story(
                text=data['text'],
                character=character,
                outline=outline,
                premise=premise
            )

        return jsonify(response)

    @flask_app.route('/api/memorability/score', methods=['POST'])
    @limiter_instance.limit(lambda: current_app.config["MEMORABILITY_RATE_LIMIT"])
    def score_memorability():
        """
        Score story memorability across multiple dimensions.

        Request body:
            {
            "text": str (required),
            "character": dict (optional),
            "outline": dict (optional),
            "premise": dict (optional)
            }

            Returns:
                {
                "overall_score": float,
                "dimensions": {...},
                "prioritized_suggestions": [...],
                "summary": str,
                "detailed_analysis": {...}
                }
                """
        data = request.get_json()
        if not data or 'text' not in data:
            raise ValidationError(
                "Text content is required for memorability scoring.",
                details={"field": "text"}
            )

        scorer = get_memorability_scorer()
        result = scorer.score_story(
            text=data['text'],
            character=data.get('character'),
            outline=data.get('outline'),
            premise=data.get('premise')
        )

        return jsonify(result)

    @flask_app.route('/api/story/<story_id>/save', methods=['POST'])
    @limiter_instance.limit(lambda: current_app.config["SAVE_STORY_RATE_LIMIT"])
    def save_story_endpoint(story_id: str):
        """
        Explicitly save a story to storage.

        Does NOT create new revisions - only updates the current story.
        Use /api/story/<id>/revise to create new revisions.

        Request Body (JSON, optional):
            - body (str, optional): Updated story body text
            - text (str, optional): Legacy field name for body

        Args:
            story_id: Unique identifier for the story

        Returns:
            JSON response with save confirmation and story data

        Raises:
            NotFoundError: If story with given ID does not exist
            ValidationError: If body exceeds word limit
            ServiceUnavailableError: If save operation fails
        """
        # Support both 'body' and 'text' for backward compatibility
        data = request.get_json() or {}
        body_text = data.get('body') or data.get('text')
        
        # Use service to save with optional body update
        story = _story_service.save_story_with_optional_update(
            story_id=story_id,
            body_text=body_text
        )
        
        logger.info(
            f"Story {story_id} saved successfully (no new revision created)")
        return jsonify({
            "success": True,
            "message": "Story saved successfully",
            "story_id": story_id,
            "body": get_story_body(story),
            "word_count": story.get("word_count", 0)
        })

    @flask_app.route('/api/stories', methods=['GET'])
    @flask_app.route('/api/story/list', methods=['GET'])  # Legacy endpoint for backward compatibility
    @limiter_instance.limit(lambda: current_app.config["LIST_STORIES_RATE_LIMIT"])
    def list_all_stories():
        """
        List all stories with metadata.

        Supports pagination via query parameters:
            - page: Page number (default: 1)
            - per_page: Items per page (default: 50, max: 100)

            Returns:
                JSON response with paginated stories, total count, and pagination metadata
                """
        try:
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            genre = request.args.get('genre', None, type=str)
            
            # Use service for listing (handles validation and pagination)
            result = _story_service.list_stories(
                page=page,
                per_page=per_page,
                genre=genre
            )
            return jsonify({
                "success": True,
                **result
            })
        except ValidationError:
            # Re-raise validation errors to be handled by error handler
            raise
        except Exception as e:
            logger.error(
                f"Failed to load stories: {str(e)}",
                exc_info=True)
            raise ServiceUnavailableError(
                "storage", "Failed to load stories. Please try again.")

    @flask_app.route('/api/templates', methods=['GET'])
    def get_templates():
        """
        Get story templates, optionally filtered by genre.

        Query Parameters:
            - genre (str, optional): Filter templates by genre

        Returns:
            JSON response with templates:
            - If genre specified: templates for that genre
            - Otherwise: all templates with available genres list
        """
        genre = request.args.get('genre')
        if genre:
            # Validate genre format using service
            _validation_service.validate_template_genre_format(genre)
            templates = get_templates_for_genre(genre)
            return jsonify({
                "success": True,
                "genre": genre,
                "templates": templates
            })
        else:
            all_templates = get_all_templates()
            return jsonify({
                "success": True,
                "templates": all_templates,
                "genres": get_available_template_genres()
            })

    @flask_app.route('/api/story/<story_id>/revise', methods=['POST'])
    @limiter_instance.limit(lambda: current_app.config["REVISION_RATE_LIMIT"])
    def revise_story(story_id: str):
        """
        Run an additional revision pass on a story.

        Creates a new revision in the story's revision history.

        Request Body (JSON, optional):
            - background (bool, optional): Use background job if available
            - use_llm (bool, optional): Use LLM for revision (default: True)

        Args:
            story_id: Unique identifier for the story

        Returns:
            JSON response with revised story in canonical format

        Raises:
            NotFoundError: If story with given ID does not exist
            ValidationError: If story has no content to revise
            ServiceUnavailableError: If revision fails
        """
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)

        # Get current story body (pure narrative text)
        current_body = get_story_body(story)
        if not current_body:
            raise ValidationError(
                "Story has no content to revise.",
                details={"story_id": story_id}
            )

        # Check if background jobs are enabled and requested
        data = request.get_json() or {}
        use_background = data.get('background', False)
        _job_service.flask_app = current_app
        
        if _job_service.is_background_jobs_enabled() and use_background:
            # Enqueue background job using service
            use_llm = data.get('use_llm', True)
            result = _job_service.enqueue_story_revision(
                story_id=story_id,
                use_llm=use_llm
            )
            logger.info(
                f"Enqueued story revision job: {result['job_id']} for story {story_id}")
            return jsonify(result), 202  # Accepted

            # Synchronous revision using service
            use_llm = data.get('use_llm', True)
            story = _revision_service.revise_story(
                story_id=story_id,
                use_llm=use_llm
            )
            
            # Return canonical response format
            return jsonify(
                build_canonical_story_response(story, story_id=story_id))
        except ValidationError:
            # Re-raise validation errors to be handled by error handler
            raise
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Invalid input during revision: {error_msg}")
            raise ValidationError(
                f"Invalid input: {error_msg}. Please check your story parameters.",
                details={"original_error": error_msg}
            )
        except (ConnectionError, TimeoutError) as e:
            error_msg = str(e)
            logger.warning(f"Network error during revision: {error_msg}")
            raise ServiceUnavailableError(
                "network",
                "Network error occurred during revision. Please check your connection and try again."
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Revision failed for story {story_id}: {error_msg}",
                exc_info=True)
            raise ServiceUnavailableError(
                "revision", f"Revision failed: {error_msg}")

    @flask_app.route('/api/story/<story_id>/revisions', methods=['GET'])
    @limiter_instance.limit(lambda: current_app.config["REVISION_HISTORY_RATE_LIMIT"])
    def get_revision_history(story_id: str):
        """
        Get revision history for a story.

        Args:
            story_id: Unique identifier for the story

        Returns:
            JSON response with revision history:
            {
                "success": bool,
                "story_id": str,
                "revision_history": [...],
                "current_revision": int,
                "total_revisions": int
            }

        Raises:
            NotFoundError: If story with given ID does not exist
        """
        # Get revision history using service
        result = _revision_service.get_revision_history(story_id)
        return jsonify(result)

    @flask_app.route('/api/story/<story_id>/compare', methods=['GET'])
    @limiter_instance.limit(lambda: current_app.config["COMPARE_VERSIONS_RATE_LIMIT"])
    def compare_story_versions(story_id: str):
        """
        Compare two versions of a story.

        Query Parameters:
            - version1 (int, optional): First version to compare (default: 1)
            - version2 (int, optional): Second version to compare (default: latest)

        Args:
            story_id: Unique identifier for the story

        Returns:
            JSON response with comparison data including:
            - Both versions' content and metadata
            - Word count differences
            - Text length differences

        Raises:
            NotFoundError: If story with given ID does not exist
            ValidationError: If not enough revisions exist or versions not found
        """
        # Validate version parameters using service
        version1 = request.args.get('version1', type=int)
        version2 = request.args.get('version2', type=int)
        
        if version1 is not None:
            _validation_service.validate_version_number(version1, "version1")
        if version2 is not None:
            _validation_service.validate_version_number(version2, "version2")

        # Compare versions using service
        result = _revision_service.compare_versions(
            story_id=story_id,
            version1=version1,
            version2=version2
        )
        return jsonify(result)

    @flask_app.route('/api/story/<story_id>/export/<format_type>',
                     methods=['GET'])
    @limiter_instance.limit(lambda: current_app.config["EXPORT_RATE_LIMIT"])
    def export_story(story_id: str, format_type: str):
        """
        Export a story in various formats.

        Supported formats: pdf, markdown, txt, docx, epub

        Query Parameters:
            - background (bool, optional): Use background job if available

        Args:
            story_id: Unique identifier for the story
            format_type: Export format (pdf, markdown, txt, docx, epub)

        Returns:
            File download response with exported story

        Raises:
            NotFoundError: If story with given ID does not exist
            ValidationError: If story has no content or format is unsupported
            ServiceUnavailableError: If export fails
            MissingDependencyError: If required export library is missing
        """
        # Validate story_id format (defense in depth - also done in get_story_or_404)
        validate_story_id(story_id)
        
        # Validate format using service
        _validation_service.validate_export_format(format_type)
        
        # Check if background jobs are enabled and requested
        use_background = request.args.get('background', 'false').lower() == 'true'
        _job_service.flask_app = current_app
        
        if _job_service.is_background_jobs_enabled() and use_background:
            # Enqueue background job using service
            result = _job_service.enqueue_story_export(
                story_id=story_id,
                format_type=format_type
            )
            logger.info(
                f"Enqueued story export job: {result['job_id']} for story {story_id}, format {format_type}")
            return jsonify(result), 202  # Accepted

        # Synchronous export using service
        return _export_service.export_story(story_id, format_type)

    @flask_app.route('/api/job/<job_id>', methods=['GET'])
    @limiter_instance.limit(lambda: current_app.config["JOB_STATUS_RATE_LIMIT"])
    def get_job_status(job_id: str):
        """
        Get the status of a background job.

        Args:
            job_id: Unique identifier for the background job

        Returns:
            JSON response with job status:
            {
                "job_id": str,
                "status": str,
                "created_at": str,
                "started_at": str,
                "ended_at": str,
                "result": Any,
                "error": str
            }

        Raises:
            NotFoundError: If job with given ID does not exist
            ServiceUnavailableError: If background jobs are not available
        """
        # Get job status using service
        _job_service.flask_app = current_app
        status = _job_service.get_job_status(job_id)
        return jsonify(status)

    @flask_app.route('/api/job/<job_id>/result', methods=['GET'])
    @limiter_instance.limit(lambda: current_app.config["JOB_STATUS_RATE_LIMIT"])
    def get_job_result(job_id: str):
        """
        Get the result of a completed background job.

        Args:
            job_id: Unique identifier for the background job

        Returns:
            JSON response with job result:
            {
                "status": "completed",
                "result": Any
            }

        Raises:
            NotFoundError: If job with given ID does not exist
            ServiceUnavailableError: If job failed or background jobs unavailable
        """
        # Get job result using service
        _job_service.flask_app = current_app
        result = _job_service.get_job_result(job_id)
        return jsonify(result)