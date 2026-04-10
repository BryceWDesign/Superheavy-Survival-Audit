"""
Canonical benchmark record schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import (
    SchemaValidationError,
    SourcePointer,
    require_membership,
    require_non_empty,
)

_ALLOWED_BENCHMARK_KINDS = (
    "evaluated_data_alignment",
    "literature_expectation",
    "internal_consistency",
    "negative_control",
    "regression_guard",
)

_ALLOWED_BENCHMARK_STATUSES = (
    "not_run",
    "pass",
    "fail",
    "mixed",
    "informational",
)


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    """
    Canonical benchmark record for comparing repository output to a reference.

    The benchmark schema records what was compared, what kind of comparison it
    was, and the outcome classification.
    """

    benchmark_id: str
    subject_id: str
    benchmark_kind: str
    reference_label: str
    status: str = "not_run"
    rationale: str | None = None
    source_pointer: SourcePointer = field(
        default_factory=lambda: SourcePointer(
            source_name="unassigned",
            source_record_id="unassigned",
        )
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "benchmark_id",
            require_non_empty(self.benchmark_id, "benchmark_id"),
        )
        object.__setattr__(
            self,
            "subject_id",
            require_non_empty(self.subject_id, "subject_id"),
        )
        object.__setattr__(
            self,
            "benchmark_kind",
            require_membership(
                self.benchmark_kind,
                "benchmark_kind",
                _ALLOWED_BENCHMARK_KINDS,
            ),
        )
        object.__setattr__(
            self,
            "reference_label",
            require_non_empty(self.reference_label, "reference_label"),
        )
        object.__setattr__(
            self,
            "status",
            require_membership(self.status, "status", _ALLOWED_BENCHMARK_STATUSES),
        )

        if self.rationale is not None and not self.rationale.strip():
            raise SchemaValidationError("rationale must not be blank when provided.")
