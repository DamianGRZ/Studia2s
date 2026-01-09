"""
FAISS Vector Store wrapper for embeddings storage and search
"""
import numpy as np
import faiss
import pickle
import os
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Wrapper around FAISS for efficient similarity search.
    """

    def __init__(self, dimension: int = 1536, index_path: Optional[str] = None):
        """
        Initialize vector store.

        Args:
            dimension: Embedding dimension (1536 for text-embedding-3-small)
            index_path: Path to save/load FAISS index
        """
        self.dimension = dimension
        self.index_path = index_path

        # Initialize FAISS index (using IndexFlatIP for cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)

        # Metadata storage (maps index position to query_id)
        self.id_to_idx = {}
        self.idx_to_id = {}
        self.next_idx = 0

        # Load existing index if available
        if index_path and os.path.exists(index_path):
            self.load(index_path)

        logger.info(f"VectorStore initialized with dimension={dimension}")

    def add(self, query_id: str, embedding: np.ndarray):
        """
        Add embedding to the index.

        Args:
            query_id: Unique identifier for the query
            embedding: Embedding vector (will be normalized)
        """
        # Normalize embedding for cosine similarity
        embedding = embedding.astype('float32')
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

        # Reshape to (1, dimension)
        embedding = embedding.reshape(1, -1)

        # Add to FAISS index
        self.index.add(embedding)

        # Store metadata
        idx = self.next_idx
        self.id_to_idx[query_id] = idx
        self.idx_to_id[idx] = query_id
        self.next_idx += 1

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (query_id, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []

        # Normalize query embedding
        query_embedding = query_embedding.astype('float32')
        query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        query_embedding = query_embedding.reshape(1, -1)

        # Search
        similarities, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        # Filter by threshold and convert to query_ids
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity >= threshold:
                query_id = self.idx_to_id.get(int(idx))
                if query_id:
                    results.append((query_id, float(similarity)))

        return results

    def save(self, path: str):
        """
        Save index and metadata to disk.

        Args:
            path: Directory path to save files
        """
        os.makedirs(path, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))

        # Save metadata
        metadata = {
            "id_to_idx": self.id_to_idx,
            "idx_to_id": self.idx_to_id,
            "next_idx": self.next_idx
        }
        with open(os.path.join(path, "metadata.pkl"), "wb") as f:
            pickle.dump(metadata, f)

        logger.info(f"VectorStore saved to {path}")

    def load(self, path: str):
        """
        Load index and metadata from disk.

        Args:
            path: Directory path to load from
        """
        # Load FAISS index
        index_file = os.path.join(path, "index.faiss")
        if os.path.exists(index_file):
            self.index = faiss.read_index(index_file)

        # Load metadata
        metadata_file = os.path.join(path, "metadata.pkl")
        if os.path.exists(metadata_file):
            with open(metadata_file, "rb") as f:
                metadata = pickle.load(f)
                self.id_to_idx = metadata["id_to_idx"]
                self.idx_to_id = metadata["idx_to_id"]
                self.next_idx = metadata["next_idx"]

        logger.info(f"VectorStore loaded from {path} with {self.index.ntotal} vectors")

    def size(self) -> int:
        """Get number of vectors in the store."""
        return self.index.ntotal

    def clear(self):
        """Clear all vectors from the store."""
        self.index.reset()
        self.id_to_idx.clear()
        self.idx_to_id.clear()
        self.next_idx = 0
