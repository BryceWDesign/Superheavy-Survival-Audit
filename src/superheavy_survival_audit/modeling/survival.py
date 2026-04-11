"""
Baseline survival-audit scoring model.

This module defines the first explicit survival-audit score for the repository.

Important boundaries:
- This is a repository-defined surrogate.
- It is not a claim of physical stabilization.
- It is not a production cross section.
- It is not an experimental viability statement.

The purpose is narrower:
combine a few auditable, interpretable signals into a conservative baseline
score that can later be replaced, stress-tested, or demoted by more rigorous
layers.

Current component weights:
- half-life support: 0.30
- daughter resolution fraction: 0.20
- alpha continuity fraction: 0.20
- Q-value coverage fraction: 0.15
- low-competition fraction: 0.15
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log10
from typing import Iterable

from superheavy_survival_audit.schemas import DecayRecord, NuclideRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_probability,
)

_COMPETITIVE_DECAY_MODES: tuple[str, ...] = (
    "spontaneous_fission",
    "cluster_decay",
    "unknown",
)


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _normalize_half_life_seconds(value: float | None) -> float:
    """
    Normalize half-life support into [0, 1].

    This is intentionally simple and transparent.

    Mapping:
    - values at or below 1e-6 seconds map near 0
    - values at or above 1 second map to 1
    - values in between are log-scaled

    This does not imply that 1 second is a physical threshold of stability.
    It is only a bounded audit scale for comparing short-lived cases.
    """
    if value is None:
        return 0.0
    if value <= 0.0:
        return 0.0

    log_floor = -6.0
    log_ceiling = 0.0
    clipped = min(max(value, 10**log_floor), 10**log_ceiling)
    normalized = (log10(clipped) - log_floor) / (log_ceiling - log_floor)
    return _clamp_unit_interval(normalized)


@dataclass(frozen=True, slots=True)
class SurvivalAuditScore:
    """
    Baseline repository-defined survival-audit summary for one nuclide.
    """

    nuclide_id: str
    branch_count: int
    half_life_support: float
    daughter_resolution_fraction: float
    alpha_continuity_fraction: float
    q_value_coverage_fraction: float
    low_competition_fraction: float
    composite_score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )

        if int(self.branch_count) < 0:
            raise SchemaValidationError("branch_count must be zero or greater.")
        object.__setattr__(self, "branch_count", int(self.branch_count))

        object.__setattr__(
            self,
            "half_life_support",
            require_probability(self.half_life_support, "half_life_support"),
        )
        object.__setattr__(
            self,
            "daughter_resolution_fraction",
            require_probability(
                self.daughter_resolution_fraction,
                "daughter_resolution_fraction",
            ),
        )
        object.__setattr__(
            self,
            "alpha_continuity_fraction",
            require_probability(
                self.alpha_continuity_fraction,
                "alpha_continuity_fraction",
            ),
        )
        object.__setattr__(
            self,
            "q_value_coverage_fraction",
            require_probability(
                self.q_value_coverage_fraction,
                "q_value_coverage_fraction",
            ),
        )
        object.__setattr__(
            self,
            "low_competition_fraction",
            require_probability(
                self.low_competition_fraction,
                "low_competition_fraction",
            ),
        )
        object.__setattr__(
            self,
            "composite_score",
            require_probability(self.composite_score, "composite_score"),
        )


def score_baseline_survival_audit(
    nuclide_record: NuclideRecord,
    decay_records: Iterable[DecayRecord],
) -> SurvivalAuditScore:
    """
    Compute a baseline survival-audit score for a single canonical nuclide record.

    The score only uses branches rooted at the target nuclide and a bounded
    half-life support term from the canonical nuclide record.
    """
    branches = [
        record
        for record in decay_records
        if record.parent_nuclide_id == nuclide_record.nuclide_id
    ]

    half_life_support = _normalize_half_life_seconds(nuclide_record.half_life_seconds)

    if not branches:
        composite_score = _clamp_unit_interval(0.30 * half_life_support)
        return SurvivalAuditScore(
            nuclide_id=nuclide_record.nuclide_id,
            branch_count=0,
            half_life_support=half_life_support,
            daughter_resolution_fraction=0.0,
            alpha_continuity_fraction=0.0,
            q_value_coverage_fraction=0.0,
            low_competition_fraction=0.0,
            composite_score=composite_score,
        )

    branch_count = len(branches)

    daughter_resolution_fraction = sum(
        1 for branch in branches if branch.daughter_nuclide_id is not None
    ) / branch_count

    alpha_continuity_fraction = sum(
        1 for branch in branches if branch.decay_mode == "alpha"
    ) / branch_count

    q_value_coverage_fraction = sum(
        1 for branch in branches if branch.q_value_mev is not None
    ) / branch_count

    competitive_weight = 0.0
    total_known_branching_weight = 0.0
    for branch in branches:
        if branch.branching_fraction is None:
            continue
        total_known_branching_weight += float(branch.branching_fraction)
        if branch.decay_mode in _COMPETITIVE_DECAY_MODES:
            competitive_weight += float(branch.branching_fraction)

    if total_known_branching_weight > 1.0:
        total_known_branching_weight = 1.0
    if competitive_weight > 1.0:
        competitive_weight = 1.0

    if total_known_branching_weight > 0.0:
        low_competition_fraction = _clamp_unit_interval(
            1.0 - (competitive_weight / total_known_branching_weight)
        )
    else:
        low_competition_fraction = 0.5

    composite_score = _clamp_unit_interval(
        (0.30 * half_life_support)
        + (0.20 * daughter_resolution_fraction)
        + (0.20 * alpha_continuity_fraction)
        + (0.15 * q_value_coverage_fraction)
        + (0.15 * low_competition_fraction)
    )

    return SurvivalAuditScore(
        nuclide_id=nuclide_record.nuclide_id,
        branch_count=branch_count,
        half_life_support=half_life_support,
        daughter_resolution_fraction=daughter_resolution_fraction,
        alpha_continuity_fraction=alpha_continuity_fraction,
        q_value_coverage_fraction=q_value_coverage_fraction,
        low_competition_fraction=low_competition_fraction,
        composite_score=composite_score,
    )
