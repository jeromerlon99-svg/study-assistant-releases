from __future__ import annotations

import pytest
from study_assistant_agent.prompts import (
    PROMPT_VERSION,
    build_course_overview_prompt,
    build_rapid_learning_module_prompt,
    get_prompt_preset,
    get_system_prompt,
    list_prompt_presets,
)


@pytest.mark.parametrize("locale", ["zh-CN", "en", "de"])
def test_each_locale_exposes_three_read_only_presets(locale: str) -> None:
    presets = list_prompt_presets(locale)

    assert [preset["id"] for preset in presets] == ["quick", "standard", "deep"]
    assert all(preset["read_only"] is True for preset in presets)
    assert all(preset["version"] == PROMPT_VERSION for preset in presets)


def test_unknown_locale_falls_back_to_chinese() -> None:
    assert get_system_prompt("unsupported") == get_system_prompt("zh-CN")
    assert get_prompt_preset("unsupported", "en").id == "standard"


def test_english_module_prompt_is_bounded_and_requests_english() -> None:
    prompt = build_rapid_learning_module_prompt("Course evidence", "quick", "en")

    assert "Write all output in English" in prompt
    assert "<course_transcript>" in prompt
    assert "Course evidence" in prompt
    assert "</course_transcript>" in prompt


def test_german_overview_prompt_is_bounded_and_requests_german() -> None:
    prompt = build_course_overview_prompt("Titel", "Notizen", "deep", "de")

    assert "Verfasse die gesamte Ausgabe auf Deutsch" in prompt
    assert "<module_notes>" in prompt
    assert "Notizen" in prompt
    assert "</module_notes>" in prompt


def test_detail_levels_have_increasing_token_budgets() -> None:
    quick = get_prompt_preset("quick", "en")
    standard = get_prompt_preset("standard", "en")
    deep = get_prompt_preset("deep", "en")

    assert quick.max_tokens < standard.max_tokens < deep.max_tokens
