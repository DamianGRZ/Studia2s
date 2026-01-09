# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Animal Encyclopedia AI Wrapper** - a FastAPI application that provides an intelligent, cost-optimized interface for answering questions about animals using OpenAI's language models. The system implements semantic routing, semantic caching, anaphora resolution, and context management to reduce API costs while maintaining conversation quality.

## Architecture

The system follows a **multi-stage pipeline architecture** where each component handles a specific optimization or processing task:

### Pipeline Flow
1. **Semantic Router** (`animal_encyclopedia/core/semantic_router.py`) - Filters non-animal queries using cosine similarity against anchor embeddings
2. **Anaphora Resolver** (`animal_encyclopedia/core/anaphora_resolver.py`) - Resolves pronouns ("it", "they") using conversation history
3. **Semantic Cache** (`animal_encyclopedia/cache/semantic_cache.py`) - Checks for semantically similar past queries using FAISS vector search
4. **Context Manager** (`animal_encyclopedia/core/context_manager.py`) - Prepares token-efficient conversation context
5. **LLM Invocation** - Calls OpenAI API only when cache misses
6. **Orchestrator** (`animal_encyclopedia/core/orchestrator.py`) - Coordinates all components

### Key Components

**Orchestrator Pattern**: The `AnimalEncyclopediaOrchestrator` class in `orchestrator.py` is the central coordinator that orchestrates the entire query processing pipeline. All API requests flow through this single entry point.

**Dependency Injection**: The orchestrator is initialized once at startup via `animal_encyclopedia/api/dependencies.py` and injected into route handlers using FastAPI's `Depends()` mechanism. This ensures singleton behavior and efficient resource usage.

**Semantic Routing**: Uses pre-computed embeddings of "positive" (animal) and "negative" (non-animal) anchor queries. Queries are classified by comparing cosine similarity against these anchors using configurable thresholds (ACCEPT_THRESHOLD, REJECT_THRESHOLD, NEGATIVE_CHECK_THRESHOLD in settings).

**Semantic Cache**: Implements a two-tier caching system - Redis (if available) or in-memory fallback. Uses FAISS vector store (`VectorStore` class) for similarity search. Cache hits occur when a new query has similarity >= CACHE_HIT_THRESHOLD with a cached query.

**Vector Storage**: The `VectorStore` class wraps FAISS IndexFlatIP for cosine similarity search. It maintains mappings between query_ids and vector indices, supports persistence to disk, and provides search/add/clear operations.

**Anaphora Resolution**: Uses regex-based entity extraction to scan recent conversation history (CONTEXT_WINDOW turns) and replace pronouns/demonstratives in current query with the last mentioned animal. Current implementation uses capitalization patterns and stopword filtering (simplified approach). Production systems should integrate spaCy NER or taxonomy databases for improved accuracy. Critical for multi-turn conversations.

**Session Management**: Sessions are stored in-memory in the orchestrator (production should use Redis/database). Each session maintains conversation history as a list of (user_query, assistant_response) tuples, truncated to MAX_HISTORY_TURNS.

## Development Commands

### Quick Start (Automated)
```bash
# Interactive setup script (recommended for first-time setup)
python scripts/init_project.py

# This will:
# 1. Install dependencies
# 2. Install spaCy model
# 3. Configure .env file interactively
# 4. Generate embeddings
# 5. Verify setup
```

### Manual Setup

#### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Unix/MacOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Note: spaCy is included in requirements for future NER enhancements
# Current implementation uses regex-based entity extraction
# Optionally download spaCy model for future use:
# python -m spacy download en_core_web_sm
```

#### Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your-key-here
```

#### Generate Embeddings (Required)
```bash
# Generate embeddings with standard anchor set
python scripts/generate_embeddings.py

# Or use extended anchor set (recommended for production)
python scripts/generate_embeddings.py --extended
```

#### Verify Setup
```bash
# Check that everything is configured correctly
python scripts/check_setup.py
```

### Running the Application
```bash
# Run development server (with auto-reload)
python animal_encyclopedia/api/app.py

# Or use uvicorn directly
uvicorn animal_encyclopedia.api.app:app --reload --host 0.0.0.0 --port 8000

# Run in production mode (set DEBUG=False in .env)
uvicorn animal_encyclopedia.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing
```bash
# NOTE: Test suite is currently under development
# Basic test structure is in place, expand as needed

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=animal_encyclopedia

# Run specific test file
pytest tests/test_orchestrator.py

# Run with async support
pytest --asyncio-mode=auto
```

**Test Files Available:**
- `test_orchestrator.py` - Pipeline integration tests
- `test_semantic_router.py` - Routing threshold tests
- `test_semantic_cache.py` - Cache hit/miss scenarios
- `test_anaphora_resolver.py` - Pronoun resolution cases

### Code Quality
```bash
# Format code with black
black animal_encyclopedia/ config/ tests/

# Lint with ruff
ruff check animal_encyclopedia/ config/ tests/

