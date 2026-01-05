"""Flask web app for Short Story Pipeline."""

# Load environment variables from .env file before other imports
from dotenv import load_dotenv  # type: ignore[import-untyped]

load_dotenv()  # noqa: E402

import os  # noqa: E402
import uuid  # noqa: E402
import re  # noqa: E402
import logging  # noqa: E402
from typing import Any, Dict, Optional  # noqa: E402
from datetime import datetime  # noqa: E402
from flask import Flask, render_template, request, jsonify, current_app, g  # noqa: E402
from flask_cors import CORS  # type: ignore[import-untyped]  # noqa: E402
from flask_limiter import Limiter  # type: ignore[import-untyped]  # noqa: E402
from flask_limiter.util import get_remote_address  # type: ignore[import-untyped]  # noqa: E402
from src.shortstory.pipeline import ShortStoryPipeline  # noqa: E402
from src.shortstory.genres import get_available_genres, get_genre_config  # noqa: E402
from src.shortstory.templates import (  # noqa: E402
    get_templates_for_genre, get_all_templates, get_available_template_genres
)
from src.shortstory.utils import (  # noqa: E402
    check_distinctiveness, MAX_WORD_COUNT,
    create_story_repository,
)
from src.shortstory.utils.story_builder import build_story_data  # noqa: E402
from src.shortstory.memorability_scorer import get_memorability_scorer  # noqa: E402
from src.shortstory.utils.errors import (  # noqa: E402
    register_error_handlers, ValidationError, NotFoundError, ServiceUnavailableError
)  # noqa: E402
from src.shortstory.exports import (  # noqa: E402
    export_story_from_dict
)  # noqa: E402

# Background job support (optional)
try:
    from rq_config import get_queue, get_job  # noqa: E402
    from src.shortstory.jobs import (  # noqa: E402
        generate_story_job, revise_story_job, export_story_job
    )  # noqa: E402
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv('FLASK_ENV') != 'development' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Module-level variables for backward compatibility
# These will be initialized by create_app() - using Any initially to avoid type errors
# The actual types are set immediately after create_app() is called
app: Any = None  # type: ignore[assignment]
limiter: Any = None  # type: ignore[assignment]
story_repository: Any = None  # type: ignore[assignment]


def init_stories(repo: Any) -> None:
    """
    Initialize story storage on application startup.

    Logs the current story count from the repository.

    Args:
        repo: The story repository instance to initialize
    """
    count = repo.count()
    logger.info(f"Story repository initialized with {count} stories")


def check_llm_setup():
    """
    Check LLM (Large Language Model) setup and provide helpful feedback.

    Verifies that the Google Gemini API is properly configured by checking:
    1. Whether the GOOGLE_API_KEY environment variable is set
    2. Whether the API client can be initialized
    3. Whether the configured model is available and accessible

    Logs status messages indicating the setup status.
    This function is typically called during application startup to verify
    that AI-powered story generation will be available.

    Note:
        If the API is not available, the application will fall back to
        template-based story generation instead of AI generation.
    """
    try:
        from src.shortstory.utils import get_default_client
        import os

        has_api_key = bool(os.getenv("GOOGLE_API_KEY"))

        if has_api_key:
            try:
                client = get_default_client()
                is_available = client.check_availability()

                if is_available:
                    logger.info(
                        f"Google Gemini API ready: Using model '{client.model_name}'")
                    logger.info(
                        "Story generation will use AI-powered prose generation")
                else:
                    logger.warning(
                        f"Google Gemini API configured but model '{client.model_name}' may not be available")
                    logger.warning(
                        "The app will try to use AI generation, but may fall back to templates")
            except ValueError as e:
                logger.warning(f"LLM setup issue: {e}")
                logger.warning(
                    "The app will work with template-based generation")
                logger.warning("See SETUP_GOOGLE.md for setup instructions")
        else:
            logger.warning("GOOGLE_API_KEY not set")
            logger.warning(
                "The app will work, but will use template-based generation")
            logger.warning("To enable AI generation:")
            logger.warning(
                "  1. Get API key from https://makersuite.google.com/app/apikey")
            logger.warning("  2. Set GOOGLE_API_KEY environment variable")
            logger.warning("  See SETUP_GOOGLE.md for details")
    except Exception as e:
        logger.error(f"Could not check LLM setup: {e}")
        logger.warning("The app will work with template-based generation")
        logger.warning("See SETUP_GOOGLE.md for setup instructions")


