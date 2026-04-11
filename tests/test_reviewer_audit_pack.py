from __future__ import annotations

import pytest

from superheavy_survival_audit.benchmarks import (
    LiteratureBenchmarkRow,
    build_literature_benchmark_table,
    build_reviewer_audit_pack,
)
from superheavy_survival_audit.benchmarks.negative_controls import (
    NegativeControlCase,
    run_negative_control_audit,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError


def _build_row(
    benchmark_id: str,
    subject_id: str,
    reference_label: str,
    status: str,
) -> LiteratureBenchmarkRow:
    return LiteratureBenchmarkRow(
        benchmark_id=benchmark_id,
        subject_id=subject_id,
        benchmark_kind="literature_expectation",
        reference_label=reference_label,
        expected_statement="Expected statement.",
        observed_statement="Observed statement.",
        status=status,
        citation_key=f"ref:{benchmark_id}",
    )


def test_build_reviewer_audit_pack_detects_added_removed_and_changed_rows() -> None:
    previous_table = build_literature_benchmark_table(
        "Previous",
        [
            _build_row("bench-001", "Mc-290", "Reference A", "fail"),
            _build_row("bench-002", "Mc-291", "Reference B", "pass"),
            _build_row("bench-003", "Lv-292", "Reference C", "informational"),
        ],
    )
    current_table = build_literature_benchmark_table(
        "Current",
        [
            _build_row("bench-001", "Mc-290", "Reference A", "mixed"),
            _build_row("bench-002", "Mc-291", "Reference B", "pass"),
            _build_row("bench-004", "Ts-294", "Reference D", "not_run"),
        ],
    )

    pack = build_reviewer_audit_pack(
        "Audit Pack",
        current_table,
        previous_table=previous_table,
    )

    assert pack.delta_count == 4
    counts = pack.delta_kind_counts
    assert counts["status_changed"] == 1
    assert counts["unchanged"] == 1
    assert counts["added"] == 1
    assert counts["removed"] == 1

    class_counts = pack.change_classification_counts
    assert class_counts["improved"] == 1
    assert class_counts["unchanged"] == 1
    assert class_counts["added"] == 1
    assert class_counts["removed"] == 1


def test_build_reviewer_audit_pack_can_include_negative_control_summary() -> None:
    current_table = build_literature_benchmark_table(
        "Current",
        [_build_row("bench-001", "Mc-290", "Reference A", "pass")],
    )

    negative_control_summary = run_negative_control_audit(
        [
            NegativeControlCase(
                case_id="nc-001",
                subject_id="route-weak-a",
                score_key="route-weak-a:info_gain",
                expected_max_score=0.40,
                failure_mode_label="over_permissive_route_priority",
                rationale="Weak route should not rank strongly.",
            )
        ],
        observed_scores_by_score_key={"route-weak-a:info_gain": 0.28},
    )

    pack = build_reviewer_audit_pack(
        "Audit Pack",
        current_table,
        negative_control_summary=negative_control_summary,
    )

    markdown = pack.to_markdown()

    assert "## Negative-control summary" in markdown
    assert "- kill triggered: False" in markdown


def test_build_reviewer_audit_pack_without_previous_table_marks_all_rows_added() -> None:
    current_table = build_literature_benchmark_table(
        "Current",
        [
            _build_row("bench-001", "Mc-290", "Reference A", "pass"),
            _build_row("bench-002", "Mc-291", "Reference B", "mixed"),
        ],
    )

    pack = build_reviewer_audit_pack("Audit Pack", current_table)

    assert all(row.delta_kind == "added" for row in pack.delta_rows)
    assert pack.change_classification_counts["added"] == 2


def test_build_reviewer_audit_pack_rejects_duplicate_benchmark_ids_in_delta_rows() -> None:
    current_table = build_literature_benchmark_table(
        "Current",
        [_build_row("bench-001", "Mc-290", "Reference A", "pass")],
    )

    with pytest.raises(SchemaValidationError):
        build_reviewer_audit_pack(
            "Audit Pack",
            current_table,
            previous_table=build_literature_benchmark_table(
                "Previous",
                [_build_row("bench-001", "Mc-290", "Reference A", "fail")],
            ),
        )
