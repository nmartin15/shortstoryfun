# Story Model Standardization Assessment

## Current State: **Partially Standardized** ⚠️

### ✅ What's Working

1. **Documentation**: `STORY_JSON_SCHEMA.md` documents the expected structure
2. **Canonical API Response**: `build_canonical_story_response()` standardizes API output
3. **Repository Abstraction**: Unified storage interface via `StoryRepository`
4. **Database Schema**: Defined SQLite schema with proper columns

### ❌ Issues Identified

1. **No Formal Validation**
   - No Pydantic models or JSON schema validation
   - Stories can be created with invalid structures
   - Type safety is not enforced

2. **Dual Format Support**
   - `body` (new format): Pure narrative text
   - `text` (legacy format): Composite markdown with metadata
   - Code handles both, creating confusion about which to use

3. **Premise Duplication**
   - Root-level `premise` object
   - `outline.premise` object (duplicate)
   - Violates DRY principle, risk of inconsistency

4. **Inconsistent Creation**
   - `app.py` creates stories with `body` + `metadata`
   - `jobs.py` creates stories with slightly different structure
   - No single source of truth for story creation

5. **Metadata Handling**
   - New format: Separated `metadata` object
   - Old format: Metadata mixed in `scaffold` and other places
   - Inconsistent extraction logic throughout codebase

## Recommended Solution

### Phase 1: Add Formal Validation (Immediate)

**Option A: Pydantic Models** (Recommended)
- Add `pydantic>=2.0.0` to `requirements.txt`
- Use the `StoryModel` class in `src/shortstory/models.py`
- Validate all story creation through this model

**Option B: JSON Schema Validation**
- Create formal JSON schema file
- Validate stories on save/load
- Less type-safe but no new dependencies

### Phase 2: Standardize Story Creation (Short-term)

1. **Single Creation Function**
   ```python
   from src.shortstory.models import create_story
   
   story = create_story(
       story_id=story_id,
       premise=premise,
       outline=outline,
       genre=genre,
       genre_config=genre_config,
       body=revised_story_text,
       word_count=word_count,
       metadata=story_metadata,
       ...
   )
   ```

2. **Update All Creation Points**
   - `app.py` `generate_story()` route
   - `src/shortstory/jobs.py` `generate_story_job()`
   - Any other story creation code

### Phase 3: Eliminate Duplication (Medium-term)

1. **Remove Premise Duplication**
   - Keep only root-level `premise`
   - Use `outline.premise_id` as reference (if needed)
   - Migration script to update existing stories

2. **Standardize on `body` + `metadata`**
   - Remove legacy `text` field from new stories
   - Generate `text` on-demand via `generate_story_text()`
   - Migration script for existing stories

### Phase 4: Migration (Long-term)

1. **Data Migration Script**
   - Convert all existing stories to new format
   - Remove premise duplication
   - Standardize metadata structure
   - Update all story files

2. **Backward Compatibility**
   - Keep legacy support for reading old format
   - Gradually migrate stories on access
   - Remove legacy code after full migration

## Implementation Priority

### High Priority (Do First)
1. ✅ Add Pydantic model (`src/shortstory/models.py` - already created)
2. Add `pydantic>=2.0.0` to `requirements.txt`
3. Update story creation in `app.py` to use model
4. Update story creation in `jobs.py` to use model

### Medium Priority
1. Create migration script for existing stories
2. Remove premise duplication
3. Standardize metadata extraction

### Low Priority
1. Remove legacy `text` field support
2. Clean up backward compatibility code

## Usage Example

### Current (Inconsistent)
```python
story_data = {
    "id": story_id,
    "premise": premise,
    "outline": outline,
    "body": revised_story_text,
    "metadata": story_metadata,
    # ... many more fields
}
get_story_repository().save(story_data)
```

### Recommended (Standardized)
```python
from src.shortstory.models import create_story, validate_story

# Create new story
story = create_story(
    story_id=story_id,
    premise=premise,
    outline=outline,
    genre=genre,
    genre_config=genre_config,
    body=revised_story_text,
    word_count=word_count,
    metadata=story_metadata,
    scaffold=scaffold,
    draft=draft,
    revised_draft=revised_draft
)

# Save validated story
get_story_repository().save(story.to_dict())

# Or validate existing story
story = validate_story(existing_story_dict)
```

## Benefits of Standardization

1. **Type Safety**: Catch errors at creation time
2. **Consistency**: All stories follow the same structure
3. **Validation**: Automatic validation of word counts, required fields, etc.
4. **Documentation**: Model serves as living documentation
5. **IDE Support**: Better autocomplete and type hints
6. **Refactoring**: Easier to change structure with validation

## Next Steps

1. **Uncomment pydantic in requirements.txt**
2. **Test the StoryModel with existing stories**
3. **Update app.py to use create_story()**
4. **Update jobs.py to use create_story()**
5. **Run tests to ensure compatibility**
6. **Create migration script for existing stories**

