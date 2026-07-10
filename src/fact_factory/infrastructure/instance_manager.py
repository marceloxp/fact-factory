from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from fact_factory.domain.exceptions import InstanceAlreadyExistsError
from fact_factory.infrastructure.config import (
    INSTANCE_DIR_NAME,
    db_path,
    default_config,
    write_config,
)
from fact_factory.infrastructure.sqlite.schema import initialize_schema

SCHEMA_VERSION = 1


class InstanceManager:
    def create(self, target_dir: Path) -> Path:
        instance_dir = target_dir.resolve() / INSTANCE_DIR_NAME
        if instance_dir.exists():
            raise InstanceAlreadyExistsError(
                f"Instance already exists at {instance_dir}"
            )

        instance_dir.mkdir(parents=True)
        write_config(instance_dir, default_config())

        database = db_path(instance_dir)
        with sqlite3.connect(database) as connection:
            initialize_schema(connection)
            connection.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, _utc_now_iso()),
            )
            connection.commit()

        return instance_dir


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
