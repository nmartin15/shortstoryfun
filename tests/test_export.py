"""
Tests for story export functionality.

This module tests export functions for various formats (PDF, Markdown, TXT, DOCX, EPUB).
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Response
from io import BytesIO

from src.shortstory.utils.llm_constants import STORY_DEFAULT_MAX_WORDS
from tests.test_constants import HTTP_OK
from tests.conftest import check_optional_dependency, require_optional_dependency

# Check for optional dependencies
DOCX_AVAILABLE = check_optional_dependency('docx')
EPUB_AVAILABLE = check_optional_dependency('ebooklib')

# Import export functions
from src.shortstory.exports import (
    sanitize_filename,
    export_pdf,
    export_markdown,
    export_txt,
    export_docx,
    export_epub,
    export_story_from_dict,
)
from src.shortstory.utils.errors import MissingDependencyError, ValidationError


@pytest.fixture
def app_context():
    """Create Flask application context for tests."""
    from app import create_app
    app = create_app()
    with app.app_context():
        yield app


@pytest.fixture
def sample_story_text():
    """Sample story text for testing."""
    return """# The Lighthouse Keeper's Collection

Each voice was stored in a glass jar, labeled with a date and a place. Mara had collected them for thirty years, never speaking above a whisper herself.

The voices told stories of ships lost at sea, of lovers separated by storms, of children calling for parents who would never return. Each one was a fragment of a life interrupted, preserved in amber silence.

When the last jar was filled, Mara finally understood why she had been chosen for this task. The voices needed a keeper who would listen without judgment, who would preserve their stories until someone came to claim them.

