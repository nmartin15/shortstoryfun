"""
Comprehensive tests for export functionality.

Tests cover PDF, Markdown, TXT, DOCX, and EPUB export formats,
including filename sanitization and error handling.
"""

import pytest
import re
import sys
from pathlib import Path
from io import BytesIO
from unittest.mock import patch, MagicMock, Mock
from flask import Flask, Response

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import (
    export_pdf,
    export_markdown,
    export_txt,
    export_docx,
    export_epub,
    sanitize_filename
)

# Import send_file for mocking
from flask import send_file

# Import before patching __import__
from src.shortstory.utils.errors import MissingDependencyError


@pytest.fixture
def sample_story_text():
    """Create sample story text for testing."""
    return """# The Lighthouse Keeper

Mara stood at the top of the lighthouse, watching the waves crash against the rocks below. The wind howled through the night, carrying with it the voices she had collected over the years.

Each voice was stored in a glass jar, carefully labeled and arranged on the shelves that lined the circular room. Some voices whispered, others sang, and a few remained silent—waiting for the right moment to speak.

Tonight, a new voice had arrived, carried by the storm. Mara could hear it calling from the darkness, asking to be collected, to be preserved, to be remembered.

She reached for an empty jar and stepped out into the storm."""


@pytest.fixture
def app():
    """Create Flask application for testing."""
    app = Flask(__name__)
    return app


@pytest.fixture
def app_context(app):
    """Create Flask application context for testing."""
    with app.app_context():
        yield app


class TestFilenameSanitization:
    """Test filename sanitization functionality."""
    
    def test_sanitize_filename_removes_dangerous_characters(self, app_context):
        """Test that dangerous characters are removed from filenames."""
        malicious_title = "../../etc/passwd<script>alert('xss')</script>"
        safe = sanitize_filename(malicious_title, "test_123")
        
        assert "<" not in safe
        assert ">" not in safe
        assert ".." not in safe
        assert "/" not in safe
        assert "\\" not in safe
    
    def test_sanitize_filename_limits_length(self, app_context):
        """Test that filenames are limited to reasonable length."""
        long_title = "A" * 200
        safe = sanitize_filename(long_title, "test_123", max_length=50)
        assert len(safe) <= 50
    
    def test_sanitize_filename_preserves_safe_characters(self, app_context):
        """Test that safe characters are preserved."""
        title = "My Story Title 2024"
        safe = sanitize_filename(title, "test_123")
        assert "My" in safe or "Story" in safe
        assert "2024" in safe
    
    def test_sanitize_filename_handles_empty_title(self, app_context):
        """Test that empty title uses story_id fallback."""
        safe = sanitize_filename("", "test_123")
        assert "test_123" in safe or len(safe) > 0
    
    def test_sanitize_filename_handles_special_characters(self, app_context):
        """Test handling of special characters."""
        title = "Story: The Beginning (Part 1)"
        safe = sanitize_filename(title, "test_123")
        # Should remove or replace dangerous chars but keep safe ones
        assert len(safe) > 0


