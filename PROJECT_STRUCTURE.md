# Project Structure

```
ShortStory/
├── src/
│   └── shortstory/          # Main package
│       ├── __init__.py      # Package initialization
│       └── pipeline.py      # ShortStoryPipeline class
│
├── examples/                # Example scripts
│   └── sample_story.py      # Example pipeline usage
│
├── tests/                   # Unit tests
│   ├── __init__.py
│   └── test_pipeline.py     # Pipeline tests
│
├── docs/                    # Documentation (future)
│
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
│
├── README.md               # Main documentation
├── CONCEPTS.md             # Core principles (DRY source of truth)
├── pipeline.md             # Pipeline architecture
├── REQUIREMENTS_TRACKER.md # Requirements tracker
├── tasks.md                # Task notes
├── planning.md             # Product requirements document
└── PROJECT_STRUCTURE.md     # This file
```

## Directory Purposes

### `src/shortstory/`
Main package containing the pipeline implementation. Follows modular design with separate modules for each stage (to be added).

### `examples/`
Example scripts demonstrating pipeline usage. Start here to understand how to use the pipeline.

### `tests/`
Unit tests for pipeline functionality. Includes tests for word count enforcement, distinctiveness validation, and voice consistency.

### Documentation Files

**Core Documentation:**
- **README.md**: Quick start and overview
- **CONCEPTS.md**: Core principles and terminology (single source of truth)
- **pipeline.md**: Detailed pipeline architecture
- **planning.md**: Product requirements document (PRD)

**Development & Tracking:**
- **REQUIREMENTS_TRACKER.md**: Functional and non-functional requirements checklist
- **tasks.md**: Task tracking
- **PROJECT_STRUCTURE.md**: This file

**Setup & Configuration:**
- **SETUP_GOOGLE.md**: Google Gemini API setup
- **STORAGE_IMPLEMENTATION.md**: Storage backends and configuration
- **STORAGE_MIGRATION.md**: Migration guide

**Deployment & Production:**
- **DEPLOYMENT.md**: Production deployment guide
- **PRODUCTION_IMPROVEMENTS.md**: Production improvements summary
- **BACKGROUND_JOBS.md**: Background job processing

**Testing & Quality:**
- **TESTING.md**: Testing guide
- **TEST_COVERAGE_IMPROVEMENTS.md**: Test coverage improvement plans

**Architecture & Models:**
- **ARCHITECTURAL_REFACTORING.md**: Refactoring suggestions
- **STORY_MODEL_STANDARDIZATION.md**: Story model standardization
- **stories/STORY_JSON_SCHEMA.md**: Story JSON schema

## Future Structure

As the project grows, additional modules will be added:

```
src/shortstory/
├── pipeline.py              # Main pipeline class
├── premise.py               # Premise capture module
├── outline.py               # Outline generation
├── scaffold.py              # Scaffolding module
├── draft.py                 # Drafting module
├── revision.py              # Revision module
├── tools/
│   ├── voice_analyzer.py    # Character voice analyzer
│   ├── cliche_detector.py   # Cliché detection system
│   ├── memorability.py      # Memorability scorer
│   └── filters.py           # Anti-generic filters
└── utils/
    ├── word_count.py        # Word count validation
    └── validation.py        # Distinctiveness validation
```

