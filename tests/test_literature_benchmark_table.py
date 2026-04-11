from __future__ import annotations

import pytest

from superheavy_survival_audit.benchmarks import (
    LiteratureBenchmarkRow,
    build_literature_benchmark_table,
    row_from_benchmark_record,
)
from superheavy_survival_audit.schemas import BenchmarkRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_literature_benchmark_row_accepts_valid_values() -> None:
    row = LiteratureBenchmarkRow(
        benchmark_id="bench-001",
        subject_id="Mc-290",
        benchmark_kind="literature_expectation",
        reference_label="Example reference",
        expected_statement="Alpha continuity should dominate the main branch.",
        observed_statement="Repository sees alpha continuity on the best supported branch.",
        status="informational",
        citation_key="ref:example-001",
        notes="Illustrative row.",
    )

    assert row.benchmark_id == "bench-001"
    assert row.status == "informational"
    assert "Mc-290" in row.to_markdown_row()


def test_row_from_benchmark_record_preserves_core_fields() -> None:
    record = BenchmarkRecord(
        benchmark_id="bench-002",
        subject_id="Mc-291",
        benchmark_kind="literature_expectation",
        reference_label="Reference B",
        status="mixed",
        rationale="Partial alignment only.",
    )

    row = row_from_benchmark_record(
        record,
        expected_statement="Reference expects partial agreement.",
        observed_statement="Repository shows mixed support.",
        citation_key="ref:example-002",
    )

    assert row.benchmark_id == "bench-002"
    assert row.subject_id == "Mc-291"
    assert row.status == "mixed"
    assert row.notes == "Partial alignment only."


def test_build_literature_benchmark_table_sorts_rows_deterministically() -> None:
    rows = [
        LiteratureBenchmarkRow(
            benchmark_id="bench-003",
            subject_id="Mc-291",
            benchmark_kind="literature_expectation",
            reference_label="Reference B",
            expected_statement="Expected B",
            observed_statement="Observed B",
            status="pass",
            citation_key="ref:b",
        ),
        LiteratureBenchmarkRow(
            benchmark_id="bench-001",
            subject_id="Mc-290",
            benchmark_kind="evaluated_data_alignment",
            reference_label="Reference A",
            expected_statement="Expected A",
            observed_statement="Observed A",
            status="informational",
            citation_key="ref:a",
        ),
        LiteratureBenchmarkRow(
            benchmark_id="bench-002",
            subject_id="Mc-290",
            benchmark_kind="literature_expectation",
            reference_label="Reference C",
            expected_statement="Expected C",
            observed_statement="Observed C",
            status="fail",
            citation_key="ref:c",
        ),
    ]

    table = build_literature_benchmark_table("Example Table", rows)

    assert table.row_count == 3
    assert [row.benchmark_id for row in table.rows] == [
        "bench-001",
        "bench-002",
        "bench-003",
    ]


def test_literature_benchmark_table_markdown_contains_expected_header() -> None:
    table = build_literature_benchmark_table(
        "Benchmark Matrix",
        [
            LiteratureBenchmarkRow(
                benchmark_id="bench-001",
                subject_id="Mc-290",
                benchmark_kind="literature_expectation",
                reference_label="Reference A",
                expected_statement="Expected A",
                observed_statement="Observed A",
                status="pass",
                citation_key="ref:a",
            )
        ],
    )

    markdown = table.to_markdown()

    assert markdown.startswith("## Benchmark Matrix")
    assert "| Subject | Reference | Expected | Observed | Status | Citation key |" in markdown
    assert "| Mc-290 | Reference A | Expected A | Observed A | pass | ref:a |" in markdown


def test_literature_benchmark_table_rejects_duplicate_ids() -> None:
    with pytest.raises(SchemaValidationError):
        build_literature_benchmark_table(
            "Duplicate Table",
            [
                LiteratureBenchmarkRow(
                    benchmark_id="bench-001",
                    subject_id="Mc-290",
                    benchmark_kind="literature_expectation",
                    reference_label="Reference A",
                    expected_statement="Expected A",
                    observed_statement="Observed A",
                    status="pass",
                    citation_key="ref:a",
                ),
                LiteratureBenchmarkRow(
                    benchmark_id="bench-001",
                    subject_id="Mc-291",
                    benchmark_kind="literature_expectation",
                    reference_label="Reference B",
                    expected_statement="Expected B",
                    observed_statement="Observed B",
                    status="fail",
                    citation_key="ref:b",
                ),
            ],
        )
