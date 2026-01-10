# Pipeline Architecture — Short Story Pipeline

> **See [CONCEPTS.md](CONCEPTS.md) for definitions of distinctiveness, voice development, memorability, and core tools.**  
> **See [planning.md](planning.md) for the Product Requirements Document (PRD).**

## Overview
The Short Story Pipeline is a modular system that transforms a creative premise into a polished short story draft through five distinct stages. Each stage builds upon the previous one, maintaining a clear separation of concerns and enabling extensibility.

## Pipeline Stages

### 1. Premise Capture
**Purpose**: Capture the foundational creative elements with emphasis on [distinctiveness and memorability](CONCEPTS.md#memorability).

**Inputs**:
- Initial idea or concept (must avoid generic setups)
- Character sketches with **specific quirks, contradictions, and voice markers**
- Theme or central question (resonant, not clichéd)

**Outputs**:
- `PremiseModel` (Pydantic model) containing:
  - Core idea (uniqueness score)
  - Primary character(s) as `CharacterModel` with **distinctive traits, speech patterns, contradictions**
  - Central theme (avoiding generic messages)
  - Validation results (distinctiveness checks)

**Key Functions**:
- `capture_premise()`: Collects and structures initial creative input, returns `PremiseModel`
- `validate_premise()`: Ensures premise has sufficient detail for outlining
- `check_distinctiveness()`: Uses [anti-generic filters](CONCEPTS.md#anti-generic-filters) to flag generic elements
- `identify_voice_markers()`: Captures character speech patterns and narrative voice potential

---

### 2. Outline Generation
**Purpose**: Create a structural blueprint with unexpected beats and memorable moments (see [distinctiveness](CONCEPTS.md#distinctiveness)).

**Inputs**:
- Premise object from Stage 1

**Outputs**:
- `OutlineModel` (Pydantic model) containing:
  - Genre and framework
  - Structure (list of act labels)
  - Acts dictionary (beginning, middle, end)
  - Detailed outline data stored separately for backward compatibility

**Key Functions**:
- `generate_outline()`: Creates three-act structure from premise, returns `OutlineModel` ✅ **Implemented**
- `generate_outline_structure()`: LLM-based outline generation with template fallback ✅ **Implemented**
- Beat validation: Uses [cliché detection](CONCEPTS.md#cliché-detection-system) to flag predictable beats ✅ **Implemented**
- Voice opportunities: Automatically identifies scenes where [voice development](CONCEPTS.md#voice-development) can emerge ✅ **Implemented**

---

### 3. Scaffolding
**Purpose**: Establish distinctive narrative voice, perspective, and stylistic parameters that create [memorability](CONCEPTS.md#memorability).

**Inputs**:
- Outline object from Stage 2

**Outputs**:
- Scaffold object containing:
  - Point of view (first, second, third person) with **specific voice characteristics**
  - Tone (serious, humorous, melancholic, etc.) with **nuanced emotional register**
  - Prose style (sparse, lyrical, dialogue-heavy, etc.) with **rhythm and texture**
  - Conflict mapping (internal/external tensions)
  - **Character voice profiles**: Speech patterns, vocabulary, rhythm for each character
  - **Language register**: Formal/colloquial/slang mix that creates distinctiveness
  - **Sensory specificity**: Which senses to emphasize for vividness

**Key Functions**:
- `scaffold()`: Generates complete scaffold structure with voice development ✅ **Implemented**
- `generate_scaffold_structure()`: LLM-based scaffolding with template fallback ✅ **Implemented**
- Narrative voice development: POV selection with rationale, prose style, sentence rhythm ✅ **Implemented**
- Character voice profiles: Speech patterns, vocabulary, rhythm from character quirks ✅ **Implemented**
- Conflict mapping: Identifies and structures internal/external conflicts (conflict-first approach) ✅ **Implemented**
- Tone and emotional register: Nuanced emotional register with mood and atmosphere ✅ **Implemented**
- Sensory specificity: Defines which senses to emphasize for vividness ✅ **Implemented**
- Style guidelines: Sentence length, dialogue ratio, description density, pacing ✅ **Implemented**

---

### 4. Drafting
**Purpose**: Generate prose narrative with precise, memorable language and distinctive character voices (see [voice development](CONCEPTS.md#voice-development)).

**Inputs**:
- Scaffold object from Stage 3

**Outputs**:
- Draft object containing:
  - Full prose narrative with **specific, vivid language**
  - Word count
  - Scene breaks
  - Character dialogue with **distinctive voice patterns**
  - Action with **sensory specificity**
  - **Language markers**: Memorable phrases, unique word choices, rhythm

**Key Functions**:
- `draft_narrative()`: Generates prose from scaffold and outline with [voice consistency](CONCEPTS.md#voice-consistency)
- `enforce_word_count()`: Ensures draft stays within ≤ 7500 word limit while maximizing impact
- `generate_scenes()`: Converts outline beats into prose scenes with vivid detail
- `apply_character_voices()`: Uses [character voice analyzer](CONCEPTS.md#character-voice-analyzer) for distinct patterns
- `avoid_generic_language()`: Uses [cliché detection system](CONCEPTS.md#cliché-detection-system)
- `maximize_sensory_detail()`: Adds specific, memorable sensory information

---

### 5. Revision
**Purpose**: Sharpen language to maximum impact, deepen character distinctiveness, eliminate generic elements (see [distinctiveness](CONCEPTS.md#distinctiveness)).

**Inputs**:
- Draft object from Stage 4

**Outputs**:
- Revised draft object containing:
  - **Precise, memorable prose** (every word earns its place)
  - Refined pacing with **rhythm and momentum**
  - **Deepened character distinctiveness** (quirks, contradictions, voice consistency)
  - **Language sharpening**: Replaced clichés, strengthened specificity, enhanced voice
  - **Memorability score**: Metrics on distinctiveness and impact

**Key Functions**:
- `revise()`: Comprehensive revision with LLM or rule-based fallback ✅ **Implemented**
- `revise_story_text()`: LLM-based revision with distinctiveness improvements ✅ **Implemented**
- Cliché detection and replacement: Uses [cliché detection system](CONCEPTS.md#cliché-detection-system) ✅ **Implemented**
- Character voice analysis: Uses [character voice analyzer](CONCEPTS.md#character-voice-analyzer) for consistency ✅ **Implemented**
- Memorability scoring: Uses [memorability scorer](CONCEPTS.md#memorability-scorer) for multi-dimensional analysis ✅ **Implemented**
- Word count validation: Validates final word count compliance ✅ **Implemented**

---

## Data Flow

```
Premise → Outline → Scaffold → Draft → Revised Draft
  ↓         ↓         ↓         ↓          ↓
[Stage 1] [Stage 2] [Stage 3] [Stage 4] [Stage 5]
```

## Pipeline Class Structure

```python
ShortStoryPipeline
├── premise: Optional[PremiseModel]  # Pydantic model (Stage 1 output)
├── outline: Optional[OutlineModel]   # Pydantic model (Stage 2 output)
├── _scaffold_data: Dict[str, Any]   # Scaffold data (Stage 3 output)
├── _draft_data: Dict[str, Any]      # Draft data (Stage 4 output)
└── _revised_draft_data: Dict[str, Any]  # Revised draft (Stage 5 output)
```

### Data Models

The pipeline uses Pydantic models for type safety and validation:

- **`PremiseModel`**: Story premise with idea, character (`CharacterModel`), theme, and validation
- **`OutlineModel`**: Story outline with genre, framework, structure, and acts
- **`CharacterModel`**: Character description with name, description, quirks, contradictions
- **`StoryMetadata`**: Separated metadata (tone, pace, pov, distinctiveness scores)
- **`StoryModel`**: Complete story model (used for final story creation)

All models are defined in `src/shortstory/models.py` and provide automatic validation, type safety, and clear structure.

## Constraints & Validation

- **Word Count**: Enforced at drafting stage and validated at revision stage (≤ 7500 words)
- **Distinctiveness**: See [distinctiveness requirement](CONCEPTS.md#distinctiveness-requirement)
- **Voice Consistency**: See [voice consistency](CONCEPTS.md#voice-consistency)
- **Memorability**: See [memorability metrics](CONCEPTS.md#memorability-metrics)
- **Conflict-First**: Scaffolding stage prioritizes conflict identification and structure
- **Modularity**: Each stage can be run independently or as part of full pipeline
- **Extensibility**: New stages or utilities can be added without breaking existing flow

## Usage Pattern

```python
from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.models import PremiseModel, OutlineModel

# Initialize pipeline
pipeline = ShortStoryPipeline(max_word_count=7500, genre="Science Fiction")

# Stage 1: Capture premise (returns PremiseModel)
premise = pipeline.capture_premise(
    idea="A scientist discovers time is a loop",
    character={"name": "Dr. Chen", "description": "Brilliant but obsessive"},
    theme="The cost of knowledge"
)

# Stage 2: Generate outline (returns OutlineModel)
outline = pipeline.generate_outline(genre="Science Fiction")

# Stage 3: Scaffold
scaffold = pipeline.scaffold()

# Stage 4: Draft
draft = pipeline.draft()

# Stage 5: Revise
revised = pipeline.revise()
```

**Note**: The pipeline now uses Pydantic models (`PremiseModel`, `OutlineModel`, `CharacterModel`) for type safety and automatic validation. These models provide better IDE support, catch errors early, and ensure data consistency throughout the pipeline.

## Integration Points

- **Flash Fiction Pipeline**: Can share premise capture and scaffolding utilities
- **Screenplay Pipeline**: Can leverage conflict mapping and outline structures
- **Future Forms**: Architecture supports novella, serialized stories, and experimental formats

