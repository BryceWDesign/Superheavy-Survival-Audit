from __future__ import annotations

import pytest

from superheavy_survival_audit.modeling import (
    run_survival_component_ablation,
    score_baseline_survival_audit,
)
from superheavy_survival_audit.schemas import DecayRecord, NuclideRecord
from superheavy_survival_audit.schemas.common import SourcePointer


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


def test_run_survival_component_ablation_returns_one_entry_per_component() -> None:
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

    summary = run_survival_component_ablation(
        baseline,
        evidence_strength=10.0,
    )

    assert summary.nuclide_id == "Mc-290"
    assert len(summary.ablations) == 5
    assert summary.posterior_mean_score >= 0.0
    assert summary.most_influential_component.component_name in {
        "half_life_support",
        "daughter_resolution_fraction",
        "alpha_continuity_fraction",
        "q_value_coverage_fraction",
        "low_competition_fraction",
    }


def test_run_survival_component_ablation_identifies_zero_value_component_as_non_helpful() -> None:
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

    summary = run_survival_component_ablation(
        baseline,
        evidence_strength=20.0,
    )

    zero_value_components = {
        entry.component_name
        for entry in summary.ablations
        if summary.component_values[entry.component_name] == pytest.approx(0.0)
    }
    non_helpful_components = {
        entry.component_name
        for entry in summary.ablations
        if entry.score_drop == pytest.approx(0.0)
    }

    assert zero_value_components <= non_helpful_components


def test_run_survival_component_ablation_shows_drop_for_strong_components() -> None:
    nuclide = _build_nuclide("Mc-291", "Mc", 115, 176, 291, 0.83)
    baseline = score_baseline_survival_audit(
        nuclide,
        [
            DecayRecord(
                decay_id="Mc291-alpha",
                parent_nuclide_id="Mc-291",
                daughter_nuclide_id="Nh-287",
                decay_mode="alpha",
                branching_fraction=1.0,
                q_value_mev=10.25,
            ),
        ],
    )

    summary = run_survival_component_ablation(
        baseline,
        evidence_strength=25.0,
    )

    half_life_ablation = next(
        entry for entry in summary.ablations if entry.component_name == "half_life_support"
    )
    alpha_ablation = next(
        entry
        for entry in summary.ablations
        if entry.component_name == "alpha_continuity_fraction"
    )

    assert half_life_ablation.score_drop > 0.0
    assert alpha_ablation.score_drop > 0.0
    assert half_life_ablation.retained_weight_sum < 1.0
    assert sum(half_life_ablation.normalized_remaining_weights.values()) == pytest.approx(
        1.0
    )
