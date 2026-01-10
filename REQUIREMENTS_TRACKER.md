# Requirements Tracker — Short Story Pipeline

> **See [CONCEPTS.md](CONCEPTS.md) for definitions of core tools and principles.**  
> **See [planning.md](planning.md) for the Product Requirements Document (PRD).**

## Functional Requirements
- [x] Base `ShortStoryPipeline` class with modular stages
- [x] Premise capture module (idea, character, theme) with [distinctiveness validation](CONCEPTS.md#distinctiveness)
- [x] Outline generator (beginning, middle, end) with unexpected beat detection
- [x] Scaffolding module (POV, tone, style) with [voice development](CONCEPTS.md#voice-development)
- [x] Drafting module for prose narrative with [anti-generic filters](CONCEPTS.md#anti-generic-filters)
- [x] Revision utility for language sharpening, character deepening, cliché elimination
- [x] [Character voice analyzer](CONCEPTS.md#character-voice-analyzer)
- [x] [Cliché detection system](CONCEPTS.md#cliché-detection-system)
- [x] [Memorability scorer](CONCEPTS.md#memorability-scorer)
- [x] Database storage with repository pattern
- [x] Background job processing (RQ)
- [x] Export functionality (PDF, Markdown, TXT, DOCX, EPUB)

## Non-Functional Requirements
- [x] Maintainable, modular Python architecture
- [x] Repo hygiene (README, tasks, planning docs)
- [x] Extensible design for future narrative forms
- [x] Clear separation of creative logic vs. utility functions
- [x] Production-ready deployment configuration
- [x] Comprehensive error handling
- [x] Rate limiting and security measures

## Compliance / Constraints
- [x] Enforce max word count (≤ 7500 words) while maximizing impact per word
- [x] Conflict-first philosophy embedded in scaffolding
- [x] [Distinctiveness requirement](CONCEPTS.md#distinctiveness-requirement)
- [x] [Voice consistency](CONCEPTS.md#voice-consistency)
- [x] [Memorability threshold](CONCEPTS.md#memorability-metrics)

