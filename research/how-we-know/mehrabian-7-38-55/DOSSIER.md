# Case 004 candidate dossier

This directory contains a deterministic, disclosure-safe research candidate derived only
from the accepted EM-0033 packet. It is draft research state: it is not admitted,
featured, live, or published.

- Dossier ID:
  `em:dossier:sha256:57e80c9a44c478c1c81ba7adedc1bafdef43ff57b4f2984015dcbef84ba66e87`
- Candidate file SHA-256:
  `44e7bf407091d7665d4f1ab2aabc285255364e790e2d17520913f9ba9c57b418`
- Accepted frontier:
  `em:research-packet:sha256:a73dc29f0a0c3f05a112b7c392d115cfcc38a1136a683325bf74bebf0c6b2e40`
- Evidence cutoff: 2026-08-27
- Review state: independent EM-0035 dossier review pending

The generated [candidate dossier](candidate-dossier.json) contains 11 source works,
12 editions, 40 exact reviewed parent spans, 20 propositions, 23 lineages,
20 assertions, 35 evidence relations, one claim family, and two policy evaluations.
Those values are derived by [the builder](build_candidate.py) from the accepted
relations and close through `prop-reviewed-source-register`,
`assertion-reviewed-source-register`, and all 40 parent-span keys.

## Scientific and historical boundaries

| Object | Bounded statement | Exact closure |
| --- | --- | --- |
| P1 | Words-and-tone result in an inconsistent isolated-word attitude task | `claim-p1-tone-dominance`; `span-wiener-single-words`, `span-wiener-result-boundary`, `span-wiener-safe-extension`; `lineage-participant-p1` |
| P2 | Face-and-tone result using the neutral word “maybe” and facial photographs | `claim-p2-face-tone`; `span-ferris-maybe`, `span-ferris-design`, `span-ferris-sums-of-squares`, `span-ferris-regression`; `lineage-participant-p2` |
| Later integration | The .07/.38/.55 values are a P2 discussion proposal across P1 and P2, not one three-channel experiment | `claim-three-coefficient-proposal`; `span-ferris-target`, `span-ferris-design`, `span-ferris-proposal`; `lineage-cross-study-proposal` |
| Seven-percent origin | The exact derivation remains unresolved and receives no credit | `claim-seven-origin`; `span-ferris-regression`, `span-ferris-proposal`, `span-silent-1971-liking`; `lineage-seven-origin-unknown` |
| Author boundary | The 1971 book calls the values approximate and limits them to one feeling dimension; the later author page also limits application | `claim-book-boundary`, `relation-author-qualification`; `span-silent-1971-liking`, `span-silent-1971-boundary`, `span-author-qualification` |
| 1981 edition | Bibliographic identity is closed, while formula-page continuity is uncollated | `claim-1981-edition`; `span-silent-1981-metadata`; `lineage-silent-1981-unknown` |
| Direct rebuttal | Hegstrom reports message-specific all-channel equations unlike a fixed universal rule | `claim-hegstrom-rebuttal`, `relation-hegstrom-direct-rebuttal`; `span-hegstrom-design`, `span-hegstrom-result` |
| Related programs | Argyle results are context-dependent boundary evidence, not exact replication | `claim-related-context`, `relation-argyle-context-qualification`; the three `span-argyle-*` records; `lineage-argyle-related-program` |
| Propagation | The three recirculation objects document spread and receive zero scientific-rule evidence credit | `claim-propagation`; the four linked Lapakko, Hampshire, and Birmingham spans; `lineage-propagation-synthesis` |
| Follow-ups | The bounded search is not exhaustive and does not establish an exact replication or universal rule | `claim-replication-search`; its three linked spans; `lineage-follow-up-synthesis` |

Five participant-data roots remain distinct: P1, P2, Hegstrom, Argyle 1970, and
Argyle 1971. The 11 accepted dependence records retain participant, speaker,
author-social, grant, stimulus, material, method, scale, citation, book-edition,
and derivation types as exact evidence-linked `edge-*` relations.

## Mechanical calculations

| Derivation | Result | Reviewed input spans | Lineage |
| --- | ---: | --- | --- |
| `derive-proposed-sum` | 1.0 | `span-ferris-proposal` | `lineage-cross-study-proposal` |
| `derive-proposed-facial-vocal-ratio` | 1.4473684210526316 | `span-ferris-proposal` | `lineage-cross-study-proposal` |
| `derive-p2-facial-vocal-ratio` | 1.4563106796116505 | `span-ferris-regression` | `lineage-cross-study-proposal` |
| `derive-ratio-difference` | 0.008942258559018867 | regression and proposal spans | `lineage-cross-study-proposal` |
| `derive-implied-vocal-verbal-ratio` | 5.428571428571428 | `span-ferris-proposal` | `lineage-seven-origin-unknown` |
| `derive-p2-allocation-with-seven-reserved` | verbal .07, vocal 0.3786166007905138, facial 0.5513833992094861 | regression and proposal spans | `lineage-seven-origin-unknown` |

The final two rows are sensitivity or reverse-engineering calculations; they do
not recover the missing source derivation of .07.

## Policy-relative views

Both evaluations use the same source graph
`e02032b582b7c0706b7498169653e98c190d27a692a8ef7ac8250b68628a28f8`.
The encyclopedia view documents the narrow historical proposal with experiment
and edition boundaries. The skeptical view withholds the universal rule and any
claim that the .07 origin was recovered. Their exact proposition, assertion,
evaluation, label, and reason-code records are in the candidate JSON.

## Validation

```console
PYTHONPATH=src python3 research/how-we-know/mehrabian-7-38-55/build_candidate.py --check
PYTHONPATH=src python3 research/how-we-know/mehrabian-7-38-55/verify_candidate.py --self-test
PYTHONPATH=src python3 research/how-we-know/mehrabian-7-38-55/verify_candidate.py --require-review
```

The first two commands must pass for the author candidate. The third must fail
until an independently authored, exact-head receipt is appended.
