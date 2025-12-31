# Test Coverage Improvements — Nice-to-Have Enhancements

This document outlines test coverage improvements that would enhance the quality and reliability of the Short Story Pipeline project. These are **nice-to-have enhancements** that go beyond the current test suite.

## 📊 Current Test Coverage Status

Based on the AI review and codebase analysis:
- ✅ **Pipeline tests**: Good coverage for core pipeline stages (38 tests)
- ✅ **Validation tests**: Comprehensive distinctiveness and validation checks
- ✅ **Word count tests**: Basic functionality covered
- ✅ **Template draft tests**: 11 tests for fallback generation
- ✅ **Rule-based revision tests**: 10 tests for revision logic
- ⚠️ **API tests**: Basic validation, could be more comprehensive
- ❌ **Database storage tests**: Missing
- ❌ **LLM utility tests**: Missing
- ❌ **Genre configuration tests**: Missing
- ❌ **Export functionality tests**: Missing
- ❌ **Frontend/JavaScript tests**: Missing
- ❌ **Integration tests**: Limited coverage
- ❌ **Performance tests**: Missing
- ❌ **Security tests**: Missing

---

## 🎯 Priority 1: Core Functionality Tests

### 1. Database Storage Tests (`tests/test_db_storage.py`)

**Why**: The database storage module (`src/shortstory/utils/db_storage.py`) is critical for production but has no test coverage.

**Test Cases Needed**:
- ✅ Database initialization and schema creation
- ✅ Story CRUD operations (create, read, update, delete)
- ✅ Story listing with pagination
- ✅ Story search/filtering functionality
- ✅ Database transaction rollback on errors
- ✅ Concurrent access handling
- ✅ Database migration scenarios
- ✅ Redis cache integration (if enabled)
- ✅ Error handling for database connection failures
- ✅ Data integrity checks (foreign keys, constraints)
- ✅ Large dataset performance (1000+ stories)

**Example Test Structure**:
```python
class TestStoryStorage:
    def test_save_and_load_story(self):
        """Test saving and loading a story from database."""
        storage = StoryStorage()
        story = {"id": "test_123", "text": "Test story"}
        storage.save_story(story)
        loaded = storage.load_story("test_123")
        assert loaded["id"] == "test_123"
    
    def test_list_stories_pagination(self):
        """Test paginated story listing."""
        storage = StoryStorage()
        # Create 25 stories
        for i in range(25):
            storage.save_story({"id": f"story_{i}", "text": f"Story {i}"})
        
        # Test pagination
        page1 = storage.list_stories(page=1, per_page=10)
        assert len(page1) == 10
        assert page1[0]["id"] == "story_0"
```

---

### 2. LLM Utility Tests (`tests/test_llm.py`)

**Why**: The LLM module handles API communication, token counting, and model validation but lacks tests.

**Test Cases Needed**:
- ✅ Model name validation (whitelist checking)
- ✅ Token counting accuracy (with and without tiktoken)
- ✅ Context window size calculations
- ✅ API request formatting
- ✅ API response parsing
- ✅ Error handling for API failures (timeout, rate limit, invalid key)
- ✅ Fallback behavior when tiktoken unavailable
- ✅ Token estimation for different text lengths
- ✅ Special character handling in prompts
- ✅ Prompt truncation when exceeding context window
- ✅ Retry logic for transient failures

**Example Test Structure**:
```python
class TestLLMClient:
    def test_model_validation(self):
        """Test that only allowed models are accepted."""
        with pytest.raises(ValueError):
            LLMClient(model="invalid-model")
    
    def test_token_counting(self):
        """Test accurate token counting."""
        client = LLMClient()
        text = "This is a test sentence."
        tokens = client._estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_api_error_handling(self):
        """Test handling of API errors."""
        # Mock API to return 429 (rate limit)
        # Verify proper error handling
```

---

### 3. Genre Configuration Tests (`tests/test_genres.py`)

**Why**: Genre configurations drive story structure but aren't validated by tests.

