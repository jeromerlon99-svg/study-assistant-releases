from __future__ import annotations

import asyncio
import html
import ipaddress
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from . import __version__
from .config import Settings

TIMESTAMP = re.compile(
    r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2}(?:[.,]\d+)?)|(?P<m2>\d{1,2}):(?P<s2>\d{2}(?:[.,]\d+)?)"
)
TAG = re.compile(r"<[^>]+>")
INCOMPLETE_DOWNLOAD = re.compile(
    r"(?:Downloaded\s+\d+\s+bytes,\s*expected\s+\d+\s+bytes|"
    r"content too short\s*\(expected\s+\d+\s+bytes and served\s+\d+\))",
    re.IGNORECASE,
)


class CourseError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(slots=True)
class Inspection:
    title: str = ""
    platform: str = "web"
    duration_seconds: float | None = None
    page_accessible: bool = False
    video_detected: bool = False
    captions_available: bool = False
    audio_available: bool = False
    drm_detected: bool = False
    login_required: bool = False
    caption_tracks: list[dict[str, str]] = field(default_factory=list)
    extractor: str = ""
    content_type: str = ""
    reasons: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def _seconds(value: re.Match[str]) -> float:
    if value.group("h") is not None:
        return (
            int(value.group("h")) * 3600
            + int(value.group("m")) * 60
            + float(value.group("s").replace(",", "."))
        )
    return int(value.group("m2")) * 60 + float(value.group("s2").replace(",", "."))


