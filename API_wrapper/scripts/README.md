# Scripts Directory

This directory contains utility scripts for setting up and managing the Animal Encyclopedia AI system.

## Available Scripts

### `generate_embeddings.py`
Generates embeddings for semantic routing anchor datasets.

**Purpose**: Creates the `data/embeddings.npz` file required for the semantic router to classify animal vs non-animal queries.

**Usage**:
```bash
# Generate embeddings with standard anchor set
python scripts/generate_embeddings.py

# Generate embeddings with extended anchor set (recommended for production)
python scripts/generate_embeddings.py --extended
```

**Requirements**:
- OpenAI API key configured in `.env`
- Internet connection
- Sufficient OpenAI API credits (~$0.01-0.02 for standard set)

**Output**:
- `data/embeddings.npz` containing:
  - `anchor_embeddings`: Positive (animal query) embeddings
  - `negative_embeddings`: Negative (non-animal query) embeddings
  - `positive_queries`: Original positive query texts
  - `negative_queries`: Original negative query texts

**When to run**:
- First time setup (required)
- After modifying anchor queries in `animal_encyclopedia/data/sample_anchors.py`
- When switching embedding models (update `EMBEDDING_MODEL` in `.env`)

---

### `check_setup.py`
Validates that the system is properly configured and ready to run.

**Purpose**: Diagnostic tool to verify all dependencies, configuration, and required files are in place.

**Usage**:
```bash
python scripts/check_setup.py
```

**What it checks**:
- ✓ `.env` file exists
- ✓ OpenAI API key is configured
- ✓ Required Python packages are installed
- ✓ spaCy language model is downloaded
- ✓ Embeddings file exists and is valid
- ⚠ Redis connection (optional, warns if unavailable)

**When to run**:
- After initial setup
- Before starting the application
- When troubleshooting configuration issues
- After making changes to environment variables

---

## Quick Start Workflow

1. **Set up environment**:
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

2. **Configure application**:
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=sk-...
   ```

3. **Generate embeddings**:
   ```bash
   python scripts/generate_embeddings.py --extended
   ```

4. **Verify setup**:
   ```bash
   python scripts/check_setup.py
   ```

5. **Start application**:
   ```bash
   python animal_encyclopedia/api/app.py
   ```

---

## Troubleshooting

### "OpenAI API key not configured"
- Ensure `.env` file exists in project root
- Verify `OPENAI_API_KEY=sk-...` is set in `.env`
- Check that the key is valid and has credits

### "Embeddings file not found"
- Run `python scripts/generate_embeddings.py`
- Check that `data/` directory exists and is writable
- Verify network connectivity to OpenAI API

### "Redis not available"
- This is a warning, not an error
- The system will use in-memory caching instead
- To use Redis, ensure it's running on configured host/port

### "spaCy model not installed"
- Run `python -m spacy download en_core_web_sm`
- Ensure you're in the correct virtual environment

### Import errors
- Verify you're running scripts from the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure virtual environment is activated