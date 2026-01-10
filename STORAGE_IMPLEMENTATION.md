# Story Storage Implementation

> **See [STORAGE_MIGRATION.md](STORAGE_MIGRATION.md) for migration from file to database storage.**  
> **See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment considerations.**

## Overview

The Short Story Pipeline supports **two storage backends** through a unified repository interface:

1. **Database Storage** (Default) - SQLite-based storage with optional Redis caching
2. **File Storage** (Legacy) - JSON file-based storage

Both implementations use the same `StoryRepository` interface, allowing the application to switch between storage backends without changing any route logic.

## Architecture

### Repository Pattern

The application uses the **Repository Pattern** to abstract storage details:

```
StoryRepository (Abstract Interface)
├── DatabaseStoryRepository (SQLite + optional Redis)
└── FileStoryRepository (JSON files)
```

### Interface Methods

All repositories implement the same interface:

- `save(story)` - Save a story
- `load(story_id)` - Load a story by ID
- `list(page, per_page, genre)` - List stories with pagination
- `update(story_id, updates)` - Update a story
- `delete(story_id)` - Delete a story
- `count(genre)` - Count stories (optionally filtered by genre)

## Database Storage (Default)

### Configuration

Set in `.env` file:

```bash
USE_DB_STORAGE=true  # Default: true
USE_REDIS_CACHE=false  # Optional: Enable Redis caching
```

### Implementation

- **Storage Class:** `StoryStorage` in `src/shortstory/utils/db_storage.py`
- **Repository:** `DatabaseStoryRepository` in `src/shortstory/utils/repository.py`
- **Database:** SQLite database at `data/stories.db`
- **Features:**
  - Efficient pagination
  - Genre filtering
  - Indexed queries for performance
  - Optional Redis caching layer
  - Transaction support

### Benefits

✅ **Scalable** - Handles thousands of stories efficiently  
✅ **Fast queries** - Indexed database queries  
✅ **Pagination** - Built-in pagination support  
✅ **Optional caching** - Redis caching for frequently accessed stories  
✅ **Data integrity** - Transaction support ensures consistency

## File Storage (Legacy)

### Configuration

Set in `.env` file:

```bash
USE_DB_STORAGE=false  # Use file-based storage
```

### Implementation

- **Storage Functions:** `src/shortstory/utils/storage.py`
- **Repository:** `FileStoryRepository` in `src/shortstory/utils/repository.py`
- **Location:** `stories/` directory
- **Format:** JSON files (one file per story)

### Use Cases

- Development and testing
- Small deployments (< 100 stories)
- Simple backup (just copy the `stories/` directory)

## Factory Function

The application uses a factory function to create the appropriate repository:

```python
from src.shortstory.utils import create_story_repository

# Automatically selects based on USE_DB_STORAGE environment variable
story_repository = create_story_repository()
```

**Default behavior:** Creates `DatabaseStoryRepository` if `USE_DB_STORAGE` is not set or is `true`.

## Usage in Application

The application uses the repository through a unified interface:

```python
# In app.py
story_repository = create_story_repository()

# All routes use the same interface
story_repository.save(story_data)
story = story_repository.load(story_id)
stories = story_repository.list(page=1, per_page=50, genre="Science Fiction")
story_repository.update(story_id, {"body": "Updated content"})
story_repository.delete(story_id)
count = story_repository.count()
```

**No route logic changes needed** when switching between storage backends!

## Testing

Comprehensive tests verify both implementations:

- **Repository Interface Tests:** `tests/test_repository.py`
  - Verifies both repositories implement the interface correctly
  - Tests all CRUD operations
  - Tests pagination and filtering
  - Tests factory function

- **Database Storage Tests:** `tests/test_db_storage.py`
  - Tests database operations
  - Tests Redis caching (when enabled)
  - Tests data serialization/deserialization

## Migration

### From File Storage to Database

1. **Enable database storage:**
   ```bash
   USE_DB_STORAGE=true
   ```

2. **Run the application** - The database will be initialized automatically

3. **Stories will be stored in the database** going forward

4. **Existing file-based stories** remain in the `stories/` directory but won't be accessed when database storage is enabled

### From Database to File Storage

1. **Disable database storage:**
   ```bash
   USE_DB_STORAGE=false
   ```

2. **Stories will be stored as JSON files** in the `stories/` directory

3. **Database remains** at `data/stories.db` but won't be accessed

## Performance Considerations

### Database Storage

- **Recommended for:** Production, large datasets (> 100 stories)
- **Performance:** Excellent for pagination and filtering
- **Scalability:** Handles thousands of stories efficiently
- **Optional Redis caching:** Reduces database load for frequently accessed stories

### File Storage

- **Recommended for:** Development, small datasets (< 100 stories)
- **Performance:** Good for small datasets, degrades with many files
- **Scalability:** Not recommended for large numbers of stories
- **Backup:** Simple (just copy the directory)

## Summary

✅ **Database option is fully implemented**  
✅ **Same interface for both storage backends**  
✅ **No route logic changes needed**  
✅ **Scalable to thousands of stories**  
✅ **Comprehensive test coverage**  
✅ **Easy configuration via environment variables**

The application can scale to thousands of stories without touching route logic!

