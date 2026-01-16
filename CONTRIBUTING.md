# Contributing to Short Story Pipeline

Thank you for your interest in contributing to the Short Story Pipeline! This guide will help you get started and ensure your contributions align with the project's standards.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style & Conventions](#code-style--conventions)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Definition of Done](#definition-of-done)

## Getting Started

### Prerequisites

- **Python 3.9+** with pip
- **Google Gemini API key** (see [SETUP_GOOGLE.md](SETUP_GOOGLE.md))
- **Git** for version control

### Initial Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ShortStory.git
   cd ShortStory
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Verify setup:**
   ```bash
   python check_setup.py
   ```

6. **Run tests to ensure everything works:**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### Branch Strategy

- **Main branch**: Production-ready code only
- **Feature branches**: `feature/description-of-feature`
- **Bug fix branches**: `fix/description-of-bug`
- **Spike/research branches**: `spike/description-of-research`

### Making Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the [Code Style & Conventions](#code-style--conventions) below
   - Write tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run specific test file
   pytest tests/test_your_feature.py -v
   
   # Run with coverage
   pytest tests/ --cov=src/shortstory --cov-report=term
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `chore:` for maintenance tasks

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style & Conventions

### Python Style

- **Naming**: Use `snake_case` for functions and variables, `PascalCase` for classes
- **Type Hints**: Always use type hints for function parameters and return values
- **Optional Types**: Use `Optional[Type]` for nullable values, not `Type | None`
- **Dict Types**: Use `Dict[str, Any]` for flexible dictionaries, prefer Pydantic models when structure is known
- **Imports**: 
  - Group imports: stdlib, third-party, local
  - Use absolute imports from `src.shortstory.*`
  - Avoid circular dependencies (use `TYPE_CHECKING` for type-only imports)

### Documentation

- **Docstrings**: All functions, classes, and modules must have docstrings
- **Style**: Use Google-style docstrings with `Args`/`Returns`/`Raises` sections
- **Comments**: Keep comments up-to-date; remove outdated or misleading comments
- **Documentation Files**: 
  - Reference `CONCEPTS.md` as single source of truth for terminology
  - Reference `pipeline.md` for pipeline architecture
  - Reference `PROJECT_STRUCTURE.md` for project organization

### Architecture Patterns

- **Provider Pattern**: LLM providers implement `BaseLLMClient` abstract class
- **Pipeline Stages**: Follow 5-stage pipeline (Premise → Outline → Scaffold → Draft → Revise)
- **Separation of Concerns**: Keep validation, generation, and storage logic separate
- **Modularity**: Each pipeline stage should be independently testable

### Code Quality Principles

- **DRY**: Extract common functionality into reusable functions, classes, or modules
- **Single Responsibility**: Each function/class should have one clear purpose
- **Descriptive Names**: Use descriptive names that clearly indicate purpose

### Logging

- **Module Loggers**: Use `logger = logging.getLogger(__name__)` at module level
- **Log Levels**: Use appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Context**: Include relevant context in log messages (word counts, story IDs, etc.)

### Error Handling

- **Model Validation**: Invalid model names raise `ValueError` with clear message
- **Network Errors**: Retry with exponential backoff (use existing retry logic)
- **API Failures**: Log errors with context, return meaningful error messages to users
- **Validation Errors**: Use Pydantic validation errors for model validation failures

### LLM Integration

- **Provider**: Google Gemini API for text generation only (no image models)
- **Valid Models**: `gemini-2.5-flash`, `gemini-2.0-flash-exp`, `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-1.0-pro`
- **Default**: `gemini-2.5-flash`
- **Factory Pattern**: Use `get_default_provider()` from `src/shortstory/providers/factory.py` for provider instances
- **Validation**: All models validated against `ALLOWED_MODELS` in `src/shortstory/providers/gemini.py`

### Pydantic Models

- Use models from `src/shortstory/models.py` (PremiseModel, OutlineModel, StoryModel, etc.)
- Prefer Pydantic models over raw dictionaries when structure is known

## Testing Requirements

### Test Framework

- **Framework**: pytest with fixtures in `tests/conftest.py`
- **Test Constants**: Use constants from `tests/test_constants.py` (GENRE_*, HTTP_*)
- **Isolation**: Each test must be independent; use `tmp_path` for temporary files

### Mocking Strategy

- Mock factory/getter functions (`app.get_pipeline()`, `app.get_story_repository()`)
- Use standardized fixtures: `mock_llm_client`, `mock_pipeline`, `mock_redis`
- Never mock module-level instances directly
- See `tests/test_mocking_helpers.py` for patterns

### Test Coverage

- **Target Coverage**: 85%+ for unit tests
- **Priority Areas**: Database storage, LLM utilities, genres, exports
- Run coverage before submitting PRs:
  ```bash
  pytest tests/ --cov=src/shortstory --cov-report=term --cov-report=html
  ```

