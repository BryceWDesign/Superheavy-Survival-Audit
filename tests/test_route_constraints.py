from __future__ import annotations

import pytest

from superheavy_survival_audit.feasibility import (
    ConstraintProfile,
    ConstraintSeverity,
    assess_route_constraints,
)
from superheavy_survival_audit.schemas import RouteRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def _build_route() -> RouteRecord:
    return RouteRecord(
        route_id="route-001",
        target_nuclide_id="Mc-290",
        route_class="fusion_evaporation",
        descriptor="Candidate non-operational route abstraction.",
        feasibility_class="low",
        bottleneck_penalty=0.75,
    )


def test_assess_route_constraints_returns_expected_penalty_summary() -> None:
    route = _build_route()
    profile = ConstraintProfile(
        target_constraint=ConstraintSeverity.HIGH,
        separator_constraint=ConstraintSeverity.MODERATE,
        handling_constraint=ConstraintSeverity.LOW,
        detection_coupling_constraint=ConstraintSeverity.MODERATE,
        notes="Illustrative non-operational bottleneck profile.",
    )

    assessment = assess_route_constraints(route, profile)

    assert assessment.route_id == "route-001"
    assert assessment.target_penalty == pytest.approx(0.75)
    assert assessment.separator_penalty == pytest.approx(0.50)
    assert assessment.handling_penalty == pytest.approx(0.25)
    assert assessment.detection_coupling_penalty == pytest.approx(0.50)
    assert assessment.mean_penalty == pytest.approx(0.50)
    assert assessment.bottleneck_retention == pytest.approx(0.50)


def test_assess_route_constraints_penalizes_more_severe_profiles() -> None:
    route = _build_route()

    light_profile = ConstraintProfile(
        target_constraint=ConstraintSeverity.LOW,
        separator_constraint=ConstraintSeverity.LOW,
        handling_constraint=ConstraintSeverity.VERY_LOW,
        detection_coupling_constraint=ConstraintSeverity.LOW,
    )
    harsh_profile = ConstraintProfile(
        target_constraint=ConstraintSeverity.EXTREME,
        separator_constraint=ConstraintSeverity.HIGH,
        handling_constraint=ConstraintSeverity.HIGH,
        detection_coupling_constraint=ConstraintSeverity.EXTREME,
    )

    light_assessment = assess_route_constraints(route, light_profile)
    harsh_assessment = assess_route_constraints(route, harsh_profile)

    assert light_assessment.mean_penalty < harsh_assessment.mean_penalty
    assert light_assessment.bottleneck_retention > harsh_assessment.bottleneck_retention


def test_constraint_profile_accepts_optional_notes() -> None:
    profile = ConstraintProfile(
        target_constraint=ConstraintSeverity.MODERATE,
        separator_constraint=ConstraintSeverity.MODERATE,
        handling_constraint=ConstraintSeverity.MODERATE,
        detection_coupling_constraint=ConstraintSeverity.MODERATE,
        notes="Context preserved.",
    )

    assert profile.notes == "Context preserved."


def test_assess_route_constraints_rejects_invalid_profile_type() -> None:
    route = _build_route()

    with pytest.raises(SchemaValidationError):
        assess_route_constraints(route, "not-a-profile")  # type: ignore[arg-type]