def parse_subtitles(text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    blocks = re.split(r"\r?\n\s*\r?\n", text.replace("\ufeff", ""))
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or lines[0].upper().startswith(("WEBVTT", "NOTE", "STYLE")):
            continue
        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        timing = lines[timing_index]
        parts = timing.split("-->", 1)
        start_match = TIMESTAMP.search(parts[0])
        end_match = TIMESTAMP.search(parts[1])
        if not start_match or not end_match:
            continue
        content_lines = lines[timing_index + 1 :]
        content = " ".join(content_lines)
        content = html.unescape(TAG.sub("", content))
        content = re.sub(r"\s+", " ", content).strip()
        if not content:
            continue
        start = _seconds(start_match)
        end = max(start, _seconds(end_match))
        if segments and segments[-1]["content"] == content:
            segments[-1]["end_seconds"] = max(segments[-1]["end_seconds"], end)
            continue
        segments.append({"start_seconds": start, "end_seconds": end, "content": content})
    return segments


class CourseInspector:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise CourseError("INVALID_URL", "只支持公开的 http 或 https 课程网址。")
        host = (parsed.hostname or "").lower()
        if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
            raise CourseError("PRIVATE_URL", "课程网址不能指向本机或内网地址。")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return
        if not address.is_global:
            raise CourseError("PRIVATE_URL", "课程网址不能指向本机或内网地址。")

    async def inspect(self, url: str) -> Inspection:
        self.validate_url(url)
        inspection = Inspection(platform=(urlparse(url).hostname or "web").removeprefix("www."))
        await self._inspect_page(url, inspection)
        await self._inspect_with_ytdlp(url, inspection)
        if inspection.drm_detected:
            inspection.reasons.append("检测到 DRM 或加密媒体标记，程序不会尝试绕过。")
            inspection.suggestions.append("请使用课程平台提供的官方字幕或讲稿。")
        if inspection.login_required:
            inspection.reasons.append("页面要求登录或出现访问验证。")
            inspection.suggestions.append("请确认课程是公开内容，或稍后使用人工协助模式。")
        if not inspection.video_detected:
            inspection.reasons.append("未定位到可处理的视频或音频。")
            inspection.suggestions.append("请确认网址直接指向课程播放页。")
        if inspection.video_detected and not inspection.captions_available:
            inspection.reasons.append("未发现可直接读取的字幕，将需要语音转写能力。")
        return inspection

    async def discover_lessons(self, url: str, limit: int = 200) -> list[dict[str, str]]:
        """Return flat playlist entries, or the original URL when it is a single lesson."""
        self.validate_url(url)

        def extract() -> dict[str, Any] | None:
            options = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": "in_playlist",
                "noplaylist": False,
                "playlistend": limit,
                "socket_timeout": 25,
            }
            with YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.to_thread(extract)
        except Exception:  # noqa: BLE001
            return [{"url": url, "title": ""}]
        if not info or info.get("_type") not in {"playlist", "multi_video"}:
            return [{"url": url, "title": str((info or {}).get("title") or "")}]
        results: list[dict[str, str]] = []
        for index, entry in enumerate(info.get("entries", [])):
            if index >= limit:
                break
            if not entry:
                continue
            entry_url = str(
                entry.get("webpage_url") or entry.get("original_url") or entry.get("url") or ""
            )
            if not entry_url.startswith(("http://", "https://")):
                continue
            results.append({"url": entry_url, "title": str(entry.get("title") or "")})
        return results or [{"url": url, "title": str(info.get("title") or "")}]

    async def _inspect_page(self, url: str, inspection: Inspection) -> None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                f"AppleWebKit/537.36 Chrome/124 Safari/537.36 StudyAssistant/{__version__}"
            )
        }
        try:
            async with (
                httpx.AsyncClient(
                    timeout=20,
                    follow_redirects=True,
                    headers=headers,
                ) as client,
                client.stream("GET", url) as response,
            ):
                inspection.content_type = response.headers.get("content-type", "")
                inspection.page_accessible = response.status_code < 400
                if response.status_code in {401, 403}:
                    inspection.login_required = True
                if response.is_error:
                    inspection.reasons.append(f"网页返回 HTTP {response.status_code}。")
                    return
                if inspection.content_type.startswith(("video/", "audio/")):
                    inspection.video_detected = True
                    inspection.audio_available = True
                    inspection.title = Path(urlparse(str(response.url)).path).name or "公开课程"
                    inspection.raw["direct_media_url"] = str(response.url)
                    return
                chunks: list[bytes] = []
                received = 0
                async for chunk in response.aiter_bytes():
                    remaining = 5_000_000 - received
                    if remaining <= 0:
                        break
                    chunks.append(chunk[:remaining])
                    received += min(len(chunk), remaining)
                text = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
                final_url = response.url
        except httpx.HTTPError as error:
            inspection.reasons.append(f"网页访问失败：{error}")
            return
        lowered = text.lower()
        soup = BeautifulSoup(text, "html.parser")
        if soup.title and soup.title.string:
            inspection.title = soup.title.string.strip()
        inspection.video_detected = bool(
            soup.find("video")
            or soup.find("audio")
            or soup.find("iframe")
            or "application/vnd.apple.mpegurl" in lowered
            or ".m3u8" in lowered
            or ".mpd" in lowered
        )
        inspection.audio_available = bool(soup.find("video") or soup.find("audio"))
        for track in soup.select("track[kind='captions'], track[kind='subtitles']"):
            source = track.get("src")
            if source:
                inspection.caption_tracks.append(
                    {
                        "url": str(final_url.join(source)),
                        "language": track.get("srclang", ""),
                        "name": track.get("label", "网页字幕"),
                    }
                )
        inspection.captions_available = bool(inspection.caption_tracks)
        inspection.login_required = inspection.login_required or any(
            token in lowered
            for token in ("sign in to continue", "login required", "请登录", "登录后观看")
        )
        inspection.drm_detected = any(
            token in lowered
            for token in (
                "widevine",
                "fairplay",
                "playready",
                "encrypted-media",
                "com.widevine.alpha",
            )
        )

    async def _inspect_with_ytdlp(self, url: str, inspection: Inspection) -> None:
        def extract() -> dict[str, Any] | None:
            options = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "noplaylist": True,
                "socket_timeout": 25,
            }
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
            if info and info.get("_type") in {"playlist", "multi_video"}:
                entries = [entry for entry in info.get("entries", []) if entry]
                return entries[0] if entries else info
            return info

        try:
            info = await asyncio.to_thread(extract)
        except DownloadError as error:
            message = str(error)
            if any(token in message.lower() for token in ("login", "cookies", "sign in")):
                inspection.login_required = True
            inspection.raw["extractor_error"] = message[:1000]
            return
        # Extractor plugins may raise provider-specific exception types that are
        # not part of yt-dlp's public exception hierarchy. Inspection must degrade
        # to a capability report instead of crashing the local service.
        except Exception as error:  # noqa: BLE001
            inspection.raw["extractor_error"] = str(error)[:1000]
            return
        if not info:
            return
        inspection.extractor = str(info.get("extractor_key") or info.get("extractor") or "")
        inspection.platform = inspection.extractor or inspection.platform
        inspection.title = str(info.get("title") or inspection.title or "公开课程")
        duration = info.get("duration")
        if isinstance(duration, (int, float)):
            inspection.duration_seconds = float(duration)
        formats = info.get("formats") or []
        inspection.video_detected = inspection.video_detected or bool(formats or info.get("url"))
        inspection.audio_available = inspection.audio_available or any(
            fmt.get("acodec") not in {None, "none"} for fmt in formats if isinstance(fmt, dict)
        )
        for source_name in ("subtitles", "automatic_captions"):
            subtitle_map = info.get(source_name) or {}
            for language, tracks in subtitle_map.items():
                for track in tracks or []:
                    track_url = track.get("url")
                    if not track_url:
                        continue
                    inspection.caption_tracks.append(
                        {
                            "url": str(track_url),
                            "language": str(language),
                            "name": "官方字幕" if source_name == "subtitles" else "自动字幕",
                            "format": str(track.get("ext", "")),
                        }
                    )
        inspection.captions_available = bool(inspection.caption_tracks)
        inspection.drm_detected = inspection.drm_detected or bool(info.get("has_drm"))
        inspection.raw["webpage_url"] = info.get("webpage_url")
        inspection.raw["extractor"] = inspection.extractor

    async def fetch_best_caption(
        self, inspection: Inspection, preferred_language: str
    ) -> list[dict[str, Any]]:
        if not inspection.caption_tracks:
            return []
        language = preferred_language.lower().split("-")[0]

        def score(track: dict[str, str]) -> tuple[int, int]:
            track_language = track.get("language", "").lower()
            ext = track.get("format", "")
            return (
                0
                if track_language == preferred_language.lower()
                else 1
                if track_language.startswith(language)
                else 2,
                0 if ext in {"vtt", "srt"} else 1,
            )

        headers = {"User-Agent": f"Mozilla/5.0 StudyAssistant/{__version__}"}
        async with httpx.AsyncClient(timeout=45, follow_redirects=True, headers=headers) as client:
            for track in sorted(inspection.caption_tracks, key=score):
                try:
                    response = await client.get(track["url"])
                    response.raise_for_status()
                except httpx.HTTPError:
                    continue
                segments = parse_subtitles(response.text)
                if segments:
                    return segments
        return []

    async def download_audio(self, url: str, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(output_dir / "course-audio.%(ext)s")

        def download() -> Path:
            options = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "max_filesize": self.settings.max_course_bytes,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "overwrites": True,
            }
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                requested = info.get("requested_downloads") or []
                if requested and requested[0].get("filepath"):
                    return Path(requested[0]["filepath"])
                return Path(ydl.prepare_filename(info))

        path: Path | None = None
        for attempt in range(2):
            try:
                path = await asyncio.to_thread(download)
                break
            except DownloadError as error:
                incomplete = bool(INCOMPLETE_DOWNLOAD.search(str(error)))
                await asyncio.to_thread(self._delete_audio_download_artifacts, output_dir)
                if incomplete and attempt == 0:
                    continue
                if incomplete:
                    raise CourseError(
                        "MEDIA_DOWNLOAD_INCOMPLETE",
                        "课程媒体下载不完整。程序已删除残缺临时文件并从头重试 1 次，"
                        "但仍未成功；请检查网络连接后点击继续。",
                    ) from error
                raise CourseError("MEDIA_DOWNLOAD_FAILED", str(error)) from error
        if path is None:
            raise CourseError("MEDIA_DOWNLOAD_FAILED", "媒体下载未返回文件。")
        if not path.exists():
            candidates = list(output_dir.glob("course-audio.*"))
            if not candidates:
                raise CourseError("MEDIA_DOWNLOAD_FAILED", "媒体工具未生成音频文件。")
            path = candidates[0]
        if path.stat().st_size > self.settings.max_course_bytes:
            raise CourseError("MEDIA_TOO_LARGE", "课程媒体超过本版本的本地处理上限。")
        return path

    @staticmethod
    def _delete_audio_download_artifacts(output_dir: Path) -> None:
        """Remove only downloader-owned files inside one lesson's media directory."""
        for candidate in output_dir.glob("course-audio.*"):
            if candidate.is_file() or candidate.is_symlink():
                candidate.unlink(missing_ok=True)
