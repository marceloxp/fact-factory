from __future__ import annotations

from fact_factory.domain.exceptions import ConflictError, NotFoundError
from fact_factory.domain.models import Fact, Gap
from fact_factory.domain.ports import EmbeddingProvider, FactRepository, GapRepository
from fact_factory.domain.services.fact_service import FactService
from fact_factory.infrastructure.sqlite.repositories import utc_now


class GapService:
    def __init__(
        self,
        gap_repo: GapRepository,
        fact_service: FactService,
    ) -> None:
        self._gap_repo = gap_repo
        self._fact_service = fact_service

    def list_open(self) -> list[Gap]:
        return self._gap_repo.list_open()

    def show(self, gap_id: str) -> Gap:
        gap = self._gap_repo.get_by_id(gap_id)
        if gap is None:
            raise NotFoundError(f"Gap not found: {gap_id}")
        return gap

    def resolve(self, gap_id: str, fact_text: str) -> tuple[Gap, Fact]:
        gap = self.show(gap_id)
        if gap.resolved_at is not None:
            raise ConflictError(f"Gap is already resolved: {gap_id}")

        fact = self._fact_service.add_fact(fact_text)
        self._gap_repo.resolve(gap_id, utc_now(), fact.id)
        resolved = self._gap_repo.get_by_id(gap_id)
        assert resolved is not None
        return resolved, fact

    def remove(self, gap_id: str, *, force: bool = False) -> None:
        self._gap_repo.remove(gap_id, force=force)
