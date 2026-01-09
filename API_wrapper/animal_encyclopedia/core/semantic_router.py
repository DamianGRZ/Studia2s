"""
Semantic Router for query classification
Determines if queries are about animals using cosine similarity
"""
import numpy as np
from typing import Dict, Literal
from dataclasses import dataclass
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of semantic routing"""
    decision: Literal["ACCEPT", "REJECT", "AMBIGUOUS"]
    confidence: float
    max_positive_score: float
    max_negative_score: float
    reason: str


class SemanticRouter:
    """
    Routes queries based on semantic similarity to anchor datasets.
    Uses cosine similarity to determine if query is about animals.
    """

    def __init__(self, anchor_embeddings: np.ndarray, negative_embeddings: np.ndarray):
        """
        Initialize semantic router with pre-computed embeddings.

        Args:
            anchor_embeddings: Array of embeddings for animal queries
            negative_embeddings: Array of embeddings for non-animal queries
        """
        self.anchor_embeddings = self._normalize_embeddings(anchor_embeddings)
        self.negative_embeddings = self._normalize_embeddings(negative_embeddings)

        self.accept_threshold = settings.ACCEPT_THRESHOLD
        self.reject_threshold = settings.REJECT_THRESHOLD
        self.negative_check_threshold = settings.NEGATIVE_CHECK_THRESHOLD

        logger.info(
            f"SemanticRouter initialized with {len(anchor_embeddings)} positive "
            f"and {len(negative_embeddings)} negative anchors"
        )

    @staticmethod
    def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit vectors for cosine similarity."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / (norms + 1e-8)

    def compute_max_similarity(
        self, query_embedding: np.ndarray, anchor_set: np.ndarray
    ) -> float:
        """Compute maximum cosine similarity between query and anchor set."""
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        similarities = np.dot(anchor_set, query_norm)
        return float(np.max(similarities))

    def route(self, query_embedding: np.ndarray) -> RoutingDecision:
        """
        Route a query based on semantic similarity.

        Args:
            query_embedding: Embedding vector for the query

        Returns:
            RoutingDecision with classification result
        """
        max_positive = self.compute_max_similarity(query_embedding, self.anchor_embeddings)
        max_negative = self.compute_max_similarity(query_embedding, self.negative_embeddings)

        # REJECT if too similar to negative examples OR too dissimilar from animal queries
        if max_negative > self.negative_check_threshold or max_positive < self.reject_threshold:
            return RoutingDecision(
                decision="REJECT",
                confidence=max(max_negative, 1.0 - max_positive),
                max_positive_score=max_positive,
                max_negative_score=max_negative,
                reason=f"Not an animal query (pos: {max_positive:.3f}, neg: {max_negative:.3f})"
            )

        # ACCEPT if clearly similar to animal queries
        if max_positive >= self.accept_threshold:
            return RoutingDecision(
                decision="ACCEPT",
                confidence=max_positive,
                max_positive_score=max_positive,
                max_negative_score=max_negative,
                reason=f"Animal query detected ({max_positive:.3f} >= {self.accept_threshold})"
            )

        # AMBIGUOUS otherwise
        return RoutingDecision(
            decision="AMBIGUOUS",
            confidence=max_positive,
            max_positive_score=max_positive,
            max_negative_score=max_negative,
            reason=f"Ambiguous query (pos: {max_positive:.3f}, neg: {max_negative:.3f})"
        )

    def get_statistics(self) -> Dict:
        """Get router statistics."""
        return {
            "num_positive_anchors": len(self.anchor_embeddings),
            "num_negative_anchors": len(self.negative_embeddings),
            "thresholds": {
                "accept": self.accept_threshold,
                "reject": self.reject_threshold,
                "negative_check": self.negative_check_threshold
            }
        }
