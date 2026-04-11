# Superheavy-Survival-Audit

Superheavy-Survival-Audit is an observability-first, provenance-first research
repository for comparing superheavy-nuclei evidence surfaces under explicit
uncertainty and explicit claim boundaries.

The repository is built to make it easier to inspect:

- what is measured or evaluated upstream
- what is transformed by the repository
- what is a repository-defined surrogate
- where benchmark agreement exists
- where disagreement or instability remains
- where route and chain interpretations become weak or ambiguous

It is deliberately narrower than a hype project.

## Core posture

This repository is designed to be useful without pretending to be more certain
than it is.

That means it prioritizes:

- provenance over convenience
- reproducibility over speed
- benchmarkability over novelty theater
- falsification over handwaving
- bounded claims over dramatic claims

## What this repository is

At `v0.1.0`, this repository is a structured audit scaffold with working code
for:

- canonical schemas for nuclides, decays, routes, and benchmarks
- provenance and source-registry foundations
- reproducibility manifest structures
- ingestion adapters for:
  - IAEA LiveChart-style CSV exports
  - AMDC AME-style mass tables
  - AMDC NUBASE-style nuclide tables
  - structured ENSDF-derived JSON exports
- neighboring-chain support for:
  - Nh
  - Fl
  - Mc
  - Lv
  - Ts
  - Og
- processed snapshot exports with uncertainty linkage
- observability and ambiguity layers
- daughter-chain legibility profiling
- baseline survival-audit scoring
- Bayesian coefficient updates for survival components
- Monte Carlo sensitivity summaries
- leave-one-term-out ablation summaries
- posterior predictive checks
- AME-aligned mass-residual consensus summaries
- route feasibility scoring
- structured route-constraint assessment
- information-gain ranking across candidate routes
- literature-facing benchmark tables
- negative-control audit logic and kill criteria
- reviewer-facing audit pack construction
- proof-of-concept release artifacts in CSV, JSON, and SVG form

## What this repository is not

This repository is not:

- proof that any superheavy nuclide can be stabilized in practice
- a synthesis recipe
- a laboratory instruction set
- an experimental operations plan
- a production cross-section model
- a substitute for real measurement

All central scores in this repository are repository-defined surrogates unless
explicitly stated otherwise.

That boundary is not a disclaimer tucked in the corner. It is part of the
design.

## Repository structure

Top-level layout:

- `src/`
  Core package code.
- `tests/`
  Automated tests and fixtures.
- `data/raw/`
  Raw or near-raw imported source artifacts.
- `data/processed/`
  Processed repository-ready data products.
- `results/`
  Generated artifact outputs, including PoC release artifacts.
- `docs/`
  Policies, architecture, reference specs, and research documentation.
- `manifests/`
  Reproducibility manifest templates.
- `scripts/release/`
  Deterministic release-artifact generation helpers.

## Main package areas

### `schemas/`
Canonical record models for:

- nuclides
- decays
- routes
- benchmarks

### `provenance/`
Source registry and provenance structures used to preserve source identity and
transformation context.

### `reproducibility/`
Snapshot-level manifest structures that bind inputs, outputs, and code paths to
a release or artifact run.

### `ingest/`
File-based, deterministic ingestion adapters for upstream-style exports.

### `region/`
Neighboring-chain utilities for the current superheavy comparison window.

### `processed/`
Processed snapshot export structures with source linkage and uncertainty fields.

### `observability/`
Repository-defined observability, ambiguity, and daughter-chain legibility
surrogates.

### `modeling/`
Repository-defined survival-audit, Bayesian weighting, Monte Carlo sensitivity,
ablation, posterior-check, and mass-residual consensus layers.

### `feasibility/`
Route feasibility, constraint abstraction, and information-gain ranking logic.

### `benchmarks/`
Literature-facing benchmark tables, negative-control checks, and reviewer audit
pack structures.

## Current target region

The current neighboring-chain region supported directly in the repository is:

- Nh
- Fl
- Mc
- Lv
- Ts
- Og

This is a comparison window, not a claim that these are the only nuclides of
interest.

## Current scoring families

### 1. Observability family
Used to inspect how readable or supportable a candidate chain looks under the
repository's own rules.

Includes:

- decay-chain observability
- branch competition ambiguity
- daughter-chain legibility

### 2. Survival-audit family
Used to create a bounded, reviewable survival-style score while exposing weight
assumptions and sensitivity.

Includes:

- baseline survival-audit score
- Bayesian component weighting
- Monte Carlo sensitivity
- ablation analysis
- posterior predictive checks

### 3. Mass-residual family
Used to compare observed AME-style mass records against reference-model
predictions.

Includes:

- residual observation summaries
- spread and sign agreement logic
- consensus scoring

### 4. Route family
Used to represent route constraint structure and prioritize which candidate
routes may be more informative to inspect next.

Includes:

- route feasibility scoring
- structured constraint assessment
- information-gain ranking

## Benchmark and falsification posture

This repository is built to be challenged.

It includes:

- literature-facing benchmark table structures
- negative-control audit logic
- breach-rate tracking
- severe-breach tracking
- kill criteria
- reviewer audit pack generation

The intention is simple:

a scoring layer that cannot survive obvious negative controls should not be
allowed to sound confident.

## Proof-of-concept artifacts

The repository includes a deterministic proof-of-concept artifact pack under
`results/poc/`.

That pack currently includes:

- `results/poc/tables/poc_survival_summary.csv`
- `results/poc/tables/poc_route_information_gain.csv`
- `results/poc/tables/poc_benchmark_deltas.csv`
- `results/poc/tables/poc_negative_controls.csv`
- `results/poc/figures/poc_route_information_gain.svg`
- `results/poc/figures/poc_survival_vs_information_gain.svg`
- `results/poc/poc_release_index.json`

These are illustrative internal outputs.
They are not external validation.

## Policies worth reading first

The repository is meant to be read with its policies, not apart from them.

Start here:

- `docs/policy/CLAIM_BOUNDARY_POLICY.md`
- `docs/policy/RESEARCH_SCOPE_POLICY.md`
- `docs/policy/DATA_VERSIONING_POLICY.md`
- `docs/policy/KILL_CRITERIA_POLICY.md`

Then read:

- `docs/charter/REPOSITORY_CHARTER.md`
- `docs/reference/ARCHITECTURE_OVERVIEW.md`
- `docs/reference/TERMINOLOGY_GLOSSARY.md`

## Research and dependency disclosure

For repository composition and dependency disclosure, see:

- `docs/RESEARCH_BOM.md`
- `docs/reference/DEPENDENCY_MANIFEST.md`
- `sbom.spdx.json`

## Manual review path

A good manual review sequence is:

1. inspect repository policies
2. inspect schemas and provenance models
3. inspect ingestion adapters
4. inspect observability and modeling layers
5. inspect negative-control logic
6. inspect reviewer audit pack logic
7. inspect proof-of-concept artifacts

That order makes it easier to see the boundaries before seeing the scores.

## Version

Current repository version:

- `0.1.0`

Release notes:

- `RELEASE_NOTES.md`

## License

This repository is licensed under:

- `Apache-2.0`

See:

- `LICENSE`
- `NOTICE`

## Citation

Citation metadata is provided in:

- `CITATION.cff`

## Final boundary statement

This repository is trying to be difficult to fool.

It is not trying to sound magical.

That is the point.
