"""
Gunicorn configuration for production deployment.

Usage:
    gunicorn -c gunicorn_config.py app:app
"""

import os
import multiprocessing


def get_env_int(var_name: str, default: int, min_value: int = 1, max_value: int = 1000) -> int:
    """Safely get and validate an integer environment variable."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        int_value = int(value)
        if int_value < min_value or int_value > max_value:
            raise ValueError(
                f"{var_name} must be between {min_value} and {max_value}, got {int_value}"
            )
        return int_value
    except ValueError as e:
        if "invalid literal" in str(e).lower():
            raise ValueError(f"{var_name} must be a valid integer, got '{value}'")
        raise


def get_env_str(var_name: str, default: str, allowed_values: list = None) -> str:
    """Safely get and validate a string environment variable."""
    value = os.getenv(var_name, default)
    if allowed_values and value not in allowed_values:
        raise ValueError(
            f"{var_name} must be one of {allowed_values}, got '{value}'"
        )
    return value


# Server socket
bind = get_env_str('GUNICORN_BIND', '0.0.0.0:5000')
backlog = 2048

# Worker processes - validate to prevent DoS
workers = get_env_int('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1, min_value=1, max_value=100)
worker_class = 'sync'
worker_connections = 1000
timeout = get_env_int('GUNICORN_TIMEOUT', 120, min_value=1, max_value=3600)  # Max 1 hour
keepalive = 5

# Logging
accesslog = get_env_str('GUNICORN_ACCESS_LOG', '-')  # '-' means stdout
errorlog = get_env_str('GUNICORN_ERROR_LOG', '-')  # '-' means stderr
loglevel = get_env_str('GUNICORN_LOG_LEVEL', 'info', allowed_values=['debug', 'info', 'warning', 'error', 'critical'])
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'shortstory'

# Server mechanics
daemon = False
pidfile = os.getenv('GUNICORN_PIDFILE', None)
umask = 0

# Validate user/group to prevent privilege escalation
user = os.getenv('GUNICORN_USER', None)
if user:
    # Basic validation - ensure it's not empty and doesn't contain dangerous characters
    if not user.strip() or '/' in user or '\\' in user:
        raise ValueError(f"Invalid GUNICORN_USER value: '{user}'. Must be a valid username.")

group = os.getenv('GUNICORN_GROUP', None)
if group:
    # Basic validation - ensure it's not empty and doesn't contain dangerous characters
    if not group.strip() or '/' in group or '\\' in group:
        raise ValueError(f"Invalid GUNICORN_GROUP value: '{group}'. Must be a valid group name.")

tmp_upload_dir = None

# SSL (if needed) - validate file paths exist if provided
keyfile = os.getenv('GUNICORN_KEYFILE', None)
if keyfile and not os.path.exists(keyfile):
    raise ValueError(f"GUNICORN_KEYFILE path does not exist: '{keyfile}'")

certfile = os.getenv('GUNICORN_CERTFILE', None)
if certfile and not os.path.exists(certfile):
    raise ValueError(f"GUNICORN_CERTFILE path does not exist: '{certfile}'")

# Preload app for better performance
preload_app = True

# Worker timeout for long-running requests (story generation can take time)
graceful_timeout = 30