**Test Cases Needed**:
- ✅ All genres have required fields (framework, outline, constraints)
- ✅ Outline structure validation (beginning, middle, end)
- ✅ Framework types are valid
- ✅ Constraint values are appropriate for each genre
- ✅ Genre retrieval functions work correctly
- ✅ Invalid genre handling
- ✅ Genre-specific constraint application
- ✅ Edge cases (empty genres, missing fields)

**Example Test Structure**:
```python
class TestGenres:
    def test_all_genres_have_required_fields(self):
        """Test that all genres have required configuration."""
        genres = get_available_genres()
        for genre in genres:
            config = get_genre_config(genre)
            assert "framework" in config
            assert "outline" in config
            assert "constraints" in config
    
    def test_outline_structure(self):
        """Test that outline structure is valid."""
        config = get_genre_config("Horror")
        outline = config["outline"]
        assert len(outline) >= 3  # Beginning, middle, end
```

---

### 4. Export Functionality Tests (`tests/test_export.py`)

**Why**: Export functions (PDF, Markdown, TXT, DOCX, EPUB) have no test coverage.

**Test Cases Needed**:
- ✅ PDF export generates valid PDF file
- ✅ Markdown export preserves formatting
- ✅ TXT export creates plain text
- ✅ DOCX export (if dependency available)
- ✅ EPUB export (if dependency available)
- ✅ Filename sanitization (XSS prevention)
- ✅ Large story export (near word limit)
- ✅ Special character handling in titles
- ✅ Missing dependency error handling
- ✅ Export with empty story text
- ✅ Export with malformed story data

**Example Test Structure**:
```python
class TestExport:
    def test_pdf_export(self):
        """Test PDF export functionality."""
        story_text = "# Test Story\n\nThis is a test."
        response = export_pdf(story_text, "Test Story", "test_123")
        assert response.status_code == 200
        assert "application/pdf" in response.content_type
    
    def test_filename_sanitization(self):
        """Test that filenames are properly sanitized."""
        malicious_title = "../../etc/passwd<script>alert('xss')</script>"
        sanitized = sanitize_filename(malicious_title)
        assert "<" not in sanitized
        assert ".." not in sanitized
```

---

## 🎯 Priority 2: API and Integration Tests

### 5. Enhanced API Endpoint Tests (`tests/test_api_comprehensive.py`)

**Why**: Current API tests (`test_api.py`) validate status codes but not response structure/content.

**Test Cases Needed**:
- ✅ Story generation response structure validation
- ✅ Story content quality checks (minimum length, structure)
- ✅ Error response format validation
- ✅ Rate limiting behavior
- ✅ Request validation (missing fields, invalid types)
- ✅ Story retrieval endpoint tests
- ✅ Story update/revision endpoint tests
- ✅ Story comparison endpoint tests
- ✅ Story deletion endpoint tests
- ✅ Story listing endpoint with filters
- ✅ Concurrent request handling
- ✅ Large payload handling
- ✅ Authentication/authorization (if added)

**Example Test Structure**:
```python
class TestAPIComprehensive:
    def test_story_generation_response_structure(self):
        """Test that story generation returns complete data."""
        response = requests.post(f"{BASE_URL}/api/generate", json=payload)
        data = response.json()
        
        # Validate structure
        assert "success" in data
        assert "story_id" in data
        assert "story" in data
        assert "word_count" in data
        assert "max_words" in data
        
        # Validate content quality
        assert len(data["story"]) >= 100  # Minimum length
        assert data["word_count"] > 0
        assert data["word_count"] <= data["max_words"]
    
    def test_rate_limiting(self):
        """Test that rate limiting works correctly."""
        # Make 60 requests in quick succession
        # Verify 50th request succeeds, 51st fails with 429
```

---

### 6. Integration Tests (`tests/test_integration.py`)

**Why**: End-to-end scenarios test the full system working together.

**Test Cases Needed**:
- ✅ Full pipeline: premise → outline → scaffold → draft → revise
- ✅ Story generation with all optional fields
- ✅ Story generation with minimal fields
- ✅ Story save → load → update → export workflow
- ✅ Story revision history tracking
- ✅ Multiple story generation in sequence
- ✅ Database persistence across server restarts
- ✅ Error recovery scenarios (LLM fails, fallback works)
- ✅ Word count enforcement throughout pipeline
- ✅ Genre-specific pipeline execution

