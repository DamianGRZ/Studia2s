"""
Anaphora Resolution System
Resolves pronouns and demonstratives in follow-up questions
"""
import re
from typing import List, Tuple, Optional
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class AnaphoraResolver:
    """
    Resolves pronouns and demonstratives like "it", "they", "that animal"
    by looking back at conversation history.
    """

    ANAPHORIC_PATTERNS = [
        r"\bit\b", r"\bits\b", r"\bthey\b", r"\bthem\b", r"\btheir\b",
        r"\bhe\b", r"\bshe\b", r"\bhim\b", r"\bher\b",
        r"\bthis animal\b", r"\bthat animal\b", r"\bthese animals\b", r"\bthose animals\b",
        r"\bthis species\b", r"\bthat species\b", r"\bthe animal\b", r"\bthe species\b"
    ]

    # Common animal name patterns
    ANIMAL_PATTERN = re.compile(
        r'\b([A-Z][a-z]+(?:\s+[a-z]+)?(?:\s+[a-z]+)?)\b'  # Capitalized words (Red Fox, African Elephant)
    )

    def __init__(self, context_window: int = None):
        """
        Initialize anaphora resolver.

        Args:
            context_window: Number of previous exchanges to consider
        """
        self.context_window = context_window or settings.CONTEXT_WINDOW
        self.entity_memory: List[str] = []

        # Compile patterns for efficiency
        self.anaphora_regex = re.compile(
            '|'.join(self.ANAPHORIC_PATTERNS),
            re.IGNORECASE
        )

    def resolve_query(
        self,
        current_query: str,
        conversation_history: List[Tuple[str, str]]
    ) -> str:
        """
        Expands anaphoric references using conversation context.

        Args:
            current_query: User's current input
            conversation_history: List of (user_query, assistant_response) tuples

        Returns:
            resolved_query: Query with pronouns replaced by entity references
        """
        # Check if query contains anaphoric expressions
        if not self.anaphora_regex.search(current_query):
            return current_query

        # Extract last mentioned animal from history
        last_animal = self._extract_last_entity(conversation_history)

        if not last_animal:
            logger.debug("Could not resolve anaphora - no previous animal found")
            return current_query

        # Replace anaphoric terms with the resolved entity
        resolved = current_query

        # Replace patterns in order of specificity (most specific first)
        replacements = [
            (r"\bthis animal\b", last_animal),
            (r"\bthat animal\b", last_animal),
            (r"\bthese animals\b", f"{last_animal}s"),
            (r"\bthose animals\b", f"{last_animal}s"),
            (r"\bthis species\b", f"the {last_animal}"),
            (r"\bthat species\b", f"the {last_animal}"),
            (r"\bthe animal\b", f"the {last_animal}"),
            (r"\bthe species\b", f"the {last_animal}"),
            (r"\bit\b", f"the {last_animal}"),
            (r"\bits\b", f"the {last_animal}'s"),
            (r"\bthey\b", f"{last_animal}s"),
            (r"\bthem\b", f"{last_animal}s"),
            (r"\btheir\b", f"{last_animal}'s"),
        ]

        for pattern, replacement in replacements:
            resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)

        if resolved != current_query:
            logger.info(f"Resolved anaphora: '{current_query}' -> '{resolved}'")

        return resolved

    def _extract_last_entity(
        self,
        history: List[Tuple[str, str]]
    ) -> Optional[str]:
        """
        Extracts the most recently mentioned animal from conversation.

        Args:
            history: Conversation history

        Returns:
            Animal name or None
        """
        # Look through last N exchanges (most recent first)
        for user_msg, assistant_msg in reversed(history[-self.context_window:]):
            # Extract from both user query and assistant response
            combined_text = user_msg + " " + assistant_msg

            # Look for italic scientific names first (*Genus species*)
            scientific_names = re.findall(r'\*([A-Z][a-z]+ [a-z]+)\*', combined_text)
            if scientific_names:
                # Extract genus name as the animal reference
                return scientific_names[0].split()[0].lower()

            # Look for capitalized animal names
            animals = self._extract_animal_names(combined_text)
            if animals:
                return animals[0].lower()

        return None

    def _extract_animal_names(self, text: str) -> List[str]:
        """
        Extract potential animal names from text.

        This is a simplified version. In production, use:
        - spaCy NER with custom animal entity training
        - Lookup against taxonomy database
        - NLTK with custom gazetteers

        Args:
            text: Text to extract from

        Returns:
            List of potential animal names
        """
        # Find capitalized phrases (potential animal names)
        matches = self.ANIMAL_PATTERN.findall(text)

        # Filter out common false positives
        stopwords = {
            'The', 'This', 'That', 'These', 'Those', 'What', 'How', 'Why',
            'When', 'Where', 'Which', 'Kingdom', 'Animalia', 'Scientific',
            'Classification', 'Related', 'Topics', 'Primary', 'Answer',
            'Details', 'Context', 'Additional'
        }

        animals = [
            match for match in matches
            if match not in stopwords and len(match) > 2
        ]

        return animals[:3]  # Return top 3 candidates
