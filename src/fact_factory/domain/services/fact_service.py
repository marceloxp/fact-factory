from __future__ import annotations

from fact_factory.domain.exceptions import NotFoundError, ValidationError
from fact_factory.domain.models import Fact, ReindexResult
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

    def add_facts(
        self,
        texts: list[str],
        confidence: float = 1.0,
        tags: list[str] | None = None,
    ) -> list[Fact]:
        if not texts:
            raise ValidationError("At least one fact text is required.")

        facts: list[Fact] = []
        tag_list = tags or []
        for text in texts:
            if not text.strip():
                raise ValidationError("Fact text cannot be empty.")
            embedding = self._embedder.embed(text)
            facts.append(
                Fact(
                    id=new_id(),
                    text=text,
                    embedding=embedding,
                    confidence=confidence,
                    tags=tag_list,
                    created_at=utc_now(),
                )
            )

        if len(facts) == 1:
            self._fact_repo.add(facts[0])
        else:
            self._fact_repo.add_many(facts)
        return facts

    def remove_fact(self, fact_id: str, *, force: bool = False) -> None:
        if not force and self._fact_repo.get_by_id(fact_id) is None:
            raise NotFoundError(f"Fact not found: {fact_id}")
        self._fact_repo.remove(fact_id, force=force)

    def reindex_facts(self, embedding_model: str) -> ReindexResult:
        facts = self._fact_repo.list_all_with_embeddings()
        for fact in facts:
            embedding = self._embedder.embed(fact.text)
            self._fact_repo.update_embedding(fact.id, embedding)
        return ReindexResult(
            reindexed=len(facts),
            embedding_model=embedding_model,
        )