def create_app(config=None):
    """
    Application factory function.

    Creates and configures a Flask application instance. This pattern enables:
    - Testing with isolated app instances
    - Multiple environments (dev/test/prod)
    - No side effects on module import
    - Better support for production servers (gunicorn, etc.)

    Args:
        config: Optional configuration dictionary or object to override defaults

    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask app
    flask_app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates')

    # Apply configuration if provided
    if config:
        flask_app.config.update(config)

    # Configure rate limits from environment variables (with sensible defaults)
    flask_app.config.setdefault(
        'GENERATE_RATE_LIMIT', os.getenv(
            'GENERATE_RATE_LIMIT', '10 per minute'))
    flask_app.config.setdefault(
        'REVISION_RATE_LIMIT', os.getenv(
            'REVISION_RATE_LIMIT', '20 per hour'))
    flask_app.config.setdefault(
        'EXPORT_RATE_LIMIT', os.getenv(
            'EXPORT_RATE_LIMIT', '50 per hour'))
    flask_app.config.setdefault(
        'MEMORABILITY_RATE_LIMIT', os.getenv(
            'MEMORABILITY_RATE_LIMIT', '30 per hour'))
    flask_app.config.setdefault(
        'SAVE_STORY_RATE_LIMIT', os.getenv(
            'SAVE_STORY_RATE_LIMIT', '100 per hour'))
    flask_app.config.setdefault(
        'LIST_STORIES_RATE_LIMIT', os.getenv(
            'LIST_STORIES_RATE_LIMIT', '60 per hour'))
    flask_app.config.setdefault(
        'REVISION_HISTORY_RATE_LIMIT', os.getenv(
            'REVISION_HISTORY_RATE_LIMIT', '60 per hour'))
    flask_app.config.setdefault(
        'COMPARE_VERSIONS_RATE_LIMIT', os.getenv(
            'COMPARE_VERSIONS_RATE_LIMIT', '30 per hour'))
    flask_app.config.setdefault(
        'JOB_STATUS_RATE_LIMIT', os.getenv(
            'JOB_STATUS_RATE_LIMIT', '120 per hour'))

    # Configure background jobs (default: enabled if RQ is available)
    use_background_jobs = os.getenv(
        'USE_BACKGROUND_JOBS',
        'true' if RQ_AVAILABLE else 'false').lower() == 'true'
    flask_app.config['USE_BACKGROUND_JOBS'] = use_background_jobs and RQ_AVAILABLE

    # Setup CORS - restrict to /api/* routes only
    # Load allowed origins from environment variable (comma-separated list)
    cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if cors_origins_env:
        allowed_origins = [
            origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
    else:
        # Default to empty list for security (no CORS allowed unless explicitly
        # configured)
        allowed_origins = []

    # Only allow CORS for /api/* routes with specified origins
    CORS(flask_app, resources={r"/api/*": {"origins": allowed_origins}})

    # Configure rate limiting
    limiter_instance = Limiter(
        app=flask_app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        # Use Redis in production if available
        storage_uri=os.getenv('REDIS_URL', 'memory://'),
        headers_enabled=True
    )

    # Initialize story repository (unified storage interface)
    story_repository_instance = create_story_repository()

    # Store as app extensions for access via current_app if needed
    flask_app.extensions['story_repository'] = story_repository_instance
    flask_app.extensions['limiter'] = limiter_instance

    # Register error handlers
    register_error_handlers(
        flask_app,
        debug=os.getenv('FLASK_ENV') == 'development')

    # Initialize on startup
    init_stories(story_repository_instance)
    check_llm_setup()

    # Register all routes
    register_routes(flask_app, limiter_instance)

    return flask_app

# Note: app instance creation is deferred until after register_routes is defined
# Module-level variables (limiter, story_repository) are set at the end of the file


def word_count_response(word_count, max_words=MAX_WORD_COUNT):
    """
    Build standardized word count response.

    Args:
        word_count: The current word count of the story
        max_words: The maximum allowed word count (default: MAX_WORD_COUNT)

    Returns:
        dict: A dictionary containing word count information with keys:
            - word_count: Current word count
            - max_words: Maximum allowed words
            - remaining_words: Words remaining before limit
    """
    return {
        "word_count": word_count,
        "max_words": max_words,
        "remaining_words": max_words - word_count
    }


def build_canonical_story_response(
        story: Dict[str, Any], story_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Build canonical story response format.

    Standardizes the response structure across all story endpoints:
    {
        "id": "...",
        "body": "...",
        "text": "...",
        "word_count": 1234,
        "max_words": 7500,
        "metadata": {
            "genre": "...",
            "tone": "...",
            "distinctiveness": {...},
            "premise": "...",
            "outline": "..."
        }
    }

    Args:
        story: Story dictionary from repository
        story_id: Optional story ID to use if not present in story dict

    Returns:
        dict: Canonical story response format
    """
    # Extract story ID (handle both "id" and "story_id" formats, or use
    # provided story_id)
    story_id = story_id or story.get("id") or story.get("story_id", "")

    # Get body (pure narrative text)
    body = get_story_body(story)

    # Get text (composite markdown)
    text = get_story_text(story)

    # Get word count and max words
    word_count = story.get("word_count", 0)
    max_words = story.get("max_words", MAX_WORD_COUNT)

    # Build metadata object
    metadata = story.get("metadata", {})

    # Extract distinctiveness scores
    idea_dist = metadata.get("idea_distinctiveness", {})
    char_dist = metadata.get("character_distinctiveness", {})

    # Combine distinctiveness into single object
    distinctiveness = {
        "idea": idea_dist,
        "character": char_dist
    }

    # Build canonical metadata
    canonical_metadata = {
        "genre": story.get("genre", ""),
        "tone": metadata.get("tone", ""),
        "distinctiveness": distinctiveness,
        "premise": story.get("premise", {}),
        "outline": story.get("outline", {})
    }

    return {
        "id": story_id,
        "body": body,
        "text": text,
        "word_count": word_count,
        "max_words": max_words,
        "metadata": canonical_metadata
    }


