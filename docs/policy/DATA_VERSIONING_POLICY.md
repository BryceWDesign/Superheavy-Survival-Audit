# Data Versioning Policy

## Purpose

This policy defines how raw imports, processed datasets, normalized records,
and generated audit artifacts must be versioned in this repository.

The goal is simple:

- never blur what came from upstream
- never silently replace a processed dataset
- never make it impossible to reconstruct a release output later

## Core rules

1. Raw imports must remain separated from processed outputs.
2. Processed outputs must be reproducible from documented transformations.
3. A processed dataset must never be silently overwritten in a way that hides
   what changed.
4. Every release-grade dataset must be tied to a reproducibility manifest.
5. Upstream source identity, access date, and repository version must remain
   attached to versioned outputs.
6. Regeneration is allowed. Ambiguous regeneration is not.

## Raw data rules

Raw data should live under `data/raw/`.

Raw data should remain as close as practical to the upstream source form.

Allowed raw-data actions include:

- storing downloaded source snapshots
- storing export files from an evaluated database
- storing near-raw API payloads
- recording minimal wrapper metadata required for later traceability

Raw data should not be silently edited by hand unless the edit is explicitly
documented and preserved as a new artifact.

## Processed data rules

Processed data should live under `data/processed/`.

Processed data may include:

- normalized canonical records
- feature tables
- joined benchmark tables
- route-abstraction inputs
- observability-analysis inputs
- release-bound snapshot exports

Every processed dataset should be traceable to:

- one or more raw artifacts
- a transformation path
- a repository version
- a source-registry entry or entries

## Version identity

A dataset version identity should be specific enough to distinguish:

- source state
- repository state
- transformation state

Acceptable examples include:

- repository release tags
- manifest IDs
- dated processed snapshot IDs
- content hashes paired with repository version labels

## Silent overwrite rule

A processed dataset must not be overwritten in a way that destroys the ability
to answer:

- what did this file contain before?
- what changed?
- what repository version changed it?
- did the source change or only the transform?

If a dataset changes meaningfully, preserve that fact through a new manifest,
new snapshot, or explicit version note.

## Schema evolution rule

When schemas evolve:

- document the schema change
- state whether older processed data becomes stale
- state whether migration is required
- avoid pretending that old and new outputs are directly comparable if they are
  not

## Reproducibility manifest rule

Any release-grade processed dataset or generated result set should have a
manifest that records:

- repository name
- repository version
- manifest version
- generated date
- source registry reference
- input artifacts
- output artifacts
- code paths involved
- notes and assumptions

## Data deletion rule

Deletion is allowed only when one of the following is true:

- the file is redundant and reproducible
- the file is invalid and replaced by a corrected version
- the file must be removed for legal, licensing, or integrity reasons

If a release-relevant artifact is removed, the removal should be documented.

## Comparison rule

When comparing two generated artifacts, the repository should be able to state:

- whether the source inputs changed
- whether the transformation logic changed
- whether the benchmark set changed
- whether the schema changed
- whether the uncertainty treatment changed

## Default posture

If a change makes the audit trail weaker, the change should be rejected.
