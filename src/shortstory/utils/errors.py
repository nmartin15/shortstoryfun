"""
Error handling utilities for the Short Story Pipeline.

Provides structured error responses and custom exception classes.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from flask import jsonify, request

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


def create_error_response(
    error: Exception,
    include_traceback: bool = False
) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        error: Exception instance
        include_traceback: Whether to include traceback in response (for debugging)
    
    Returns:
        Tuple of (json_response, status_code)
    """
    # Log the error
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={
            "path": request.path if request else None,
            "method": request.method if request else None,
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
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle APIError exceptions."""
        return create_error_response(error, include_traceback=debug)
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        return create_error_response(
            NotFoundError("Resource", request.path),
            include_traceback=debug
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
            include_traceback=debug
        )
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors."""
        return create_error_response(error, include_traceback=debug)
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        """Handle all other exceptions."""
        return create_error_response(error, include_traceback=debug)

