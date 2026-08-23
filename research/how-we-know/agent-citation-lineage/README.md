# Case 002 research: agent citation lineage

Status: **frozen trace protocol; no agent traces captured yet; research only**

Task: EM-0026

Working title:

> When agent agreement is really one retrieval lineage

## Question

What empirical evidence published or publicly posted by 2026-08-22 measures whether citations
produced by deep-research agents resolve and actually support the claims made from them?

This is deliberately narrower than “can agents do research?” It asks whether a citation can be
retrieved and whether the examined source span warrants the proposition the agent attached to it.
It does not treat a polished answer, a valid-looking URL, repeated agent agreement, or a different
runtime profile as independent evidence.

## Why this protocol is frozen first

The target, cutoff, prompt, run matrix, capture fields, dependence dimensions, and stop conditions
are fixed before the first trace. That prevents the observed answers from silently changing the
question or collection method. The immutable inputs are:

- [`target-decision.json`](target-decision.json): the suitability and risk decision;
- [`frozen-prompt.md`](frozen-prompt.md): the exact public prompt used in every run;
- [`protocol.json`](protocol.json): the eight-slot matrix and verification rules; and
- [`trace-record-template.json`](trace-record-template.json): the public trace envelope.

`python research/how-we-know/agent-citation-lineage/verify_protocol.py` checks the frozen file
identities and matrix. The later `--require-traces` gate also requires eight terminal records and
verifies every completed answer artifact by digest and byte count.

The protocol records unavailable generation, system, or retrieval settings as `unknown`. A fresh
context excludes inherited conversation turns; it does not prove that provider system context,
pretraining, retrieval infrastructure, or other hidden dependencies are absent.

## Planned accounting

The pilot will derive, rather than type editorially:

1. captured report count;
2. cited URL count and resolving URL roots;
3. source-work and examined-edition roots;
4. exact source-span roots;
5. warrant roots after claim-to-span review;
6. non-resolving, inaccessible, malformed, or unsupported citations; and
7. known and unresolved model, prompt, retrieval, URL, source, span, upstream-citation, and
   derivation dependencies.

The eight reports are observations about the collection process. They are not eight independent
confirmations of their answers.

## Disclosure and licensing

Only the frozen prompt, final answer, citations, declared public retrieval receipts, and
quote-minimal source spans are eligible for this public research packet. Hidden reasoning,
restricted provider context, credentials, personal data, and inherited private conversation are
out of scope. Full copyrighted works are not redistributed. Open-license text retains its exact
license and edition; other works receive metadata, retrieval identity where available, and only
the minimal attributed span needed for warrant review.

## Stop conditions

The candidate fails closed if the trace cannot be captured safely, the question changes after
collection starts, authoritative source editions cannot be re-retrieved, exact spans cannot be
matched, URL uniqueness cannot be separated from source and warrant identity, counts cannot be
reproduced, or an independently rooted reviewer cannot repeat the evidence checks.

No file in this directory is accepted knowledge or a public Case 002 dossier merely because the
protocol or later traces exist.
