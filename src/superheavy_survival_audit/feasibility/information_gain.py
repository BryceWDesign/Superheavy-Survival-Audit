"""
Information-gain ranking across candidate routes.

This module ranks candidate routes by a repository-defined information-gain score.

Important boundaries:
- this is not an experimental scheduling tool
- this is not a production probability estimate
- this is not a claim that a route will succeed in practice

The purpose is narrower:
prioritize candidate routes according to how informative they may be under the
repository's current uncertainty and evidence structure.

Current component weights:
- disagreement signal: 0.35
- observability support: 0.20
- feasibility support: 0.20
- benchmark scarcity: 0.15
- ambiguity retention: 0.10

Interpretation:
- higher disagreement can increase information value because it indicates the
  route may help separate competing explanations
- higher observability and feasibility raise the odds that the disagreement is
  actually interpretable
- higher benchmark scarcity raises priority where the repository has less
  comparison coverage
- lower ambiguity is rewarded via ambiguity retention
"""

from __future__ import annotations

from dataclasses import dataclass

from superheavy_survival_audit.observability import AmbiguityScore, ObservabilityScore
from superheavy_survival_audit.schemas.common import (
    SchemaValidationError,
    require_non_empty,
    require_probability,
)

from .route_scoring import RouteFeasibilityScore


