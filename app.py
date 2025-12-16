"""Flask web app for Short Story Pipeline."""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.genres import get_available_genres, get_genre_config
from src.shortstory.utils import check_distinctiveness, MAX_WORD_COUNT

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

pipeline = ShortStoryPipeline()
stories = {}


def word_count_response(word_count, max_words=MAX_WORD_COUNT):
    """Build standardized word count response."""
    return {
        "word_count": word_count,
        "max_words": max_words,
        "remaining_words": max_words - word_count
    }


def get_story_or_404(story_id):
    """Get story or return 404."""
    if story_id not in stories:
        return None, jsonify({"error": "Not found"}), 404
    return stories[story_id], None, None


@app.route('/')
def index():
    return render_template('index.html', genres=get_available_genres())


@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/api/genres', methods=['GET'])
def get_genres():
    return jsonify({"genres": get_available_genres()})


@app.route('/api/generate', methods=['POST'])
def generate_story():
    try:
        data = request.get_json() or {}
        idea = data.get('idea', '').strip()
        character = data.get('character', {})
        theme = data.get('theme', '').strip()
        genre = data.get('genre', 'General Fiction')
        
        if not idea:
            return jsonify({"error": "Story idea required"}), 400
        
        if isinstance(character, str):
            character = {"description": character}
        
        genre_config = get_genre_config(genre)
        pipeline.genre = genre
        pipeline.genre_config = genre_config
        
        premise = pipeline.capture_premise(idea, character, theme, validate=True)
        outline = pipeline.generate_outline(genre=genre)
        scaffold = pipeline.scaffold(genre=genre)
        
        framework = genre_config.get('framework', 'narrative_arc')
        outline_structure = genre_config.get('outline', ['setup', 'complication', 'resolution'])
        constraints = genre_config.get('constraints', {})
        tone = scaffold.get('tone', constraints.get('tone', 'balanced'))
        pace = scaffold.get('pace', constraints.get('pace', 'moderate'))
        pov = scaffold.get('pov', constraints.get('pov_preference', 'flexible'))
        
        idea_dist = check_distinctiveness(idea)
        char_dist = check_distinctiveness(None, character=character)
        
        char_desc = character.get('description', character) if isinstance(character, dict) else character
        cliche_msg = f"⚠️ Clichés: {', '.join(idea_dist.get('found_cliches', []))}" if idea_dist.get('has_cliches') else "✓ No clichés"
        generic_msg = f"⚠️ Generic: {', '.join(char_dist.get('generic_elements', []))}" if char_dist.get('has_generic_archetype') else "✓ Distinctive"
        
        story_text = f"""# {idea}

## Genre: {genre} | Framework: {framework} | Structure: {', '.join(outline_structure)}
**Tone:** {tone} | **Pace:** {pace} | **POV:** {pov}

## Character
{char_desc}

## Theme
{theme}

## Distinctiveness
Idea: {idea_dist['distinctiveness_score']:.2f}/1.0 | Character: {char_dist['distinctiveness_score']:.2f}/1.0
{cliche_msg}
{generic_msg}

## Story
[Placeholder - full pipeline stages to be implemented]

**Constraints:** {', '.join([f"{k}:{v}" for k, v in constraints.items()])}

Word count: 0 / {MAX_WORD_COUNT}
"""
        
        word_count = pipeline.word_validator.count_words(story_text)
        story_id = f"story_{len(stories)}"
        stories[story_id] = {
            "id": story_id, "premise": premise, "genre": genre,
            "genre_config": genre_config, "text": story_text,
            "word_count": word_count, "max_words": MAX_WORD_COUNT
        }
        
        return jsonify({
            "success": True, "story_id": story_id, "story": story_text,
            **word_count_response(word_count), "premise": premise,
            "genre": genre, "genre_config": genre_config
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/story/<story_id>', methods=['GET'])
def get_story(story_id):
    story, error, code = get_story_or_404(story_id)
    if error:
        return error, code
    word_count = pipeline.word_validator.count_words(story["text"])
    return jsonify({
        "story_id": story_id, "story": story["text"],
        **word_count_response(word_count, story["max_words"]),
        "premise": story.get("premise")
    })


@app.route('/api/story/<story_id>', methods=['PUT'])
def update_story(story_id):
    story, error, code = get_story_or_404(story_id)
    if error:
        return error, code
    
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Text required"}), 400
    
    word_count, is_valid = pipeline.word_validator.validate(data['text'], raise_error=False)
    if not is_valid:
        return jsonify({
            "error": f"Exceeds limit ({word_count} > {MAX_WORD_COUNT})",
            **word_count_response(word_count)
        }), 400
    
    story["text"] = data['text']
    story["word_count"] = word_count
    return jsonify({"success": True, "story_id": story_id, **word_count_response(word_count)})


@app.route('/api/validate', methods=['POST'])
def validate_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Text required"}), 400
    
    word_count, is_valid = pipeline.word_validator.validate(data['text'], raise_error=False)
    return jsonify({
        **word_count_response(word_count),
        "is_valid": is_valid,
        "distinctiveness": check_distinctiveness(data['text'])
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

