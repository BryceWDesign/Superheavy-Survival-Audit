"""
Daughter-chain legibility profiling.

This module builds a plot-ready legibility profile for reachable daughter chains.
It does not claim experimental identifiability. It produces a structured,
repository-defined view of how much chain support exists at each reachable node.

Current node-level legibility components:
- incoming branch support:
  mean of daughter linkage presence and Q-value availability for parent->node edges
- radiation support:
  whether structured radiation observations exist for the node
- continuation support:
  whether the node itself has one or more outgoing branches

Current node composite weights:
- incoming branch support: 0.50
- radiation support: 0.30
- continuation support: 0.20
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
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
class DaughterChainLegibilityNode:
    """
    Plot-ready legibility summary for one reachable nuclide in a decay chain.
    """

    nuclide_id: str
    depth: int
    parent_nuclide_ids: tuple[str, ...]
    incoming_branch_count: int
    outgoing_branch_count: int
    incoming_link_fraction: float
    incoming_q_value_fraction: float
    radiation_support: float
    continuation_support: float
    node_score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nuclide_id",
            require_non_empty(self.nuclide_id, "nuclide_id"),
        )
        if int(self.depth) < 0:
            raise SchemaValidationError("depth must be zero or greater.")
        if int(self.incoming_branch_count) < 0:
            raise SchemaValidationError("incoming_branch_count must be zero or greater.")
        if int(self.outgoing_branch_count) < 0:
            raise SchemaValidationError("outgoing_branch_count must be zero or greater.")

        object.__setattr__(self, "depth", int(self.depth))
        object.__setattr__(self, "incoming_branch_count", int(self.incoming_branch_count))
        object.__setattr__(self, "outgoing_branch_count", int(self.outgoing_branch_count))
        object.__setattr__(self, "parent_nuclide_ids", tuple(self.parent_nuclide_ids))

        object.__setattr__(
            self,
            "incoming_link_fraction",
            require_probability(self.incoming_link_fraction, "incoming_link_fraction"),
        )
        object.__setattr__(
            self,
            "incoming_q_value_fraction",
            require_probability(
                self.incoming_q_value_fraction,
                "incoming_q_value_fraction",
            ),
        )
        object.__setattr__(
            self,
            "radiation_support",
            require_probability(self.radiation_support, "radiation_support"),
        )
        object.__setattr__(
            self,
            "continuation_support",
            require_probability(self.continuation_support, "continuation_support"),
        )
        object.__setattr__(
            self,
            "node_score",
            require_probability(self.node_score, "node_score"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DaughterChainLegibilityProfile:
    """
    Plot-ready legibility profile for a reachable daughter chain.
    """

    root_nuclide_id: str
    max_depth: int
    nodes: tuple[DaughterChainLegibilityNode, ...]
    reachable_nuclide_count: int
    mean_node_score: float
    depth_coverage_fraction: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "root_nuclide_id",
            require_non_empty(self.root_nuclide_id, "root_nuclide_id"),
        )
        if int(self.max_depth) <= 0:
            raise SchemaValidationError("max_depth must be greater than zero.")
        object.__setattr__(self, "max_depth", int(self.max_depth))
        object.__setattr__(self, "nodes", tuple(self.nodes))

        if int(self.reachable_nuclide_count) < 1:
            raise SchemaValidationError(
                "reachable_nuclide_count must be greater than or equal to one."
            )
        object.__setattr__(
            self,
            "reachable_nuclide_count",
            int(self.reachable_nuclide_count),
        )
        object.__setattr__(
            self,
            "mean_node_score",
            require_probability(self.mean_node_score, "mean_node_score"),
        )
        object.__setattr__(
            self,
            "depth_coverage_fraction",
            require_probability(
                self.depth_coverage_fraction,
                "depth_coverage_fraction",
            ),
        )

    def to_plot_rows(self) -> list[dict[str, object]]:
        """
        Return plot-ready rows sorted by depth and nuclide identifier.
        """
        return [
            node.to_dict()
            for node in sorted(self.nodes, key=lambda item: (item.depth, item.nuclide_id))
        ]


def build_daughter_chain_legibility_profile(
    root_nuclide_id: str,
    decay_records: Iterable[DecayRecord],
    *,
    radiation_observations: Iterable[ENSDFRadiationObservation] = (),
    max_depth: int = 4,
) -> DaughterChainLegibilityProfile:
    """
    Build a daughter-chain legibility profile rooted at a parent nuclide.

    Notes:
    - This is a repository-defined surrogate.
    - It is intended to be plot-ready and comparison-friendly.
    - It does not claim guaranteed detection or unambiguous chain recovery.
    """
    cleaned_root = require_non_empty(root_nuclide_id, "root_nuclide_id")
    if max_depth <= 0:
        raise SchemaValidationError("max_depth must be greater than zero.")

    parent_index: dict[str, list[DecayRecord]] = {}
    incoming_index: dict[str, list[DecayRecord]] = {}
    for record in decay_records:
        parent_index.setdefault(record.parent_nuclide_id, []).append(record)
        if record.daughter_nuclide_id is not None:
            incoming_index.setdefault(record.daughter_nuclide_id, []).append(record)

    radiation_parent_ids = {
        observation.parent_nuclide_id for observation in radiation_observations
    }

    visited_depths: dict[str, int] = {cleaned_root: 0}
    queue: deque[tuple[str, int]] = deque([(cleaned_root, 0)])

    while queue:
        current_nuclide_id, current_depth = queue.popleft()
        if current_depth >= max_depth:
            continue

        for branch in parent_index.get(current_nuclide_id, []):
            daughter_id = branch.daughter_nuclide_id
            if daughter_id is None:
                continue

            next_depth = current_depth + 1
            prior_depth = visited_depths.get(daughter_id)
            if prior_depth is None or next_depth < prior_depth:
                visited_depths[daughter_id] = next_depth
                queue.append((daughter_id, next_depth))

    nodes: list[DaughterChainLegibilityNode] = []
    max_reached_depth = 0

    for nuclide_id, depth in sorted(visited_depths.items(), key=lambda item: (item[1], item[0])):
        incoming_branches = incoming_index.get(nuclide_id, [])
        outgoing_branches = parent_index.get(nuclide_id, [])

        if nuclide_id == cleaned_root:
            incoming_link_fraction = 1.0
            incoming_q_value_fraction = 1.0
            parent_nuclide_ids: tuple[str, ...] = ()
        else:
            parent_nuclide_ids = tuple(
                sorted({branch.parent_nuclide_id for branch in incoming_branches})
            )
            incoming_link_fraction = (
                sum(1 for branch in incoming_branches if branch.daughter_nuclide_id is not None)
                / len(incoming_branches)
                if incoming_branches
                else 0.0
            )
            incoming_q_value_fraction = (
                sum(1 for branch in incoming_branches if branch.q_value_mev is not None)
                / len(incoming_branches)
                if incoming_branches
                else 0.0
            )

        radiation_support = 1.0 if nuclide_id in radiation_parent_ids else 0.0
        continuation_support = 1.0 if outgoing_branches else 0.0

        incoming_branch_support = 0.5 * (
            incoming_link_fraction + incoming_q_value_fraction
        )

        node_score = _clamp_unit_interval(
            (0.50 * incoming_branch_support)
            + (0.30 * radiation_support)
            + (0.20 * continuation_support)
        )

        node = DaughterChainLegibilityNode(
            nuclide_id=nuclide_id,
            depth=depth,
            parent_nuclide_ids=parent_nuclide_ids,
            incoming_branch_count=len(incoming_branches),
            outgoing_branch_count=len(outgoing_branches),
            incoming_link_fraction=incoming_link_fraction,
            incoming_q_value_fraction=incoming_q_value_fraction,
            radiation_support=radiation_support,
            continuation_support=continuation_support,
            node_score=node_score,
        )
        nodes.append(node)
        max_reached_depth = max(max_reached_depth, depth)

    mean_node_score = sum(node.node_score for node in nodes) / len(nodes)
    depth_coverage_fraction = _clamp_unit_interval(max_reached_depth / max_depth)

    return DaughterChainLegibilityProfile(
        root_nuclide_id=cleaned_root,
        max_depth=max_depth,
        nodes=tuple(nodes),
        reachable_nuclide_count=len(nodes),
        mean_node_score=mean_node_score,
        depth_coverage_fraction=depth_coverage_fraction,
    )