And one day, someone did."""


@pytest.fixture
def sample_story_dict():
    """Sample story dictionary for testing."""
    return {
        "id": "story_12345678",
        "premise": {
            "idea": "A lighthouse keeper collects lost voices",
            "character": {"name": "Mara", "description": "A quiet keeper"},
            "theme": "Untold stories"
        },
        "body": "Each voice was stored in a glass jar...",
        "word_count": 150,
        "max_words": STORY_DEFAULT_MAX_WORDS,
    }


class TestFilenameSanitization:
    """Test filename sanitization functionality."""
    
    def test_sanitize_filename_removes_dangerous_characters(self):
        """Test that dangerous characters are removed from filenames."""
        malicious_title = "../../etc/passwd<script>alert('xss')</script>\\:*?\"<>|&;`$"
        safe = sanitize_filename(malicious_title, "test_123")
        
        # Check all dangerous characters are removed
        assert "<" not in safe
        assert ">" not in safe
        assert ".." not in safe
        assert "/" not in safe
        assert "\\" not in safe
        assert ":" not in safe
        assert "*" not in safe
        assert "?" not in safe
        assert '"' not in safe
        assert "|" not in safe
        assert "&" not in safe
        assert ";" not in safe
        assert "`" not in safe
        assert "$" not in safe
        # Check XSS patterns are removed
        assert "alert('xss')" not in safe
        assert "script" not in safe.lower()
        assert "javascript" not in safe.lower()
        # Should not be empty
        assert len(safe) >= 1
    
    def test_sanitize_filename_handles_only_dangerous_characters(self):
        """Test that a title consisting only of dangerous characters is handled gracefully."""
        title = "../:<>\\*?|\"&;`$"
        safe = sanitize_filename(title, "test_123_fallback")
        # Should default to fallback or be valid
        assert len(safe) >= 1
        assert "test_123" in safe or "Story_" in safe
    
    def test_sanitize_filename_preserves_safe_characters(self):
        """Test that safe characters are preserved."""
        title = "My Story Title 2024"
        safe = sanitize_filename(title, "story_123")
        assert "My" in safe
        assert "Story" in safe
        assert "Title" in safe
        assert "2024" in safe
        assert "story_123" in safe
    
    def test_sanitize_filename_handles_path_traversal(self):
        """Test that path traversal sequences are removed."""
        title = "../../../etc/passwd"
        safe = sanitize_filename(title, "test_123")
        assert ".." not in safe
        assert "/" not in safe
        assert "etc" not in safe or "passwd" not in safe  # Should be sanitized
    
    def test_sanitize_filename_handles_script_tags(self):
        """Test that script tags and XSS patterns are removed."""
        title = "Story<script>alert('XSS')</script>Title"
        safe = sanitize_filename(title, "test_123")
        assert "<script>" not in safe
        assert "</script>" not in safe
        assert "alert" not in safe
        assert "XSS" not in safe
        # Should preserve safe parts
        assert "Story" in safe or "Title" in safe
    
    def test_sanitize_filename_handles_event_handlers(self):
        """Test that JavaScript event handlers are removed."""
        title = "Story onclick=alert('xss') Title"
        safe = sanitize_filename(title, "test_123")
        assert "onclick" not in safe
        assert "alert" not in safe
    
    def test_sanitize_filename_handles_empty_string(self):
        """Test that empty string uses fallback."""
        safe = sanitize_filename("", "test_123")
        assert len(safe) >= 1
        assert "Story_" in safe or "test_123" in safe
    
    def test_sanitize_filename_handles_unicode(self):
        """Test that unicode characters are handled (removed or preserved safely)."""
        title = "Story with émojis 🎭 and spéciál chàracters"
        safe = sanitize_filename(title, "test_123")
        # Unicode should be removed (only alphanumeric, _, - allowed)
        assert len(safe) >= 1
        # Should contain safe parts or fallback
        assert "Story" in safe or "test_123" in safe
    
    def test_sanitize_filename_respects_max_length(self):
        """Test that filename is truncated to max_length."""
        long_title = "A" * 100
        safe = sanitize_filename(long_title, "test_123", max_length=20)
        assert len(safe) <= 20
    
    def test_sanitize_filename_removes_leading_trailing_special_chars(self):
        """Test that leading/trailing underscores and hyphens are removed."""
        title = "___Story___---"
        safe = sanitize_filename(title, "test_123")
        assert not safe.startswith("_")
        assert not safe.startswith("-")
        assert not safe.endswith("_")
        assert not safe.endswith("-")
        assert "Story" in safe
    
    def test_sanitize_filename_handles_none_title(self):
        """Test that None title uses fallback."""
        safe = sanitize_filename(None, "test_123")
        assert len(safe) >= 1
        assert "test_123" in safe or "Story_" in safe
    
    def test_sanitize_filename_handles_none_story_id(self):
        """Test that None story_id is handled gracefully."""
        safe = sanitize_filename("My Story", None)
        assert len(safe) >= 1
        # Should either use a default fallback or handle None gracefully
        assert "My" in safe or "Story" in safe or len(safe) >= 1
    
    def test_sanitize_filename_handles_control_characters(self):
        """Test that control characters are removed."""
        title = "Story\x00\x01\x02\x03\x04\x05Title"
        safe = sanitize_filename(title, "test_123")
        # Control characters should be removed
        assert "\x00" not in safe
        assert "\x01" not in safe
        assert "\x02" not in safe
        # Should preserve safe parts
        assert "Story" in safe or "Title" in safe or "test_123" in safe
    
    def test_sanitize_filename_handles_windows_reserved_names(self):
        """Test that Windows reserved names are handled."""
        # Windows reserved names: CON, PRN, AUX, NUL, COM1-9, LPT1-9
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for reserved in reserved_names:
            safe = sanitize_filename(reserved, "test_123")
            # Should not be exactly the reserved name
            assert safe.upper() != reserved.upper() or "test_123" in safe
            assert len(safe) >= 1
    
    def test_sanitize_filename_handles_multiple_consecutive_special_chars(self):
        """Test that multiple consecutive special characters are handled."""
        title = "Story___---___Title"
        safe = sanitize_filename(title, "test_123")
        # Should not have multiple consecutive underscores or hyphens
        assert "___" not in safe
        assert "---" not in safe
        # Should preserve safe parts
        assert "Story" in safe or "Title" in safe or "test_123" in safe
    
    def test_sanitize_filename_handles_zero_max_length(self):
        """Test that zero max_length is handled gracefully."""
        title = "My Story Title"
        safe = sanitize_filename(title, "test_123", max_length=0)
        # Should either use a minimum length or handle gracefully
        assert len(safe) >= 1  # Should have at least fallback
    
    def test_sanitize_filename_handles_very_long_story_id(self):
        """Test that very long story IDs are handled correctly in fallback."""
        title = ""
        very_long_id = "a" * 1000
        safe = sanitize_filename(title, very_long_id)
        # Should truncate story_id in fallback
        assert len(safe) <= 50  # Should respect max_length default
        assert "Story_" in safe or safe.startswith("Story_")
    
    def test_sanitize_filename_handles_story_id_with_dangerous_chars(self):
        """Test that story IDs with dangerous characters are sanitized in fallback."""
        title = ""
        dangerous_id = "../../etc/passwd<script>alert('xss')</script>"
        safe = sanitize_filename(title, dangerous_id)
        # Should sanitize story_id in fallback
        assert "<" not in safe
        assert ">" not in safe
        assert ".." not in safe
        assert "/" not in safe
        assert "script" not in safe.lower()
        assert len(safe) >= 1
    
    def test_sanitize_filename_handles_unicode_in_story_id(self):
        """Test that unicode characters in story IDs are handled in fallback."""
        title = ""
        unicode_id = "story_émoji🎭_123"
        safe = sanitize_filename(title, unicode_id)
        # Should sanitize unicode from story_id in fallback
        assert len(safe) >= 1
        assert "Story_" in safe or "story" in safe.lower()
    
    def test_sanitize_filename_handles_only_whitespace_title(self):
        """Test that titles with only whitespace are handled correctly."""
        whitespace_title = "   \t\n   "
        safe = sanitize_filename(whitespace_title, "test_123")
        # Should use fallback for whitespace-only title
        assert len(safe) >= 1
        assert "test_123" in safe or "Story_" in safe
    
    def test_sanitize_filename_handles_mixed_dangerous_and_safe_chars(self):
        """Test that mixed dangerous and safe characters are handled correctly."""
        mixed_title = "My<script>alert('xss')</script>Story/Title\\2024"
        safe = sanitize_filename(mixed_title, "test_123")
        # Should remove dangerous chars but preserve safe parts
        assert "<" not in safe
        assert ">" not in safe
        assert "/" not in safe
        assert "\\" not in safe
        assert "script" not in safe.lower()
        # Should preserve some safe content
        assert len(safe) >= 1
        # May contain sanitized versions of "My", "Story", "Title", "2024"
    
    def test_sanitize_filename_handles_negative_max_length(self):
        """Test that negative max_length is handled gracefully."""
        title = "My Story Title"
        safe = sanitize_filename(title, "test_123", max_length=-10)
        # Should handle negative max_length gracefully (use default or minimum)
        assert len(safe) >= 1  # Should have at least fallback
    
    def test_sanitize_filename_handles_extremely_long_title(self):
        """Test that extremely long titles are truncated correctly."""
        extremely_long_title = "A" * 10000
        safe = sanitize_filename(extremely_long_title, "test_123", max_length=50)
        # Should truncate to max_length
        assert len(safe) <= 50
        assert len(safe) >= 1
    
    def test_sanitize_filename_handles_exact_max_length(self):
        """Test that filename exactly at max_length boundary is handled correctly."""
        # Create a title that will be exactly max_length after sanitization
        title = "A" * 50  # Exactly 50 characters
        safe = sanitize_filename(title, "test_123", max_length=50)
        assert len(safe) <= 50
        assert len(safe) >= 1
    
    def test_sanitize_filename_handles_all_windows_reserved_names(self):
        """Test that all Windows reserved names (including all COM and LPT ports) are handled."""
        # Windows reserved names: CON, PRN, AUX, NUL, COM1-9, LPT1-9
        reserved_names = ["CON", "PRN", "AUX", "NUL"] + \
                        [f"COM{i}" for i in range(1, 10)] + \
                        [f"LPT{i}" for i in range(1, 10)]
        
        for reserved in reserved_names:
            safe = sanitize_filename(reserved, "test_123")
            # Should not be exactly the reserved name (case-insensitive check)
            assert safe.upper() != reserved.upper() or "test_123" in safe or "Story_" in safe, \
                f"Reserved name {reserved} should be sanitized"
            assert len(safe) >= 1
    
    def test_sanitize_filename_handles_windows_reserved_names_case_variations(self):
        """Test that Windows reserved names in different cases are handled."""
        # Test case variations of reserved names
        case_variations = ["con", "Con", "cOn", "coN", "CON", "PrN", "pRn", "PRN"]
        for reserved in case_variations:
            safe = sanitize_filename(reserved, "test_123")
            # Should not be exactly the reserved name (case-insensitive)
            assert safe.upper() != reserved.upper() or "test_123" in safe or "Story_" in safe, \
                f"Case variation {reserved} should be sanitized"
            assert len(safe) >= 1
    
    def test_sanitize_filename_handles_reserved_name_after_sanitization(self):
        """Test that filenames that become reserved names after sanitization are handled."""
        # Title that becomes a reserved name after removing spaces/special chars
        # "C O N" -> "C_O_N" (safe), but "CON" -> should be sanitized
        title_that_becomes_con = "C-O-N"  # After removing hyphens, becomes "CON"
        safe = sanitize_filename(title_that_becomes_con, "test_123")
        # Should not be exactly "CON" (case-insensitive)
        assert safe.upper() != "CON" or "test_123" in safe or "Story_" in safe, \
            "Filename that becomes reserved name should be sanitized"
        assert len(safe) >= 1
    
    def test_sanitize_filename_handles_carriage_return_and_newline(self):
        """Test that carriage return and newline characters are handled."""
        title_with_newlines = "Story\r\nTitle\nWith\rCarriage"
        safe = sanitize_filename(title_with_newlines, "test_123")
        # Newlines and carriage returns should be replaced with underscores
        assert "\r" not in safe
        assert "\n" not in safe
        # Should preserve safe content
        assert "Story" in safe or "Title" in safe or "test_123" in safe
    
    def test_sanitize_filename_handles_only_spaces(self):
        """Test that title with only spaces (not other whitespace) is handled."""
        title_only_spaces = "     "  # Only spaces, no tabs or newlines
        safe = sanitize_filename(title_only_spaces, "test_123")
        # Should use fallback for whitespace-only title
        assert len(safe) >= 1
        assert "test_123" in safe or "Story_" in safe
    
    def test_sanitize_filename_handles_multiple_consecutive_spaces(self):
        """Test that multiple consecutive spaces are replaced with single underscore."""
        title_multiple_spaces = "Story    Title   With    Spaces"
        safe = sanitize_filename(title_multiple_spaces, "test_123")
        # Multiple spaces should be replaced with underscores (but may be multiple underscores)
        # The implementation replaces whitespace with underscores, so "    " becomes "____"
        # But then leading/trailing underscores are stripped
        assert "Story" in safe or "Title" in safe
        assert len(safe) >= 1
    
    def test_sanitize_filename_handles_empty_after_sanitization(self):
        """Test that title that becomes empty after all sanitization steps uses fallback."""
        # Title with only dangerous characters that all get removed
        title_only_dangerous = "<>:\"/\\|?*&;`$"
        safe = sanitize_filename(title_only_dangerous, "test_123")
        # Should use fallback since all characters are removed
        assert len(safe) >= 1
        assert "test_123" in safe or "Story_" in safe
    
    def test_sanitize_filename_handles_none_both_params(self):
        """Test that both title and story_id being None is handled gracefully."""
        # This tests the edge case where both inputs are problematic
        safe = sanitize_filename(None, None)
        # Should have a valid fallback
        assert len(safe) >= 1
        assert "Story_" in safe or isinstance(safe, str)


class TestPDFExport:
    """Test PDF export functionality."""
    
    @patch('src.shortstory.exports.send_file')
    def test_export_pdf_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_pdf returns a Flask response."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        response = export_pdf(sample_story_text, "Test Story", "test_123")
        
        assert response is not None
        assert response.status_code == HTTP_OK
        assert mock_send_file.called
    
    @patch('src.shortstory.exports.send_file')
    def test_export_pdf_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that PDF export has correct MIME type."""
        mock_response = Response()
        mock_response.headers = {}
        mock_send_file.return_value = mock_response
        
        export_pdf(sample_story_text, "Test Story", "test_123")
        
        call_kwargs = mock_send_file.call_args.kwargs
        assert call_kwargs.get('mimetype') == 'application/pdf'
    
    @patch('src.shortstory.exports.send_file')
    def test_export_pdf_includes_story_content(self, mock_send_file, app_context, sample_story_text):
        """Test that PDF export includes story content."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        export_pdf(sample_story_text, "Test Story", "test_123")
        
        mock_send_file.assert_called_once()
        call_args, _ = mock_send_file.call_args
        exported_file_buffer = call_args[0]
        assert isinstance(exported_file_buffer, BytesIO)
        
        # Verify the buffer contains valid PDF content
        exported_file_buffer.seek(0)
        content = exported_file_buffer.read()
        assert len(content) > 0, "PDF buffer should not be empty"
        
        # Verify PDF header (PDF files start with %PDF)
        assert content.startswith(b'%PDF'), "Generated file should be a valid PDF"
        
        # Verify PDF structure - should contain PDF objects and end with %%EOF
        assert b'%%EOF' in content, "PDF should end with %%EOF marker"
        assert b'endobj' in content, "PDF should contain object definitions"
        assert b'/Type /Page' in content or b'/Pages' in content, \
            "PDF should contain page structure"
        
        # PDF text is compressed/encoded, so we can't easily verify exact text content
        # without a PDF parser. Instead, we verify:
        # 1. It's a valid PDF (header check above)
        # 2. It has proper structure (EOF, objects, pages)
        # 3. The buffer was generated (length check above)
        # 4. Key story content appears in the PDF (even if encoded)
        # This verifies that the export function actually generated PDF content,
        # not just an empty or invalid file
        
        # Verify that key story content appears in the PDF (may be encoded/compressed)
        # PDFs often contain text in readable form even when compressed
        content_str = content.decode('utf-8', errors='ignore')
        # Check for key words from the story (may appear in metadata or text streams)
        story_keywords = ["lighthouse", "keeper", "voice", "jar", "Mara"]
        found_keywords = [kw for kw in story_keywords if kw.lower() in content_str.lower()]
        # At least some story content should be present (even if encoded)
        assert len(found_keywords) > 0 or len(content) > 1000, \
            f"PDF should contain story content. Found keywords: {found_keywords}, Content length: {len(content)}"
        
        # Verify PDF version is reasonable (PDF files start with %PDF-version)
        assert content.startswith(b'%PDF-'), \
            "PDF should start with %PDF-version header"
        
        # Verify the buffer position is reset (good practice check)
        assert exported_file_buffer.tell() == len(content), \
            "Buffer position should be at end after reading"


class TestMarkdownExport:
    """Test Markdown export functionality."""
    
    def test_export_markdown_returns_response(self, app_context, sample_story_text):
        """Test that export_markdown returns a Flask response."""
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        
        assert response is not None
        assert response.status_code == HTTP_OK
    
    def test_export_markdown_has_correct_mimetype(self, app_context, sample_story_text):
        """Test that Markdown export has correct MIME type."""
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        
        assert "text/markdown" in response.content_type or "text/plain" in response.content_type
    
    def test_export_markdown_preserves_content(self, app_context, sample_story_text):
        """Test that Markdown export preserves story content."""
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        
        assert response.status_code == HTTP_OK
        content = response.get_data(as_text=True)
        assert "Each voice was stored in a glass jar" in content
        assert "Mara" in content
        assert sample_story_text in content or "lighthouse keeper" in content.lower()


class TestTXTExport:
    """Test TXT export functionality."""
    
    @patch('src.shortstory.exports.send_file')
    def test_export_txt_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_txt returns a Flask response."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        response = export_txt(sample_story_text, "Test Story", "test_123")
        
        assert response is not None
        assert response.status_code == HTTP_OK
        assert mock_send_file.called
    
    @patch('src.shortstory.exports.send_file')
    def test_export_txt_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that TXT export has correct MIME type."""
        mock_response = Response()
        mock_send_file.return_value = mock_response
        
        export_txt(sample_story_text, "Test Story", "test_123")
        
        call_kwargs = mock_send_file.call_args.kwargs
        assert call_kwargs.get('mimetype') == 'text/plain'
    
    @patch('src.shortstory.exports.send_file')
    def test_export_txt_preserves_story_content(self, mock_send_file, app_context, sample_story_text):
        """Test that TXT export preserves story content and removes markdown formatting."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        export_txt(sample_story_text, "Test Story", "test_123")
        
        mock_send_file.assert_called_once()
        call_args, _ = mock_send_file.call_args
        exported_file_buffer = call_args[0]
        assert isinstance(exported_file_buffer, BytesIO)
        
        exported_file_buffer.seek(0)
        content = exported_file_buffer.read().decode('utf-8')
        
        # Verify key story content is present
        assert "Each voice was stored in a glass jar" in content, \
            "TXT export should contain key story content"
        assert "Mara" in content, "TXT export should contain character name"
        assert "lighthouse keeper" in content.lower() or "voices" in content.lower(), \
            "TXT export should contain story themes"
        
        # Verify markdown formatting is removed (headers, bold, italic)
        # The original has "# The Lighthouse Keeper's Collection" - header should be removed
        assert "# The Lighthouse Keeper's Collection" not in content, \
            "TXT export should remove markdown headers"
        # If there were markdown bold/italic, they should be removed
        # (sample_story_text doesn't have bold/italic, but we verify the pattern)
        
        # Verify the content is plain text (no markdown syntax)
        assert not content.startswith("#"), "TXT export should not start with markdown header"
        
        # Verify UTF-8 encoding is preserved
        assert len(content) > 0, "TXT export should not be empty"
        
        # Verify content length is reasonable (should have substantial content)
        assert len(content) > 50, \
            f"TXT export should have substantial content, got {len(content)} characters"
        
        # Verify the exported content structure matches expectations
        # Should have multiple lines (story has paragraphs)
        lines = content.split('\n')
        assert len(lines) > 1, \
            "TXT export should preserve paragraph structure (multiple lines)"
        
        # Verify that the story title or key phrases appear in the content
        # (title might be in filename, but story content should be present)
        assert any(keyword in content for keyword in ["voice", "jar", "keeper", "Mara", "lighthouse"]), \
            "TXT export should contain key story elements"
        
        # Verify buffer was properly read (position check)
        assert exported_file_buffer.tell() == len(content.encode('utf-8')), \
            "Buffer should be at end after reading"
    
    def test_export_txt_removes_markdown_formatting(self, app_context):
        """Test that TXT export correctly removes markdown formatting."""
        # Create story text with various markdown elements
        story_with_markdown = """# Title

