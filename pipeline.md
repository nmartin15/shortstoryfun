# Pipeline Architecture — Short Story Pipeline

> **See [CONCEPTS.md](CONCEPTS.md) for definitions of distinctiveness, voice development, memorability, and core tools.**

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
- Structured premise object containing:
  - Core idea (uniqueness score)
  - Primary character(s) with **distinctive traits, speech patterns, contradictions**
  - Central theme (avoiding generic messages)
  - Potential conflicts (specific, not archetypal)
  - **Character voice markers** (dialect, rhythm, vocabulary quirks)

**Key Functions**:
- `capture_premise()`: Collects and structures initial creative input
- `validate_premise()`: Ensures premise has sufficient detail for outlining
- `check_distinctiveness()`: Uses [anti-generic filters](CONCEPTS.md#anti-generic-filters) to flag generic elements
- `identify_voice_markers()`: Captures character speech patterns and narrative voice potential

---

### 2. Outline Generation
**Purpose**: Create a structural blueprint with unexpected beats and memorable moments (see [distinctiveness](CONCEPTS.md#distinctiveness)).

**Inputs**:
- Premise object from Stage 1

**Outputs**:
- Outline object containing:
  - Beginning (setup with **distinctive hook**, inciting incident that surprises)
  - Middle (rising action with **unexpected complications**, not formulaic obstacles)
  - End (climax with **specific resolution**, avoiding generic endings)
  - **Memorable moments**: Scenes that create lasting impressions
  - **Voice opportunities**: Places where character voice can shine

**Key Functions**:
- `generate_outline()`: Creates three-act structure from premise
- `enrich_outline()`: Adds scene-level detail and transitions
- `flag_predictable_beats()`: Uses [cliché detection](CONCEPTS.md#cliché-detection-system) for story beats
- `identify_voice_moments()`: Marks scenes where [voice development](CONCEPTS.md#voice-development) can emerge

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
- `scaffold_pov()`: Determines and configures narrative perspective with voice markers
- `scaffold_tone()`: Establishes emotional register with nuance
- `scaffold_style()`: Sets prose characteristics (sentence length, rhythm, texture)
- `map_conflicts()`: Identifies and structures conflicts (conflict-first approach)
- `develop_character_voices()`: Uses [character voice analyzer](CONCEPTS.md#character-voice-analyzer) to create distinct patterns
- `establish_language_register()`: Defines the linguistic texture (formal/colloquial/slang mix)

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
- `revise_language()`: Sharpens word choice, uses [cliché detection](CONCEPTS.md#cliché-detection-system), strengthens specificity
- `refine_pacing()`: Adjusts rhythm and scene transitions for maximum impact
- `strengthen_arc()`: Enhances narrative progression and character development
- `deepen_character_voices()`: Uses [character voice analyzer](CONCEPTS.md#character-voice-analyzer) for consistency
- `eliminate_generic_elements()`: Uses [anti-generic filters](CONCEPTS.md#anti-generic-filters)
- `calculate_memorability_score()`: Uses [memorability scorer](CONCEPTS.md#memorability-scorer)
- `final_word_count_check()`: Validates final word count compliance

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
├── premise_capture (Stage 1)
├── outline_generator (Stage 2)
├── scaffolding (Stage 3)
├── drafting (Stage 4)
└── revision (Stage 5)
```

## Constraints & Validation

- **Word Count**: Enforced at drafting stage and validated at revision stage (≤ 7500 words)
- **Distinctiveness**: See [distinctiveness requirement](CONCEPTS.md#distinctiveness-requirement)
- **Voice Consistency**: See [voice consistency](CONCEPTS.md#voice-consistency)
- **Memorability**: See [memorability metrics](CONCEPTS.md#memorability-metrics)
- **Conflict-First**: Scaffolding stage prioritizes conflict identification and structure
- **Modularity**: Each stage can be run independently or as part of full pipeline
- **Extensibility**: New stages or utilities can be added without breaking existing flow

## Usage Pattern

1. Initialize pipeline with configuration
2. Run stages sequentially or individually
3. Validate outputs at each stage
4. Export final revised draft

## Integration Points

- **Flash Fiction Pipeline**: Can share premise capture and scaffolding utilities
- **Screenplay Pipeline**: Can leverage conflict mapping and outline structures
- **Future Forms**: Architecture supports novella, serialized stories, and experimental formats