**Example Test Structure**:
```python
class TestIntegration:
    def test_full_pipeline_with_database(self):
        """Test complete pipeline with database storage."""
        # Generate story
        story = pipeline.run_full_pipeline(...)
        
        # Save to database
        story_storage.save_story(story)
        
        # Load from database
        loaded = story_storage.load_story(story["id"])
        
        # Verify integrity
        assert loaded["text"] == story["text"]
        assert loaded["word_count"] == story["word_count"]
    
    def test_error_recovery(self):
        """Test that system recovers from LLM failures."""
        # Mock LLM to fail
        # Verify template fallback works
        # Verify story is still generated
```

---

## 🎯 Priority 3: Frontend and UI Tests

### 7. JavaScript/Frontend Tests (`tests/test_frontend.js` or `tests/test_frontend.py` with Selenium/Playwright)

**Why**: Frontend JavaScript (`static/js/app.js`) has no test coverage.

**Test Cases Needed**:
- ✅ Form submission and validation
- ✅ Story generation UI flow
- ✅ Auto-save functionality
- ✅ Export menu interactions
- ✅ Story browser/list functionality
- ✅ Revision history display
- ✅ Error message display
- ✅ Loading indicators
- ✅ Word count updates
- ✅ XSS prevention in displayed content
- ✅ Responsive design behavior
- ✅ Accessibility (keyboard navigation, screen readers)

**Tools**: Jest, Mocha, or Playwright for E2E tests

**Example Test Structure**:
```javascript
// Using Jest or similar
describe('Story Generation', () => {
    test('form submission generates story', async () => {
        // Fill form
        // Submit
        // Verify story appears
    });
    
    test('auto-save works correctly', async () => {
        // Edit story
        // Wait for auto-save
        // Verify save was called
    });
});
```

---

## 🎯 Priority 4: Performance and Load Tests

### 8. Performance Tests (`tests/test_performance.py`)

**Why**: Ensure system handles production load.

**Test Cases Needed**:
- ✅ Story generation response time (target: < 30s)
- ✅ Database query performance (1000+ stories)
- ✅ Concurrent story generation (10+ simultaneous)
- ✅ Memory usage during bulk operations
- ✅ Token counting performance (large texts)
- ✅ Export performance (large stories)
- ✅ Database connection pooling
- ✅ Redis cache hit rates
- ✅ API rate limiting performance impact

**Example Test Structure**:
```python
class TestPerformance:
    @pytest.mark.slow
    def test_concurrent_story_generation(self):
        """Test system handles concurrent requests."""
        import concurrent.futures
        
        def generate():
            return pipeline.run_full_pipeline(...)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate) for _ in range(10)]
            results = [f.result() for f in futures]
        
        assert all(r is not None for r in results)
        assert all(r["word_count"] > 0 for r in results)
```

---

## 🎯 Priority 5: Security Tests

### 9. Security Tests (`tests/test_security.py`)

**Why**: Security vulnerabilities can be catastrophic.

**Test Cases Needed**:
- ✅ XSS prevention in story content
- ✅ XSS prevention in filenames
- ✅ SQL injection prevention (if using raw queries)
- ✅ Path traversal prevention in file operations
- ✅ Input sanitization (special characters, control chars)
- ✅ Rate limiting effectiveness
- ✅ API key validation
- ✅ Model name whitelist enforcement
- ✅ File upload validation (if added)
- ✅ CSRF protection (if added)

**Example Test Structure**:
```python
class TestSecurity:
    def test_xss_prevention_in_story_content(self):
        """Test that XSS attempts are sanitized."""
        malicious_story = "<script>alert('xss')</script>Story text"
        # Display in UI
        # Verify script tags are escaped
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        malicious_id = "../../etc/passwd"
        # Attempt to load story
        # Verify error or sanitization
```

---

## 🎯 Priority 6: Edge Cases and Error Handling