def generate_story_text(story: Dict[str, Any]) -> str:
    """
    Generate markdown composite text from story body and metadata.

    This function creates the formatted markdown output that combines:
    - Story metadata (title, genre, character, theme, etc.)
    - Pure narrative body text

    Args:
        story: Story dictionary containing body and metadata fields

    Returns:
        str: Formatted markdown text with metadata headers and story body
    """
    # Extract body (pure narrative text)
    body = story.get("body", "")

    # If body doesn't exist, try to extract from legacy text field
    if not body and story.get("text"):
        # Try to extract body from legacy composite text
        # Look for "## Story" section or assume everything after metadata
        text = story.get("text", "")
        story_match = re.search(r'## Story\s*\n\s*\n(.+)$', text, re.DOTALL)
        if story_match:
            body = story_match.group(1).strip()
        else:
            # Fallback: use the whole text (backward compatibility)
            body = text

    # Extract metadata
    metadata = story.get("metadata", {})
    premise = story.get("premise", {})
    genre = story.get("genre", "General Fiction")
    genre_config = story.get("genre_config", {})

    # Build metadata fields
    idea = premise.get("idea", "") if isinstance(
        premise, dict) else str(premise) if premise else ""
    character = premise.get(
        "character",
        {}) if isinstance(
        premise,
        dict) else {}
    theme = premise.get("theme", "") if isinstance(premise, dict) else ""

    char_desc = character.get("description", "") if isinstance(
        character, dict) else str(character) if character else ""

    framework = genre_config.get(
        'framework', 'narrative_arc') if isinstance(
        genre_config, dict) else 'narrative_arc'
    outline_structure = genre_config.get(
        'outline', [
            'setup', 'complication', 'resolution']) if isinstance(
        genre_config, dict) else [
                'setup', 'complication', 'resolution']

    # Get tone, pace, POV from metadata or scaffold
    scaffold = story.get("scaffold", {})
    constraints = genre_config.get(
        'constraints',
        {}) if isinstance(
        genre_config,
        dict) else {}
    tone = metadata.get('tone') or scaffold.get('tone') or constraints.get(
        'tone',
        'balanced') if isinstance(
        scaffold,
        dict) else constraints.get(
            'tone',
            'balanced') if isinstance(
                constraints,
        dict) else 'balanced'
    pace = metadata.get('pace') or scaffold.get('pace') or constraints.get(
        'pace',
        'moderate') if isinstance(
        scaffold,
        dict) else constraints.get(
            'pace',
            'moderate') if isinstance(
                constraints,
        dict) else 'moderate'
    pov = metadata.get('pov') or scaffold.get('pov') or constraints.get(
        'pov_preference',
        'flexible') if isinstance(
        scaffold,
        dict) else constraints.get(
            'pov_preference',
            'flexible') if isinstance(
                constraints,
        dict) else 'flexible'

    # Get distinctiveness scores if available
    idea_dist = metadata.get('idea_distinctiveness', {})
    char_dist = metadata.get('character_distinctiveness', {})

    idea_score = idea_dist.get(
        'distinctiveness_score',
        0.0) if isinstance(
        idea_dist,
        dict) else 0.0
    char_score = char_dist.get(
        'distinctiveness_score',
        0.0) if isinstance(
        char_dist,
        dict) else 0.0

    cliche_msg = ""
    if isinstance(idea_dist, dict) and idea_dist.get('has_cliches'):
        cliches = idea_dist.get('found_cliches', [])
        cliche_msg = f"⚠️ Clichés: {', '.join(cliches)}"
    else:
        cliche_msg = "✓ No clichés"

    generic_msg = ""
    if isinstance(char_dist, dict) and char_dist.get('has_generic_archetype'):
        generic = char_dist.get('generic_elements', [])
        generic_msg = f"⚠️ Generic: {', '.join(generic)}"
    else:
        generic_msg = "✓ Distinctive"

    # Build the composite markdown
    story_text = f"""# {idea}

## Genre: {genre} | Framework: {framework} | Structure: {', '.join(outline_structure)}
**Tone:** {tone} | **Pace:** {pace} | **POV:** {pov}

## Character
{char_desc if char_desc else 'Not specified'}

## Theme
{theme if theme else 'Not specified'}

## Distinctiveness
Idea: {idea_score:.2f}/1.0 | Character: {char_score:.2f}/1.0
{cliche_msg}
{generic_msg}

## Story

{body}
"""
    return story_text


