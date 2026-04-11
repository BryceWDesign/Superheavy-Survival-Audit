from __future__ import annotations

import pytest

from superheavy_survival_audit.modeling import (
    SurvivalComponentPrior,
    run_survival_weight_monte_carlo,
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


def test_run_survival_weight_monte_carlo_returns_reproducible_summary() -> None:
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

    summary_a = run_survival_weight_monte_carlo(
        baseline,
        evidence_strength=10.0,
        sample_count=500,
        seed=123,
    )
    summary_b = run_survival_weight_monte_carlo(
        baseline,
        evidence_strength=10.0,
        sample_count=500,
        seed=123,
    )

    assert summary_a.nuclide_id == "Mc-290"
    assert summary_a.sample_count == 500
    assert summary_a.seed == 123
    assert summary_a.monte_carlo_mean_score == pytest.approx(
        summary_b.monte_carlo_mean_score
    )
    assert summary_a.lower_quantile_score == pytest.approx(
        summary_b.lower_quantile_score
    )
    assert sum(summary_a.component_mean_weights.values()) == pytest.approx(1.0)


def test_run_survival_weight_monte_carlo_tracks_higher_uncertainty_for_weaker_evidence() -> None:
    nuclide = _build_nuclide("Mc-288", "Mc", 115, 173, 288, 0.000002)
    baseline = score_baseline_survival_audit(
        nuclide,
        [
            DecayRecord(
                decay_id="Mc288-unknown",
                parent_nuclide_id="Mc-288",
                decay_mode="unknown",
                branching_fraction=0.60,
            ),
            DecayRecord(
                decay_id="Mc288-sf",
                parent_nuclide_id="Mc-288",
                decay_mode="spontaneous_fission",
                branching_fraction=0.40,
            ),
        ],
    )

    low_strength = run_survival_weight_monte_carlo(
        baseline,
        evidence_strength=2.0,
        sample_count=600,
        seed=77,
    )
    high_strength = run_survival_weight_monte_carlo(
        baseline,
        evidence_strength=40.0,
        sample_count=600,
        seed=77,
    )

    assert low_strength.monte_carlo_std_score > high_strength.monte_carlo_std_score
    assert low_strength.score_spread > high_strength.score_spread


def test_run_survival_weight_monte_carlo_respects_custom_prior() -> None:
    nuclide = _build_nuclide("Mc-291", "Mc", 115, 176, 291, 0.83)
    baseline = score_baseline_survival_audit(nuclide, [])

    custom_prior = SurvivalComponentPrior(
        half_life_support_alpha=1.0,
        daughter_resolution_alpha=1.0,
        alpha_continuity_alpha=1.0,
        q_value_coverage_alpha=1.0,
        low_competition_alpha=6.0,
    )

    summary = run_survival_weight_monte_carlo(
        baseline,
        prior=custom_prior,
        evidence_strength=0.0,
        sample_count=800,
        seed=19,
    )

    assert summary.component_mean_weights["low_competition_fraction"] == pytest.approx(
        0.6,
        abs=0.03,
    )
    assert summary.component_mean_weights["half_life_support"] == pytest.approx(
        0.1,
        abs=0.03,
    )


def test_run_survival_weight_monte_carlo_rejects_invalid_sample_count() -> None:
    nuclide = _build_nuclide("Mc-290", "Mc", 115, 175, 290, 0.65)
    baseline = score_baseline_survival_audit(nuclide, [])

    with pytest.raises(SchemaValidationError):
        run_survival_weight_monte_carlo(
            baseline,
            sample_count=0,
        )
