# Architecture Overview

This document states the intended architecture of the repository at a high
level. It is not a user guide and it is not the project README.

## High-level layers

The repository is expected to evolve through the following layers:

1. source registration
2. ingestion
3. normalization
4. provenance capture
5. processed snapshot generation
6. observability analysis
7. route-feasibility abstraction
8. uncertainty-aware modeling
9. benchmark generation
10. reproducible release artifacts

## Conceptual data flow

External sources enter the repository through adapters.

Adapters emit records into validated schemas.

Validated records are normalized into processed tables and feature sets while
preserving source identity, access context, and transformation notes.

Processed records feed into:

- observability scoring
- ambiguity scoring
- route-feasibility scoring
- survival-audit modeling
- benchmark comparison
- release artifact generation

## Repository directories

The intended top-level directories are:

- `src/` for package code
- `tests/` for automated tests
- `data/raw/` for raw or near-raw imported records
- `data/processed/` for normalized repository-ready records
- `results/` for generated outputs that are safe to regenerate
- `docs/` for policy, architecture, references, and generated notes

## Non-goals of the architecture

The architecture is not intended to:

- provide laboratory operating instructions
- optimize for minimum file count
- hide transformation steps
- present model output without provenance
- maximize visual drama over audit value

## Design constraints

The architecture should make it easy to answer:

- where did this record come from?
- what transformed it?
- which release produced this output?
- which score is measured versus surrogate?
- what uncertainty was retained, bounded, or lost?
- what benchmark was used and why?

## Release expectation

A release should be reconstructible from the repository state, source metadata,
and the documented transformation logic available at that version.
