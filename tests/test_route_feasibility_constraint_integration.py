from __future__ import annotations

import pytest

from superheavy_survival_audit.feasibility import (
    ConstraintProfile,
    ConstraintSeverity,
    assess_route_constraints,
    score_route_feasibility,
)
from superheavy_survival_audit.schemas import RouteRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def _build_route(route_id: str = "route-001", target_nuclide_id: str = "Mc-290") -> RouteRecord:
    return RouteRecord(
        route_id=route_id,
        target_nuclide_id=target_nuclide_id,
        route_class="fusion_evaporation",
        descriptor="Candidate non-operational route abstraction.",
        feasibility_class="low",
        bottleneck_penalty=0.75,
    )


def test_score_route_feasibility_prefers_structured_constraint_assessment_when_provided() -> None:
    route = _build_route()
    profile = ConstraintProfile(
        target_constraint=ConstraintSeverity.LOW,
        separator_constraint=ConstraintSeverity.LOW,
        handling_constraint=ConstraintSeverity.LOW,
        detection_coupling_constraint=ConstraintSeverity.LOW,
    )
    assessment = assess_route_constraints(route, profile)

    score_with_assessment = score_route_feasibility(
        route,
        constraint_assessment=assessment,
    )
    score_without_assessment = score_route_feasibility(route)

    assert assessment.bottleneck_retention == pytest.approx(0.75)
    assert score_with_assessment.bottleneck_retention == pytest.approx(0.75)
    assert score_without_assessment.bottleneck_retention == pytest.approx(0.25)
    assert score_with_assessment.composite_score > score_without_assessment.composite_score


def test_score_route_feasibility_accepts_harsher_constraint_assessment_than_inline_penalty() -> None:
    route = _build_route()
    harsh_profile = ConstraintProfile(
        target_constraint=ConstraintSeverity.EXTREME,
        separator_constraint=ConstraintSeverity.HIGH,
        handling_constraint=ConstraintSeverity.HIGH,
        detection_coupling_constraint=ConstraintSeverity.EXTREME,
    )
    harsh_assessment = assess_route_constraints(route, harsh_profile)

    score = score_route_feasibility(
        route,
        constraint_assessment=harsh_assessment,
    )

    assert harsh_assessment.bottleneck_retention < 0.25
    assert score.bottleneck_retention == pytest.approx(harsh_assessment.bottleneck_retention)


def test_score_route_feasibility_rejects_constraint_assessment_route_mismatch() -> None:
    route = _build_route(route_id="route-a")
    other_route = _build_route(route_id="route-b")
    assessment = assess_route_constraints(
        other_route,
        ConstraintProfile(
            target_constraint=ConstraintSeverity.MODERATE,
            separator_constraint=ConstraintSeverity.MODERATE,
            handling_constraint=ConstraintSeverity.MODERATE,
            detection_coupling_constraint=ConstraintSeverity.MODERATE,
        ),
    )

    with pytest.raises(SchemaValidationError):
        score_route_feasibility(
            route,
            constraint_assessment=assessment,
        )


def test_score_route_feasibility_rejects_constraint_assessment_target_mismatch() -> None:
    route = _build_route(route_id="route-a", target_nuclide_id="Mc-290")
    other_route = _build_route(route_id="route-a", target_nuclide_id="Mc-291")
    assessment = assess_route_constraints(
        other_route,
        ConstraintProfile(
            target_constraint=ConstraintSeverity.MODERATE,
            separator_constraint=ConstraintSeverity.MODERATE,
            handling_constraint=ConstraintSeverity.MODERATE,
            detection_coupling_constraint=ConstraintSeverity.MODERATE,
        ),
    )

    with pytest.raises(SchemaValidationError):
        score_route_feasibility(
            route,
            constraint_assessment=assessment,
        )
