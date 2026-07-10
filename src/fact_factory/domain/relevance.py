from __future__ import annotations

from enum import StrEnum


class RelevanceLevel(StrEnum):
    MAXIMUM = "maximum"
    HIGH = "high"
    GOOD = "good"
    LOW = "low"
    NONE = "none"


GAP_THRESHOLD = 0.55

_RELEVANCE_THRESHOLDS: tuple[tuple[float, RelevanceLevel], ...] = (
    (0.85, RelevanceLevel.MAXIMUM),
    (0.75, RelevanceLevel.HIGH),
    (0.65, RelevanceLevel.GOOD),
    (0.55, RelevanceLevel.LOW),
)


def score_to_relevance(score: float) -> RelevanceLevel:
    for threshold, relevance in _RELEVANCE_THRESHOLDS:
        if score >= threshold:
            return relevance
    return RelevanceLevel.NONE


def is_gap(score: float, *, min_score: float = GAP_THRESHOLD) -> bool:
    return score < min_score
