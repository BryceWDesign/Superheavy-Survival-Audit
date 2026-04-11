from __future__ import annotations

import pytest

from superheavy_survival_audit.ingest import ENSDFRadiationObservation
from superheavy_survival_audit.observability import (
    build_daughter_chain_legibility_profile,
)
from superheavy_survival_audit.schemas import DecayRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_build_daughter_chain_legibility_profile_returns_plot_ready_nodes() -> None:
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
    ]

    profile = build_daughter_chain_legibility_profile(
        "Mc-290",
        decay_records,
        radiation_observations=radiation_observations,
        max_depth=4,
    )

    assert profile.root_nuclide_id == "Mc-290"
    assert profile.reachable_nuclide_count == 3
    assert profile.depth_coverage_fraction == pytest.approx(0.5)

    rows = profile.to_plot_rows()
    assert [row["nuclide_id"] for row in rows] == ["Mc-290", "Nh-286", "Rg-282"]
    assert rows[0]["depth"] == 0
    assert rows[1]["radiation_support"] == pytest.approx(1.0)
    assert rows[2]["continuation_support"] == pytest.approx(1.0)
    assert 0.0 <= profile.mean_node_score <= 1.0


def test_build_daughter_chain_legibility_profile_handles_root_only_case() -> None:
    profile = build_daughter_chain_legibility_profile(
        "Mc-290",
        [],
        radiation_observations=[],
        max_depth=4,
    )

    assert profile.reachable_nuclide_count == 1
    rows = profile.to_plot_rows()
    assert rows[0]["nuclide_id"] == "Mc-290"
    assert rows[0]["incoming_branch_count"] == 0
    assert rows[0]["outgoing_branch_count"] == 0
    assert profile.depth_coverage_fraction == pytest.approx(0.0)


def test_build_daughter_chain_legibility_profile_rejects_invalid_max_depth() -> None:
    with pytest.raises(SchemaValidationError):
        build_daughter_chain_legibility_profile(
            "Mc-290",
            [],
            max_depth=0,
        )
