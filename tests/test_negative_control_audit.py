from __future__ import annotations

import pytest

from superheavy_survival_audit.benchmarks import (
    NegativeControlCase,
    run_negative_control_audit,
)
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_run_negative_control_audit_passes_when_controls_stay_below_thresholds() -> None:
    cases = [
        NegativeControlCase(
            case_id="nc-001",
            subject_id="route-weak-a",
            score_key="route-weak-a:info_gain",
            expected_max_score=0.40,
            failure_mode_label="over_permissive_route_priority",
            rationale="Weak route should not rank strongly.",
        ),
        NegativeControlCase(
            case_id="nc-002",
            subject_id="chain-ambiguous-b",
            score_key="chain-ambiguous-b:observability",
            expected_max_score=0.35,
            failure_mode_label="over_permissive_chain_legibility",
            rationale="Highly ambiguous chain should not score cleanly.",
        ),
    ]

    summary = run_negative_control_audit(
        cases,
        observed_scores_by_score_key={
            "route-weak-a:info_gain": 0.28,
            "chain-ambiguous-b:observability": 0.30,
        },
        breach_tolerance=0.20,
        severe_breach_margin_threshold=0.15,
    )

    assert summary.total_case_count == 2
    assert summary.breach_count == 0
    assert summary.breach_rate == pytest.approx(0.0)
    assert summary.kill_triggered is False
    assert summary.pass_count == 2


def test_run_negative_control_audit_triggers_kill_on_excessive_breach_rate() -> None:
    cases = [
        NegativeControlCase(
            case_id="nc-001",
            subject_id="route-weak-a",
            score_key="route-weak-a:info_gain",
            expected_max_score=0.40,
            failure_mode_label="over_permissive_route_priority",
            rationale="Weak route should not rank strongly.",
        ),
        NegativeControlCase(
            case_id="nc-002",
            subject_id="chain-ambiguous-b",
            score_key="chain-ambiguous-b:observability",
            expected_max_score=0.35,
            failure_mode_label="over_permissive_chain_legibility",
            rationale="Highly ambiguous chain should not score cleanly.",
        ),
        NegativeControlCase(
            case_id="nc-003",
            subject_id="route-weak-c",
            score_key="route-weak-c:feasibility",
            expected_max_score=0.30,
            failure_mode_label="over_permissive_route_feasibility",
            rationale="Weak feasibility case should remain low.",
        ),
    ]

    summary = run_negative_control_audit(
        cases,
        observed_scores_by_score_key={
            "route-weak-a:info_gain": 0.52,
            "chain-ambiguous-b:observability": 0.30,
            "route-weak-c:feasibility": 0.46,
        },
        breach_tolerance=0.20,
        severe_breach_margin_threshold=0.25,
    )

    assert summary.breach_count == 2
    assert summary.breach_rate == pytest.approx(2 / 3)
    assert summary.kill_triggered is True
    assert summary.severe_breach_count == 0


def test_run_negative_control_audit_triggers_kill_on_single_severe_breach() -> None:
    cases = [
        NegativeControlCase(
            case_id="nc-001",
            subject_id="route-weak-a",
            score_key="route-weak-a:info_gain",
            expected_max_score=0.40,
            failure_mode_label="over_permissive_route_priority",
            rationale="Weak route should not rank strongly.",
        )
    ]

    summary = run_negative_control_audit(
        cases,
        observed_scores_by_score_key={
            "route-weak-a:info_gain": 0.70,
        },
        breach_tolerance=0.50,
        severe_breach_margin_threshold=0.15,
    )

    assert summary.breach_count == 1
    assert summary.max_breach_margin == pytest.approx(0.30)
    assert summary.severe_breach_count == 1
    assert summary.kill_triggered is True


def test_run_negative_control_audit_rejects_missing_observed_score() -> None:
    cases = [
        NegativeControlCase(
            case_id="nc-001",
            subject_id="route-weak-a",
            score_key="route-weak-a:info_gain",
            expected_max_score=0.40,
            failure_mode_label="over_permissive_route_priority",
            rationale="Weak route should not rank strongly.",
        )
    ]

    with pytest.raises(SchemaValidationError):
        run_negative_control_audit(
            cases,
            observed_scores_by_score_key={},
        )