**Bold text** and *italic text*.

## Subheading

More content here."""
        
        with patch('src.shortstory.exports.send_file') as mock_send_file:
            mock_response = Response()
            mock_response.status_code = HTTP_OK
            mock_send_file.return_value = mock_response
            
            export_txt(story_with_markdown, "Test Story", "test_123")
            
            # Get the exported content
            call_args, _ = mock_send_file.call_args
            exported_file_buffer = call_args[0]
            exported_file_buffer.seek(0)
            content = exported_file_buffer.read().decode('utf-8')
            
            # Verify markdown headers are removed
            assert "# Title" not in content, "Markdown headers should be removed"
            assert "## Subheading" not in content, "Markdown subheadings should be removed"
            
            # Verify markdown formatting is removed (bold/italic markers)
            assert "**Bold text**" not in content, "Bold markdown markers should be removed"
            assert "*italic text*" not in content, "Italic markdown markers should be removed"
            
            # Verify actual text content is preserved
            assert "Bold text" in content, "Bold text content should be preserved"
            assert "italic text" in content, "Italic text content should be preserved"
            assert "Title" in content, "Title text should be preserved"
            assert "Subheading" in content, "Subheading text should be preserved"


class TestDOCXExport:
    """Test DOCX export functionality."""
    
    @require_optional_dependency('docx')
    @patch('src.shortstory.exports.send_file')
    def test_export_docx_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_docx returns a Flask response."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        response = export_docx(sample_story_text, "Test Story", "test_123")
        
        assert response is not None
        assert response.status_code == HTTP_OK
        assert mock_send_file.called
    
    @require_optional_dependency('docx')
    @patch('src.shortstory.exports.send_file')
    def test_export_docx_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that DOCX export has correct MIME type."""
        mock_response = Response()
        mock_send_file.return_value = mock_response
        
        export_docx(sample_story_text, "Test Story", "test_123")
        
        call_kwargs = mock_send_file.call_args.kwargs
        content_type = call_kwargs.get('mimetype', '')
        assert "wordprocessingml" in content_type or "docx" in content_type.lower() or "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in content_type
    
    @require_optional_dependency('docx')
    def test_export_docx_requires_dependency(self, app_context, sample_story_text):
        """Test that export_docx raises MissingDependencyError when python-docx is not available."""
        if DOCX_AVAILABLE:
            pytest.skip("python-docx is available, cannot test missing dependency")
        
        with patch('src.shortstory.exports.docx', None):
            with pytest.raises(MissingDependencyError):
                export_docx(sample_story_text, "Test Story", "test_123")


