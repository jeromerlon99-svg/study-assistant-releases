from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import __version__
from .config import get_settings
from .course import CourseError
from .database import Database
from .events import EventHub
from .orchestrator import AgentOrchestrator
from .prompts import list_prompt_presets
from .provider import ModelProvider, ProviderError
from .schemas import (
    CapabilityReport,
    ChatRequest,
    ChatResponse,
    Conversation,
    ConversationUpdate,
    ExportResponse,
    LessonCandidate,
    Message,
    NoteBlock,
    PreferencesUpdate,
    ProviderSelfTest,
    ProviderSettingsUpdate,
    SemanticStatus,
    Source,
    SourceCreate,
    SourceUpdate,
    Task,
    TaskControlResponse,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
    TranscriptSegment,
)
from .semantic import SemanticSearch
from .transcriber import LocalTranscriber

settings = get_settings()
database = Database(settings.database_path)
events = EventHub()
provider = ModelProvider(settings)
transcriber = LocalTranscriber(settings)
semantic = SemanticSearch(settings, database, events)
orchestrator = AgentOrchestrator(settings, database, events, provider, transcriber, semantic)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.initialize()
    await semantic.start()
    try:
        yield
    finally:
        await semantic.close()


app = FastAPI(
    title="Study Assistant Agent",
    version=__version__,
    description="Local API for course inspection, notes, task state, and course-first Q&A.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_session(
    request: Request,
    x_study_assistant_token: str | None = Header(default=None),
) -> None:
    if request.url.path in {"/health", "/version"}:
        return
    supplied_token = x_study_assistant_token or request.query_params.get("token")
    if settings.session_token and supplied_token != settings.session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token"
        )


Session = Depends(verify_session)


def require_task(task: dict[str, Any] | None) -> dict[str, Any]:
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


async def require_source(task_id: str, source_id: str) -> dict[str, Any]:
    source = await database.get_source(source_id)
    if not source or source["task_id"] != task_id:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return source


@app.exception_handler(CourseError)
async def course_error_handler(_: Request, error: CourseError):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422,
        content={"detail": {"code": error.code, "message": str(error)}},
    )


@app.exception_handler(ProviderError)
async def provider_error_handler(_: Request, error: ProviderError):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422,
        content={"detail": {"code": "TEXT_MODEL_NOT_READY", "message": str(error)}},
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "text_model_configured": provider.text_ready,
        "transcription_configured": transcriber.runtime_available,
        "local_transcription": transcriber.public_status(),
        "semantic_retrieval": await semantic.public_status(),
    }


@app.get("/version")
async def version() -> dict[str, str]:
    return {"version": __version__}


@app.get("/settings", dependencies=[Session])
async def get_provider_settings() -> dict[str, object]:
    return settings.public_dict()


@app.put("/settings", dependencies=[Session])
async def update_provider_settings(payload: ProviderSettingsUpdate) -> dict[str, object]:
    result = await provider.save_settings(payload)
    await events.publish("settings.updated", result)
    return result


@app.post("/settings/self-test", response_model=ProviderSelfTest, dependencies=[Session])
async def test_provider_settings() -> ProviderSelfTest:
    result = await provider.self_test()
    result.transcription_configured = transcriber.runtime_available
    local_state = (
        f"本地转写已就绪（{transcriber.model_name} 模型"
        + ("已下载）。" if transcriber.model_downloaded else "将在首次需要时下载）。")
        if transcriber.runtime_available
        else "本地 faster-whisper 运行库不可用。"
    )
    result.message = f"{result.message} {local_state}"
    return result


@app.get("/transcription/status", dependencies=[Session])
async def get_transcription_status() -> dict[str, object]:
    return transcriber.public_status()


@app.get("/semantic/status", response_model=SemanticStatus, dependencies=[Session])
async def get_semantic_status() -> dict[str, object]:
    return await semantic.public_status()


@app.get("/preferences", dependencies=[Session])
async def get_preferences() -> dict[str, str]:
    return settings.load_preferences()


@app.put("/preferences", dependencies=[Session])
async def update_preferences(payload: PreferencesUpdate) -> dict[str, str]:
    result = settings.save_preferences(payload.ui_language)
    await events.publish("preferences.updated", result)
    return result


@app.get("/note-prompts", dependencies=[Session])
async def get_note_prompts(locale: str = Query(default="zh-CN")) -> list[dict[str, object]]:
    return list_prompt_presets(locale)


