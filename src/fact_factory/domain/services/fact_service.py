from __future__ import annotations

from fact_factory.domain.exceptions import NotFoundError
from fact_factory.domain.models import Fact
from fact_factory.domain.ports import EmbeddingProvider, FactRepository
from fact_factory.infrastructure.sqlite.repositories import new_id, utc_now


class FactService:
    def __init__(
        self,
        fact_repo: FactRepository,
        embedder: EmbeddingProvider,
    ) -> None:
        self._fact_repo = fact_repo
        self._embedder = embedder

    def add_fact(
        self,
        text: str,
        confidence: float = 1.0,
        tags: list[str] | None = None,
    ) -> Fact:
        embedding = self._embedder.embed(text)
        fact = Fact(
            id=new_id(),
            text=text,
            embedding=embedding,
            confidence=confidence,
            tags=tags or [],
            created_at=utc_now(),
        )
        self._fact_repo.add(fact)
        return fact

    def remove_fact(self, fact_id: str) -> None:
        if self._fact_repo.get_by_id(fact_id) is None:
            raise NotFoundError(f"Fact not found: {fact_id}")
        self._fact_repo.remove(fact_id)