def get_story_body(story: Dict[str, Any]) -> str:
    """
    Get the pure narrative body text from a story.

    Handles both new format (body field) and legacy format (text field).

    Args:
        story: Story dictionary

    Returns:
        str: Pure narrative text without metadata
    """
    # New format: body field exists
    if "body" in story:
        return story.get("body", "")

    # Legacy format: extract from text field
    if "text" in story:
        text = story.get("text", "")
        # Try to extract body from composite text
        story_match = re.search(r'## Story\s*\n\s*\n(.+)$', text, re.DOTALL)
        if story_match:
            return story_match.group(1).strip()
        # If no "## Story" marker, assume the whole text is body (backward
        # compatibility)
        return text

    return ""


def get_story_text(story: Dict[str, Any]) -> str:
    """
    Get the full markdown composite text from a story.

    Generates the composite on demand if it doesn't exist.

    Args:
        story: Story dictionary

    Returns:
        str: Full markdown composite text
    """
    # If text field exists and body doesn't, use legacy text
    if "text" in story and "body" not in story:
        return story.get("text", "")

    # Generate composite from body + metadata
    return generate_story_text(story)


def get_story_repository() -> Any:
    """
    Get the story repository from current_app context.

    Uses Flask's application context to access the story repository
    that was registered during app initialization.

    Returns:
        Story repository instance from app extensions
    """
    return current_app.extensions['story_repository']


def get_limiter() -> Any:
    """
    Get the rate limiter from current_app context.

    Uses Flask's application context to access the limiter
    that was registered during app initialization.

    Returns:
        Limiter instance from app extensions
    """
    return current_app.extensions['limiter']


def create_pipeline(genre=None, genre_config=None, max_word_count=None):
    """
    Create a request-scoped pipeline instance.

    This factory function creates a properly configured ShortStoryPipeline
    instance for use within a request handler. Each request gets its own
    pipeline instance to ensure isolation and prevent state leakage.

    Args:
        genre: Optional genre name
        genre_config: Optional genre configuration dict
        max_word_count: Optional maximum word count (default: MAX_WORD_COUNT)

    Returns:
        ShortStoryPipeline instance configured for the request
    """
    if max_word_count is None:
        max_word_count = MAX_WORD_COUNT

    # If genre_config not provided but genre is, fetch it
    if genre_config is None and genre:
        genre_config = get_genre_config(genre)

    return ShortStoryPipeline(
        max_word_count=max_word_count,
        genre=genre,
        genre_config=genre_config
    )


