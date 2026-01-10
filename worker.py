#!/usr/bin/env python3
"""
RQ Worker for background job processing.

This worker processes background jobs for story generation, revision, and export.
"""

import os
import sys
import argparse
import logging
from typing import List
from rq import Connection, Worker, exceptions as rq_exceptions
from rq_config import get_redis_connection

try:
    import redis.exceptions
except ImportError:
    # If redis is not available, rq will handle it
    redis = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for the RQ worker script.

    Parses command-line arguments to determine which Redis queues to listen to
    and whether to run in burst mode. Connects to Redis and starts an RQ worker.

    Returns:
        int: The exit code for the script (0 for success, 1 for error).

    Raises:
        SystemExit: If an unhandled exception occurs during worker operation,
                    the script will exit with a non-zero status code.
    """
    parser = argparse.ArgumentParser(description='RQ worker for Short Story Pipeline')
    parser.add_argument(
        '--queue',
        type=str,
        default='default',
        help='Comma-separated list of queue names to listen on (default: default)'
    )
    parser.add_argument(
        '--burst',
        action='store_true',
        help='Run in burst mode (exit after processing all jobs)'
    )
    
    args = parser.parse_args()
    
    # Parse queue names
    queue_names: List[str] = [q.strip() for q in args.queue.split(',')]
    
    logger.info(f"Starting RQ worker for queues: {queue_names}")
    logger.info(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    
    try:
        redis_conn = get_redis_connection()
        
        with Connection(redis_conn):
            worker = Worker(queue_names, name='shortstory-worker')
            worker.work(burst=args.burst, logging_level='INFO')
            
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        return 0
    except (redis.exceptions.ConnectionError, rq_exceptions.ConnectionError) as ce:
        logger.critical(f"Redis connection error: {ce}. Worker cannot connect.", exc_info=True)
        return 1
    except Exception as e:
        # Catch any other unexpected exceptions. Consider if these should be more specific.
        logger.error(f"An unexpected worker error occurred: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
