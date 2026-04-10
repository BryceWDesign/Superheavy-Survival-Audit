# Contributing to Superheavy-Survival-Audit

Thank you for contributing.

This repository is built around a narrow standard: claims must remain smaller
than the uncertainty surrounding them. Contributions are welcome when they
improve reproducibility, provenance, benchmarking, uncertainty handling,
observability analysis, or software quality without overstating what the
repository can support.

## Core contribution rules

1. All scientific or technical claims must be traceable.
2. All imported or normalized data must preserve source provenance.
3. Any model term that is not directly measured must be labeled as a surrogate,
   heuristic, prior, or derived construct.
4. Any new score, rank, or plot must state what it can and cannot mean.
5. No contribution may imply that this repository demonstrates experimental
   production, stabilization, control, or practical exploitation of
   superheavy nuclei.
6. Uncertainty handling is mandatory where uncertainty exists upstream.
7. Negative results are valuable and should not be hidden.

## What good contributions look like

Examples of valuable contributions include:

- new ingestion adapters for evaluated nuclear-data sources
- schema improvements that preserve provenance and uncertainty
- benchmark additions tied to literature or database expectations
- stronger validation, testing, and reproducibility
- clearer separation between evidence and interpretation
- route-feasibility abstractions that remain non-operational and
  non-instructional
- documentation that reduces ambiguity or overclaim risk

## What not to contribute

The following are not acceptable:

- speculative claims presented as established facts
- magical or undefined mechanisms
- hidden coefficient changes without documentation
- hand-wavy language about stabilization, activation, unlocking, resonance,
  or field effects without evidence
- practical instructions for producing restricted materials or enabling harmful
  misuse
- unverifiable datasets
- plagiarism or unattributed reuse

## Pull request expectations

Each pull request should include:

- a short summary of what changed
- why the change is needed
- whether the change affects data, models, or benchmarks
- any uncertainty implications
- any new source dependencies
- any tests added or updated
- any claim-boundary implications

## Data and source expectations

When adding or transforming data:

- keep raw and processed forms separate
- record source name, source date if known, access date if relevant,
  version if known, and transformation notes
- never silently overwrite previously versioned processed outputs
- note any assumptions used during normalization

## Model-development expectations

When changing scoring or modeling logic:

- describe the physical or practical motivation
- state whether the term is measured, literature-derived, or repository-defined
- define units where applicable
- provide tests or validation checks
- explain failure modes
- avoid implying causal certainty where only correlation or ranking logic exists

## Documentation style

Prefer:

- precise language
- explicit uncertainty
- direct statements of limitation
- falsification-friendly wording

Avoid:

- hype
- sensational phrasing
- dramatic extrapolation
- language that sounds stronger than the evidence

## Licensing

By contributing to this repository, you agree that your contribution is
submitted under the Apache License, Version 2.0, unless explicitly stated
otherwise in writing and accepted by the repository owner.

## Attribution

Contributors must respect upstream licenses, source terms, and citation norms.
Third-party facts, datasets, and references remain subject to their original
terms.
