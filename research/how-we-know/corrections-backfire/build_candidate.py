"""Build and verify the EM-0019 draft dossier.

The source packets below contain only the exact excerpts needed for review. Full
provider artifacts remain outside the repository; their retrieval digests and
license limits are recorded in each packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from epistemedia.core import canonical_json
from epistemedia.dossier import (
    DOSSIER_FORMAT,
    independence_summary,
    stamp_dossier,
    validate_dossier,
)

HERE = Path(__file__).resolve().parent
CANDIDATE_PATH = HERE / "candidate-dossier.json"
RETRIEVED_AT = "2026-08-22T06:13:51Z"


def prose(*sentences: str) -> str:
    return " ".join(sentence.strip() for sentence in sentences)


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def content_bytes(value: Any) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return canonical_json(value).encode("utf-8")


def edition(
    key: str,
    work_key: str,
    label: str,
    media_type: str,
    content: dict[str, Any],
) -> dict[str, Any]:
    encoded = content_bytes(content)
    return {
        "key": key,
        "work_key": work_key,
        "edition_label": label,
        "media_type": media_type,
        "retrieved_at": RETRIEVED_AT,
        "content": content,
        "content_digest": digest_bytes(encoded),
        "content_length": len(encoded),
        "visibility": "public",
    }


def excerpt(locator: str, text: str) -> dict[str, str]:
    return {"locator": locator, "text": text}


def span(
    key: str,
    edition_key: str,
    excerpt_index: int,
    label: str,
    exact_text: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "edition_key": edition_key,
        "locator": {
            "type": "json-pointer",
            "pointer": f"/excerpts/{excerpt_index}/text",
            "label": label,
        },
        "extent": {"type": "json-value", "value": exact_text},
        "digest": digest_bytes(exact_text.encode("utf-8")),
        "visibility": "public",
    }


SKURNIK_SUMMARY = prose(
    "Telling people that a consumer claim is false can make them misremember it as true.",
    "In two experiments, older adults were especially susceptible to this “illusion of "
    "truth” effect.",
)

HANDBOOK_CLAIM = "Hence the backfire effect is real."
HANDBOOK_ADVICE = "Ideally, avoid mentioning the myth altogether while correcting it."
HANDBOOK_REFERENCE = (
    "Skurnik, I., Yoon, C., Park, D., & Schwarz, N. (2005). How warnings about "
    "false claims become recommendations. Journal of Consumer Research, 31, 713-724."
)
HANDBOOK_UPDATE = (
    "For the most current information about this elusive effect please read the relevant "
    "excerpt from the new version of the handbook here."
)

SCHWARZ_CLAIM = prose(
    "Erroneous beliefs are difficult to correct.",
    "Worse, popular correction strategies, such as the myth-versus-fact article format, "
    "may backfire because they subtly reinforce the myths through repetition and further "
    "increase the spread and acceptance of misinformation.",
)
SCHWARZ_REFERENCE = (
    "Skurnik I., Yoon C., Park D. C., & Schwarz N. (2005). How warnings about false "
    "claims become recommendations Journal of Consumer Research, 31, 713–724"
)

ECKER_2020_RESULT = prose(
    "Experiment 1 found some evidence for a familiarity backfire effect, but the evidence "
    "was statistically weak and the result failed to occur in an exact replication with "
    "greater experimental power (Experiment 2) as well as a close replication that added "
    "only a trivial secondary task (the no-load condition of Experiment 3).",
    "In fact, both Experiments 2 and 3 yielded substantial evidence against the presence "
    "of a familiarity backfire effect, even under conditions that should maximize reliance "
    "on familiarity and thus facilitate occurrence of familiarity backfire, viz. the "
    "combination of novel claims that maximized the familiarity boost conveyed by first "
    "exposure, a relatively long 1-week retention interval, and correction encoding under "
    "cognitive load (the load condition of Experiment 3).",
)
ECKER_2020_GUIDANCE_OVERREACH = (
    "The practical implications of this research are clear: recommendations to front-line "
    "educators and communicators to entirely avoid repeating misinformation when debunking "
    "(Cook & Lewandowsky, 2011; Lewandowsky et al., 2012; Peter & Koch, 2016; Schwarz et "
    "al., 2007, 2016) were unwarranted."
)
ECKER_2020_GUIDANCE_CONCLUSION = (
    "Finally, the present study suggests that exposure to a correction does not cause "
    "familiarity backfire relative to a no-exposure control even with novel claims, and "
    "thus corrections do not seem to spread misinformation to new audiences easily."
)

PRIKE_2023_RESULT = prose(
    "Across three experiments (total N = 1156) we found that standalone corrections did "
    "not backfire immediately (Experiment 1) or after a one-week delay (Experiment 2).",
    "However, there was some mixed evidence suggesting corrections may backfire when there "
    "is skepticism regarding the correction (Experiment 3).",
    "Specifically, in Experiment 3, we found the standalone correction to backfire in "
    "open-ended responses, but only when there was skepticism towards the correction.",
    "However, this did not replicate with the rating scales measure.",
)

ECKER_2023_RESULT = prose(
    "We found that the myths vs. facts condition reduced vaccine misconceptions.",
    "None of the conditions increased vaccine misconceptions relative to control at either "
    "timepoint, or relative to a pre-intervention baseline; thus, no backfire effects were "
    "observed.",
    "This failure to replicate adds to the mounting evidence against familiarity backfire "
    "effects and has implications for vaccination communications and the design of "
    "debunking interventions.",
)


def source_works() -> list[dict[str, Any]]:
    return [
        {
            "key": "work-skurnik-2005",
            "kind": "paper",
            "title": "How Warnings about False Claims Become Recommendations",
            "creators": ["Ian Skurnik", "Carolyn Yoon", "Denise C. Park", "Norbert Schwarz"],
            "canonical_uri": "https://doi.org/10.1086/426605",
            "license": (
                "All rights reserved in the examined journal PDF; only two short attributed "
                "abstract sentences are retained and the PDF is not redistributed."
            ),
            "visibility": "public",
        },
        {
            "key": "work-handbook-2011",
            "kind": "webpage",
            "title": "The Debunking Handbook Part 2: The Familiarity Backfire Effect",
            "creators": ["John Cook", "Stephan Lewandowsky"],
            "canonical_uri": (
                "https://skepticalscience.com/"
                "Debunking-Handbook-Part-2-Familiarity-Backfire-Effect.html"
            ),
            "license": (
                "Copyright notice present and no page-wide reuse license confirmed; only "
                "short attributed excerpts and one bibliographic reference are retained."
            ),
            "visibility": "public",
        },
        {
            "key": "work-schwarz-2016",
            "kind": "paper",
            "title": "Making the Truth Stick & the Myths Fade: Lessons from Cognitive Psychology",
            "creators": ["Norbert Schwarz", "Eryn Newman", "William Leach"],
            "canonical_uri": "https://doi.org/10.1177/237946151600200110",
            "license": (
                "Publisher states that site manuscript content uses Creative Commons "
                "licenses but does not identify the variant on the article page; only an "
                "exact publisher-rendered abstract excerpt and reference are retained."
            ),
            "visibility": "public",
        },
        {
            "key": "work-ecker-2020",
            "kind": "paper",
            "title": (
                "Can corrections spread misinformation to new audiences? Testing for the "
                "elusive familiarity backfire effect"
            ),
            "creators": ["Ullrich K. H. Ecker", "Stephan Lewandowsky", "Matthew Chadwick"],
            "canonical_uri": "https://doi.org/10.1186/s41235-020-00241-6",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0).",
            "visibility": "public",
        },
        {
            "key": "work-prike-2023",
            "kind": "paper",
            "title": "Examining the replicability of backfire effects after standalone corrections",
            "creators": [
                "Toby Prike",
                "Phoebe Blackley",
                "Briony Swire-Thompson",
                "Ullrich K. H. Ecker",
            ],
            "canonical_uri": "https://doi.org/10.1186/s41235-023-00492-z",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0).",
            "visibility": "public",
        },
        {
            "key": "work-ecker-2023",
            "kind": "paper",
            "title": (
                "Correcting vaccine misinformation: A failure to replicate familiarity or "
                "fear-driven backfire effects"
            ),
            "creators": ["Ullrich K. H. Ecker", "Caitlin X. M. Sharkey", "Briony Swire-Thompson"],
            "canonical_uri": "https://doi.org/10.1371/journal.pone.0281140",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0).",
            "visibility": "public",
        },
    ]


def editions() -> list[dict[str, Any]]:
    return [
        edition(
            "edition-skurnik-2005",
            "work-skurnik-2005",
            "Journal PDF, volume 31, issue 4, pages 713–724; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://bear.warrington.ufl.edu/brenner/mar7588/Papers/skurnik-jcr2005.pdf"
                    ),
                    "sha256": "c4893504537d256cff0c37a58b17aca0d6ceda11d9c5cea1aa3c066a544108f2",
                    "bytes": 331989,
                    "custody": "Temporary research download; full PDF not committed.",
                },
                "excerpts": [
                    excerpt("PDF page 1; journal page 713; abstract sentences 1–2", SKURNIK_SUMMARY)
                ],
            },
        ),
        edition(
            "edition-handbook-2011",
            "work-handbook-2011",
            "Live HTML page including 2017 and 2020 update notices; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://skepticalscience.com/"
                        "Debunking-Handbook-Part-2-Familiarity-Backfire-Effect.html"
                    ),
                    "sha256": "bfd2e4ff7e2a5cc5a0c8f2e7aee70680cdc5eabbcf2333c4ef2a7ac3e3cfc3c4",
                    "bytes": 89663,
                    "custody": "Temporary HTML capture; full page not committed.",
                },
                "excerpts": [
                    excerpt("2011 body; paragraph beginning 'Hence'", HANDBOOK_CLAIM),
                    excerpt("2011 body; paragraph beginning 'How does one avoid'", HANDBOOK_ADVICE),
                    excerpt("References; item 1", HANDBOOK_REFERENCE),
                    excerpt("2020 update notice", HANDBOOK_UPDATE),
                ],
            },
        ),
        edition(
            "edition-schwarz-2016",
            "work-schwarz-2016",
            "Publisher HTML abstract and reference-list transcript; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://journals.sagepub.com/doi/10.1177/237946151600200110"
                    ),
                    "sha256": None,
                    "bytes": None,
                    "custody": (
                        "Authoritative publisher text independently visible through web "
                        "read-back; automated byte capture returned HTTP 403."
                    ),
                },
                "excerpts": [
                    excerpt("Publisher HTML abstract; opening sentences", SCHWARZ_CLAIM),
                    excerpt("Publisher HTML references; item 42", SCHWARZ_REFERENCE),
                ],
            },
        ),
        edition(
            "edition-ecker-2020",
            "work-ecker-2020",
            "Europe PMC JATS XML, PMCID PMC7447737; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7447737/fullTextXML"
                    ),
                    "sha256": "15620a5e73fe87bb19f3f37c84a4d1a0f7efa9b50be3a5d2749a07f588eb4047",
                    "bytes": 208195,
                    "custody": "Temporary CC BY 4.0 XML download; exact excerpts committed.",
                },
                "excerpts": [
                    excerpt("General discussion; opening result sentences", ECKER_2020_RESULT),
                    excerpt(
                        "General discussion; practical implications opening",
                        ECKER_2020_GUIDANCE_OVERREACH,
                    ),
                    excerpt(
                        "General discussion; practical implications conclusion",
                        ECKER_2020_GUIDANCE_CONCLUSION,
                    ),
                ],
            },
        ),
        edition(
            "edition-prike-2023",
            "work-prike-2023",
            "Europe PMC JATS XML, PMCID PMC10317933; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10317933/fullTextXML"
                    ),
                    "sha256": "a546f640397adf7ac208f040634e480181588e5c29e1a2c76f5a301ef728e019",
                    "bytes": 172943,
                    "custody": "Temporary CC BY 4.0 XML download; exact excerpts committed.",
                },
                "excerpts": [
                    excerpt("Abstract; results and qualification sentences", PRIKE_2023_RESULT)
                ],
            },
        ),
        edition(
            "edition-ecker-2023",
            "work-ecker-2023",
            "Europe PMC JATS XML, PMCID PMC10096191.1; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10096191/fullTextXML"
                    ),
                    "sha256": "44ebae212686059b211ae7a9e8757958d8851d73b51513c6f9a2f9c9a518f88e",
                    "bytes": 167791,
                    "custody": "Temporary CC BY 4.0 XML download; exact excerpts committed.",
                },
                "excerpts": [excerpt("Abstract; outcome sentences", ECKER_2023_RESULT)],
            },
        ),
    ]


def build_candidate() -> dict[str, Any]:
    spans = [
        span(
            "span-skurnik-summary",
            "edition-skurnik-2005",
            0,
            "PDF p. 1 / journal p. 713, abstract sentences 1–2",
            SKURNIK_SUMMARY,
        ),
        span(
            "span-handbook-claim",
            "edition-handbook-2011",
            0,
            "2011 body claim",
            HANDBOOK_CLAIM,
        ),
        span(
            "span-handbook-advice",
            "edition-handbook-2011",
            1,
            "2011 body advice",
            HANDBOOK_ADVICE,
        ),
        span(
            "span-handbook-reference",
            "edition-handbook-2011",
            2,
            "Reference 1",
            HANDBOOK_REFERENCE,
        ),
        span(
            "span-handbook-update",
            "edition-handbook-2011",
            3,
            "2020 update notice",
            HANDBOOK_UPDATE,
        ),
        span(
            "span-schwarz-claim",
            "edition-schwarz-2016",
            0,
            "Publisher HTML abstract opening",
            SCHWARZ_CLAIM,
        ),
        span(
            "span-schwarz-reference",
            "edition-schwarz-2016",
            1,
            "Publisher HTML reference 42",
            SCHWARZ_REFERENCE,
        ),
        span(
            "span-ecker-2020-result",
            "edition-ecker-2020",
            0,
            "General discussion result",
            ECKER_2020_RESULT,
        ),
        span(
            "span-ecker-2020-guidance-overreach",
            "edition-ecker-2020",
            1,
            "General discussion practical implications opening",
            ECKER_2020_GUIDANCE_OVERREACH,
        ),
        span(
            "span-ecker-2020-guidance-conclusion",
            "edition-ecker-2020",
            2,
            "General discussion practical implications conclusion",
            ECKER_2020_GUIDANCE_CONCLUSION,
        ),
        span(
            "span-prike-2023-result",
            "edition-prike-2023",
            0,
            "Abstract results and qualification",
            PRIKE_2023_RESULT,
        ),
        span(
            "span-ecker-2023-result",
            "edition-ecker-2023",
            0,
            "Abstract outcome",
            ECKER_2023_RESULT,
        ),
    ]

    propositions = [
        {
            "key": "prop-general-backfire",
            "text": (
                "Repeating misinformation inside an evidence-based correction generally "
                "makes recipients believe or rely on the misinformation more than a "
                "no-correction or pre-correction baseline."
            ),
            "scope": (
                "Group-level familiarity backfire from corrective repetition; excludes "
                "continued influence, worldview backfire, and one-person anecdotes."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-older-adult-result",
            "text": (
                "Skurnik et al. reported delayed misremembering of warned-against consumer "
                "claims among older adults in two experiments."
            ),
            "scope": "Older adults, consumer claims, and the tested delays in the 2005 paper.",
            "visibility": "public",
        },
        {
            "key": "prop-guidance-overreach",
            "text": (
                "Some communicator guidance advised avoiding repetition more generally than "
                "the later experimental record warranted."
            ),
            "scope": "The recommendation sources named by Ecker et al. 2020.",
            "visibility": "public",
        },
        {
            "key": "prop-skepticism-boundary",
            "text": (
                "Skepticism toward a correction may be a boundary condition under which a "
                "standalone correction can backfire on some measures."
            ),
            "scope": (
                "Prike et al. 2023 Experiment 3; open-ended response result did not repeat "
                "on the rating-scale measure."
            ),
            "visibility": "public",
        },
    ]

    lineages = [
        {
            "key": "lineage-skurnik-data",
            "status": "known",
            "dimensions": ["data", "method", "apparatus"],
            "depends_on": [],
            "basis_span_keys": ["span-skurnik-summary"],
            "assertion_keys": ["assert-skurnik-result"],
            "note": (
                "Original participant-data root. Its older-adult and consumer-claim scope "
                "must not silently become a general population result."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-handbook-guidance",
            "status": "known",
            "dimensions": ["source", "social"],
            "depends_on": ["lineage-skurnik-data"],
            "basis_span_keys": ["span-handbook-reference"],
            "assertion_keys": ["assert-handbook-claim"],
            "note": (
                "The page makes the broad claim and recommendation, and its sole numbered "
                "reference is Skurnik et al. 2005. It therefore adds a mention, not a new "
                "participant-data root."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-schwarz-review",
            "status": "unknown",
            "dimensions": ["source", "method"],
            "depends_on": [],
            "basis_span_keys": ["span-schwarz-claim", "span-schwarz-reference"],
            "assertion_keys": ["assert-schwarz-claim"],
            "note": (
                "Unknown sentence-level upstream lineage: the publisher abstract makes the "
                "claim and the bibliography includes Skurnik et al. 2005, but the accessible "
                "HTML does not expose which references support that exact abstract sentence."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2020-data",
            "status": "known",
            "dimensions": ["data", "method", "apparatus"],
            "depends_on": [],
            "basis_span_keys": [
                "span-ecker-2020-result",
                "span-ecker-2020-guidance-overreach",
                "span-ecker-2020-guidance-conclusion",
            ],
            "assertion_keys": ["assert-ecker-2020-result", "assert-ecker-2020-guidance"],
            "note": (
                "New participant-data root for the dossier count. Shared authors and method "
                "traditions are visible, so this is not a claim of full team or method "
                "independence."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-prike-2023-data",
            "status": "known",
            "dimensions": ["data", "method", "apparatus"],
            "depends_on": [],
            "basis_span_keys": ["span-prike-2023-result"],
            "assertion_keys": ["assert-prike-2023-result", "assert-prike-2023-skepticism"],
            "note": (
                "New participant-data root. It shares Ecker and the broader experimental "
                "tradition with other records; only the participant-data root is counted "
                "separately."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2023-data",
            "status": "known",
            "dimensions": ["data", "method", "apparatus"],
            "depends_on": [],
            "basis_span_keys": ["span-ecker-2023-result"],
            "assertion_keys": ["assert-ecker-2023-result"],
            "note": (
                "New vaccine-study participant-data root. It shares Ecker and "
                "Swire-Thompson with another later record, so research-team independence is "
                "not claimed."
            ),
            "visibility": "public",
        },
    ]

    assertions = [
        {
            "key": "assert-skurnik-result",
            "proposition_key": "prop-older-adult-result",
            "actor": {"id": "doi:10.1086/426605#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-skurnik-summary"],
            "lineage_key": "lineage-skurnik-data",
            "asserted_at": "2005-03-01T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-handbook-claim",
            "proposition_key": "prop-general-backfire",
            "actor": {"id": "web:debunking-handbook-2011#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-handbook-claim", "span-handbook-advice"],
            "lineage_key": "lineage-handbook-guidance",
            "asserted_at": "2011-11-18T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-schwarz-claim",
            "proposition_key": "prop-general-backfire",
            "actor": {"id": "doi:10.1177/237946151600200110#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-schwarz-claim"],
            "lineage_key": "lineage-schwarz-review",
            "asserted_at": "2016-04-01T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-ecker-2020-result",
            "proposition_key": "prop-general-backfire",
            "actor": {"id": "doi:10.1186/s41235-020-00241-6#authors", "kind": "collective"},
            "stance": "questions",
            "span_keys": [
                "span-ecker-2020-result",
                "span-ecker-2020-guidance-conclusion",
            ],
            "lineage_key": "lineage-ecker-2020-data",
            "asserted_at": "2020-08-26T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-ecker-2020-guidance",
            "proposition_key": "prop-guidance-overreach",
            "actor": {"id": "doi:10.1186/s41235-020-00241-6#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-ecker-2020-guidance-overreach"],
            "lineage_key": "lineage-ecker-2020-data",
            "asserted_at": "2020-08-26T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-prike-2023-result",
            "proposition_key": "prop-general-backfire",
            "actor": {"id": "doi:10.1186/s41235-023-00492-z#authors", "kind": "collective"},
            "stance": "questions",
            "span_keys": ["span-prike-2023-result"],
            "lineage_key": "lineage-prike-2023-data",
            "asserted_at": "2023-07-03T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-prike-2023-skepticism",
            "proposition_key": "prop-skepticism-boundary",
            "actor": {"id": "doi:10.1186/s41235-023-00492-z#authors", "kind": "collective"},
            "stance": "hypothesizes",
            "span_keys": ["span-prike-2023-result"],
            "lineage_key": "lineage-prike-2023-data",
            "asserted_at": "2023-07-03T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-ecker-2023-result",
            "proposition_key": "prop-general-backfire",
            "actor": {"id": "doi:10.1371/journal.pone.0281140#authors", "kind": "collective"},
            "stance": "questions",
            "span_keys": ["span-ecker-2023-result"],
            "lineage_key": "lineage-ecker-2023-data",
            "asserted_at": "2023-04-12T00:00:00Z",
            "visibility": "public",
        },
    ]

    relations = [
        {
            "key": "relation-skurnik-qualifies-general",
            "relation_type": "qualification",
            "from_ref": "assert-skurnik-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-skurnik-summary"],
            "note": "Shows a possible effect in a narrower older-adult consumer-claim setting.",
            "visibility": "public",
        },
        {
            "key": "relation-handbook-supports-general",
            "relation_type": "support",
            "from_ref": "assert-handbook-claim",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-handbook-claim", "span-handbook-advice"],
            "note": "A broad public-facing claim and recommendation.",
            "visibility": "public",
        },
        {
            "key": "relation-schwarz-supports-general",
            "relation_type": "support",
            "from_ref": "assert-schwarz-claim",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-schwarz-claim"],
            "note": "A second broad review-level mention with unresolved sentence-level lineage.",
            "visibility": "public",
        },
        {
            "key": "relation-handbook-depends-skurnik",
            "relation_type": "dependence",
            "from_ref": "lineage-handbook-guidance",
            "to_ref": "lineage-skurnik-data",
            "basis_span_keys": ["span-handbook-reference"],
            "note": "The 2011 page has one numbered reference: Skurnik et al. 2005.",
            "visibility": "public",
        },
        {
            "key": "relation-update-qualifies-handbook",
            "relation_type": "qualification",
            "from_ref": "span-handbook-update",
            "to_ref": "assert-handbook-claim",
            "basis_span_keys": ["span-handbook-update"],
            "note": "The live page now directs readers to newer treatment of the effect.",
            "visibility": "public",
        },
        {
            "key": "relation-ecker-2020-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-ecker-2020-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": [
                "span-ecker-2020-result",
                "span-ecker-2020-guidance-conclusion",
            ],
            "note": (
                "Later experiments did not reproduce a general effect in their tested conditions."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-undercuts-guidance",
            "relation_type": "undercutting",
            "from_ref": "assert-ecker-2020-guidance",
            "to_ref": "assert-handbook-claim",
            "basis_span_keys": ["span-ecker-2020-guidance-overreach"],
            "note": (
                "Challenges the inference from familiarity concern to blanket repetition advice."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-undercuts-review",
            "relation_type": "undercutting",
            "from_ref": "assert-ecker-2020-guidance",
            "to_ref": "assert-schwarz-claim",
            "basis_span_keys": ["span-ecker-2020-guidance-overreach"],
            "note": "Challenges broad review-level wording using later experimental evidence.",
            "visibility": "public",
        },
        {
            "key": "relation-prike-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-prike-2023-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-prike-2023-result"],
            "note": (
                "No immediate or delayed effect in two experiments; third result was "
                "measure-specific."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-prike-qualifies-boundary",
            "relation_type": "qualification",
            "from_ref": "assert-prike-2023-skepticism",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-prike-2023-result"],
            "note": (
                "Preserves the induced-skepticism open-response result as an unresolved boundary."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-2023-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-ecker-2023-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-ecker-2023-result"],
            "note": "A separate vaccine-context study did not observe the predicted effect.",
            "visibility": "public",
        },
    ]

    material = {
        "format": DOSSIER_FORMAT,
        "title": "Does repeating misinformation in a correction make it more believable?",
        "question": (
            "When a correction repeats a false claim, does familiarity generally cause "
            "belief or reliance to rise above an uncorrected or pre-correction baseline?"
        ),
        "scope": (
            "A lineage audit of the familiarity backfire claim. Independent counts refer "
            "to participant-data roots, not complete independence of authors, methods, or "
            "research programs. Worldview backfire and continued influence are distinct."
        ),
        "stage": "draft",
        "visibility": "public",
        "source_works": source_works(),
        "editions": editions(),
        "spans": spans,
        "propositions": propositions,
        "lineages": lineages,
        "assertions": assertions,
        "evidence_relations": relations,
        "claim_families": [
            {
                "key": "family-familiarity-backfire",
                "title": "Familiarity backfire from corrective repetition",
                "question": (
                    "Does repeating misinformation within a correction generally make the "
                    "misinformation more believable?"
                ),
                "proposition_keys": [record["key"] for record in propositions],
                "assertion_keys": [record["key"] for record in assertions],
                "relation_keys": [record["key"] for record in relations],
                "visibility": "public",
            }
        ],
        "evaluations": [
            {
                "key": "evaluation-encyclopedia",
                "claim_family_key": "family-familiarity-backfire",
                "policy_id": "em:application-policy:encyclopedia-v0.1",
                "frontier": "research-candidate-em-0019",
                "label": (
                    "The tested correction formats usually did not produce familiarity "
                    "backfire; early narrower results and an unresolved skepticism boundary "
                    "remain visible."
                ),
                "reason_codes": [
                    "early-result-narrower-than-general-rule",
                    "later-data-roots-rebut-general-rule",
                    "skepticism-boundary-unresolved",
                    "continued-influence-is-distinct",
                ],
                "visibility": "public",
            },
            {
                "key": "evaluation-skeptical",
                "claim_family_key": "family-familiarity-backfire",
                "policy_id": "em:application-policy:skeptical-v0.1",
                "frontier": "research-candidate-em-0019",
                "label": (
                    "No universal rule is admitted: supportive scope was overgeneralized, "
                    "one review lineage is unresolved, and later studies share some authors "
                    "and methods despite using new participant data."
                ),
                "reason_codes": [
                    "unresolved-review-lineage",
                    "team-and-method-overlap",
                    "measure-specific-qualifier",
                    "population-and-context-limits",
                ],
                "visibility": "public",
            },
        ],
    }
    return stamp_dossier(material)


SUPPORT_ASSERTIONS = [
    "assert-skurnik-result",
    "assert-handbook-claim",
    "assert-schwarz-claim",
]
COUNTER_ASSERTIONS = [
    "assert-ecker-2020-result",
    "assert-prike-2023-result",
    "assert-ecker-2023-result",
]


def derived_counts(candidate: dict[str, Any]) -> dict[str, Any]:
    supportive = independence_summary(candidate, SUPPORT_ASSERTIONS)
    counter = independence_summary(candidate, COUNTER_ASSERTIONS)
    return {
        "raw_supporting_assertions": len(SUPPORT_ASSERTIONS),
        "confirmed_supporting_data_roots": supportive["independent_lineage_count"],
        "unresolved_support_lineages": supportive["unknown_lineage_count"],
        "supporting_root_keys": supportive["independent_lineage_roots"],
        "unresolved_support_keys": supportive["unknown_lineages"],
        "raw_counterevidence_assertions": len(COUNTER_ASSERTIONS),
        "counterevidence_data_roots": counter["independent_lineage_count"],
        "counterevidence_root_keys": counter["independent_lineage_roots"],
        "counting_scope": (
            "Participant-data roots only; author, method, and research-program overlap "
            "remain disclosed and are not counted as independent dimensions."
        ),
    }


def write_candidate(candidate: dict[str, Any]) -> None:
    CANDIDATE_PATH.write_text(
        json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def check_candidate(candidate: dict[str, Any]) -> None:
    validate_dossier(candidate)
    recorded = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    validate_dossier(recorded)
    if canonical_json(recorded) != canonical_json(candidate):
        raise SystemExit(f"generated candidate drift: run {Path(__file__).name} --write")
    print(
        json.dumps({"dossier_id": candidate["dossier_id"], **derived_counts(candidate)}, indent=2)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    candidate = build_candidate()
    if args.write:
        write_candidate(candidate)
        print(CANDIDATE_PATH)
    else:
        check_candidate(candidate)


if __name__ == "__main__":
    main()
