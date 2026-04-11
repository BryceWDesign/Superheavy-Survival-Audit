"""
Reviewer audit pack with benchmark delta summaries.

This module builds a compact reviewer-facing audit artifact from current
literature-facing benchmark rows and optional prior benchmark rows.

The goal is not to replace the underlying data structures. The goal is to make
release-to-release review easier by showing:

- current benchmark counts by status
- per-benchmark status deltas relative to a prior snapshot
- which rows are new, removed, improved, worsened, or unchanged
- negative-control kill state, when available

This is a review and governance surface, not a claim engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
)

from .literature_table import LiteratureBenchmarkRow, LiteratureBenchmarkTable
from .negative_controls import FalsificationAuditSummary

_ALLOWED_DELTA_KINDS: tuple[str, ...] = (
    "added",
    "removed",
    "status_changed",
    "unchanged",
)

_STATUS_SEVERITY: dict[str, int] = {
    "fail": 0,
    "mixed": 1,
    "not_run": 2,
    "informational": 3,
    "pass": 4,
}


def _escape_markdown_cell(value: str) -> str:
    """Escape pipe characters for markdown table output."""
    return value.replace("|", "\\|")


def _status_transition_label(previous_status: str | None, current_status: str | None) -> str:
    """Return a human-readable status transition label."""
    previous_label = "missing" if previous_status is None else previous_status
    current_label = "missing" if current_status is None else current_status
    return f"{previous_label} -> {current_label}"


def _classify_status_change(previous_status: str, current_status: str) -> str:
    """Classify whether a status change improved, worsened, or stayed neutral."""
    if previous_status == current_status:
        return "unchanged"

    previous_rank = _STATUS_SEVERITY[previous_status]
    current_rank = _STATUS_SEVERITY[current_status]

    if current_rank > previous_rank:
        return "improved"
    if current_rank < previous_rank:
        return "worsened"
    return "changed"


@dataclass(frozen=True, slots=True)
class BenchmarkDeltaRow:
    """
    One reviewer-facing benchmark delta row.
    """

    benchmark_id: str
    subject_id: str
    reference_label: str
    delta_kind: str
    previous_status: str | None
    current_status: str | None
    status_transition: str
    change_classification: str

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
            "reference_label",
            require_non_empty(self.reference_label, "reference_label"),
        )
        object.__setattr__(
            self,
            "delta_kind",
            require_non_empty(self.delta_kind, "delta_kind"),
        )
        object.__setattr__(
            self,
            "status_transition",
            require_non_empty(self.status_transition, "status_transition"),
        )
        object.__setattr__(
            self,
            "change_classification",
            require_non_empty(self.change_classification, "change_classification"),
        )

        if self.delta_kind not in _ALLOWED_DELTA_KINDS:
            raise SchemaValidationError(
                f"delta_kind must be one of: {', '.join(_ALLOWED_DELTA_KINDS)}."
            )

        if self.previous_status is None and self.current_status is None:
            raise SchemaValidationError(
                "At least one of previous_status or current_status must be present."
            )

    def to_markdown_row(self) -> str:
        """Return a markdown table row."""
        previous_status = "missing" if self.previous_status is None else self.previous_status
        current_status = "missing" if self.current_status is None else self.current_status

        return (
            f"| {_escape_markdown_cell(self.benchmark_id)} "
            f"| {_escape_markdown_cell(self.subject_id)} "
            f"| {_escape_markdown_cell(self.reference_label)} "
            f"| {_escape_markdown_cell(self.delta_kind)} "
            f"| {_escape_markdown_cell(previous_status)} "
            f"| {_escape_markdown_cell(current_status)} "
            f"| {_escape_markdown_cell(self.change_classification)} |"
        )


@dataclass(frozen=True, slots=True)
class ReviewerAuditPack:
    """
    Compact reviewer-facing audit pack for one benchmark snapshot.
    """

    title: str
    current_table: LiteratureBenchmarkTable
    delta_rows: tuple[BenchmarkDeltaRow, ...]
    negative_control_summary: FalsificationAuditSummary | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", require_non_empty(self.title, "title"))
        object.__setattr__(self, "delta_rows", tuple(self.delta_rows))

        seen_benchmark_ids: set[str] = set()
        for row in self.delta_rows:
            if row.benchmark_id in seen_benchmark_ids:
                raise SchemaValidationError(
                    f"Duplicate benchmark_id in delta_rows: {row.benchmark_id}"
                )
            seen_benchmark_ids.add(row.benchmark_id)

    @property
    def delta_count(self) -> int:
        """Return the number of delta rows."""
        return len(self.delta_rows)

    @property
    def delta_kind_counts(self) -> dict[str, int]:
        """Return counts by delta kind."""
        counts = {kind: 0 for kind in _ALLOWED_DELTA_KINDS}
        for row in self.delta_rows:
            counts[row.delta_kind] += 1
        return counts

    @property
    def change_classification_counts(self) -> dict[str, int]:
        """Return counts by change classification."""
        counts = {
            "added": 0,
            "removed": 0,
            "improved": 0,
            "worsened": 0,
            "changed": 0,
            "unchanged": 0,
        }
        for row in self.delta_rows:
            counts[row.change_classification] += 1
        return counts

    def to_markdown(self) -> str:
        """Return the reviewer audit pack as markdown."""
        lines: list[str] = [
            f"# {self.title}",
            "",
            "## Current benchmark status counts",
            "",
            f"- total rows: {self.current_table.row_count}",
        ]

        for status, count in self.current_table.status_counts.items():
            lines.append(f"- {status}: {count}")

        lines.extend(
            [
                "",
                "## Benchmark deltas",
                "",
                "| Benchmark ID | Subject | Reference | Delta kind | Previous | Current | Classification |",
                "|---|---|---|---|---|---|---|",
            ]
        )

        for row in self.delta_rows:
            lines.append(row.to_markdown_row())

        if self.negative_control_summary is not None:
            summary = self.negative_control_summary
            lines.extend(
                [
                    "",
                    "## Negative-control summary",
                    "",
                    f"- total controls: {summary.total_case_count}",
                    f"- breaches: {summary.breach_count}",
                    f"- breach rate: {summary.breach_rate:.3f}",
                    f"- severe breaches: {summary.severe_breach_count}",
                    f"- max breach margin: {summary.max_breach_margin:.3f}",
                    f"- kill triggered: {summary.kill_triggered}",
                ]
            )

        return "\n".join(lines)


def _index_rows_by_benchmark_id(
    rows: tuple[LiteratureBenchmarkRow, ...] | list[LiteratureBenchmarkRow],
) -> dict[str, LiteratureBenchmarkRow]:
    """Index rows by benchmark_id while checking uniqueness."""
    index: dict[str, LiteratureBenchmarkRow] = {}
    for row in rows:
        if row.benchmark_id in index:
            raise SchemaValidationError(
                f"Duplicate benchmark_id in benchmark rows: {row.benchmark_id}"
            )
        index[row.benchmark_id] = row
    return index


def build_reviewer_audit_pack(
    title: str,
    current_table: LiteratureBenchmarkTable,
    *,
    previous_table: LiteratureBenchmarkTable | None = None,
    negative_control_summary: FalsificationAuditSummary | None = None,
) -> ReviewerAuditPack:
    """
    Build a reviewer-facing audit pack with benchmark deltas.

    Delta logic:
    - added: benchmark exists only in current table
    - removed: benchmark exists only in previous table
    - unchanged: same status in both tables
    - status_changed: status differs between previous and current
    """
    current_index = _index_rows_by_benchmark_id(current_table.rows)
    previous_index = {} if previous_table is None else _index_rows_by_benchmark_id(previous_table.rows)

    all_benchmark_ids = sorted(set(current_index) | set(previous_index))
    delta_rows: list[BenchmarkDeltaRow] = []

    for benchmark_id in all_benchmark_ids:
        current_row = current_index.get(benchmark_id)
        previous_row = previous_index.get(benchmark_id)

        if previous_row is None and current_row is not None:
            delta_rows.append(
                BenchmarkDeltaRow(
                    benchmark_id=benchmark_id,
                    subject_id=current_row.subject_id,
                    reference_label=current_row.reference_label,
                    delta_kind="added",
                    previous_status=None,
                    current_status=current_row.status,
                    status_transition=_status_transition_label(None, current_row.status),
                    change_classification="added",
                )
            )
            continue

        if current_row is None and previous_row is not None:
            delta_rows.append(
                BenchmarkDeltaRow(
                    benchmark_id=benchmark_id,
                    subject_id=previous_row.subject_id,
                    reference_label=previous_row.reference_label,
                    delta_kind="removed",
                    previous_status=previous_row.status,
                    current_status=None,
                    status_transition=_status_transition_label(previous_row.status, None),
                    change_classification="removed",
                )
            )
            continue

        assert current_row is not None
        assert previous_row is not None

        if current_row.status == previous_row.status:
            delta_kind = "unchanged"
            change_classification = "unchanged"
        else:
            delta_kind = "status_changed"
            change_classification = _classify_status_change(
                previous_row.status,
                current_row.status,
            )

        delta_rows.append(
            BenchmarkDeltaRow(
                benchmark_id=benchmark_id,
                subject_id=current_row.subject_id,
                reference_label=current_row.reference_label,
                delta_kind=delta_kind,
                previous_status=previous_row.status,
                current_status=current_row.status,
                status_transition=_status_transition_label(
                    previous_row.status,
                    current_row.status,
                ),
                change_classification=change_classification,
            )
        )

    ordered_delta_rows = tuple(
        sorted(
            delta_rows,
            key=lambda row: (
                row.subject_id,
                row.reference_label,
                row.benchmark_id,
            ),
        )
    )

    return ReviewerAuditPack(
        title=title,
        current_table=current_table,
        delta_rows=ordered_delta_rows,
        negative_control_summary=negative_control_summary,
    )
