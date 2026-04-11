from __future__ import annotations

import json
from pathlib import Path

from superheavy_survival_audit.ingest import ENSDFRadiationObservation
from superheavy_survival_audit.observability import (
    build_daughter_chain_legibility_profile,
    score_branch_competition_ambiguity,
    score_decay_chain_observability,
)
from superheavy_survival_audit.schemas import DecayRecord


def _load_scenarios() -> dict[str, object]:
    fixture_path = Path("tests/fixtures/observability_scenarios.sample.json")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _build_decay_records(items: list[dict[str, object]]) -> list[DecayRecord]:
    return [DecayRecord(**item) for item in items]


def _build_radiation_observations(
    items: list[dict[str, object]],
) -> list[ENSDFRadiationObservation]:
    return [ENSDFRadiationObservation(**item) for item in items]


def test_well_supported_chain_scores_better_than_degraded_chain() -> None:
    scenarios = _load_scenarios()

    well_supported = scenarios["well_supported_chain"]
    degraded = scenarios["degraded_chain"]

    well_decay_records = _build_decay_records(well_supported["decay_records"])
    well_radiation = _build_radiation_observations(
        well_supported["radiation_observations"]
    )

    degraded_decay_records = _build_decay_records(degraded["decay_records"])
    degraded_radiation = _build_radiation_observations(
        degraded["radiation_observations"]
    )

    well_observability = score_decay_chain_observability(
        well_supported["root_nuclide_id"],
        well_decay_records,
        radiation_observations=well_radiation,
        max_depth=4,
    )
    degraded_observability = score_decay_chain_observability(
        degraded["root_nuclide_id"],
        degraded_decay_records,
        radiation_observations=degraded_radiation,
        max_depth=4,
    )

    well_ambiguity = score_branch_competition_ambiguity(
        well_supported["root_nuclide_id"],
        well_decay_records,
    )
    degraded_ambiguity = score_branch_competition_ambiguity(
        degraded["root_nuclide_id"],
        degraded_decay_records,
    )

    well_legibility = build_daughter_chain_legibility_profile(
        well_supported["root_nuclide_id"],
        well_decay_records,
        radiation_observations=well_radiation,
        max_depth=4,
    )
    degraded_legibility = build_daughter_chain_legibility_profile(
        degraded["root_nuclide_id"],
        degraded_decay_records,
        radiation_observations=degraded_radiation,
        max_depth=4,
    )

    assert well_observability.composite_score > degraded_observability.composite_score
    assert well_ambiguity.composite_score < degraded_ambiguity.composite_score
    assert well_legibility.mean_node_score > degraded_legibility.mean_node_score


def test_radiation_support_improves_observability_without_changing_branch_ambiguity() -> None:
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
            decay_id="Nh286-alpha",
            parent_nuclide_id="Nh-286",
            daughter_nuclide_id="Rg-282",
            decay_mode="alpha",
            branching_fraction=0.77,
            q_value_mev=9.51,
        ),
    ]

    no_radiation_score = score_decay_chain_observability(
        "Mc-290",
        decay_records,
        radiation_observations=[],
        max_depth=4,
    )

    with_radiation_score = score_decay_chain_observability(
        "Mc-290",
        decay_records,
        radiation_observations=[
            ENSDFRadiationObservation(
                observation_id="Nh286-gamma-001",
                parent_nuclide_id="Nh-286",
                radiation_kind="gamma",
                energy_kev=218.5,
                intensity_fraction=0.42,
            )
        ],
        max_depth=4,
    )

    ambiguity_before = score_branch_competition_ambiguity("Mc-290", decay_records)
    ambiguity_after = score_branch_competition_ambiguity("Mc-290", decay_records)

    assert with_radiation_score.composite_score > no_radiation_score.composite_score
    assert ambiguity_before.composite_score == ambiguity_after.composite_score


def test_branch_fragmentation_raises_ambiguity_and_reduces_legibility() -> None:
    concentrated_branching = [
        DecayRecord(
            decay_id="Mc290-alpha",
            parent_nuclide_id="Mc-290",
            daughter_nuclide_id="Nh-286",
            decay_mode="alpha",
            branching_fraction=1.0,
            q_value_mev=10.12,
        )
    ]

    fragmented_branching = [
        DecayRecord(
            decay_id="Mc290-alpha",
            parent_nuclide_id="Mc-290",
            daughter_nuclide_id="Nh-286",
            decay_mode="alpha",
            branching_fraction=0.50,
            q_value_mev=10.12,
        ),
        DecayRecord(
            decay_id="Mc290-sf",
            parent_nuclide_id="Mc-290",
            decay_mode="spontaneous_fission",
            branching_fraction=0.30,
        ),
        DecayRecord(
            decay_id="Mc290-unknown",
            parent_nuclide_id="Mc-290",
            decay_mode="unknown",
            branching_fraction=0.20,
        ),
    ]

    concentrated_ambiguity = score_branch_competition_ambiguity(
        "Mc-290",
        concentrated_branching,
    )
    fragmented_ambiguity = score_branch_competition_ambiguity(
        "Mc-290",
        fragmented_branching,
    )

    concentrated_legibility = build_daughter_chain_legibility_profile(
        "Mc-290",
        concentrated_branching,
        radiation_observations=[],
        max_depth=4,
    )
    fragmented_legibility = build_daughter_chain_legibility_profile(
        "Mc-290",
        fragmented_branching,
        radiation_observations=[],
        max_depth=4,
    )

    assert fragmented_ambiguity.composite_score > concentrated_ambiguity.composite_score
    assert fragmented_legibility.mean_node_score < concentrated_legibility.mean_node_score


def test_depth_limit_changes_profile_coverage_without_changing_root_identity() -> None:
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
            decay_id="Nh286-alpha",
            parent_nuclide_id="Nh-286",
            daughter_nuclide_id="Rg-282",
            decay_mode="alpha",
            branching_fraction=0.77,
            q_value_mev=9.51,
        ),
        DecayRecord(
            decay_id="Rg282-alpha",
            parent_nuclide_id="Rg-282",
            daughter_nuclide_id="Mt-278",
            decay_mode="alpha",
            branching_fraction=0.64,
            q_value_mev=8.88,
        ),
    ]

    shallow_profile = build_daughter_chain_legibility_profile(
        "Mc-290",
        decay_records,
        radiation_observations=[],
        max_depth=1,
    )
    deeper_profile = build_daughter_chain_legibility_profile(
        "Mc-290",
        decay_records,
        radiation_observations=[],
        max_depth=4,
    )

    assert shallow_profile.root_nuclide_id == deeper_profile.root_nuclide_id == "Mc-290"
    assert shallow_profile.reachable_nuclide_count < deeper_profile.reachable_nuclide_count
    assert shallow_profile.depth_coverage_fraction == 1.0
    assert deeper_profile.depth_coverage_fraction < 1.0
