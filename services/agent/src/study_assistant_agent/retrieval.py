from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

_LATIN_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9_+#.\-]{1,}")
_CJK_RUN = re.compile(r"[\u3400-\u9fff]+")
_LATIN_STOP = {
    "about",
    "and",
    "are",
    "das",
    "der",
    "die",
    "ein",
    "eine",
    "for",
    "from",
    "how",
    "ist",
    "mit",
    "oder",
    "the",
    "this",
    "und",
    "von",
    "was",
    "what",
    "when",
    "where",
    "which",
    "why",
    "wie",
    "wieso",
    "would",
    "课程",
    "老师",
}
_CJK_NOISE = (
    "请问",
    "请",
    "课程中",
    "课程",
    "这一节",
    "这节课",
    "老师",
    "教授",
    "讲了",
    "讲的",
    "讲",
    "提到",
    "说明",
    "解释",
    "为什么",
    "是什么",
    "什么意思",
    "怎么样",
    "怎么",
    "如何",
    "哪些",
    "哪个",
    "是否",
    "可以",
    "一下",
    "关于",
    "相关",
)
_CJK_STOP_NGRAMS = {
    "什么",
    "为何",
    "为什么",
    "怎么",
    "如何",
    "哪些",
    "哪个",
    "是否",
    "可以",
    "课程",
    "老师",
    "教授",
    "这一",
    "一节",
    "节课",
    "讲了",
    "讲的",
    "解释",
}


def extract_search_terms(queries: Iterable[str], limit: int = 36) -> list[str]:
    """Build multilingual lexical terms, including Chinese substring n-grams."""
    terms: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        normalized = value.strip(" .,:;!?，。；：！？、()[]{}\"'").casefold()
        if len(normalized) < 2 or normalized in seen:
            return
        seen.add(normalized)
        terms.append(normalized)

    for query in queries:
        for word in _LATIN_WORD.findall(query):
            if word.casefold() not in _LATIN_STOP:
                add(word)
        for original in _CJK_RUN.findall(query):
            cleaned = original
            for noise in _CJK_NOISE:
                cleaned = cleaned.replace(noise, "")
            if len(cleaned) >= 2:
                add(cleaned[:24])
            candidates: list[str] = []
            for size in (4, 3, 2):
                if len(cleaned) < size:
                    continue
                candidates.extend(
                    cleaned[index : index + size] for index in range(len(cleaned) - size + 1)
                )
            for candidate in candidates:
                if candidate not in _CJK_STOP_NGRAMS:
                    add(candidate)
        if len(terms) >= limit:
            break
    return terms[:limit]


def lexical_score(text: str, queries: Iterable[str], terms: Iterable[str]) -> float:
    normalized = text.casefold()
    score = 0.0
    for query in queries:
        candidate = query.strip().casefold()
        if len(candidate) >= 2 and candidate in normalized:
            score += 18.0
    matched = 0
    for term in terms:
        count = normalized.count(term)
        if count:
            matched += 1
            score += min(count, 3) * (2.0 + min(len(term), 8) * 0.45)
    if matched > 1:
        score += min(matched, 6) * 1.5
    return score


def relevant_excerpt(text: str, terms: Iterable[str], radius: int = 700) -> str:
    normalized = text.casefold()
    positions = [normalized.find(term) for term in terms]
    positions = [position for position in positions if position >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - radius // 3)
    end = min(len(text), start + radius)
    prefix = "…" if start else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def reciprocal_rank_fusion(
    rankings: Iterable[list[dict[str, Any]]], limit: int = 10, rank_constant: int = 60
) -> list[dict[str, Any]]:
    """Fuse lexical and dense rankings without comparing incomparable raw scores."""
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    scores: dict[tuple[str, str], float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            key = (str(item.get("source_id", "")), str(item.get("id", "")))
            candidates.setdefault(key, item)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rank_constant + rank)
    ordered = sorted(candidates, key=lambda key: -scores[key])
    selected: list[dict[str, Any]] = []
    for key in ordered:
        candidate = candidates[key]
        if any(_same_passage(candidate, existing) for existing in selected):
            continue
        candidate["fusion_score"] = scores[key]
        selected.append(candidate)
        if len(selected) >= limit:
            break
    return selected


def _same_passage(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("source_id") != right.get("source_id"):
        return False
    left_start = float(left.get("start_seconds", 0))
    left_end = float(left.get("end_seconds", left_start))
    right_start = float(right.get("start_seconds", 0))
    right_end = float(right.get("end_seconds", right_start))
    overlap = max(0.0, min(left_end, right_end) - max(left_start, right_start))
    shortest = max(0.001, min(left_end - left_start, right_end - right_start))
    return overlap / shortest >= 0.6
