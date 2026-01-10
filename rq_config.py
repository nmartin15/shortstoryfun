"""
RQ (Redis Queue) configuration for background jobs.
"""

import os
from typing import Optional
from redis import Redis
from rq import Queue, Connection
from rq.job import Job


def get_redis_connection() -> Redis:
    """
    Get Redis connection from environment or use default.
    
    Reads the REDIS_URL environment variable to determine the Redis connection
    string. Falls back to 'redis://localhost:6379/0' if not set.
    
    Note: If REDIS_URL starts with 'memory://', it is replaced with the default
    Redis URL since RQ requires an actual Redis instance.
    
    Returns:
        Redis: A Redis connection instance configured from REDIS_URL or default.
    
    Raises:
        redis.ConnectionError: If unable to connect to Redis server.
    """
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Handle memory:// for in-memory storage (development)
    if redis_url.startswith('memory://'):
        # Use default localhost Redis for RQ (RQ requires Redis)
        redis_url = 'redis://localhost:6379/0'
    
    return Redis.from_url(redis_url)


def get_queue(name: str = 'default') -> Queue:
    """
    Get an RQ queue by name.
    
    Creates or retrieves an RQ Queue instance for the specified queue name.
    Uses the Redis connection from get_redis_connection().
    
    Args:
        name: Queue name. Defaults to 'default' if not specified.
        
    Returns:
        Queue: An RQ Queue instance connected to the specified queue.
    
    Raises:
        redis.ConnectionError: If unable to connect to Redis server.
    """
    redis_conn = get_redis_connection()
    return Queue(name, connection=redis_conn)


def get_job(job_id: str) -> Optional[Job]:
    """
    Get a job by ID.
    
    Fetches an RQ Job instance by its unique identifier. Returns None if the
    job is not found or if an error occurs during fetching.
    
    Args:
        job_id: The unique identifier of the job to retrieve.
        
    Returns:
        Optional[Job]: The Job instance if found, None otherwise.
    """
    try:
        redis_conn = get_redis_connection()
        return Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return None

