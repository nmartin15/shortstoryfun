"""
Integration tests for end-to-end workflows.

Tests cover:
- Complete story generation workflow
- Story revision workflow
- Story export workflow
- Story browser workflow
- API endpoint integration
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask

from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.utils.repository import DatabaseStoryRepository, FileStoryRepository
from src.shortstory.utils.db_storage import StoryStorage, init_database
from tests.conftest import check_optional_dependency
from tests.test_constants import HTTP_OK, HTTP_CREATED


@pytest.fixture
def temp_db_dir(tmp_path):
    """Create a temporary directory for test database."""
    test_db_dir = tmp_path / "test_data"
    test_db_dir.mkdir()
    test_db_path = test_db_dir / "stories.db"
    
    with patch('src.shortstory.utils.db_storage.DB_DIR', test_db_dir), \
         patch('src.shortstory.utils.db_storage.DB_PATH', test_db_path):
        yield test_db_dir, test_db_path
    
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def repository(temp_db_dir):
    """Create a DatabaseStoryRepository instance for testing."""
    test_db_dir, test_db_path = temp_db_dir
    init_database()
    yield DatabaseStoryRepository(use_cache=False)


@pytest.fixture
def app_context():
    """Create Flask application context for tests."""
    from app import create_app
    app = create_app()
    with app.app_context():
        yield app


class TestCompleteStoryGenerationWorkflow:
    """Test complete story generation from start to finish."""
    
    def test_generate_story_end_to_end(self, app_context, repository):
        """Test complete story generation workflow via API."""
        from app import create_app
        app = create_app()
        
        with app.test_client() as client:
            with patch('app.get_pipeline') as mock_pipeline, \
                 patch('app.get_story_repository', return_value=repository):
                
                # Setup mock pipeline
                mock_pipe = MagicMock()
                mock_pipe.capture_premise.return_value = {
                    "idea": "A lighthouse keeper collects lost voices",
                    "character": {"name": "Mara", "description": "A quiet keeper"},
                    "theme": "Untold stories"
                }
                mock_pipe.generate_outline.return_value = {
                    "genre": "General Fiction",
                    "framework": "narrative_arc",
                    "acts": {
                        "beginning": "Mara tends her collection",
                        "middle": "A voice calls out",
                        "end": "Mara finds peace"
                    }
                }
                mock_pipe.scaffold.return_value = {
                    "tone": "melancholic",
                    "pace": "slow",
                    "pov": "third person"
                }
                mock_pipe.draft.return_value = {
                    "text": "# The Lighthouse Keeper's Collection\n\nEach voice was stored in a glass jar...",
                    "word_count": 5000
                }
                mock_pipe.revise.return_value = {
                    "text": "# The Lighthouse Keeper's Collection\n\nEach voice was stored in a glass jar...",
                    "word_count": 5200
                }
                mock_pipeline.return_value = mock_pipe
                
                # Step 1: Generate story
                response = client.post('/api/story/generate', json={
                    "genre": "General Fiction",
                    "premise": {
                        "idea": "A lighthouse keeper collects lost voices",
                        "character": {"name": "Mara"},
                        "theme": "Untold stories"
                    }
                })
                
                assert response.status_code in [HTTP_OK, HTTP_CREATED]
                data = response.get_json()
                assert data is not None
                assert "story" in data
                
                story_id = data["story"]["id"]
                assert story_id is not None
                
                # Step 2: Verify story was saved
                saved_story = repository.load(story_id)
                assert saved_story is not None
                assert saved_story["id"] == story_id
                
                # Step 3: Load story via API
                response = client.get(f'/api/story/{story_id}')
                assert response.status_code == HTTP_OK
                loaded_data = response.get_json()
                assert loaded_data is not None
                assert loaded_data["story"]["id"] == story_id
    
    def test_story_generation_with_all_stages(self, repository):
        """Test story generation with all pipeline stages."""
        with patch('src.shortstory.providers.factory.get_default_provider') as mock_provider:
            # Setup mock LLM client
            mock_client = MagicMock()
            mock_client.generate.return_value = "Generated story text"
            mock_client.model_name = "gemini-2.5-flash"
            mock_provider.return_value = mock_client
            
            # Create pipeline
            pipeline = ShortStoryPipeline()
            pipeline.genre = "General Fiction"
            
            # Step 1: Capture premise
            premise = pipeline.capture_premise(
                idea="A test story",
                character={"name": "Test Character"},
                theme="Test theme"
            )
            assert premise is not None
            
            # Step 2: Generate outline
            outline = pipeline.generate_outline()
            assert outline is not None
            
            # Step 3: Scaffold
            scaffold = pipeline.scaffold()
            assert scaffold is not None
            
            # Step 4: Draft
            draft = pipeline.draft()
            assert draft is not None
            assert "text" in draft
            
            # Step 5: Save to repository
            story_data = {
                "id": pipeline.story_id,
                "genre": pipeline.genre,
                "premise": premise,
                "outline": outline,
                "scaffold": scaffold,
                "text": draft.get("text", ""),
                "word_count": draft.get("word_count", 0)
            }
            
            result = repository.save(story_data)
            assert result is True
            
            # Step 6: Verify saved
            saved = repository.load(pipeline.story_id)
            assert saved is not None
            assert saved["id"] == pipeline.story_id


class TestStoryRevisionWorkflow:
    """Test story revision workflow."""
    
    def test_revise_story_end_to_end(self, app_context, repository):
        """Test complete story revision workflow."""
        from app import create_app
        app = create_app()
        
        # First, create a story
        story_id = "test_revision_workflow"
        story = {
            "id": story_id,
            "genre": "General Fiction",
            "text": "Original story text",
            "word_count": 1000
        }
        repository.save(story)
        
        with app.test_client() as client:
            with patch('app.get_pipeline') as mock_pipeline, \
                 patch('app.get_story_repository', return_value=repository):
                
                mock_pipe = MagicMock()
                mock_pipe.revise.return_value = {
                    "text": "Revised story text",
                    "word_count": 1200
                }
                mock_pipeline.return_value = mock_pipe
                
                # Revise story
                response = client.post(f'/api/story/{story_id}/revise', json={
                    "use_llm": True
                })
                
                assert response.status_code == HTTP_OK
                data = response.get_json()
                assert data is not None
                
                # Verify story was updated
                updated_story = repository.load(story_id)
                assert updated_story is not None
                # Story should have revision history
                assert "revision_history" in updated_story or "revised_draft" in updated_story


class TestStoryExportWorkflow:
    """Test story export workflow."""
    
    def test_export_story_workflow(self, app_context, repository):
        """Test complete story export workflow."""
        from app import create_app
        app = create_app()
        
        # Create a story
        story_id = "test_export_workflow"
        story = {
            "id": story_id,
            "genre": "General Fiction",
            "text": "# Test Story\n\nThis is test content.",
            "word_count": 100
        }
        repository.save(story)
        
        with app.test_client() as client:
            with patch('app.get_story_repository', return_value=repository):
                # Export as PDF
                response = client.get(f'/api/story/{story_id}/export/pdf')
                assert response.status_code == HTTP_OK
                assert response.content_type == 'application/pdf'
                
                # Export as Markdown
                response = client.get(f'/api/story/{story_id}/export/markdown')
                assert response.status_code == HTTP_OK
                assert "text/markdown" in response.content_type or "text/plain" in response.content_type
                
                # Export as TXT
                response = client.get(f'/api/story/{story_id}/export/txt')
                assert response.status_code == HTTP_OK
                assert response.content_type == 'text/plain'


class TestStoryBrowserWorkflow:
    """Test story browser workflow."""
    
    def test_list_and_browse_stories(self, app_context, repository):
        """Test listing and browsing stories."""
        from app import create_app
        app = create_app()
        
        # Create multiple stories
        for i in range(5):
            story = {
                "id": f"browser_test_{i}",
                "genre": "General Fiction" if i % 2 == 0 else "Science Fiction",
                "text": f"Story content {i}",
                "word_count": 100 + i * 10
            }
            repository.save(story)
        
        with app.test_client() as client:
            with patch('app.get_story_repository', return_value=repository):
                # List all stories
                response = client.get('/api/story/list')
                assert response.status_code == HTTP_OK
                data = response.get_json()
                assert data is not None
                assert "stories" in data
                assert len(data["stories"]) == 5
                
                # List with pagination
                response = client.get('/api/story/list?page=1&per_page=2')
                assert response.status_code == HTTP_OK
                data = response.get_json()
                assert len(data["stories"]) == 2
                assert data["pagination"]["total"] == 5
                
                # Filter by genre
                response = client.get('/api/story/list?genre=General Fiction')
                assert response.status_code == HTTP_OK
                data = response.get_json()
                # Should have 3 General Fiction stories (0, 2, 4)
                assert len(data["stories"]) == 3
    
    def test_load_story_from_browser(self, app_context, repository):
        """Test loading a story from the browser."""
        from app import create_app
        app = create_app()
        
        # Create a story
        story_id = "browser_load_test"
        story = {
            "id": story_id,
            "genre": "General Fiction",
            "text": "Test story content",
            "word_count": 100
        }
        repository.save(story)
        
        with app.test_client() as client:
            with patch('app.get_story_repository', return_value=repository):
                # Load story
                response = client.get(f'/api/story/{story_id}')
                assert response.status_code == HTTP_OK
                data = response.get_json()
                assert data is not None
                assert data["story"]["id"] == story_id
                assert data["story"]["text"] == "Test story content"


class TestAPIEndpointIntegration:
    """Test API endpoint integration."""
    
    def test_story_lifecycle_api(self, app_context, repository):
        """Test complete story lifecycle via API."""
        from app import create_app
        app = create_app()
        
        with app.test_client() as client:
            with patch('app.get_pipeline') as mock_pipeline, \
                 patch('app.get_story_repository', return_value=repository):
                
                # Setup mock pipeline
                mock_pipe = MagicMock()
                mock_pipe.capture_premise.return_value = {
                    "idea": "Test idea",
                    "character": {"name": "Test"},
                    "theme": "Test theme"
                }
                mock_pipe.generate_outline.return_value = {
                    "genre": "General Fiction",
                    "framework": "narrative_arc",
                    "acts": {"beginning": "start", "middle": "middle", "end": "end"}
                }
                mock_pipe.scaffold.return_value = {"tone": "balanced"}
                mock_pipe.draft.return_value = {"text": "Test story", "word_count": 100}
                mock_pipe.revise.return_value = {"text": "Revised story", "word_count": 120}
                mock_pipeline.return_value = mock_pipe
                
                # 1. Generate story
                response = client.post('/api/story/generate', json={
                    "genre": "General Fiction",
                    "premise": {"idea": "Test idea"}
                })
                assert response.status_code in [HTTP_OK, HTTP_CREATED]
                story_id = response.get_json()["story"]["id"]
                
                # 2. Get story
                response = client.get(f'/api/story/{story_id}')
                assert response.status_code == HTTP_OK
                
                # 3. Update story
                response = client.put(f'/api/story/{story_id}', json={
                    "text": "Updated story text"
                })
                assert response.status_code == HTTP_OK
                
                # 4. Revise story
                response = client.post(f'/api/story/{story_id}/revise', json={
                    "use_llm": False
                })
                assert response.status_code == HTTP_OK
                
                # 5. Export story
                response = client.get(f'/api/story/{story_id}/export/markdown')
                assert response.status_code == HTTP_OK
                
                # 6. Delete story
                response = client.delete(f'/api/story/{story_id}')
                assert response.status_code in [HTTP_OK, 204]
                
                # 7. Verify deleted
                response = client.get(f'/api/story/{story_id}')
                assert response.status_code == 404


class TestRepositoryIntegration:
    """Test repository integration."""
    
    def test_database_repository_integration(self, temp_db_dir):
        """Test DatabaseStoryRepository integration."""
        test_db_dir, test_db_path = temp_db_dir
        init_database()
        
        repo = DatabaseStoryRepository(use_cache=False)
        
        # Create story
        story = {
            "id": "repo_integration_test",
            "genre": "General Fiction",
            "text": "Test story",
            "word_count": 100
        }
        
        # Save
        result = repo.save(story)
        assert result is True
        
        # Load
        loaded = repo.load("repo_integration_test")
        assert loaded is not None
        assert loaded["id"] == "repo_integration_test"
        
        # List
        result = repo.list(page=1, per_page=10)
        assert "stories" in result
        assert len(result["stories"]) == 1
        
        # Update
        result = repo.update("repo_integration_test", {"text": "Updated text"})
        assert result is True
        
        # Verify update
        loaded = repo.load("repo_integration_test")
        assert loaded["text"] == "Updated text"
        
        # Delete
        result = repo.delete("repo_integration_test")
        assert result is True
        
        # Verify deletion
        loaded = repo.load("repo_integration_test")
        assert loaded is None
    
    def test_file_repository_integration(self, tmp_path):
        """Test FileStoryRepository integration."""
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir()
        
        with patch('src.shortstory.utils.repository.FILE_STORAGE_DIR', stories_dir):
            repo = FileStoryRepository()
            
            # Create story
            story = {
                "id": "file_repo_test",
                "genre": "General Fiction",
                "text": "Test story",
                "word_count": 100
            }
            
            # Save
            result = repo.save(story)
            assert result is True
            
            # Load
            loaded = repo.load("file_repo_test")
            assert loaded is not None
            assert loaded["id"] == "file_repo_test"
            
            # List
            result = repo.list(page=1, per_page=10)
            assert "stories" in result
            assert len(result["stories"]) == 1
            
            # Delete
            result = repo.delete("file_repo_test")
            assert result is True
            
            # Verify deletion
            loaded = repo.load("file_repo_test")
            assert loaded is None

