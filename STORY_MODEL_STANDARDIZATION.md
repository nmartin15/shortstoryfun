# Story Model Standardization

> **See [STORY_JSON_SCHEMA.md](stories/STORY_JSON_SCHEMA.md) for the complete JSON schema documentation.**

This document outlines the current state of story model standardization and provides a recommended approach for achieving full standardization.

## Current State: **Standardized with Pydantic Models** ✅

### ✅ What's Working

1. **Documentation**: `STORY_JSON_SCHEMA.md` documents the expected structure
2. **Canonical API Response**: `build_canonical_story_response()` standardizes API output
3. **Repository Abstraction**: Unified storage interface via `StoryRepository`
4. **Database Schema**: Defined SQLite schema with proper columns
5. **Story Builder**: `src/shortstory/utils/story_builder.py` provides standardized story creation
6. **✅ Pydantic Models in Pipeline**: Pipeline now uses `PremiseModel`, `OutlineModel`, `CharacterModel` for type safety and validation
7. **✅ Model Validation**: Automatic validation through Pydantic models
8. **✅ Type Safety**: Type hints and IDE support throughout pipeline

### ⚠️ Remaining Issues

1. **Storage Format**
   - Stories are still stored as dictionaries in database/file storage
   - Models are used in pipeline but converted to dicts for storage
   - Consider storing as validated models in future

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
   - `story_builder.py` provides standardization but not always used

5. **Metadata Handling**
   - New format: Separated `metadata` object
   - Old format: Metadata mixed in `scaffold` and other places
   - Inconsistent extraction logic throughout codebase

## Recommended Approach: **Pragmatic Incremental Adoption** ✅

Given that this is a **production application** with existing stories and a focus on backward compatibility, here's what makes sense:

### Phase 1: Use Story Builder (Immediate) 🎯

**Status**: ✅ Implemented - `src/shortstory/utils/story_builder.py` exists

**Action**: Ensure all story creation uses `build_story_data()`:
- ✅ Update `app.py` to use `build_story_data()`
- ✅ Update `jobs.py` to use `build_story_data()`
- ✅ Test that existing stories still work

**Benefits:**
- ✅ Single source of truth for story creation
- ✅ No new dependencies
- ✅ Immediate consistency fix
- ✅ Easy to adopt (just replace dict creation)

### Phase 2: Add Optional Validation Layer (Recommended) 🔍

**Status**: ✅ **IMPLEMENTED** - Pydantic models are now used in the pipeline

**Action**: ✅ **COMPLETED**
1. ✅ Pydantic models fully defined in `src/shortstory/models.py`
2. ✅ Pipeline now uses `PremiseModel`, `OutlineModel`, and `CharacterModel` internally
3. ✅ Models provide automatic validation and type safety
4. ✅ Backward compatibility maintained (accepts dicts, converts to models)

**Current Implementation:**
- `ShortStoryPipeline.capture_premise()` returns `PremiseModel`
- `ShortStoryPipeline.generate_outline()` returns `OutlineModel`
- Pipeline state uses Pydantic models instead of dictionaries
- Models provide validation, type hints, and clear structure

**Why Optional?**
- Production safety: Don't break existing functionality
- Gradual adoption: Can fix validation issues over time
- Development value: Catch bugs during development

**Implementation:**
```python
def validate_story_soft(story: Dict[str, Any]) -> Dict[str, Any]:
    """Validate story, return normalized version with warnings."""
    try:
        from .models import StoryModel
        validated = StoryModel.from_dict(story)
        return validated.to_dict()
    except Exception as e:
        logger.warning(f"Story validation issue (non-fatal): {e}")
        # Return original story, but log the issue
        return story
```

### Phase 3: Lazy Migration (Long-term) 🔄

**Action**: Normalize stories on access:
- Normalize stories when they're loaded
- Save normalized version back
- Gradually migrate the database

**Benefits:**
- No downtime
- No big migration script
- Natural migration as stories are accessed

### Phase 4: Eliminate Duplication (Medium-term)

1. **Remove Premise Duplication**
   - Keep only root-level `premise`
   - Use `outline.premise_id` as reference (if needed)
   - Migration script to update existing stories

2. **Standardize on `body` + `metadata`**
   - Remove legacy `text` field from new stories
   - Generate `text` on-demand via `generate_story_text()`
   - Migration script for existing stories

## What NOT to Do ❌

1. **Don't make validation mandatory** - Would break production
2. **Don't do big-bang migration** - Too risky for production
3. **Don't remove backward compatibility** - Existing stories must work
4. **Don't over-engineer** - Keep it simple and practical

## Implementation Priority

### ✅ Do Now (High Value, Low Risk)
1. Ensure `build_story_data()` is used everywhere
2. Add optional validation in repository.save()
3. Log validation warnings (don't fail)

### 🔄 Do Soon (Medium Priority)
1. Fix validation issues as they're discovered
2. Standardize metadata extraction

### 📋 Do Later (Low Priority)
1. Lazy migration on story access
2. Remove premise duplication gradually
3. Clean up legacy code after full migration

## Benefits of Standardization

1. **Type Safety**: Catch errors at creation time
2. **Consistency**: All stories follow the same structure
3. **Validation**: Automatic validation of word counts, required fields, etc.
4. **Documentation**: Model serves as living documentation
5. **IDE Support**: Better autocomplete and type hints
6. **Refactoring**: Easier to change structure with validation

## Related Documentation

- **[STORY_JSON_SCHEMA.md](stories/STORY_JSON_SCHEMA.md)** - Complete JSON schema reference
- **[STORAGE_IMPLEMENTATION.md](STORAGE_IMPLEMENTATION.md)** - Storage backend details
- **[ARCHITECTURAL_REFACTORING.md](ARCHITECTURAL_REFACTORING.md)** - Related refactoring suggestions

