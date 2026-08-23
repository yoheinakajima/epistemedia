# EM-0027 preliminary scout packet — “Do fact-checks work at all?”

**Status:** preliminary lead/readiness research only. Not a dossier, evidence admission, effect-size synthesis, or verdict.

**Scope and cutoff:** credential-free public primary/authoritative material inspected on or before 2026-08-22. This repository packet preserves a byte-verified recovery scout artifact; it does not admit or publish evidence.

## 1. Work and edition identity

- **Task:** `EM-0027`, *Map primary-source readiness for the next How We Know library*. The immutable task contract calls for a fact-check packet covering the four-country experiment, a broad evidence review, the 2023 science-misinformation meta-analysis, a 2025 reply, durability and behavior boundaries, and overlap with Case 001. It expressly limits the work to preliminary mapping, not a conclusion.
- **Candidate label:** “Do fact-checks work at all?” This is a circulated question, not a tested proposition. It combines materially different outcomes and intervention classes.
- **Anchor experiment (verified):** Ethan Porter and Thomas J. Wood, “The global effectiveness of fact-checking: Evidence from simultaneous experiments in Argentina, Nigeria, South Africa, and the United Kingdom,” *Proceedings of the National Academy of Sciences* 118(37), e2104235118 (2021). Stable DOI/URL: <https://doi.org/10.1073/PNAS.2104235118>. PNAS records acceptance 2021-07-23 and publication 2021-09-10. Public full-text landing page was available without credentials when inspected; article license was **not verified** from the captured record.
- **Broad political-fact-checking review (verified identity):** Nathan Walter, Jonathan Cohen,
  R. Lance Holbert, and Yasmin Morag, “Fact-Checking: A Meta-Analysis of What Works and for
  Whom,” *Political Communication* 37, 350–375 (2020). DOI:
  <https://doi.org/10.1080/10584609.2019.1668894>. The captured publisher abstract reports
  (k=30), (N=20,963), and a positive overall influence on political beliefs, (d=0.29). Full
  text/license/access beyond the publisher abstract: **not verified**.