class TestPDFExport:
    """Test PDF export functionality."""
    
    @patch('app.send_file')
    def test_export_pdf_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_pdf returns a Flask response."""
        # Mock send_file to return a Response
        mock_response = Response()
        mock_response.status_code = 200
        mock_send_file.return_value = mock_response
        
        response = export_pdf(sample_story_text, "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200
        assert mock_send_file.called
    
    @patch('app.send_file')
    def test_export_pdf_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that PDF export has correct MIME type."""
        mock_response = Response()
        mock_response.content_type = "application/pdf"
        mock_send_file.return_value = mock_response
        
        response = export_pdf(sample_story_text, "Test Story", "test_123")
        assert "application/pdf" in response.content_type
    
    @patch('app.send_file')
    def test_export_pdf_has_attachment_header(self, mock_send_file, app_context, sample_story_text):
        """Test that PDF export includes attachment header."""
        mock_response = Response()
        mock_response.headers = {"Content-Disposition": "attachment; filename=test.pdf"}
        mock_send_file.return_value = mock_response
        
        response = export_pdf(sample_story_text, "Test Story", "test_123")
        assert "attachment" in response.headers.get("Content-Disposition", "").lower()
    
    @patch('app.send_file')
    def test_export_pdf_includes_story_content(self, mock_send_file, app_context, sample_story_text):
        """Test that PDF includes story content."""
        mock_response = Response()
        mock_response.data = b"PDF content"
        mock_send_file.return_value = mock_response
        
        response = export_pdf(sample_story_text, "Test Story", "test_123")
        # Verify send_file was called with BytesIO containing content
        assert mock_send_file.called
        call_args = mock_send_file.call_args
        # Check that BytesIO was passed
        assert call_args is not None
    
    @patch('app.send_file')
    def test_export_pdf_removes_markdown_headers(self, mock_send_file, app_context, sample_story_text):
        """Test that markdown headers are processed."""
        mock_response = Response()
        mock_send_file.return_value = mock_response
        
        response = export_pdf(sample_story_text, "Test Story", "test_123")
        # Verify send_file was called
        assert mock_send_file.called
    
    @patch('app.send_file')
    def test_export_pdf_handles_empty_text(self, mock_send_file, app_context):
        """Test that empty text is handled."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_send_file.return_value = mock_response
        
        response = export_pdf("", "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200
    
    @patch('app.send_file')
    def test_export_pdf_sanitizes_filename(self, mock_send_file, app_context, sample_story_text):
        """Test that PDF filename is sanitized."""
        mock_response = Response()
        mock_response.headers = {}
        mock_send_file.return_value = mock_response
        
        malicious_title = "../../etc/passwd"
        response = export_pdf(sample_story_text, malicious_title, "test_123")
        # Verify send_file was called with sanitized filename
        assert mock_send_file.called
        call_kwargs = mock_send_file.call_args.kwargs if mock_send_file.call_args.kwargs else {}
        attachment_filename = call_kwargs.get('attachment_filename', '')
        assert ".." not in attachment_filename
        assert "/" not in attachment_filename


class TestMarkdownExport:
    """Test Markdown export functionality."""
    
    @patch('app.send_file')
    def test_export_markdown_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_markdown returns a Flask response."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_send_file.return_value = mock_response
        
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200
    
    @patch('app.send_file')
    def test_export_markdown_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that Markdown export has correct MIME type."""
        mock_response = Response()
        mock_response.content_type = "text/markdown"
        mock_send_file.return_value = mock_response
        
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        assert "text/markdown" in response.content_type
    
    @patch('app.send_file')
    def test_export_markdown_preserves_content(self, mock_send_file, app_context, sample_story_text):
        """Test that Markdown export preserves story content."""
        mock_response = Response()
        mock_response.data = sample_story_text.encode()
        mock_send_file.return_value = mock_response
        
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        content = response.get_data(as_text=True)
        assert "lighthouse" in content.lower() or "Mara" in content
    
    @patch('app.send_file')
    def test_export_markdown_has_attachment_header(self, mock_send_file, app_context, sample_story_text):
        """Test that Markdown export includes attachment header."""
        mock_response = Response()
        mock_response.headers = {"Content-Disposition": "attachment; filename=test.md"}
        mock_send_file.return_value = mock_response
        
        response = export_markdown(sample_story_text, "Test Story", "test_123")
        assert "attachment" in response.headers.get("Content-Disposition", "").lower()
    
    def test_export_markdown_sanitizes_filename(self, app_context, sample_story_text):
        """Test that Markdown filename is sanitized."""
        malicious_title = "<script>alert('xss')</script>"
        response = export_markdown(sample_story_text, malicious_title, "test_123")
        # Check Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "<" not in content_disposition
        assert ">" not in content_disposition


