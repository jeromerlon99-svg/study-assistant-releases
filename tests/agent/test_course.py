from __future__ import annotations

import pytest
from study_assistant_agent.course import CourseError, CourseInspector, parse_subtitles


def test_parse_webvtt_segments_and_html_entities() -> None:
    text = """WEBVTT

00:00:01.000 --> 00:00:03.500
<b>Hello</b> &amp; welcome

00:03.500 --> 00:00:05.000
Second line
"""

    segments = parse_subtitles(text)

    assert segments == [
        {"start_seconds": 1.0, "end_seconds": 3.5, "content": "Hello & welcome"},
        {"start_seconds": 3.5, "end_seconds": 5.0, "content": "Second line"},
    ]


def test_parse_srt_with_numeric_cue() -> None:
    text = """1
00:01:02,500 --> 00:01:04,250
A subtitle
"""

    assert parse_subtitles(text)[0] == {
        "start_seconds": 62.5,
        "end_seconds": 64.25,
        "content": "A subtitle",
    }


def test_parse_merges_adjacent_duplicate_content() -> None:
    text = """00:00.000 --> 00:02.000
Repeated

00:02.000 --> 00:04.000
Repeated
"""

    assert parse_subtitles(text) == [
        {"start_seconds": 0.0, "end_seconds": 4.0, "content": "Repeated"}
    ]


@pytest.mark.parametrize(
    "url",
    ["https://example.com/course/1", "http://public.example.org/video"],
)
def test_validate_url_accepts_public_http_urls(url: str) -> None:
    CourseInspector.validate_url(url)


@pytest.mark.parametrize(
    "url,code",
    [
        ("ftp://example.com/course", "INVALID_URL"),
        ("not-a-url", "INVALID_URL"),
        ("http://localhost/course", "PRIVATE_URL"),
        ("http://127.0.0.1/course", "PRIVATE_URL"),
        ("http://10.0.0.8/course", "PRIVATE_URL"),
        ("http://course.local/video", "PRIVATE_URL"),
    ],
)
def test_validate_url_rejects_unsupported_or_private_targets(url: str, code: str) -> None:
    with pytest.raises(CourseError) as captured:
        CourseInspector.validate_url(url)
    assert captured.value.code == code
