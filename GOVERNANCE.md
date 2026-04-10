# Governance

## Project owner

**Bryce Lovell**

## Project operating principle

This repository is governed by an evidence-first standard.

The repository exists to audit, compare, rank, and stress-test candidate
superheavy-nuclei interpretations under explicit uncertainty and provenance
constraints. It does not exist to dramatize unsupported mechanisms or to make
claims beyond the reach of the underlying evidence.

## Decision priorities

When tradeoffs appear, decisions should favor:

1. provenance over convenience
2. reproducibility over speed
3. explicit uncertainty over false precision
4. benchmarkability over novelty theater
5. narrower defensible claims over broader weak claims

## Maintainer authority

The maintainer may reject or rewrite contributions that:

- overstate the meaning of outputs
- weaken provenance
- blur the distinction between measured and surrogate quantities
- introduce unsupported operational detail
- reduce reproducibility or test coverage
- conflict with the repository's claim-boundary policy

## Change categories

### Minor changes
Examples:
- typo fixes
- formatting
- documentation clarification
- internal refactors that do not change outputs

These may be accepted quickly if they do not alter scientific interpretation.

### Moderate changes
Examples:
- schema updates
- ingestion adjustments
- new plots
- new benchmarks
- added tests
- expanded neighboring-chain coverage

These should include rationale and validation notes.

### Major changes
Examples:
- new scoring terms
- new ranking systems
- new priors or coefficient families
- route-feasibility model changes
- uncertainty-engine changes
- benchmark reinterpretation

These require a written justification and should clearly state what changed,
why it changed, and what the expected failure modes are.

## Release philosophy

Releases should represent coherent audit stages rather than arbitrary bundles
of files. A release should make it easier, not harder, for an outside reader to
understand:

- what data was used
- how outputs were generated
- what is measured versus inferred
- what changed since the previous release

## Scientific posture

This project values disciplined non-claims.

A cleanly bounded negative result is preferable to an exciting but weak claim.
A model that reveals its own instability is more useful than one that hides it.

## Archival expectations

Releases, generated tables, benchmark packs, and formal notes should be
structured so an external reader can reconstruct what version produced what
result.

## Dispute resolution

When a disagreement exists about wording, modeling, or scope, the repository
defaults to the more conservative interpretation unless stronger evidence
clearly supports the more ambitious one.
