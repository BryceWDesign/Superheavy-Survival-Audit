"""
Branch competition and ambiguity scoring.

This module computes a repository-defined ambiguity score for decay branching
structure. The purpose is not to claim true experimental confusion metrics. The
purpose is narrower: estimate how ambiguous a decay interpretation may become
when branching is fragmented, daughters are missing, or branch evidence is
incomplete.

Current score components:
- branch dispersion: how split the branching fractions are across modes
- missing daughter fraction: how often branches do not resolve to daughters
- missing Q-value fraction: how often branches lack Q-value support
- unresolved mass fraction: how much total branch weight lacks daughter linkage

Higher composite scores indicate more ambiguity under this repository's
assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Iterable

from superheavy_survival_audit.schemas import DecayRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_probability,
)


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _normalized_entropy(probabilities: list[float]) -> float:
    """
    Compute normalized Shannon entropy on a probability list.

    Returns 0 when the distribution is fully concentrated and 1 when it is
    maximally dispersed across the provided entries.
    """
    positive = [value for value in probabilities if value > 0.0]
    if len(positive) <= 1:
        return 0.0

    entropy = -sum(value * log(value) for value in positive)
    max_entropy = log(len(positive))
    if max_entropy == 0.0:
        return 0.0
    return _clamp_unit_interval(entropy / max_entropy)


@dataclass(frozen=True, slots=True)
class AmbiguityScore:
    """
    Repository-defined ambiguity summary for a parent nuclide's decay branches.
    """

    parent_nuclide_id: str
    branch_count: int
    normalized_branch_weight_sum: float
    branch_dispersion: float
    missing_daughter_fraction: float
    missing_q_value_fraction: float
    unresolved_mass_fraction: float
    composite_score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parent_nuclide_id",
            require_non_empty(self.parent_nuclide_id, "parent_nuclide_id"),
        )

        if int(self.branch_count) < 0:
            raise SchemaValidationError("branch_count must be zero or greater.")
        object.__setattr__(self, "branch_count", int(self.branch_count))

        object.__setattr__(
            self,
            "normalized_branch_weight_sum",
            require_probability(
                self.normalized_branch_weight_sum,
                "normalized_branch_weight_sum",
            ),
        )
        object.__setattr__(
            self,
            "branch_dispersion",
            require_probability(self.branch_dispersion, "branch_dispersion"),
        )
        object.__setattr__(
            self,
            "missing_daughter_fraction",
            require_probability(
                self.missing_daughter_fraction,
                "missing_daughter_fraction",
            ),
        )
        object.__setattr__(
            self,
            "missing_q_value_fraction",
            require_probability(
                self.missing_q_value_fraction,
                "missing_q_value_fraction",
            ),
        )
        object.__setattr__(
            self,
            "unresolved_mass_fraction",
            require_probability(
                self.unresolved_mass_fraction,
                "unresolved_mass_fraction",
            ),
        )
        object.__setattr__(
            self,
            "composite_score",
            require_probability(self.composite_score, "composite_score"),
        )


def score_branch_competition_ambiguity(
    parent_nuclide_id: str,
    decay_records: Iterable[DecayRecord],
) -> AmbiguityScore:
    """
    Score ambiguity for all branches attached to a parent nuclide.

    Current composite weights:
    - branch dispersion: 0.35
    - missing daughter fraction: 0.25
    - missing Q-value fraction: 0.20
    - unresolved mass fraction: 0.20

    Notes:
    - This is a repository-defined surrogate.
    - It does not claim direct experimental ambiguity.
    - Missing branching fractions are treated conservatively as unknown weight
      and excluded from entropy normalization, while still contributing to
      incompleteness penalties.
    """
    cleaned_parent = require_non_empty(parent_nuclide_id, "parent_nuclide_id")
    branches = [
        record for record in decay_records if record.parent_nuclide_id == cleaned_parent
    ]

    if not branches:
        return AmbiguityScore(
            parent_nuclide_id=cleaned_parent,
            branch_count=0,
            normalized_branch_weight_sum=0.0,
            branch_dispersion=0.0,
            missing_daughter_fraction=0.0,
            missing_q_value_fraction=0.0,
            unresolved_mass_fraction=0.0,
            composite_score=0.0,
        )

    known_branch_weights = [
        float(record.branching_fraction)
        for record in branches
        if record.branching_fraction is not None
    ]
    known_weight_sum = sum(known_branch_weights)

    normalized_probabilities: list[float] = []
    if known_weight_sum > 0.0:
        normalized_probabilities = [
            weight / known_weight_sum for weight in known_branch_weights
        ]

    branch_dispersion = _normalized_entropy(normalized_probabilities)

    missing_daughter_fraction = sum(
        1 for record in branches if record.daughter_nuclide_id is None
    ) / len(branches)

    missing_q_value_fraction = sum(
        1 for record in branches if record.q_value_mev is None
    ) / len(branches)

    if known_weight_sum > 1.0:
        known_weight_sum = 1.0

    unresolved_mass_fraction = sum(
        float(record.branching_fraction)
        for record in branches
        if record.branching_fraction is not None and record.daughter_nuclide_id is None
    )
    if unresolved_mass_fraction > 1.0:
        unresolved_mass_fraction = 1.0

    composite_score = _clamp_unit_interval(
        (0.35 * branch_dispersion)
        + (0.25 * missing_daughter_fraction)
        + (0.20 * missing_q_value_fraction)
        + (0.20 * unresolved_mass_fraction)
    )

    return AmbiguityScore(
        parent_nuclide_id=cleaned_parent,
        branch_count=len(branches),
        normalized_branch_weight_sum=known_weight_sum,
        branch_dispersion=branch_dispersion,
        missing_daughter_fraction=missing_daughter_fraction,
        missing_q_value_fraction=missing_q_value_fraction,
        unresolved_mass_fraction=unresolved_mass_fraction,
        composite_score=composite_score,
    )
