from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from .config import Settings

if TYPE_CHECKING:
    from .database import Database
    from .events import EventHub

logger = logging.getLogger(__name__)

MODEL_ID = "intfloat/multilingual-e5-small"
MODEL_REVISION = "761b726dd34fb83930e26aab4e9ac3899aa1fa78"
ARTIFACT_REPO_ID = "Xenova/multilingual-e5-small"
MODEL_SHA256 = "4d24e2bc01a447951524466ef533e52944bf48509e6552810bcee1a2711cb02c"
MODEL_DIMENSION = 384
MODEL_MAX_TOKENS = 512
CHUNK_TARGET_TOKENS = 320
CHUNK_OVERLAP_TOKENS = 48
MODEL_FILES = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
    "onnx/model_int8.onnx",
)


class EmbeddingRuntime(Protocol):
    @property
    def runtime_available(self) -> bool: ...

    @property
    def model_downloaded(self) -> bool: ...

    async def ensure_ready(
        self, progress: Callable[[float, str], None] | None = None
    ) -> None: ...

    async def encode(self, texts: list[str], *, query: bool) -> Any: ...

    def token_count(self, text: str) -> int: ...


class LocalEmbeddingModel:
    """Pinned multilingual E5 model running locally through ONNX Runtime."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session: Any | None = None
        self._tokenizer: Any | None = None
        self._load_lock = asyncio.Lock()
        self._manifest_validated = False

    @property
    def model_dir(self) -> Path:
        return self.settings.embedding_models_dir / "multilingual-e5-small" / MODEL_REVISION

    @property
    def quantized_model_path(self) -> Path:
        return self.model_dir / "model.int8.onnx"

    @property
    def tokenizer_path(self) -> Path:
        return self.model_dir / "tokenizer.json"

    @property
    def manifest_path(self) -> Path:
        return self.model_dir / "model-manifest.json"

    @property
    def runtime_available(self) -> bool:
        return all(
            importlib.util.find_spec(name) is not None
            for name in ("numpy", "onnxruntime", "tokenizers")
        )

    @property
    def model_downloaded(self) -> bool:
        if not (
            self.quantized_model_path.is_file()
            and self.tokenizer_path.is_file()
            and self.manifest_path.is_file()
        ):
            return False
        if self._manifest_validated:
            return True
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            valid = (
                manifest.get("model_id") == MODEL_ID
                and manifest.get("model_revision") == MODEL_REVISION
                and manifest.get("dimension") == MODEL_DIMENSION
                and manifest.get("model_sha256")
                == self._sha256(self.quantized_model_path)
                and manifest.get("tokenizer_sha256") == self._sha256(self.tokenizer_path)
            )
            self._manifest_validated = valid
            return valid
        except (OSError, json.JSONDecodeError):
            return False

    async def ensure_ready(
        self, progress: Callable[[float, str], None] | None = None
    ) -> None:
        if self._session is not None and self._tokenizer is not None:
            return
        async with self._load_lock:
            if self._session is not None and self._tokenizer is not None:
                return
            if not self.runtime_available:
                raise RuntimeError("本地语义检索运行库不完整，请重新安装完整发布版。")
            if not self.model_downloaded:
                await asyncio.to_thread(self._prepare_model_sync, progress)
            await asyncio.to_thread(self._load_sync)

    def _prepare_model_sync(self, progress: Callable[[float, str], None] | None) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        for path in self.model_dir.glob("*.part"):
            path.unlink(missing_ok=True)
        download_dir = self.model_dir / "download"
        hub_cache = self.model_dir / ".hub-cache"
        download_dir.mkdir(parents=True, exist_ok=True)
        for attempt in range(2):
            try:
                self._download_model_sync(download_dir, progress)
                source_model = download_dir / "onnx" / "model_int8.onnx"
                if self._sha256(source_model) != MODEL_SHA256:
                    raise RuntimeError("语义模型文件校验失败。")
                temporary_model = self.quantized_model_path.with_suffix(".onnx.part")
                temporary_model.write_bytes(source_model.read_bytes())
                os.replace(temporary_model, self.quantized_model_path)
                source_tokenizer = download_dir / "tokenizer.json"
                self.tokenizer_path.write_bytes(source_tokenizer.read_bytes())
                manifest = {
                    "model_id": MODEL_ID,
                    "model_revision": MODEL_REVISION,
                    "dimension": MODEL_DIMENSION,
                    "artifact_repo": ARTIFACT_REPO_ID,
                    "format": "onnx-int8",
                    "model_sha256": self._sha256(self.quantized_model_path),
                    "tokenizer_sha256": self._sha256(self.tokenizer_path),
                }
                temporary_manifest = self.manifest_path.with_suffix(".json.part")
                temporary_manifest.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                os.replace(temporary_manifest, self.manifest_path)
                self._manifest_validated = True
                self._remove_tree(download_dir)
                self._remove_tree(hub_cache)
                if progress:
                    progress(0.82, "本地语义模型准备完成")
                return
            except Exception:
                self._remove_tree(download_dir)
                self.quantized_model_path.unlink(missing_ok=True)
                self.tokenizer_path.unlink(missing_ok=True)
                self.manifest_path.unlink(missing_ok=True)
                if attempt:
                    self._remove_tree(hub_cache)
                    raise
                download_dir.mkdir(parents=True, exist_ok=True)

    def _download_model_sync(
        self, download_dir: Path, progress: Callable[[float, str], None] | None
    ) -> None:
        from huggingface_hub import hf_hub_download

        hub_cache = self.model_dir / ".hub-cache"
        for index, remote_name in enumerate(MODEL_FILES):
            if progress:
                progress(index / len(MODEL_FILES) * 0.68, "正在下载本地语义模型")
            destination = Path(
                hf_hub_download(
                    repo_id=ARTIFACT_REPO_ID,
                    filename=remote_name,
                    revision=MODEL_REVISION,
                    cache_dir=hub_cache,
                    local_dir=download_dir,
                )
            )
            if not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError(f"模型文件下载为空：{remote_name}")
        if progress:
            progress(0.68, "本地语义模型下载完成")

    def _load_sync(self) -> None:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        tokenizer = Tokenizer.from_file(str(self.tokenizer_path))
        tokenizer.enable_truncation(max_length=MODEL_MAX_TOKENS)
        tokenizer.enable_padding(pad_id=1, pad_token="<pad>")
        options = ort.SessionOptions()
        options.intra_op_num_threads = min(8, max(1, (os.cpu_count() or 2) // 2))
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._tokenizer = tokenizer
        self._session = ort.InferenceSession(
            str(self.quantized_model_path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

    async def encode(self, texts: list[str], *, query: bool) -> Any:
        await self.ensure_ready()
        return await asyncio.to_thread(self._encode_sync, texts, query)

    def _encode_sync(self, texts: list[str], query: bool) -> Any:
        import numpy as np

        if self._tokenizer is None or self._session is None:
            raise RuntimeError("本地语义模型尚未加载。")
        prefix = "query: " if query else "passage: "
        encoded = self._tokenizer.encode_batch([prefix + text for text in texts])
        input_ids = np.asarray([item.ids for item in encoded], dtype=np.int64)
        attention_mask = np.asarray([item.attention_mask for item in encoded], dtype=np.int64)
        type_ids = np.asarray([item.type_ids for item in encoded], dtype=np.int64)
        available = {item.name for item in self._session.get_inputs()}
        feed: dict[str, Any] = {}
        if "input_ids" in available:
            feed["input_ids"] = input_ids
        if "attention_mask" in available:
            feed["attention_mask"] = attention_mask
        if "token_type_ids" in available:
            feed["token_type_ids"] = type_ids
        hidden = self._session.run(None, feed)[0]
        mask = attention_mask[..., None].astype(np.float32)
        pooled = (hidden * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        return (pooled / np.clip(norms, 1e-9, None)).astype(np.float32)

    def token_count(self, text: str) -> int:
        if self._tokenizer is None:
            return max(1, len(text) // 2)
        return len(self._tokenizer.encode(text, add_special_tokens=True).ids)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _remove_tree(path: Path) -> None:
        if not path.exists():
            return
        for child in sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        path.rmdir()


class SemanticSearch:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        events: EventHub,
        runtime: EmbeddingRuntime | None = None,
    ) -> None:
        self.settings = settings
        self.database = database
        self.events = events
        self.runtime = runtime or LocalEmbeddingModel(settings)
        self._state = "NOT_READY"
        self._progress = 0.0
        self._message = "等待初始化本地语义检索"
        self._tasks: set[asyncio.Task[Any]] = set()
        self._index_locks: dict[str, asyncio.Lock] = {}

    async def start(self) -> None:
        if self.settings.semantic_auto_initialize:
            self._track(asyncio.create_task(self.initialize_all()))

    async def close(self) -> None:
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def schedule_source(self, task_id: str, source_id: str) -> None:
        self._track(asyncio.create_task(self.initialize_source(task_id, source_id)))

    def _track(self, task: asyncio.Task[Any]) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def initialize_all(self) -> None:
        try:
            await self._ensure_runtime()
            sources = await self.database.list_sources_with_transcript()
            for index, source in enumerate(sources):
                self._state = "INDEXING"
                self._progress = 0.82 + (index / max(1, len(sources))) * 0.17
                self._message = "正在为已有课程建立本地语义索引"
                await self._publish()
                await self._index_source(source["task_id"], source["id"])
            self._state = "READY"
            self._progress = 1.0
            self._message = "本地语义检索已就绪"
            await self._publish()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.exception("Semantic initialization failed")
            self._state = "FAILED"
            self._message = f"本地语义检索初始化失败：{error}"
            await self._publish()

    async def initialize_source(self, task_id: str, source_id: str) -> None:
        try:
            await self._ensure_runtime()
            self._state = "INDEXING"
            self._message = "正在更新课程语义索引"
            await self._publish()
            await self._index_source(task_id, source_id)
            self._state = "READY"
            self._progress = 1.0
            self._message = "本地语义检索已就绪"
            await self._publish()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.exception("Semantic source indexing failed")
            self._state = "FAILED"
            self._message = f"课程语义索引失败：{error}"
            await self._publish()

    async def _ensure_runtime(self) -> None:
        if self._state == "READY" and self.runtime.model_downloaded:
            return
        self._state = "DOWNLOADING" if not self.runtime.model_downloaded else "PREPARING"
        self._message = (
            "正在下载内置多语言语义模型"
            if not self.runtime.model_downloaded
            else "正在加载本地语义模型"
        )
        await self._publish()
        loop = asyncio.get_running_loop()

        def progress(value: float, message: str) -> None:
            loop.call_soon_threadsafe(self._set_progress_from_thread, value, message)

        await self.runtime.ensure_ready(progress)
        self._progress = max(self._progress, 0.82)

    def _set_progress_from_thread(self, value: float, message: str) -> None:
        self._progress = max(0.0, min(0.82, value))
        self._message = message
        self._track(asyncio.create_task(self._publish()))

    async def _index_source(self, task_id: str, source_id: str) -> None:
        lock = self._index_locks.setdefault(source_id, asyncio.Lock())
        async with lock:
            transcript = await self.database.list_transcript(task_id, source_id)
            if not transcript:
                return
            transcript_hash = self._transcript_hash(transcript)
            state = await self.database.get_semantic_source_state(source_id)
            if (
                state
                and state["transcript_hash"] == transcript_hash
                and state["model_revision"] == MODEL_REVISION
            ):
                return
            chunks = self._chunk_transcript(transcript)
            vectors = await self.runtime.encode([item["content"] for item in chunks], query=False)
            rows: list[dict[str, Any]] = []
            for chunk, vector in zip(chunks, vectors, strict=True):
                rows.append(
                    {
                        **chunk,
                        "id": hashlib.sha256(
                            f"{source_id}:{chunk['content_hash']}".encode()
                        ).hexdigest(),
                        "task_id": task_id,
                        "source_id": source_id,
                        "model_id": MODEL_ID,
                        "model_revision": MODEL_REVISION,
                        "dimension": MODEL_DIMENSION,
                        "vector": vector.tobytes(),
                    }
                )
            await self.database.replace_semantic_index(
                task_id,
                source_id,
                transcript_hash,
                MODEL_ID,
                MODEL_REVISION,
                rows,
            )

    async def search(
        self,
        task_id: str,
        question: str,
        expanded_queries: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if self._state != "READY":
            return []
        rows = await self.database.list_semantic_chunks(task_id, MODEL_REVISION)
        if not rows:
            return []
        import numpy as np

        queries = [question, *(expanded_queries or [])[:6]]
        query_vectors = await self.runtime.encode(queries, query=True)
        matrix = np.vstack(
            [np.frombuffer(row.pop("vector"), dtype=np.float32) for row in rows]
        )
        scores = (matrix @ query_vectors.T).mean(axis=1)
        order = np.argsort(-scores)[:limit]
        result: list[dict[str, Any]] = []
        for rank in order:
            row = rows[int(rank)]
            row["semantic_score"] = float(scores[int(rank)])
            result.append(row)
        return result

    async def public_status(self) -> dict[str, object]:
        counts = await self.database.semantic_status_counts(MODEL_REVISION)
        return {
            "state": self._state,
            "model": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "runtime_available": self.runtime.runtime_available,
            "model_downloaded": self.runtime.model_downloaded,
            "progress": self._progress,
            "indexed_sources": counts["indexed_sources"],
            "pending_sources": counts["pending_sources"],
            "indexed_chunks": counts["indexed_chunks"],
            "message": self._message,
        }

    async def _publish(self) -> None:
        await self.events.publish("semantic.status", await self.public_status())

    def _chunk_transcript(self, transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        current: list[dict[str, Any]] = []
        for segment in transcript:
            candidate = [*current, segment]
            candidate_text = " ".join(str(item["content"]).strip() for item in candidate)
            if current and self.runtime.token_count(candidate_text) > CHUNK_TARGET_TOKENS:
                chunks.append(self._make_chunk(current))
                overlap: list[dict[str, Any]] = []
                for previous in reversed(current):
                    possible = [previous, *overlap]
                    text = " ".join(str(item["content"]).strip() for item in possible)
                    if overlap and self.runtime.token_count(text) > CHUNK_OVERLAP_TOKENS:
                        break
                    overlap = possible
                current = overlap
            current.append(segment)
        if current:
            chunk = self._make_chunk(current)
            if not chunks or chunk["content_hash"] != chunks[-1]["content_hash"]:
                chunks.append(chunk)
        return chunks

    @staticmethod
    def _make_chunk(segments: list[dict[str, Any]]) -> dict[str, Any]:
        content = " ".join(str(item["content"]).strip() for item in segments).strip()
        fingerprint = (
            f"{float(segments[0]['start_seconds']):.3f}:"
            f"{float(segments[-1]['end_seconds']):.3f}:{content}"
        )
        return {
            "start_seconds": float(segments[0]["start_seconds"]),
            "end_seconds": float(segments[-1]["end_seconds"]),
            "content": content,
            "content_hash": hashlib.sha256(fingerprint.encode("utf-8")).hexdigest(),
        }

    @staticmethod
    def _transcript_hash(transcript: list[dict[str, Any]]) -> str:
        digest = hashlib.sha256()
        for item in transcript:
            digest.update(
                (
                    f"{float(item['start_seconds']):.3f}|{float(item['end_seconds']):.3f}|"
                    f"{str(item['content']).strip()}\n"
                ).encode()
            )
        return digest.hexdigest()
