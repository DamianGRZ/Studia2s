#!/usr/bin/env python
"""
Generate embeddings for anchor datasets and save to disk.

This script:
1. Loads positive and negative anchor queries from sample_anchors.py
2. Generates embeddings using sentence-transformers (FREE local model)
3. Saves embeddings to data/embeddings.npz for use by the application

Usage:
    python scripts/generate_embeddings.py [--extended]

Options:
    --extended  Use extended anchor set with more examples (recommended for production)
"""
import os
import sys
import argparse
import numpy as np
from pathlib import Path

# Add parent directory to path to import from animal_encyclopedia
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from config.settings import settings
from animal_encyclopedia.data.sample_anchors import get_sample_anchors, get_extended_anchors


def generate_embeddings_batch(
    model: SentenceTransformer,
    texts: list[str],
    batch_size: int = 32
) -> np.ndarray:
    """
    Generate embeddings for a list of texts in batches.

    Args:
        model: SentenceTransformer model instance
        texts: List of text strings to embed
        batch_size: Number of texts to process per batch

    Returns:
        numpy array of embeddings (n_texts, embedding_dim)
    """
    all_embeddings = []
    total = len(texts)

    print(f"Generating embeddings for {total} texts in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")

        try:
            # Generate embeddings for batch
            batch_embeddings = model.encode(
                batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )
            all_embeddings.append(batch_embeddings)

            print(f"  [OK] Batch {batch_num} complete")

        except Exception as e:
            print(f"  [ERROR] Error processing batch {batch_num}: {e}")
            raise

    embeddings_array = np.vstack(all_embeddings).astype('float32')
    print(f"[OK] Generated {len(embeddings_array)} embeddings of dimension {embeddings_array.shape[1]}")

    return embeddings_array


def main(use_extended: bool = False):
    """
    Main function to generate and save embeddings.

    Args:
        use_extended: Whether to use extended anchor set
    """
    print("=" * 60)
    print("Animal Encyclopedia - Embedding Generation Script")
    print("=" * 60)
    print()

    print(f"Configuration:")
    print(f"  Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"  Anchor Set: {'Extended' if use_extended else 'Standard'}")
    print(f"  Output Directory: {settings.DATA_DIR}")
    print()

    # Load embedding model
    print(f"Loading embedding model '{settings.EMBEDDING_MODEL}'...")
    print("(First run will download model ~80MB, subsequent runs are instant)")
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    print("[OK] Model loaded successfully")
    print()

    # Load anchor queries
    print("Loading anchor queries...")
    if use_extended:
        positive_queries, negative_queries = get_extended_anchors()
    else:
        positive_queries, negative_queries = get_sample_anchors()

    print(f"  Positive (animal) queries: {len(positive_queries)}")
    print(f"  Negative (non-animal) queries: {len(negative_queries)}")
    print()

    # Generate embeddings
    print("Generating positive anchor embeddings...")
    positive_embeddings = generate_embeddings_batch(model, positive_queries)
    print()

    print("Generating negative anchor embeddings...")
    negative_embeddings = generate_embeddings_batch(model, negative_queries)
    print()

    # Create data directory if it doesn't exist
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    # Save to npz file
    output_path = os.path.join(settings.DATA_DIR, "embeddings.npz")
    print(f"Saving embeddings to {output_path}...")

    np.savez(
        output_path,
        anchor_embeddings=positive_embeddings,
        negative_embeddings=negative_embeddings,
        positive_queries=positive_queries,
        negative_queries=negative_queries
    )

    print("[OK] Embeddings saved successfully!")
    print()

    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Total queries processed: {len(positive_queries) + len(negative_queries)}")
    print(f"Embedding dimension: {positive_embeddings.shape[1]}")
    print(f"Cost: $0.00 (FREE local model)")
    print(f"Output file: {output_path}")
    print()
    print("[OK] Setup complete! You can now run the application.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate embeddings for semantic routing anchor datasets"
    )
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Use extended anchor set with more examples (recommended for production)"
    )

    args = parser.parse_args()

    # Run main function
    main(use_extended=args.extended)
