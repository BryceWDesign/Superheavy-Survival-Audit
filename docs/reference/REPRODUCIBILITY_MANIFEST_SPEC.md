# Reproducibility Manifest Specification

## Purpose

A reproducibility manifest is the smallest structured record that explains how
a repository-managed artifact set was produced.

It is not a substitute for provenance on individual records. It is a release-
or snapshot-level envelope that ties together:

- repository identity
- source-registry context
- input artifacts
- output artifacts
- code paths
- generation date
- human notes

## Why this exists

This repository is designed to generate processed datasets, benchmarks, plots,
and audit packs that must remain interpretable later.

A manifest makes it possible to answer:

- what repository version produced this?
- which source registry did it rely on?
- what inputs were used?
- what outputs were generated?
- which code paths were involved?
- are two outputs even comparable?

## Required fields

### `manifest_id`
A unique identifier for the manifest.

### `manifest_version`
The version of the manifest format itself.

### `repository_name`
Expected to be `Superheavy-Survival-Audit`.

### `repository_version`
The repository version or release label that produced the artifacts.

### `generated_date`
ISO-8601 calendar date in `YYYY-MM-DD` format.

### `source_registry_path`
The path to the source registry used by the run.

### `input_artifacts`
A non-empty list of repository paths used as inputs.

### `output_artifacts`
A non-empty list of repository paths produced by the run.

### `code_paths`
A non-empty list of repository code paths involved in generation.

## Optional fields

### `source_registry_hash`
A digest or snapshot identity for the source registry file.

### `notes`
Free-text explanation of assumptions, caveats, or run context.

## Interpretation notes

A manifest does not prove that the outputs are scientifically correct.

It proves something narrower and more useful:

- the generation context was recorded
- the input-output relationship was declared
- the repository can point to the code paths involved

## Minimal example

See the template JSON file included in the repository for the expected shape.

## Scope boundary

A reproducibility manifest is not a laboratory log, not an experiment record,
and not a substitute for release notes or benchmark documentation.
