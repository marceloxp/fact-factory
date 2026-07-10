from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ResultType(StrEnum):
    FACT = "fact"
    GAP = "gap"


@dataclass(frozen=True)
class Config:
    embedding_model: str = "qwen3-embedding:0.6b"
    ollama_base_url: str = "http://localhost:11434"
    top_k: int = 10
    min_relevance_score: float = 0.65
    page_size: int = 20


@dataclass(frozen=True)
class Fact:
    id: str
    text: str
    embedding: bytes
    confidence: float
    tags: list[str]
    created_at: datetime


@dataclass(frozen=True)
class FactSummary:
    id: str
    text: str
    confidence: float
    tags: list[str]
    created_at: datetime


@dataclass(frozen=True)
class ScoredFact:
    fact: Fact
    score: float


@dataclass(frozen=True)
class Gap:
    id: str
    question: str
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_fact_id: str | None = None


@dataclass(frozen=True)
class QueryLog:
    id: str
    query_text: str
    created_at: datetime
    result_type: ResultType
    result_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QueryResult:
    facts: list[ScoredFact]
    gap: Gap | None = None


@dataclass(frozen=True)
class Stats:
    fact_count: int
    gap_count: int
    open_gaps: int
    resolved_gaps: int
    query_count: int
    answered_queries: int
    unanswered_queries: int
    top_queries: list[tuple[str, int]]
    top_gap_subjects: list[tuple[str, int]]
