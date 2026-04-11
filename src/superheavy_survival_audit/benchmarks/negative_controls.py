"""
Negative-control audit engine with kill criteria and failure-mode tracking.

This module exists to make the repository easier to falsify.

It does not prove that a scoring layer is correct. It does something narrower
and more important for research hygiene:

- define cases that should remain low-support under the repository's own logic
- compare observed scores against explicit maximum-allowed thresholds
- track breach rate and breach severity
- trigger kill criteria when negative controls fail too often or too strongly

This is meant to prevent a weak scoring layer from sounding impressive while
also assigning strong scores to cases that should have been rejected.
"""

from __future__ import annotations

from dataclasses import dataclass

from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_probability,
)


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass(frozen=True, slots=True)
class NegativeControlCase:
    """
    One negative-control case with an explicit maximum allowed score.
    """

    case_id: str
    subject_id: str
    score_key: str
    expected_max_score: float
    failure_mode_label: str
    rationale: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", require_non_empty(self.case_id, "case_id"))
        object.__setattr__(
            self,
            "subject_id",
            require_non_empty(self.subject_id, "subject_id"),
        )
        object.__setattr__(
            self,
            "score_key",
            require_non_empty(self.score_key, "score_key"),
        )
        object.__setattr__(
            self,
            "expected_max_score",
            require_probability(self.expected_max_score, "expected_max_score"),
        )
        object.__setattr__(
            self,
            "failure_mode_label",
            require_non_empty(self.failure_mode_label, "failure_mode_label"),
        )
        object.__setattr__(
            self,
            "rationale",
            require_non_empty(self.rationale, "rationale"),
        )


@dataclass(frozen=True, slots=True)
class NegativeControlResult:
    """
    Result of comparing one negative-control case to an observed score.
    """

    case_id: str
    subject_id: str
    score_key: str
    failure_mode_label: str
    expected_max_score: float
    observed_score: float
    breach_margin: float
    status: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", require_non_empty(self.case_id, "case_id"))
        object.__setattr__(
            self,
            "subject_id",
            require_non_empty(self.subject_id, "subject_id"),
        )
        object.__setattr__(
            self,
            "score_key",
            require_non_empty(self.score_key, "score_key"),
        )
        object.__setattr__(
            self,
            "failure_mode_label",
            require_non_empty(self.failure_mode_label, "failure_mode_label"),
        )
        object.__setattr__(
            self,
            "expected_max_score",
            require_probability(self.expected_max_score, "expected_max_score"),
        )
        object.__setattr__(
            self,
            "observed_score",
            require_probability(self.observed_score, "observed_score"),
        )
        object.__setattr__(
            self,
            "breach_margin",
            require_probability(self.breach_margin, "breach_margin"),
        )
        object.__setattr__(
            self,
            "status",
            require_non_empty(self.status, "status"),
        )

        if self.status not in {"pass", "breach"}:
            raise SchemaValidationError("status must be either 'pass' or 'breach'.")


@dataclass(frozen=True, slots=True)
class FalsificationAuditSummary:
    """
    Summary across all negative-control checks.
    """

    total_case_count: int
    breach_count: int
    breach_rate: float
    max_breach_margin: float
    severe_breach_count: int
    breach_tolerance: float
    severe_breach_margin_threshold: float
    kill_triggered: bool
    results: tuple[NegativeControlResult, ...]

    def __post_init__(self) -> None:
        if int(self.total_case_count) <= 0:
            raise SchemaValidationError("total_case_count must be greater than zero.")
        if int(self.breach_count) < 0:
            raise SchemaValidationError("breach_count must be zero or greater.")
        if int(self.severe_breach_count) < 0:
            raise SchemaValidationError("severe_breach_count must be zero or greater.")

        object.__setattr__(self, "total_case_count", int(self.total_case_count))
        object.__setattr__(self, "breach_count", int(self.breach_count))
        object.__setattr__(self, "severe_breach_count", int(self.severe_breach_count))
        object.__setattr__(
            self,
            "breach_rate",
            require_probability(self.breach_rate, "breach_rate"),
        )
        object.__setattr__(
            self,
            "max_breach_margin",
            require_probability(self.max_breach_margin, "max_breach_margin"),
        )
        object.__setattr__(
            self,
            "breach_tolerance",
            require_probability(self.breach_tolerance, "breach_tolerance"),
        )
        object.__setattr__(
            self,
            "severe_breach_margin_threshold",
            require_probability(
                self.severe_breach_margin_threshold,
                "severe_breach_margin_threshold",
            ),
        )
        object.__setattr__(self, "results", tuple(self.results))

        if len(self.results) != self.total_case_count:
            raise SchemaValidationError(
                "results length must match total_case_count."
            )

    @property
    def pass_count(self) -> int:
        """Return the number of passing negative controls."""
        return self.total_case_count - self.breach_count