# Auto-fix linting issues
ruff check --fix animal_encyclopedia/ config/ tests/
```

### API Documentation
Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health (or http://localhost:8000/)

## Important Implementation Notes

### Embeddings File
The application requires pre-computed embeddings to function properly:
- **Required file**: `data/embeddings.npz` containing:
  - `anchor_embeddings` - Positive (animal) query embedding vectors
  - `negative_embeddings` - Non-animal query embedding vectors
  - `positive_queries` - Original anchor query text (metadata)
  - `negative_queries` - Original negative query text (metadata)
- The `dependencies.py` file loads anchor queries from `animal_encyclopedia.data.sample_anchors.get_sample_anchors()`
- If `embeddings.npz` is missing, the system falls back to random embeddings (for demo only - NOT functional)
- **To generate embeddings**: Run `python scripts/generate_embeddings.py` (see setup instructions above)
- This file is automatically generated by the init script or can be generated manually
- Regenerate whenever you modify anchor queries in `sample_anchors.py`

### Session Storage
Current implementation stores sessions in-memory (`self.sessions` dict in orchestrator). For production:
- Replace with Redis using same connection settings as semantic cache
- Use session_id as key, JSON-serialized history as value
- Implement TTL for automatic session cleanup

### Cache Backend
The semantic cache automatically detects Redis availability:
- If Redis is running and accessible → uses Redis with TTL
- If Redis unavailable → falls back to in-memory dict with LRU eviction
- Check logs for "Semantic cache using [redis|in-memory] backend"

### Environment Variables
All configuration is managed through `config/settings.py` using pydantic-settings:
- Loads from `.env` file automatically
- Falls back to defaults if env vars not set
- Critical variables: `OPENAI_API_KEY` (required for LLM responses, optional if only testing semantic routing/caching)
- Tunable thresholds: `ACCEPT_THRESHOLD`, `REJECT_THRESHOLD`, `CACHE_HIT_THRESHOLD`, `NEGATIVE_CHECK_THRESHOLD`

### Advanced Configuration
Additional settings available in `config/settings.py`:

**Monitoring:**
- `ENABLE_METRICS` (bool, default: True) - Enable Prometheus metrics
- `METRICS_PORT` (int, default: 9090) - Metrics endpoint port

**Context Caching:**
- `CONTEXT_CACHE_THRESHOLD` (int, default: 3) - Minimum turns for context summarization

**Data Paths:**
- `ANCHOR_DATASET_PATH` (str) - Path to anchor dataset JSON file

### Logging
Logging is configured in `app.py`:
- DEBUG level if `settings.DEBUG=True`
- INFO level otherwise
- Format includes timestamp, logger name, level, message
- Key log points: cache hits, anaphora resolution, routing decisions

### Error Handling
The FastAPI app includes:
- Global exception handler that catches all unhandled exceptions
- Returns detailed error in DEBUG mode, generic message in production
- Route-specific try/except blocks for granular error handling
- HTTP 500 for server errors, appropriate status codes in routes

## Project Structure
```
animal_encyclopedia/
  api/           - FastAPI routes and dependencies
  cache/         - Semantic caching system
  core/          - Core processing pipeline (routing, resolution, context, orchestrator)
  data/          - Data loading utilities (sample anchors)
  utils/         - Utilities (vector store)
config/          - Application settings
scripts/         - Setup and maintenance scripts
  init_project.py       - Interactive setup wizard
  generate_embeddings.py - Generate anchor embeddings
  check_setup.py        - Verify configuration
tests/           - Test suite (currently empty)
logs/            - Application logs
data/            - Runtime data (embeddings, vector store)
```

## Common Tasks

### Adding New Anchor Queries
1. Edit the function in `animal_encyclopedia/data/sample_anchors.py` (or create it)
2. Add queries to positive/negative lists
3. Regenerate embeddings: `python scripts/generate_embeddings.py`
4. Restart application to load new embeddings

### Adjusting Routing Sensitivity
Edit thresholds in `.env`:
- Increase `ACCEPT_THRESHOLD` (0.72) → fewer queries accepted, stricter animal filter
- Decrease `REJECT_THRESHOLD` (0.45) → reject more aggressively
- Adjust `NEGATIVE_CHECK_THRESHOLD` (0.60) → tune non-animal detection

### Modifying Response Format
Edit `NANO_SYSTEM_PROMPT` in `animal_encyclopedia/core/prompts.py`:
- Contains full system prompt with markdown formatting instructions
- Uses template variables: `{CONTEXT_HISTORY}` and `{USER_QUERY}`
- Changes take effect on next API call (no restart needed)

### Debugging Pipeline Issues
Enable debug mode in `.env`: `DEBUG=True`
- Detailed logs for each pipeline stage
- Full error stack traces in API responses
- Check logs for: routing decisions, anaphora resolution, cache hits/misses
- Use `/api/v1/stats` endpoint to monitor router and cache statistics