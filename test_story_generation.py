python
# In src/shortstory/pipeline.py (Hypothetical change for clarity)
# Assuming ShortStoryPipeline can take genre in its constructor or has a set_genre method
# If it needs to be set before capture_premise, ensure the pipeline handles the config.

def test_story_generation():
    # ...

        "description": "A lighthouse keeper with an unusual collection",
        # Run the pipeline
        from src.shortstory.genres import get_genre_config
    
    # Define Character input schema explicitly (e.g., using TypedDict or Pydantic for real code)
    # For a test script, a detailed comment is a good start.
    pipeline = ShortStoryPipeline(genre=genre) # Pass genre to constructor if it handles config
    # OR pipeline.set_genre(genre) if there's a method
        pipeline.genre = genre
        pipeline.genre_config = get_genre_config(genre)
        "quirks": ["Never speaks above a whisper", "Counts everything in threes"], # Expects list of strings
        "contradictions": "Fiercely protective but terrified of connection" # Expects string
    }
    theme = "What happens to the stories we never tell?"
    genre = "Literary"
    
    print(f"📝 Story Idea: {idea}")
    print(f"👤 Character: {character['name']}")
    # ...

    try:
        # ...
        pipeline.capture_premise(idea, character, theme, validate=True) # validate=True is good

        # Optional: Assert on the processed premise if character is incorporated
        # For example, if premise.character is expected to be a dict of specific structure
        # assert isinstance(pipeline.premise.character, dict)
        # assert pipeline.premise.character.get('name') == character['name']
        # ...