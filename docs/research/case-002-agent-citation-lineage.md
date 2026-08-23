# Case 002 research protocol: agent citation lineage

Status: frozen protocol; collection not yet started.

Case 002 asks whether apparent agreement among research agents survives inspection of the sources
and exact spans behind their citations. The pilot is designed to teach a distinct lesson from Case
001: a report, URL, citation, source work, source span, and warranted proposition are different
units.

## Frozen target

> What empirical evidence published or publicly posted by 2026-08-22 measures whether citations
> produced by deep-research agents resolve and actually support the claims made from them?

The dated cutoff prevents a fast-moving product comparison from masquerading as a timeless result.
The question is about public empirical evaluations, not private vendor performance or all agents.

## Collection design

The protocol assigns eight context-isolated runs: four on `gpt-5.6-sol` and four on
`gpt-5.6-terra`, each at requested high reasoning effort. Every run receives the same frozen prompt
with no inherited conversation turns. Unavailable provider system, sampling, or retrieval settings
remain `unknown`.

Different runtime profiles are not different epistemic observers. The matrix gives the project a
bounded set of outputs to inspect; it does not turn eight reports into eight evidence roots.

## What will be inspected

For each citation, later work must resolve:

- requested and final URL, redirect chain, retrieval status, media type, bytes, and digest where
  an artifact can be captured;
- source work, edition, exact span, and license treatment;
- the proposition asserted by the agent and the narrower proposition the span actually supports;
- modality, causality, scope, time, population, metric, comparison-class, and numerical-strength
  changes; and
- shared model, prompt, retrieval, URL, source, span, upstream citation, data, method, and
  derivation dependencies.

The planned public card has no numbers yet. Its grammar is:

> N agent reports → U resolving URL roots → S exact span roots → D warrant roots

Every number must be computed from captured records and relations. Failures and unknowns stay
visible rather than being replaced with a cleaner run.

## Public boundary

The packet may retain the frozen prompt, final answers, citations, and declared public retrieval
receipts. It excludes hidden reasoning, private context, credentials, logged-in state, personal
data, and provider-restricted instructions. Restricted sources receive quote-minimal treatment.

## Authority boundary

This protocol authorizes research collection only under EM-0026. It does not admit a dossier,
alter a public lens, feature Case 002, deploy a site, or establish a universal result about agents.
The full protocol lives in
[`research/how-we-know/agent-citation-lineage/`](../../research/how-we-know/agent-citation-lineage/README.md).
