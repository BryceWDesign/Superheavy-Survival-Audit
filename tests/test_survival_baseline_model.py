from __future__ import annotations

import pytest

from superheavy_survival_audit.modeling import score_baseline_survival_audit
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


def test_score_baseline_survival_audit_rewards_supported_alpha_chain() -> None:
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

    score = score_baseline_survival_audit(nuclide, decay_records)

    assert score.nuclide_id == "Mc-290"
    assert score.branch_count == 2
    assert score.half_life_support > 0.0
    assert score.daughter_resolution_fraction == pytest.approx(0.5)
    assert score.alpha_continuity_fraction == pytest.approx(0.5)
    assert score.q_value_coverage_fraction == pytest.approx(0.5)
    assert score.low_competition_fraction == pytest.approx(0.82)
    assert 0.0 <= score.composite_score <= 1.0


def test_score_baseline_survival_audit_handles_missing_branches_conservatively() -> None:
    nuclide = _build_nuclide("Mc-291", "Mc", 115, 176, 291, 0.83)

    score = score_baseline_survival_audit(nuclide, [])

    assert score.branch_count == 0
    assert score.daughter_resolution_fraction == pytest.approx(0.0)
    assert score.alpha_continuity_fraction == pytest.approx(0.0)
    assert score.q_value_coverage_fraction == pytest.approx(0.0)
    assert score.low_competition_fraction == pytest.approx(0.0)
    assert score.composite_score == pytest.approx(0.30 * score.half_life_support)


def test_score_baseline_survival_audit_penalizes_competitive_and_incomplete_branching() -> None:
    nuclide = _build_nuclide("Mc-288", "Mc", 115, 173, 288, 0.000002)
    strong_case = [
        DecayRecord(
            decay_id="Mc288-alpha",
            parent_nuclide_id="Mc-288",
            daughter_nuclide_id="Nh-284",
            decay_mode="alpha",
            branching_fraction=1.0,
            q_value_mev=10.01,
        ),
    ]
    weak_case = [
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
    ]

    strong_score = score_baseline_survival_audit(nuclide, strong_case)
    weak_score = score_baseline_survival_audit(nuclide, weak_case)

    assert strong_score.composite_score > weak_score.composite_score
    assert strong_score.low_competition_fraction == pytest.approx(1.0)
    assert weak_score.low_competition_fraction == pytest.approx(0.0)


def test_score_baseline_survival_audit_ignores_unrelated_parent_branches() -> None:
    nuclide = _build_nuclide("Mc-290", "Mc", 115, 175, 290, 0.65)
    decay_records = [
        DecayRecord(
            decay_id="Nh286-alpha",
            parent_nuclide_id="Nh-286",
            daughter_nuclide_id="Rg-282",
            decay_mode="alpha",
            branching_fraction=0.77,
            q_value_mev=9.51,
        ),
    ]

    score = score_baseline_survival_audit(nuclide, decay_records)

    assert score.branch_count == 0
    assert score.nuclide_id == "Mc-290"