@app.get("/lessons/discover", response_model=list[LessonCandidate], dependencies=[Session])
async def discover_lessons(url: str = Query(min_length=8, max_length=4000)) -> list[dict[str, str]]:
    return await orchestrator.inspector.discover_lessons(url)


@app.post("/tasks", response_model=Task, status_code=201, dependencies=[Session])
async def create_task(payload: TaskCreate) -> dict[str, Any]:
    task = await database.create_task(payload.title.strip(), payload.language)
    await events.publish("task.created", task)
    return task


@app.get("/tasks", response_model=list[Task], dependencies=[Session])
async def list_tasks() -> list[dict[str, Any]]:
    return await database.list_tasks()


@app.get("/tasks/{task_id}", response_model=Task, dependencies=[Session])
async def get_task(task_id: str) -> dict[str, Any]:
    return require_task(await database.get_task(task_id))


@app.patch("/tasks/{task_id}", response_model=Task, dependencies=[Session])
async def update_task(task_id: str, payload: TaskUpdate) -> dict[str, Any]:
    task = await database.update_task_fields(
        task_id,
        payload.title.strip() if payload.title else None,
    )
    task = require_task(task)
    await events.publish("task.updated", task)
    return task


@app.delete("/tasks/{task_id}", dependencies=[Session])
async def delete_task(task_id: str) -> dict[str, object]:
    require_task(await database.get_task(task_id))
    deleted = await orchestrator.delete_task(task_id)
    return {"task_id": task_id, "deleted": deleted}


@app.post(
    "/tasks/{task_id}/sources", response_model=Source, status_code=201, dependencies=[Session]
)
async def add_source(task_id: str, payload: SourceCreate) -> dict[str, Any]:
    require_task(await database.get_task(task_id))
    source = await database.add_source(
        task_id,
        str(payload.url),
        payload.prompt_preset_id,
        payload.output_language,
        payload.custom_title.strip(),
    )
    await events.publish("source.created", source)
    return source


@app.get("/tasks/{task_id}/sources", response_model=list[Source], dependencies=[Session])
async def list_sources(task_id: str) -> list[dict[str, Any]]:
    require_task(await database.get_task(task_id))
    return await database.list_sources(task_id)


@app.get("/tasks/{task_id}/lessons", response_model=list[Source], dependencies=[Session])
async def list_lessons(task_id: str) -> list[dict[str, Any]]:
    return await list_sources(task_id)


@app.post(
    "/tasks/{task_id}/lessons", response_model=Source, status_code=201, dependencies=[Session]
)
async def add_lesson(task_id: str, payload: SourceCreate) -> dict[str, Any]:
    return await add_source(task_id, payload)


@app.patch("/tasks/{task_id}/lessons/{source_id}", response_model=Source, dependencies=[Session])
async def update_lesson(task_id: str, source_id: str, payload: SourceUpdate) -> dict[str, Any]:
    await require_source(task_id, source_id)
    source = await database.update_source_fields(
        source_id,
        custom_title=payload.custom_title.strip() if payload.custom_title is not None else None,
        prompt_preset_id=payload.prompt_preset_id,
        output_language=payload.output_language,
    )
    await events.publish("source.updated", source)
    return source  # type: ignore[return-value]


@app.delete("/tasks/{task_id}/lessons/{source_id}", dependencies=[Session])
async def delete_lesson(task_id: str, source_id: str) -> dict[str, object]:
    await require_source(task_id, source_id)
    return {"source_id": source_id, "deleted": await orchestrator.delete_source(task_id, source_id)}


