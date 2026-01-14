#!/usr/bin/env python3
"""
Spike Research: Story Generation Diagnostic

This script generates a test story and logs all intermediate steps
to diagnose why stories are cutting off before reaching 4000+ words.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging to file
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"spike_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 80)
logger.info("SPIKE RESEARCH: Story Generation Diagnostic")
logger.info("=" * 80)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.shortstory.pipeline import ShortStoryPipeline
from src.shortstory.genres import get_genre_config
from src.shortstory.utils.llm import get_default_client
from src.shortstory.utils.word_count import WordCountValidator

def log_stage(stage_name, data):
    """Log a pipeline stage with details."""
    logger.info("")
    logger.info("-" * 80)
    logger.info(f"STAGE: {stage_name}")
    logger.info("-" * 80)
    if isinstance(data, dict):
        if 'text' in data:
            word_count = len(data['text'].split()) if data.get('text') else 0
            logger.info(f"Word count: {word_count}")
            logger.info(f"Text length: {len(data.get('text', ''))} characters")
            # Log last 200 chars to see how it ends
            if data.get('text'):
                logger.info(f"Last 200 chars: ...{data['text'][-200:]}")
        for key, value in data.items():
            if key != 'text':  # Already logged
                logger.info(f"{key}: {value}")
    else:
        logger.info(f"Data: {data}")

def main():
    """Run diagnostic story generation."""
    
    # Test parameters
    idea = "A lawn mower operator in Arizona discovers a hidden surveillance system in a wealthy client's home"
    character = {
        "name": "Ángel Reyes",
        "description": "Thirty-two-year-old lawn care worker with calloused hands and a keen eye for detail",
        "quirks": ["Notices small details others miss", "Prefers invisibility"],
        "contradictions": "Appears placid but calculates everything"
    }
    theme = "The invisible see everything"
    genre = "Thriller"
    
    logger.info(f"Test Parameters:")
    logger.info(f"  Idea: {idea}")
    logger.info(f"  Character: {character['name']}")
    logger.info(f"  Theme: {theme}")
    logger.info(f"  Genre: {genre}")
    logger.info("")
    
    try:
        # Check API availability
        logger.info("Checking LLM client availability...")
        client = get_default_client()
        is_available = client.check_availability()
        logger.info(f"LLM Client available: {is_available}")
        logger.info(f"Model: {client.model_name}")
        logger.info("")
        
        # Get genre config
        logger.info("Fetching genre config...")
        genre_config = get_genre_config(genre)
        logger.info(f"Genre config loaded: {genre_config is not None}")
        logger.info("")
        
        # Create pipeline
        logger.info("Creating pipeline...")
        pipeline = ShortStoryPipeline(
            max_word_count=7500,
            genre=genre,
            genre_config=genre_config
        )
        logger.info(f"Pipeline max_words: {pipeline.word_validator.max_words}")
        logger.info("")
        
        # Stage 1: Premise
        logger.info("=" * 80)
        logger.info("STARTING PIPELINE EXECUTION")
        logger.info("=" * 80)
        premise = pipeline.capture_premise(idea, character, theme, validate=True)
        log_stage("Premise", premise.dict() if hasattr(premise, 'dict') else premise)
        
        # Stage 2: Outline
        outline = pipeline.generate_outline(genre=genre)
        log_stage("Outline", outline.dict() if hasattr(outline, 'dict') else outline)
        
        # Stage 3: Scaffold
        scaffold = pipeline.scaffold(genre=genre)
        log_stage("Scaffold", scaffold if isinstance(scaffold, dict) else scaffold.__dict__)
        
        # Stage 4: Draft - THIS IS WHERE THE ISSUE LIKELY OCCURS
        logger.info("")
        logger.info("=" * 80)
        logger.info("DRAFT GENERATION - CRITICAL STAGE")
        logger.info("=" * 80)
        draft = pipeline.draft()
        
        draft_word_count = len(draft.get('text', '').split()) if draft.get('text') else 0
        logger.info(f"DRAFT WORD COUNT: {draft_word_count}")
        logger.info(f"MINIMUM REQUIRED: 4000")
        logger.info(f"STATUS: {'✅ PASS' if draft_word_count >= 4000 else '❌ FAIL'}")
        
        if draft.get('text'):
            text = draft['text']
            logger.info(f"Text length: {len(text)} characters")
            logger.info(f"First 500 chars: {text[:500]}")
            logger.info(f"Last 500 chars: {text[-500:]}")
            
            # Check for truncation indicators
            if text.endswith('...'):
                logger.warning("⚠️  Story ends with '...' - may have been truncated by pipeline!")
            if not text.rstrip().endswith(('.', '!', '?', '"', "'")):
                logger.warning("⚠️  Story doesn't end with punctuation - may be cut off mid-sentence!")
        
        log_stage("Draft", draft)
        
        # Stage 5: Revise
        logger.info("")
        logger.info("=" * 80)
        logger.info("REVISION STAGE")
        logger.info("=" * 80)
        revised = pipeline.revise()
        
        revised_word_count = len(revised.get('text', '').split()) if revised.get('text') else 0
        logger.info(f"REVISED WORD COUNT: {revised_word_count}")
        logger.info(f"MINIMUM REQUIRED: 4000")
        logger.info(f"STATUS: {'✅ PASS' if revised_word_count >= 4000 else '❌ FAIL'}")
        
        if revised.get('text'):
            text = revised['text']
            logger.info(f"Text length: {len(text)} characters")
            logger.info(f"Last 500 chars: {text[-500:]}")
            
            # Check for truncation indicators
            if text.endswith('...'):
                logger.warning("⚠️  Revised story ends with '...' - may have been truncated by pipeline!")
            if not text.rstrip().endswith(('.', '!', '?', '"', "'")):
                logger.warning("⚠️  Revised story doesn't end with punctuation - may be cut off!")
        
        log_stage("Revised", revised)
        
        # Final summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Draft word count: {draft_word_count}")
        logger.info(f"Revised word count: {revised_word_count}")
        logger.info(f"Minimum required: 4000")
        logger.info(f"Draft status: {'✅ PASS' if draft_word_count >= 4000 else '❌ FAIL'}")
        logger.info(f"Revised status: {'✅ PASS' if revised_word_count >= 4000 else '❌ FAIL'}")
        
        if draft_word_count < 4000:
            logger.error(f"❌ DRAFT FAILED: Only {draft_word_count} words (need 4000+)")
        if revised_word_count < 4000:
            logger.error(f"❌ REVISED FAILED: Only {revised_word_count} words (need 4000+)")
        
        logger.info("")
        logger.info(f"Full log saved to: {log_file}")
        logger.info("=" * 80)
        
        return {
            'draft_word_count': draft_word_count,
            'revised_word_count': revised_word_count,
            'draft_passed': draft_word_count >= 4000,
            'revised_passed': revised_word_count >= 4000,
            'log_file': str(log_file)
        }
        
    except Exception as e:
        logger.error(f"ERROR during story generation: {e}", exc_info=True)
        logger.info(f"Full error log saved to: {log_file}")
        raise

if __name__ == "__main__":
    result = main()
    sys.exit(0 if (result['draft_passed'] and result['revised_passed']) else 1)