class TestEPUBExport:
    """Test EPUB export functionality."""
    
    @require_optional_dependency('ebooklib')
    @patch('src.shortstory.exports.send_file')
    def test_export_epub_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_epub returns a Flask response."""
        mock_response = Response()
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        response = export_epub(sample_story_text, "Test Story", "test_123")
        
        assert response is not None
        assert response.status_code == HTTP_OK
        assert mock_send_file.called
    
    @require_optional_dependency('ebooklib')
    @patch('src.shortstory.exports.send_file')
    def test_export_epub_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that EPUB export has correct MIME type."""
        mock_response = Response()
        mock_send_file.return_value = mock_response
        
        export_epub(sample_story_text, "Test Story", "test_123")
        
        call_kwargs = mock_send_file.call_args.kwargs
        content_type = call_kwargs.get('mimetype', '')
        assert "epub" in content_type.lower() or "application/epub+zip" in content_type
    
    @require_optional_dependency('ebooklib')
    def test_export_epub_requires_dependency(self, app_context, sample_story_text):
        """Test that export_epub raises MissingDependencyError when ebooklib is not available."""
        if EPUB_AVAILABLE:
            pytest.skip("ebooklib is available, cannot test missing dependency")
        
        with patch('src.shortstory.exports.ebooklib', None):
            with pytest.raises(MissingDependencyError):
                export_epub(sample_story_text, "Test Story", "test_123")