def _clamp_unit_interval(value: float) -> float:
    """Clamp a numeric value into the closed interval [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass(frozen=True, slots=True)
class RouteInformationGainScore:
    """
    Repository-defined information-gain score for a candidate route.
    """

    route_id: str
    target_nuclide_id: str
    disagreement_signal: float
    observability_support: float
    feasibility_support: float
    benchmark_scarcity: float
    ambiguity_retention: float
    composite_score: float
    rank_position: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", require_non_empty(self.route_id, "route_id"))
        object.__setattr__(
            self,
            "target_nuclide_id",
            require_non_empty(self.target_nuclide_id, "target_nuclide_id"),
        )
        object.__setattr__(
            self,
            "disagreement_signal",
            require_probability(self.disagreement_signal, "disagreement_signal"),
        )
        object.__setattr__(
            self,
            "observability_support",
            require_probability(self.observability_support, "observability_support"),
        )
        object.__setattr__(
            self,
            "feasibility_support",
            require_probability(self.feasibility_support, "feasibility_support"),
        )
        object.__setattr__(
            self,
            "benchmark_scarcity",
            require_probability(self.benchmark_scarcity, "benchmark_scarcity"),
        )
        object.__setattr__(
            self,
            "ambiguity_retention",
            require_probability(self.ambiguity_retention, "ambiguity_retention"),
        )
        object.__setattr__(
            self,
            "composite_score",
            require_probability(self.composite_score, "composite_score"),
        )

        if self.rank_position is not None:
            if int(self.rank_position) <= 0:
                raise SchemaValidationError("rank_position must be greater than zero.")
            object.__setattr__(self, "rank_position", int(self.rank_position))


@dataclass(frozen=True, slots=True)
class RouteInformationGainRanking:
    """
    Ranked collection of candidate route information-gain scores.
    """

    ranked_scores: tuple[RouteInformationGainScore, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "ranked_scores", tuple(self.ranked_scores))
        if not self.ranked_scores:
            raise SchemaValidationError("ranked_scores must not be empty.")

        prior_score: float | None = None
        seen_route_ids: set[str] = set()
        expected_rank = 1
        for score in self.ranked_scores:
            if score.route_id in seen_route_ids:
                raise SchemaValidationError(
                    f"Duplicate route_id in ranking: {score.route_id}"
                )
            seen_route_ids.add(score.route_id)

            if score.rank_position != expected_rank:
                raise SchemaValidationError(
                    "rank_position values must start at 1 and increase without gaps."
                )
            expected_rank += 1

            if prior_score is not None and score.composite_score > prior_score + 1e-12:
                raise SchemaValidationError(
                    "ranked_scores must be sorted in non-increasing composite_score order."
                )
            prior_score = score.composite_score

    @property
    def top_route(self) -> RouteInformationGainScore:
        """Return the highest-ranked route."""
        return self.ranked_scores[0]


def rank_routes_by_information_gain(
    route_feasibility_scores: list[RouteFeasibilityScore],
    *,
    observability_scores_by_route_id: dict[str, ObservabilityScore] | None = None,
    ambiguity_scores_by_route_id: dict[str, AmbiguityScore] | None = None,
    disagreement_signal_by_route_id: dict[str, float] | None = None,
    benchmark_coverage_by_route_id: dict[str, float] | None = None,
) -> RouteInformationGainRanking:
    """
    Rank candidate routes by repository-defined information value.

    Inputs:
    - route_feasibility_scores: required feasibility layer outputs
    - observability_scores_by_route_id: optional route-linked observability scores
    - ambiguity_scores_by_route_id: optional route-linked ambiguity scores
    - disagreement_signal_by_route_id: optional values in [0, 1], where higher
      means stronger model disagreement or uncertainty tension
    - benchmark_coverage_by_route_id: optional values in [0, 1], where higher
      means the route is already well benchmarked; scarcity is computed as
      1 - coverage

    Neutral defaults:
    - disagreement_signal: 0.50
    - observability_support: 0.50
    - ambiguity_retention: 0.50
    - benchmark_coverage: 0.50
    """
    if not route_feasibility_scores:
        raise SchemaValidationError("route_feasibility_scores must not be empty.")

    observability_scores_by_route_id = observability_scores_by_route_id or {}
    ambiguity_scores_by_route_id = ambiguity_scores_by_route_id or {}
    disagreement_signal_by_route_id = disagreement_signal_by_route_id or {}
    benchmark_coverage_by_route_id = benchmark_coverage_by_route_id or {}

    scored_routes: list[RouteInformationGainScore] = []
    seen_route_ids: set[str] = set()

    for route_score in route_feasibility_scores:
        if route_score.route_id in seen_route_ids:
            raise SchemaValidationError(
                f"Duplicate route_id in route_feasibility_scores: {route_score.route_id}"
            )
        seen_route_ids.add(route_score.route_id)

        disagreement_signal = disagreement_signal_by_route_id.get(route_score.route_id, 0.50)
        disagreement_signal = require_probability(
            disagreement_signal,
            f"disagreement_signal_by_route_id[{route_score.route_id}]",
        )

        observability = observability_scores_by_route_id.get(route_score.route_id)
        observability_support = (
            0.50 if observability is None else observability.composite_score
        )

        ambiguity = ambiguity_scores_by_route_id.get(route_score.route_id)
        ambiguity_retention = (
            0.50 if ambiguity is None else 1.0 - ambiguity.composite_score
        )
        ambiguity_retention = _clamp_unit_interval(ambiguity_retention)

        coverage = benchmark_coverage_by_route_id.get(route_score.route_id, 0.50)
        coverage = require_probability(
            coverage,
            f"benchmark_coverage_by_route_id[{route_score.route_id}]",
        )
        benchmark_scarcity = _clamp_unit_interval(1.0 - coverage)

        composite_score = _clamp_unit_interval(
            (0.35 * disagreement_signal)
            + (0.20 * observability_support)
            + (0.20 * route_score.composite_score)
            + (0.15 * benchmark_scarcity)
            + (0.10 * ambiguity_retention)
        )

        scored_routes.append(
            RouteInformationGainScore(
                route_id=route_score.route_id,
                target_nuclide_id=route_score.target_nuclide_id,
                disagreement_signal=disagreement_signal,
                observability_support=observability_support,
                feasibility_support=route_score.composite_score,
                benchmark_scarcity=benchmark_scarcity,
                ambiguity_retention=ambiguity_retention,
                composite_score=composite_score,
            )
        )

    ranked = sorted(
        scored_routes,
        key=lambda item: (-item.composite_score, item.route_id),
    )

    ranked_with_positions = tuple(
        RouteInformationGainScore(
            route_id=item.route_id,
            target_nuclide_id=item.target_nuclide_id,
            disagreement_signal=item.disagreement_signal,
            observability_support=item.observability_support,
            feasibility_support=item.feasibility_support,
            benchmark_scarcity=item.benchmark_scarcity,
            ambiguity_retention=item.ambiguity_retention,
            composite_score=item.composite_score,
            rank_position=index + 1,
        )
        for index, item in enumerate(ranked)
    )

    return RouteInformationGainRanking(ranked_scores=ranked_with_positions)
