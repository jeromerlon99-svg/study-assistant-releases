from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TaskStatus(StrEnum):
    IDLE = "IDLE"
    CHECKING = "CHECKING"
    WATCHING = "WATCHING"
    TRANSCRIBING = "TRANSCRIBING"
    NOTE_TAKING = "NOTE_TAKING"
    NEEDS_USER = "NEEDS_USER"
    PAUSED = "PAUSED"
    READY_FOR_QA = "READY_FOR_QA"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class CapabilityStatus(StrEnum):
    READY = "READY"
    LIMITED = "LIMITED"
    NEEDS_USER = "NEEDS_USER"
    UNSUPPORTED = "UNSUPPORTED"


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    language: str = Field(default="zh-CN", max_length=32)


class TaskUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)


class Task(ApiModel):
    id: str
    title: str
    status: TaskStatus
    language: str
    progress: float
    status_detail: str
    created_at: str
    updated_at: str
    lesson_count: int = 0
    completed_lessons: int = 0


class SourceCreate(ApiModel):
    url: HttpUrl
    custom_title: str = Field(default="", max_length=200)
    prompt_preset_id: Literal["quick", "standard", "deep"] = "standard"
    output_language: Literal["auto", "zh-CN", "en", "de"] = "auto"


class SourceUpdate(ApiModel):
    custom_title: str | None = Field(default=None, max_length=200)
    prompt_preset_id: Literal["quick", "standard", "deep"] | None = None
    output_language: Literal["auto", "zh-CN", "en", "de"] | None = None


class LessonCandidate(ApiModel):
    url: str
    title: str = ""


class Source(ApiModel):
    id: str
    task_id: str
    url: str
    title: str
    custom_title: str = ""
    platform: str
    duration_seconds: float | None
    lesson_index: int
    status: TaskStatus
    progress: float
    status_detail: str
    prompt_preset_id: Literal["quick", "standard", "deep"]
    prompt_version: str
    output_language: Literal["auto", "zh-CN", "en", "de"]
    created_at: str


class CapabilityReport(ApiModel):
    id: str
    task_id: str
    source_id: str
    status: CapabilityStatus
    page_accessible: bool
    video_detected: bool
    captions_available: bool
    audio_available: bool
    drm_detected: bool
    login_required: bool
    text_model_available: bool
    transcription_available: bool
    duration_seconds: float | None = None
    estimated_minutes: float | None = None
    reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class NoteBlock(ApiModel):
    id: str
    task_id: str
    source_id: str | None
    kind: str
    title: str
    content: str
    start_seconds: float | None
    end_seconds: float | None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    prompt_preset_id: str = "standard"
    prompt_version: str = "1.1"
    output_language: str = "auto"
    created_at: str


class TranscriptSegment(ApiModel):
    id: str
    task_id: str
    source_id: str
    start_seconds: float
    end_seconds: float
    speaker: str
    content: str
    confidence: float | None
    created_at: str


class ChatRequest(ApiModel):
    question: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None


class Citation(ApiModel):
    source_type: Literal["course", "external"]
    title: str
    url: str | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    excerpt: str = ""
    source_id: str | None = None
    lesson_index: int | None = None


class ChatResponse(ApiModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: list[Citation]
    course_evidence_found: bool
    retrieval_queries: list[str] = Field(default_factory=list)
    course_evidence_count: int = 0


class Conversation(ApiModel):
    id: str
    task_id: str
    title: str
    created_at: str
    updated_at: str


class ConversationUpdate(ApiModel):
    title: str = Field(min_length=1, max_length=200)


class Message(ApiModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str


class ProviderSettingsUpdate(ApiModel):
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    text_model: str = ""
    reasoning_effort: Literal["low", "high", "max"] = "low"
    local_whisper_model: Literal["small", "medium", "large-v3"] = "small"


class ProviderSelfTest(ApiModel):
    text: bool
    transcription_configured: bool
    message: str


class SemanticStatus(ApiModel):
    state: Literal[
        "NOT_READY", "DOWNLOADING", "PREPARING", "INDEXING", "READY", "FAILED"
    ]
    model: str
    model_revision: str
    runtime_available: bool
    model_downloaded: bool
    progress: float
    indexed_sources: int
    pending_sources: int
    indexed_chunks: int
    message: str


class TaskControlResponse(ApiModel):
    task_id: str
    status: TaskStatus
    message: str


class ExportResponse(ApiModel):
    path: str


class PreferencesUpdate(ApiModel):
    ui_language: Literal["zh-CN", "en", "de"]
