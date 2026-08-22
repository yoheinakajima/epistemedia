# Candidate dossier: corrections and familiarity backfire

Status: **draft research candidate; not accepted catalog knowledge**

Task: EM-0019

Candidate identity: `em:dossier:sha256:999dfd06596c965578f663b00380abac8cec5d8139b4735d2399c4b8207c6947`

## Human question

Does repeating misinformation inside an evidence-based correction generally make people believe or rely on that misinformation more than they otherwise would?

This is deliberately narrower than “can corrections ever fail?” It separates:

- **familiarity backfire**: belief or reliance rises above a no-correction or pre-correction baseline because the correction repeats the claim;
- **continued influence**: a correction helps but does not fully erase the misinformation’s effect; and
- **worldview backfire**: a different proposed mechanism involving identity or prior attitudes.

Collapsing those outcomes would manufacture a stronger claim than the reviewed experiments test.

## What the lineage audit currently shows

The candidate’s deterministic calculation reports:

| Reviewed item | Raw assertions | Confirmed participant-data roots | Unresolved lineages |
| --- | ---: | ---: | ---: |
| Apparent support for familiarity backfire | 3 | 1 | 1 |
| Later counterevidence | 3 | 3 | 0 |

The supportive side contains:

1. a 2005 two-experiment result explicitly scoped to older adults and consumer claims (`span-skurnik-summary`);
2. a 2011 public handbook page that says the effect is real and advises avoiding myth repetition, while naming the 2005 study as its sole numbered reference (`span-handbook-claim`, `span-handbook-advice`, `span-handbook-reference`); and
3. a 2016 review abstract making a broader repetition claim, whose exact sentence-level upstream basis remains unresolved (`span-schwarz-claim`, `span-schwarz-reference`).

The later side contains three new participant-data roots:

- Ecker, Lewandowsky, and Chadwick (2020) report that a weak first result did not repeat in two higher-powered follow-ups (`span-ecker-2020-result`) and challenge blanket advice against repetition (`span-ecker-2020-guidance-overreach`, `span-ecker-2020-guidance-conclusion`).
- Prike et al. (2023) report no immediate or one-week effect in two experiments and a measure-specific result under induced correction skepticism in a third (`span-prike-2023-result`).
- Ecker, Sharkey, and Swire-Thompson (2023) report no effect in their vaccine-misinformation study conditions (`span-ecker-2023-result`).

Those later roots are independent only at the participant-data level. Authors, theory, and methods overlap. The dossier records that limitation and does not turn “three data roots” into “three fully independent research programs.”

Interpretation, not admitted fact: the popular blanket rule outran the scope and independence of its visible support. The reviewed later studies make group-level familiarity backfire look uncommon in their tested settings, not impossible in every population, format, delay, or measure. The skepticism result remains an open boundary condition.

## Source editions, custody, and reuse

Only the exact review excerpts are committed. Full provider artifacts are not.

