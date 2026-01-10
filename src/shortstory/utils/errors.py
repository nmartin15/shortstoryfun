"""
Error handling utilities for the Short Story Pipeline.

Provides structured error responses and custom exception classes.
"""

import logging
import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING
from flask import jsonify

if TYPE_CHECKING:
    from flask import Request

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(APIError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(APIError):
    """Raised when a resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found.",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None):
        message = "Rate limit exceeded. Please try again later."
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            message += f" Retry after {retry_after} seconds."
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class ServiceUnavailableError(APIError):
    """Raised when an external service is unavailable."""
    
    def __init__(self, service: str, message: Optional[str] = None):
        error_message = message or f"Service '{service}' is currently unavailable."
        super().__init__(
            message=error_message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service}
        )


class MissingDependencyError(APIError):
    """Raised when a required dependency/library is not installed."""
    
    def __init__(self, dependency: str, install_command: str):
        message = f"Export requires '{dependency}'. Install with: {install_command}"
        super().__init__(
            message=message,
            error_code="MISSING_DEPENDENCY",
            status_code=503,
            details={"dependency": dependency, "install_command": install_command}
        )


class StorageError(APIError):
    """Base exception for storage-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            status_code=500,
            details=details
        )


class DataIntegrityError(StorageError):
    """Raised when data integrity constraints are violated."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_code = "DATA_INTEGRITY_ERROR"


class DatabaseConnectionError(StorageError):
    """Raised when database connection or operational errors occur."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_code = "DATABASE_CONNECTION_ERROR"


def parse_error_response(response_text: str, status_code: int) -> Dict[str, Any]:
    """
    Parse error response from API, handling both JSON and plain text.
    
    Provides consistent error parsing for better error reporting and debugging.
    
    Args:
        response_text: Response body text
        status_code: HTTP status code
        
    Returns:
        Dict with parsed error information:
        {
            "error": str,
            "error_code": str,
            "details": Dict (optional),
            "raw_text": str (if JSON parsing failed)
        }
    """
    import json
    
    error_info = {
        "error": f"API request failed with status {status_code}",
        "error_code": f"HTTP_{status_code}",
        "status_code": status_code
    }
    
    if not response_text:
        error_info["error"] = f"API request failed with status {status_code} (empty response)"
        return error_info
    
    # Try to parse as JSON first
    try:
        error_data = json.loads(response_text)
        if isinstance(error_data, dict):
            # Extract standard error fields
            error_info["error"] = error_data.get("error", error_info["error"])
            error_info["error_code"] = error_data.get("error_code", error_info["error_code"])
            if "details" in error_data:
                error_info["details"] = error_data["details"]
            # Include full response if it's an error object
            if "error" in error_data or "error_code" in error_data:
                error_info["full_response"] = error_data
    except (json.JSONDecodeError, ValueError):
        # Not JSON, use text directly
        error_info["raw_text"] = response_text[:1000]  # Limit to 1000 chars
        if len(response_text) > 1000:
            error_info["raw_text_truncated"] = True
    
    return error_info


def create_error_response(
    error: Exception,
    include_traceback: bool = False,
    request_context: Optional['Request'] = None
) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        error: Exception instance
        include_traceback: Whether to include traceback in response (for debugging)
        request_context: Optional Flask request object for logging context
    
    Returns:
        Tuple of (json_response, status_code)
    """
    # Extract request info if available
    request_path = request_context.path if request_context else None
    request_method = request_context.method if request_context else None
    
    # Log the error
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={
            "path": request_path,
            "method": request_method,
        }
    )
    
    # Handle APIError instances
    if isinstance(error, APIError):
        response = {
            "error": error.message,
            "error_code": error.error_code,
        }
        if error.details:
            response["details"] = error.details
        if include_traceback:
            response["traceback"] = traceback.format_exc()
        
        return jsonify(response), error.status_code
    
    # Handle other exceptions
    error_message = str(error)
    error_type = type(error).__name__
    
    # Don't expose internal errors in production
    if not include_traceback:
        error_message = "An unexpected error occurred. Please try again or contact support if the issue persists."
    
    response = {
        "error": error_message,
        "error_code": "INTERNAL_ERROR",
        "error_type": error_type,
    }
    
    if include_traceback:
        response["traceback"] = traceback.format_exc()
    
    return jsonify(response), 500


def register_error_handlers(app, debug: bool = False):
    """
    Register error handlers for the Flask app.
    
    Args:
        app: Flask application instance
        debug: Whether to include tracebacks in error responses
    """
    from flask import request  # Import here to avoid circular dependency
    
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle APIError exceptions."""
        return create_error_response(error, include_traceback=debug, request_context=request)
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        return create_error_response(
            NotFoundError("Resource", request.path),
            include_traceback=debug,
            request_context=request
        )
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            "error": f"Method '{request.method}' not allowed for this endpoint.",
            "error_code": "METHOD_NOT_ALLOWED",
        }), 405
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle 429 Rate Limit errors."""
        return create_error_response(
            RateLimitError(),
            include_traceback=debug,
            request_context=request
        )
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors."""
        return create_error_response(error, include_traceback=debug, request_context=request)
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        """Handle all other exceptions."""
        return create_error_response(error, include_traceback=debug, request_context=request)
