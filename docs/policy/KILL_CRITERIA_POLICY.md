# Kill Criteria Policy

## Purpose

This repository should be willing to demote or reject its own scoring layers
when they fail obvious checks.

This policy defines the repository's negative-control kill-criteria posture.

## Why this exists

A scoring system can look clean and still be weak.

One of the fastest ways to catch weak scoring behavior is to define cases that
should stay low-support under the repository's own assumptions and then verify
that they actually do.

If those cases start receiving strong scores, the repository should not keep
speaking confidently.

## Negative-control rule

A negative control is a case that the repository expects to score below a stated
maximum threshold.

Examples include:

- deliberately weak-support route cases
- high-ambiguity chains that should not look clean
- poorly constrained benchmark-scarce cases that should not receive strong
  feasibility-style confidence
- internally degraded scenarios used to stress-test ranking logic

## Required fields for a negative control

Every negative-control case should declare:

- a stable case identifier
- the subject being checked
- the score key being tested
- the maximum allowed score
- the failure mode label
- a short rationale

## Current kill triggers

The current repository kill logic is intentionally simple:

- trigger if the negative-control breach rate is greater than the configured
  breach tolerance
- trigger if any single breach is severe enough to exceed the configured severe
  breach margin threshold

## What a kill means

A triggered kill does not mean the entire repository is worthless.

It means something narrower and important:

- the current scoring layer is over-permissive for the checked cases
- any strong claims based on that layer should be demoted
- the layer should be revised, bounded more tightly, or removed from headline use

## What should happen after a kill

When a kill is triggered, the repository should do one or more of the following:

- move the affected score out of headline ranking use
- raise the issue in release notes
- revise the component structure
- revise thresholds if they were poorly chosen
- add stronger negative controls
- add more explicit warning language around the affected outputs

## Scope boundary

Kill criteria are governance and quality logic.

They are not experimental truth conditions, and they do not replace external
validation.
