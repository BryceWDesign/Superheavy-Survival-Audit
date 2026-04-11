# Release Notes

## v0.1.0 — 2026-04-10

This release establishes the first complete public audit scaffold for
`Superheavy-Survival-Audit`.

It is intentionally conservative.

The repository now contains:

- canonical schemas for nuclides, decays, routes, and benchmarks
- provenance models and source registry foundations
- reproducibility manifest structures
- ingestion adapters for IAEA LiveChart, AMDC AME/NUBASE-style tables, and
  structured ENSDF exports
- neighboring-chain support for Nh, Fl, Mc, Lv, Ts, and Og
- processed snapshot export utilities with explicit uncertainty linkage
- observability, ambiguity, and daughter-chain legibility scoring layers
- baseline survival-audit logic plus Bayesian, Monte Carlo, ablation, and
  posterior-predictive extensions
- mass-residual consensus logic for AME-aligned comparison
- route feasibility, structured constraint assessment, and information-gain
  ranking
- literature-facing benchmark tables
- negative-control kill logic
- reviewer audit pack generation surfaces
- proof-of-concept generated tables and SVG figures
- SPDX SBOM and research BOM disclosure files

## What this release is

This release is:

- a disciplined research-audit scaffold
- a provenance-first comparison environment
- a reviewer-friendly evidence packaging system
- an explicit uncertainty and falsification surface

## What this release is not

This release is not:

- proof of superheavy stabilization
- a laboratory procedure
- an operational synthesis plan
- a validated production model
- a substitute for experiment

## Review posture

The recommended way to review this release is:

1. read the README
2. inspect repository policies under `docs/policy/`
3. inspect benchmark and reviewer audit tooling
4. inspect proof-of-concept artifacts under `results/poc/`
5. inspect the negative-control and kill-criteria logic
6. inspect model boundaries before reading any score as if it were a fact

## Notes

All scores in this repository remain repository-defined surrogates unless a
future release explicitly upgrades a layer with stronger external support.

That boundary is intentional and should remain visible.