def get_pipeline(genre: Optional[str] = None, genre_config: Optional[Dict[str, Any]] = None, max_word_count: Optional[int] = None) -> Any:
    """
    Get or create a request-scoped pipeline instance.

    Uses Flask's request context (g object) to store the pipeline
    for the duration of the request, ensuring each request gets
    exactly one pipeline instance.

    Args:
        genre: Optional genre name
        genre_config: Optional genre configuration dict
        max_word_count: Optional maximum word count (default: MAX_WORD_COUNT)

    Returns:
        ShortStoryPipeline instance for the current request
    """
    # Check if pipeline already exists in request context
    if not hasattr(g, 'pipeline'):
        g.pipeline = create_pipeline(
            genre=genre,
            genre_config=genre_config,
            max_word_count=max_word_count)
    else:
        # If genre/config changed, update the existing pipeline
        if genre and g.pipeline.genre != genre:
            g.pipeline.genre = genre
            if genre_config:
                g.pipeline.genre_config = genre_config
            elif genre:
                g.pipeline.genre_config = get_genre_config(genre)

    return g.pipeline


def get_story_or_404(story_id: str) -> Optional[Dict[str, Any]]:
    """
    Get story from repository, or return None.

    Uses current_app context to access the story repository.
    Note: This function does NOT raise 404 errors - it returns None.
    Route handlers should check the return value and raise NotFoundError
    if the story is not found.

    Args:
        story_id: Unique identifier for the story

    Returns:
        Story data dictionary if found, None otherwise
    """
    repo = get_story_repository()
    return repo.load(story_id)