def run_negative_control_audit(
    cases: list[NegativeControlCase],
    *,
    observed_scores_by_score_key: dict[str, float],
    breach_tolerance: float = 0.20,
    severe_breach_margin_threshold: float = 0.15,
) -> FalsificationAuditSummary:
    """
    Run negative-control checks against observed score outputs.

    Kill criteria:
    - trigger if breach_rate > breach_tolerance
    - trigger if any individual breach margin >= severe_breach_margin_threshold

    Notes:
    - observed_scores_by_score_key must contain a value for every case score_key
    - each observed score must already be bounded in [0, 1]
    """
    if not cases:
        raise SchemaValidationError("cases must not be empty.")

    breach_tolerance = require_probability(breach_tolerance, "breach_tolerance")
    severe_breach_margin_threshold = require_probability(
        severe_breach_margin_threshold,
        "severe_breach_margin_threshold",
    )

    seen_case_ids: set[str] = set()
    seen_score_keys: set[str] = set()
    results: list[NegativeControlResult] = []

    for case in cases:
        if case.case_id in seen_case_ids:
            raise SchemaValidationError(f"Duplicate case_id in cases: {case.case_id}")
        seen_case_ids.add(case.case_id)

        if case.score_key in seen_score_keys:
            raise SchemaValidationError(
                f"Duplicate score_key in negative-control cases: {case.score_key}"
            )
        seen_score_keys.add(case.score_key)

        if case.score_key not in observed_scores_by_score_key:
            raise SchemaValidationError(
                f"Missing observed score for score_key: {case.score_key}"
            )

        observed_score = require_probability(
            observed_scores_by_score_key[case.score_key],
            f"observed_scores_by_score_key[{case.score_key}]",
        )

        breach_margin = _clamp_unit_interval(observed_score - case.expected_max_score)
        status = "breach" if observed_score > case.expected_max_score else "pass"

        results.append(
            NegativeControlResult(
                case_id=case.case_id,
                subject_id=case.subject_id,
                score_key=case.score_key,
                failure_mode_label=case.failure_mode_label,
                expected_max_score=case.expected_max_score,
                observed_score=observed_score,
                breach_margin=breach_margin,
                status=status,
            )
        )

    breach_count = sum(1 for result in results if result.status == "breach")
    breach_rate = breach_count / len(results)
    severe_breach_count = sum(
        1
        for result in results
        if result.breach_margin >= severe_breach_margin_threshold
    )
    max_breach_margin = max(result.breach_margin for result in results)

    kill_triggered = (
        breach_rate > breach_tolerance or severe_breach_count > 0
    )

    ordered_results = tuple(sorted(results, key=lambda item: item.case_id))

    return FalsificationAuditSummary(
        total_case_count=len(ordered_results),
        breach_count=breach_count,
        breach_rate=breach_rate,
        max_breach_margin=max_breach_margin,
        severe_breach_count=severe_breach_count,
        breach_tolerance=breach_tolerance,
        severe_breach_margin_threshold=severe_breach_margin_threshold,
        kill_triggered=kill_triggered,
        results=ordered_results,
    )