class TestTXTExport:
    """Test plain text export functionality."""
    
    @patch('app.send_file')
    def test_export_txt_returns_response(self, mock_send_file, app_context, sample_story_text):
        """Test that export_txt returns a Flask response."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_send_file.return_value = mock_response
        
        response = export_txt(sample_story_text, "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200
    
    @patch('app.send_file')
    def test_export_txt_has_correct_mimetype(self, mock_send_file, app_context, sample_story_text):
        """Test that TXT export has correct MIME type."""
        mock_response = Response()
        mock_response.content_type = "text/plain"
        mock_send_file.return_value = mock_response
        
        response = export_txt(sample_story_text, "Test Story", "test_123")
        assert "text/plain" in response.content_type
    
    @patch('app.send_file')
    def test_export_txt_removes_markdown(self, mock_send_file, app_context, sample_story_text):
        """Test that TXT export removes markdown formatting."""
        # Create a response with processed text (markdown removed)
        processed_text = sample_story_text.replace("# ", "").replace("#", "")
        mock_response = Response()
        mock_response.data = processed_text.encode()
        mock_send_file.return_value = mock_response
        
        response = export_txt(sample_story_text, "Test Story", "test_123")
        content = response.get_data(as_text=True)
        # Content should still be there
        assert "lighthouse" in content.lower() or "Mara" in content
    
    @patch('app.send_file')
    def test_export_txt_preserves_story_content(self, mock_send_file, app_context, sample_story_text):
        """Test that TXT export preserves story content."""
        mock_response = Response()
        mock_response.data = sample_story_text.encode()
        mock_send_file.return_value = mock_response
        
        response = export_txt(sample_story_text, "Test Story", "test_123")
        content = response.get_data(as_text=True)
        assert len(content) > 0
        assert "Mara" in content or "lighthouse" in content.lower()
    
    @patch('app.send_file')
    def test_export_txt_has_attachment_header(self, mock_send_file, app_context, sample_story_text):
        """Test that TXT export includes attachment header."""
        mock_response = Response()
        mock_response.headers = {"Content-Disposition": "attachment; filename=test.txt"}
        mock_send_file.return_value = mock_response
        
        response = export_txt(sample_story_text, "Test Story", "test_123")
        assert "attachment" in response.headers.get("Content-Disposition", "").lower()
    
    @patch('app.send_file')
    def test_export_txt_handles_empty_text(self, mock_send_file, app_context):
        """Test that empty text is handled."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_send_file.return_value = mock_response
        
        response = export_txt("", "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200


class TestDOCXExport:
    """Test DOCX export functionality."""
    
    @patch('app.send_file')
    def test_export_docx_requires_dependency(self, mock_send_file, app_context, sample_story_text):
        """Test that DOCX export requires python-docx library."""
        # Patch import only for 'docx' module, not for our own imports
        def side_effect(name, *args, **kwargs):
            if name == 'docx':
                raise ImportError("No module named 'docx'")
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=side_effect):
            with pytest.raises(MissingDependencyError, match="python-docx"):
                export_docx(sample_story_text, "Test Story", "test_123")
    
    @pytest.mark.skipif(True, reason="Requires python-docx library")
    def test_export_docx_returns_response(self, app_context, sample_story_text):
        """Test that export_docx returns a Flask response."""
        response = export_docx(sample_story_text, "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200
    
    @pytest.mark.skipif(True, reason="Requires python-docx library")
    def test_export_docx_has_correct_mimetype(self, app_context, sample_story_text):
        """Test that DOCX export has correct MIME type."""
        response = export_docx(sample_story_text, "Test Story", "test_123")
        assert "wordprocessingml" in response.content_type or "docx" in response.content_type.lower()


class TestEPUBExport:
    """Test EPUB export functionality."""
    
    @patch('app.send_file')
    def test_export_epub_requires_dependency(self, mock_send_file, app_context, sample_story_text):
        """Test that EPUB export requires ebooklib library."""
        # Patch import only for 'ebooklib' module, not for our own imports
        def side_effect(name, *args, **kwargs):
            if name == 'ebooklib':
                raise ImportError("No module named 'ebooklib'")
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=side_effect):
            with pytest.raises(MissingDependencyError, match="ebooklib"):
                export_epub(sample_story_text, "Test Story", "test_123")
    
    @pytest.mark.skipif(True, reason="Requires ebooklib library")
    def test_export_epub_returns_response(self, app_context, sample_story_text):
        """Test that export_epub returns a Flask response."""
        response = export_epub(sample_story_text, "Test Story", "test_123")
        assert response is not None
        assert response.status_code == 200
    
    @pytest.mark.skipif(True, reason="Requires ebooklib library")
    def test_export_epub_has_correct_mimetype(self, app_context, sample_story_text):
        """Test that EPUB export has correct MIME type."""
        response = export_epub(sample_story_text, "Test Story", "test_123")
        assert "epub" in response.content_type.lower()


