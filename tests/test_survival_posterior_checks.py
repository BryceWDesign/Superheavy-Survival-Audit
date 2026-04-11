from __future__ import annotations

import pytest

from superheavy_survival_audit.modeling import (
    run_survival_posterior_predictive_check,
    score_baseline_survival_audit,
)
from superheavy_survival_audit.schemas import DecayRecord, NuclideRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError, SourcePointer


def _build_nuclide(
    nuclide_id: str,
    symbol: str,
    z_value: int,
    n_value: int,
    a_value: int,
    half_life_seconds: float | None,
) -> NuclideRecord:
    return NuclideRecord(
        nuclide_id=nuclide_id,
        element_symbol=symbol,
        atomic_number_z=z_value,
        neutron_number_n=n_value,
        mass_number_a=a_value,
        half_life_seconds=half_life_seconds,
        source_pointer=SourcePointer(
            source_name="nubase2020",
            source_record_id=nuclide_id.replace("-", ""),
        ),
    )


def test_run_survival_posterior_predictive_check_returns_interval_summary() -> None:
    nuclide = _build_nuclide("Mc-290", "Mc", 115, 175, 290, 0.65)
    baseline = score_baseline_survival_audit(
        nuclide,
        [
            DecayRecord(
                decay_id="Mc290-alpha",
                parent_nuclide_id="Mc-290",
                daughter_nuclide_id="Nh-286",
                decay_mode="alpha",
                branching_fraction=0.82,
                q_value_mev=10.12,
            ),
            DecayRecord(
                decay_id="Mc290-sf",
                parent_nuclide_id="Mc-290",
                decay_mode="spontaneous_fission",
                branching_fraction=0.18,
            ),
        ],
    )

    summary = run_survival_posterior_predictive_check(
        baseline,
        evidence_strength=10.0,
        sample_count=600,
        seed=123,
    )

    assert summary.nuclide_id == "Mc-290"
    assert summary.sample_count == 600
    assert 0.0 <= summary.predictive_lower_score <= summary.predictive_median_score
    assert summary.predictive_median_score <= summary.predictive_upper_score <= 1.0
    assert 0.0 <= summary.reference_percentile <= 1.0
    assert summary.predictive_interval_width >= 0.0


def test_run_survival_posterior_predictive_check_uses_baseline_score_by_default() -> None:
    nuclide = _build_nuclide("Mc-291", "Mc", 115, 176, 291, 0.83)
    baseline = score_baseline_survival_audit(nuclide, [])

    summary = run_survival_posterior_predictive_check(
        baseline,
        evidence_strength=5.0,
        sample_count=400,
        seed=7,
    )

    assert summary.reference_score == pytest.approx(baseline.composite_score)
    assert summary.calibration_gap >= 0.0


def test_run_survival_posterior_predictive_check_respects_custom_reference_score() -> None:
    nuclide = _build_nuclide("Mc-288", "Mc", 115, 173, 288, 0.000002)
    baseline = score_baseline_survival_audit(
        nuclide,
        [
            DecayRecord(
                decay_id="Mc288-sf",
                parent_nuclide_id="Mc-288",
                decay_mode="spontaneous_fission",
                branching_fraction=0.70,
            ),
            DecayRecord(
                decay_id="Mc288-unknown",
                parent_nuclide_id="Mc-288",
                decay_mode="unknown",
                branching_fraction=0.30,
            ),
        ],
    )

    summary = run_survival_posterior_predictive_check(
        baseline,
        evidence_strength=20.0,
        sample_count=500,
        seed=17,
        reference_score=0.10,
    )

    assert summary.reference_score == pytest.approx(0.10)
    assert 0.0 <= summary.reference_percentile <= 1.0


def test_run_survival_posterior_predictive_check_rejects_invalid_interval_mass() -> None:
    nuclide = _build_nuclide("Mc-290", "Mc", 115, 175, 290, 0.65)
    baseline = score_baseline_survival_audit(nuclide, [])

    with pytest.raises(SchemaValidationError):
        run_survival_posterior_predictive_check(
            baseline,
            interval_mass=1.0,
        )
