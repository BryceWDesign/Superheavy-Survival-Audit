# Reviewer Audit Pack Specification

## Purpose

The reviewer audit pack is a compact review artifact intended to make release
comparison easier.

It is not the canonical store of benchmark truth. It is a reviewer-facing layer
that combines:

- the current literature-facing benchmark table
- optional benchmark deltas relative to a previous table
- optional negative-control summary information

## Why this exists

A release can add rows, remove rows, change statuses, and trigger or clear
negative-control failures. Review becomes much easier when those changes are
made explicit in one place.

The audit pack is designed to answer:

- what changed since the last benchmark snapshot?
- which rows improved?
- which rows worsened?
- were rows added or removed?
- did the negative-control layer trigger a kill condition?

## Delta kinds

Allowed delta kinds are:

- `added`
- `removed`
- `status_changed`
- `unchanged`

## Change classifications

The current repository uses these classifications:

- `added`
- `removed`
- `improved`
- `worsened`
- `changed`
- `unchanged`

A status change is classified by comparing the prior and current status against
the repository's internal severity ordering.

## Current status severity ordering

The current reviewer comparison order is:

1. `fail`
2. `mixed`
3. `not_run`
4. `informational`
5. `pass`

This ordering is only for reviewer comparison and delta classification. It is
not a statement of universal scientific value.

## Negative-control inclusion

If a negative-control summary is attached, the reviewer audit pack should report:

- total controls
- breach count
- breach rate
- severe breach count
- maximum breach margin
- whether kill criteria were triggered

## Output shape

The reviewer audit pack should be able to emit markdown suitable for:

- audit packs
- release notes
- reviewer appendices
- paper-adjacent comparison materials

## Scope boundary

The reviewer audit pack improves interpretability of changes.

It does not itself validate the science.
