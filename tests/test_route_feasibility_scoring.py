from __future__ import annotations

import pytest

from superheavy_survival_audit.feasibility import score_route_feasibility
from superheavy_survival_audit.modeling import MassResidualConsensus, MassResidualObservation
from superheavy_survival_audit.observability import AmbiguityScore, ObservabilityScore
from superheavy_survival_audit.schemas import RouteRecord
from superheavy_survival_audit.schemas.common import SchemaValidationError


def _build_observability_score(value: float) -> ObservabilityScore:
    return ObservabilityScore(
        root_nuclide_id="Mc-290",
        max_depth=4,
        chain_nuclide_ids=("Mc-290", "Nh-286"),
        visited_decay_ids=("Mc290-alpha",),
        chain_depth=1,
        decay_branch_count=1,
        daughter_link_fraction=value,
        q_value_coverage_fraction=value,
        radiation_support_fraction=value,
        depth_fraction=value,
        composite_score=value,
    )


def _build_ambiguity_score(value: float) -> AmbiguityScore:
    return AmbiguityScore(
        parent_nuclide_id="Mc-290",
        branch_count=2,
        normalized_branch_weight_sum=1.0,
        branch_dispersion=value,
        missing_daughter_fraction=value,
        missing_q_value_fraction=value,
        unresolved_mass_fraction=value,
        composite_score=value,
    )


def _build_mass_consensus(value: float) -> MassResidualConsensus:
    observation = MassResidualObservation(
        model_name="ws4",
        predicted_mass_excess_kev=136500.0,
        signed_residual_kev=12.0,
        absolute_residual_kev=12.0,
    )
    return MassResidualConsensus(
        nuclide_id="Mc-290",
        observed_mass_excess_kev=136512.0,
        model_count=1,
        majority_sign_label="positive",
        sign_agreement_fraction=1.0,
        mean_signed_residual_kev=12.0,
        mean_absolute_residual_kev=12.0,
        residual_std_kev=0.0,
        accuracy_score=value,
        spread_score=value,
        consensus_score=value,
        residual_observations=(observation,),
    )


def test_score_route_feasibility_rewards_stronger_supporting_evidence() -> None:
    strong_route = RouteRecord(
        route_id="route-strong",
        target_nuclide_id="Mc-290",
        route_class="fusion_evaporation",
        descriptor="High-level candidate route abstraction.",
        feasibility_class="moderate",
        bottleneck_penalty=0.25,
    )
    weak_route = RouteRecord(
        route_id="route-weak",
        target_nuclide_id="Mc-290",
        route_class="unknown",
        descriptor="Poorly constrained route abstraction.",
        feasibility_class="very_low",
        bottleneck_penalty=0.85,
    )

    strong_score = score_route_feasibility(
        strong_route,
        observability_score=_build_observability_score(0.80),
        ambiguity_score=_build_ambiguity_score(0.15),
        mass_residual_consensus=_build_mass_consensus(0.90),
    )
    weak_score = score_route_feasibility(
        weak_route,
        observability_score=_build_observability_score(0.20),
        ambiguity_score=_build_ambiguity_score(0.80),
        mass_residual_consensus=_build_mass_consensus(0.25),
    )

    assert strong_score.route_id == "route-strong"
    assert strong_score.composite_score > weak_score.composite_score
    assert strong_score.bottleneck_retention == pytest.approx(0.75)
    assert weak_score.ambiguity_retention == pytest.approx(0.20)


def test_score_route_feasibility_uses_neutral_defaults_when_evidence_is_missing() -> None:
    route = RouteRecord(
        route_id="route-neutral",
        target_nuclide_id="Mc-291",
        route_class="multi_nucleon_transfer",
        descriptor="Route with no linked evidence yet.",
        feasibility_class="unknown",
        bottleneck_penalty=None,
    )

    score = score_route_feasibility(route)

    assert score.route_class_prior == pytest.approx(0.35)
    assert score.feasibility_class_support == pytest.approx(0.50)
    assert score.bottleneck_retention == pytest.approx(0.50)
    assert score.observability_support == pytest.approx(0.50)
    assert score.ambiguity_retention == pytest.approx(0.50)
    assert score.mass_consensus_support == pytest.approx(0.50)


def test_score_route_feasibility_rejects_unknown_route_class_in_scoring() -> None:
    route = RouteRecord(
        route_id="route-bad",
        target_nuclide_id="Mc-290",
        route_class="unknown",
        descriptor="Valid schema route.",
        feasibility_class="moderate",
    )

    score = score_route_feasibility(route)
    assert score.route_class_prior == pytest.approx(0.15)


def test_score_route_feasibility_handles_high_ambiguity_as_retention_penalty() -> None:
    route = RouteRecord(
        route_id="route-ambiguity",
        target_nuclide_id="Mc-290",
        route_class="fusion_evaporation",
        descriptor="Route with branch competition concerns.",
        feasibility_class="low",
        bottleneck_penalty=0.40,
    )

    low_ambiguity = score_route_feasibility(
        route,
        ambiguity_score=_build_ambiguity_score(0.10),
    )
    high_ambiguity = score_route_feasibility(
        route,
        ambiguity_score=_build_ambiguity_score(0.90),
    )

    assert low_ambiguity.ambiguity_retention > high_ambiguity.ambiguity_retention
    assert low_ambiguity.composite_score > high_ambiguity.composite_score
