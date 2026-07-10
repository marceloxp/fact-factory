from __future__ import annotations

import re

from fact_factory.domain.models import Fact, ScoredFact
from fact_factory.infrastructure.ollama.client import cosine_similarity

EN_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "must", "shall", "can", "this", "that", "these", "those",
    "it", "its", "as", "if", "how", "what", "when", "where", "which", "who",
    "whom", "why", "into", "about", "over", "under", "between", "through",
}

PT_STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos",
    "das", "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob",
    "sobre", "entre", "e", "ou", "mas", "se", "que", "como", "quando", "onde",
    "qual", "quais", "quem", "porque", "porquê", "é", "são", "foi", "foram",
    "ser", "estar", "tem", "têm", "ter", "há", "ao", "aos", "à", "às", "pelo",
    "pela", "pelos", "pelas", "isso", "isto", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas", "um", "uma", "meu", "minha",
}

STOPWORDS = EN_STOPWORDS | PT_STOPWORDS
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
MAX_KEYWORD_BOOST = 0.15


class HybridReranker:
    def rank(
        self,
        question: str,
        query_embedding: bytes,
        facts: list[Fact],
        top_k: int,
    ) -> list[ScoredFact]:
        candidates: list[ScoredFact] = []
        for fact in facts:
            cosine_score = cosine_similarity(query_embedding, fact.embedding)
            keyword_boost = _keyword_boost(question, fact.text)
            final_score = cosine_score + keyword_boost
            candidates.append(ScoredFact(fact=fact, score=final_score))

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[:top_k]


def _keyword_boost(question: str, fact_text: str) -> float:
    question_tokens = _significant_tokens(question)
    if not question_tokens:
        return 0.0

    fact_tokens = set(_significant_tokens(fact_text))
    overlap = sum(1 for token in question_tokens if token in fact_tokens)
    ratio = overlap / len(question_tokens)
    return ratio * MAX_KEYWORD_BOOST


def _significant_tokens(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]
