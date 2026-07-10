from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fact_factory.domain.exceptions import ConflictError, NotFoundError
from fact_factory.domain.models import ClearResult, Fact, FactSummary, Gap, QueryLog, ResultType, Stats
from fact_factory.infrastructure.config import db_path, normalize_query_text
from fact_factory.infrastructure.sqlite.schema import initialize_schema


class SqliteConnection:
    def __init__(self, instance_dir: Path) -> None:
        self._db_path = db_path(instance_dir)
        self._ensure_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self.connect() as connection:
            initialize_schema(connection)
            connection.commit()


class SqliteFactRepository:
    def __init__(self, connection_factory: SqliteConnection) -> None:
        self._connection_factory = connection_factory

    def add(self, fact: Fact) -> None:
        with self._connection_factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO facts (id, text, embedding, confidence, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.id,
                    fact.text,
                    fact.embedding,
                    fact.confidence,
                    json.dumps(fact.tags),
                    _format_datetime(fact.created_at),
                ),
            )
            connection.commit()

    def get_by_id(self, fact_id: str) -> Fact | None:
        with self._connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT * FROM facts WHERE id = ?",
                (fact_id,),
            ).fetchone()
        return _row_to_fact(row) if row else None

    def list_all_with_embeddings(self) -> list[Fact]:
        with self._connection_factory.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM facts ORDER BY created_at DESC"
            ).fetchall()
        return [_row_to_fact(row) for row in rows]

    def list_page(self, page: int, page_size: int) -> tuple[list[FactSummary], int]:
        offset = max(page - 1, 0) * page_size
        with self._connection_factory.connect() as connection:
            total = connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            rows = connection.execute(
                """
                SELECT id, text, confidence, tags, created_at
                FROM facts
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset),
            ).fetchall()
        return [_row_to_summary(row) for row in rows], int(total)

    def search(self, term: str, page: int, page_size: int) -> tuple[list[FactSummary], int]:
        offset = max(page - 1, 0) * page_size
        pattern = f"%{term}%"
        with self._connection_factory.connect() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM facts WHERE text LIKE ? COLLATE NOCASE",
                (pattern,),
            ).fetchone()[0]
            rows = connection.execute(
                """
                SELECT id, text, confidence, tags, created_at
                FROM facts
                WHERE text LIKE ? COLLATE NOCASE
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (pattern, page_size, offset),
            ).fetchall()
        return [_row_to_summary(row) for row in rows], int(total)

    def count(self) -> int:
        with self._connection_factory.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0])

    def remove(self, fact_id: str) -> None:
        with self._connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT id FROM facts WHERE id = ?",
                (fact_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Fact not found: {fact_id}")

            connection.execute(
                "UPDATE gaps SET resolved_fact_id = NULL WHERE resolved_fact_id = ?",
                (fact_id,),
            )
            connection.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
            connection.commit()

    def update_embedding(self, fact_id: str, embedding: bytes) -> None:
        with self._connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT id FROM facts WHERE id = ?",
                (fact_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Fact not found: {fact_id}")

            connection.execute(
                "UPDATE facts SET embedding = ? WHERE id = ?",
                (embedding, fact_id),
            )
            connection.commit()


class SqliteGapRepository:
    def __init__(self, connection_factory: SqliteConnection) -> None:
        self._connection_factory = connection_factory

    def add(self, gap: Gap) -> None:
        with self._connection_factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO gaps (id, question, created_at, resolved_at, resolved_fact_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    gap.id,
                    gap.question,
                    _format_datetime(gap.created_at),
                    _format_datetime(gap.resolved_at) if gap.resolved_at else None,
                    gap.resolved_fact_id,
                ),
            )
            connection.commit()

    def get_by_id(self, gap_id: str) -> Gap | None:
        with self._connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT * FROM gaps WHERE id = ?",
                (gap_id,),
            ).fetchone()
        return _row_to_gap(row) if row else None

    def list_open(self) -> list[Gap]:
        with self._connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM gaps
                WHERE resolved_at IS NULL
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [_row_to_gap(row) for row in rows]

    def resolve(self, gap_id: str, resolved_at: datetime, resolved_fact_id: str) -> None:
        with self._connection_factory.connect() as connection:
            updated = connection.execute(
                """
                UPDATE gaps
                SET resolved_at = ?, resolved_fact_id = ?
                WHERE id = ? AND resolved_at IS NULL
                """,
                (_format_datetime(resolved_at), resolved_fact_id, gap_id),
            ).rowcount
            connection.commit()
        if updated == 0:
            gap = self.get_by_id(gap_id)
            if gap is None:
                raise NotFoundError(f"Gap not found: {gap_id}")
            raise ConflictError(f"Gap is already resolved: {gap_id}")

    def remove(self, gap_id: str) -> None:
        with self._connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT resolved_at FROM gaps WHERE id = ?",
                (gap_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Gap not found: {gap_id}")
            if row["resolved_at"] is not None:
                raise ConflictError(f"Cannot remove a resolved gap: {gap_id}")
            connection.execute("DELETE FROM gaps WHERE id = ?", (gap_id,))
            connection.commit()

    def count(self) -> int:
        with self._connection_factory.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM gaps").fetchone()[0])

    def count_open(self) -> int:
        with self._connection_factory.connect() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM gaps WHERE resolved_at IS NULL"
                ).fetchone()[0]
            )

    def count_resolved(self) -> int:
        with self._connection_factory.connect() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM gaps WHERE resolved_at IS NOT NULL"
                ).fetchone()[0]
            )

    def top_open_subjects(self, limit: int) -> list[tuple[str, int]]:
        with self._connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT question, COUNT(*) AS total
                FROM gaps
                WHERE resolved_at IS NULL
                GROUP BY question
                ORDER BY total DESC, question ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [(row["question"], int(row["total"])) for row in rows]


