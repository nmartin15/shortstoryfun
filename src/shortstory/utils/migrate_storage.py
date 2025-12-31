"""
Migration utility to convert JSON file storage to database storage.

This script migrates existing story JSON files to the SQLite database,
allowing for a smooth transition from file-based to database-backed storage.
"""

import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.shortstory.utils.storage import load_all_stories, STORAGE_DIR
from src.shortstory.utils.db_storage import StoryStorage, init_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_stories_to_database(dry_run: bool = False) -> int:
    """
    Migrate all stories from JSON files to database.
    
    Args:
        dry_run: If True, only report what would be migrated without actually migrating
        
    Returns:
        Number of stories migrated
    """
    logger.info("Starting story migration to database...")
    
    # Initialize database
    init_database()
    
    # Load all stories from JSON files
    logger.info(f"Loading stories from {STORAGE_DIR}...")
    stories = load_all_stories()
    
    if not stories:
        logger.info("No stories found to migrate.")
        return 0
    
    logger.info(f"Found {len(stories)} stories to migrate.")
    
    if dry_run:
        logger.info("DRY RUN: Would migrate the following stories:")
        for story_id, story in stories.items():
            logger.info(f"  - {story_id}: {story.get('genre', 'Unknown')} "
                       f"({story.get('word_count', 0)} words)")
        return len(stories)
    
    # Initialize database storage
    storage = StoryStorage(use_cache=False)
    
    # Migrate each story
    migrated = 0
    failed = 0
    
    for story_id, story in stories.items():
        try:
            if storage.save_story(story):
                migrated += 1
                logger.info(f"Migrated story {story_id}")
            else:
                failed += 1
                logger.error(f"Failed to migrate story {story_id}")
        except Exception as e:
            failed += 1
            logger.error(f"Error migrating story {story_id}: {e}", exc_info=True)
    
    logger.info(f"Migration complete: {migrated} migrated, {failed} failed")
    return migrated


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate stories from JSON files to database")
    parser.add_argument("--dry-run", action="store_true", 
                      help="Show what would be migrated without actually migrating")
    args = parser.parse_args()
    
    count = migrate_stories_to_database(dry_run=args.dry_run)
    sys.exit(0 if count > 0 or args.dry_run else 1)

