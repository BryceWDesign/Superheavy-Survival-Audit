from __future__ import annotations

import pytest

from superheavy_survival_audit.ingest import ENSDFRadiationObservation
from superheavy_survival_audit.observability import score_decay_chain_observability
from superheavy_survival_audit.schemas import DecayRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_score_decay_chain_observability_returns_expected_chain_metrics() -> None:
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
            decay_id="Rg282-sf",
            parent_nuclide_id="Rg-282",
            decay_mode="spontaneous_fission",
            branching_fraction=0.23,
        ),
    ]

    radiation_observations = [
        ENSDFRadiationObservation(
            observation_id="Nh286-gamma-001",
            parent_nuclide_id="Nh-286",
            radiation_kind="gamma",
            energy_kev=218.5,
            intensity_fraction=0.42,
        ),
        ENSDFRadiationObservation(
            observation_id="Rg282-xray-001",
            parent_nuclide_id="Rg-282",
            radiation_kind="xray",
            energy_kev=95.0,
            intensity_fraction=0.18,
        ),
    ]

    score = score_decay_chain_observability(
        "Mc-290",
        decay_records,
        radiation_observations=radiation_observations,
        max_depth=4,
    )

    assert score.root_nuclide_id == "Mc-290"
    assert score.chain_nuclide_ids == ("Mc-290", "Nh-286", "Rg-282")
    assert score.visited_decay_ids == ("Mc290-alpha", "Nh286-alpha", "Rg282-sf")
    assert score.chain_depth == 2
    assert score.decay_branch_count == 3
    assert score.daughter_link_fraction == pytest.approx(2 / 3)
    assert score.q_value_coverage_fraction == pytest.approx(2 / 3)
    assert score.radiation_support_fraction == pytest.approx(2 / 3)
    assert score.depth_fraction == pytest.approx(0.5)
    assert 0.0 <= score.composite_score <= 1.0


def test_score_decay_chain_observability_handles_missing_reachable_branches() -> None:
    score = score_decay_chain_observability(
        "Mc-290",
        [],
        radiation_observations=[],
        max_depth=4,
    )

    assert score.chain_nuclide_ids == ("Mc-290",)
    assert score.visited_decay_ids == ()
    assert score.chain_depth == 0
    assert score.decay_branch_count == 0
    assert score.composite_score == pytest.approx(0.0)


def test_score_decay_chain_observability_rejects_invalid_max_depth() -> None:
    with pytest.raises(SchemaValidationError):
        score_decay_chain_observability(
            "Mc-290",
            [],
            max_depth=0,
        )
