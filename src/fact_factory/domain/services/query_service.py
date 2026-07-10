from __future__ import annotations

from fact_factory.domain.models import Config, Gap, QueryLog, QueryResult, ResultType
from fact_factory.domain.relevance import RelevanceLevel
from fact_factory.domain.ports import (
    EmbeddingProvider,
    FactRepository,
    GapRepository,
    QueryLogRepository,
)
from fact_factory.infrastructure.sqlite.repositories import new_id, utc_now
from fact_factory.reranking.hybrid import HybridReranker


class QueryService:
    def __init__(
        self,
        config: Config,
        fact_repo: FactRepository,
        gap_repo: GapRepository,
        query_log_repo: QueryLogRepository,
        embedder: EmbeddingProvider,
        reranker: HybridReranker | None = None,
    ) -> None:
        self._config = config
        self._fact_repo = fact_repo
        self._gap_repo = gap_repo
        self._query_log_repo = query_log_repo
        self._embedder = embedder
        self._reranker = reranker or HybridReranker()

    def query(self, question: str) -> QueryResult:
        query_embedding = self._embedder.embed(question)
        facts = self._fact_repo.list_all_with_embeddings()

        if not facts:
            gap = self._create_gap(question)
            self._log_query(question, ResultType.GAP, [gap.id])
            return QueryResult(facts=[], gap=gap)

        ranked = self._reranker.rank(
            question=question,
            query_embedding=query_embedding,
            facts=facts,
            top_k=self._config.top_k,
        )
        relevant = [
            item for item in ranked
            if item.relevance is not RelevanceLevel.NONE
        ]

        if relevant:
            self._log_query(
                question,
                ResultType.FACT,
                [item.fact.id for item in relevant],
            )
            return QueryResult(facts=relevant)

        gap = self._create_gap(question)
        self._log_query(question, ResultType.GAP, [gap.id])
        return QueryResult(facts=[], gap=gap)

    def _create_gap(self, question: str) -> Gap:
        gap = Gap(
            id=new_id(),
            question=question,
            created_at=utc_now(),
        )
        self._gap_repo.add(gap)
        return gap

    def _log_query(
        self,
        question: str,
        result_type: ResultType,
        result_ids: list[str],
    ) -> None:
        self._query_log_repo.add(
            QueryLog(
                id=new_id(),
                query_text=question,
                created_at=utc_now(),
                result_type=result_type,
                result_ids=result_ids,
            )
        )
