# Storage Migration Guide

This document describes the migration from in-memory storage to database-backed storage.

## Overview

The application has been updated to support database-backed storage using SQLite, with optional Redis caching. This provides better scalability and performance compared to the previous in-memory storage approach.

## Benefits

- **Scalability**: No longer limited by available RAM
- **Persistence**: Stories are stored in a database, not just in memory
- **Performance**: Optional Redis caching for frequently accessed stories
- **Pagination**: Efficient database-level pagination
- **Horizontal Scaling**: Can scale across multiple instances

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable database storage (recommended)
USE_DB_STORAGE=true

# Optional: Enable Redis caching for better performance
USE_REDIS_CACHE=false  # Set to true if you have Redis available
```

### Storage Backends

1. **Database Storage (Recommended)**: Uses SQLite for persistence
   - Database file: `data/stories.db`
   - Automatically created on first use
   - No additional setup required

2. **Redis Caching (Optional)**: Adds a caching layer on top of database storage
   - Requires Redis server
   - Set `USE_REDIS_CACHE=true` and configure `REDIS_URL`
   - Caches frequently accessed stories for faster retrieval

3. **Legacy Mode**: In-memory storage (for backward compatibility)
   - Set `USE_DB_STORAGE=false`
   - Not recommended for production

## Migration

### Migrating Existing Stories

If you have existing stories stored as JSON files, you can migrate them to the database:

```bash
# Dry run (see what would be migrated)
python3 -m src.shortstory.utils.migrate_storage --dry-run

# Actual migration
python3 -m src.shortstory.utils.migrate_storage
```

The migration script will:
1. Load all stories from the `stories/` directory
2. Convert them to database format
3. Store them in `data/stories.db`

**Note**: The original JSON files are not deleted during migration. You can keep them as backup or delete them manually after verifying the migration.

## Database Schema

The database uses a single `stories` table with the following structure:

- `id`: Story identifier (PRIMARY KEY)
- `genre`: Story genre
- `premise`, `outline`, `scaffold`: Story structure (stored as JSON)
- `text`: Story content
- `word_count`, `max_words`: Word count information
- `draft`, `revised_draft`: Draft versions (stored as JSON)
- `revision_history`: Revision history (stored as JSON)
- `current_revision`: Current revision number
- `genre_config`: Genre configuration (stored as JSON)
- `created_at`, `updated_at`, `saved_at`: Timestamps

## API Changes

The API remains backward compatible. The `/api/stories` endpoint now supports:

- **Pagination**: Already supported, now more efficient with database
- **Genre Filtering**: New `?genre=<genre>` query parameter
- **Better Performance**: Database queries are faster than loading all files

Example:
```
GET /api/stories?page=1&per_page=50&genre=Science Fiction
```

## Backward Compatibility

The application maintains backward compatibility:

- If `USE_DB_STORAGE=false`, it falls back to in-memory storage
- Existing JSON files continue to work
- No breaking changes to the API

## Production Recommendations

1. **Enable Database Storage**: Set `USE_DB_STORAGE=true`
2. **Use Redis Caching**: If you have Redis available, set `USE_REDIS_CACHE=true`
3. **Backup Database**: Regularly backup `data/stories.db`
4. **Monitor Performance**: Use database indexes for optimal performance

## Troubleshooting

### Database Not Created

If the database file is not created:
- Check that the `data/` directory exists and is writable
- Check application logs for errors

### Migration Fails

If migration fails:
- Check that JSON files are valid
- Verify file permissions
- Check application logs for specific errors

### Performance Issues

If you experience performance issues:
- Enable Redis caching (`USE_REDIS_CACHE=true`)
- Check database file size (SQLite can handle large databases)
- Consider database optimization if needed

## Future Enhancements

Potential future improvements:
- PostgreSQL support for larger deployments
- Full-text search capabilities
- Advanced querying and filtering
- Database replication for high availability

