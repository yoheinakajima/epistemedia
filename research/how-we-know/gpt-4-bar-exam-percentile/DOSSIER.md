# Case 003 candidate dossier

This directory contains a deterministic, disclosure-safe research candidate derived only
from the accepted EM-0032 packet. It remains draft research state: it is not admitted,
featured, live, or published.

- Dossier ID:
  `em:dossier:sha256:babe89ba3bda594a8d9f2db86a5a2987f284437a069b940d19b6928856d936d1`
- Candidate file SHA-256:
  `32c4457b3823237b2f988a26d51b2f6222af8060e662993524aff1c1a5d79e5d`
- Accepted frontier:
  `em:research-packet:sha256:535d07e59563b12f66e590c31b0d53a21db1a8dfce1487129a54c5e86b9fd55b`
- Evidence cutoff: 2026-08-27
- Source-graph SHA-256:
  `2bb896ded74d63469ec4e3947d75adfd6ac9a9c5dee6fe0db7ef9251760da38e`
- Review state: independent EM-0034 dossier review pending

The generated [candidate dossier](candidate-dossier.json) contains 8 accepted research works,
19 accepted source editions, 35 exact reviewed parent spans, and one repository calculation
register with 10 exact derivation-and-input-cell spans. The full dossier has 9 works,
20 editions, 45 spans, 21 propositions, 7 lineages, 21 assertions, 33 evidence relations,
one claim family, and two policy evaluations.
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

The dossier reproduces all ten accepted calculations from the accepted packet. Each calculation
closes to a structured span containing its exact accepted equation, inputs, input-cell IDs and
resolved cell values, comparison population, uncertainty, dependencies, and result. The three
Illinois values are explicitly reviewer sensitivity analyses, not values stated in the
official charts. The Martínez results are model outputs whose assumptions and comparison
populations remain visible. Neither kind of calculation creates a new performance root.

Multi-source typed edges are expanded into one referentially closed relation per endpoint pair.
The New York and NCBE roots therefore remain structural inputs to both the comparison-class and
derivation relations rather than surviving only in explanatory prose.

## Policy-relative views

Both evaluations use the same source graph
`2bb896ded74d63469ec4e3947d75adfd6ac9a9c5dee6fe0db7ef9251760da38e`.
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