@app.post("/tasks/{task_id}/check", response_model=CapabilityReport, dependencies=[Session])
async def check_task(
    task_id: str,
    source_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return await orchestrator.check(task_id, source_id)


@app.get(
    "/tasks/{task_id}/capability",
    response_model=CapabilityReport | None,
    dependencies=[Session],
)
async def latest_capability(
    task_id: str, source_id: str | None = Query(default=None)
) -> dict[str, Any] | None:
    require_task(await database.get_task(task_id))
    return await database.latest_capability_report(task_id, source_id)


@app.post("/tasks/{task_id}/run", response_model=TaskControlResponse, dependencies=[Session])
async def run_task(
    task_id: str, source_id: str | None = Query(default=None)
) -> TaskControlResponse:
    require_task(await database.get_task(task_id))
    await orchestrator.start(task_id, source_id)
    return TaskControlResponse(task_id=task_id, status=TaskStatus.WATCHING, message="任务已开始。")


@app.post("/tasks/{task_id}/pause", response_model=TaskControlResponse, dependencies=[Session])
async def pause_task(task_id: str) -> TaskControlResponse:
    require_task(await database.get_task(task_id))
    await orchestrator.pause(task_id)
    return TaskControlResponse(task_id=task_id, status=TaskStatus.PAUSED, message="任务已暂停。")


@app.post("/tasks/{task_id}/resume", response_model=TaskControlResponse, dependencies=[Session])
async def resume_task(task_id: str) -> TaskControlResponse:
    require_task(await database.get_task(task_id))
    await orchestrator.resume(task_id)
    return TaskControlResponse(
        task_id=task_id, status=TaskStatus.WATCHING, message="任务正在继续。"
    )


@app.post("/tasks/{task_id}/stop", response_model=TaskControlResponse, dependencies=[Session])
async def stop_task(task_id: str) -> TaskControlResponse:
    require_task(await database.get_task(task_id))
    await orchestrator.stop(task_id)
    return TaskControlResponse(task_id=task_id, status=TaskStatus.STOPPED, message="任务已停止。")


@app.post("/tasks/{task_id}/regenerate", response_model=TaskControlResponse, dependencies=[Session])
async def regenerate_task_notes(
    task_id: str, source_id: str | None = Query(default=None)
) -> TaskControlResponse:
    require_task(await database.get_task(task_id))
    await orchestrator.regenerate_notes(task_id, source_id)
    return TaskControlResponse(
        task_id=task_id,
        status=TaskStatus.NOTE_TAKING,
        message="已开始基于现有课程文字重新生成速学速记。",
    )


@app.get("/tasks/{task_id}/notes", response_model=list[NoteBlock], dependencies=[Session])
async def get_notes(
    task_id: str, source_id: str | None = Query(default=None)
) -> list[dict[str, Any]]:
    require_task(await database.get_task(task_id))
    return await database.list_notes(task_id, source_id)


@app.get(
    "/tasks/{task_id}/transcript",
    response_model=list[TranscriptSegment],
    dependencies=[Session],
)
async def get_transcript(
    task_id: str, source_id: str | None = Query(default=None)
) -> list[dict[str, Any]]:
    require_task(await database.get_task(task_id))
    return await database.list_transcript(task_id, source_id)


@app.post("/tasks/{task_id}/chat", response_model=ChatResponse, dependencies=[Session])
async def chat(task_id: str, payload: ChatRequest) -> dict[str, Any]:
    return await orchestrator.answer(
        task_id,
        payload.question.strip(),
        payload.conversation_id,
    )


@app.get(
    "/tasks/{task_id}/conversations",
    response_model=list[Conversation],
    dependencies=[Session],
)
async def list_conversations(task_id: str) -> list[dict[str, Any]]:
    require_task(await database.get_task(task_id))
    return await database.list_conversations(task_id)


@app.patch(
    "/tasks/{task_id}/conversations/{conversation_id}",
    response_model=Conversation,
    dependencies=[Session],
)
async def update_conversation(
    task_id: str, conversation_id: str, payload: ConversationUpdate
) -> dict[str, Any]:
    require_task(await database.get_task(task_id))
    if not await database.conversation_belongs_to_task(conversation_id, task_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation = await database.update_conversation_title(conversation_id, payload.title.strip())
    return conversation  # type: ignore[return-value]


@app.delete("/tasks/{task_id}/conversations/{conversation_id}", dependencies=[Session])
async def delete_conversation(task_id: str, conversation_id: str) -> dict[str, object]:
    require_task(await database.get_task(task_id))
    if not await database.conversation_belongs_to_task(conversation_id, task_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "conversation_id": conversation_id,
        "deleted": await database.delete_conversation(conversation_id),
    }


@app.delete("/tasks/{task_id}/conversations", dependencies=[Session])
async def clear_conversations(task_id: str) -> dict[str, int]:
    require_task(await database.get_task(task_id))
    return {"deleted": await database.delete_task_conversations(task_id)}


@app.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[Message],
    dependencies=[Session],
)
async def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    return await database.list_messages(conversation_id)


@app.post("/tasks/{task_id}/export", response_model=ExportResponse, dependencies=[Session])
async def export_task(task_id: str, source_id: str | None = Query(default=None)) -> ExportResponse:
    path = await orchestrator.export_markdown(task_id, source_id)
    return ExportResponse(path=str(path))


@app.get("/events", dependencies=[Session])
async def event_stream() -> StreamingResponse:
    return StreamingResponse(
        events.subscribe(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
