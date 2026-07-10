from __future__ import annotations

from fact_factory.domain.models import Stats
from fact_factory.infrastructure.sqlite.repositories import SqliteStatsReader


class StatsService:
    def __init__(self, stats_reader: SqliteStatsReader) -> None:
        self._stats_reader = stats_reader

    def get_stats(self) -> Stats:
        return self._stats_reader.get_stats()
