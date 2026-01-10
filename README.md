# Short Story Pipeline

This repository provides a modular pipeline for short story creation that prioritizes **distinctive voice, memorable characters, and non-generic language**. Every word must earn its place.

> **See [CONCEPTS.md](CONCEPTS.md) for core principles and terminology.**

- Premise capture (unique idea, distinctive character, resonant theme)
- Outline (beginning, middle, end with unexpected beats)
- Scaffolding (POV, tone, style that creates voice)
- Drafting (prose narrative with precision and pop)
- Revision (language sharpening, character deepening, cliché elimination)

## Features
- **AI-powered story generation** via Google Gemini API
- **Memorability Scorer** - Multi-dimensional scoring (language precision, character uniqueness, voice strength, beat originality)
- **Full Outline Generation** - Detailed beats with unexpected moments and voice opportunities
- **Full Scaffolding with Voice Development** - Narrative voice, character voice profiles, conflict mapping, sensory specificity
- Enforces word count (≤ 7500 words) while maximizing impact
- Anti-generic filters (see [CONCEPTS.md](CONCEPTS.md))
- Voice development tools (see [CONCEPTS.md](CONCEPTS.md))
- Character distinctiveness validation (see [CONCEPTS.md](CONCEPTS.md))
- Conflict-first scaffolding for clarity
- Modular design for extensibility
- Automatic fallback to template-based generation if LLM unavailable

## Getting Started

### Prerequisites

- **Google Gemini API key** (see [SETUP_GOOGLE.md](SETUP_GOOGLE.md) for setup)
- **Python 3.9+** with pip

### Web Application (Recommended)

1. **Get API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **Set environment variable:**
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify setup (optional):**
   ```bash
   python check_setup.py
   ```

5. **Start the web server:**
   ```bash
   python app.py
   ```

5. **Open your browser** to `http://localhost:5000`

6. **Enter your story idea, character, and theme**, then click "Generate Story"

7. **Edit the generated story** in the text editor

> **Note:** If the Google API is not available, the pipeline will automatically fall back to template-based generation.

### Command Line Interface (CLI)

The CLI provides local story management without needing the web UI:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **List all stories:**
   ```bash
   python cli.py list-stories
   # Or with options:
   python cli.py list-stories --format json --page 1 --per-page 10
   ```

3. **Delete a story:**
   ```bash
   python cli.py delete-story <story_id>
   # Skip confirmation:
   python cli.py delete-story <story_id> --confirm
   ```

4. **Export a story:**
   ```bash
   python cli.py export-story <story_id> pdf
   python cli.py export-story <story_id> markdown -o my_story.md
   # Supported formats: pdf, markdown, txt, docx, epub
   ```

5. **Validate a story:**
   ```bash
   python cli.py validate-story <story_id>
   # With detailed results:
   python cli.py validate-story <story_id> --verbose
   ```

See `python cli.py --help` for more information.

### Command Line Usage (Pipeline Examples)

1. **Set up Google API key** (see [SETUP_GOOGLE.md](SETUP_GOOGLE.md))
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Run pipeline examples** in `examples/`

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for repository layout.

## Documentation

### Core Documentation
- **[CONCEPTS.md](CONCEPTS.md)** - Core principles and terminology (single source of truth)
- **[pipeline.md](pipeline.md)** - Pipeline architecture and stages
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization

### Setup & Configuration
- **[SETUP_GOOGLE.md](SETUP_GOOGLE.md)** - Google Gemini API setup guide
- **[STORAGE_IMPLEMENTATION.md](STORAGE_IMPLEMENTATION.md)** - Storage backends and configuration
- **[STORAGE_MIGRATION.md](STORAGE_MIGRATION.md)** - Migration from file to database storage

### Deployment & Production
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[PRODUCTION_IMPROVEMENTS.md](PRODUCTION_IMPROVEMENTS.md)** - Production improvements summary
- **[BACKGROUND_JOBS.md](BACKGROUND_JOBS.md)** - Background job processing with RQ

### Development & Testing
- **[TESTING.md](TESTING.md)** - Testing guide
- **[TEST_COVERAGE_IMPROVEMENTS.md](TEST_COVERAGE_IMPROVEMENTS.md)** - Test coverage improvement plans

### Security
- **Security Features** - See Security section below

### Data Models & Architecture
- **[STORY_JSON_SCHEMA.md](stories/STORY_JSON_SCHEMA.md)** - Story JSON file structure
- **[STORY_MODEL_STANDARDIZATION.md](STORY_MODEL_STANDARDIZATION.md)** - Story model standardization approach (✅ **Now using Pydantic models**)
- **[ARCHITECTURAL_REFACTORING.md](ARCHITECTURAL_REFACTORING.md)** - Architectural refactoring suggestions

## Production Features

- ✅ **Enhanced error handling** with structured responses and logging
- ✅ **Rate limiting** to prevent abuse and ensure fair resource usage
- ✅ **Production-ready deployment** with Gunicorn configuration
- ✅ **Comprehensive logging** for monitoring and debugging
- ✅ **Environment-based configuration** for development and production

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

## Security

This application implements multiple security measures to protect against common vulnerabilities:

### Input Sanitization

- **Filename Sanitization**: All user-provided titles and story IDs are sanitized before use in file operations to prevent:
  - Path traversal attacks (`../`, `/`, `\`)
  - Command injection (`|`, `&`, `;`, `` ` ``, `$`)
  - OS-specific issues (Windows forbidden characters: `:`, `*`, `?`, `<`, `>`, `"`)
  - XSS in download attributes (script tags, HTML entities, event handlers)

- **XSS Prevention**: All user-controlled data displayed in the UI is properly escaped:
  - Story titles, premises, and metadata in the story browser
  - Validation results including clichés and suggestions
  - Revision history data
  - All API responses are sanitized before rendering

### Model Security

- **Dynamic Model Validation**: The LLM client fetches available models dynamically from the API to prevent using deprecated or insecure models
- **Fallback Protection**: If dynamic fetching fails, a fallback list is used with security warnings logged
- **Model Name Validation**: All model names are validated against the current API list before use

### CDN Security

- **Version Pinning**: External JavaScript libraries are pinned to specific versions (e.g., Lucide icons)
- **Font Preloading**: Critical fonts are preloaded to improve performance and reduce dependency on external CDNs
- **Security Headers**: All external resources use `crossorigin="anonymous"` for CORS protection
- **Self-Hosting Recommendations**: Documentation includes guidance for self-hosting assets in production for better security control

### API Security

- **Input Validation**: All API endpoints validate and sanitize input data
- **Error Handling**: Structured error responses prevent information leakage
- **Rate Limiting**: API endpoints are rate-limited to prevent abuse

### Best Practices

1. **Never trust user input**: All user-provided data is sanitized before use
2. **Defense in depth**: Multiple layers of validation and sanitization
3. **Security logging**: Security-related events (e.g., fallback model list usage) are logged
4. **Regular updates**: Keep dependencies updated and review security advisories

### Reporting Security Issues

If you discover a security vulnerability, please report it responsibly. Do not open public issues for security vulnerabilities.

## Roadmap
- ✅ Google Gemini API integration
- ✅ AI-powered story generation and revision
- ✅ Production deployment setup
- ✅ Error handling and rate limiting
- ✅ Full outline generation with detailed beats
- ✅ Full scaffolding with voice development
- ✅ Memorability scorer with multi-dimensional analysis
- ✅ Core distinctiveness tools (see [CONCEPTS.md](CONCEPTS.md))
- ✅ **Pydantic model integration** - Type-safe pipeline with automatic validation
- Integrate with flash fiction pipeline for hybrid workflows

