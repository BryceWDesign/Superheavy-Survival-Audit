"""
Literature-facing benchmark table builder.

This module turns benchmark records into a comparison-friendly table that is
easy to review in release notes, audit packs, or paper-adjacent artifacts.

Important boundaries:
- this does not decide scientific truth
- this does not replace the underlying benchmark records
- this is a presentation and comparison layer for explicit benchmark claims

The intended output is a table that makes it easy to see:
- what subject was benchmarked
- what reference expectation was used
- what the repository observed
- how the benchmark was classified
- what citation key or source label should be checked next
"""

from __future__ import annotations

from dataclasses import dataclass

from superheavy_survival_audit.schemas import BenchmarkRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
)

_ALLOWED_ROW_STATUSES: tuple[str, ...] = (
    "not_run",
    "pass",
    "fail",
    "mixed",
    "informational",
)


def _escape_markdown_cell(value: str) -> str:
    """Escape pipe characters for markdown table output."""
    return value.replace("|", "\\|")


@dataclass(frozen=True, slots=True)
class LiteratureBenchmarkRow:
    """
    One literature-facing benchmark comparison row.
    """

    benchmark_id: str
    subject_id: str
    benchmark_kind: str
    reference_label: str
    expected_statement: str
    observed_statement: str
    status: str
    citation_key: str
    notes: str | None = None

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
            require_non_empty(self.benchmark_kind, "benchmark_kind"),
        )
        object.__setattr__(
            self,
            "reference_label",
            require_non_empty(self.reference_label, "reference_label"),
        )
        object.__setattr__(
            self,
            "expected_statement",
            require_non_empty(self.expected_statement, "expected_statement"),
        )
        object.__setattr__(
            self,
            "observed_statement",
            require_non_empty(self.observed_statement, "observed_statement"),
        )
        object.__setattr__(
            self,
            "status",
            require_non_empty(self.status, "status"),
        )
        object.__setattr__(
            self,
            "citation_key",
            require_non_empty(self.citation_key, "citation_key"),
        )

        if self.status not in _ALLOWED_ROW_STATUSES:
            raise SchemaValidationError(
                f"status must be one of: {', '.join(_ALLOWED_ROW_STATUSES)}."
            )

        if self.notes is not None:
            object.__setattr__(self, "notes", require_non_empty(self.notes, "notes"))

    def to_markdown_row(self) -> str:
        """Return a markdown table row."""
        return (
            f"| {_escape_markdown_cell(self.subject_id)} "
            f"| {_escape_markdown_cell(self.reference_label)} "
            f"| {_escape_markdown_cell(self.expected_statement)} "
            f"| {_escape_markdown_cell(self.observed_statement)} "
            f"| {_escape_markdown_cell(self.status)} "
            f"| {_escape_markdown_cell(self.citation_key)} |"
        )


@dataclass(frozen=True, slots=True)
class LiteratureBenchmarkTable:
    """
    Collection of literature-facing benchmark rows with deterministic ordering.
    """

    title: str
    rows: tuple[LiteratureBenchmarkRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", require_non_empty(self.title, "title"))
        object.__setattr__(self, "rows", tuple(self.rows))

        if not self.rows:
            raise SchemaValidationError("rows must not be empty.")

        seen_benchmark_ids: set[str] = set()
        for row in self.rows:
            if row.benchmark_id in seen_benchmark_ids:
                raise SchemaValidationError(
                    f"Duplicate benchmark_id in literature table: {row.benchmark_id}"
                )
            seen_benchmark_ids.add(row.benchmark_id)

    @property
    def row_count(self) -> int:
        """Return the number of rows in the table."""
        return len(self.rows)

    @property
    def status_counts(self) -> dict[str, int]:
        """Return status counts across all rows."""
        counts = {status: 0 for status in _ALLOWED_ROW_STATUSES}
        for row in self.rows:
            counts[row.status] += 1
        return counts

    def to_markdown(self) -> str:
        """Return the table as markdown text."""
        header = [
            f"## {self.title}",
            "",
            "| Subject | Reference | Expected | Observed | Status | Citation key |",
            "|---|---|---|---|---|---|",
        ]
        body = [row.to_markdown_row() for row in self.rows]
        return "\n".join(header + body)

    def to_dict_rows(self) -> list[dict[str, str | None]]:
        """Return JSON-serializable row dictionaries."""
        return [
            {
                "benchmark_id": row.benchmark_id,
                "subject_id": row.subject_id,
                "benchmark_kind": row.benchmark_kind,
                "reference_label": row.reference_label,
                "expected_statement": row.expected_statement,
                "observed_statement": row.observed_statement,
                "status": row.status,
                "citation_key": row.citation_key,
                "notes": row.notes,
            }
            for row in self.rows
        ]


def row_from_benchmark_record(
    record: BenchmarkRecord,
    *,
    expected_statement: str,
    observed_statement: str,
    citation_key: str,
    notes: str | None = None,
) -> LiteratureBenchmarkRow:
    """
    Convert a canonical benchmark record into a literature-facing table row.
    """
    merged_notes = notes
    if merged_notes is None:
        merged_notes = record.rationale

    return LiteratureBenchmarkRow(
        benchmark_id=record.benchmark_id,
        subject_id=record.subject_id,
        benchmark_kind=record.benchmark_kind,
        reference_label=record.reference_label,
        expected_statement=expected_statement,
        observed_statement=observed_statement,
        status=record.status,
        citation_key=citation_key,
        notes=merged_notes,
    )


def build_literature_benchmark_table(
    title: str,
    rows: list[LiteratureBenchmarkRow],
) -> LiteratureBenchmarkTable:
    """
    Build a deterministically ordered literature-facing benchmark table.
    """
    if not rows:
        raise SchemaValidationError("rows must not be empty.")

    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.subject_id,
                row.benchmark_kind,
                row.reference_label,
                row.benchmark_id,
            ),
        )
    )
    return LiteratureBenchmarkTable(title=title, rows=ordered_rows)
