"""
Test constants for consistent test data.

This module provides constants for genres, status codes, and other
test values to avoid magic strings and improve test maintainability.
"""

# Genre names - use these instead of hardcoded strings
GENRE_HORROR = "Horror"
GENRE_ROMANCE = "Romance"
GENRE_SCIENCE_FICTION = "Science Fiction"
GENRE_MYSTERY = "Mystery"
GENRE_THRILLER = "Thriller"
GENRE_LITERARY = "Literary"
GENRE_GENERAL_FICTION = "General Fiction"

# Default genre (fallback)
DEFAULT_GENRE = GENRE_GENERAL_FICTION

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# Common test values
INVALID_GENRE = "Invalid Genre"
EMPTY_STRING = ""
WHITESPACE_ONLY = "   \t   "