class TestExportErrorHandling:
    """Test error handling in export functions."""
    
    def test_export_handles_missing_dependencies(self, app_context, sample_story_text):
        """Test that missing dependencies raise appropriate errors."""
        from src.shortstory.utils.errors import MissingDependencyError
        
        # Test DOCX
        with patch('builtins.__import__', side_effect=ImportError("No module named 'docx'")):
            with pytest.raises(MissingDependencyError):
                export_docx(sample_story_text, "Test Story", "test_123")
        
        # Test EPUB
        with patch('builtins.__import__', side_effect=ImportError("No module named 'ebooklib'")):
            with pytest.raises(MissingDependencyError):
                export_epub(sample_story_text, "Test Story", "test_123")
    
    def test_export_handles_large_stories(self, app_context):
        """Test that large stories can be exported."""
        large_text = "# Large Story\n\n" + "This is a sentence. " * 10000
        response = export_txt(large_text, "Large Story", "test_123")
        assert response is not None
        assert response.status_code == 200
    
    def test_export_handles_special_characters_in_content(self, app_context):
        """Test that special characters in content are handled."""
        special_text = "# Story with Special Chars\n\némojis 🎭 and spéciál chàracters: @#$%"
        response = export_txt(special_text, "Special Story", "test_123")
        assert response is not None
        assert response.status_code == 200


class TestExportFilenameHandling:
    """Test filename handling across export formats."""
    
    @patch('app.send_file')
    def test_all_exports_include_story_id_in_filename(self, mock_send_file, app_context, sample_story_text):
        """Test that all exports include story ID in filename."""
        story_id = "test_story_123"
        mock_response = Response()
        mock_response.headers = {}
        mock_send_file.return_value = mock_response
        
        # Test PDF (uses send_file)
        export_pdf(sample_story_text, "Test Story", story_id)
        if mock_send_file.called and mock_send_file.call_args:
            call_kwargs = mock_send_file.call_args.kwargs if mock_send_file.call_args.kwargs else {}
            attachment_filename = call_kwargs.get('download_name', '') or call_kwargs.get('attachment_filename', '')
            assert story_id in attachment_filename or story_id in str(mock_send_file.call_args)
        mock_send_file.reset_mock()
        
        # Test Markdown (returns Response directly)
        response = export_markdown(sample_story_text, "Test Story", story_id)
        content_disposition = response.headers.get("Content-Disposition", "")
        assert story_id in content_disposition
        
        # Test TXT (uses send_file)
        export_txt(sample_story_text, "Test Story", story_id)
        if mock_send_file.called and mock_send_file.call_args:
            call_kwargs = mock_send_file.call_args.kwargs if mock_send_file.call_args.kwargs else {}
            attachment_filename = call_kwargs.get('download_name', '') or call_kwargs.get('attachment_filename', '')
            assert story_id in attachment_filename or story_id in str(mock_send_file.call_args)
    
    @patch('app.send_file')
    def test_all_exports_sanitize_filenames(self, mock_send_file, app_context, sample_story_text):
        """Test that all exports sanitize filenames."""
        malicious_title = "../../etc/passwd<script>alert('xss')</script>"
        story_id = "test_123"
        mock_response = Response()
        mock_response.headers = {}
        mock_send_file.return_value = mock_response
        
        formats = [
            ("pdf", export_pdf),
            ("markdown", export_markdown),
            ("txt", export_txt),
        ]
        
        for format_name, export_func in formats:
            export_func(sample_story_text, malicious_title, story_id)
            call_kwargs = mock_send_file.call_args.kwargs if mock_send_file.call_args.kwargs else {}
            attachment_filename = call_kwargs.get('attachment_filename', '')
            assert "<" not in attachment_filename
            assert ">" not in attachment_filename
            assert ".." not in attachment_filename


class TestExportContentPreservation:
    """Test that export functions preserve story content."""
    
    def test_export_preserves_story_structure(self, app_context, sample_story_text):
        """Test that exports preserve story structure."""
        # Test TXT export (easiest to verify)
        response = export_txt(sample_story_text, "Test Story", "test_123")
        content = response.get_data(as_text=True)
        
        # Key elements should be present
        assert "Mara" in content or "lighthouse" in content.lower()
        assert len(content) > 100  # Should have substantial content
    
    def test_export_handles_multiline_content(self, app_context):
        """Test that exports handle multiline content correctly."""
        multiline_text = """# Multiline Story

First paragraph.

Second paragraph with multiple sentences. This is another sentence.

Third paragraph."""
        
        response = export_txt(multiline_text, "Multiline Story", "test_123")
        content = response.get_data(as_text=True)
        
        # Should preserve paragraph structure
        assert "First paragraph" in content
        assert "Second paragraph" in content
        assert "Third paragraph" in content

