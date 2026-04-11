"""
Build deterministic proof-of-concept release artifacts.

This script writes a small, review-friendly artifact pack into results/poc/.
It is intentionally simple, standard-library only, and non-operational.

The outputs are illustrative repository artifacts, not experimental claims.
They exist to prove that the repository can emit coherent release-grade tables,
figures, and an index file from structured internal data.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


REPOSITORY_NAME = "Superheavy-Survival-Audit"
REPOSITORY_VERSION = "0.1.0a0"
GENERATED_DATE = "2026-04-10"


SURVIVAL_ROWS = [
    {
        "nuclide_id": "Mc-290",
        "baseline_survival_score": 0.613,
        "posterior_survival_score": 0.609,
        "monte_carlo_mean_score": 0.608,
        "predictive_lower_score": 0.516,
        "predictive_upper_score": 0.691,
    },
    {
        "nuclide_id": "Mc-291",
        "baseline_survival_score": 0.674,
        "posterior_survival_score": 0.648,
        "monte_carlo_mean_score": 0.646,
        "predictive_lower_score": 0.558,
        "predictive_upper_score": 0.722,
    },
    {
        "nuclide_id": "Mc-288",
        "baseline_survival_score": 0.061,
        "posterior_survival_score": 0.086,
        "monte_carlo_mean_score": 0.089,
        "predictive_lower_score": 0.031,
        "predictive_upper_score": 0.156,
    },
    {
        "nuclide_id": "Lv-292",
        "baseline_survival_score": 0.214,
        "posterior_survival_score": 0.239,
        "monte_carlo_mean_score": 0.241,
        "predictive_lower_score": 0.161,
        "predictive_upper_score": 0.331,
    },
]

ROUTE_INFORMATION_GAIN_ROWS = [
    {
        "rank_position": 1,
        "route_id": "route-a",
        "target_nuclide_id": "Mc-290",
        "disagreement_signal": 0.65,
        "observability_support": 0.80,
        "feasibility_support": 0.657,
        "benchmark_scarcity": 0.50,
        "ambiguity_retention": 0.80,
        "composite_score": 0.688,
    },
    {
        "rank_position": 2,
        "route_id": "route-b",
        "target_nuclide_id": "Mc-291",
        "disagreement_signal": 0.90,
        "observability_support": 0.45,
        "feasibility_support": 0.523,
        "benchmark_scarcity": 0.80,
        "ambiguity_retention": 0.40,
        "composite_score": 0.640,
    },
    {
        "rank_position": 3,
        "route_id": "route-c",
        "target_nuclide_id": "Lv-292",
        "disagreement_signal": 0.40,
        "observability_support": 0.70,
        "feasibility_support": 0.432,
        "benchmark_scarcity": 0.25,
        "ambiguity_retention": 0.90,
        "composite_score": 0.472,
    },
]

BENCHMARK_DELTA_ROWS = [
    {
        "benchmark_id": "bench-001",
        "subject_id": "Mc-290",
        "reference_label": "Reference A",
        "delta_kind": "status_changed",
        "previous_status": "fail",
        "current_status": "mixed",
        "classification": "improved",
    },
    {
        "benchmark_id": "bench-002",
        "subject_id": "Mc-291",
        "reference_label": "Reference B",
        "delta_kind": "unchanged",
        "previous_status": "pass",
        "current_status": "pass",
        "classification": "unchanged",
    },
    {
        "benchmark_id": "bench-003",
        "subject_id": "Lv-292",
        "reference_label": "Reference C",
        "delta_kind": "removed",
        "previous_status": "informational",
        "current_status": "missing",
        "classification": "removed",
    },
    {
        "benchmark_id": "bench-004",
        "subject_id": "Ts-294",
        "reference_label": "Reference D",
        "delta_kind": "added",
        "previous_status": "missing",
        "current_status": "not_run",
        "classification": "added",
    },
]

NEGATIVE_CONTROL_ROWS = [
    {
        "case_id": "nc-001",
        "subject_id": "route-weak-a",
        "score_key": "route-weak-a:info_gain",
        "expected_max_score": 0.40,
        "observed_score": 0.28,
        "breach_margin": 0.00,
        "status": "pass",
    },
    {
        "case_id": "nc-002",
        "subject_id": "chain-ambiguous-b",
        "score_key": "chain-ambiguous-b:observability",
        "expected_max_score": 0.35,
        "observed_score": 0.30,
        "breach_margin": 0.00,
        "status": "pass",
    },
]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a CSV file from a list of dictionaries."""
    if not rows:
        raise ValueError("rows must not be empty")

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    """Write a JSON file with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _bar_chart_svg(rows: list[dict[str, object]]) -> str:
    """Build a simple static SVG bar chart for route information gain."""
    width = 760
    height = 360
    chart_left = 90
    chart_top = 60
    chart_bottom = 300
    chart_height = chart_bottom - chart_top
    bar_width = 110
    gap = 70

    max_value = 1.0
    bars: list[str] = []
    labels: list[str] = []

    for index, row in enumerate(rows):
        value = float(row["composite_score"])
        x = chart_left + index * (bar_width + gap)
        bar_height = int(chart_height * (value / max_value))
        y = chart_bottom - bar_height

        bars.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" '
            f'fill="#5B8DEF" stroke="#1F2937" stroke-width="1" />'
        )
        labels.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{chart_bottom + 24}" '
            f'font-size="14" text-anchor="middle" fill="#111827">{row["route_id"]}</text>'
        )
        labels.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{y - 10}" '
            f'font-size="13" text-anchor="middle" fill="#111827">{value:.3f}</text>'
        )

    y_ticks = []
    for tick in range(0, 6):
        tick_value = tick * 0.2
        y = chart_bottom - int(chart_height * tick_value)
        y_ticks.append(
            f'<line x1="{chart_left - 8}" y1="{y}" x2="{chart_left}" y2="{y}" '
            f'stroke="#374151" stroke-width="1" />'
        )
        y_ticks.append(
            f'<text x="{chart_left - 16}" y="{y + 5}" font-size="12" '
            f'text-anchor="end" fill="#374151">{tick_value:.1f}</text>'
        )
        y_ticks.append(
            f'<line x1="{chart_left}" y1="{y}" x2="{width - 40}" y2="{y}" '
            f'stroke="#E5E7EB" stroke-width="1" />'
        )

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect x="0" y="0" width="100%" height="100%" fill="white" />',
            '<text x="380" y="28" font-size="22" text-anchor="middle" fill="#111827">PoC Route Information Gain Ranking</text>',
            '<text x="380" y="48" font-size="12" text-anchor="middle" fill="#4B5563">Repository-defined illustration only; not an experimental claim</text>',
            f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#374151" stroke-width="2" />',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{width - 40}" y2="{chart_bottom}" stroke="#374151" stroke-width="2" />',
            *y_ticks,
            *bars,
            *labels,
            '<text x="24" y="180" font-size="14" transform="rotate(-90 24,180)" text-anchor="middle" fill="#111827">Composite score</text>',
            '<text x="380" y="342" font-size="14" text-anchor="middle" fill="#111827">Candidate routes</text>',
            "</svg>",
        ]
    )


def _scatter_svg(
    survival_rows: list[dict[str, object]],
    route_rows: list[dict[str, object]],
) -> str:
    """Build a simple static SVG scatter plot linking survival and route priority."""
    width = 760
    height = 360
    chart_left = 90
    chart_top = 60
    chart_right = 700
    chart_bottom = 300
    chart_width = chart_right - chart_left
    chart_height = chart_bottom - chart_top

    survival_by_nuclide = {
        row["nuclide_id"]: float(row["posterior_survival_score"]) for row in survival_rows
    }

    x_ticks = []
    y_ticks = []
    for tick in range(0, 6):
        tick_value = tick * 0.2
        x = chart_left + int(chart_width * tick_value)
        y = chart_bottom - int(chart_height * tick_value)

        x_ticks.append(
            f'<line x1="{x}" y1="{chart_bottom}" x2="{x}" y2="{chart_bottom + 8}" '
            f'stroke="#374151" stroke-width="1" />'
        )
        x_ticks.append(
            f'<text x="{x}" y="{chart_bottom + 24}" font-size="12" '
            f'text-anchor="middle" fill="#374151">{tick_value:.1f}</text>'
        )
        x_ticks.append(
            f'<line x1="{x}" y1="{chart_top}" x2="{x}" y2="{chart_bottom}" '
            f'stroke="#E5E7EB" stroke-width="1" />'
        )

        y_ticks.append(
            f'<line x1="{chart_left - 8}" y1="{y}" x2="{chart_left}" y2="{y}" '
            f'stroke="#374151" stroke-width="1" />'
        )
        y_ticks.append(
            f'<text x="{chart_left - 16}" y="{y + 5}" font-size="12" '
            f'text-anchor="end" fill="#374151">{tick_value:.1f}</text>'
        )
        y_ticks.append(
            f'<line x1="{chart_left}" y1="{y}" x2="{chart_right}" y2="{y}" '
            f'stroke="#E5E7EB" stroke-width="1" />'
        )

    points: list[str] = []
    labels: list[str] = []
    for row in route_rows:
        nuclide_id = str(row["target_nuclide_id"])
        x_value = survival_by_nuclide.get(nuclide_id, 0.0)
        y_value = float(row["composite_score"])

        x = chart_left + int(chart_width * x_value)
        y = chart_bottom - int(chart_height * y_value)

        points.append(
            f'<circle cx="{x}" cy="{y}" r="7" fill="#10B981" stroke="#1F2937" stroke-width="1.5" />'
        )
        labels.append(
            f'<text x="{x + 10}" y="{y - 8}" font-size="12" fill="#111827">{nuclide_id}</text>'
        )

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect x="0" y="0" width="100%" height="100%" fill="white" />',
            '<text x="380" y="28" font-size="22" text-anchor="middle" fill="#111827">PoC Survival vs. Route Information Gain</text>',
            '<text x="380" y="48" font-size="12" text-anchor="middle" fill="#4B5563">Posterior survival score on x-axis; information-gain score on y-axis</text>',
            f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#374151" stroke-width="2" />',
            f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#374151" stroke-width="2" />',
            *x_ticks,
            *y_ticks,
            *points,
            *labels,
            '<text x="395" y="342" font-size="14" text-anchor="middle" fill="#111827">Posterior survival score</text>',
            '<text x="26" y="180" font-size="14" transform="rotate(-90 26,180)" text-anchor="middle" fill="#111827">Information-gain score</text>',
            "</svg>",
        ]
    )


def build_poc_release_artifacts(repo_root: Path) -> None:
    """Write deterministic proof-of-concept artifacts into results/poc/."""
    results_root = repo_root / "results" / "poc"
    tables_root = results_root / "tables"
    figures_root = results_root / "figures"

    _write_csv(tables_root / "poc_survival_summary.csv", SURVIVAL_ROWS)
    _write_csv(tables_root / "poc_route_information_gain.csv", ROUTE_INFORMATION_GAIN_ROWS)
    _write_csv(tables_root / "poc_benchmark_deltas.csv", BENCHMARK_DELTA_ROWS)
    _write_csv(tables_root / "poc_negative_controls.csv", NEGATIVE_CONTROL_ROWS)

    figures_root.mkdir(parents=True, exist_ok=True)
    (figures_root / "poc_route_information_gain.svg").write_text(
        _bar_chart_svg(ROUTE_INFORMATION_GAIN_ROWS),
        encoding="utf-8",
    )
    (figures_root / "poc_survival_vs_information_gain.svg").write_text(
        _scatter_svg(SURVIVAL_ROWS, ROUTE_INFORMATION_GAIN_ROWS),
        encoding="utf-8",
    )

    _write_json(
        results_root / "poc_release_index.json",
        {
            "repository_name": REPOSITORY_NAME,
            "repository_version": REPOSITORY_VERSION,
            "generated_date": GENERATED_DATE,
            "artifact_pack_label": "proof_of_concept_release_artifacts",
            "notes": [
                "Illustrative repository outputs only.",
                "These artifacts are deterministic and non-operational.",
                "Scores remain repository-defined surrogates.",
            ],
            "tables": [
                "results/poc/tables/poc_survival_summary.csv",
                "results/poc/tables/poc_route_information_gain.csv",
                "results/poc/tables/poc_benchmark_deltas.csv",
                "results/poc/tables/poc_negative_controls.csv",
            ],
            "figures": [
                "results/poc/figures/poc_route_information_gain.svg",
                "results/poc/figures/poc_survival_vs_information_gain.svg",
            ],
        },
    )


if __name__ == "__main__":
    build_poc_release_artifacts(Path(__file__).resolve().parents[2])
