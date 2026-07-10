from __future__ import annotations

from fact_factory.domain.models import ClearResult
from fact_factory.domain.ports import InstanceStore


class ClearService:
    def __init__(self, instance_store: InstanceStore) -> None:
        self._instance_store = instance_store

    def clear_all(self) -> ClearResult:
        return self._instance_store.clear_all()
