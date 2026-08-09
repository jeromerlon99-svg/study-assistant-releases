from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root() -> Path:
    starts = (Path.cwd(), Path(__file__).resolve().parent, Path(sys.executable).resolve().parent)
    for start in starts:
        for candidate in (start, *start.parents):
            if (
                (candidate / "VERSION").is_file()
                and (candidate / "apps").is_dir()
                and (candidate / "services").is_dir()
            ):
                return candidate
    return Path.cwd()


def default_data_dir() -> Path:
    if configured := os.getenv("STUDY_ASSISTANT_DATA_DIR"):
        return Path(configured).expanduser().resolve()
    return _find_project_root() / "runtime-data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STUDY_ASSISTANT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "INFO"
    session_token: str = ""
    data_dir: Path = Field(default_factory=default_data_dir)

    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    text_model: str = ""
    reasoning_effort: Literal["low", "high", "max"] = "low"
    local_whisper_model: Literal["small", "medium", "large-v3"] = "small"
    semantic_auto_initialize: bool = True

    # Long reasoning models can legitimately take several minutes to finish a
    # course-note response. Connection setup still uses a separate short limit.
    request_timeout_seconds: float = 600.0
    media_timeout_seconds: float = 1800.0
    max_course_bytes: int = 4 * 1024 * 1024 * 1024
    chunk_seconds: int = 300

    @property
    def database_path(self) -> Path:
        return self.data_dir / "study-assistant.db"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def whisper_models_dir(self) -> Path:
        return self.data_dir / "models" / "faster-whisper"

    @property
    def embedding_models_dir(self) -> Path:
        return self.data_dir / "models" / "embedding"

    @property
    def provider_config_path(self) -> Path:
        return self.data_dir / "provider.json"

    @property
    def preferences_path(self) -> Path:
        return self.data_dir / "preferences.json"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_models_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_models_dir.mkdir(parents=True, exist_ok=True)

    def public_dict(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "data_dir": str(self.data_dir),
            "api_base_url": self.api_base_url,
            "text_model": self.text_model,
            "reasoning_effort": self.reasoning_effort,
            "local_whisper_model": self.local_whisper_model,
            "has_api_key": bool(self.api_key),
        }

    def load_non_secret_provider_config(self) -> None:
        if not self.provider_config_path.exists():
            return
        try:
            payload = json.loads(self.provider_config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for field in (
            "api_base_url",
            "text_model",
            "reasoning_effort",
            "local_whisper_model",
        ):
            value = payload.get(field)
            if isinstance(value, str):
                setattr(self, field, value.strip())

    def load_preferences(self) -> dict[str, str]:
        defaults = {"ui_language": "zh-CN"}
        if not self.preferences_path.exists():
            return defaults
        try:
            payload = json.loads(self.preferences_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return defaults
        language = payload.get("ui_language")
        if language in {"zh-CN", "en", "de"}:
            defaults["ui_language"] = language
        return defaults

    def save_preferences(self, ui_language: str) -> dict[str, str]:
        payload = {"ui_language": ui_language}
        self.preferences_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return payload


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    settings.load_non_secret_provider_config()
    return settings
