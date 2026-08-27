# GPT-4 bar-exam percentile research packet

Status: author packet complete; fresh-clone independent review pending. This is research input, not
an admitted How We Know dossier, public verdict, current-model benchmark, or deployment.

Task: `EM-0032`

Target question:

> How did a historical simulated UBE score reported for GPT-4 become a roughly 90th-percentile
> claim, and how does the rank change when the comparison population changes?

Evidence cutoff: `2026-08-27`

## Current author recommendation

**GO, pending independent review**, for a later dossier about comparison-class ambiguity and
missing launch provenance. The useful result is not “the real percentile was X.” It is:

- OpenAI's launch report displayed `298/400 (~90th)` for “test takers” without identifying the
  UBE chart, administration, denominator, or interpolation;
- the later study version of record reports approximately `297`, explains how a best-performing
  MBE choice could yield `298 or higher`, and treats `68th–90th` as a plausible
  administration-dependent range;
- official Illinois February and July charts put the same score region in materially different
  places;
- Martínez's assumption-bound re-analysis yields about `62nd` among modeled first-time takers
  and about `45th` under its encoded passers calculation, while its own abstract and discussion
  say about `48th`; and
- none of these comparisons ranks GPT-4 against practicing lawyers or establishes current model
  performance or general legal competence.

The original launch chart and interpolation remain **unresolved-no-credit**. A linear
interpolation is included only as a visible sensitivity calculation; it is never attributed to
OpenAI.

## Packet identities

- candidate packet:
  `em:research-packet:sha256:3302c2c7282699e52ab53d670a83ded21f2a43de7685604075a1eed8a2f63ae1`;
- artifact inventory:
  `em:artifact-inventory:sha256:715844dcdcc9464e0f2b86e7d47f18145865bffb9fc7d02351836b53488621b9`;
- 15 preliminary core source objects plus 4 derivation supplements;
- 32 quote-minimal source spans;
- 89 mechanical artifacts: 78 pinned Git blobs, 1 Figshare PDF, and 10 OSF files;
- 10 deterministic calculations; and
- 5 lineage groups.

All 89 artifacts receive zero automatic independent-evidence credit. OpenAI report editions,
Katz's preprint/VOR/repository/supplement, and the study outputs collapse to one historical model
performance root. Martínez's VOR and OSF deposit collapse to one re-analysis root.

## Files

- `source-records.json` — source, edition, capture, license, span, claim, lineage, negative-search,
  and limitation records;
- `artifact-inventory.json` — content-addressed 89-file metadata inventory;
- `candidate-packet.json` — deterministic content-addressed packet;
- `build_packet.py` — capture helper and offline deterministic builder;
- `verify_packet.py` — source/count/math/lineage verifier and fail-closed review gate; and
- `independent-review-receipt.json` — absent until a separate reviewer completes exact-head
  review.

Source bodies remain outside Git. CC BY works are still quoted minimally; unlicensed works and
artifacts are link/metadata/quote-minimal only.

## Reproduce

```bash
python research/how-we-know/gpt-4-bar-exam-percentile/build_packet.py --check
python research/how-we-know/gpt-4-bar-exam-percentile/verify_packet.py
python research/how-we-know/gpt-4-bar-exam-percentile/verify_packet.py \
  --require-review
make check
```

Before independent review, the third command must fail with `independent review receipt missing`.
After review, it must bind the exact author head, packet bytes, all source/span/artifact coverage,
recomputed calculations, lineage edges, limitations, and recommendation.

## Hard boundary

This packet does not authorize a Case 003 dossier, catalog admission, feature, Pages deployment,
provider call, proprietary rerun, credential use, spend, public launch, or claim about a current
OpenAI model. Those remain separate governed tasks.
