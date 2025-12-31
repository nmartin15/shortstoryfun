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

### Command Line Usage

1. **Set up Google API key** (see [SETUP_GOOGLE.md](SETUP_GOOGLE.md))
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Run pipeline examples** in `examples/`

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for repository layout.

## Documentation

- **[CONCEPTS.md](CONCEPTS.md)** - Core principles and terminology
- **[SETUP_GOOGLE.md](SETUP_GOOGLE.md)** - Google Gemini API setup guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[PRODUCTION_IMPROVEMENTS.md](PRODUCTION_IMPROVEMENTS.md)** - Production improvements summary

## Production Features

- ✅ **Enhanced error handling** with structured responses and logging
- ✅ **Rate limiting** to prevent abuse and ensure fair resource usage
- ✅ **Production-ready deployment** with Gunicorn configuration
- ✅ **Comprehensive logging** for monitoring and debugging
- ✅ **Environment-based configuration** for development and production

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

## Roadmap
- ✅ Google Gemini API integration
- ✅ AI-powered story generation and revision
- ✅ Production deployment setup
- ✅ Error handling and rate limiting
- ✅ Full outline generation with detailed beats
- ✅ Full scaffolding with voice development
- ✅ Memorability scorer with multi-dimensional analysis
- ✅ Core distinctiveness tools (see [CONCEPTS.md](CONCEPTS.md))
- Integrate with flash fiction pipeline for hybrid workflows

