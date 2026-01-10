# Architectural Refactoring Suggestions

> **See [STORY_MODEL_STANDARDIZATION.md](STORY_MODEL_STANDARDIZATION.md) for story model standardization approach.**  
> **See [STORAGE_IMPLEMENTATION.md](STORAGE_IMPLEMENTATION.md) for current storage architecture.**

This document outlines architectural improvements that would require **significant refactoring** of the codebase. These are more substantial changes than quick fixes and would impact multiple components.

## 1. Separation of Concerns in Validation Module

**Current Issue:**
The `check_distinctiveness()` function in `src/shortstory/utils/validation.py` mixes multiple concerns:
- Cliché detection logic
- Archetype detection logic  
- Generic pattern detection
- Distinctiveness score calculation

**Refactoring Required:**
Split into separate, focused functions following Single Responsibility Principle:

```python
# Proposed structure:
def detect_cliches(text) -> Dict:
    """Detect clichés in the given text."""
    # Pure cliché detection logic
    pass

def detect_generic_archetypes(character) -> Dict:
    """Detect generic archetypes in character description."""
    # Pure archetype detection logic
    pass

def detect_generic_patterns(text) -> List[Dict]:
    """Detect generic language patterns."""
    # Pure pattern detection logic
    pass

def calculate_distinctiveness_score(
    cliche_results: Dict,
    archetype_results: Dict,
    pattern_results: List[Dict]
) -> float:
    """Calculate distinctiveness score from detection results."""
    # Pure scoring logic
    pass

def check_distinctiveness(text=None, character=None) -> Dict:
    """Orchestrator function that coordinates detection and scoring."""
    cliche_results = detect_cliches(text) if text else {}
    archetype_results = detect_generic_archetypes(character) if character else {}
    pattern_results = detect_generic_patterns(text) if text else []
    
    score = calculate_distinctiveness_score(cliche_results, archetype_results, pattern_results)
    
    return {
        "distinctiveness_score": score,
        **cliche_results,
        **archetype_results,
        "generic_patterns": pattern_results
    }
```

**Impact:**
- **Files affected:** `src/shortstory/utils/validation.py`, `tests/test_validation.py`
- **Breaking changes:** Function signatures change, all callers need updates
- **Benefits:** Easier to test, maintain, and extend with new detection types

---

## 2. Data Structure Refactoring - Eliminate Premise Duplication

**Current Issue:**
Story JSON structure duplicates premise data:
- Top-level `premise` object
- `outline.premise` object (duplicate)

This violates DRY principle and creates risk of data inconsistency.

**Refactoring Required:**
Refactor to use reference-based structure:

```json
{
  "id": "story_62d94026",
  "premise": {
    "id": "premise_abc123",
    "idea": "...",
    "character": {...},
    "theme": "..."
  },
  "outline": {
    "premise_id": "premise_abc123",  // Reference instead of duplicate
    "genre": "Crime / Noir",
    "framework": "mystery_arc",
    "structure": [...]
  }
}
```

**Alternative Approach:**
Use normalized data model with separate premise storage:

```python
# Separate premise storage
premises = {
    "premise_abc123": {
        "idea": "...",
        "character": {...},
        "theme": "..."
    }
}

# Stories reference premises
stories = {
    "story_62d94026": {
        "premise_id": "premise_abc123",
        "outline": {...},
        "text": "..."
    }
}
```

**Impact:**
- **Files affected:** 
  - All story JSON files in `stories/`
  - `app.py` (story generation and retrieval)
  - `src/shortstory/pipeline.py` (outline generation)
  - `src/shortstory/utils/db_storage.py` (database schema)
  - `src/shortstory/utils/storage.py` (file storage)
- **Breaking changes:** Complete data model change, migration script needed
- **Benefits:** Single source of truth, easier updates, reduced storage

---

## 3. Pipeline Architecture - Stage Separation

**Current Issue:**
The `ShortStoryPipeline` class mixes orchestration with implementation details. Each stage method contains both:
- Stage-specific logic
- Data transformation
- Error handling
- LLM fallback logic

**Refactoring Required:**
Implement Strategy Pattern with separate stage classes:

```python
# Base stage interface
class PipelineStage(ABC):
    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute this stage and return updated context."""
        pass

# Concrete stage implementations
class PremiseCaptureStage(PipelineStage):
    def execute(self, context: PipelineContext) -> PipelineContext:
        # Pure premise capture logic
        pass

class OutlineGenerationStage(PipelineStage):
    def execute(self, context: PipelineContext) -> PipelineContext:
        # Pure outline generation logic
        pass

class ScaffoldingStage(PipelineStage):
    def execute(self, context: PipelineContext) -> PipelineContext:
        # Pure scaffolding logic
        pass

class DraftingStage(PipelineStage):
    def __init__(self, llm_client, template_fallback):
        self.llm_client = llm_client
        self.template_fallback = template_fallback
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        # Drafting with dependency injection
        pass

class RevisionStage(PipelineStage):
    def execute(self, context: PipelineContext) -> PipelineContext:
        # Pure revision logic
        pass

# Pipeline orchestrator
class ShortStoryPipeline:
    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages
    
    def run_full_pipeline(self, idea, character, theme, genre=None):
        context = PipelineContext(idea=idea, character=character, theme=theme, genre=genre)
        
        for stage in self.stages:
            context = stage.execute(context)
        
        return context.get_revised_draft()
```