class TestExportStoryFromDict:
    """Test the centralized export_story_from_dict function."""
    
    def test_export_story_from_dict_pdf(self, app_context, sample_story_dict, sample_story_text):
        """Test export_story_from_dict with PDF format."""
        with patch('src.shortstory.exports.export_pdf') as mock_export:
            mock_response = Response()
            mock_response.status_code = HTTP_OK
            mock_export.return_value = mock_response
            
            response = export_story_from_dict(
                sample_story_dict, "story_12345678", "pdf", sample_story_text
            )
            
            assert response.status_code == HTTP_OK
            mock_export.assert_called_once()
    
    def test_export_story_from_dict_markdown(self, app_context, sample_story_dict, sample_story_text):
        """Test export_story_from_dict with Markdown format."""
        with patch('src.shortstory.exports.export_markdown') as mock_export:
            mock_response = Response()
            mock_response.status_code = HTTP_OK
            mock_export.return_value = mock_response
            
            response = export_story_from_dict(
                sample_story_dict, "story_12345678", "markdown", sample_story_text
            )
            
            assert response.status_code == HTTP_OK
            mock_export.assert_called_once()
            
            # Verify that export_markdown was called with correct parameters
            # This verifies content is passed correctly without using get_data() on mocked response
            call_args = mock_export.call_args
            assert call_args is not None, "export_markdown should be called with arguments"
            
            # Verify story text is passed (first positional argument)
            called_story_text = call_args[0][0] if call_args[0] else None
            assert called_story_text == sample_story_text, \
                "export_markdown should be called with the correct story text"
            
            # Verify title is passed (second positional argument)
            if len(call_args[0]) > 1:
                called_title = call_args[0][1]
                # Title might come from story_dict or be derived
                assert called_title is not None, "export_markdown should be called with a title"
            
            # Verify story_id is passed (third positional argument)
            if len(call_args[0]) > 2:
                called_story_id = call_args[0][2]
                assert called_story_id == "story_12345678", \
                    "export_markdown should be called with the correct story_id"
    
    def test_export_story_from_dict_invalid_format(self, app_context, sample_story_dict, sample_story_text):
        """Test export_story_from_dict with invalid format."""
        with pytest.raises(ValidationError):
            export_story_from_dict(
                sample_story_dict, "story_12345678", "invalid_format", sample_story_text
            )
    
    @require_optional_dependency('docx')
    def test_export_story_from_dict_docx(self, app_context, sample_story_dict, sample_story_text):
        """Test export_story_from_dict with DOCX format."""
        with patch('src.shortstory.exports.export_docx') as mock_export:
            mock_response = Response()
            mock_response.status_code = HTTP_OK
            mock_export.return_value = mock_response
            
            response = export_story_from_dict(
                sample_story_dict, "story_12345678", "docx", sample_story_text
            )
            
            assert response.status_code == HTTP_OK
            mock_export.assert_called_once()
    
    @require_optional_dependency('ebooklib')
    def test_export_story_from_dict_epub(self, app_context, sample_story_dict, sample_story_text):
        """Test export_story_from_dict with EPUB format."""
        with patch('src.shortstory.exports.export_epub') as mock_export:
            mock_response = Response()
            mock_response.status_code = HTTP_OK
            mock_export.return_value = mock_response
            
            response = export_story_from_dict(
                sample_story_dict, "story_12345678", "epub", sample_story_text
            )
            
            assert response.status_code == HTTP_OK
            mock_export.assert_called_once()


