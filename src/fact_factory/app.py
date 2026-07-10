from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fact_factory.domain.models import Config
from fact_factory.domain.services.clear_service import ClearService
from fact_factory.domain.services.fact_service import FactService
from fact_factory.domain.services.gap_service import GapService
from fact_factory.domain.services.query_service import QueryService
from fact_factory.domain.services.stats_service import StatsService
from fact_factory.infrastructure.config import load_config
from fact_factory.infrastructure.discovery import InstanceDiscovery
from fact_factory.infrastructure.instance_manager import InstanceManager
from fact_factory.infrastructure.ollama.client import OllamaEmbeddingClient
from fact_factory.infrastructure.sqlite.repositories import (
    SqliteConnection,
    SqliteFactRepository,
    SqliteGapRepository,
    SqliteInstanceStore,
    SqliteQueryLogRepository,
    SqliteStatsReader,
)
from fact_factory.reranking.hybrid import HybridReranker


@dataclass(frozen=True)
class AppContext:
    instance_dir: Path
    config: Config
    fact_service: FactService
    query_service: QueryService
    gap_service: GapService
    stats_service: StatsService
    clear_service: ClearService
    fact_repo: SqliteFactRepository


def build_context(instance_dir: Path) -> AppContext:
    config = load_config(instance_dir)
    connection = SqliteConnection(instance_dir)
    fact_repo = SqliteFactRepository(connection)
    gap_repo = SqliteGapRepository(connection)
    query_log_repo = SqliteQueryLogRepository(connection)
    embedder = OllamaEmbeddingClient(
        base_url=config.ollama_base_url,
        model=config.embedding_model,
    )
    fact_service = FactService(fact_repo=fact_repo, embedder=embedder)
    query_service = QueryService(
        config=config,
        fact_repo=fact_repo,
        gap_repo=gap_repo,
        query_log_repo=query_log_repo,
        embedder=embedder,
        reranker=HybridReranker(),
    )
    gap_service = GapService(gap_repo=gap_repo, fact_service=fact_service)
    stats_service = StatsService(
        stats_reader=SqliteStatsReader(
            fact_repo=fact_repo,
            gap_repo=gap_repo,
            query_repo=query_log_repo,
        )
    )
    clear_service = ClearService(instance_store=SqliteInstanceStore(connection))
    return AppContext(
        instance_dir=instance_dir,
        config=config,
        fact_service=fact_service,
        query_service=query_service,
        gap_service=gap_service,
        stats_service=stats_service,
        clear_service=clear_service,
        fact_repo=fact_repo,
    )


def locate_instance(start: Path | None = None) -> Path:
    return InstanceDiscovery().locate(start=start)


def create_instance(target_dir: Path) -> Path:
    return InstanceManager().create(target_dir)
