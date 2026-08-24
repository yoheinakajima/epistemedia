# Case 002 research: agent citation lineage

Status: **v1 preflight retained as failed; v2 matrix and EM-0026 source review accepted; EM-0029 candidate dossier awaiting exact-head independent review; research only**

Tasks: EM-0026 (accepted source packet) and EM-0029 (reversible candidate dossier)

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
are fixed before the first admissible trace. That prevents the observed answers from silently
changing the question or collection method.

The first transport preflight failed because one of two started invocations received one extra
character. Both were interrupted before final-answer capture. The exact mismatch and zero-admission
disposition remain visible in
[`failed-preflight/20260823T031151Z-v1-transport.json`](failed-preflight/20260823T031151Z-v1-transport.json).
Those v1 slots cannot be replaced or completed. No answer or citation from that preflight is part
of the research corpus.

The active v2 inputs are:

- [`target-decision.json`](target-decision.json): the suitability and risk decision;
- [`frozen-prompt-v2.md`](frozen-prompt-v2.md): the exact public prompt used in every v2 run;
- [`protocol-v2.json`](protocol-v2.json): a new eight-slot matrix, bound to the failed v1 record;
  and
- [`trace-record-template-v2.json`](trace-record-template-v2.json): the v2 public trace envelope.

`python research/how-we-know/agent-citation-lineage/verify_protocol_v2.py` checks the v2 file
identities, the failed-preflight linkage, and the new matrix. The later `--require-traces` gate also
requires eight terminal v2 records and verifies every captured answer artifact by digest and byte
count. The older `verify_protocol.py` remains available only to reproduce the frozen v1 identity.

The protocol records unavailable generation, system, or retrieval settings as `unknown`. A fresh
context excludes inherited conversation turns; it does not prove that provider system context,
pretraining, retrieval infrastructure, or other hidden dependencies are absent.

## Captured matrix and accounting

All eight frozen v2 slots terminated with disclosure-safe answer and trace artifacts. The raw
artifacts have not been edited. The author-side source review derives, rather than types
editorially:

1. captured report count;
2. cited URL count and resolving URL roots;
3. source-work and examined-edition roots;
4. exact source-span roots;
5. warrant roots after claim-to-span review;
6. non-resolving, inaccessible, malformed, or unsupported citations; and
7. known and unresolved model, prompt, retrieval, URL, source, span, upstream-citation, and
   derivation dependencies.

The current deterministic ledger reports:

> 8 reports → 30 cited URL strings (27 usable public readbacks) → 11 source works → 14 examined
> editions → 72 independently matched exact-span roots → 7 author-candidate warrant roots →
> 0 independently confirmed warrant roots

Those compact numbers are not a clean success funnel. The raw corpus contains 48 citation
occurrences, 127 span occurrences, and 52 result claims. Thirty-four citation occurrences remain
unresolved because a carrier was inaccessible, a quote did not match the independently extracted
edition text, a supplemental file was not captured, or a review correction prevents credit. The
three inaccessible carriers are the Wiley version-of-record URL and the cited OpenReview PDF,
which returned HTTP 403, plus a PubMed URL that returned HTTP 203 with a cookie interstitial. PMC
and ICLR provide readable authoritative editions for the same works, but their availability does
not silently turn the original carrier readbacks into successes.

Twenty claim occurrences are unsupported or force-raised after review. Nine of those were
explicitly downgraded because their linked quote fragments establish only part of the asserted
method, comparison, metric, scope, or direction. Four normalized warrant groups remain pending
for the same semantic-closure reason and are excluded from the seven candidate-warrant roots.

The machine records are:

- [`source-normalization-v1.json`](source-normalization-v1.json): work, edition, license,
  dependence, claim-review, and correction decisions;
- [`source-readbacks-v1.json`](source-readbacks-v1.json): fresh URL-level status, media type,
  bytes, and digest without redistributed source bodies;