### Writing Tests

- Write tests for all new functionality
- Include edge cases and error conditions
- Test both success and failure paths
- Use descriptive test names: `test_function_name_scenario_expected_result`

See [TESTING.md](TESTING.md) for detailed testing guidelines.

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   pytest tests/ -v
   ```

2. **Check code coverage:**
   ```bash
   pytest tests/ --cov=src/shortstory --cov-report=term
   ```

3. **Verify no linting errors:**
   - Follow Python style guidelines
   - Ensure all imports are used

4. **Update documentation:**
   - Update relevant `.md` files if your changes affect functionality
   - Add docstrings to new functions/classes
   - Update `CHANGELOG.md` if applicable

5. **Test manually:**
   - Run the web application and test your changes
   - Verify the CLI works if you changed CLI functionality

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
```

### Review Process

- All PRs require at least one review before merging
- Address review comments promptly
- Keep PRs focused and reasonably sized
- Rebase on main before merging if there are conflicts

## Definition of Done

A feature, bug fix, or change is considered **Done** when all of the following criteria are met:

### Code Quality

- ✅ **Code Review**: Code has been reviewed and approved by at least one maintainer
- ✅ **Style Compliance**: Code follows all style guidelines and conventions outlined in this document
- ✅ **Type Safety**: All functions have proper type hints; Pydantic models used where appropriate
- ✅ **Documentation**: All new functions, classes, and modules have Google-style docstrings
- ✅ **No Technical Debt**: No TODO comments, temporary hacks, or known issues introduced

### Testing

- ✅ **Unit Tests**: All new functionality has corresponding unit tests
- ✅ **Test Coverage**: Code coverage meets or exceeds 85% for new code
- ✅ **All Tests Pass**: All existing and new tests pass (`pytest tests/ -v`)
- ✅ **Edge Cases**: Edge cases and error conditions are tested
- ✅ **Integration**: Manual testing completed in the web application (if applicable)

### Functionality

- ✅ **Requirements Met**: Feature meets all specified requirements
- ✅ **Error Handling**: Proper error handling and user-friendly error messages
- ✅ **Backward Compatibility**: Changes don't break existing functionality (unless intentional breaking change)
- ✅ **Performance**: No significant performance regressions introduced

### Documentation

- ✅ **Code Documentation**: Docstrings added for all new public functions/classes
- ✅ **User Documentation**: README.md or relevant docs updated if user-facing changes
- ✅ **Architecture Docs**: Architecture documentation updated if structural changes made
- ✅ **API Documentation**: API endpoints documented if new endpoints added

### Security & Best Practices

- ✅ **Input Validation**: All user inputs are validated and sanitized
- ✅ **Security Review**: Security implications considered (XSS, injection, etc.)
- ✅ **Sensitive Data**: No sensitive data (API keys, passwords) committed to repository
- ✅ **Environment Variables**: New configuration uses environment variables, not hardcoded values

### Story Generation Specific

- ✅ **Word Count**: Story generation meets minimum word count requirements (4000+ words)
- ✅ **Completion**: Stories complete with full thoughts, not cut off mid-sentence
- ✅ **Dialogue**: Stories include substantial, complete dialogue when appropriate
- ✅ **Distinctiveness**: Generated stories pass distinctiveness validation
- ✅ **Voice Consistency**: Character and narrative voice maintained throughout pipeline

### Deployment Readiness

- ✅ **Environment Config**: All configuration uses environment variables
- ✅ **Logging**: Appropriate logging added for debugging and monitoring
- ✅ **Error Messages**: Error messages are user-friendly and actionable
- ✅ **Migration Scripts**: Database/storage migrations provided if data structure changes

### Git & Version Control

- ✅ **Commit Messages**: Commits use conventional commit format (`feat:`, `fix:`, etc.)
- ✅ **Branch Clean**: Branch is up-to-date with main (rebased if needed)
- ✅ **No Merge Conflicts**: No unresolved merge conflicts
- ✅ **Clean History**: Git history is clean and logical (no "WIP" or "fix typo" commits)

### Final Checklist

Before marking as Done, verify:

- [ ] All items above are checked
- [ ] PR description is complete and accurate
- [ ] Code has been tested in the target environment
- [ ] No console errors or warnings in browser (for frontend changes)
- [ ] No linting errors or warnings
- [ ] All dependencies are properly declared in `requirements.txt`

---

## Questions?

If you have questions about contributing, please:

1. Check existing documentation (README.md, CONCEPTS.md, TESTING.md)
2. Review existing code for patterns and examples
3. Open an issue for discussion before starting major changes
4. Ask in PR comments for clarification during review

Thank you for contributing to Short Story Pipeline! 🎉