**Impact:**
- **Files affected:** 
  - `src/shortstory/pipeline.py` (complete rewrite)
  - Create new `src/shortstory/stages/` directory
  - All tests in `tests/test_pipeline.py`
- **Breaking changes:** Complete API change
- **Benefits:** Better testability, easier to add new stages, clearer separation of concerns

---

## 4. Storage Abstraction Layer

**Current Issue:**
Storage logic is scattered and dual-mode (database vs in-memory) creates complexity:
- `app.py` has conditional logic for storage mode
- `src/shortstory/utils/storage.py` (file-based)
- `src/shortstory/utils/db_storage.py` (database-based)
- Direct access patterns mixed throughout

**Refactoring Required:**
Implement Repository Pattern with unified interface:

```python
# Abstract storage interface
class StoryRepository(ABC):
    @abstractmethod
    def save(self, story: Dict) -> bool:
        pass
    
    @abstractmethod
    def load(self, story_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def list(self, page: int = 1, per_page: int = 50, genre: Optional[str] = None) -> Dict:
        pass
    
    @abstractmethod
    def update(self, story_id: str, updates: Dict) -> bool:
        pass
    
    @abstractmethod
    def delete(self, story_id: str) -> bool:
        pass

# Concrete implementations
class DatabaseStoryRepository(StoryRepository):
    def __init__(self, db_connection, cache=None):
        self.db = db_connection
        self.cache = cache
    
    # Implementation using database

class FileStoryRepository(StoryRepository):
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
    
    # Implementation using file system

# Factory for creating appropriate repository
def create_story_repository() -> StoryRepository:
    if USE_DB_STORAGE:
        return DatabaseStoryRepository(db_connection, cache=redis_cache)
    else:
        return FileStoryRepository(storage_path="stories/")

# Usage in app.py
story_repository = create_story_repository()

@app.route('/api/story/<story_id>', methods=['GET'])
def get_story(story_id):
    story = story_repository.load(story_id)
    if not story:
        raise NotFoundError("Story", story_id)
    return jsonify(story)
```

**Impact:**
- **Files affected:**
  - `app.py` (remove storage conditionals)
  - `src/shortstory/utils/storage.py` (refactor to repository)
  - `src/shortstory/utils/db_storage.py` (refactor to repository)
  - Create `src/shortstory/utils/repository.py`
- **Breaking changes:** Storage API changes
- **Benefits:** Cleaner code, easier to add new storage backends, better testability

---

## 5. LLM Client Abstraction

**Current Issue:**
LLM client logic is tightly coupled to Google Gemini:
- Hardcoded model names
- Direct API calls in pipeline methods
- Fallback logic mixed with generation logic

**Refactoring Required:**
Implement Provider Pattern for LLM abstraction:

```python
# Abstract LLM provider
class LLMProvider(ABC):
    @abstractmethod
    def generate_story_draft(self, prompt: str, config: Dict) -> str:
        pass
    
    @abstractmethod
    def revise_story(self, text: str, instructions: str) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

# Concrete implementations
class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def generate_story_draft(self, prompt: str, config: Dict) -> str:
        # Gemini-specific implementation
        pass

class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def generate_story_draft(self, prompt: str, config: Dict) -> str:
        # OpenAI-specific implementation
        pass

# Factory
def create_llm_provider() -> Optional[LLMProvider]:
    if google_api_key := os.getenv("GOOGLE_API_KEY"):
        return GeminiLLMProvider(google_api_key)
    elif openai_api_key := os.getenv("OPENAI_API_KEY"):
        return OpenAILLMProvider(openai_api_key)
    return None

# Usage in pipeline
class DraftingStage(PipelineStage):
    def __init__(self, llm_provider: Optional[LLMProvider], template_fallback):
        self.llm_provider = llm_provider
        self.template_fallback = template_fallback
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        if self.llm_provider and self.llm_provider.is_available():
            try:
                draft = self.llm_provider.generate_story_draft(...)
            except Exception:
                draft = self.template_fallback.generate(...)
        else:
            draft = self.template_fallback.generate(...)
        
        context.draft = draft
        return context
```

**Impact:**
- **Files affected:**
  - `src/shortstory/utils/llm.py` (complete rewrite)
  - `src/shortstory/pipeline.py` (use provider abstraction)
  - Create `src/shortstory/providers/` directory
- **Breaking changes:** LLM client API changes
- **Benefits:** Support multiple LLM providers, easier testing, better separation

---

## 6. Error Handling Architecture

**Current Issue:**
Error handling is inconsistent:
- Some functions catch and log, others re-raise
- Error types mixed (ValueError, custom exceptions)
- Error context not always preserved

**Refactoring Required:**
Implement consistent error handling with Result/Either pattern:

