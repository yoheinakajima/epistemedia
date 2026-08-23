# Case 002 research protocol: agent citation lineage

Status: v1 transport preflight failed and is retained; v2 matrix and author-side source review
complete; independent review pending; research only.

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

The active v2 protocol assigns eight context-isolated runs: four on `gpt-5.6-sol` and four on
`gpt-5.6-terra`, each at requested high reasoning effort. Every run receives the same frozen prompt
with no inherited conversation turns. Unavailable provider system, sampling, or retrieval settings
remain `unknown`.

Before v2 was frozen, the v1 transport preflight detected that one invocation received a prompt
with one extra character. Both started invocations were stopped before final-answer capture. The
failed v1 matrix is not being completed or repaired in place: its exact prompt identities, terminal
statuses, and zero admitted answers remain a negative preflight record. V2 is a separately
identified matrix, not a replacement run inside v1.

Different runtime profiles are not different epistemic observers. The matrix gives the project a
bounded set of outputs to inspect; it does not turn eight reports into eight evidence roots.

## What was inspected

For each citation, later work must resolve:

- requested and final URL, redirect chain, retrieval status, media type, bytes, and digest where
  an artifact can be captured;
- source work, edition, exact span, and license treatment;
- the proposition asserted by the agent and the narrower proposition the span actually supports;
- modality, causality, scope, time, population, metric, comparison-class, and numerical-strength
  changes; and
- shared model, prompt, retrieval, URL, source, span, upstream citation, data, method, and
  derivation dependencies.

The deterministic research-only ledger currently reports:

> 8 agent reports → 30 cited URL strings → 27 resolving URL roots → 11 source works → 14
> examined editions → 72 matched exact-span roots → 7 author-candidate warrant roots → 0
> independently confirmed warrant roots

Every number is computed from captured records and relations. The raw matrix contains 48 citation
occurrences, 127 source-span occurrences, and 52 result claims. Twenty claim occurrences are
unsupported or force-raised after review, including nine whose linked quote fragments do not
support their complete proposition. Thirty-four citation occurrences remain unresolved and
receive no automatic credit. Three cited carriers were inaccessible during
fresh readback: two returned HTTP 403 and PubMed returned a cookie interstitial under HTTP 203. No
URL was malformed or found to identify a different work.

The seven author-candidate warrants are narrower than many raw answer sentences. They preserve
benchmark, time, population, metric, comparison, edition, retrieval, and judge boundaries. They
are not independently confirmed, and no raw run or profile supplies independence. Four additional
normalized warrant groups remain pending because their captured spans do not close the full
canonical proposition.

## Material corrections and negative results

Fresh authoritative readback found four important interpretation boundaries:

- link resolution, topical relevance, cited-claim support, and citation coverage are different
  measurements and are not pooled;
- DeepResearch Bench arXiv v1 and ICLR 2026 have materially different FACT values;
- DeepTRACE's own table and prose disagree on the Gemini Deep Research value, 50.3% versus 40.3%;
  and
- *Cited but Not Verified* reuses DeepResearch Bench and BrowseComp query roots, while the
  URL-health study reuses DeepResearch Bench outputs; and
- a resolved claim-to-citation edge is no longer asserted when the target citation remains
  unresolved.

The packet also corrects a LiveResearchBench license statement to CC BY-NC-SA 4.0 and records that
Mendeley landing pages were accessible while the credential-free file API was not. These
corrections live in review records; raw answers remain byte-identical.

The machine ledger and reproduction command are documented in
[`research/how-we-know/agent-citation-lineage/README.md`](../../research/how-we-know/agent-citation-lineage/README.md).

## Public boundary

The packet may retain the frozen prompt, final answers, citations, and declared public retrieval
receipts. It excludes hidden reasoning, private context, credentials, logged-in state, personal
data, and provider-restricted instructions. Restricted sources receive quote-minimal treatment.

## Authority boundary

This protocol authorizes research collection and review preparation only under EM-0026. It does
not admit a dossier, alter a public lens, feature Case 002, deploy a site, or establish a universal
result about agents. A fresh-clone independently rooted reviewer must reproduce the exact-head
trace identities, source readbacks, span matches, dependence relations, corrections, and counts
before the research packet may pass its final gate.
The full protocol lives in
[`research/how-we-know/agent-citation-lineage/`](../../research/how-we-know/agent-citation-lineage/README.md).
