# Literature Benchmark Table Specification

## Purpose

This document defines the repository's literature-facing benchmark table format.

The table exists to make benchmark comparisons easier to review by humans.
It is not the canonical benchmark store. It is a release-friendly comparison
surface built from benchmark records and explicit interpretive text.

## Required columns

A valid literature-facing benchmark row must contain:

- `benchmark_id`
- `subject_id`
- `benchmark_kind`
- `reference_label`
- `expected_statement`
- `observed_statement`
- `status`
- `citation_key`

## Optional field

A row may also contain:

- `notes`

## Status vocabulary

Allowed status values are:

- `not_run`
- `pass`
- `fail`
- `mixed`
- `informational`

## Why this table exists

The table is designed to answer simple but important review questions quickly:

- what was compared?
- what expectation was used?
- what did the repository observe?
- how was the result classified?
- where should the reviewer look next?

## Scope boundary

This table does not establish scientific truth by itself.

It is only as strong as:

- the underlying benchmark record
- the traceability of the expected statement
- the honesty of the observed statement
- the correctness of the cited source label or citation key

## Review rule

Every expected statement and observed statement should remain narrower than the
evidence supporting it.

If a row sounds stronger than the underlying benchmark can justify, rewrite the
row more conservatively.

## Deterministic ordering

Rows should be ordered deterministically to make release diffs easier to review.

The current repository rule is to sort by:

1. subject identifier
2. benchmark kind
3. reference label
4. benchmark identifier

## Output shape

The benchmark table layer should be able to emit:

- markdown for release notes or audit packs
- JSON-friendly rows for downstream export or inspection
