from __future__ import annotations

from datetime import datetime

from fact_factory.domain.models import (
    ClearResult,
    Fact,
    FactSummary,
    Gap,
    QueryResult,
    ReindexResult,
    ScoredFact,
    Stats,
)


def fact_dict(fact: Fact | FactSummary) -> dict:
    return {
        "id": fact.id,
        "text": fact.text,
        "confidence": fact.confidence,
        "tags": fact.tags,
        "created_at": _iso_datetime(fact.created_at),
    }


def scored_fact_dict(item: ScoredFact) -> dict:
    payload = fact_dict(item.fact)
    payload["score"] = round(item.score, 6)
    return payload


def gap_dict(gap: Gap) -> dict:
    return {
        "id": gap.id,
        "question": gap.question,
        "created_at": _iso_datetime(gap.created_at),
        "resolved_at": _iso_datetime(gap.resolved_at) if gap.resolved_at else None,
        "resolved_fact_id": gap.resolved_fact_id,
    }


def query_result_dict(result: QueryResult) -> dict:
    return {
        "facts": [scored_fact_dict(item) for item in result.facts],
        "gap": gap_dict(result.gap) if result.gap else None,
    }


def fact_page_dict(
    facts: list[FactSummary],
    page: int,
    page_size: int,
    total: int,
) -> dict:
    pages = (total + page_size - 1) // page_size if total else 1
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
        "facts": [fact_dict(fact) for fact in facts],
    }


def reindex_result_dict(result: ReindexResult) -> dict:
    return {
        "reindexed": result.reindexed,
        "embedding_model": result.embedding_model,
    }


def clear_result_dict(result: ClearResult) -> dict:
    return {
        "facts_removed": result.facts_removed,
        "gaps_removed": result.gaps_removed,
        "query_logs_removed": result.query_logs_removed,
    }


def stats_dict(stats: Stats) -> dict:
    return {
        "fact_count": stats.fact_count,
        "gap_count": stats.gap_count,
        "open_gaps": stats.open_gaps,
        "resolved_gaps": stats.resolved_gaps,
        "query_count": stats.query_count,
        "answered_queries": stats.answered_queries,
        "unanswered_queries": stats.unanswered_queries,
        "top_queries": [
            {"subject": subject, "count": count}
            for subject, count in stats.top_queries
        ],
        "top_gap_subjects": [
            {"subject": subject, "count": count}
            for subject, count in stats.top_gap_subjects
        ],
    }


def _iso_datetime(value: datetime) -> str:
    return value.isoformat()
