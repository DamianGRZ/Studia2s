#!/usr/bin/env python
"""
Check if the Animal Encyclopedia system is properly configured.

This script verifies:
1. Environment variables are set
2. Required embeddings file exists
3. Dependencies are installed
4. Redis connection (optional)
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        print("✓ .env file exists")
        return True
    else:
        print("✗ .env file not found")
        print("  → Copy .env.example to .env and configure it")
        return False


def check_openai_key():
    """Check if OpenAI API key is configured."""
    try:
        from config.settings import settings
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
            print("✓ OpenAI API key is configured")
            return True
        else:
            print("✗ OpenAI API key not configured")
            print("  → Set OPENAI_API_KEY in .env file")
            return False
    except Exception as e:
        print(f"✗ Error loading settings: {e}")
        return False


def check_embeddings():
    """Check if embeddings file exists."""
    try:
        from config.settings import settings
        import numpy as np

        embeddings_path = os.path.join(settings.DATA_DIR, "embeddings.npz")

        if os.path.exists(embeddings_path):
            # Try to load and verify
            data = np.load(embeddings_path)
            if 'anchor_embeddings' in data and 'negative_embeddings' in data:
                anchor_count = len(data['anchor_embeddings'])
                negative_count = len(data['negative_embeddings'])
                print(f"✓ Embeddings file exists ({anchor_count} positive, {negative_count} negative)")
                return True
            else:
                print("✗ Embeddings file is corrupted (missing required arrays)")
                return False
        else:
            print("✗ Embeddings file not found")
            print("  → Run: python scripts/generate_embeddings.py")
            return False
    except Exception as e:
        print(f"✗ Error checking embeddings: {e}")
        return False


def check_dependencies():
    """Check if key dependencies are installed."""
    required_packages = [
        'fastapi',
        'openai',
        'faiss',
        'numpy',
        'redis',
        'spacy'
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} not installed")
            all_installed = False

    if not all_installed:
        print("  → Run: pip install -r requirements.txt")

    # Check spaCy model
    try:
        import spacy
        try:
            spacy.load("en_core_web_sm")
            print("✓ spaCy model 'en_core_web_sm' installed")
        except OSError:
            print("✗ spaCy model 'en_core_web_sm' not installed")
            print("  → Run: python -m spacy download en_core_web_sm")
            all_installed = False
    except ImportError:
        pass

    return all_installed


def check_redis():
    """Check if Redis is available (optional)."""
    try:
        import redis
        from config.settings import settings

        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=2
        )
        client.ping()
        print("✓ Redis connection successful")
        return True
    except Exception as e:
        print("⚠ Redis not available (will use in-memory cache)")
        print(f"  Note: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Animal Encyclopedia - Setup Check")
    print("=" * 60)
    print()

    checks = {
        "Environment file": check_env_file(),
        "OpenAI API key": check_openai_key(),
        "Dependencies": check_dependencies(),
        "Embeddings": check_embeddings(),
        "Redis (optional)": check_redis()
    }

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    required_checks = ["Environment file", "OpenAI API key", "Dependencies", "Embeddings"]
    required_passed = all(checks[k] for k in required_checks)

    if required_passed:
        print("✓ All required checks passed!")
        print()
        print("You can now start the application:")
        print("  python animal_encyclopedia/api/app.py")
        print()
        print("Or use uvicorn:")
        print("  uvicorn animal_encyclopedia.api.app:app --reload")
    else:
        print("✗ Some required checks failed")
        print()
        print("Please fix the issues above before running the application.")

    print()


if __name__ == "__main__":
    main()