class SqliteQueryLogRepository:
    def __init__(self, connection_factory: SqliteConnection) -> None:
        self._connection_factory = connection_factory

    def add(self, log: QueryLog) -> None:
        with self._connection_factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO query_logs (id, query_text, created_at, result_type, result_ids)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.query_text,
                    _format_datetime(log.created_at),
                    log.result_type.value,
                    json.dumps(log.result_ids),
                ),
            )
            connection.commit()

    def count(self) -> int:
        with self._connection_factory.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM query_logs").fetchone()[0])

    def count_by_result_type(self, result_type: ResultType) -> int:
        with self._connection_factory.connect() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM query_logs WHERE result_type = ?",
                    (result_type.value,),
                ).fetchone()[0]
            )

    def top_queries(self, limit: int) -> list[tuple[str, int]]:
        with self._connection_factory.connect() as connection:
            rows = connection.execute(
                "SELECT query_text FROM query_logs"
            ).fetchall()

        counts: dict[str, int] = {}
        display: dict[str, str] = {}
        for row in rows:
            original = row["query_text"]
            key = normalize_query_text(original)
            counts[key] = counts.get(key, 0) + 1
            display.setdefault(key, original.strip())

        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [(display[key], count) for key, count in ranked[:limit]]


class SqliteInstanceStore:
    def __init__(self, connection_factory: SqliteConnection) -> None:
        self._connection_factory = connection_factory

    def clear_all(self) -> ClearResult:
        with self._connection_factory.connect() as connection:
            facts_removed = int(connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0])
            gaps_removed = int(connection.execute("SELECT COUNT(*) FROM gaps").fetchone()[0])
            query_logs_removed = int(
                connection.execute("SELECT COUNT(*) FROM query_logs").fetchone()[0]
            )
            connection.execute("DELETE FROM query_logs")
            connection.execute("DELETE FROM gaps")
            connection.execute("DELETE FROM facts")
            connection.commit()

        return ClearResult(
            facts_removed=facts_removed,
            gaps_removed=gaps_removed,
            query_logs_removed=query_logs_removed,
        )


class SqliteStatsReader:
    def __init__(
        self,
        fact_repo: SqliteFactRepository,
        gap_repo: SqliteGapRepository,
        query_repo: SqliteQueryLogRepository,
    ) -> None:
        self._fact_repo = fact_repo
        self._gap_repo = gap_repo
        self._query_repo = query_repo

    def get_stats(self) -> Stats:
        return Stats(
            fact_count=self._fact_repo.count(),
            gap_count=self._gap_repo.count(),
            open_gaps=self._gap_repo.count_open(),
            resolved_gaps=self._gap_repo.count_resolved(),
            query_count=self._query_repo.count(),
            answered_queries=self._query_repo.count_by_result_type(ResultType.FACT),
            unanswered_queries=self._query_repo.count_by_result_type(ResultType.GAP),
            top_queries=self._query_repo.top_queries(10),
            top_gap_subjects=self._gap_repo.top_open_subjects(10),
        )


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


def _format_datetime(value: datetime) -> str:
    return value.isoformat()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _row_to_fact(row: sqlite3.Row) -> Fact:
    return Fact(
        id=row["id"],
        text=row["text"],
        embedding=row["embedding"],
        confidence=float(row["confidence"]),
        tags=json.loads(row["tags"]),
        created_at=_parse_datetime(row["created_at"]),
    )


def _row_to_summary(row: sqlite3.Row) -> FactSummary:
    return FactSummary(
        id=row["id"],
        text=row["text"],
        confidence=float(row["confidence"]),
        tags=json.loads(row["tags"]),
        created_at=_parse_datetime(row["created_at"]),
    )


def _row_to_gap(row: sqlite3.Row) -> Gap:
    return Gap(
        id=row["id"],
        question=row["question"],
        created_at=_parse_datetime(row["created_at"]),
        resolved_at=_parse_datetime(row["resolved_at"]) if row["resolved_at"] else None,
        resolved_fact_id=row["resolved_fact_id"],
    )
