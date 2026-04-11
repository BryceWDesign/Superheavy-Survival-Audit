"""
Target, separator, and handling constraint abstractions.

This module adds a non-operational constraint layer for route analysis.
It does not describe how to run an experiment. It only provides a structured,
auditable way to represent broad bottleneck classes that commonly dominate
whether a route looks more or less constrained.

Constraint categories covered here:
- target constraints
- separator constraints
- handling constraints
- detection coupling constraints

The purpose is to let the repository carry route bottleneck structure explicitly
instead of hiding it inside one opaque penalty number.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from superheavy_survival_audit.schemas import RouteRecord
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


class ConstraintSeverity(str, Enum):
    """
    Supported qualitative constraint severities.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


_SEVERITY_TO_PENALTY: dict[ConstraintSeverity, float] = {
    ConstraintSeverity.VERY_LOW: 0.10,
    ConstraintSeverity.LOW: 0.25,
    ConstraintSeverity.MODERATE: 0.50,
    ConstraintSeverity.HIGH: 0.75,
    ConstraintSeverity.EXTREME: 0.95,
}


@dataclass(frozen=True, slots=True)
class ConstraintProfile:
    """
    Structured non-operational bottleneck profile for one route.
    """

    target_constraint: ConstraintSeverity
    separator_constraint: ConstraintSeverity
    handling_constraint: ConstraintSeverity
    detection_coupling_constraint: ConstraintSeverity
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.notes is not None:
            object.__setattr__(self, "notes", require_non_empty(self.notes, "notes"))

    @property
    def target_penalty(self) -> float:
        """Return the numeric target penalty."""
        return _SEVERITY_TO_PENALTY[self.target_constraint]

    @property
    def separator_penalty(self) -> float:
        """Return the numeric separator penalty."""
        return _SEVERITY_TO_PENALTY[self.separator_constraint]

    @property
    def handling_penalty(self) -> float:
        """Return the numeric handling penalty."""
        return _SEVERITY_TO_PENALTY[self.handling_constraint]

    @property
    def detection_coupling_penalty(self) -> float:
        """Return the numeric detection-coupling penalty."""
        return _SEVERITY_TO_PENALTY[self.detection_coupling_constraint]


@dataclass(frozen=True, slots=True)
class RouteConstraintAssessment:
    """
    Summarized constraint assessment for a route.
    """

    route_id: str
    target_nuclide_id: str
    target_penalty: float
    separator_penalty: float
    handling_penalty: float
    detection_coupling_penalty: float
    mean_penalty: float
    bottleneck_retention: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", require_non_empty(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "target_nuclide_id",
            require_non_empty(self.target_nuclide_id, "target_nuclide_id"),
        )
        object.__setattr__(
            self,
            "target_penalty",
            require_probability(self.target_penalty, "target_penalty"),
        )
        object.__setattr__(
            self,
            "separator_penalty",
            require_probability(self.separator_penalty, "separator_penalty"),
        )
        object.__setattr__(
            self,
            "handling_penalty",
            require_probability(self.handling_penalty, "handling_penalty"),
        )
        object.__setattr__(
            self,
            "detection_coupling_penalty",
            require_probability(
                self.detection_coupling_penalty,
                "detection_coupling_penalty",
            ),
        )
        object.__setattr__(
            self,
            "mean_penalty",
            require_probability(self.mean_penalty, "mean_penalty"),
        )
        object.__setattr__(
            self,
            "bottleneck_retention",
            require_probability(self.bottleneck_retention, "bottleneck_retention"),
        )


def assess_route_constraints(
    route_record: RouteRecord,
    constraint_profile: ConstraintProfile,
) -> RouteConstraintAssessment:
    """
    Convert a qualitative constraint profile into a compact route assessment.

    The resulting bottleneck_retention is defined as 1 - mean_penalty.
    This is still a repository-defined abstraction and should not be read as an
    operational feasibility estimate.
    """
    if not isinstance(constraint_profile, ConstraintProfile):
        raise SchemaValidationError("constraint_profile must be a ConstraintProfile.")

    penalties = [
        constraint_profile.target_penalty,
        constraint_profile.separator_penalty,
        constraint_profile.handling_penalty,
        constraint_profile.detection_coupling_penalty,
    ]
    mean_penalty = sum(penalties) / len(penalties)
    bottleneck_retention = _clamp_unit_interval(1.0 - mean_penalty)

    return RouteConstraintAssessment(
        route_id=route_record.route_id,
        target_nuclide_id=route_record.target_nuclide_id,
        target_penalty=constraint_profile.target_penalty,
        separator_penalty=constraint_profile.separator_penalty,
        handling_penalty=constraint_profile.handling_penalty,
        detection_coupling_penalty=constraint_profile.detection_coupling_penalty,
        mean_penalty=mean_penalty,
        bottleneck_retention=bottleneck_retention,
    )
