from __future__ import annotations

import json

from study_assistant_agent.config import Settings


def make_settings(tmp_path, **overrides) -> Settings:
    return Settings(_env_file=None, data_dir=tmp_path, **overrides)


def test_public_settings_never_expose_api_key(tmp_path) -> None:
    settings = make_settings(tmp_path, api_key="secret", text_model="model")

    public = settings.public_dict()

    assert public["has_api_key"] is True
    assert "api_key" not in public
    assert "secret" not in json.dumps(public)


def test_non_secret_provider_config_ignores_persisted_key(tmp_path) -> None:
    settings = make_settings(tmp_path, api_key="session-key")
    settings.ensure_directories()
    settings.provider_config_path.write_text(
        json.dumps(
            {
                "api_base_url": "https://provider.example/v1",
                "text_model": "model-name",
                "reasoning_effort": "high",
                "local_whisper_model": "medium",
                "api_key": "must-not-load",
            }
        ),
        encoding="utf-8",
    )

    settings.load_non_secret_provider_config()

    assert settings.api_base_url == "https://provider.example/v1"
    assert settings.text_model == "model-name"
    assert settings.api_key == "session-key"


def test_preferences_round_trip_and_reject_unknown_language(tmp_path) -> None:
    settings = make_settings(tmp_path)
    settings.ensure_directories()

    assert settings.save_preferences("de") == {"ui_language": "de"}
    assert settings.load_preferences() == {"ui_language": "de"}

    settings.preferences_path.write_text('{"ui_language":"fr"}', encoding="utf-8")
    assert settings.load_preferences() == {"ui_language": "zh-CN"}
