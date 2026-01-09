"""
Main Orchestrator for Animal Encyclopedia AI Wrapper
Coordinates all components: routing, caching, context management, LLM calls
"""
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from config.settings import settings
from animal_encyclopedia.core.semantic_router import SemanticRouter, RoutingDecision
from animal_encyclopedia.core.anaphora_resolver import AnaphoraResolver
from animal_encyclopedia.core.context_manager import ContextManager
from animal_encyclopedia.core.prompts import format_prompt
from animal_encyclopedia.cache.semantic_cache import SemanticCache
from animal_encyclopedia.utils.vector_store import VectorStore

logger = logging.getLogger(__name__)


class AnimalEncyclopediaOrchestrator:
    """
    Main orchestrator for the Animal Encyclopedia AI Wrapper.
    Handles the complete pipeline from query to response.
    """

    def __init__(
        self,
        semantic_router: SemanticRouter,
        vector_store_cache: VectorStore,
        anchor_embeddings: Optional[np.ndarray] = None,
        negative_embeddings: Optional[np.ndarray] = None
    ):
        """
        Initialize the orchestrator.

        Args:
            semantic_router: Initialized semantic router
            vector_store_cache: Vector store for semantic cache
            anchor_embeddings: Anchor embeddings for routing
            negative_embeddings: Negative example embeddings
        """
        # Initialize OpenAI client for LLM calls
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

        # Initialize local embedding model (FREE)
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")

        # Components
        self.semantic_router = semantic_router
        self.anaphora_resolver = AnaphoraResolver()
        self.context_manager = ContextManager()
        self.semantic_cache = SemanticCache(vector_store_cache, use_redis=True)

        # Session storage (in production, use Redis or database)
        self.sessions: Dict[str, List[Tuple[str, str]]] = {}

        logger.info("AnimalEncyclopediaOrchestrator initialized")

    async def process_query(
        self,
        session_id: str,
        query: str,
        skip_cache: bool = False
    ) -> Dict:
        """
        Full pipeline for processing user query.

        Pipeline:
        1. Get or create session
        2. Generate embedding
        3. Semantic Routing (is it an animal query?)
        4. Anaphora Resolution (resolve pronouns)
        5. Semantic Cache Check (do we have a cached answer?)
        6. Context Preparation (prepare prompt efficiently)
        7. LLM Invocation (call OpenAI with optimized prompt)
        8. Cache Storage (save for future similar queries)

        Args:
            session_id: Session identifier for conversation history
            query: User query string
            skip_cache: Skip cache lookup (for testing)

        Returns:
            Response dictionary with answer and metadata
        """
        start_time = datetime.now()

        # Step 1: Get session history
        history = self.sessions.get(session_id, [])

        try:
            # Step 2: Generate embedding for the query
            query_embedding = await self._embed(query)

            # Step 3: Semantic Routing
            routing_decision = self.semantic_router.route(query_embedding)

            if routing_decision.decision == "REJECT":
                response = {
                    "session_id": session_id,
                    "query": {
                        "original": query,
                        "resolved": query,
                        "anaphora_resolved": False
                    },
                    "routing": {
                        "decision": "REJECT",
                        "confidence": routing_decision.confidence,
                        "reason": routing_decision.reason
                    },
                    "cache": {
                        "hit": False,
                        "similarity": 0.0
                    },
                    "response": {
                        "answer": "I specialize exclusively in animal-related questions. Please ask me about any creature in Kingdom Animalia.",
                        "source": "semantic_filter"
                    },
                    "metadata": {
                        "response_time_ms": self._get_elapsed_ms(start_time),
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return response

            # Step 4: Anaphora Resolution
            resolved_query = self.anaphora_resolver.resolve_query(query, history)

            # Step 5: Semantic Cache Check
            cache_result = None
            cache_similarity = 0.0

            if not skip_cache:
                cache_result, cache_similarity = await self.semantic_cache.get(
                    resolved_query,
                    query_embedding
                )

            if cache_result:
                response = {
                    "session_id": session_id,
                    "query": {
                        "original": query,
                        "resolved": resolved_query,
                        "anaphora_resolved": resolved_query != query
                    },
                    "routing": {
                        "decision": "ACCEPT",
                        "confidence": routing_decision.confidence,
                        "reason": routing_decision.reason
                    },
                    "cache": {
                        "hit": True,
                        "similarity": cache_similarity,
                        "original_query": cache_result.get("query")
                    },
                    "response": {
                        "answer": cache_result["response"]["answer"],
                        "source": "semantic_cache"
                    },
                    "metadata": {
                        "response_time_ms": self._get_elapsed_ms(start_time),
                        "timestamp": datetime.now().isoformat()
                    }
                }

                # Update session history
                self._update_session(session_id, query, cache_result["response"]["answer"])

                return response

            # Step 6: Context Preparation
            context_string = self.context_manager.prepare_context(history, resolved_query)

            # Step 7: LLM Invocation
            llm_response = await self._call_llm(context_string, resolved_query)

            # Step 8: Cache Storage
            await self.semantic_cache.set(
                resolved_query,
                query_embedding,
                {
                    "answer": llm_response["answer"],
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Update session history
            self._update_session(session_id, query, llm_response["answer"])

            # Build response
            response = {
                "session_id": session_id,
                "query": {
                    "original": query,
                    "resolved": resolved_query,
                    "anaphora_resolved": resolved_query != query
                },
                "routing": {
                    "decision": routing_decision.decision,
                    "confidence": routing_decision.confidence,
                    "reason": routing_decision.reason
                },
                "cache": {
                    "hit": False,
                    "similarity": 0.0
                },
                "response": {
                    "answer": llm_response["answer"],
                    "source": "llm",
                    "model": llm_response["model"],
                    "tokens": llm_response["tokens"]
                },
                "metadata": {
                    "response_time_ms": self._get_elapsed_ms(start_time),
                    "timestamp": datetime.now().isoformat()
                }
            }

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "session_id": session_id,
                "error": str(e),
                "metadata": {
                    "response_time_ms": self._get_elapsed_ms(start_time),
                    "timestamp": datetime.now().isoformat()
                }
            }

    async def _embed(self, text: str) -> np.ndarray:
        """Generate embedding for text using local sentence-transformers model."""
        # sentence-transformers is synchronous, but we wrap it in async for API consistency
        embedding = self.embedding_model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        return embedding.astype('float32')

    async def _call_llm(self, context: str, query: str) -> Dict:
        """Call LLM with formatted prompt."""
        prompt = format_prompt(context, query)

        response = await self.openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )

        return {
            "answer": response.choices[0].message.content,
            "model": response.model,
            "tokens": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            }
        }

    def _update_session(self, session_id: str, query: str, response: str):
        """Update session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append((query, response))

        # Keep only last N turns
        max_turns = settings.MAX_HISTORY_TURNS * 2  # Keep more for better context
        if len(self.sessions[session_id]) > max_turns:
            self.sessions[session_id] = self.sessions[session_id][-max_turns:]

    def _get_elapsed_ms(self, start_time: datetime) -> int:
        """Calculate elapsed time in milliseconds."""
        return int((datetime.now() - start_time).total_seconds() * 1000)

    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get formatted session history."""
        history = self.sessions.get(session_id, [])
        return self.context_manager.format_history_for_display(history)

    def clear_session(self, session_id: str):
        """Clear session history."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} cleared")

    def get_stats(self) -> Dict:
        """Get overall system statistics."""
        return {
            "router": self.semantic_router.get_statistics(),
            "cache": self.semantic_cache.get_stats(),
            "active_sessions": len(self.sessions)
        }
