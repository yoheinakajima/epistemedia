# Case 003 candidate dossier

This directory contains a deterministic, disclosure-safe research candidate derived only
from the accepted EM-0032 packet. It remains draft research state: it is not admitted,
featured, live, or published.

- Dossier ID:
  `em:dossier:sha256:e3d91aa0bc840a20036a57d48971585efa41b3b8d36310d00c0ec37341793306`
- Candidate file SHA-256:
  `976194f1395b5e83f3daff4e6bfed038925e8759dd71153b36260fcd348c100e`
- Accepted frontier:
  `em:research-packet:sha256:535d07e59563b12f66e590c31b0d53a21db1a8dfce1487129a54c5e86b9fd55b`
- Evidence cutoff: 2026-08-27
- Source-graph SHA-256:
  `cca1fff36a03b829267a638bbbb07d91a6772171f6e863b253fd32cf82c577fe`
- Review state: independent EM-0034 dossier review pending

The generated [candidate dossier](candidate-dossier.json) contains 8 source works,
19 editions, 35 exact reviewed parent spans, 21 propositions, 7 lineages,
21 assertions, 31 evidence relations, one claim family, and two policy evaluations.
Those values are derived by [the builder](build_candidate.py) from the accepted packet.

## What the dossier preserves

| Question | Bounded answer | Exact closure |
| --- | --- | --- |
| What was reported? | OpenAI's launch-edition report displayed 298/400 and approximately 90th percentile for a simulated UBE. | `claim-launch-score-label`; its accepted report spans; `lineage-model-performance-root` |
| What population produced 90th? | The launch report does not identify the exact administration, jurisdiction, chart, population composition, or interpolation. | `claim-launch-comparison-unspecified`; `lineage-model-performance-root` |
| Were 297 and 298 separate tests? | No. They are scoring choices within one historical experiment. | `claim-score-discrepancy`; `edge-score-component-composite` |
| How sensitive is the rank? | Reviewer-disclosed interpolation places 298 near 89.0 in Illinois February 2018, 67.8 in July 2018, and 88.6 in February 2019. | the three `derive-illinois-*` propositions; `edge-benchmark-illinois-charts` |
| What does the re-analysis say? | Under modeled assumptions, the same score is about 62nd among first-time takers and roughly 45th among passers, while the article's abstract and discussion say roughly 48th. | the Martínez claims and derivations; `lineage-martinez-analysis-root` |
| Does this rank GPT-4 against lawyers? | No captured source compares the score with practicing lawyers or establishes general legal competence. | `claim-no-lawyer-rank`; the skeptical policy boundary |

## Lineage and independence

The report, paper, code, and score manifestations share one historical model-performance
root; documents do not become independent experiments merely by being cited separately.
The accepted register has five empirical lineage groups and seven independent roots in
total: one model-performance root, one re-analysis root, three Illinois administration
roots, one NCBE aggregate root, and one New York pass-rate root. Ten evidence-linked
typed dependence edges retain author-social, benchmark, citation, comparison-class,
data, derivation, material, method, model, and score dimensions.

## Mechanical calculations

The dossier reproduces all ten accepted calculations from the accepted packet. The three
Illinois values are explicitly reviewer sensitivity analyses, not values stated in the
official charts. The Martínez results are model outputs whose assumptions and comparison
populations remain visible. Neither kind of calculation creates a new performance root.

## Policy-relative views

Both evaluations use the same source graph
`cca1fff36a03b829267a638bbbb07d91a6772171f6e863b253fd32cf82c577fe`.
The encyclopedia view preserves the historical simulated score while stating that its
percentile depends on the comparison population. The skeptical view withholds a general
90th-percentile or lawyer-quality claim because the launch distribution is unresolved,
administration sensitivity is material, and the 45/48 article discrepancy remains.

## Validation

```console
PYTHONPATH=src python3 research/how-we-know/gpt-4-bar-exam-percentile/build_candidate.py --check
PYTHONPATH=src python3 research/how-we-know/gpt-4-bar-exam-percentile/verify_candidate.py --self-test
PYTHONPATH=src python3 research/how-we-know/gpt-4-bar-exam-percentile/verify_candidate.py --require-review
```

The first two commands must pass for the author candidate. The third must fail until an
independently authored, exact-head review receipt is appended.
