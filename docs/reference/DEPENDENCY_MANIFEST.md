# Dependency Manifest

## Purpose

This document is the human-readable dependency manifest for the repository.

It complements:

- `pyproject.toml`
- `sbom.spdx.json`
- `docs/RESEARCH_BOM.md`

This file exists so a reviewer can understand, at a glance, what the project
actually depends on at the software level and what it intentionally does not.

## Runtime posture

Current runtime posture:

- Python standard library first
- no third-party runtime package requirement declared in `pyproject.toml`
- deterministic text, CSV, JSON, and SVG output generation
- no required network I/O inside the current repository code paths

That is intentional.

The project is being built to remain inspectable and easy to reproduce before
it grows outward.

## Build dependencies

Current declared build dependencies:

- `setuptools>=69`
- `wheel`

## Python version

Current required Python version:

- `>=3.11`

## Why the dependency surface is intentionally small

This repository is still in its early audit phase.

Keeping the dependency surface small helps with:

- manual review
- deterministic behavior
- reduced packaging noise
- easier provenance inspection
- lower risk of hidden dependency drift

## What is not currently required

The repository currently does not require declared third-party packages for:

- plotting
- dataframe work
- Bayesian sampling
- MCMC frameworks
- numerical linear algebra
- CLI frameworks
- HTTP clients

That may change later, but if it does, the change should be explicit and justified.

## Expected future expansion zones

These are plausible future dependency zones, not locked requirements:

- numerical arrays
- tabular analysis
- plotting
- probabilistic modeling
- scientific serialization helpers

Any future expansion should answer:

- what new capability is gained?
- why is standard-library handling no longer enough?
- what reproducibility cost does the dependency introduce?
- what licensing implications does it add?

## Dependency review rule

Any new dependency should be reviewed for:

- license compatibility
- maintenance maturity
- reproducibility impact
- security and supply-chain implications
- necessity versus convenience

## Manual build note

This repository is currently being assembled through manual browser-based commit
construction. That makes explicit dependency discipline even more important,
because hidden automation assumptions are easier to miss in manual workflows.
