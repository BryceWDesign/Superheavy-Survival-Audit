# Research Scope Policy

## Scope

Superheavy-Survival-Audit is a research-audit repository.

Its scope is limited to:

- evaluated and curated nuclear-data ingestion
- provenance-preserving transformation
- uncertainty-aware comparison
- observability and decay-legibility analysis
- route-feasibility abstraction at a non-operational level
- benchmark construction against literature and evaluated data
- reproducible generation of audit artifacts

## Out of scope

The following are outside scope:

- laboratory instructions
- build recipes for restricted experimental systems
- operational synthesis guidance
- unsafe engineering recommendations
- claims of physical realization without evidence
- speculative narrative expansion for its own sake

## Role of patents and adjacent engineering sources

Patents, engineering references, and adjacent process descriptions may be used
as contextual inspiration for abstraction design, bottleneck modeling, or
terminology comparison.

They may not be treated as proof that a route is suitable for superheavy
research, nor as evidence that a method has been validated for the repository's
specific use case.

## Role of machine learning

Machine learning in this repository is allowed only when:

- features are documented
- provenance is preserved
- benchmark performance is reported honestly
- failure modes are discussed
- outputs are not presented as replacing experiment

## Role of uncertainty

Uncertainty is not a footnote. It is part of the product.

Where upstream uncertainty exists, this repository should carry it forward,
bound it, or clearly state why it was not propagated.

## Minimal standard for new modules

A new module should answer at least one of these questions:

- does this improve traceability?
- does this improve benchmarkability?
- does this expose uncertainty more honestly?
- does this make observability or ambiguity more legible?
- does this reduce unsupported interpretation?

If the answer is no, the module probably does not belong.

## Scope creep rule

A proposed addition that increases drama faster than rigor should be rejected.
A proposed addition that narrows ambiguity, improves evidence flow, or reveals
failure modes should be favored.