```python
from typing import Generic, TypeVar, Union

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

class Result(Generic[T, E]):
    """Result type for explicit error handling."""
    
    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        return Success(value)
    
    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        return Failure(error)
    
    def is_success(self) -> bool:
        return isinstance(self, Success)
    
    def is_failure(self) -> bool:
        return isinstance(self, Failure)
    
    def unwrap(self) -> T:
        if isinstance(self, Success):
            return self.value
        raise self.error

class Success(Result[T, E]):
    def __init__(self, value: T):
        self.value = value

class Failure(Result[T, E]):
    def __init__(self, error: E):
        self.error = error

# Usage in pipeline stages
class DraftingStage(PipelineStage):
    def execute(self, context: PipelineContext) -> Result[PipelineContext, PipelineError]:
        try:
            draft = self.generate_draft(context)
            context.draft = draft
            return Result.success(context)
        except LLMError as e:
            logger.error(f"LLM generation failed: {e}")
            return Result.failure(PipelineError("Draft generation failed", original_error=e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return Result.failure(PipelineError("Unexpected error in drafting", original_error=e))

# Pipeline orchestrator handles results
class ShortStoryPipeline:
    def run_full_pipeline(self, idea, character, theme, genre=None):
        context = PipelineContext(...)
        
        for stage in self.stages:
            result = stage.execute(context)
            if result.is_failure():
                raise result.unwrap()  # Or handle gracefully
            context = result.unwrap()
        
        return context
```

**Impact:**
- **Files affected:** All files with error handling
- **Breaking changes:** Error handling patterns change throughout
- **Benefits:** Explicit error handling, better error context, easier debugging

---

## Summary of Refactoring Complexity

| Refactoring | Complexity | Breaking Changes | Files Affected | Estimated Effort |
|------------|------------|------------------|----------------|------------------|
| 1. Validation Separation | Medium | Medium | 2-3 files | 2-3 days |
| 2. Data Structure | High | High | 10+ files + migration | 1-2 weeks |
| 3. Pipeline Architecture | High | High | 5+ files | 1-2 weeks |
| 4. Storage Abstraction | Medium | Medium | 5-6 files | 3-5 days |
| 5. LLM Provider Pattern | Medium | Medium | 3-4 files | 3-5 days |
| 6. Error Handling | High | High | All files | 1-2 weeks |

## Practical Recommendation: What's Actually Worth It?

### ✅ **DO NOW** (High ROI, Low Risk)

**1. Validation Separation (#1)** - **2-3 days**
- ✅ Low risk, high reward
- ✅ Makes adding new detection types easier (you need this for planned features)
- ✅ Contained scope, won't break existing functionality
- ✅ Directly helps with: Cliché detection system, Character voice analyzer, Memorability scorer

**2. Storage Abstraction (#4)** - **3-5 days**
- ✅ Medium effort, high value
- ✅ You already have database storage, just needs cleanup
- ✅ Removes conditional logic scattered throughout `app.py`
- ✅ Makes future storage changes easier

### ⏸️ **DEFER** (Wait for Need)

**3. LLM Provider Pattern (#5)** - **3-5 days**
- ⚠️ Only worth it if you plan to support multiple LLM providers
- ⚠️ If staying with Gemini, adds complexity without benefit
- ✅ Do it when you actually need OpenAI/Claude support

### ❌ **SKIP FOR NOW** (Low ROI, High Risk)

**4. Data Structure Refactoring (#2)** - **1-2 weeks**
- ❌ High effort, low immediate benefit
- ❌ Premise duplication is annoying but not blocking
- ❌ Migration risk for existing stories
- ✅ Better to fix when you need versioning/sharing features

**5. Pipeline Architecture (#3)** - **1-2 weeks**
- ❌ High effort, low immediate benefit
- ❌ Current structure works fine
- ❌ You still have TODOs for outline/scaffolding - finish features first!
- ✅ Refactor when you need: custom stage ordering, parallel stages, or stage plugins

**6. Error Handling (#6)** - **1-2 weeks**
- ❌ High effort, low immediate benefit
- ❌ Current error handling is functional
- ❌ Result pattern adds complexity that may not be needed
- ✅ Better to standardize incrementally as you touch code

---

## Strategic Assessment

**Your project is in active development** with planned features:
- Character voice analyzer
- Cliché detection system  
- Memorability scorer
- Full outline generation
- Full scaffolding with voice development

**The refactorings that help you build these features faster are worth it.**
**The ones that are "architecturally pure" but don't help you ship are not.**

### Recommended Approach:

1. **Week 1-2:** Do #1 (Validation Separation) - this directly helps you build the detection systems
2. **Week 3:** Do #4 (Storage Abstraction) - clean up the dual-mode mess
3. **Build your features** using the cleaner validation module
4. **Reassess** after shipping: Do you need the other refactorings? Or are you fine?

### The Real Question:

**Are these refactorings blocking you from building features?** 
- If yes → Do them
- If no → Build features, refactor later when you have real pain points

**Most of these are "nice to have" not "need to have."** The validation and storage ones are the exceptions because they directly help with upcoming features.

