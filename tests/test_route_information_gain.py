from __future__ import annotations

import pytest

from superheavy_survival_audit.feasibility import rank_routes_by_information_gain
from superheavy_survival_audit.feasibility.route_scoring import RouteFeasibilityScore
from superheavy_survival_audit.observability import AmbiguityScore, ObservabilityScore
from superheavy_survival_audit.schemas.common import SchemaValidationError


def _build_route_score(route_id: str, target_nuclide_id: str, composite: float) -> RouteFeasibilityScore:
    return RouteFeasibilityScore(
        route_id=route_id,
        target_nuclide_id=target_nuclide_id,
        route_class="fusion_evaporation",
        route_class_prior=0.55,
        feasibility_class_support=0.60,
        bottleneck_retention=0.70,
        observability_support=0.50,
        ambiguity_retention=0.50,
        mass_consensus_support=0.50,
        composite_score=composite,
    )


def _build_observability(route_id_score: float) -> ObservabilityScore:
    return ObservabilityScore(
        root_nuclide_id="Mc-290",
        max_depth=4,
        chain_nuclide_ids=("Mc-290", "Nh-286"),
        visited_decay_ids=("Mc290-alpha",),
        chain_depth=1,
        decay_branch_count=1,
        daughter_link_fraction=route_id_score,
        q_value_coverage_fraction=route_id_score,
        radiation_support_fraction=route_id_score,
        depth_fraction=route_id_score,
        composite_score=route_id_score,
    )


def _build_ambiguity(value: float) -> AmbiguityScore:
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


def test_rank_routes_by_information_gain_prioritizes_disagreement_plus_support() -> None:
    route_scores = [
        _build_route_score("route-a", "Mc-290", 0.72),
        _build_route_score("route-b", "Mc-291", 0.55),
        _build_route_score("route-c", "Lv-292", 0.48),
    ]

    ranking = rank_routes_by_information_gain(
        route_scores,
        observability_scores_by_route_id={
            "route-a": _build_observability(0.80),
            "route-b": _build_observability(0.45),
            "route-c": _build_observability(0.70),
        },
        ambiguity_scores_by_route_id={
            "route-a": _build_ambiguity(0.20),
            "route-b": _build_ambiguity(0.60),
            "route-c": _build_ambiguity(0.10),
        },
        disagreement_signal_by_route_id={
            "route-a": 0.65,
            "route-b": 0.90,
            "route-c": 0.40,
        },
        benchmark_coverage_by_route_id={
            "route-a": 0.50,
            "route-b": 0.20,
            "route-c": 0.75,
        },
    )

    assert ranking.top_route.route_id == "route-a"
    assert ranking.ranked_scores[0].rank_position == 1
    assert ranking.ranked_scores[1].rank_position == 2
    assert ranking.ranked_scores[2].rank_position == 3
    assert ranking.ranked_scores[0].composite_score >= ranking.ranked_scores[1].composite_score


def test_rank_routes_by_information_gain_uses_neutral_defaults() -> None:
    route_scores = [
        _build_route_score("route-a", "Mc-290", 0.60),
        _build_route_score("route-b", "Mc-291", 0.60),
    ]

    ranking = rank_routes_by_information_gain(route_scores)

    assert len(ranking.ranked_scores) == 2
    assert ranking.ranked_scores[0].benchmark_scarcity == pytest.approx(0.50)
    assert ranking.ranked_scores[0].observability_support == pytest.approx(0.50)
    assert ranking.ranked_scores[0].ambiguity_retention == pytest.approx(0.50)


def test_rank_routes_by_information_gain_rewards_scarce_and_interpretable_cases() -> None:
    route_scores = [
        _build_route_score("route-a", "Mc-290", 0.58),
        _build_route_score("route-b", "Mc-290", 0.58),
    ]

    ranking = rank_routes_by_information_gain(
        route_scores,
        observability_scores_by_route_id={
            "route-a": _build_observability(0.75),
            "route-b": _build_observability(0.75),
        },
        ambiguity_scores_by_route_id={
            "route-a": _build_ambiguity(0.20),
            "route-b": _build_ambiguity(0.20),
        },
        disagreement_signal_by_route_id={
            "route-a": 0.70,
            "route-b": 0.70,
        },
        benchmark_coverage_by_route_id={
            "route-a": 0.10,
            "route-b": 0.90,
        },
    )

    assert ranking.ranked_scores[0].route_id == "route-a"
    assert ranking.ranked_scores[0].benchmark_scarcity > ranking.ranked_scores[1].benchmark_scarcity


def test_rank_routes_by_information_gain_rejects_invalid_probability_inputs() -> None:
    route_scores = [_build_route_score("route-a", "Mc-290", 0.60)]

    with pytest.raises(SchemaValidationError):
        rank_routes_by_information_gain(
            route_scores,
            disagreement_signal_by_route_id={"route-a": 1.5},
        )
