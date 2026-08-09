from __future__ import annotations

import sqlite3

import pytest
from study_assistant_agent.database import Database


@pytest.mark.asyncio
async def test_database_initializes_current_schema(tmp_path) -> None:
    database = Database(tmp_path / "study-assistant.db")

    await database.initialize()

    with sqlite3.connect(database.path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 5
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert {"tasks", "sources", "transcript_segments", "semantic_chunks"} <= tables


@pytest.mark.asyncio
async def test_task_and_lesson_lifecycle(tmp_path) -> None:
    database = Database(tmp_path / "study-assistant.db")
    await database.initialize()

    task = await database.create_task("Machine Learning", "en")
    first = await database.add_source(task["id"], "https://example.com/one")
    second = await database.add_source(
        task["id"],
        "https://example.com/two",
        prompt_preset_id="deep",
        output_language="de",
        custom_title="Custom lesson",
    )

    assert first["lesson_index"] == 1
    assert second["lesson_index"] == 2
    assert second["custom_title"] == "Custom lesson"
    assert (await database.get_task(task["id"]))["lesson_count"] == 2

    renamed = await database.update_task_fields(task["id"], "Renamed")
    updated_source = await database.update_source_fields(first["id"], custom_title="Lesson one")
    assert renamed["title"] == "Renamed"
    assert updated_source["custom_title"] == "Lesson one"

    assert await database.delete_source(first["id"])
    remaining = await database.list_sources(task["id"])
    assert len(remaining) == 1
    assert remaining[0]["lesson_index"] == 1

    assert await database.delete_task(task["id"])
    assert await database.get_task(task["id"]) is None


@pytest.mark.asyncio
async def test_delete_missing_records_is_false(tmp_path) -> None:
    database = Database(tmp_path / "study-assistant.db")
    await database.initialize()

    assert await database.delete_source("missing") is False
    assert await database.delete_task("missing") is False
