from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .retrieval import extract_search_terms, lexical_score, relevant_excerpt


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    def _initialize_sync(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            language TEXT NOT NULL,
            allow_external_sources INTEGER NOT NULL DEFAULT 0,
            progress REAL NOT NULL DEFAULT 0,
            status_detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            custom_title TEXT NOT NULL DEFAULT '',
            platform TEXT NOT NULL DEFAULT 'web',
            duration_seconds REAL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            lesson_index INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'IDLE',
            progress REAL NOT NULL DEFAULT 0,
            status_detail TEXT NOT NULL DEFAULT '',
            prompt_preset_id TEXT NOT NULL DEFAULT 'standard',
            prompt_version TEXT NOT NULL DEFAULT '1.2',
            output_language TEXT NOT NULL DEFAULT 'auto',
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sources_task ON sources(task_id);
        CREATE TABLE IF NOT EXISTS capability_reports (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            report_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_reports_task ON capability_reports(task_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            progress REAL NOT NULL DEFAULT 0,
            cursor_seconds REAL NOT NULL DEFAULT 0,
            processed_segments INTEGER NOT NULL DEFAULT 0,
            error_code TEXT,
            error_message TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_task ON jobs(task_id, updated_at DESC);
        CREATE TABLE IF NOT EXISTS transcript_segments (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            start_seconds REAL NOT NULL,
            end_seconds REAL NOT NULL,
            speaker TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL,
            confidence REAL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_transcript_task_time ON transcript_segments(task_id, start_seconds);
        CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
            segment_id UNINDEXED,
            task_id UNINDEXED,
            content,
            tokenize='unicode61'
        );
        CREATE TABLE IF NOT EXISTS note_blocks (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            start_seconds REAL,
            end_seconds REAL,
            citations_json TEXT NOT NULL DEFAULT '[]',
            prompt_preset_id TEXT NOT NULL DEFAULT 'standard',
            prompt_version TEXT NOT NULL DEFAULT '1.2',
            output_language TEXT NOT NULL DEFAULT 'auto',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_notes_task ON note_blocks(task_id, start_seconds, created_at);
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_conversations_task ON conversations(task_id, updated_at DESC);
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations_json TEXT NOT NULL DEFAULT '[]',
            model TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
        CREATE TABLE IF NOT EXISTS semantic_chunks (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            start_seconds REAL NOT NULL,
            end_seconds REAL NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            model_id TEXT NOT NULL,
            model_revision TEXT NOT NULL,
            dimension INTEGER NOT NULL,
            vector BLOB NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_task_model
            ON semantic_chunks(task_id, model_revision);
        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_source
            ON semantic_chunks(source_id, start_seconds);
        CREATE TABLE IF NOT EXISTS semantic_source_state (
            source_id TEXT PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
            task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            transcript_hash TEXT NOT NULL,
            model_id TEXT NOT NULL,
            model_revision TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_semantic_state_task
            ON semantic_source_state(task_id, model_revision);
        """
        with self._lock, self._connect() as connection:
            existing_schema = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
            ).fetchone()
            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if existing_schema and user_version < 5:
                source_version = (
                    "0.1.0"
                    if user_version < 2
                    else "0.1.1"
                    if user_version < 3
                    else "0.1.2"
                    if user_version < 4
                    else "0.1.4"
                )
                self._backup_before_migration(connection, source_version)
            connection.executescript(schema)
            if user_version < 2:
                self._migrate_to_0_1_1(connection)
            if user_version < 3:
                self._migrate_to_0_1_2(connection)
            if user_version < 4:
                self._migrate_to_0_1_3(connection)
            if user_version < 5:
                self._migrate_to_0_1_5(connection)
            connection.execute(
                """
                UPDATE tasks
                SET status = 'PAUSED', status_detail = '应用重新启动，可继续任务', updated_at = ?
                WHERE status IN ('CHECKING', 'WATCHING', 'TRANSCRIBING', 'NOTE_TAKING')
                """,
                (utc_now(),),
            )
            connection.commit()

    def _backup_before_migration(self, connection: sqlite3.Connection, source_version: str) -> Path:
        backup_dir = self.path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_dir / f"study-assistant-{source_version}-{timestamp}.db"
        suffix = 1
        while backup_path.exists():
            backup_path = backup_dir / f"study-assistant-{source_version}-{timestamp}-{suffix}.db"
            suffix += 1
        destination = sqlite3.connect(backup_path)
        try:
            connection.backup(destination)
        finally:
            destination.close()
        return backup_path

    @staticmethod
    def _migrate_to_0_1_1(connection: sqlite3.Connection) -> None:
        source_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(sources)").fetchall()
        }
        source_additions = {
            "lesson_index": "INTEGER NOT NULL DEFAULT 1",
            "status": "TEXT NOT NULL DEFAULT 'IDLE'",
            "progress": "REAL NOT NULL DEFAULT 0",
            "status_detail": "TEXT NOT NULL DEFAULT ''",
            "prompt_preset_id": "TEXT NOT NULL DEFAULT 'standard'",
            "prompt_version": "TEXT NOT NULL DEFAULT '1.1'",
            "output_language": "TEXT NOT NULL DEFAULT 'auto'",
        }
        for column, definition in source_additions.items():
            if column not in source_columns:
                connection.execute(f"ALTER TABLE sources ADD COLUMN {column} {definition}")

        note_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(note_blocks)").fetchall()
        }
        note_additions = {
            "prompt_preset_id": "TEXT NOT NULL DEFAULT 'standard'",
            "prompt_version": "TEXT NOT NULL DEFAULT '1.1'",
            "output_language": "TEXT NOT NULL DEFAULT 'auto'",
        }
        for column, definition in note_additions.items():
            if column not in note_columns:
                connection.execute(f"ALTER TABLE note_blocks ADD COLUMN {column} {definition}")

        task_ids = [row[0] for row in connection.execute("SELECT id FROM tasks").fetchall()]
        for task_id in task_ids:
            sources = connection.execute(
                "SELECT id FROM sources WHERE task_id = ? ORDER BY created_at, rowid", (task_id,)
            ).fetchall()
            for lesson_index, source in enumerate(sources, start=1):
                source_id = source[0]
                has_notes = connection.execute(
                    "SELECT 1 FROM note_blocks WHERE source_id = ? LIMIT 1", (source_id,)
                ).fetchone()
                has_transcript = connection.execute(
                    "SELECT 1 FROM transcript_segments WHERE source_id = ? LIMIT 1", (source_id,)
                ).fetchone()
                task = connection.execute(
                    "SELECT status, progress, status_detail, language FROM tasks WHERE id = ?",
                    (task_id,),
                ).fetchone()
                status = "READY_FOR_QA" if has_notes else (task[0] if has_transcript else "IDLE")
                progress = 1.0 if has_notes else (task[1] if has_transcript else 0.0)
                detail = task[2] if (has_notes or has_transcript) else ""
                output_language = task[3] or "auto"
                connection.execute(
                    """
                    UPDATE sources
                    SET lesson_index = ?, status = ?, progress = ?, status_detail = ?,
                        output_language = ?
                    WHERE id = ?
                    """,
                    (lesson_index, status, progress, detail, output_language, source_id),
                )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_task_lesson "
            "ON sources(task_id, lesson_index)"
        )
        connection.execute("PRAGMA user_version = 2")

    @staticmethod
    def _migrate_to_0_1_2(connection: sqlite3.Connection) -> None:
        source_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(sources)").fetchall()
        }
        if "custom_title" not in source_columns:
            connection.execute(
                "ALTER TABLE sources ADD COLUMN custom_title TEXT NOT NULL DEFAULT ''"
            )
        connection.execute("UPDATE sources SET prompt_version = '1.2' WHERE prompt_version = '1.1'")
        connection.execute("PRAGMA user_version = 3")

    @staticmethod
    def _migrate_to_0_1_3(connection: sqlite3.Connection) -> None:
        # Keep the physical column so older databases remain forward-compatible,
        # but retire the feature and clear every previously enabled task flag.
        connection.execute("UPDATE tasks SET allow_external_sources = 0")
        connection.execute("PRAGMA user_version = 4")

    @staticmethod
    def _migrate_to_0_1_5(connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA user_version = 5")

    async def execute(self, sql: str, params: Iterable[object] = ()) -> None:
        await asyncio.to_thread(self._execute_sync, sql, tuple(params))

    def _execute_sync(self, sql: str, params: tuple[object, ...]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(sql, params)
            connection.commit()

    async def query_one(self, sql: str, params: Iterable[object] = ()) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._query_one_sync, sql, tuple(params))

    def _query_one_sync(self, sql: str, params: tuple[object, ...]) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(sql, params).fetchone()
            return dict(row) if row else None

    async def query_all(self, sql: str, params: Iterable[object] = ()) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._query_all_sync, sql, tuple(params))

    def _query_all_sync(self, sql: str, params: tuple[object, ...]) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    async def create_task(self, title: str, language: str) -> dict[str, Any]:
        task_id = new_id()
        timestamp = utc_now()
        await self.execute(
            """
            INSERT INTO tasks(id, title, status, language, allow_external_sources, progress,
                              status_detail, created_at, updated_at)
            VALUES (?, ?, 'IDLE', ?, ?, 0, '等待课程网址', ?, ?)
            """,
            (task_id, title, language, 0, timestamp, timestamp),
        )
        return await self.get_task(task_id)  # type: ignore[return-value]

    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        row = await self.query_one(
            """
            SELECT tasks.*,
                   COUNT(sources.id) AS lesson_count,
                   COALESCE(SUM(CASE WHEN sources.status = 'READY_FOR_QA' THEN 1 ELSE 0 END), 0)
                       AS completed_lessons
            FROM tasks LEFT JOIN sources ON sources.task_id = tasks.id
            WHERE tasks.id = ? GROUP BY tasks.id
            """,
            (task_id,),
        )
        return self._normalize_task(row) if row else None

    async def list_tasks(self) -> list[dict[str, Any]]:
        rows = await self.query_all(
            """
            SELECT tasks.*,
                   COUNT(sources.id) AS lesson_count,
                   COALESCE(SUM(CASE WHEN sources.status = 'READY_FOR_QA' THEN 1 ELSE 0 END), 0)
                       AS completed_lessons
            FROM tasks LEFT JOIN sources ON sources.task_id = tasks.id
            GROUP BY tasks.id ORDER BY tasks.updated_at DESC
            """
        )
        return [self._normalize_task(row) for row in rows]

    async def delete_task(self, task_id: str) -> bool:
        return await asyncio.to_thread(self._delete_task_sync, task_id)

    def _delete_task_sync(self, task_id: str) -> bool:
        with self._lock, self._connect() as connection:
            exists = connection.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not exists:
                return False
            connection.execute("DELETE FROM transcript_fts WHERE task_id = ?", (task_id,))
            connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            connection.commit()
            return True

    @staticmethod
    def _normalize_task(row: dict[str, Any]) -> dict[str, Any]:
        row.pop("allow_external_sources", None)
        return row

    async def update_task_state(
        self,
        task_id: str,
        status: str,
        detail: str,
        progress: float | None = None,
    ) -> None:
        if progress is None:
            await self.execute(
                "UPDATE tasks SET status = ?, status_detail = ?, updated_at = ? WHERE id = ?",
                (status, detail, utc_now(), task_id),
            )
        else:
            await self.execute(
                """
                UPDATE tasks SET status = ?, status_detail = ?, progress = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, detail, max(0.0, min(1.0, progress)), utc_now(), task_id),
            )

    async def update_task_fields(self, task_id: str, title: str | None) -> dict[str, Any] | None:
        current = await self.get_task(task_id)
        if not current:
            return None
        await self.execute(
            """
            UPDATE tasks SET title = ?, allow_external_sources = 0, updated_at = ? WHERE id = ?
            """,
            (
                title or current["title"],
                utc_now(),
                task_id,
            ),
        )
        return await self.get_task(task_id)

    async def add_source(
        self,
        task_id: str,
        url: str,
        prompt_preset_id: str = "standard",
        output_language: str = "auto",
        custom_title: str = "",
    ) -> dict[str, Any]:
        source_id = new_id()
        timestamp = utc_now()
        await asyncio.to_thread(
            self._add_source_sync,
            source_id,
            task_id,
            url,
            prompt_preset_id,
            output_language,
            custom_title,
            timestamp,
        )
        await self.execute(
            "UPDATE tasks SET status_detail = '课程网址已添加，等待能力检查', updated_at = ? WHERE id = ?",
            (timestamp, task_id),
        )
        return await self.get_source(source_id)  # type: ignore[return-value]

    def _add_source_sync(
        self,
        source_id: str,
        task_id: str,
        url: str,
        prompt_preset_id: str,
        output_language: str,
        custom_title: str,
        timestamp: str,
    ) -> None:
        with self._lock, self._connect() as connection:
            next_index = connection.execute(
                "SELECT COALESCE(MAX(lesson_index), 0) + 1 FROM sources WHERE task_id = ?",
                (task_id,),
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO sources(
                    id, task_id, url, title, custom_title, platform, lesson_index, status, status_detail,
                    prompt_preset_id, prompt_version, output_language, created_at
                ) VALUES (?, ?, ?, '', ?, 'web', ?, 'IDLE', '', ?, '1.2', ?, ?)
                """,
                (
                    source_id,
                    task_id,
                    url,
                    custom_title,
                    next_index,
                    prompt_preset_id,
                    output_language,
                    timestamp,
                ),
            )
            connection.commit()

    async def get_source(self, source_id: str) -> dict[str, Any] | None:
        return await self.query_one(
            """
            SELECT id, task_id, url, title, custom_title, platform, duration_seconds, lesson_index,
                   status, progress, status_detail, prompt_preset_id, prompt_version,
                   output_language, created_at
            FROM sources WHERE id = ?
            """,
            (source_id,),
        )

    async def list_sources(self, task_id: str) -> list[dict[str, Any]]:
        return await self.query_all(
            """
            SELECT id, task_id, url, title, custom_title, platform, duration_seconds, lesson_index,
                   status, progress, status_detail, prompt_preset_id, prompt_version,
                   output_language, created_at
            FROM sources WHERE task_id = ? ORDER BY lesson_index
            """,
            (task_id,),
        )

    async def update_source_metadata(
        self,
        source_id: str,
        title: str,
        platform: str,
        duration: float | None,
        metadata: dict[str, Any],
    ) -> None:
        await self.execute(
            """
            UPDATE sources SET title = ?, platform = ?, duration_seconds = ?, metadata_json = ?
            WHERE id = ?
            """,
            (title, platform, duration, _json(metadata), source_id),
        )

    async def update_source_fields(
        self,
        source_id: str,
        *,
        custom_title: str | None = None,
        prompt_preset_id: str | None = None,
        output_language: str | None = None,
    ) -> dict[str, Any] | None:
        current = await self.get_source(source_id)
        if not current:
            return None
        await self.execute(
            """
            UPDATE sources SET custom_title = ?, prompt_preset_id = ?, output_language = ?
            WHERE id = ?
            """,
            (
                current["custom_title"] if custom_title is None else custom_title,
                current["prompt_preset_id"] if prompt_preset_id is None else prompt_preset_id,
                current["output_language"] if output_language is None else output_language,
                source_id,
            ),
        )
        return await self.get_source(source_id)

    async def update_source_state(
        self, source_id: str, status: str, detail: str, progress: float | None = None
    ) -> None:
        if progress is None:
            await self.execute(
                "UPDATE sources SET status = ?, status_detail = ? WHERE id = ?",
                (status, detail, source_id),
            )
        else:
            await self.execute(
                "UPDATE sources SET status = ?, status_detail = ?, progress = ? WHERE id = ?",
                (status, detail, max(0.0, min(1.0, progress)), source_id),
            )

    async def delete_source(self, source_id: str) -> bool:
        return await asyncio.to_thread(self._delete_source_sync, source_id)

    def _delete_source_sync(self, source_id: str) -> bool:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT task_id, lesson_index FROM sources WHERE id = ?", (source_id,)
            ).fetchone()
            if not row:
                return False
            task_id, lesson_index = row
            segment_ids = connection.execute(
                "SELECT id FROM transcript_segments WHERE source_id = ?", (source_id,)
            ).fetchall()
            connection.executemany("DELETE FROM transcript_fts WHERE segment_id = ?", segment_ids)
            connection.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            connection.execute(
                "UPDATE sources SET lesson_index = lesson_index - 1 "
                "WHERE task_id = ? AND lesson_index > ?",
                (task_id, lesson_index),
            )
            connection.commit()
            return True

    async def save_capability_report(self, report: dict[str, Any]) -> dict[str, Any]:
        report_id = report.get("id") or new_id()
        timestamp = utc_now()
        payload = {**report, "id": report_id, "created_at": timestamp}
        await self.execute(
            """
            INSERT INTO capability_reports(id, task_id, source_id, status, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                report["task_id"],
                report["source_id"],
                report["status"],
                _json(payload),
                timestamp,
            ),
        )
        return payload

    async def latest_capability_report(
        self, task_id: str, source_id: str | None = None
    ) -> dict[str, Any] | None:
        if source_id:
            row = await self.query_one(
                """
                SELECT report_json FROM capability_reports
                WHERE task_id = ? AND source_id = ? ORDER BY created_at DESC LIMIT 1
                """,
                (task_id, source_id),
            )
        else:
            row = await self.query_one(
                """
                SELECT report_json FROM capability_reports
                WHERE task_id = ? ORDER BY created_at DESC LIMIT 1
                """,
                (task_id,),
            )
        return json.loads(row["report_json"]) if row else None

    async def insert_transcript_segments(self, segments: list[dict[str, Any]]) -> None:
        await asyncio.to_thread(self._insert_transcript_segments_sync, segments)

    def _insert_transcript_segments_sync(self, segments: list[dict[str, Any]]) -> None:
        timestamp = utc_now()
        with self._lock, self._connect() as connection:
            for segment in segments:
                segment_id = segment.get("id") or new_id()
                connection.execute(
                    """
                    INSERT INTO transcript_segments(
                        id, task_id, source_id, start_seconds, end_seconds, speaker,
                        content, confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        segment_id,
                        segment["task_id"],
                        segment["source_id"],
                        segment["start_seconds"],
                        segment["end_seconds"],
                        segment.get("speaker", ""),
                        segment["content"],
                        segment.get("confidence"),
                        timestamp,
                    ),
                )
                connection.execute(
                    "INSERT INTO transcript_fts(segment_id, task_id, content) VALUES (?, ?, ?)",
                    (segment_id, segment["task_id"], segment["content"]),
                )
            connection.commit()

    async def list_transcript(
        self, task_id: str, source_id: str | None = None
    ) -> list[dict[str, Any]]:
        if source_id:
            return await self.query_all(
                "SELECT * FROM transcript_segments WHERE task_id = ? AND source_id = ? "
                "ORDER BY start_seconds",
                (task_id, source_id),
            )
        return await self.query_all(
            "SELECT * FROM transcript_segments WHERE task_id = ? ORDER BY source_id, start_seconds",
            (task_id,),
        )

    async def list_sources_with_transcript(self) -> list[dict[str, Any]]:
        return await self.query_all(
            """
            SELECT s.id, s.task_id, s.lesson_index, COUNT(ts.id) AS segment_count
            FROM sources s JOIN transcript_segments ts ON ts.source_id = s.id
            GROUP BY s.id, s.task_id, s.lesson_index
            ORDER BY s.task_id, s.lesson_index
            """
        )

    async def get_semantic_source_state(self, source_id: str) -> dict[str, Any] | None:
        return await self.query_one(
            "SELECT * FROM semantic_source_state WHERE source_id = ?", (source_id,)
        )

    async def replace_semantic_index(
        self,
        task_id: str,
        source_id: str,
        transcript_hash: str,
        model_id: str,
        model_revision: str,
        chunks: list[dict[str, Any]],
    ) -> None:
        await asyncio.to_thread(
            self._replace_semantic_index_sync,
            task_id,
            source_id,
            transcript_hash,
            model_id,
            model_revision,
            chunks,
        )

    def _replace_semantic_index_sync(
        self,
        task_id: str,
        source_id: str,
        transcript_hash: str,
        model_id: str,
        model_revision: str,
        chunks: list[dict[str, Any]],
    ) -> None:
        timestamp = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM semantic_chunks WHERE source_id = ?", (source_id,))
            connection.executemany(
                """
                INSERT INTO semantic_chunks(
                    id, task_id, source_id, start_seconds, end_seconds, content,
                    content_hash, model_id, model_revision, dimension, vector, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk["id"],
                        task_id,
                        source_id,
                        chunk["start_seconds"],
                        chunk["end_seconds"],
                        chunk["content"],
                        chunk["content_hash"],
                        model_id,
                        model_revision,
                        chunk["dimension"],
                        chunk["vector"],
                        timestamp,
                    )
                    for chunk in chunks
                ],
            )
            connection.execute(
                """
                INSERT INTO semantic_source_state(
                    source_id, task_id, transcript_hash, model_id, model_revision,
                    chunk_count, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    task_id = excluded.task_id,
                    transcript_hash = excluded.transcript_hash,
                    model_id = excluded.model_id,
                    model_revision = excluded.model_revision,
                    chunk_count = excluded.chunk_count,
                    updated_at = excluded.updated_at
                """,
                (
                    source_id,
                    task_id,
                    transcript_hash,
                    model_id,
                    model_revision,
                    len(chunks),
                    timestamp,
                ),
            )
            connection.commit()

    async def list_semantic_chunks(
        self, task_id: str, model_revision: str
    ) -> list[dict[str, Any]]:
        return await self.query_all(
            """
            SELECT c.*, s.lesson_index, s.title AS lesson_title,
                   s.custom_title AS lesson_custom_title, s.url AS lesson_url
            FROM semantic_chunks c JOIN sources s ON s.id = c.source_id
            WHERE c.task_id = ? AND c.model_revision = ?
            ORDER BY s.lesson_index, c.start_seconds
            """,
            (task_id, model_revision),
        )

    async def semantic_status_counts(self, model_revision: str) -> dict[str, int]:
        total_row = await self.query_one(
            """
            SELECT COUNT(DISTINCT source_id) AS count
            FROM transcript_segments
            """
        )
        indexed_row = await self.query_one(
            """
            SELECT COUNT(*) AS source_count, COALESCE(SUM(chunk_count), 0) AS chunk_count
            FROM semantic_source_state WHERE model_revision = ?
            """,
            (model_revision,),
        )
        total = int(total_row["count"] if total_row else 0)
        indexed = int(indexed_row["source_count"] if indexed_row else 0)
        return {
            "indexed_sources": indexed,
            "pending_sources": max(0, total - indexed),
            "indexed_chunks": int(indexed_row["chunk_count"] if indexed_row else 0),
        }

    async def search_transcript(
        self,
        task_id: str,
        query: str,
        limit: int = 8,
        expanded_queries: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        queries = [query, *(expanded_queries or [])]
        terms = extract_search_terms(queries)
        candidates: dict[str, dict[str, Any]] = {}
        fts_terms = [term.replace('"', '""') for term in terms[:16]]
        fts_query = " OR ".join(f'"{term}"' for term in fts_terms)
        if fts_query:
            try:
                rows = await self.query_all(
                    """
                    SELECT ts.*, s.lesson_index, s.title AS lesson_title,
                           s.custom_title AS lesson_custom_title, s.url AS lesson_url,
                           bm25(transcript_fts) AS rank
                    FROM transcript_fts
                    JOIN transcript_segments ts ON ts.id = transcript_fts.segment_id
                    JOIN sources s ON s.id = ts.source_id
                    WHERE transcript_fts MATCH ? AND transcript_fts.task_id = ?
                    ORDER BY rank LIMIT ?
                    """,
                    (fts_query, task_id, max(limit * 8, 40)),
                )
                for row in rows:
                    row["fts_match"] = True
                    candidates[row["id"]] = row
            except sqlite3.OperationalError:
                pass
        if terms:
            clauses = " OR ".join("ts.content LIKE ? COLLATE NOCASE" for _ in terms[:24])
            rows = await self.query_all(
                f"""
                SELECT ts.*, s.lesson_index, s.title AS lesson_title,
                       s.custom_title AS lesson_custom_title, s.url AS lesson_url
                FROM transcript_segments ts JOIN sources s ON s.id = ts.source_id
                WHERE ts.task_id = ? AND ({clauses})
                ORDER BY s.lesson_index, ts.start_seconds LIMIT ?
                """,
                (task_id, *(f"%{term}%" for term in terms[:24]), max(limit * 20, 120)),
            )
            for row in rows:
                candidates.setdefault(row["id"], row)
        ranked: list[dict[str, Any]] = []
        for row in candidates.values():
            score = lexical_score(row["content"], queries, terms)
            if row.get("fts_match"):
                score += 3.0
            display_title = row.get("lesson_custom_title") or row.get("lesson_title") or ""
            score += lexical_score(display_title, queries, terms) * 0.35
            row["retrieval_score"] = score
            ranked.append(row)
        ranked.sort(
            key=lambda item: (
                -float(item["retrieval_score"]),
                int(item["lesson_index"]),
                float(item["start_seconds"]),
            )
        )
        return ranked[:limit]

    async def expand_transcript_context(
        self,
        matches: list[dict[str, Any]],
        window_seconds: float = 35.0,
        limit: int = 24,
    ) -> list[dict[str, Any]]:
        context: dict[str, dict[str, Any]] = {}
        for match in matches:
            rows = await self.query_all(
                """
                SELECT ts.*, s.lesson_index, s.title AS lesson_title,
                       s.custom_title AS lesson_custom_title, s.url AS lesson_url
                FROM transcript_segments ts JOIN sources s ON s.id = ts.source_id
                WHERE ts.source_id = ? AND ts.end_seconds >= ? AND ts.start_seconds <= ?
                ORDER BY ts.start_seconds LIMIT 12
                """,
                (
                    match["source_id"],
                    max(0.0, float(match["start_seconds"]) - window_seconds),
                    float(match["end_seconds"]) + window_seconds,
                ),
            )
            for row in rows:
                context[row["id"]] = row
                if len(context) >= limit:
                    break
            if len(context) >= limit:
                break
        return sorted(
            context.values(),
            key=lambda item: (int(item["lesson_index"]), float(item["start_seconds"])),
        )

    async def search_notes(
        self,
        task_id: str,
        query: str,
        expanded_queries: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        queries = [query, *(expanded_queries or [])]
        terms = extract_search_terms(queries)
        rows = await self.query_all(
            """
            SELECT n.*, s.lesson_index, s.title AS lesson_title,
                   s.custom_title AS lesson_custom_title, s.url AS lesson_url
            FROM note_blocks n LEFT JOIN sources s ON s.id = n.source_id
            WHERE n.task_id = ? AND n.kind IN ('rapid_overview', 'rapid_module')
            ORDER BY CASE WHEN n.kind = 'rapid_overview' THEN 0 ELSE 1 END, n.created_at DESC
            """,
            (task_id,),
        )
        ranked: list[dict[str, Any]] = []
        for row in rows:
            score = lexical_score(f"{row['title']}\n{row['content']}", queries, terms)
            if score <= 0:
                continue
            row["retrieval_score"] = score
            row["excerpt"] = relevant_excerpt(row["content"], terms)
            row["citations"] = json.loads(row.pop("citations_json"))
            ranked.append(row)
        ranked.sort(key=lambda item: -float(item["retrieval_score"]))
        if ranked:
            return ranked[:limit]
        overviews: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        for row in rows:
            if row["kind"] != "rapid_overview" or not row.get("source_id"):
                continue
            if row["source_id"] in seen_sources:
                continue
            seen_sources.add(row["source_id"])
            row["excerpt"] = relevant_excerpt(row["content"], terms, radius=1000)
            row["citations"] = json.loads(row.pop("citations_json"))
            overviews.append(row)
            if len(overviews) >= min(limit, 3):
                break
        return overviews

    async def add_note(
        self,
        task_id: str,
        source_id: str | None,
        kind: str,
        title: str,
        content: str,
        start_seconds: float | None,
        end_seconds: float | None,
        citations: list[dict[str, Any]],
        prompt_preset_id: str = "standard",
        prompt_version: str = "1.2",
        output_language: str = "auto",
    ) -> dict[str, Any]:
        note_id = new_id()
        timestamp = utc_now()
        await self.execute(
            """
            INSERT INTO note_blocks(id, task_id, source_id, kind, title, content,
                                    start_seconds, end_seconds, citations_json,
                                    prompt_preset_id, prompt_version, output_language,
                                    created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_id,
                task_id,
                source_id,
                kind,
                title,
                content,
                start_seconds,
                end_seconds,
                _json(citations),
                prompt_preset_id,
                prompt_version,
                output_language,
                timestamp,
                timestamp,
            ),
        )
        return {
            "id": note_id,
            "task_id": task_id,
            "source_id": source_id,
            "kind": kind,
            "title": title,
            "content": content,
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "citations": citations,
            "created_at": timestamp,
            "prompt_preset_id": prompt_preset_id,
            "prompt_version": prompt_version,
            "output_language": output_language,
        }

    async def list_notes(self, task_id: str, source_id: str | None = None) -> list[dict[str, Any]]:
        if source_id:
            rows = await self.query_all(
                """
                SELECT * FROM note_blocks WHERE task_id = ? AND source_id = ?
                ORDER BY COALESCE(start_seconds, -1), created_at
                """,
                (task_id, source_id),
            )
        else:
            rows = await self.query_all(
                """
                SELECT n.* FROM note_blocks n
                LEFT JOIN sources s ON s.id = n.source_id
                WHERE n.task_id = ?
                ORDER BY COALESCE(s.lesson_index, 0), COALESCE(n.start_seconds, -1), n.created_at
                """,
                (task_id,),
            )
        for row in rows:
            row["citations"] = json.loads(row.pop("citations_json"))
            row.pop("updated_at", None)
        return rows

    async def delete_notes(self, task_id: str, source_id: str | None = None) -> None:
        if source_id:
            await self.execute(
                "DELETE FROM note_blocks WHERE task_id = ? AND source_id = ?",
                (task_id, source_id),
            )
        else:
            await self.execute("DELETE FROM note_blocks WHERE task_id = ?", (task_id,))

    async def create_conversation(self, task_id: str, title: str) -> str:
        conversation_id = new_id()
        timestamp = utc_now()
        await self.execute(
            """
            INSERT INTO conversations(id, task_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, task_id, title, timestamp, timestamp),
        )
        return conversation_id

    async def conversation_belongs_to_task(self, conversation_id: str, task_id: str) -> bool:
        row = await self.query_one(
            "SELECT id FROM conversations WHERE id = ? AND task_id = ?",
            (conversation_id, task_id),
        )
        return bool(row)

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        model: str = "",
    ) -> dict[str, Any]:
        message_id = new_id()
        timestamp = utc_now()
        payload = citations or []
        await self.execute(
            """
            INSERT INTO messages(id, conversation_id, role, content, citations_json, model, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, role, content, _json(payload), model, timestamp),
        )
        await self.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (timestamp, conversation_id),
        )
        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "citations": payload,
            "created_at": timestamp,
        }

    async def list_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        rows = await self.query_all(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,),
        )
        for row in rows:
            row["citations"] = json.loads(row.pop("citations_json"))
            row.pop("model", None)
        return rows

    async def list_conversations(self, task_id: str) -> list[dict[str, Any]]:
        return await self.query_all(
            "SELECT * FROM conversations WHERE task_id = ? ORDER BY updated_at DESC",
            (task_id,),
        )

    async def update_conversation_title(
        self, conversation_id: str, title: str
    ) -> dict[str, Any] | None:
        await self.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, utc_now(), conversation_id),
        )
        return await self.query_one("SELECT * FROM conversations WHERE id = ?", (conversation_id,))

    async def delete_conversation(self, conversation_id: str) -> bool:
        row = await self.query_one("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not row:
            return False
        await self.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        return True

    async def delete_task_conversations(self, task_id: str) -> int:
        rows = await self.query_all("SELECT id FROM conversations WHERE task_id = ?", (task_id,))
        await self.execute("DELETE FROM conversations WHERE task_id = ?", (task_id,))
        return len(rows)
