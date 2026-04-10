"""
Decay-chain observability scoring.

This module is deliberately conservative. It does not claim experimental
visibility. It computes a repository-defined observability score from the
structure and completeness of decay-chain information under explicit,
non-physical scoring assumptions.

The current score emphasizes:
- whether daughters are identified
- whether Q-values are available
- whether downstream radiation observations exist
- whether the reachable chain extends beyond the root nuclide
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from superheavy_survival_audit.ingest import ENSDFRadiationObservation
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


@dataclass(frozen=True, slots=True)
class ObservabilityScore:
    """
    Repository-defined observability summary for a reachable decay chain.
    """

    root_nuclide_id: str
    max_depth: int
    chain_nuclide_ids: tuple[str, ...]
    visited_decay_ids: tuple[str, ...]
    chain_depth: int
    decay_branch_count: int
    daughter_link_fraction: float
    q_value_coverage_fraction: float
    radiation_support_fraction: float
    depth_fraction: float
    composite_score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "root_nuclide_id",
            require_non_empty(self.root_nuclide_id, "root_nuclide_id"),
        )

        depth_value = int(self.max_depth)
        if depth_value <= 0:
            raise SchemaValidationError("max_depth must be greater than zero.")
        object.__setattr__(self, "max_depth", depth_value)

        if int(self.chain_depth) < 0:
            raise SchemaValidationError("chain_depth must be zero or greater.")
        if int(self.decay_branch_count) < 0:
            raise SchemaValidationError("decay_branch_count must be zero or greater.")

        object.__setattr__(self, "chain_depth", int(self.chain_depth))
        object.__setattr__(self, "decay_branch_count", int(self.decay_branch_count))
        object.__setattr__(self, "chain_nuclide_ids", tuple(self.chain_nuclide_ids))
        object.__setattr__(self, "visited_decay_ids", tuple(self.visited_decay_ids))

        object.__setattr__(
            self,
            "daughter_link_fraction",
            require_probability(
                self.daughter_link_fraction,
                "daughter_link_fraction",
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
            "radiation_support_fraction",
            require_probability(
                self.radiation_support_fraction,
                "radiation_support_fraction",
            ),
        )
        object.__setattr__(
            self,
            "depth_fraction",
            require_probability(self.depth_fraction, "depth_fraction"),
        )
        object.__setattr__(
            self,
            "composite_score",
            require_probability(self.composite_score, "composite_score"),
        )


def score_decay_chain_observability(
    root_nuclide_id: str,
    decay_records: Iterable[DecayRecord],
    *,
    radiation_observations: Iterable[ENSDFRadiationObservation] = (),
    max_depth: int = 4,
) -> ObservabilityScore:
    """
    Score reachable decay-chain observability from a root nuclide.

    Scoring notes:
    - This is a repository-defined surrogate.
    - The score reflects chain interpretability under stated assumptions.
    - It is not a prediction of guaranteed experimental detection.

    Current composite weights:
    - daughter link fraction: 0.35
    - Q-value coverage fraction: 0.25
    - radiation support fraction: 0.20
    - depth fraction: 0.20
    """
    cleaned_root = require_non_empty(root_nuclide_id, "root_nuclide_id")
    if max_depth <= 0:
        raise SchemaValidationError("max_depth must be greater than zero.")

    decay_index: dict[str, list[DecayRecord]] = {}
    for record in decay_records:
        decay_index.setdefault(record.parent_nuclide_id, []).append(record)

    radiation_parent_ids = {
        observation.parent_nuclide_id for observation in radiation_observations
    }

    queue: deque[tuple[str, int]] = deque([(cleaned_root, 0)])
    visited_nuclides_order: list[str] = []
    visited_nuclides_seen: set[str] = set()
    visited_decay_ids: list[str] = []
    visited_decay_seen: set[str] = set()

    reachable_branches: list[DecayRecord] = []
    max_reached_depth = 0

    while queue:
        current_nuclide_id, current_depth = queue.popleft()

        if current_nuclide_id not in visited_nuclides_seen:
            visited_nuclides_seen.add(current_nuclide_id)
            visited_nuclides_order.append(current_nuclide_id)

        max_reached_depth = max(max_reached_depth, current_depth)

        if current_depth >= max_depth:
            continue

        for branch in decay_index.get(current_nuclide_id, []):
            reachable_branches.append(branch)

            if branch.decay_id not in visited_decay_seen:
                visited_decay_seen.add(branch.decay_id)
                visited_decay_ids.append(branch.decay_id)

            daughter_id = branch.daughter_nuclide_id
            if daughter_id is not None and daughter_id not in visited_nuclides_seen:
                queue.append((daughter_id, current_depth + 1))

    branch_count = len(reachable_branches)
    if branch_count == 0:
        return ObservabilityScore(
            root_nuclide_id=cleaned_root,
            max_depth=max_depth,
            chain_nuclide_ids=(cleaned_root,),
            visited_decay_ids=(),
            chain_depth=0,
            decay_branch_count=0,
            daughter_link_fraction=0.0,
            q_value_coverage_fraction=0.0,
            radiation_support_fraction=1.0 if cleaned_root in radiation_parent_ids else 0.0,
            depth_fraction=0.0,
            composite_score=0.20 if cleaned_root in radiation_parent_ids else 0.0,
        )

    daughter_link_fraction = sum(
        1 for branch in reachable_branches if branch.daughter_nuclide_id is not None
    ) / branch_count

    q_value_coverage_fraction = sum(
        1 for branch in reachable_branches if branch.q_value_mev is not None
    ) / branch_count

    supported_nuclides = [
        nuclide_id
        for nuclide_id in visited_nuclides_order
        if nuclide_id in radiation_parent_ids
    ]
    radiation_support_fraction = len(supported_nuclides) / len(visited_nuclides_order)

    depth_fraction = _clamp_unit_interval(max_reached_depth / max_depth)

    composite_score = _clamp_unit_interval(
        (0.35 * daughter_link_fraction)
        + (0.25 * q_value_coverage_fraction)
        + (0.20 * radiation_support_fraction)
        + (0.20 * depth_fraction)
    )

    return ObservabilityScore(
        root_nuclide_id=cleaned_root,
        max_depth=max_depth,
        chain_nuclide_ids=tuple(visited_nuclides_order),
        visited_decay_ids=tuple(visited_decay_ids),
        chain_depth=max_reached_depth,
        decay_branch_count=branch_count,
        daughter_link_fraction=daughter_link_fraction,
        q_value_coverage_fraction=q_value_coverage_fraction,
        radiation_support_fraction=radiation_support_fraction,
        depth_fraction=depth_fraction,
        composite_score=composite_score,
    )