- [`span-readbacks-v1.json`](span-readbacks-v1.json): one match result for each raw span
  occurrence; and
- [`evidence-ledger-v1.json`](evidence-ledger-v1.json): the deterministic relation ledger and
  derived counts.

EM-0029 adds three research-only files without changing those accepted records:

- [`build_candidate.py`](build_candidate.py): the deterministic adapter from the accepted ledger
  and review receipt into the repository dossier format; and
- [`candidate-dossier.json`](candidate-dossier.json): a content-addressed, quote-minimal candidate
  that remains outside the public catalog until independent review and a later admission task; and
- [`review-supplement-spans-v1.json`](review-supplement-spans-v1.json), which binds three
  quote-minimal qualification passages omitted from the accepted 72-span set: the two sides of the
  DeepTRACE Gemini table/prose discrepancy and the URL-health paper's DRBench corpus description.
  They close dossier sentences without changing EM-0026 counts or adding warrant credit.

The candidate models all eight reports as dependent observations of one capture program. It keeps
the seven scoped warrant candidates connected to an unknown source/method/derivation boundary,
so neither report count nor candidate-warrant count is presented as an independent evidence count.
Four pending warrant groups, nine independently rejected claim occurrences, twenty unsupported or
force-raised occurrences, thirty-four unresolved citations, and three inaccessible carriers are
typed no-credit records rather than hidden cleanup.

Run:

```bash
python research/how-we-know/agent-citation-lineage/build_evidence_ledger.py verify
```

The eight reports are observations about the collection process. They are not eight independent
confirmations of their answers. The seven author-candidate warrants are proposition-level roots,
not seven independent papers: shared task data, Jina Reader retrieval, LLM-judge methods, paper
editions, official repositories, and supplementary artifacts remain connected in the dependence
graph.

## Corrections retained outside raw output

The review records, without changing any answer bytes:

- LiveResearchBench v5 is licensed CC BY-NC-SA 4.0, not CC BY 4.0 as one run stated;
- *Cited but Not Verified* used queries from both DeepResearch Bench and BrowseComp, not only
  DeepResearch Bench;
- DeepResearch Bench arXiv v1 and ICLR 2026 report materially different FACT values and cannot be
  pooled as one edition;
- DeepTRACE Table 1 gives Gemini Deep Research citation accuracy as 50.3%, while nearby prose says
  40.3%; the exact Gemini value is unresolved;
- separate papers are not automatically independent when they reuse benchmark outputs, task
  populations, extraction services, or LLM-judge methods; and
- Mendeley landing pages were retrieved, but its credential-free file API returned 401, so
  uncaptured supplement-file contents receive no span credit;
- nine claims receive no credit because their linked spans do not entail the complete raw
  proposition; and
- claim-to-citation edges inherit the citation's actual resolution state instead of asserting a
  resolved edge to an unresolved target.

## Disclosure and licensing

Only the frozen prompt, final answer, citations, declared public retrieval receipts, and
quote-minimal source spans are eligible for this public research packet. Hidden reasoning,
restricted provider context, credentials, personal data, and inherited private conversation are
out of scope. Full copyrighted works are not redistributed. Open-license text retains its exact
license and edition; other works receive metadata, retrieval identity where available, and only
the minimal attributed span needed for warrant review.

## Stop conditions

The accepted EM-0026 review reproduced the captured sources, spans, corrections, and count grammar.
The EM-0029 candidate still fails closed unless a newly rooted reviewer can bind its exact bytes,
re-resolve the named editions, reproduce its sentence-to-span and relation closure, inspect all 34
unresolved citation occurrences, and confirm that the two policy evaluations do not strengthen the
accepted packet. Independently confirmed warrant count remains mechanically fixed at zero.

No file in this directory is accepted knowledge or a public Case 002 dossier merely because the
protocol, traces, ledger, or candidate exists. Admission and publication require the separately
sequenced EM-0030 task after EM-0029 independent review.
