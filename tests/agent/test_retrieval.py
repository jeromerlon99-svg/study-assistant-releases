from __future__ import annotations

from study_assistant_agent.retrieval import (
    extract_search_terms,
    lexical_score,
    reciprocal_rank_fusion,
    relevant_excerpt,
)


def test_extract_search_terms_supports_latin_and_cjk() -> None:
    terms = extract_search_terms(["How does React state work?", "解释机器学习模型"])

    assert "react" in terms
    assert "state" in terms
    assert any("机器" in term or "学习" in term for term in terms)
    assert "how" not in terms


def test_lexical_score_rewards_exact_query_and_multiple_terms() -> None:
    exact = lexical_score("React state updates trigger rendering.", ["React state"], ["react", "state"])
    partial = lexical_score("React components render.", ["React state"], ["react", "state"])

    assert exact > partial > 0


def test_relevant_excerpt_centers_on_match() -> None:
    text = "prefix " * 100 + "semantic retrieval" + " suffix" * 100

    excerpt = relevant_excerpt(text, ["semantic"], radius=120)

    assert "semantic retrieval" in excerpt
    assert len(excerpt) <= 122


def test_reciprocal_rank_fusion_combines_rankings() -> None:
    first = [
        {"id": "a", "source_id": "lesson-1", "start_seconds": 0, "end_seconds": 10},
        {"id": "b", "source_id": "lesson-1", "start_seconds": 20, "end_seconds": 30},
    ]
    second = [
        {"id": "b", "source_id": "lesson-1", "start_seconds": 20, "end_seconds": 30},
        {"id": "c", "source_id": "lesson-2", "start_seconds": 0, "end_seconds": 10},
    ]

    fused = reciprocal_rank_fusion([first, second])

    assert fused[0]["id"] == "b"
    assert {item["id"] for item in fused} == {"a", "b", "c"}


def test_reciprocal_rank_fusion_deduplicates_overlapping_passages() -> None:
    ranking = [
        {"id": "a", "source_id": "lesson", "start_seconds": 0, "end_seconds": 10},
        {"id": "b", "source_id": "lesson", "start_seconds": 2, "end_seconds": 9},
    ]

    assert len(reciprocal_rank_fusion([ranking])) == 1
