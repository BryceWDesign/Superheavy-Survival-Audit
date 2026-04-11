"""
Route-feasibility scoring engine.

This module provides a conservative, non-operational scoring layer for route
comparison. It is not a laboratory recipe and it must not be read as one.

The purpose is narrower:
- take a canonical RouteRecord
- combine its high-level feasibility metadata with already-derived evidence
  layers from elsewhere in the repository
- optionally incorporate a structured constraint assessment
- return a bounded, auditable route-feasibility score suitable for ranking and
  comparison under explicit assumptions

Current component weights:
- route class prior: 0.20
- feasibility class support: 0.20
- bottleneck retention: 0.20
- observability support: 0.15
- ambiguity retention: 0.10
- mass consensus support: 0.15

Important boundaries:
- the score is repository-defined
- the score does not imply experimental viability
- the score does not encode instructions for synthesis or operation
"""

from __future__ import annotations

from dataclasses import dataclass

from superheavy_survival_audit.modeling import MassResidualConsensus
from superheavy_survival_audit.observability import AmbiguityScore, ObservabilityScore
from superheavy_survival_audit.schemas import RouteRecord
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_probability,
)

from .constraints import RouteConstraintAssessment

_ROUTE_CLASS_PRIORS: dict[str, float] = {
    "fusion_evaporation": 0.55,
    "transfer_reaction": 0.30,
    "multi_nucleon_transfer": 0.35,
    "secondary_beam": 0.25,
    "spallation_derived": 0.20,
    "unknown": 0.15,
}

_FEASIBILITY_CLASS_SUPPORT: dict[str, float] = {
    "very_low": 0.15,
    "low": 0.35,
    "moderate": 0.60,
    "high": 0.80,
    "unknown": 0.50,
}


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass(frozen=True, slots=True)
class RouteFeasibilityScore:
    """
    Repository-defined route-feasibility summary.
    """

    route_id: str
    target_nuclide_id: str
    route_class: str
    route_class_prior: float
    feasibility_class_support: float
    bottleneck_retention: float
    observability_support: float
    ambiguity_retention: float
    mass_consensus_support: float
    composite_score: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", require_non_empty(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "target_nuclide_id",
            require_non_empty(self.target_nuclide_id, "target_nuclide_id"),
        )
        object.__setattr__(
            self,
            "route_class",
            require_non_empty(self.route_class, "route_class"),
        )
        object.__setattr__(
            self,
            "route_class_prior",
            require_probability(self.route_class_prior, "route_class_prior"),
        )
        object.__setattr__(
            self,
            "feasibility_class_support",
            require_probability(
                self.feasibility_class_support,
                "feasibility_class_support",
            ),
        )
        object.__setattr__(
            self,
            "bottleneck_retention",
            require_probability(
                self.bottleneck_retention,
                "bottleneck_retention",
            ),
        )
        object.__setattr__(
            self,
            "observability_support",
            require_probability(
                self.observability_support,
                "observability_support",
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_retention",
            require_probability(
                self.ambiguity_retention,
                "ambiguity_retention",
            ),
        )
        object.__setattr__(
            self,
            "mass_consensus_support",
            require_probability(
                self.mass_consensus_support,
                "mass_consensus_support",
            ),
        )
        object.__setattr__(
            self,
            "composite_score",
            require_probability(self.composite_score, "composite_score"),
        )


def _resolve_bottleneck_retention(
    route_record: RouteRecord,
    constraint_assessment: RouteConstraintAssessment | None,
    feasibility_class_support: float,
) -> float:
    """
    Resolve bottleneck retention from either a structured assessment or the
    route record's direct penalty field.
    """
    if constraint_assessment is not None:
        if constraint_assessment.route_id != route_record.route_id:
            raise SchemaValidationError(
                "constraint_assessment.route_id must match route_record.route_id."
            )
        if constraint_assessment.target_nuclide_id != route_record.target_nuclide_id:
            raise SchemaValidationError(
                "constraint_assessment.target_nuclide_id must match "
                "route_record.target_nuclide_id."
            )
        return constraint_assessment.bottleneck_retention

    if route_record.bottleneck_penalty is None:
        return feasibility_class_support
    return _clamp_unit_interval(1.0 - route_record.bottleneck_penalty)


def score_route_feasibility(
    route_record: RouteRecord,
    *,
    observability_score: ObservabilityScore | None = None,
    ambiguity_score: AmbiguityScore | None = None,
    mass_residual_consensus: MassResidualConsensus | None = None,
    constraint_assessment: RouteConstraintAssessment | None = None,
) -> RouteFeasibilityScore:
    """
    Score one candidate route under the repository's non-operational feasibility logic.

    Neutral evidence defaults:
    - observability support: 0.50
    - ambiguity retention: 0.50
    - mass consensus support: 0.50
    """
    route_class_prior = _ROUTE_CLASS_PRIORS.get(route_record.route_class)
    if route_class_prior is None:
        raise SchemaValidationError(
            f"Unsupported route_class for scoring: {route_record.route_class}"
        )

    feasibility_class_support = _FEASIBILITY_CLASS_SUPPORT.get(
        route_record.feasibility_class
    )
    if feasibility_class_support is None:
        raise SchemaValidationError(
            "Unsupported feasibility_class for scoring: "
            f"{route_record.feasibility_class}"
        )

    bottleneck_retention = _resolve_bottleneck_retention(
        route_record,
        constraint_assessment,
        feasibility_class_support,
    )

    observability_support = (
        0.50 if observability_score is None else observability_score.composite_score
    )
    ambiguity_retention = (
        0.50 if ambiguity_score is None else 1.0 - ambiguity_score.composite_score
    )
    ambiguity_retention = _clamp_unit_interval(ambiguity_retention)

    mass_consensus_support = (
        0.50
        if mass_residual_consensus is None
        else mass_residual_consensus.consensus_score
    )

    composite_score = _clamp_unit_interval(
        (0.20 * route_class_prior)
        + (0.20 * feasibility_class_support)
        + (0.20 * bottleneck_retention)
        + (0.15 * observability_support)
        + (0.10 * ambiguity_retention)
        + (0.15 * mass_consensus_support)
    )

    return RouteFeasibilityScore(
        route_id=route_record.route_id,
        target_nuclide_id=route_record.target_nuclide_id,
        route_class=route_record.route_class,
        route_class_prior=route_class_prior,
        feasibility_class_support=feasibility_class_support,
        bottleneck_retention=bottleneck_retention,
        observability_support=observability_support,
        ambiguity_retention=ambiguity_retention,
        mass_consensus_support=mass_consensus_support,
        composite_score=composite_score,
    )
