from __future__ import annotations

import pytest

from superheavy_survival_audit.modeling import (
    SurvivalComponentPrior,
    score_baseline_survival_audit,
    score_bayesian_survival_audit,
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


def test_survival_component_prior_has_expected_default_mass() -> None:
    prior = SurvivalComponentPrior()

    assert prior.total_alpha == pytest.approx(10.0)
    assert prior.as_dict()["half_life_support"] == pytest.approx(3.0)
    assert prior.as_dict()["low_competition_fraction"] == pytest.approx(1.5)


def test_score_bayesian_survival_audit_returns_normalized_posterior_weights() -> None:
    nuclide = _build_nuclide("Mc-290", "Mc", 115, 175, 290, 0.65)
    decay_records = [
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
    ]

    baseline = score_baseline_survival_audit(nuclide, decay_records)
    posterior = score_bayesian_survival_audit(baseline, evidence_strength=10.0)

    assert posterior.nuclide_id == "Mc-290"
    assert posterior.evidence_strength == pytest.approx(10.0)
    assert sum(posterior.posterior_mean_weights.values()) == pytest.approx(1.0)
    assert 0.0 <= posterior.posterior_weighted_score <= 1.0


def test_score_bayesian_survival_audit_moves_weight_toward_strong_components() -> None:
    strong_nuclide = _build_nuclide("Mc-290", "Mc", 115, 175, 290, 0.65)
    weak_nuclide = _build_nuclide("Mc-288", "Mc", 115, 173, 288, 0.000002)

    strong_baseline = score_baseline_survival_audit(
        strong_nuclide,
        [
            DecayRecord(
                decay_id="Mc290-alpha",
                parent_nuclide_id="Mc-290",
                daughter_nuclide_id="Nh-286",
                decay_mode="alpha",
                branching_fraction=1.0,
                q_value_mev=10.12,
            )
        ],
    )
    weak_baseline = score_baseline_survival_audit(
        weak_nuclide,
        [
            DecayRecord(
                decay_id="Mc288-unknown",
                parent_nuclide_id="Mc-288",
                decay_mode="unknown",
                branching_fraction=1.0,
            )
        ],
    )

    strong_posterior = score_bayesian_survival_audit(
        strong_baseline,
        evidence_strength=20.0,
    )
    weak_posterior = score_bayesian_survival_audit(
        weak_baseline,
        evidence_strength=20.0,
    )

    assert (
        strong_posterior.posterior_mean_weights["alpha_continuity_fraction"]
        > weak_posterior.posterior_mean_weights["alpha_continuity_fraction"]
    )
    assert (
        strong_posterior.posterior_mean_weights["q_value_coverage_fraction"]
        > weak_posterior.posterior_mean_weights["q_value_coverage_fraction"]
    )
    assert (
        strong_posterior.posterior_weighted_score
        > weak_posterior.posterior_weighted_score
    )


def test_score_bayesian_survival_audit_respects_custom_prior() -> None:
    nuclide = _build_nuclide("Mc-291", "Mc", 115, 176, 291, 0.83)
    baseline = score_baseline_survival_audit(nuclide, [])

    prior = SurvivalComponentPrior(
        half_life_support_alpha=1.0,
        daughter_resolution_alpha=1.0,
        alpha_continuity_alpha=1.0,
        q_value_coverage_alpha=1.0,
        low_competition_alpha=6.0,
    )
    posterior = score_bayesian_survival_audit(
        baseline,
        prior=prior,
        evidence_strength=0.0,
    )

    assert posterior.posterior_mean_weights["low_competition_fraction"] == pytest.approx(
        0.6
    )
    assert posterior.posterior_mean_weights["half_life_support"] == pytest.approx(0.1)


def test_survival_component_prior_rejects_non_positive_alpha() -> None:
    with pytest.raises(SchemaValidationError):
        SurvivalComponentPrior(half_life_support_alpha=0.0)
