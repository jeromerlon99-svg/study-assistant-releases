from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path
from typing import Any

from .config import Settings


class LocalTranscriptionError(RuntimeError):
    pass


class LocalTranscriber:
    """Lazily downloads and runs faster-whisper entirely on the local machine."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: Any | None = None
        self._loaded_model_name = ""
        self._load_lock = asyncio.Lock()

    @property
    def runtime_available(self) -> bool:
        return importlib.util.find_spec("faster_whisper") is not None

    @property
    def model_name(self) -> str:
        return self.settings.local_whisper_model

    @property
    def model_dir(self) -> Path:
        return self.settings.whisper_models_dir / self.model_name

    @property
    def model_downloaded(self) -> bool:
        return (self.model_dir / "model.bin").is_file() and (
            self.model_dir / "config.json"
        ).is_file()

    def public_status(self) -> dict[str, object]:
        return {
            "runtime_available": self.runtime_available,
            "model": self.model_name,
            "model_downloaded": self.model_downloaded,
            "model_dir": str(self.model_dir),
            "device": "cpu",
            "compute_type": "int8",
        }

    async def ensure_model(self) -> Any:
        if self._model is not None and self._loaded_model_name == self.model_name:
            return self._model
        async with self._load_lock:
            if self._model is not None and self._loaded_model_name == self.model_name:
                return self._model
            try:
                model = await asyncio.to_thread(self._load_model_sync)
            except Exception as error:
                raise LocalTranscriptionError(
                    f"本地转写模型下载或加载失败。请检查网络、磁盘空间后重试：{error}"
                ) from error
            self._model = model
            self._loaded_model_name = self.model_name
            return model

    def _load_model_sync(self) -> Any:
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model

        target = self.model_dir
        target.parent.mkdir(parents=True, exist_ok=True)
        if not self.model_downloaded:
            target.mkdir(parents=True, exist_ok=True)
            download_model(self.model_name, output_dir=str(target))
        cpu_threads = min(8, max(1, (os.cpu_count() or 2) // 2))
        return WhisperModel(
            str(target),
            device="cpu",
            compute_type="int8",
            cpu_threads=cpu_threads,
        )

    async def transcribe(
        self, media_path: Path, language: str | None = None
    ) -> list[dict[str, Any]]:
        if not self.runtime_available:
            raise LocalTranscriptionError(
                "当前程序未包含 faster-whisper 本地转写运行库，请重新安装完整发布版。"
            )
        model = await self.ensure_model()
        language_code = language.lower().split("-")[0] if language else None

        def run() -> list[dict[str, Any]]:
            segments, _ = model.transcribe(
                str(media_path),
                language=language_code,
                beam_size=5,
                vad_filter=True,
            )
            return [
                {
                    "start_seconds": float(segment.start),
                    "end_seconds": float(segment.end),
                    "speaker": "",
                    "content": str(segment.text).strip(),
                    "confidence": None,
                }
                for segment in segments
                if str(segment.text).strip()
            ]

        try:
            return await asyncio.to_thread(run)
        except Exception as error:
            raise LocalTranscriptionError(f"本地语音转写失败：{error}") from error
