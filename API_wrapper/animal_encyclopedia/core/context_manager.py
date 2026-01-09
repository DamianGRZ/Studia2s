"""
Context Management System
Manages conversation context for efficient token usage
"""
from typing import List, Tuple
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context to prepend to LLM calls.
    Optimizes for token efficiency while maintaining coherence.
    """

    def __init__(
        self,
        max_context_tokens: int = None,
        max_history_turns: int = None
    ):
        """
        Initialize context manager.

        Args:
            max_context_tokens: Maximum tokens to use for context
            max_history_turns: Maximum conversation turns to include
        """
        self.max_context_tokens = max_context_tokens or settings.MAX_CONTEXT_TOKENS
        self.max_history_turns = max_history_turns or settings.MAX_HISTORY_TURNS

    def prepare_context(
        self,
        conversation_history: List[Tuple[str, str]],
        current_query: str
    ) -> str:
        """
        Creates optimized context string for LLM.

        Strategy:
        1. Include only last N turns
        2. Compress older turns to entity mentions only
        3. Always include full last exchange for coherence

        Args:
            conversation_history: List of (user_query, assistant_response) tuples
            current_query: Current user query

        Returns:
            Formatted context string
        """
        if not conversation_history:
            return "No previous conversation."

        context_parts = []

        # If history is long, create a summary of older conversations
        if len(conversation_history) > self.max_history_turns:
            summary = self._create_conversation_summary(
                conversation_history[:-self.max_history_turns]
            )
            if summary:
                context_parts.append(f"Earlier topics: {summary}\n")

        # Add recent full exchanges
        recent_history = conversation_history[-self.max_history_turns:]
        for user_msg, assistant_msg in recent_history:
            context_parts.append(f"User: {user_msg}")

            # Truncate long assistant responses
            truncated_response = self._truncate_response(assistant_msg, max_tokens=150)
            context_parts.append(f"Assistant: {truncated_response}\n")

        # Assemble context
        context_string = "\n".join(context_parts)

        # Token count check (rough estimation: 1 token ≈ 4 chars)
        estimated_tokens = len(context_string) // 4
        if estimated_tokens > self.max_context_tokens:
            logger.warning(
                f"Context exceeds token limit ({estimated_tokens} > {self.max_context_tokens}), truncating"
            )
            context_string = self._truncate_to_token_limit(
                context_string,
                self.max_context_tokens
            )

        return context_string

    def _create_conversation_summary(
        self,
        old_history: List[Tuple[str, str]]
    ) -> str:
        """
        Compress old conversation turns to animal names only.

        Args:
            old_history: Older conversation turns

        Returns:
            Comma-separated list of animals discussed
        """
        animals_mentioned = []

        for user_msg, assistant_msg in old_history:
            # Simple extraction of capitalized words (animal names)
            import re
            words = re.findall(r'\b[A-Z][a-z]+\b', user_msg + " " + assistant_msg)

            # Filter common non-animal words
            stopwords = {'The', 'This', 'That', 'What', 'How', 'Why', 'Scientific'}
            animals = [w for w in words if w not in stopwords]

            animals_mentioned.extend(animals)

        # Keep only unique animals, preserve order
        unique_animals = list(dict.fromkeys(animals_mentioned))

        return ", ".join(unique_animals[:5])  # Top 5 animals

    def _truncate_response(self, text: str, max_tokens: int) -> str:
        """
        Intelligently truncate assistant response to preserve key info.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens to keep

        Returns:
            Truncated text
        """
        # Estimate max characters (1 token ≈ 4 chars)
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return text

        # Try to truncate at sentence boundary
        sentences = text.split(". ")
        truncated = []
        char_count = 0

        for sentence in sentences:
            sentence_len = len(sentence) + 2  # +2 for ". "
            if char_count + sentence_len > max_chars:
                break
            truncated.append(sentence)
            char_count += sentence_len

        result = ". ".join(truncated)
        if len(truncated) < len(sentences):
            result += "..."

        return result

    def _truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        return text[:max_chars] + "..."

    def format_history_for_display(
        self,
        conversation_history: List[Tuple[str, str]]
    ) -> List[dict]:
        """
        Format conversation history for API responses.

        Args:
            conversation_history: List of (user_query, assistant_response) tuples

        Returns:
            List of formatted message dictionaries
        """
        messages = []
        for user_msg, assistant_msg in conversation_history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})

        return messages
