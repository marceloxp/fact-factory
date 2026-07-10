from __future__ import annotations

import json
import re
from pathlib import Path

from fact_factory.domain.models import Config

INSTANCE_DIR_NAME = ".fact-factory"
DB_FILE_NAME = "facts.db"
CONFIG_FILE_NAME = "config.json"


def default_config() -> Config:
    return Config()


def config_path(instance_dir: Path) -> Path:
    return instance_dir / CONFIG_FILE_NAME


def db_path(instance_dir: Path) -> Path:
    return instance_dir / DB_FILE_NAME


def load_config(instance_dir: Path) -> Config:
    path = config_path(instance_dir)
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config(
        embedding_model=data.get("embedding_model", "embeddinggemma:latest"),
        ollama_base_url=data.get("ollama_base_url", "http://localhost:11434"),
        top_k=int(data.get("top_k", 10)),
        min_relevance_score=float(data.get("min_relevance_score", 0.65)),
        page_size=int(data.get("page_size", 20)),
    )


def write_config(instance_dir: Path, config: Config | None = None) -> None:
    config = config or default_config()
    payload = {
        "embedding_model": config.embedding_model,
        "ollama_base_url": config.ollama_base_url,
        "top_k": config.top_k,
        "min_relevance_score": config.min_relevance_score,
        "page_size": config.page_size,
    }
    config_path(instance_dir).write_text(
        json.dumps(payload, indent=4) + "\n",
        encoding="utf-8",
    )


def normalize_query_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())
