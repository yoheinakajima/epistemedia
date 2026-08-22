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
CORRECTION_RETRIEVED_AT = "2026-08-22T07:11:15Z"
REVIEW_REPAIR_RETRIEVED_AT = "2026-08-22T16:14:38Z"


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
    *,
    retrieved_at: str = RETRIEVED_AT,
) -> dict[str, Any]:
    encoded = content_bytes(content)
    return {
        "key": key,
        "work_key": work_key,
        "edition_label": label,
        "media_type": media_type,
        "retrieved_at": retrieved_at,
        "content": content,
        "content_digest": digest_bytes(encoded),
        "content_length": len(encoded),
        "visibility": "public",
    }


def excerpt(
    locator: str,
    text: str,
    *,
    verification: str = "artifact",
) -> dict[str, str]:
    return {"locator": locator, "text": text, "verification": verification}


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
HANDBOOK_EXPERIMENT = (
    "To test for this backfire effect, people were shown a flyer that debunked common "
    "myths about flu vaccines."
)
HANDBOOK_DELAY = (
    "However, when queried 30 minutes after reading the flyer, some people actually scored "
    "worse after reading the flyer."
)
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
    "Skurnik, I., Yoon, C., Park, D. C., & Schwarz, N. (2005). How warnings about false "
    "claims become recommendations. Journal of Consumer Research, 31, 713–724."
)
SCHWARZ_SKURNIK_2005_DELAY = (
    "But 3 days later, after their memories had a chance to fade, participants were more "
    "likely to think that any statement they had seen was true, whether it had been "
    "presented as true or false."
)
SCHWARZ_SKURNIK_2005_OLDER = (
    "Older participants were particularly vulnerable to this bias, presumably because "
    "their poorer memory made it harder to remember the details of what they had heard earlier."
)
SCHWARZ_FLU_2007_MEMORY = (
    "When undergraduates viewed a myths-and-facts flyer about the flu taken from the CDC "
    "website, they remembered some myths as facts after only 30 minutes."
)
SCHWARZ_FLU_2007_INTENTIONS = (
    "Worse, their reported intentions to get vaccinated were even lower than those of "
    "control participants who had not been exposed to any message about the flu."
)
SCHWARZ_REFERENCE_6 = (
    "Schwarz, N., Sanna, L. J., Skurnik, I., & Yoon, C. (2007). Metacognitive experiences "
    "and the intricacies of setting people straight: Implications for debiasing and public "
    "information campaigns. Advances in Experimental Social Psychology, 39, 127–161."
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
ECKER_2020_UNPUBLISHED_LINEAGE = (
    "the only clear demonstration of a familiarity backfire effect was reported in an "
    "unpublished manuscript by Skurnik, Yoon, and Schwarz (2007; discussed by Schwarz et "
    "al., 2007)"
)
ECKER_2020_NO_BASELINE = (
    "the study also did not feature a baseline condition against which to access actual “backfire.”"
)
ECKER_2020_RECRUITMENT = (
    "Participants were US-based adult Amazon Mechanical Turk (MTurk) workers, who had "
    "completed at least 5000 so-called human-intelligence tasks (HITs) with 97% + approval."
)
ECKER_2020_CLOUDRESEARCH = (
    "The experiment was administered using Qualtrics survey software (Qualtrics, Provo, UT) "
    "via the CloudResearch platform (formerly TurkPrime; Litman, Robinson, & Abberbock, 2017)."
)
ECKER_2020_ECKER_2011_SEARCH = (
    "unlike Skurnik et al. (2005), Ecker et al. (2011) found that multiple retractions were "
    "more effective than singular retractions at reducing continued influence."
)
ECKER_2020_ECKER_2017_SEARCH = (
    "Likewise, Ecker, Hogan, and Lewandowsky (2017) found that repeating a piece of "
    "misinformation when correcting it actually led to stronger reduction of the continued "
    "influence effect than a correction that avoided misinformation repetition."
)
ECKER_2020_SWIRE_2017_SEARCH = prose(
    "They, too, failed to observe any familiarity backfire effects: post-correction belief "
    "in misinformation was always lower than pre-correction belief.",
    "This reduction in false-claim belief was observed even under conditions where the impact "
    "of familiarity (relative to recollection) should be maximal, viz. in elderly participants "
    "and after a long retention interval of up to 3 weeks.",
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
PRIKE_2023_RECRUITMENT = prose(
    "To account for potential exclusions and ensure ample statistical power, 283 participants "
    "were recruited from the online testing platform Amazon Mechanical Turk (MTurk) via "
    "CloudResearch (Litman et al., 2017).",
    "Participants were eligible if they resided in the United States of America and had "
    "previously completed more than 5000 MTurk tasks (HITs) with a minimum approval rating "
    "of 97%.",
)
PRIKE_2023_ETHICS = (
    "All procedures were approved by the University of Western Australia’s Human Research "
    "Ethics Office (Ethics ID: RA/4/20/6423)."
)
PRIKE_2023_AUTRY_SAMPLE = (
    "Additionally, Autry and Duarte only sampled undergraduates whereas our participants "
    "were recruited from MTurk without any age restrictions."
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
ECKER_2023_RECRUITMENT = (
    "To additionally account for an expected drop-out rate of 15% between T1 and T2, a "
    "convenience sample of 440 UK-based participants was recruited using Prolific."
)
ECKER_2023_MATERIALS = (
    "Stimuli were taken directly from Pluviano et al. (2017) and are provided in the S1 File, "
    "available at https://osf.io/dwyma/."
)
ECKER_2023_ETHICS = (
    "The experiment was approved by the Human Research Ethics Office of the University of "
    "Western Australia (RA/4/20/6423)."
)

AUTRY_2021_RESULT = (
    "When subjects were exposed to the target concept, negated corrections reduced mentions "
    "of the misinformation relative to no correction; however, when not exposed to the "
    "concept, negated corrections increased mentions relative to no correction."
)
AUTRY_2021_QUALIFIER = (
    "When subjects were not exposed, negated corrections increased mentions of the target "
    "concept compared to no correction (although this effect was nonsignificant in Experiment 2)."
)
AUTRY_2021_TIMING_LIMIT = (
    "The effects of exposure on negated corrections occurred after a 5-min delay in "
    "Experiment 1 and no delay in Experiment 2; therefore, further research is necessary "
    "to determine whether the increased belief from negated corrections persists over "
    "longer intervals."
)

PLUVIANO_2017_RESULT = (
    "This time, beliefs in the vaccines/autism link were statistically significantly higher "
    "in the myths vs. facts condition compared to the visual (M = .97, SE = .22, p < .001) "
    "and control condition (M = .8, SE = .22, p = .002), and in the fear condition compared "
    "to visual condition (M = .67, SE = .22, p = .016)."
)
PLUVIANO_2017_LIMITATION = prose(
    "Some aspects of our experimental procedures may limit the generalization of the findings.",
    "Firstly, we used a convenience sample with limited variability in age and educational level.",
)

PLUVIANO_2019_RESULT = (
    "Data provided support for the existence of backfire effects associated with the use of "
    "the myths vs. fact format, with parents in this condition having stronger vaccine "
    "misconceptions over time compared with participants in the control condition."
)
PLUVIANO_2019_DEPENDENCE = (
    "We opted for a 7-day delay between the two tests as suggested by Nyhan et al.’s (2014) "
    "study and to allow a straight comparison with our own previous study (Pluviano et al. 2017)."
)

THOMAS_2024_RESULT = (
    "Misinformation use was significantly greater when a correction was provided without "
    "licensing than when no information was provided at all."
)
THOMAS_2024_MECHANISM = (
    "We suggest that the backfire effect observed in this study may be the result of a "
    "violation of the Gricean maxims of communication"
)

NIBAT_2026_SCOPE = (
    "Across five studies (N = 4337), this article systematically compares the competing "
    "effects of repetition and correction on belief in corporate misinformation and brand "
    "evaluations."
)
NIBAT_2026_RESULT = (
    "This research finds no evidence of a familiarity backfire effect: in none of the studies, "
    "repetition increases belief in the misinformation more than correction reduces it."
)

CAMERON_2013_KNOWLEDGE = (
    "All participants’ knowledge scores increased significantly (p <0.05); those exposed to "
    "the CDC Control message had a higher posttest knowledge score (adjusted mean=11.18) than "
    "those in the Facts Only condition (adjusted mean 9.61, p=<0.02)."
)
CAMERON_2013_NO_COUNTERPRODUCTIVE = (
    "We found no evidence that presenting both facts and myths is counterproductive to recall "
    "accuracy."
)
ECKER_SHORT_2020_RESULT = (
    "Regarding (1), simple retractions reduced belief in false claims, and we found no evidence "
    "for a familiarity‐driven backfire effect."
)
SWIRE_THOMPSON_2023_RESULT = prose(
    "In two nearly identical experiments, we conducted a longitudinal pre/post design with "
    "N = 388 and 532 participants.",
    "Participants rated 21 misinformation items and were assigned to a correction condition "
    "or test-retest control.",
    "We found that no items backfired more in the correction condition compared to test-retest "
    "control or initial belief ratings.",
)
PETER_KOCH_2016_RESULT = (
    "In a web-based experiment, we find evidence for a systematic backfire effect that occurs "
    "after a few minutes and strengthens after five days."
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
                "No article-specific Creative Commons grant was visible in the exact 2016 "
                "publisher rendition; it is treated as restricted and only quote-minimal "
                "transcript extents and metadata are retained."
            ),
            "visibility": "public",
        },
        {
            "key": "work-peter-koch-2016",
            "kind": "paper",
            "title": "When Debunking Scientific Myths Fails (and When It Does Not)",
            "creators": ["Christina Peter", "Thomas Koch"],
            "canonical_uri": "https://doi.org/10.1177/1075547015613523",
            "license": (
                "Crossref exposes the abstract under SAGE text-and-data-mining terms, not an "
                "open article reuse license; one quote-minimal result sentence is retained."
            ),
            "visibility": "public",
        },
        {
            "key": "work-cameron-2013",
            "kind": "paper",
            "title": (
                "Patient Knowledge and Recall of Health Information Following Exposure to "
                "\u201cFacts and Myths\u201d Message Format Variations"
            ),
            "creators": [
                "Kenzie A. Cameron",
                "Michael E. Roloff",
                "Elisha M. Friesema",
                "Tiffany Brown",
                "Borko D. Jovanovic",
                "Sara Hauber",
                "David W. Baker",
            ],
            "canonical_uri": "https://doi.org/10.1016/j.pec.2013.06.017",
            "license": (
                "The examined NCBI author-manuscript XML permits text mining and fair-use "
                "treatment but states no open reuse license; only short attributed abstract "
                "results are retained."
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
            "key": "work-ecker-short-2020",
            "kind": "paper",
            "title": "The effectiveness of short‐format refutational fact‐checks",
            "creators": ["Ullrich K. H. Ecker", "Ziggy O’Reilly", "Jesse S. Reid", "Ee Pin Chang"],
            "canonical_uri": "https://doi.org/10.1111/bjop.12383",
            "license": (
                "Crossref identifies both accepted-manuscript and version-of-record content "
                "as Creative Commons Attribution-NonCommercial-NoDerivatives 4.0; one short "
                "attributed abstract result is retained."
            ),
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
        {
            "key": "work-autry-2021",
            "kind": "paper",
            "title": prose(
                "Correcting the unknown: Negated corrections may increase belief in",
                "misinformation",
            ),
            "creators": ["Kevin S. Autry", "Shea E. Duarte"],
            "canonical_uri": "https://doi.org/10.1002/acp.3823",
            "license": (
                "Crossref identifies the version of record as CC BY 4.0; the excerpt packet "
                "also records publisher-HTML qualification and timing spans requiring "
                "independent read-back."
            ),
            "visibility": "public",
        },
        {
            "key": "work-pluviano-2017",
            "kind": "paper",
            "title": (
                "Misinformation lingers in memory: Failure of three pro-vaccination strategies"
            ),
            "creators": ["Sara Pluviano", "Caroline Watt", "Sergio Della Sala"],
            "canonical_uri": "https://doi.org/10.1371/journal.pone.0181640",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0).",
            "visibility": "public",
        },
        {
            "key": "work-pluviano-2019",
            "kind": "paper",
            "title": (
                "Parents’ beliefs in misinformation about vaccines are strengthened by "
                "pro-vaccine campaigns"
            ),
            "creators": [
                "Sara Pluviano",
                "Caroline Watt",
                "Giovanni Ragazzini",
                "Sergio Della Sala",
            ],
            "canonical_uri": "https://doi.org/10.1007/s10339-019-00919-w",
            "license": (
                "Examined accepted manuscript retains author or publisher rights; two short "
                "attributed excerpts are retained and the PDF is not redistributed."
            ),
            "visibility": "public",
        },
        {
            "key": "work-thomas-2024",
            "kind": "paper",
            "title": (
                "Unlicensed Corrections Violate the Gricean Maxims of Communication: "
                "Evidence for a Cognitive Mechanism Underlying Misinformation Backfire Effects"
            ),
            "creators": ["Jacob G. Thomas", "Kevin S. Autry"],
            "canonical_uri": "https://doi.org/10.1002/acp.70004",
            "license": (
                "No open reuse license was confirmed for the version of record; only short "
                "attributed abstract fragments are retained and the article is not redistributed."
            ),
            "visibility": "public",
        },
        {
            "key": "work-swire-thompson-2023",
            "kind": "paper",
            "title": (
                "The backfire effect after correcting misinformation is strongly associated "
                "with reliability"
            ),
            "creators": [
                "Briony Swire-Thompson",
                "Nicholas Miklaucic",
                "John P. Wihbey",
                "David Lazer",
                "Joseph DeGutis",
            ],
            "canonical_uri": "https://doi.org/10.1037/xge0001131",
            "license": (
                "The examined NCBI author-manuscript XML permits text mining and fair-use "
                "treatment but states no open reuse license; only short attributed abstract "
                "results are retained."
            ),
            "visibility": "public",
        },
        {
            "key": "work-nibat-2026",
            "kind": "paper",
            "title": (
                "Familiarity backfire effects? Disentangling the competing effects of "
                "repetition and fact-checking corrections of brand misinformation"
            ),
            "creators": [
                "Ipek N. Nibat",
                "Olivier Trendel",
                "Robert Mai",
                "Tinka Krüger",
                "Wassili Lasarov",
                "Stefan Hoffmann",
            ],
            "canonical_uri": "https://doi.org/10.1016/j.ijresmar.2026.03.007",
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
                    excerpt("2011 body; flu-vaccine flyer description", HANDBOOK_EXPERIMENT),
                    excerpt("2011 body; 30-minute delayed result", HANDBOOK_DELAY),
                    excerpt("References; item 1", HANDBOOK_REFERENCE),
                    excerpt("2020 update notice", HANDBOOK_UPDATE),
                ],
            },
        ),
        edition(
            "edition-schwarz-2016",
            "work-schwarz-2016",
            "Publisher PDF, volume 2 issue 1, pages 85–95; independently read excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://journals.sagepub.com/doi/pdf/10.1177/237946151600200110"
                    ),
                    "sha256": None,
                    "bytes": None,
                    "custody": (
                        "Authoritative publisher text independently visible through web "
                        "read-back; automated byte capture returned HTTP 403."
                    ),
                },
                "alternate_identifiers": ["https://doi.org/10.1353/bsp.2016.0009"],
                "excerpts": [
                    excerpt(
                        "PDF page 1; abstract opening",
                        SCHWARZ_CLAIM,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "PDF page 6; journal page 90; 2005 delayed result sentence",
                        SCHWARZ_SKURNIK_2005_DELAY,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "PDF page 6; journal page 90; 2005 older-adult sentence",
                        SCHWARZ_SKURNIK_2005_OLDER,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "PDF page 7; journal page 91; flu-flyer memory sentence",
                        SCHWARZ_FLU_2007_MEMORY,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "PDF page 7; journal page 91; flu-flyer intentions sentence",
                        SCHWARZ_FLU_2007_INTENTIONS,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "PDF page 10; reference 6",
                        SCHWARZ_REFERENCE_6,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "PDF page 10; reference 42",
                        SCHWARZ_REFERENCE,
                        verification="independent-readback",
                    ),
                ],
            },
        ),
        edition(
            "edition-peter-koch-2016",
            "work-peter-koch-2016",
            "Crossref deposited abstract record; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": ("https://api.crossref.org/works/10.1177/1075547015613523"),
                    "sha256": "5c5b6743373d7d8539d21a31f6ac33ba461d4625834109e13efdcd3f87181494",
                    "bytes": 10168,
                    "custody": "Temporary Crossref JSON capture; article is not redistributed.",
                },
                "excerpts": [
                    excerpt("Crossref abstract; web-experiment result", PETER_KOCH_2016_RESULT)
                ],
            },
            retrieved_at=REVIEW_REPAIR_RETRIEVED_AT,
        ),
        edition(
            "edition-cameron-2013",
            "work-cameron-2013",
            "NCBI BioC XML, PMCID PMC3772650; author-manuscript excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/"
                        "pmcoa.cgi/BioC_xml/PMC3772650/unicode"
                    ),
                    "sha256": "40b29203eb82caf07c0a0c8d46438f01efb21795b39941aea03b3c898cd36ecb",
                    "bytes": 78951,
                    "custody": (
                        "Two byte-identical NCBI BioC XML retrievals; only exact abstract "
                        "results are committed in the excerpt packet."
                    ),
                },
                "excerpts": [
                    excerpt("BioC abstract; knowledge-score result", CAMERON_2013_KNOWLEDGE),
                    excerpt(
                        "BioC abstract; no-counterproductive-recall conclusion",
                        CAMERON_2013_NO_COUNTERPRODUCTIVE,
                    ),
                ],
            },
            retrieved_at="2026-08-22T16:12:27Z",
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
                    excerpt(
                        "Introduction; paragraph 7; unpublished 2007 lineage",
                        ECKER_2020_UNPUBLISHED_LINEAGE,
                    ),
                    excerpt(
                        "Introduction; paragraph 7; missing-baseline qualification",
                        ECKER_2020_NO_BASELINE,
                    ),
                    excerpt("Experiment 1; participants", ECKER_2020_RECRUITMENT),
                    excerpt(
                        "Experiment 1; procedure; administration platform",
                        ECKER_2020_CLOUDRESEARCH,
                    ),
                    excerpt(
                        "Introduction; paragraph 8; Ecker et al. 2011 search exclusion",
                        ECKER_2020_ECKER_2011_SEARCH,
                    ),
                    excerpt(
                        "Introduction; paragraph 8; Ecker et al. 2017 search exclusion",
                        ECKER_2020_ECKER_2017_SEARCH,
                    ),
                    excerpt(
                        "Introduction; paragraph 8; Swire et al. 2017 search lead",
                        ECKER_2020_SWIRE_2017_SEARCH,
                    ),
                ],
            },
        ),
        edition(
            "edition-ecker-short-2020",
            "work-ecker-short-2020",
            "Crossref deposited abstract record; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": "https://api.crossref.org/works/10.1111/bjop.12383",
                    "sha256": "07408e83b8ff2702d8e7615829427bc2e93c5d0d586642ee5b67d05eb78c6ee5",
                    "bytes": 10954,
                    "custody": "Temporary Crossref JSON capture; article is not redistributed.",
                },
                "excerpts": [
                    excerpt("Crossref abstract; simple-retraction result", ECKER_SHORT_2020_RESULT)
                ],
            },
            retrieved_at="2026-08-22T16:12:15Z",
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
                    excerpt("Abstract; results and qualification sentences", PRIKE_2023_RESULT),
                    excerpt("Experiment 1; participants", PRIKE_2023_RECRUITMENT),
                    excerpt("Ethics approval", PRIKE_2023_ETHICS),
                    excerpt("General discussion; sample comparison", PRIKE_2023_AUTRY_SAMPLE),
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
                "excerpts": [
                    excerpt("Abstract; outcome sentences", ECKER_2023_RESULT),
                    excerpt("Method; participants", ECKER_2023_RECRUITMENT),
                    excerpt("Method; materials source", ECKER_2023_MATERIALS),
                    excerpt("Method; ethics approval", ECKER_2023_ETHICS),
                ],
            },
        ),
        edition(
            "edition-autry-2021",
            "work-autry-2021",
            "Publisher-deposited Crossref record plus publisher HTML qualifier; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": "https://api.crossref.org/works/10.1002/acp.3823",
                    "sha256": "39293b19eb31c866b74e5017f7af0377f52a227162b034ad1f4c84471e82906d",
                    "bytes": 9943,
                    "custody": (
                        "Temporary Crossref JSON capture; publisher HTML qualifier was read "
                        "separately and requires independent read-back."
                    ),
                },
                "excerpts": [
                    excerpt("Crossref abstract; result sentence", AUTRY_2021_RESULT),
                    excerpt(
                        "Publisher HTML; general discussion; qualified result",
                        AUTRY_2021_QUALIFIER,
                        verification="independent-readback",
                    ),
                    excerpt(
                        "Publisher HTML; limitations; timing and persistence",
                        AUTRY_2021_TIMING_LIMIT,
                        verification="independent-readback",
                    ),
                ],
                "data_artifacts": [
                    {
                        "label": "Experiment 1 inference data",
                        "project_uri": "https://osf.io/yweu6/",
                        "file_id": "5df17dee078b52000c5ae2d2",
                        "retrieved_from": "https://osf.io/download/37ewu/",
                        "license_record": (
                            "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96c/"
                        ),
                        "sha256": (
                            "bc069a90152b887116cd4972df4376844570ba25cefbfa1055668c78eeaca80a"
                        ),
                        "bytes": 148954,
                        "license_treatment": (
                            "The OSF project yweu6 declares CC0 1.0 Universal at project scope; "
                            "the workbook identity and digest are recorded, while its bytes "
                            "remain outside the repository."
                        ),
                    },
                    {
                        "label": "Experiment 2 inference data",
                        "project_uri": "https://osf.io/yweu6/",
                        "file_id": "5df17dfc18536f000c8e4c72",
                        "retrieved_from": "https://osf.io/download/kqjm2/",
                        "license_record": (
                            "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96c/"
                        ),
                        "sha256": (
                            "de9f27b026ceadea0a6309ef695be06bc06c1fa35ba9209260f246d89b108ea5"
                        ),
                        "bytes": 216736,
                        "license_treatment": (
                            "The OSF project yweu6 declares CC0 1.0 Universal at project scope; "
                            "the workbook identity and digest are recorded, while its bytes "
                            "remain outside the repository."
                        ),
                    },
                ],
                "readback_sources": [
                    {
                        "label": "Wiley version-of-record HTML",
                        "retrieved_from": ("https://onlinelibrary.wiley.com/doi/10.1002/acp.3823"),
                        "custody": (
                            "Exact qualifier and timing spans require independent publisher "
                            "read-back; automated full-page capture returned HTTP 403."
                        ),
                    }
                ],
            },
            retrieved_at=CORRECTION_RETRIEVED_AT,
        ),
        edition(
            "edition-pluviano-2017",
            "work-pluviano-2017",
            "PLOS JATS XML; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5547702/fullTextXML"
                    ),
                    "sha256": "87e363cb1cae5896c42c7e7e0295bd2e6969637473d14ff76deea3c740024377",
                    "bytes": 114003,
                    "custody": "Temporary CC BY 4.0 XML capture; exact excerpt committed.",
                },
                "excerpts": [
                    excerpt("Results; beliefs in vaccines/autism link", PLUVIANO_2017_RESULT),
                    excerpt("Discussion; limitations paragraph 8", PLUVIANO_2017_LIMITATION),
                ],
            },
            retrieved_at=CORRECTION_RETRIEVED_AT,
        ),
        edition(
            "edition-pluviano-2019",
            "work-pluviano-2019",
            "University of Edinburgh accepted manuscript; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.pure.ed.ac.uk/ws/portalfiles/portal/82242964/"
                        "Parents_belief_in_misinformation.pdf"
                    ),
                    "identity_mode": "pdftotext-stdout",
                    "semantic_sha256": (
                        "cd054a8f7e1bcb31a6d7f700b775eb936c9e0d3f43899cd8411b01f6252ff670"
                    ),
                    "semantic_bytes": 36848,
                    "semantic_method": "pdftotext SOURCE.pdf -; raw stdout bytes",
                    "sha256": None,
                    "bytes": None,
                    "captures": [
                        {
                            "retrieved_at": CORRECTION_RETRIEVED_AT,
                            "sha256": (
                                "42968a50225e7ef7c65afd35742d2fc47eec5bf0c394faca48543850c1b5fb60"
                            ),
                            "bytes": 762139,
                        },
                        {
                            "retrieved_at": "2026-08-22T16:09:47Z",
                            "sha256": (
                                "97b7132942e3ad7772bcd0123334429fbfc3bc1169975dc26ea7dccac3be0c71"
                            ),
                            "bytes": 762139,
                        },
                    ],
                    "custody": (
                        "The institutional endpoint regenerates a timestamped cover, so raw PDF "
                        "digests are capture-specific. Two raw captures produced byte-identical "
                        "pdftotext output; only short excerpts are committed and the PDF is not "
                        "redistributed."
                    ),
                },
                "excerpts": [
                    excerpt("Accepted manuscript page 2; abstract", PLUVIANO_2019_RESULT),
                    excerpt(
                        "Accepted manuscript procedure; comparison with prior study",
                        PLUVIANO_2019_DEPENDENCE,
                    ),
                ],
            },
            retrieved_at=CORRECTION_RETRIEVED_AT,
        ),
        edition(
            "edition-thomas-2024",
            "work-thomas-2024",
            "Publisher-deposited Crossref record; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": "https://api.crossref.org/works/10.1002/acp.70004",
                    "sha256": "f71d065da32f2179ff262008a863cae22aeec81b01e59997c994a1871e87bf23",
                    "bytes": 11291,
                    "custody": "Temporary Crossref JSON capture; article is not redistributed.",
                },
                "excerpts": [
                    excerpt("Crossref abstract; result sentence", THOMAS_2024_RESULT),
                    excerpt(
                        "Crossref abstract; mechanism sentence fragment", THOMAS_2024_MECHANISM
                    ),
                ],
                "data_artifacts": [
                    {
                        "label": "Study data workbook",
                        "project_uri": "https://osf.io/y65ke/",
                        "file_id": "654a7d79f5503205568a1111",
                        "retrieved_from": "https://osf.io/download/fg3dy/",
                        "sha256": (
                            "4a65116f6f10b02dc34b8353a228a16604a48ebcca576b2aae91ad5073f4d66c"
                        ),
                        "bytes": 644279,
                        "license_treatment": (
                            "No separate OSF data license was confirmed; identity and digest "
                            "only, with workbook bytes kept outside the repository."
                        ),
                    }
                ],
            },
            retrieved_at=CORRECTION_RETRIEVED_AT,
        ),
        edition(
            "edition-swire-thompson-2023",
            "work-swire-thompson-2023",
            "NCBI BioC XML, PMCID PMC9283209; author-manuscript excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/"
                        "pmcoa.cgi/BioC_xml/PMC9283209/unicode"
                    ),
                    "sha256": "0480d8d31af7c1525433838c91b8fc49f33997b95038ded5de40f255e54af5a2",
                    "bytes": 93558,
                    "custody": (
                        "Two byte-identical NCBI BioC XML retrievals; only exact abstract "
                        "results are committed in the excerpt packet."
                    ),
                },
                "excerpts": [
                    excerpt(
                        "BioC abstract; design, controls, and no-backfire result",
                        SWIRE_THOMPSON_2023_RESULT,
                    )
                ],
            },
            retrieved_at="2026-08-22T16:12:27Z",
        ),
        edition(
            "edition-nibat-2026",
            "work-nibat-2026",
            "Sabanci University author-deposited Elsevier corrected proof; excerpt packet",
            "application/json",
            {
                "artifact": {
                    "retrieved_from": (
                        "https://research.sabanciuniv.edu/id/eprint/54047/1/Familiarity.pdf"
                    ),
                    "landing_page": "https://research.sabanciuniv.edu/id/eprint/54047/",
                    "sha256": "99075c8a58b19d3be262486ccb78b3508747887e350802e5b41b74390b13d3bc",
                    "bytes": 2525138,
                    "custody": "Temporary CC BY 4.0 PDF download; exact excerpts committed.",
                },
                "excerpts": [
                    excerpt("PDF page 1; abstract scope", NIBAT_2026_SCOPE),
                    excerpt("PDF page 1; abstract result", NIBAT_2026_RESULT),
                ],
            },
            retrieved_at=CORRECTION_RETRIEVED_AT,
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
            "span-handbook-experiment",
            "edition-handbook-2011",
            2,
            "2011 body flu-vaccine flyer description",
            HANDBOOK_EXPERIMENT,
        ),
        span(
            "span-handbook-delay",
            "edition-handbook-2011",
            3,
            "2011 body 30-minute delayed result",
            HANDBOOK_DELAY,
        ),
        span(
            "span-handbook-reference",
            "edition-handbook-2011",
            4,
            "Reference 1",
            HANDBOOK_REFERENCE,
        ),
        span(
            "span-handbook-update",
            "edition-handbook-2011",
            5,
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
            "span-schwarz-skurnik-2005-delay",
            "edition-schwarz-2016",
            1,
            "PDF p. 6 / journal p. 90, delayed result sentence",
            SCHWARZ_SKURNIK_2005_DELAY,
        ),
        span(
            "span-schwarz-skurnik-2005-older",
            "edition-schwarz-2016",
            2,
            "PDF p. 6 / journal p. 90, older-adult sentence",
            SCHWARZ_SKURNIK_2005_OLDER,
        ),
        span(
            "span-schwarz-flu-2007-memory",
            "edition-schwarz-2016",
            3,
            "PDF p. 7 / journal p. 91, flu-flyer memory sentence",
            SCHWARZ_FLU_2007_MEMORY,
        ),
        span(
            "span-schwarz-flu-2007-intentions",
            "edition-schwarz-2016",
            4,
            "PDF p. 7 / journal p. 91, flu-flyer intentions sentence",
            SCHWARZ_FLU_2007_INTENTIONS,
        ),
        span(
            "span-schwarz-reference-6",
            "edition-schwarz-2016",
            5,
            "PDF p. 10, reference 6",
            SCHWARZ_REFERENCE_6,
        ),
        span(
            "span-schwarz-reference-42",
            "edition-schwarz-2016",
            6,
            "PDF p. 10, reference 42",
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
            "span-ecker-2020-unpublished-lineage",
            "edition-ecker-2020",
            3,
            "Introduction paragraph 7, unpublished 2007 lineage",
            ECKER_2020_UNPUBLISHED_LINEAGE,
        ),
        span(
            "span-ecker-2020-no-baseline",
            "edition-ecker-2020",
            4,
            "Introduction paragraph 7, missing-baseline qualification",
            ECKER_2020_NO_BASELINE,
        ),
        span(
            "span-ecker-2020-recruitment",
            "edition-ecker-2020",
            5,
            "Experiment 1 participants",
            ECKER_2020_RECRUITMENT,
        ),
        span(
            "span-ecker-2020-cloudresearch",
            "edition-ecker-2020",
            6,
            "Experiment 1 procedure administration platform",
            ECKER_2020_CLOUDRESEARCH,
        ),
        span(
            "span-ecker-2020-ecker-2011-search",
            "edition-ecker-2020",
            7,
            "Introduction paragraph 8 Ecker et al. 2011 exclusion",
            ECKER_2020_ECKER_2011_SEARCH,
        ),
        span(
            "span-ecker-2020-ecker-2017-search",
            "edition-ecker-2020",
            8,
            "Introduction paragraph 8 Ecker et al. 2017 exclusion",
            ECKER_2020_ECKER_2017_SEARCH,
        ),
        span(
            "span-ecker-2020-swire-2017-search",
            "edition-ecker-2020",
            9,
            "Introduction paragraph 8 Swire et al. 2017 search lead",
            ECKER_2020_SWIRE_2017_SEARCH,
        ),
        span(
            "span-peter-koch-2016-result",
            "edition-peter-koch-2016",
            0,
            "Crossref abstract web-experiment result",
            PETER_KOCH_2016_RESULT,
        ),
        span(
            "span-cameron-2013-knowledge",
            "edition-cameron-2013",
            0,
            "BioC abstract knowledge-score result",
            CAMERON_2013_KNOWLEDGE,
        ),
        span(
            "span-cameron-2013-no-counterproductive",
            "edition-cameron-2013",
            1,
            "BioC abstract no-counterproductive-recall conclusion",
            CAMERON_2013_NO_COUNTERPRODUCTIVE,
        ),
        span(
            "span-ecker-short-2020-result",
            "edition-ecker-short-2020",
            0,
            "Crossref abstract simple-retraction result",
            ECKER_SHORT_2020_RESULT,
        ),
        span(
            "span-prike-2023-result",
            "edition-prike-2023",
            0,
            "Abstract results and qualification",
            PRIKE_2023_RESULT,
        ),
        span(
            "span-prike-2023-recruitment",
            "edition-prike-2023",
            1,
            "Experiment 1 participants",
            PRIKE_2023_RECRUITMENT,
        ),
        span(
            "span-prike-2023-ethics",
            "edition-prike-2023",
            2,
            "Ethics approval",
            PRIKE_2023_ETHICS,
        ),
        span(
            "span-prike-2023-autry-sample",
            "edition-prike-2023",
            3,
            "General discussion sample comparison",
            PRIKE_2023_AUTRY_SAMPLE,
        ),
        span(
            "span-ecker-2023-result",
            "edition-ecker-2023",
            0,
            "Abstract outcome",
            ECKER_2023_RESULT,
        ),
        span(
            "span-ecker-2023-recruitment",
            "edition-ecker-2023",
            1,
            "Method participants",
            ECKER_2023_RECRUITMENT,
        ),
        span(
            "span-ecker-2023-materials",
            "edition-ecker-2023",
            2,
            "Method materials source",
            ECKER_2023_MATERIALS,
        ),
        span(
            "span-ecker-2023-ethics",
            "edition-ecker-2023",
            3,
            "Method ethics approval",
            ECKER_2023_ETHICS,
        ),
        span(
            "span-autry-2021-result",
            "edition-autry-2021",
            0,
            "Crossref abstract result",
            AUTRY_2021_RESULT,
        ),
        span(
            "span-autry-2021-qualifier",
            "edition-autry-2021",
            1,
            "Publisher HTML general-discussion qualifier",
            AUTRY_2021_QUALIFIER,
        ),
        span(
            "span-autry-2021-timing-limit",
            "edition-autry-2021",
            2,
            "Publisher HTML limitations timing and persistence",
            AUTRY_2021_TIMING_LIMIT,
        ),
        span(
            "span-pluviano-2017-result",
            "edition-pluviano-2017",
            0,
            "Results vaccine-autism comparison",
            PLUVIANO_2017_RESULT,
        ),
        span(
            "span-pluviano-2017-limitation",
            "edition-pluviano-2017",
            1,
            "Discussion limitations paragraph 8",
            PLUVIANO_2017_LIMITATION,
        ),
        span(
            "span-pluviano-2019-result",
            "edition-pluviano-2019",
            0,
            "Accepted manuscript abstract result",
            PLUVIANO_2019_RESULT,
        ),
        span(
            "span-pluviano-2019-dependence",
            "edition-pluviano-2019",
            1,
            "Procedure comparison with prior study",
            PLUVIANO_2019_DEPENDENCE,
        ),
        span(
            "span-thomas-2024-result",
            "edition-thomas-2024",
            0,
            "Crossref abstract result",
            THOMAS_2024_RESULT,
        ),
        span(
            "span-thomas-2024-mechanism",
            "edition-thomas-2024",
            1,
            "Crossref abstract mechanism",
            THOMAS_2024_MECHANISM,
        ),
        span(
            "span-nibat-2026-scope",
            "edition-nibat-2026",
            0,
            "PDF p. 1 abstract scope",
            NIBAT_2026_SCOPE,
        ),
        span(
            "span-nibat-2026-result",
            "edition-nibat-2026",
            1,
            "PDF p. 1 abstract result",
            NIBAT_2026_RESULT,
        ),
        span(
            "span-swire-thompson-2023-result",
            "edition-swire-thompson-2023",
            0,
            "BioC abstract design, controls, and no-backfire result",
            SWIRE_THOMPSON_2023_RESULT,
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
                "claims among older adults in two experiments, but the study lacked the "
                "no-correction or pre-correction baseline required by this dossier’s target."
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
        {
            "key": "prop-flu-flyer-result",
            "text": (
                "An unpublished 2007 study reportedly found worse myth classification and "
                "lower flu-vaccination intentions after a myths-and-facts flyer than in the "
                "relevant control conditions."
            ),
            "scope": (
                "Skurnik, Yoon, and Schwarz 2007 participant data as described in later "
                "publications; the manuscript and participant-level record remain unavailable."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-unlicensed-negation-boundary",
            "text": (
                "A standalone negated correction can increase later use of a previously unseen "
                "claim when the negation lacks contextual licensing, although the exact effect "
                "did not reach significance in every experiment."
            ),
            "scope": (
                "Autry and Duarte 2021 and Thomas and Autry 2024; novel or unexpected negated "
                "details, not all correction formats."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-vaccine-myths-boundary",
            "text": (
                "Two vaccine-message studies reported delayed outcomes worse than control for "
                "myths-and-facts formats, while a later direct replication using the same "
                "materials did not reproduce the effect."
            ),
            "scope": (
                "Pluviano et al. 2017 and 2019 positive reports and Ecker et al. 2023 "
                "replication; vaccine beliefs and intentions in their tested samples."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-peter-koch-boundary",
            "text": (
                "Peter and Koch reported a delayed backfire effect after journalistic "
                "myth-and-fact coverage, but the captured abstract does not establish the "
                "target comparator design used by this dossier."
            ),
            "scope": (
                "Peter and Koch 2016 web experiment; result is visible, while target "
                "comparability remains unassessed without an exact methods span."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-cameron-flu-result",
            "text": (
                "Cameron et al. found knowledge gains across flu-message conditions and no "
                "evidence that presenting facts and myths was counterproductive to recall "
                "accuracy."
            ),
            "scope": (
                "Cameron et al. 2013 randomized flu-message study; knowledge and recall "
                "outcomes over the tested one-week interval."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-short-format-result",
            "text": (
                "Simple retractions reduced false-claim belief and did not show a "
                "familiarity-driven backfire effect in the Ecker et al. short-format series."
            ),
            "scope": "Ecker et al. 2020 short-format fact-check experiments and tested delays.",
            "visibility": "public",
        },
        {
            "key": "prop-reliability-counter-result",
            "text": (
                "Across two correction-versus-test-retest experiments, no item backfired "
                "relative to the control or initial-belief baselines."
            ),
            "scope": (
                "Swire-Thompson et al. 2023, published online in 2022; 21 items and two "
                "participant samples."
            ),
            "visibility": "public",
        },
        {
            "key": "prop-brand-correction-result",
            "text": (
                "Across five brand-misinformation studies, repetition did not increase belief "
                "more than correction reduced it."
            ),
            "scope": (
                "Nibat et al. 2026; corporate misinformation, fact-check labels, brand "
                "familiarity, immediate and delayed tests, and first-exposure corrections."
            ),
            "visibility": "public",
        },
    ]

    lineages = [
        {
            "key": "lineage-skurnik-2005-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-skurnik-summary", "span-ecker-2020-no-baseline"],
            "assertion_keys": ["assert-skurnik-result"],
            "note": (
                "Published 2005 participant-data root. Its older-adult and consumer-claim "
                "scope must not silently become a general population result, and the paper "
                "did not include the baseline required for target-comparable backfire."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-skurnik-2007-data",
            "status": "unknown",
            "dimensions": ["data", "method", "apparatus"],
            "depends_on": [],
            "basis_span_keys": [
                "span-ecker-2020-unpublished-lineage",
                "span-schwarz-flu-2007-memory",
                "span-schwarz-flu-2007-intentions",
                "span-schwarz-reference-6",
            ],
            "assertion_keys": [],
            "note": (
                "Unknown participant-data root for the unpublished Skurnik, Yoon, and "
                "Schwarz 2007 flu-flyer manuscript. Later sources describe the result, but "
                "the manuscript, data, sample record, and direct edition remain unavailable."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-handbook-guidance",
            "status": "known",
            "dimensions": ["source", "social"],
            "depends_on": ["lineage-skurnik-2007-data"],
            "basis_span_keys": [
                "span-handbook-experiment",
                "span-handbook-delay",
                "span-handbook-reference",
                "span-ecker-2020-unpublished-lineage",
            ],
            "assertion_keys": ["assert-handbook-claim"],
            "note": (
                "The page describes the 30-minute flu-flyer study but its sole numbered "
                "reference names the nonmatching 2005 paper. Later literature identifies the "
                "described data as the unpublished 2007 study, so the page adds a mention and "
                "guidance, not a participant-data root."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-schwarz-general-review",
            "status": "known",
            "dimensions": ["source", "method", "social"],
            "depends_on": ["lineage-skurnik-2005-data", "lineage-skurnik-2007-data"],
            "basis_span_keys": [
                "span-schwarz-claim",
                "span-schwarz-skurnik-2005-delay",
                "span-schwarz-skurnik-2005-older",
                "span-schwarz-flu-2007-memory",
                "span-schwarz-flu-2007-intentions",
                "span-schwarz-reference-6",
                "span-schwarz-reference-42",
            ],
            "assertion_keys": ["assert-schwarz-claim"],
            "note": (
                "Review-level synthesis, not participant data. The publisher PDF maps its "
                "2005 delayed older-adult passage to reference 42 and its separate flu-flyer "
                "passage to reference 6; the latter leads to the unknown 2007 data root."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-schwarz-flu-review",
            "status": "known",
            "dimensions": ["source", "method"],
            "depends_on": ["lineage-skurnik-2007-data"],
            "basis_span_keys": [
                "span-schwarz-flu-2007-memory",
                "span-schwarz-flu-2007-intentions",
                "span-schwarz-reference-6",
                "span-ecker-2020-unpublished-lineage",
            ],
            "assertion_keys": ["assert-schwarz-flu-result"],
            "note": (
                "The 2016 flu-flyer passage cites the 2007 Schwarz et al. review, while Ecker "
                "et al. 2020 identifies that review as discussing the unpublished 2007 "
                "participant data. This is a review mention, not a new data root."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2020-historical-report",
            "status": "known",
            "dimensions": ["source", "social"],
            "depends_on": ["lineage-skurnik-2007-data"],
            "basis_span_keys": ["span-ecker-2020-unpublished-lineage"],
            "assertion_keys": ["assert-ecker-2020-historical-report"],
            "note": (
                "A historical report of the unpublished 2007 participant-data lineage, not "
                "a new participant-data root. It receives no independent data credit."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2020-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": [
                "span-ecker-2020-result",
                "span-ecker-2020-guidance-conclusion",
            ],
            "assertion_keys": ["assert-ecker-2020-result"],
            "note": (
                "One participant-data root for the Ecker et al. 2020 publication. Method "
                "and recruitment overlap are modeled separately so they do not collapse "
                "this paper-defined data collection into another data root."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-peter-koch-2016-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-peter-koch-2016-result"],
            "assertion_keys": ["assert-peter-koch-2016-result"],
            "note": (
                "Publication-defined participant-data root for a delayed journalistic "
                "myth-debunking result. The captured abstract does not expose the comparator "
                "needed to classify it as target-comparable."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-cameron-2013-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": [
                "span-cameron-2013-knowledge",
                "span-cameron-2013-no-counterproductive",
            ],
            "assertion_keys": ["assert-cameron-2013-result"],
            "note": (
                "Publication-defined participant-data root for the randomized flu-message "
                "study. Its CDC condition belongs to the historical flu-flyer family, but "
                "the participant collection is separately reported."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2020-method",
            "status": "known",
            "dimensions": ["method", "social"],
            "depends_on": [],
            "basis_span_keys": [
                "span-ecker-2020-recruitment",
                "span-ecker-2020-cloudresearch",
            ],
            "assertion_keys": [],
            "note": (
                "Recruitment-method lineage for the US MTurk and CloudResearch frame, "
                "including the 5000-HIT and 97% approval thresholds."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-short-2020-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-ecker-short-2020-result"],
            "assertion_keys": ["assert-ecker-short-2020-result"],
            "note": (
                "Publication-defined two-experiment participant-data root. It shares Ecker "
                "and a correction research program with later papers, but no data reuse is "
                "asserted."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2020-interpretation",
            "status": "known",
            "dimensions": ["source", "social"],
            "depends_on": ["lineage-ecker-2020-data"],
            "basis_span_keys": [
                "span-ecker-2020-guidance-overreach",
                "span-ecker-2020-guidance-conclusion",
            ],
            "assertion_keys": ["assert-ecker-2020-guidance"],
            "note": "Interpretive guidance derived from the paper's participant-data series.",
            "visibility": "public",
        },
        {
            "key": "lineage-prike-2023-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-prike-2023-result"],
            "assertion_keys": ["assert-prike-2023-result", "assert-prike-2023-skepticism"],
            "note": (
                "Separately reported participant-data root. It shares authors and a research "
                "program with Ecker et al. 2023 and shares the US MTurk/CloudResearch frame "
                "and thresholds with Ecker et al. 2020. Cross-paper participant overlap is "
                "unverified; only the paper-defined data collection is counted separately."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-prike-2023-method",
            "status": "known",
            "dimensions": ["method", "social"],
            "depends_on": [],
            "basis_span_keys": [
                "span-prike-2023-recruitment",
                "span-prike-2023-ethics",
                "span-prike-2023-autry-sample",
            ],
            "assertion_keys": [],
            "note": (
                "Method and research-team lineage. The MTurk frame matches Ecker et al. "
                "2020, while authors and the UWA ethics series overlap Ecker et al. 2023."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2023-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-ecker-2023-result"],
            "assertion_keys": ["assert-ecker-2023-result"],
            "note": (
                "Separately reported UK Prolific participant-data root. It shares Ecker and "
                "Swire-Thompson, UWA ethics approval RA/4/20/6423, and a research program with "
                "Prike et al. 2023, and it directly reuses Pluviano et al. 2017 materials. "
                "Team, ethics, and material independence are not claimed."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-ecker-2023-method",
            "status": "known",
            "dimensions": ["method", "apparatus", "social"],
            "depends_on": ["lineage-pluviano-2017-method"],
            "basis_span_keys": [
                "span-ecker-2023-recruitment",
                "span-ecker-2023-materials",
                "span-ecker-2023-ethics",
            ],
            "assertion_keys": [],
            "note": (
                "Replication method and apparatus lineage. It directly reused the 2017 "
                "stimuli and overlaps the Prike research program in authors and ethics approval."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-autry-2021-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": [
                "span-autry-2021-result",
                "span-autry-2021-qualifier",
                "span-autry-2021-timing-limit",
                "span-prike-2023-autry-sample",
            ],
            "assertion_keys": ["assert-autry-2021-result"],
            "note": (
                "Separately reported undergraduate participant-data root. Experiment 1 found "
                "the unlicensed-negation effect; the same contrast was nonsignificant in "
                "Experiment 2. It shares Autry and a research program with Thomas 2024."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-pluviano-2017-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": [
                "span-pluviano-2017-result",
                "span-pluviano-2017-limitation",
            ],
            "assertion_keys": ["assert-pluviano-2017-result"],
            "note": (
                "Participant-data root for the 2017 student vaccine-message study. It shares "
                "authors, a vaccine-message research program, and materials with the 2019 "
                "study and the later Ecker et al. replication."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-pluviano-2017-method",
            "status": "known",
            "dimensions": ["method", "apparatus", "social"],
            "depends_on": [],
            "basis_span_keys": [
                "span-pluviano-2017-result",
                "span-pluviano-2017-limitation",
            ],
            "assertion_keys": [],
            "note": (
                "Student-sample vaccine-message method lineage. Later work reused or "
                "deliberately compared against this material and timing family."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-pluviano-2019-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": [
                "span-pluviano-2019-result",
                "span-pluviano-2019-dependence",
            ],
            "assertion_keys": ["assert-pluviano-2019-result"],
            "note": (
                "Separately reported parent participant-data root. It remains part of the "
                "same Pluviano author and vaccine-message program as the 2017 study, so "
                "program-level independence is not claimed."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-pluviano-2019-method",
            "status": "known",
            "dimensions": ["method", "apparatus", "social"],
            "depends_on": ["lineage-pluviano-2017-method"],
            "basis_span_keys": ["span-pluviano-2019-dependence"],
            "assertion_keys": [],
            "note": (
                "Parent-sample method lineage. The seven-day delay was explicitly chosen "
                "to allow straight comparison with the authors' 2017 study."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-thomas-2024-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-thomas-2024-result", "span-thomas-2024-mechanism"],
            "assertion_keys": ["assert-thomas-2024-result"],
            "note": (
                "Separately reported participant-data root testing unlicensed negated "
                "corrections with novel-word meanings. It shares Autry and a research program "
                "with Autry and Duarte 2021; program independence is not claimed."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-nibat-2026-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-nibat-2026-scope", "span-nibat-2026-result"],
            "assertion_keys": ["assert-nibat-2026-result"],
            "note": (
                "Separately reported participant-data root spanning five brand-misinformation "
                "studies and 4,337 participants. Author, sample, and method independence from "
                "the earlier paper series is not inferred merely from different authorship."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-swire-thompson-2023-data",
            "status": "known",
            "dimensions": ["data"],
            "depends_on": [],
            "basis_span_keys": ["span-swire-thompson-2023-result"],
            "assertion_keys": ["assert-swire-thompson-2023-result"],
            "note": (
                "Publication-defined two-experiment participant-data root. Swire-Thompson "
                "also appears in other modeled papers, but the captured report describes new "
                "samples and no data-reuse dependence is asserted."
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
            "span_keys": ["span-skurnik-summary", "span-ecker-2020-no-baseline"],
            "lineage_key": "lineage-skurnik-2005-data",
            "asserted_at": "2005-03-01T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-handbook-claim",
            "proposition_key": "prop-general-backfire",
            "actor": {"id": "web:debunking-handbook-2011#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": [
                "span-handbook-experiment",
                "span-handbook-delay",
                "span-handbook-claim",
                "span-handbook-advice",
                "span-handbook-reference",
            ],
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
            "lineage_key": "lineage-schwarz-general-review",
            "asserted_at": "2016-04-01T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-schwarz-flu-result",
            "proposition_key": "prop-flu-flyer-result",
            "actor": {"id": "doi:10.1177/237946151600200110#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": [
                "span-schwarz-flu-2007-memory",
                "span-schwarz-flu-2007-intentions",
                "span-schwarz-reference-6",
                "span-ecker-2020-unpublished-lineage",
            ],
            "lineage_key": "lineage-schwarz-flu-review",
            "asserted_at": "2016-04-01T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-ecker-2020-historical-report",
            "proposition_key": "prop-flu-flyer-result",
            "actor": {"id": "doi:10.1186/s41235-020-00241-6#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-ecker-2020-unpublished-lineage"],
            "lineage_key": "lineage-ecker-2020-historical-report",
            "asserted_at": "2020-08-26T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-peter-koch-2016-result",
            "proposition_key": "prop-peter-koch-boundary",
            "actor": {"id": "doi:10.1177/1075547015613523#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-peter-koch-2016-result"],
            "lineage_key": "lineage-peter-koch-2016-data",
            "asserted_at": "2015-10-25T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-cameron-2013-result",
            "proposition_key": "prop-cameron-flu-result",
            "actor": {"id": "doi:10.1016/j.pec.2013.06.017#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": [
                "span-cameron-2013-knowledge",
                "span-cameron-2013-no-counterproductive",
            ],
            "lineage_key": "lineage-cameron-2013-data",
            "asserted_at": "2013-09-01T00:00:00Z",
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
            "lineage_key": "lineage-ecker-2020-interpretation",
            "asserted_at": "2020-08-26T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-ecker-short-2020-result",
            "proposition_key": "prop-short-format-result",
            "actor": {"id": "doi:10.1111/bjop.12383#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-ecker-short-2020-result"],
            "lineage_key": "lineage-ecker-short-2020-data",
            "asserted_at": "2019-03-02T00:00:00Z",
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
        {
            "key": "assert-autry-2021-result",
            "proposition_key": "prop-unlicensed-negation-boundary",
            "actor": {"id": "doi:10.1002/acp.3823#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": [
                "span-autry-2021-result",
                "span-autry-2021-qualifier",
                "span-autry-2021-timing-limit",
            ],
            "lineage_key": "lineage-autry-2021-data",
            "asserted_at": "2021-03-31T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-pluviano-2017-result",
            "proposition_key": "prop-vaccine-myths-boundary",
            "actor": {"id": "doi:10.1371/journal.pone.0181640#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-pluviano-2017-result", "span-pluviano-2017-limitation"],
            "lineage_key": "lineage-pluviano-2017-data",
            "asserted_at": "2017-07-27T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-pluviano-2019-result",
            "proposition_key": "prop-vaccine-myths-boundary",
            "actor": {"id": "doi:10.1007/s10339-019-00919-w#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-pluviano-2019-result", "span-pluviano-2019-dependence"],
            "lineage_key": "lineage-pluviano-2019-data",
            "asserted_at": "2019-04-08T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-thomas-2024-result",
            "proposition_key": "prop-unlicensed-negation-boundary",
            "actor": {"id": "doi:10.1002/acp.70004#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-thomas-2024-result", "span-thomas-2024-mechanism"],
            "lineage_key": "lineage-thomas-2024-data",
            "asserted_at": "2024-11-09T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-nibat-2026-result",
            "proposition_key": "prop-brand-correction-result",
            "actor": {"id": "doi:10.1016/j.ijresmar.2026.03.007#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-nibat-2026-scope", "span-nibat-2026-result"],
            "lineage_key": "lineage-nibat-2026-data",
            "asserted_at": "2026-03-27T00:00:00Z",
            "visibility": "public",
        },
        {
            "key": "assert-swire-thompson-2023-result",
            "proposition_key": "prop-reliability-counter-result",
            "actor": {"id": "doi:10.1037/xge0001131#authors", "kind": "collective"},
            "stance": "asserts",
            "span_keys": ["span-swire-thompson-2023-result"],
            "lineage_key": "lineage-swire-thompson-2023-data",
            "asserted_at": "2022-07-01T00:00:00Z",
            "visibility": "public",
        },
    ]

    relations = [
        {
            "key": "relation-skurnik-supports-older-adult-result",
            "relation_type": "support",
            "from_ref": "assert-skurnik-result",
            "to_ref": "prop-older-adult-result",
            "basis_span_keys": ["span-skurnik-summary", "span-ecker-2020-no-baseline"],
            "note": (
                "Preserves the reported delayed older-adult result while separating it from "
                "the dossier's target-comparable general claim."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-skurnik-qualifies-general",
            "relation_type": "qualification",
            "from_ref": "assert-skurnik-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-skurnik-summary", "span-ecker-2020-no-baseline"],
            "note": (
                "Shows a narrower delayed older-adult effect but lacks the baseline required "
                "to establish target-comparable backfire."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-handbook-supports-general",
            "relation_type": "support",
            "from_ref": "assert-handbook-claim",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": [
                "span-handbook-experiment",
                "span-handbook-delay",
                "span-handbook-claim",
                "span-handbook-advice",
            ],
            "note": (
                "A broad public-facing claim and recommendation rooted in the described "
                "30-minute flu-flyer result."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-schwarz-supports-general",
            "relation_type": "support",
            "from_ref": "assert-schwarz-claim",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-schwarz-claim"],
            "note": (
                "A broad review-level mention; its concrete 2005 and flu-flyer examples are "
                "represented separately rather than treated as new data."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-handbook-depends-skurnik-2007",
            "relation_type": "dependence",
            "from_ref": "lineage-handbook-guidance",
            "to_ref": "lineage-skurnik-2007-data",
            "basis_span_keys": [
                "span-handbook-experiment",
                "span-handbook-delay",
                "span-ecker-2020-unpublished-lineage",
            ],
            "note": (
                "Later literature identifies the page’s flu-flyer/30-minute result as the "
                "unpublished 2007 data, not the 2005 paper named in its sole reference."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-handbook-citation-mismatch",
            "relation_type": "undercutting",
            "from_ref": "span-handbook-reference",
            "to_ref": "assert-handbook-claim",
            "basis_span_keys": [
                "span-handbook-experiment",
                "span-handbook-delay",
                "span-handbook-reference",
                "span-ecker-2020-unpublished-lineage",
                "span-ecker-2020-no-baseline",
            ],
            "note": (
                "The visible reference names the 2005 older-adult consumer-claim study, whose "
                "design does not match the page’s flu-flyer/30-minute description."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-schwarz-flu-depends-skurnik-2007",
            "relation_type": "dependence",
            "from_ref": "lineage-schwarz-flu-review",
            "to_ref": "lineage-skurnik-2007-data",
            "basis_span_keys": [
                "span-schwarz-flu-2007-memory",
                "span-schwarz-flu-2007-intentions",
                "span-schwarz-reference-6",
                "span-ecker-2020-unpublished-lineage",
            ],
            "note": (
                "The PDF’s flu-flyer passage cites reference 6, and Ecker et al. identify that "
                "review as the public discussion of the unpublished 2007 data."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-schwarz-flu-supports-boundary",
            "relation_type": "support",
            "from_ref": "assert-schwarz-flu-result",
            "to_ref": "prop-flu-flyer-result",
            "basis_span_keys": [
                "span-schwarz-flu-2007-memory",
                "span-schwarz-flu-2007-intentions",
                "span-schwarz-reference-6",
            ],
            "note": "A review-level report of the unresolved flu-flyer participant data.",
            "visibility": "public",
        },
        {
            "key": "relation-ecker-historical-supports-boundary",
            "relation_type": "support",
            "from_ref": "assert-ecker-2020-historical-report",
            "to_ref": "prop-flu-flyer-result",
            "basis_span_keys": ["span-ecker-2020-unpublished-lineage"],
            "note": (
                "A later historical report identifies the unpublished 2007 manuscript; "
                "it is not credited as newly collected participant data."
            ),
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
            "key": "relation-cameron-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-cameron-2013-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": [
                "span-cameron-2013-knowledge",
                "span-cameron-2013-no-counterproductive",
            ],
            "note": (
                "A randomized flu-message study reported gains across conditions and no "
                "counterproductive facts-and-myths recall result."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-short-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-ecker-short-2020-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-ecker-short-2020-result"],
            "note": "Simple retractions reduced belief without the proposed backfire.",
            "visibility": "public",
        },
        {
            "key": "relation-swire-thompson-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-swire-thompson-2023-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-swire-thompson-2023-result"],
            "note": (
                "Two correction-versus-control experiments found no item-level backfire "
                "relative to either comparison baseline."
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
        {
            "key": "relation-autry-qualifies-general",
            "relation_type": "qualification",
            "from_ref": "assert-autry-2021-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": [
                "span-autry-2021-result",
                "span-autry-2021-qualifier",
                "span-autry-2021-timing-limit",
            ],
            "note": (
                "Preserves an unlicensed-negation boundary while recording that the same "
                "contrast was nonsignificant in Experiment 2 and longer-interval persistence "
                "remains unresolved."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-autry-supports-unlicensed-boundary",
            "relation_type": "support",
            "from_ref": "assert-autry-2021-result",
            "to_ref": "prop-unlicensed-negation-boundary",
            "basis_span_keys": [
                "span-autry-2021-result",
                "span-autry-2021-qualifier",
                "span-autry-2021-timing-limit",
            ],
            "note": "Supports the narrower unlicensed-negation boundary, with qualifiers.",
            "visibility": "public",
        },
        {
            "key": "relation-pluviano-2017-supports-vaccine-boundary",
            "relation_type": "support",
            "from_ref": "assert-pluviano-2017-result",
            "to_ref": "prop-vaccine-myths-boundary",
            "basis_span_keys": [
                "span-pluviano-2017-result",
                "span-pluviano-2017-limitation",
            ],
            "note": (
                "A target-comparable delayed myths-and-facts result in a student sample, "
                "subject to the paper's convenience-sample and generalizability limits."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-pluviano-2019-supports-vaccine-boundary",
            "relation_type": "support",
            "from_ref": "assert-pluviano-2019-result",
            "to_ref": "prop-vaccine-myths-boundary",
            "basis_span_keys": [
                "span-pluviano-2019-result",
                "span-pluviano-2019-dependence",
            ],
            "note": (
                "A target-comparable delayed myths-and-facts result in a parent sample from "
                "the same author and comparison-method program as the 2017 study."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-thomas-qualifies-general",
            "relation_type": "qualification",
            "from_ref": "assert-thomas-2024-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-thomas-2024-result", "span-thomas-2024-mechanism"],
            "note": (
                "Preserves a target-comparable unlicensed-negation result and its proposed "
                "Gricean mechanism without generalizing it to all corrections."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-thomas-supports-unlicensed-boundary",
            "relation_type": "support",
            "from_ref": "assert-thomas-2024-result",
            "to_ref": "prop-unlicensed-negation-boundary",
            "basis_span_keys": ["span-thomas-2024-result", "span-thomas-2024-mechanism"],
            "note": "Supports the narrower unlicensed-negation boundary and proposed mechanism.",
            "visibility": "public",
        },
        {
            "key": "relation-peter-koch-supports-boundary",
            "relation_type": "support",
            "from_ref": "assert-peter-koch-2016-result",
            "to_ref": "prop-peter-koch-boundary",
            "basis_span_keys": ["span-peter-koch-2016-result"],
            "note": (
                "Preserves the reported delayed result without inferring an unobserved "
                "target comparator from the abstract."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-nibat-rebuts-general",
            "relation_type": "rebuttal",
            "from_ref": "assert-nibat-2026-result",
            "to_ref": "prop-general-backfire",
            "basis_span_keys": ["span-nibat-2026-scope", "span-nibat-2026-result"],
            "note": "Five brand-misinformation studies did not observe familiarity backfire.",
            "visibility": "public",
        },
        {
            "key": "relation-ecker-2023-failed-replication-pluviano-2017",
            "relation_type": "failed-replication",
            "from_ref": "assert-ecker-2023-result",
            "to_ref": "assert-pluviano-2017-result",
            "basis_span_keys": ["span-ecker-2023-result", "span-ecker-2023-materials"],
            "note": (
                "The later study reused the 2017 materials but did not reproduce the reported "
                "backfire effect."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-prike-shared-recruitment-frame",
            "relation_type": "dependence",
            "from_ref": "lineage-prike-2023-method",
            "to_ref": "lineage-ecker-2020-method",
            "basis_span_keys": [
                "span-ecker-2020-recruitment",
                "span-ecker-2020-cloudresearch",
                "span-prike-2023-recruitment",
            ],
            "note": (
                "Both papers used US MTurk workers through CloudResearch with the same "
                "5000-HIT and 97% approval thresholds; cross-paper participant overlap is "
                "unreported."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-prike-shared-ethics-series",
            "relation_type": "dependence",
            "from_ref": "lineage-ecker-2023-method",
            "to_ref": "lineage-prike-2023-method",
            "basis_span_keys": ["span-prike-2023-ethics", "span-ecker-2023-ethics"],
            "note": (
                "The papers share authors and UWA ethics approval RA/4/20/6423; they are "
                "separate reported data collections, not independent research programs."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-ecker-2023-reuses-pluviano-materials",
            "relation_type": "dependence",
            "from_ref": "lineage-ecker-2023-method",
            "to_ref": "lineage-pluviano-2017-method",
            "basis_span_keys": ["span-ecker-2023-materials"],
            "note": (
                "The replication directly reused the 2017 stimuli, so material lineage is "
                "shared even though participant data were newly collected."
            ),
            "visibility": "public",
        },
        {
            "key": "relation-pluviano-2019-reuses-comparison-method",
            "relation_type": "dependence",
            "from_ref": "lineage-pluviano-2019-method",
            "to_ref": "lineage-pluviano-2017-method",
            "basis_span_keys": ["span-pluviano-2019-dependence"],
            "note": (
                "The 2019 study chose its seven-day delay to allow direct comparison with "
                "the authors' 2017 study; the participant-data roots remain distinct."
            ),
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
                    "Target-comparable backfire appears in some tested formats and contexts, "
                    "while replications and later studies also report counterevidence. The "
                    "record does not warrant a blanket rule against repeating misinformation "
                    "inside corrections, and the causal mechanism remains unresolved."
                ),
                "reason_codes": [
                    "target-comparable-support-preserved",
                    "counterevidence-preserved",
                    "baseline-mismatch-preserved",
                    "skepticism-boundary-unresolved",
                    "mechanism-attribution-unresolved",
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
                    "the unpublished 2007 data remain unresolved, and both supportive and "
                    "counterevidence papers cluster in overlapping author, material, and "
                    "method programs despite distinct participant-data roots."
                ),
                "reason_codes": [
                    "unpublished-data-lineage-unresolved",
                    "team-and-method-overlap",
                    "measure-specific-qualifier",
                    "population-and-context-limits",
                ],
                "visibility": "public",
            },
        ],
    }
    return stamp_dossier(material)


TARGET_COMPARABLE_SUPPORT_PROPOSITIONS = {
    "prop-flu-flyer-result",
    "prop-unlicensed-negation-boundary",
    "prop-vaccine-myths-boundary",
}


def assertion_keys_for_relation_type(candidate: dict[str, Any], relation_type: str) -> list[str]:
    assertion_keys = {record["key"] for record in candidate["assertions"]}
    return sorted(
        {
            record["from_ref"]
            for record in candidate["evidence_relations"]
            if record["relation_type"] == relation_type and record["from_ref"] in assertion_keys
        }
    )


def derived_counts(candidate: dict[str, Any]) -> dict[str, Any]:
    assertions = {record["key"]: record for record in candidate["assertions"]}
    lineages = {record["key"]: record for record in candidate["lineages"]}
    apparent_support_assertions = assertion_keys_for_relation_type(candidate, "support")
    counter_assertions = assertion_keys_for_relation_type(candidate, "rebuttal")
    review_report_assertions = sorted(
        key
        for key in apparent_support_assertions
        if "data" not in lineages[assertions[key]["lineage_key"]]["dimensions"]
    )
    target_comparable_assertions = sorted(
        key
        for key in apparent_support_assertions
        if assertions[key]["proposition_key"] in TARGET_COMPARABLE_SUPPORT_PROPOSITIONS
    )
    supportive = independence_summary(candidate, apparent_support_assertions)
    target_comparable = independence_summary(candidate, target_comparable_assertions)
    counter = independence_summary(candidate, counter_assertions)
    return {
        "modeled_apparent_support_assertions": len(apparent_support_assertions),
        "apparent_support_assertion_keys": apparent_support_assertions,
        "known_supporting_data_roots": supportive["independent_lineage_count"],
        "unresolved_support_data_roots": supportive["unknown_lineage_count"],
        "support_root_keys": supportive["independent_lineage_roots"],
        "unresolved_support_keys": supportive["unknown_lineages"],
        "target_comparable_supporting_data_roots": target_comparable["independent_lineage_count"],
        "target_comparable_support_root_keys": target_comparable["independent_lineage_roots"],
        "target_comparable_unresolved_data_roots": target_comparable["unknown_lineage_count"],
        "target_comparable_unresolved_keys": target_comparable["unknown_lineages"],
        "modeled_review_report_assertions_without_new_data_credit": len(review_report_assertions),
        "review_report_assertion_keys": review_report_assertions,
        "modeled_counterevidence_assertions": len(counter_assertions),
        "counter_assertion_keys": counter_assertions,
        "modeled_counterevidence_data_roots": counter["independent_lineage_count"],
        "counterevidence_root_keys": counter["independent_lineage_roots"],
        "counting_unit": (
            "One participant-data lineage per publication-defined data series. Multiple "
            "experiments within one publication are collapsed; separate publications with "
            "separately reported samples remain roots unless data reuse is evidenced. Author, "
            "method, material, and research-program overlap remain disclosed separately."
        ),
        "derivation_rule": (
            "Apparent-support and counterevidence assertion keys are the unique assertion "
            "endpoints of modeled support and rebuttal relations. Review/report keys are the "
            "support endpoints whose own lineage has no data dimension; root counts are then "
            "computed by independence_summary."
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