- **Science-misinformation meta-analysis — original edition (verified identity):** Man-pui Sally Chan and Dolores Albarracín, “A meta-analysis of correction effects in science-relevant misinformation,” *Nature Human Behaviour* 7, 1514–1525 (2023), DOI <https://doi.org/10.1038/s41562-023-01623-8>, online version of record 2023-06-15; issue September 2023. Public author-hosted PDF and a public PMC record were located; the publisher page presents subscription access. The original article says data and code are at OSF <https://osf.io/vkygw/>; the current contents/version of that OSF project were **not directly inspected** in this recovery.
- **Science meta-analysis — correction edition (verified identity):** Chan and Albarracín, “Author Correction: A meta-analysis of correction effects in science-relevant misinformation,” *Nature Human Behaviour* 9, 1992–1994 (2025), DOI <https://doi.org/10.1038/s41562-025-02294-3>, published/version of record 2025-08-08. The correction states that original counts of included studies/effect sizes were incorrect and that some effect-size estimates/codings were erroneous or imprecise. Therefore, original-edition counts and estimates must not be carried forward as the current meta-analytic result.
- **2025 Matters Arising (verified identity):** Lucy H. Butler, Joseph DeGutis, Li Qian Tay, Ullrich K. H. Ecker, and Briony Swire-Thompson, “Corrections are effective for science misinformation,” *Nature Human Behaviour* 9, 2458–2460 (2025), DOI <https://doi.org/10.1038/s41562-025-02245-y>, published 2025-10-06. It is a response to the 2023 Chan–Albarracín article, not an independent primary intervention trial. Publisher page showed subscription access; source page says its relevant code is at <https://osf.io/f72ay/> and directs readers to Chan–Albarracín OSF data at <https://osf.io/vkygw/>. License: **not verified**.
- **2025 reply (verified identity):** Man-pui Sally Chan and Dolores Albarracín, “Reply to:
  Corrections are effective for science misinformation,” *Nature Human Behaviour* 9,
  2461–2470 (2025), DOI <https://doi.org/10.1038/s41562-025-02265-8>, PMID
  [`41053228`](https://pubmed.ncbi.nlm.nih.gov/41053228/), PMCID
  [`PMC13188179`](https://pmc.ncbi.nlm.nih.gov/articles/PMC13188179/). The version of record was
  published 2025-10-06 with a December 2025 issue date and explicitly replies to Butler et al.
  It is an author response/reanalysis in the same meta-analysis dispute, not a new primary
  intervention trial. Public PMC author-manuscript access was identified; no separate
  article-specific reuse license was confirmed, so retain metadata and quote minimally.

## 2. What the anchor experiment actually tested

### Verified design and estimands

PNAS reports 28 simultaneous experiments evaluating 22 fact-checks in Argentina, Nigeria, South Africa, and the United Kingdom, fielded in September–October 2020 with fact-checking organizations. Participants were randomized to misinformation, misinformation followed by a fact-check, or control. The primary reported outcome was respondents’ belief in the false claim on a five-point scale.

- **Correction estimand:** factual-accuracy/belief contrast, fact-check condition versus misinformation condition.
- **Misinformation estimand:** misinformation condition versus control.
- **Durability:** in Argentina, South Africa, and the UK, recontact approximately two weeks later measured the belief outcome again without stimulus reminders/truth cues.
- **Reported result (source statement, not a packet conclusion):** “fact-checks reduced belief in misinformation by at least 0.59 points on a 5-point scale”; the source says most correction effects remained detectable after more than two weeks. It also reports the misinformation-only contrast as less than 0.07 points on that scale.
- **Not tested by this anchor as a general result:** observed real-world exposure/reach, platform diffusion, actual sharing, vote choice, vaccination, other behavior, long-run persistence beyond the approximately two-week retest, or every type of fact-check.

### Comparator and population boundary

The comparison is an assigned, survey-delivered exposure to a brief misinformation summary followed by a locally produced fact-check, versus assigned misinformation alone (and separately versus control). It is not an estimate of a naturally encountered platform intervention. The study countries and heterogeneous topic set broaden the setting compared with a one-country study, but no representativeness claim beyond the source’s described samples is made here; sampling-frame details and weighted-population estimands were not independently extracted.

## 3. Reproducibility and direct artifacts

- **Harvard Dataverse deposit (verified):** Porter & Wood, “Replication Data for: The Global Effectiveness of Fact-Checking: Evidence From Simultaneous Experiments in Argentina, Nigeria, South Africa, and the U.K.”, DOI <https://doi.org/10.7910/DVN/Y8WPFR>. Public API metadata identified released version 1.1, publication date 2021-08-20, license **CC0 1.0**. It lists three `.rds` data files and 14 R scripts, including `rep_fig_1.R` through `rep_fig_5.R` and supplemental scripts. Platform-provided checksums are MD5 (not SHA-1 despite a prior abbreviated field label).
- **Direct capture:** the public `readme.txt` (Dataverse file id 5003598) was retrieved: **849 bytes**, SHA-256 `aab93c66a97c316d3bc7e78d5ace97f438b1c21f69d222fad51d5109f50862d7`; platform MD5 `1e06a7c5c21c246af5fa11492630717d`. It says the R scripts reproduce separate manuscript figures/tables and that data are loaded from GitHub. This establishes an available replication route, not successful reproduction.
- **Not executed:** no R script or dependency/data download was run; no output matches, environment pin, GitHub revision, or full source-artifact hash was verified. The Dataverse README’s stale-looking DOI placeholder (`10.1073/pnas.XXXXXXXXXX`) is a documentation defect/lead, not a change to the verified PNAS DOI.
- **Chan–Albarracín meta-analysis:** data/code availability is asserted by the original article at OSF `vkygw`; Butler et al. point to their code at OSF `f72ay`. Direct OSF listing/download, file names, R/Rmd file(s), revisions, licenses, bytes, hashes, and runability are **unknown**. In particular, the current authoritative Rmd/analysis file and whether it incorporates the 2025 correction are **unknown**. Do not rely on an original Rmd or a pre-correction result until version-pinned and reconciled with the correction.

## 4. Dependence and lineage map

| Item | Data/method lineage | Independence note |
| --- | --- | --- |
| Porter–Wood PNAS | Same 28 experiments/22 checks; Harvard Dataverse code/data; fieldwork by Ipsos MORI and YouGov, per PNAS acknowledgment | One source program; figures, tables, data deposit, and article are not independent efficacy evidence. |
| Walter et al. review | Meta-analysis of political fact-checking studies | Requires report-level overlap audit before combining with the PNAS anchor or other reviews. Overlap is unknown here. |
| Chan–Albarracín original/correction | One science-relevant correction synthesis and its author correction | The 2025 correction supersedes erroneous original counts/estimates. It is not independent evidence from its included reports. |
| Butler et al. Matters Arising | Reanalysis/critique using Chan–Albarracín repository, per its data/code statements | Not independent data from the original meta-analysis; it is a methodological counteranalysis. |
| Chan–Albarracín reply | Author response and reanalysis within the same dispute | Not a new participant-data root or independent synthesis; it answers Butler and must remain linked to the original, correction, and Matters Arising editions. |
| Case 001 | Existing Epistemedia correction/backfire candidate | Confirmed author-program overlap: Butler coauthors Ullrich K. H. Ecker and Briony Swire-Thompson are represented throughout Case 001's correction/backfire program. Exact included-report and participant-data overlap remains unaudited; prevent double counting until item-level matching. |

## 5. Counterevidence, qualifications, and boundaries

These are leads/boundaries, not an attempt to settle the literature.

1. **Edition instability is active counterevidence to any simple meta-analytic claim.** The correction says original counts were wrong and notes coding/effect-size problems. Butler et al. state that the original null resulted from pooling two distinct effect types; the source page quotes their description of the original as 75 studies/245 effect sizes and an average (d=0.11), (P=0.142). Neither figure should be reported as the corrected edition’s final estimate without reading/pinning the correction and current code/data.
   Chan and Albarracín's reply defends combining different correction approaches and reports a
   correction-effect estimate, but that argument remains part of the same contested analytical
   lineage and is not independent confirmation.
2. **Outcome mismatch.** The PNAS anchor supports a randomized, assigned-exposure claim about
   false-belief accuracy, including a limited delay. It does not establish that fact-checks
   change sharing or behavior. Ethan Porter and Thomas J. Wood, “Factual corrections: Concerns
   and current evidence,” *Current Opinion in Psychology* 55, 101715 (2024), DOI
   <https://doi.org/10.1016/j.copsyc.2023.101715>, PMID
   [`37988954`](https://pubmed.ncbi.nlm.nih.gov/37988954/), was published online 2023-10-21.
   The credential-free publisher HTML was inspected; no open license was confirmed for that
   version, so it is link/quote-minimal. Its public preprint DOI
   <https://doi.org/10.31234/osf.io/svbru> reports CC BY 4.0, but edition equivalence has not
   been collated. The review distinguishes belief accuracy from the less-settled evidence on
   attitudes, behavior, durability, and real-world exposure; it is a boundary review, not an
   independent intervention root.
3. **Scope mismatch.** Walter et al. synthesize political fact-checking; Chan–Albarracín focus science-relevant misinformation/corrections. Their intervention definitions, populations, outcomes, and inclusion rules cannot be treated as interchangeable.
4. **Exposure/selection gap.** Survey assignment demonstrates efficacy conditional on exposure, not reach to audiences who would ordinarily select, avoid, trust, or encounter a correction. This is an interpretation of the anchor design, not a claim that no real-world effects exist.

## 6. Quote-minimal exact spans

- PNAS abstract: “fact-checks reduced belief in misinformation by at least 0.59 points on a 5-point scale.”
- Chan–Albarracín correction: “the reported numbers of included studies and effect sizes were incorrect.”
- Butler et al. page: “inappropriate pooling of two distinct effect types into a single estimate.”

Each quotation is under 25 words and is included solely to anchor source identity/claim boundary.

## 7. Bounded corpus and review-cost estimate

**Provisional minimum corpus:** 6 source records (PNAS article + supplement, Dataverse deposit,
Walter review, Chan original plus correction treated as one version lineage, Butler Matters
Arising, and the Chan–Albarracín reply), plus 2–4 purpose-matched behavior/sharing studies. This
is a *scout* corpus, not a complete literature review.

**Expected review units:** roughly 10–16 records/artifacts after de-duplication, including versioned article/correction/reply records, supplements, code/data deposits, and boundary studies. Estimate is uncertain because OSF/Rmd state and report-level overlap have not been inspected. No provider budget or paid access is required for the next closure pass if public endpoints remain available.

## 8. Disposition

**HOLD — not READY for a full Case research pass yet.**

The anchor experiment and an openly licensed replication deposit are strongly identifiable, and they support a narrow candidate proposition: assigned fact-check exposure can improve a tested false-belief-accuracy outcome in the four-country experiments, with a limited (~two-week) durability result in three countries. They do not support the title question as a universal claim.

### Exact closure gaps before a full Case can be scoped

1. Retrieve/version-pin `vkygw` and `f72ay`: file inventory, licenses, bytes/hashes, current analysis/Rmd, revision dates, and whether the corrected analysis is reproducible from specified inputs.
2. Reconcile the original 2023 counts/estimates with the 2025 correction and reply; record corrected values only from the correction/current reproducible materials, never by inference.
3. Build a deliberately separate behavior/sharing branch with direct intervention and outcome evidence; do not transfer belief-accuracy or two-week persistence effects to behavior/reach/diffusion.
4. Perform report/item-level overlap mapping across Walter, Chan–Albarracín, Butler,
   PNAS/Dataverse, and Case 001 before counting evidence or describing convergence. The known
   Ecker/Swire-Thompson author-program overlap is not itself proof of report or participant-data
   overlap.
5. Check sampling/recruitment, attrition, stimuli, and analytic scripts sufficiently to state the exact population, delay denominator, and reproducibility status.

**Prohibitions preserved:** no source admission, dossier construction, public copy, verdict, repository edit, PR, credential use, deployment, or spend.

## Source register (captured authoritative/public routes)

1. PNAS landing/full text: <https://doi.org/10.1073/PNAS.2104235118>.
2. Harvard Dataverse deposit: <https://doi.org/10.7910/DVN/Y8WPFR>.
3. Walter et al. publisher record: <https://doi.org/10.1080/10584609.2019.1668894>.
4. Chan–Albarracín original: <https://doi.org/10.1038/s41562-023-01623-8>.
5. Chan–Albarracín correction: <https://doi.org/10.1038/s41562-025-02294-3>.
6. Butler et al. Matters Arising: <https://doi.org/10.1038/s41562-025-02245-y>.
7. Chan–Albarracín reply: <https://doi.org/10.1038/s41562-025-02265-8>;
   public manuscript record: <https://pmc.ncbi.nlm.nih.gov/articles/PMC13188179/>.
8. Original article’s declared OSF project: <https://osf.io/vkygw/>; Butler page’s declared code project: <https://osf.io/f72ay/>.
9. Porter and Wood boundary review: <https://doi.org/10.1016/j.copsyc.2023.101715>;
   PubMed <https://pubmed.ncbi.nlm.nih.gov/37988954/>; public preprint
   <https://doi.org/10.31234/osf.io/svbru>.
