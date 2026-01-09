"""
FastAPI dependencies for initializing and injecting components
"""
import numpy as np
import json
import os
import logging
from functools import lru_cache

from config.settings import settings
from animal_encyclopedia.core.orchestrator import AnimalEncyclopediaOrchestrator
from animal_encyclopedia.core.semantic_router import SemanticRouter
from animal_encyclopedia.utils.vector_store import VectorStore
from animal_encyclopedia.data.sample_anchors import get_sample_anchors

logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator = None


async def get_embedding_client():
    """Get OpenAI client for embeddings."""
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_embeddings(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    client = await get_embedding_client()

    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts
    )

    embeddings = [item.embedding for item in response.data]
    return np.array(embeddings)


@lru_cache()
def initialize_orchestrator() -> AnimalEncyclopediaOrchestrator:
    """
    Initialize the orchestrator with all components.
    This is called once on startup and cached.
    """
    global _orchestrator

    if _orchestrator is not None:
        return _orchestrator

    logger.info("Initializing Animal Encyclopedia Orchestrator...")

    # Get sample anchor queries (in production, load from database)
    anchor_queries, negative_queries = get_sample_anchors()

    logger.info(f"Loaded {len(anchor_queries)} anchor queries and {len(negative_queries)} negative examples")

    # Check if we have pre-computed embeddings
    embeddings_path = os.path.join(settings.DATA_DIR, "embeddings.npz")

    if os.path.exists(embeddings_path):
        logger.info("Loading pre-computed embeddings...")
        data = np.load(embeddings_path)
        anchor_embeddings = data['anchor_embeddings']
        negative_embeddings = data['negative_embeddings']
    else:
        logger.info("Embeddings not found. Please run 'python scripts/generate_embeddings.py' first.")
        logger.info("Using minimal sample embeddings for demo...")

        # For demo purposes, create dummy embeddings
        # In production, you MUST run the embedding generation script
        # Dimension must match embedding model: all-MiniLM-L6-v2 = 384
        anchor_embeddings = np.random.rand(len(anchor_queries), 384).astype('float32')
        negative_embeddings = np.random.rand(len(negative_queries), 384).astype('float32')

    # Initialize semantic router
    semantic_router = SemanticRouter(
        anchor_embeddings=anchor_embeddings,
        negative_embeddings=negative_embeddings
    )

    # Initialize vector store for cache
    # Dimension must match embedding model: all-MiniLM-L6-v2 = 384
    vector_store_cache = VectorStore(
        dimension=384,
        index_path=settings.VECTOR_DB_PATH
    )

    # Initialize orchestrator
    _orchestrator = AnimalEncyclopediaOrchestrator(
        semantic_router=semantic_router,
        vector_store_cache=vector_store_cache,
        anchor_embeddings=anchor_embeddings,
        negative_embeddings=negative_embeddings
    )

    logger.info("Orchestrator initialized successfully")

    return _orchestrator


def get_orchestrator() -> AnimalEncyclopediaOrchestrator:
    """
    FastAPI dependency to get the orchestrator instance.

    This is used in route handlers via Depends(get_orchestrator).
    """
    return initialize_orchestrator()
