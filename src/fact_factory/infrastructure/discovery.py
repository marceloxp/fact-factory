from __future__ import annotations

from pathlib import Path

from fact_factory.domain.exceptions import InstanceNotFoundError
from fact_factory.infrastructure.config import CONFIG_FILE_NAME, DB_FILE_NAME, INSTANCE_DIR_NAME


class InstanceDiscovery:
    def locate(self, start: Path | None = None) -> Path:
        current = (start or Path.cwd()).resolve()
        home = Path.home().resolve()

        while True:
            instance_dir = current / INSTANCE_DIR_NAME
            if _is_valid_instance(instance_dir):
                return instance_dir

            if current == home:
                break

            parent = current.parent
            if parent == current:
                break
            current = parent

        global_instance = home / INSTANCE_DIR_NAME
        if _is_valid_instance(global_instance):
            return global_instance

        raise InstanceNotFoundError(
            "No fact-factory instance found. Run 'fact create' in your project directory."
        )


def _is_valid_instance(instance_dir: Path) -> bool:
    return (
        instance_dir.is_dir()
        and (instance_dir / DB_FILE_NAME).is_file()
        and (instance_dir / CONFIG_FILE_NAME).is_file()
    )
