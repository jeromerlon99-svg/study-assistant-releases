from __future__ import annotations

import json

import httpx
import keyring

from .config import Settings
from .schemas import ProviderSelfTest, ProviderSettingsUpdate

KEYRING_SERVICE = "StudyAssistant"
API_KEY_ACCOUNT = "model-api-key"
SEARCH_KEY_ACCOUNT = "search-api-key"


class ProviderError(RuntimeError):
    pass


class ModelProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._clear_persisted_keys()

    def _clear_persisted_keys(self) -> None:
        # Keys are deliberately session-only. Clear values supplied by the
        # environment and remove credentials left by pre-0.1.0 builds.
        self.settings.api_key = ""
        # Also delete the legacy search credential left by versions that
        # exposed an optional external-search integration.
        for account in (API_KEY_ACCOUNT, SEARCH_KEY_ACCOUNT):
            try:
                keyring.delete_password(KEYRING_SERVICE, account)
            except keyring.errors.KeyringError:
                pass

    def _headers(self, api_key: str | None = None) -> dict[str, str]:
        key = api_key if api_key is not None else self.settings.api_key
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    @property
    def text_ready(self) -> bool:
        """Whether this process currently has everything needed for text generation."""
        return bool(self.settings.text_model.strip() and self.settings.api_key.strip())

    def require_text_ready(self) -> None:
        if not self.settings.text_model.strip():
            raise ProviderError("尚未配置文本模型，请先打开“API 设置”填写模型名称。")
        if not self.settings.api_key.strip():
            raise ProviderError(
                "当前运行尚未填写 API Key。出于安全策略，程序每次启动都会清空 Key；"
                "请重新打开“API 设置”，保存并确认连接测试成功。"
            )

    def _endpoint(self, path: str) -> str:
        return f"{self.settings.api_base_url.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def is_kimi_k3(model: str) -> bool:
        normalized = model.strip().lower()
        return normalized == "kimi-k3" or normalized.startswith("kimi-k3-")

    async def save_settings(self, update: ProviderSettingsUpdate) -> dict[str, object]:
        for field in (
            "api_base_url",
            "text_model",
            "reasoning_effort",
            "local_whisper_model",
        ):
            setattr(self.settings, field, getattr(update, field).strip())
        if update.api_key is not None:
            self.settings.api_key = update.api_key.strip()
        payload = {
            "api_base_url": self.settings.api_base_url,
            "text_model": self.settings.text_model,
            "reasoning_effort": self.settings.reasoning_effort,
            "local_whisper_model": self.settings.local_whisper_model,
        }
        self.settings.provider_config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return self.settings.public_dict()

    async def self_test(self) -> ProviderSelfTest:
        if not self.settings.text_model:
            return ProviderSelfTest(
                text=False,
                transcription_configured=False,
                message="尚未配置文本模型；课程可检查和保存，但无法生成智能笔记。",
            )
        if not self.settings.api_key:
            return ProviderSelfTest(
                text=False,
                transcription_configured=False,
                message="当前运行未填写 API Key，无法生成速学速记或回答问题。",
            )
        try:
            result = await self.chat(
                [
                    {"role": "system", "content": "Return exactly: OK"},
                    {"role": "user", "content": "Capability check"},
                ],
                max_tokens=1024 if self.is_kimi_k3(self.settings.text_model) else 8,
                temperature=0,
                read_timeout_seconds=120 if self.is_kimi_k3(self.settings.text_model) else 45,
            )
            text_ok = bool(result.strip())
            message = "文本模型连接成功。" if text_ok else "模型响应为空。"
        except ProviderError as error:
            text_ok = False
            message = str(error)
        return ProviderSelfTest(
            text=text_ok,
            transcription_configured=False,
            message=message,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 1800,
        temperature: float = 0.2,
        read_timeout_seconds: float | None = None,
    ) -> str:
        self.require_text_ready()
        read_timeout = read_timeout_seconds or self.settings.request_timeout_seconds
        payload: dict[str, object] = {
            "model": self.settings.text_model,
            "messages": messages,
        }
        if self.is_kimi_k3(self.settings.text_model):
            payload["max_completion_tokens"] = max_tokens
            payload["reasoning_effort"] = self.settings.reasoning_effort
        else:
            payload["temperature"] = temperature
            payload["max_tokens"] = max_tokens
        try:
            timeout = httpx.Timeout(
                connect=20.0,
                read=read_timeout,
                write=60.0,
                pool=30.0,
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self._endpoint("chat/completions"),
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.ReadTimeout as error:
            raise ProviderError(
                f"模型 API 已连接，但等待生成结果超过 {read_timeout:g} 秒。"
                "课程转写已经保留，可稍后重新生成；也可以降低推理强度后重试。"
            ) from error
        except httpx.ConnectTimeout as error:
            raise ProviderError(
                "连接模型 API 超时（20 秒），请检查网络或 API Base URL。"
            ) from error
        except httpx.ConnectError as error:
            detail = str(error).strip() or type(error).__name__
            raise ProviderError(f"无法建立模型 API 连接：{detail}") from error
        except httpx.HTTPError as error:
            detail = str(error).strip() or type(error).__name__
            raise ProviderError(f"模型 API 通信失败（{type(error).__name__}）：{detail}") from error
        if response.is_error:
            detail = response.text[:500]
            raise ProviderError(f"模型 API 返回 {response.status_code}：{detail}")
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ProviderError("模型 API 响应格式不兼容 chat/completions。") from error
        if isinstance(content, list):
            content = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
        return str(content).strip()