# Forward declaration - register_routes is defined later but needs to be
# available when create_app() is called. This is a workaround for the
# circular dependency issue.
def register_routes(flask_app, limiter_instance):
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
        try:
            data = request.get_json() or {}
            idea = data.get('idea', '').strip()
            character = data.get('character', {})
            theme = data.get('theme', '').strip()
            genre = data.get('genre', 'General Fiction')
            # Optional: use background job
            use_background = data.get('background', False)

            if not idea:
                raise ValidationError(
                    "Story idea is required. Please provide a creative premise for your story.",
                    details={
                        "field": "idea"})

            if isinstance(character, str):
                character = {"description": character}

            # Check if background jobs are enabled and requested
            use_bg_jobs = (
                current_app.config.get(
                    'USE_BACKGROUND_JOBS',
                    False) and use_background and RQ_AVAILABLE)

            if use_bg_jobs:
                # Enqueue background job
                queue = get_queue('default')
                max_word_count = data.get(
                    'max_word_count', MAX_WORD_COUNT)
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
                return jsonify({
                    "status": "queued",
                    "job_id": job.id,
                    "message": "Story generation started in background. Use /api/job/<job_id> to check status."
                }), 202  # Accepted

            # Synchronous generation (original behavior)
            genre_config = get_genre_config(genre)
            if genre_config is None:
                # Fallback to General Fiction if genre not found
                genre_config = get_genre_config('General Fiction')
                # Ensure genre_config is not None (should always be
                # a dict)
                if genre_config is None:
                    raise ServiceUnavailableError(
                        "genre_config", "Genre configuration service unavailable")

            # Get request-scoped pipeline instance
            pipeline = get_pipeline(genre=genre, genre_config=genre_config)

            premise = pipeline.capture_premise(
                idea, character, theme, validate=True)
            outline = pipeline.generate_outline(genre=genre)
            scaffold = pipeline.scaffold(genre=genre)

            # Run full pipeline: draft and revise
            draft = pipeline.draft()
            revised_draft = pipeline.revise()

            constraints = genre_config.get('constraints', {})
            tone = scaffold.get(
                'tone',
                constraints.get(
                    'tone',
                    'balanced')) if isinstance(
                scaffold,
                dict) else constraints.get(
                'tone',
                'balanced')
            pace = scaffold.get(
                'pace',
                constraints.get(
                    'pace',
                    'moderate')) if isinstance(
                scaffold,
                dict) else constraints.get(
                'pace',
                'moderate')
            pov = scaffold.get(
                'pov',
                constraints.get(
                    'pov_preference',
                    'flexible')) if isinstance(
                scaffold,
                dict) else constraints.get(
                'pov_preference',
                'flexible')

            idea_dist = check_distinctiveness(idea)
            char_dist = check_distinctiveness(None, character=character)

            # Get the revised story text (pure narrative body)
            revised_story_text = revised_draft.get('text', '')

            # IMPORTANT: Word count should ONLY count the actual story text, not metadata
            # Recalculate word count from the story text only to ensure
            # accuracy
            story_word_count = pipeline.word_validator.count_words(
                revised_story_text)

            # Log if there's a discrepancy (for debugging)
            draft_word_count = revised_draft.get('word_count', 0)
            if abs(story_word_count - draft_word_count) > 50:
                logger.warning(
                    f"Word count discrepancy: draft reported {draft_word_count}, "
                    f"actual story text is {story_word_count} words")

            # Use the actual story text word count (not metadata)
            word_count = story_word_count

            story_id = f"story_{uuid.uuid4().hex[:8]}"

            # Store metadata separately
            story_metadata = {
                "tone": tone,
                "pace": pace,
                "pov": pov,
                "idea_distinctiveness": idea_dist,
                "character_distinctiveness": char_dist
            }

            # Build standardized story data using story_builder
            # This ensures consistency across all story creation points
            story_data = build_story_data(
                story_id=story_id,
                premise=premise,
                outline=outline,
                genre=genre,
                genre_config=genre_config,
                body=revised_story_text,  # Pure narrative text
                word_count=word_count,
                scaffold=scaffold,
                metadata=story_metadata,  # Separated metadata
                draft=draft,
                revised_draft=revised_draft,
                max_words=MAX_WORD_COUNT
            )

            # Save to repository
            get_story_repository().save(story_data)

            logger.info(f"Successfully generated story {story_id}")
            # Return canonical response format
            return jsonify(build_canonical_story_response(story_data))
        except ValidationError:
            # Re-raise validation errors to be handled by error handler
            raise
        except ValueError as e:
            error_msg = str(e)
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
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)
        # Get request-scoped pipeline instance for word counting
        pipeline = get_pipeline()
        # Count words from body (pure narrative), not composite
        body = get_story_body(story)
        word_count = pipeline.word_validator.count_words(body)
        # Update word count in story for canonical response
        story["word_count"] = word_count
        story["max_words"] = story.get("max_words", MAX_WORD_COUNT)
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
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)

        data = request.get_json()
        # Support both 'body' (new format) and 'text' (legacy/backward
        # compatibility)
        body_text = data.get('body') or data.get('text', '')
        if not body_text:
            raise ValidationError(
                "Story body/text is required in the request body.",
                details={"field": "body"}
            )

        # Get request-scoped pipeline instance for validation
        pipeline = get_pipeline()
        word_count, is_valid = pipeline.word_validator.validate(
            body_text, raise_error=False)
        if not is_valid:
            raise ValidationError(
                f"Story exceeds word limit ({word_count:,} > {MAX_WORD_COUNT:,} words). Please reduce the length.",
                details={
                    "word_count": word_count,
                    "max_words": MAX_WORD_COUNT,
                    **word_count_response(word_count)})

        # Update body (pure narrative)
        story["body"] = body_text
        story["word_count"] = word_count
        story["max_words"] = story.get("max_words", MAX_WORD_COUNT)

        # Update in repository
        get_story_repository().update(
            story_id, {"body": body_text, "word_count": word_count})

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

        # Get request-scoped pipeline instance for validation
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
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)

        # Optionally update body if provided (support both 'body' and
        # 'text' for backward compatibility)
        data = request.get_json() or {}
        body_text = data.get('body') or data.get('text')
        if body_text:
            # Get request-scoped pipeline instance for validation
            pipeline = get_pipeline()
            word_count, is_valid = pipeline.word_validator.validate(
                body_text, raise_error=False)
            if not is_valid:
                raise ValidationError(
                    f"Story exceeds word limit ({word_count:,} > {MAX_WORD_COUNT:,} words). Please reduce the length.",
                    details={
                        "word_count": word_count,
                        "max_words": MAX_WORD_COUNT,
                        **word_count_response(word_count)})
            story["body"] = body_text
            story["word_count"] = word_count

        # IMPORTANT: Save does NOT create new revisions - it just updates the current story
        # Only the /revise endpoint creates new revisions

        # Save to repository
        success = get_story_repository().save(story)

        if success:
            logger.info(
                f"Story {story_id} saved successfully (no new revision created)")
            return jsonify({
                "success": True,
                "message": "Story saved successfully",
                "story_id": story_id,
                "body": get_story_body(story),
                "word_count": story.get("word_count", 0)
            })
        else:
            logger.error(f"Failed to save story {story_id}")
            raise ServiceUnavailableError(
                "storage", "Failed to save story. Please try again.")

    @flask_app.route('/api/stories', methods=['GET'])
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

            # Validate and limit per_page
            per_page = min(max(1, per_page), 100)  # Between 1 and 100
            page = max(1, page)  # At least page 1

            # Use repository for listing (handles pagination internally)
            result = get_story_repository().list(page=page, per_page=per_page, genre=genre)
            return jsonify({
                "success": True,
                **result
            })
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
        use_bg_jobs = (
            current_app.config.get('USE_BACKGROUND_JOBS', False) and
            use_background and
            RQ_AVAILABLE
        )

        if use_bg_jobs:
            # Enqueue background job
            queue = get_queue('default')
            use_llm = data.get('use_llm', True)
            job = queue.enqueue(
                revise_story_job,
                story_id=story_id,
                use_llm=use_llm,
                job_timeout='5m'  # 5 minute timeout for revision
            )
            logger.info(
                f"Enqueued story revision job: {job.id} for story {story_id}")
            return jsonify({
                "status": "queued",
                "job_id": job.id,
                "story_id": story_id,
                "message": "Story revision started in background. Use /api/job/<job_id> to check status."
            }), 202  # Accepted

        # Synchronous revision (original behavior)
        try:
            # Get genre and genre_config from story for revision
            story_genre = story.get("genre", "General Fiction")
            story_genre_config = story.get("genre_config")
            if story_genre_config is None:
                story_genre_config = get_genre_config(story_genre)

            # Get request-scoped pipeline instance with story's genre
            pipeline = get_pipeline(
                genre=story_genre,
                genre_config=story_genre_config)

            # Create a temporary draft object for revision
            temp_draft = {
                "text": current_body,
                "word_count": story.get("word_count", 0)
            }

            # Run revision
            use_llm = data.get('use_llm', True)
            revised_draft = pipeline.revise(draft=temp_draft, use_llm=use_llm)
            revised_body = revised_draft.get('text', '')
            revised_word_count = revised_draft.get('word_count', 0)

            # Update story with revised body
            story["body"] = revised_body
            story["word_count"] = revised_word_count
            story["max_words"] = story.get("max_words", MAX_WORD_COUNT)

            # Add to revision history (store body, not composite)
            if "revision_history" not in story:
                story["revision_history"] = []
            if "current_revision" not in story:
                story["current_revision"] = 0

            new_version = story["current_revision"] + 1
            story["revision_history"].append({
                "version": new_version,
                "body": revised_body,  # Store body, not composite
                "word_count": revised_word_count,
                "type": "revised",
                "timestamp": datetime.now().isoformat()
            })
            story["current_revision"] = new_version
            story["revised_draft"] = revised_draft

            # Save to repository
            get_story_repository().save(story)

            logger.info(
                f"Story {story_id} revised to version {new_version}")
            # Return canonical response format (pass story_id from URL
            # for consistency)
            return jsonify(
                build_canonical_story_response(
                    story, story_id=story_id))
        except Exception as e:
            logger.error(
                f"Revision failed for story {story_id}: {str(e)}",
                exc_info=True)
            raise ServiceUnavailableError(
                "revision", f"Revision failed: {str(e)}")

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
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)

        revision_history = story.get("revision_history", [])
        current_revision = story.get(
            "current_revision", len(revision_history))

        return jsonify({
            "success": True,
            "story_id": story_id,
            "revision_history": revision_history,
            "current_revision": current_revision,
            "total_revisions": len(revision_history)
        })

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
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)

        revision_history = story.get("revision_history", [])
        if len(revision_history) < 2:
            raise ValidationError(
                "Not enough revisions to compare. Need at least 2 versions.", details={
                    "story_id": story_id, "revision_count": len(revision_history)})

        version1 = request.args.get('version1', type=int)
        version2 = request.args.get('version2', type=int)

        if version1 is None or version2 is None:
            # Default to first and last
            version1 = 1
            version2 = len(revision_history)

        # Find versions
        v1_data = next(
            (r for r in revision_history if r.get("version") == version1), None)
        v2_data = next(
            (r for r in revision_history if r.get("version") == version2), None)

        if not v1_data or not v2_data:
            available_versions = [
                r.get('version') for r in revision_history]
            raise ValidationError(
                f"Version(s) not found. Available versions: {available_versions}",
                details={
                    "story_id": story_id,
                    "requested_versions": {
                        "version1": version1,
                        "version2": version2},
                    "available_versions": available_versions})

        # Get body text from revision history (support both
        # 'body' and 'text' for backward compatibility)
        text1 = v1_data.get("body") or v1_data.get("text", "")
        text2 = v2_data.get("body") or v2_data.get("text", "")

        words1 = text1.split()
        words2 = text2.split()

        # Calculate basic statistics
        word_count_diff = v2_data.get(
            "word_count", 0) - v1_data.get("word_count", 0)

        return jsonify({
            "success": True,
            "story_id": story_id,
            "version1": {
                "version": version1,
                "body": text1,  # Pure narrative text
                "word_count": v1_data.get("word_count", 0),
                "timestamp": v1_data.get("timestamp"),
                "type": v1_data.get("type", "unknown")
            },
            "version2": {
                "version": version2,
                "body": text2,  # Pure narrative text
                "word_count": v2_data.get("word_count", 0),
                "timestamp": v2_data.get("timestamp"),
                "type": v2_data.get("type", "unknown")
            },
            "comparison": {
                "word_count_diff": word_count_diff,
                "text_length_diff": len(text2) - len(text1),
                "words_added": max(0, len(words2) - len(words1)),
                "words_removed": max(0, len(words1) - len(words2))
            }
        })

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
        story = get_story_or_404(story_id)
        if story is None:
            raise NotFoundError("Story", story_id)

        # Check if background jobs are enabled and requested
        use_background = request.args.get(
            'background', 'false').lower() == 'true'
        use_bg_jobs = (
            current_app.config.get('USE_BACKGROUND_JOBS', False) and
            use_background and
            RQ_AVAILABLE
        )

        if use_bg_jobs:
            # Enqueue background job
            queue = get_queue('default')
            job = queue.enqueue(
                export_story_job,
                story_id=story_id,
                format_type=format_type,
                job_timeout='2m'  # 2 minute timeout for export
            )
            logger.info(
                f"Enqueued story export job: {job.id} for story {story_id}, format {format_type}")
            return jsonify({
                "status": "queued",
                "job_id": job.id,
                "story_id": story_id,
                "format_type": format_type,
                "message": "Export started in background. Use /api/job/<job_id> to check status."
            }), 202  # Accepted

        # Synchronous export (original behavior)
        # Get composite text for export (includes metadata headers)
        story_text = get_story_text(story)
        
        # Use the centralized export function from exports.py
        return export_story_from_dict(story, story_id, format_type, story_text)

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
        if not RQ_AVAILABLE:
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured.")

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
            "error": None}

        # Add result or error if job is finished
        if job.is_finished:
            try:
                result = job.result
                status["result"] = result

                # If result contains story_id, include it for
                # convenience
                if isinstance(result, dict):
                    if "story_id" in result:
                        status["story_id"] = result["story_id"]
                    if "status" in result:
                        status["job_status"] = result["status"]
            except Exception as e:
                status["error"] = str(e)
        elif job.is_failed:
            status["error"] = str(
                job.exc_info) if job.exc_info else "Job failed"

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
        if not RQ_AVAILABLE:
            raise ServiceUnavailableError(
                "background_jobs",
                "Background jobs are not available. RQ is not installed or configured.")

        job = get_job(job_id)
        if job is None:
            raise NotFoundError("Job", job_id)

        if not job.is_finished:
            return jsonify({
                "status": job.get_status(),
                "message": "Job is not finished yet. Use /api/job/<job_id> to check status."
            }), 202

        if job.is_failed:
            error_msg = str(
                job.exc_info) if job.exc_info else "Job failed"
            raise ServiceUnavailableError(
                "job_execution", f"Job failed: {error_msg}")

        try:
            result = job.result
            return jsonify({
                "status": "completed",
                "result": result
            })
        except Exception as e:
            raise ServiceUnavailableError(
                "job_result", f"Failed to retrieve job result: {str(e)}")


# Create app instance for backward compatibility
# This ensures existing code that imports 'app' directly still works
# Must be after register_routes is defined (which is above)
app = create_app()

# Set module-level variables for backward compatibility
# Routes use these directly, so we maintain them for now
# These are guaranteed to be set by create_app()
limiter = app.extensions['limiter']  # type: ignore[assignment]
story_repository = app.extensions['story_repository']  # type: ignore[assignment]


if __name__ == '__main__':
    # Production settings
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')

    app.run(debug=debug_mode, host=host, port=port)
