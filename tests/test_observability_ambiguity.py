from __future__ import annotations

import pytest

from superheavy_survival_audit.observability import score_branch_competition_ambiguity
from superheavy_survival_audit.schemas import DecayRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def test_score_branch_competition_ambiguity_with_fragmented_branches() -> None:
    decay_records = [
        DecayRecord(
            decay_id="Mc290-alpha",
            parent_nuclide_id="Mc-290",
            daughter_nuclide_id="Nh-286",
            decay_mode="alpha",
            branching_fraction=0.62,
            q_value_mev=10.12,
        ),
        DecayRecord(
            decay_id="Mc290-sf",
            parent_nuclide_id="Mc-290",
            decay_mode="spontaneous_fission",
            branching_fraction=0.28,
        ),
        DecayRecord(
            decay_id="Mc290-cluster",
            parent_nuclide_id="Mc-290",
            decay_mode="cluster_decay",
            branching_fraction=0.10,
        ),
    ]

    score = score_branch_competition_ambiguity("Mc-290", decay_records)

    assert score.parent_nuclide_id == "Mc-290"
    assert score.branch_count == 3
    assert score.normalized_branch_weight_sum == pytest.approx(1.0)
    assert 0.0 < score.branch_dispersion <= 1.0
    assert score.missing_daughter_fraction == pytest.approx(2 / 3)
    assert score.missing_q_value_fraction == pytest.approx(2 / 3)
    assert score.unresolved_mass_fraction == pytest.approx(0.38)
    assert 0.0 <= score.composite_score <= 1.0


def test_score_branch_competition_ambiguity_handles_single_clear_branch() -> None:
    decay_records = [
        DecayRecord(
            decay_id="Mc290-alpha",
            parent_nuclide_id="Mc-290",
            daughter_nuclide_id="Nh-286",
            decay_mode="alpha",
            branching_fraction=1.0,
            q_value_mev=10.12,
        ),
    ]

    score = score_branch_competition_ambiguity("Mc-290", decay_records)

    assert score.branch_count == 1
    assert score.branch_dispersion == pytest.approx(0.0)
    assert score.missing_daughter_fraction == pytest.approx(0.0)
    assert score.missing_q_value_fraction == pytest.approx(0.0)
    assert score.unresolved_mass_fraction == pytest.approx(0.0)
    assert score.composite_score == pytest.approx(0.0)


def test_score_branch_competition_ambiguity_handles_no_matching_parent() -> None:
    score = score_branch_competition_ambiguity("Mc-290", [])

    assert score.branch_count == 0
    assert score.composite_score == pytest.approx(0.0)


def test_score_branch_competition_ambiguity_rejects_blank_parent_id() -> None:
    with pytest.raises(SchemaValidationError):
        score_branch_competition_ambiguity(
            "   ",
            [],
        )
