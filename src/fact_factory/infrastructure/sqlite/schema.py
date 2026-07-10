from __future__ import annotations

import sqlite3


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS facts (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL,
            confidence REAL NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS gaps (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            resolved_fact_id TEXT,
            FOREIGN KEY (resolved_fact_id) REFERENCES facts(id)
        );

        CREATE TABLE IF NOT EXISTS query_logs (
            id TEXT PRIMARY KEY,
            query_text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            result_type TEXT NOT NULL,
            result_ids TEXT NOT NULL DEFAULT '[]'
        );

        CREATE INDEX IF NOT EXISTS idx_facts_created_at ON facts(created_at);
        CREATE INDEX IF NOT EXISTS idx_gaps_resolved_at ON gaps(resolved_at);
        CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
        """
    )