| Work | Examined edition | Artifact receipt | Public excerpt treatment |
| --- | --- | --- | --- |
| [Skurnik et al. 2005](https://doi.org/10.1086/426605) | University-hosted copy of the journal PDF, 12 pages | SHA-256 `c4893504537d256cff0c37a58b17aca0d6ceda11d9c5cea1aa3c066a544108f2`; 331,989 bytes | All rights reserved; two short abstract sentences only |
| [Cook and Lewandowsky 2011](https://skepticalscience.com/Debunking-Handbook-Part-2-Familiarity-Backfire-Effect.html) | Live HTML including later update notices | SHA-256 `bfd2e4ff7e2a5cc5a0c8f2e7aee70680cdc5eabbcf2333c4ef2a7ac3e3cfc3c4`; 89,663 bytes | Copyright notice present; short excerpts and reference only |
| [Schwarz, Newman, and Leach 2016](https://doi.org/10.1177/237946151600200110) | Publisher-rendered HTML abstract and references | Full byte snapshot unavailable: automated retrieval returned HTTP 403 | Publisher says manuscript content uses Creative Commons licenses but does not name the variant on-page; excerpt-only transcript pending independent check |
| [Ecker, Lewandowsky, and Chadwick 2020](https://doi.org/10.1186/s41235-020-00241-6) | Europe PMC JATS XML, PMCID PMC7447737 | SHA-256 `15620a5e73fe87bb19f3f37c84a4d1a0f7efa9b50be3a5d2749a07f588eb4047`; 208,195 bytes | CC BY 4.0; exact result and implications excerpts |
| [Prike et al. 2023](https://doi.org/10.1186/s41235-023-00492-z) | Europe PMC JATS XML, PMCID PMC10317933 | SHA-256 `a546f640397adf7ac208f040634e480181588e5c29e1a2c76f5a301ef728e019`; 172,943 bytes | CC BY 4.0; exact abstract excerpt |
| [Ecker, Sharkey, and Swire-Thompson 2023](https://doi.org/10.1371/journal.pone.0281140) | Europe PMC JATS XML, PMCID PMC10096191.1 | SHA-256 `44ebae212686059b211ae7a9e8757958d8851d73b51513c6f9a2f9c9a518f88e`; 167,791 bytes | CC BY 4.0; exact abstract excerpt |

The artifact hashes identify what the authoring agent actually examined. A provider may later serve different bytes at the same URL. A reviewer must record any new digest rather than silently replacing these receipts.

## Candidate and negative-result log

EM-0019 considered the initial product-direction candidates before selecting this one:

- **Selected and narrowed:** “Why repetition can change belief without adding evidence” became the mechanism-specific correction question above. It has accessible primary experiments, a visible lineage collapse, counterevidence, a live qualifier, and a practical human question.
- **Deferred:** “Information is not meaning.” Shannon, semantic-information, and truth distinctions are valuable, but the first slice would be mainly conceptual and would not expose an equally clear empirical lineage-count interaction.
- **Deferred:** “When justified true belief still is not knowledge.” A Gettier dossier remains promising, but counting argumentative lineages without first specifying an argument-dependence model would overstate what the alpha dossier can represent.
- **Deferred:** worldview backfire. It risks making politics the first realm, combines a different mechanism with familiarity, and would make the public question less clean.
- **Deferred:** “What can an AI responsibly claim to know?” It is fast-moving and too adjacent to the platform itself for the first outward-facing proof.
- **Excluded from evidential counts:** the 2012 Association for Psychological Science summary because its broad “sometimes backfire” wording does not distinguish familiarity, worldview, and continued-influence mechanisms.
- **Excluded from independent credit:** review and guidance statements that merely cite or summarize upstream experiments.
- **Excluded as a root:** an inaccessible/unpublished familiarity-backfire report discussed in later literature. A provenance dead end cannot receive automatic evidential credit.

These exclusions are negative results, not claims that the works are unimportant.

## Reproduce the candidate and counts

From the repository root:

```bash
.venv/bin/python research/how-we-know/corrections-backfire/build_candidate.py --check
```

Regenerate only when the reviewed material intentionally changes:

```bash
.venv/bin/python research/how-we-know/corrections-backfire/build_candidate.py --write
```

With the five captured artifacts present in `/tmp`, verify their bytes and every machine-checkable excerpt:

```bash
.venv/bin/python research/how-we-know/corrections-backfire/verify_retrievals.py \
  --artifact-dir /tmp
```

`--require-complete` intentionally fails today because the Schwarz publisher excerpt still needs independently rooted read-back.

## Independent-review gate

The authoring agent cannot satisfy “independently rooted reviewer” by checking its own extraction again. Before this candidate can move into `catalog/dossiers/how-we-know/` or change from `draft` to `reviewed`, another reviewer must:

1. retrieve the six works without relying on the authoring agent’s temporary files;
2. verify every committed excerpt against the identified edition and locator;
3. resolve or preserve the Schwarz lineage as unknown and identify the exact Creative Commons variant if possible;
4. confirm that the handbook-to-Skurnik dependence is warranted by the page’s reference structure;
5. assess whether any later participant samples or materials share an upstream data source that would reduce the three-root count;
6. confirm the quote-minimal treatment of restricted works and the CC BY attributions;
7. run the build, retrieval, and repository checks; and
8. append a reviewer identity, lineage, timestamp, exact commands, source digests, findings, and limitations as a new receipt.

Until then, this is a reviewable research proposal, not accepted knowledge and not homepage copy.