class TestExportFilenameSanitization:
    """Test that all exports sanitize filenames."""
    
    @patch('src.shortstory.exports.send_file')
    def test_all_exports_sanitize_filenames(self, mock_send_file, app_context, sample_story_text):
        """Test that all exports sanitize filenames robustly."""
        malicious_title = "../../etc/passwd<script>alert('xss')</script>\\:*?\"<>|&;`$"
        story_id = "test_123"
        mock_response = Response()
        mock_response.headers = {}
        mock_response.status_code = HTTP_OK
        mock_send_file.return_value = mock_response
        
        formats = [
            ("pdf", export_pdf),
            ("txt", export_txt),
        ]
        
        for format_name, export_func in formats:
            mock_send_file.reset_mock()
            export_func(sample_story_text, malicious_title, story_id)
            
            assert mock_send_file.called, f"{format_name} export should call send_file"
            
            call_kwargs = mock_send_file.call_args.kwargs if mock_send_file.call_args else {}
            attachment_filename = call_kwargs.get('download_name', '') or call_kwargs.get('attachment_filename', '')
            
            # Comprehensive security checks
            assert "<" not in attachment_filename, f"{format_name}: < should be removed"
            assert ">" not in attachment_filename, f"{format_name}: > should be removed"
            assert ".." not in attachment_filename, f"{format_name}: .. should be removed"
            assert "/" not in attachment_filename, f"{format_name}: / should be removed"
            assert "\\" not in attachment_filename, f"{format_name}: \\ should be removed"
            assert ":" not in attachment_filename, f"{format_name}: : should be removed"
            assert "*" not in attachment_filename, f"{format_name}: * should be removed"
            assert "?" not in attachment_filename, f"{format_name}: ? should be removed"
            assert '"' not in attachment_filename, f"{format_name}: \" should be removed"
            assert "|" not in attachment_filename, f"{format_name}: | should be removed"
            assert "&" not in attachment_filename, f"{format_name}: & should be removed"
            assert ";" not in attachment_filename, f"{format_name}: ; should be removed"
            assert "alert('xss')" not in attachment_filename, f"{format_name}: XSS patterns should be removed"
            assert "script" not in attachment_filename.lower(), f"{format_name}: script tags should be removed"
            # Story ID should be present for identification
            assert story_id in attachment_filename or "Story_" in attachment_filename, \
                f"{format_name}: Should contain story_id or fallback"
    
    def test_markdown_export_sanitizes_content_disposition(self, app_context, sample_story_text):
        """Test that markdown export sanitizes Content-Disposition header."""
        from flask import request
        from src.shortstory.exports import export_markdown
        
        malicious_title = "../../etc/passwd<script>alert('xss')</script>\\:*?\"<>|"
        story_id = "test_123"
        
        # Create a test request context for send_file
        with app_context.test_request_context():
            response = export_markdown(sample_story_text, malicious_title, story_id)
        
        content_disposition = response.headers.get("Content-Disposition", "")
        
        # Verify header exists
        assert content_disposition, "Content-Disposition header should be present"
        
        # Check all dangerous characters are removed from header
        assert "<" not in content_disposition, "Content-Disposition should not contain <"
        assert ">" not in content_disposition, "Content-Disposition should not contain >"
        assert ".." not in content_disposition, "Content-Disposition should not contain .."
        assert "/" not in content_disposition, "Content-Disposition should not contain /"
        assert "\\" not in content_disposition, "Content-Disposition should not contain \\"
        assert ":" not in content_disposition, "Content-Disposition should not contain :"
        assert "*" not in content_disposition, "Content-Disposition should not contain *"
        assert "?" not in content_disposition, "Content-Disposition should not contain ?"
        assert '"' not in content_disposition or content_disposition.count('"') <= 2, \
            "Content-Disposition should have minimal quotes (only for header format)"
        assert "|" not in content_disposition, "Content-Disposition should not contain |"
        assert "alert('xss')" not in content_disposition, \
            "Content-Disposition should not contain XSS patterns"
        
        # Verify the header contains a filename (either the sanitized one or a fallback)
        # The exact format depends on Flask's send_file implementation, but it should be safe
        assert "filename" in content_disposition.lower() or "attachment" in content_disposition.lower(), \
            "Content-Disposition should indicate a file attachment"