### 10. Edge Case Tests (`tests/test_edge_cases.py`)

**Why**: Edge cases often reveal bugs.

**Test Cases Needed**:
- ✅ Empty input handling
- ✅ Very long inputs (exceeding limits)
- ✅ Special characters (Unicode, emoji)
- ✅ Null/None value handling
- ✅ Missing optional fields
- ✅ Invalid data types
- ✅ Network timeouts
- ✅ Partial failures (some stages succeed, others fail)
- ✅ Database corruption scenarios
- ✅ Disk full scenarios
- ✅ Memory exhaustion scenarios

**Example Test Structure**:
```python
class TestEdgeCases:
    def test_empty_story_idea(self):
        """Test handling of empty story idea."""
        with pytest.raises(ValueError):
            pipeline.capture_premise(idea="", ...)
    
    def test_unicode_characters(self):
        """Test handling of Unicode characters."""
        idea = "A story with émojis 🎭 and spéciál chàracters"
        premise = pipeline.capture_premise(idea=idea, ...)
        assert premise is not None
```

---

## 🎯 Priority 7: Test Infrastructure Improvements

### 11. Test Utilities and Fixtures

**Why**: Better test infrastructure makes writing tests easier.

**Improvements Needed**:
- ✅ Mock LLM client for fast, deterministic tests
- ✅ Database fixtures (test database, sample stories)
- ✅ API client fixtures
- ✅ Test data generators (random stories, characters, themes)
- ✅ Performance benchmarking utilities
- ✅ Test coverage reporting (pytest-cov)
- ✅ Continuous integration setup (GitHub Actions, etc.)

**Example Structure**:
```python
# tests/conftest.py
@pytest.fixture
def mock_llm_client(monkeypatch):
    """Mock LLM client for testing."""
    def mock_generate(*args, **kwargs):
        return "Mock generated story text"
    
    monkeypatch.setattr(LLMClient, "generate", mock_generate)
    return mock_generate

@pytest.fixture
def test_database(tmp_path):
    """Create a test database."""
    db_path = tmp_path / "test.db"
    # Initialize test database
    return db_path
```

---

## 📈 Test Coverage Goals

### Current State
- **Estimated Coverage**: ~60-70% (pipeline, validation, word count)

### Target State
- **Unit Tests**: 85%+ coverage
- **Integration Tests**: All critical workflows covered
- **API Tests**: All endpoints with comprehensive validation
- **Frontend Tests**: Core user interactions covered

### Metrics to Track
- Code coverage percentage (aim for 85%+)
- Test execution time (keep under 5 minutes for full suite)
- Test reliability (flaky test rate < 1%)
- Test maintainability (clear, focused tests)

---

## 🛠️ Implementation Recommendations

### Phase 1: Foundation (Weeks 1-2)
1. Database storage tests
2. LLM utility tests
3. Genre configuration tests
4. Enhanced API endpoint tests

### Phase 2: Integration (Weeks 3-4)
5. Integration tests
6. Export functionality tests
7. Edge case tests

### Phase 3: Advanced (Weeks 5-6)
8. Frontend/JavaScript tests
9. Performance tests
10. Security tests

### Phase 4: Infrastructure (Ongoing)
11. Test utilities and fixtures
12. CI/CD integration
13. Coverage reporting

---

## 📝 Notes

- **Test Independence**: Each test should be independent and not rely on other tests
- **Test Speed**: Keep unit tests fast (< 1s each), integration tests can be slower
- **Test Data**: Use fixtures and factories for consistent test data
- **Mocking**: Mock external dependencies (LLM API, database) for unit tests
- **Documentation**: Document test purpose and expected behavior
- **Maintenance**: Review and update tests when code changes

---

## 🔗 Related Documents

- [TESTING.md](TESTING.md) - Current testing guide
- [ai-review-2025-12-31T15-41-28.md](ai-review-2025-12-31T15-41-28.md) - AI review with testing issues
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project structure overview

---

**Last Updated**: 2025-12-31
**Status**: Planning Document - Nice-to-Have Enhancements

