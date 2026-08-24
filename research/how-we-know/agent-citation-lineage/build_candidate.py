"""Build and verify the EM-0029 reversible Case 002 dossier.

The accepted EM-0026 packet remains the source record. This adapter creates a
quote-minimal application dossier without changing any trace, readback,
normalization, ledger, or review-receipt byte.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from epistemedia.core import canonical_json
from epistemedia.dossier import (
    DOSSIER_FORMAT,
    DossierValidationError,
    independence_summary,
    stamp_dossier,
    validate_dossier,
)

HERE = Path(__file__).resolve().parent
LEDGER_PATH = HERE / "evidence-ledger-v1.json"
NORMALIZATION_PATH = HERE / "source-normalization-v1.json"
SOURCE_READBACKS_PATH = HERE / "source-readbacks-v1.json"
REVIEW_PATH = HERE / "independent-review-receipt.json"
SUPPLEMENT_PATH = HERE / "review-supplement-spans-v1.json"
CANDIDATE_PATH = HERE / "candidate-dossier.json"
RETRIEVED_AT = "2026-08-23T18:33:06Z"
MATCHED = {"exact-normalized-match", "ordered-fragment-match"}
EXPECTED_COUNTS = {
    "captured_reports": 8,
    "citation_occurrences": 48,
    "cited_urls": 30,
    "resolving_url_roots": 27,
    "source_work_roots": 11,
    "examined_edition_roots": 14,
    "raw_span_occurrences": 127,
    "exact_span_roots": 72,
    "raw_claim_occurrences": 52,
    "candidate_warrant_roots": 7,
    "independently_confirmed_warrant_roots": 0,
    "inaccessible_citations": 3,
    "invalid_citations": 0,
    "non_resolving_citations": 0,
    "unresolved_citations": 34,
    "unsupported_or_force_raised_claims": 20,
}
PENDING_WARRANTS = {
    "warrant:citation-verifier-calibration",
    "warrant:researcherbench-faithfulness-groundedness",
    "warrant:liveresearchbench-e1-e2-e3",
    "warrant:url-health-correction-loop",
}
EXPECTED_SUPPLEMENTS = {
    "supplement:deeptrace-gemini-table-50-3": "warrant:deeptrace-support-variation",
    "supplement:deeptrace-gemini-prose-40-3": "warrant:deeptrace-support-variation",
    "supplement:url-health-drbench-precollected-outputs": "warrant:url-health-resolution",
}
CREATORS = {
    "work:citation-verifier-benchmark": [
        "Ethan Leung",
        "Elias Lumer",
        "Corey Feld",
        "Austin Huber",
        "Vamse Kumar Subbiah",
        "Kevin Paul",
    ],
    "work:cited-not-verified": [
        "Hailey Onweller",
        "Elias Lumer",
        "Austin Huber",
        "Pia Ramchandani",
        "Vamse Kumar Subbiah",
        "Corey Feld",
    ],
    "work:deepresearch-bench-paper": [
        "Mingxuan Du",
        "Benfeng Xu",
        "Chiwei Zhu",
        "Licheng Zhang",
        "Xiaorui Wang",
        "Zhendong Mao",
    ],
    "work:deepresearch-bench-repository": ["DeepResearch Bench project"],
    "work:deeptrace": [
        "Pranav Narayanan Venkit",
        "Philippe Laban",
        "Yilun Zhou",
        "Kung-Hsiang Huang",
        "Yixin Mao",
        "Chien-Sheng Wu",
    ],
    "work:keplinger-dermatology-audit": [
        "Lauren E. Keplinger",
        "Luke K. Frashure",
        "Sabrina A. Duran",
        "Gangqing Hu",
    ],
    "work:keplinger-supplement": ["Gangqing Hu", "West Virginia University"],
    "work:liveresearchbench": [
        "Jiayu Wang",
        "Yifei Ming",
        "Riya Dulepet",
        "Qinglin Chen",
        "Austin Xu",
        "Zixuan Ke",
        "Frederic Sala",
        "Aws Albarghouthi",
        "Caiming Xiong",
        "Shafiq Joty",
    ],
    "work:reportbench": [
        "Minghao Li",
        "Ying Zeng",
        "Zhihao Cheng",
        "Cong Ma",
        "Kai Jia",
    ],
    "work:researcherbench": ["ResearcherBench authors", "SII-GAIR"],
    "work:url-health": ["Delip Rao", "Eric Wong", "Chris Callison-Burch"],
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain an object")
    return value


def load_review_supplements(
    ledger: dict[str, Any], source_readbacks: dict[str, Any]
) -> dict[str, Any]:
    packet = load(SUPPLEMENT_PATH)
    if packet.get("format") != "epistemedia-em0029-review-supplement-spans-v1":
        raise SystemExit("unsupported EM-0029 review-supplement format")
    records = packet.get("records")
    if not isinstance(records, list) or len(records) != 3:
        raise SystemExit("EM-0029 review supplement must contain exactly three spans")
    if packet.get("supplement_span_count") != len(records):
        raise SystemExit("EM-0029 review-supplement count drift")
    if packet.get("accepted_em0026_exact_span_roots") != EXPECTED_COUNTS[
        "exact_span_roots"
    ]:
        raise SystemExit("EM-0029 supplement changed the accepted EM-0026 span-root count")

    editions = {item["edition_id"]: item for item in ledger["editions"]}
    works = {item["work_id"]: item for item in ledger["works"]}
    readbacks = source_readbacks.get("records")
    if not isinstance(readbacks, list):
        raise SystemExit("accepted source-readback packet lacks records")
    identities = {}
    for record in records:
        supplement_id = record.get("supplement_id")
        warrant_id = record.get("warrant_id")
        if EXPECTED_SUPPLEMENTS.get(supplement_id) != warrant_id:
            raise SystemExit(f"unexpected EM-0029 supplement identity: {supplement_id}")
        if supplement_id in identities:
            raise SystemExit(f"duplicate EM-0029 supplement identity: {supplement_id}")
        identities[supplement_id] = warrant_id
        edition_record = editions.get(record.get("edition_id"))
        if edition_record is None:
            raise SystemExit(f"supplement edition is unknown: {supplement_id}")
        if edition_record["work_id"] != record.get("work_id"):
            raise SystemExit(f"supplement work/edition binding drift: {supplement_id}")
        if record["work_id"] not in works:
            raise SystemExit(f"supplement work is unknown: {supplement_id}")
        if edition_record["canonical_url"] != record.get("canonical_url"):
            raise SystemExit(f"supplement canonical URL drift: {supplement_id}")
        if edition_record["license_treatment"] != record.get("license_treatment"):
            raise SystemExit(f"supplement license treatment drift: {supplement_id}")
        carrier = record.get("carrier")
        if not isinstance(carrier, dict):
            raise SystemExit(f"supplement carrier is missing: {supplement_id}")
        matches = [
            item
            for item in readbacks
            if item.get("edition_id") == record["edition_id"]
            and item.get("requested_url") == record["canonical_url"]
            and item.get("captured_bytes") == carrier.get("bytes")
            and item.get("captured_sha256") == carrier.get("sha256")
            and item.get("media_type") == carrier.get("media_type")
            and item.get("retrieval_status") == "retrieved"
        ]
        if len(matches) != 1:
            raise SystemExit(f"supplement carrier differs from accepted readback: {supplement_id}")
        if not isinstance(record.get("locator"), str) or not record["locator"]:
            raise SystemExit(f"supplement locator is missing: {supplement_id}")
        if not isinstance(record.get("extent"), (str, dict)):
            raise SystemExit(f"supplement extent is invalid: {supplement_id}")
    if identities != EXPECTED_SUPPLEMENTS:
        raise SystemExit("EM-0029 review-supplement identity set drift")
    return packet


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def content_bytes(value: Any) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return canonical_json(value).encode("utf-8")


def key(prefix: str, identity: str) -> str:
    tail = identity.split(":")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", tail.lower()).strip("-")
    short = hashlib.sha256(identity.encode()).hexdigest()[:10]
    return f"{prefix}-{slug[:48]}-{short}"


def edition(
    edition_key: str,
    work_key: str,
    label: str,
    content: dict[str, Any],
) -> dict[str, Any]:
    encoded = content_bytes(content)
    return {
        "key": edition_key,
        "work_key": work_key,
        "edition_label": label,
        "media_type": "application/json",
        "retrieved_at": RETRIEVED_AT,
        "content": content,
        "content_digest": digest_bytes(encoded),
        "content_length": len(encoded),
        "visibility": "public",
    }


def structured_span(
    span_key: str,
    edition_key: str,
    pointer: str,
    label: str,
    value: Any,
) -> dict[str, Any]:
    return {
        "key": span_key,
        "edition_key": edition_key,
        "locator": {"type": "json-pointer", "pointer": pointer, "label": label},
        "extent": {"type": "json-value", "value": value},
        "digest": digest_bytes(content_bytes(value)),
        "visibility": "public",
    }


def _unsupported_occurrences(normalization: dict[str, Any]) -> list[str]:
    result_occurrences = {
        occurrence
        for group in normalization["claim_groups"]
        for occurrence in group["result_occurrences"]
    }
    kinds = {"scope", "internal-source-conflict", "dependence", "edition", "semantic-warrant"}
    return sorted(
        {
            occurrence
            for correction in normalization["corrections"]
            if correction["kind"] in kinds
            for occurrence in correction["raw_occurrences"]
            if occurrence in result_occurrences or occurrence.endswith(":answer")
        }
    )


def audit_content(
    ledger: dict[str, Any],
    normalization: dict[str, Any],
    review: dict[str, Any],
    supplements: dict[str, Any],
) -> dict[str, Any]:
    matched_roots = sorted(
        {
            item["span_root_id"]
            for item in ledger["spans"]
            if item["match_status"] in MATCHED
        }
    )
    unresolved = [
        item for item in ledger["citations"] if item["resolution_status"] == "unresolved"
    ]
    inaccessible = [
        item
        for item in ledger["citations"]
        if item["readback"]["retrieval_status"] == "inaccessible"
    ]
    candidate_ids = sorted(item["warrant_id"] for item in ledger["candidate_warrants"])
    rejected_ids = sorted(review["semantic_disposition"]["no_credit_claim_occurrence_ids"])
    content = {
        "format": "epistemedia-case-002-audit-projection-v0.1",
        "accepted_ledger_path": LEDGER_PATH.relative_to(HERE.parent.parent.parent).as_posix(),
        "accepted_ledger_sha256": hashlib.sha256(LEDGER_PATH.read_bytes()).hexdigest(),
        "accepted_review_path": REVIEW_PATH.relative_to(HERE.parent.parent.parent).as_posix(),
        "accepted_review_sha256": hashlib.sha256(REVIEW_PATH.read_bytes()).hexdigest(),
        "accepted_source_readbacks_path": SOURCE_READBACKS_PATH.relative_to(
            HERE.parent.parent.parent
        ).as_posix(),
        "accepted_source_readbacks_sha256": hashlib.sha256(
            SOURCE_READBACKS_PATH.read_bytes()
        ).hexdigest(),
        "review_supplement_path": SUPPLEMENT_PATH.relative_to(
            HERE.parent.parent.parent
        ).as_posix(),
        "review_supplement_sha256": hashlib.sha256(SUPPLEMENT_PATH.read_bytes()).hexdigest(),
        "count_grammar": ledger["count_grammar"],
        "reports": ledger["reports"],
        "citation_occurrence_ids": sorted(
            item["citation_occurrence_id"] for item in ledger["citations"]
        ),
        "cited_urls": sorted({item["requested_url"] for item in ledger["citations"]}),
        "resolving_url_roots": sorted(
            {
                item["requested_url"]
                for item in ledger["citations"]
                if item["readback"]["retrieval_status"] == "retrieved"
            }
        ),
        "source_work_ids": sorted(item["work_id"] for item in ledger["works"]),
        "examined_edition_ids": sorted(item["edition_id"] for item in ledger["editions"]),
        "raw_span_occurrence_ids": sorted(
            item["span_occurrence_id"] for item in ledger["spans"]
        ),
        "matched_span_root_ids": matched_roots,
        "raw_claim_occurrence_ids": sorted(
            item["claim_occurrence_id"] for item in ledger["claims"]
        ),
        "candidate_warrants": ledger["candidate_warrants"],
        "independently_confirmed_warrant_ids": [],
        "pending_warrant_ids": sorted(PENDING_WARRANTS),
        "rejected_claim_occurrence_ids": rejected_ids,
        "unsupported_or_force_raised_occurrence_ids": _unsupported_occurrences(normalization),
        "unresolved_citations": unresolved,
        "inaccessible_citations": inaccessible,
        "corrections": normalization["corrections"],
        "dependence_edges": ledger["dependence_edges"],
        "shared_capture_lineage": {
            "prompt_sha256": ledger["reports"][0]["prompt_sha256"],
            "requested_profiles": sorted(
                {item["requested_model_profile"] for item in ledger["reports"]}
            ),
            "reported_model_identity": "unknown",
            "retrieval_infrastructure": "unknown",
            "automatic_independence_credit": 0,
        },
        "source_dependence_boundary": {
            "dimensions": [
                "data",
                "method",
                "retrieval",
                "source_work",
                "edition",
                "exact_span",
                "derivation",
                "upstream_citation",
            ],
            "automatic_independence_credit": 0,
            "note": (
                "Candidate warrant roots remain connected by declared or unresolved task, "
                "retrieval, judge-method, source, edition, span, and derivation lineage."
            ),
        },
        "limitations": ledger["limitations"],
    }
    lengths = {
        "captured_reports": len(content["reports"]),
        "citation_occurrences": len(content["citation_occurrence_ids"]),
        "cited_urls": len(content["cited_urls"]),
        "resolving_url_roots": len(content["resolving_url_roots"]),
        "source_work_roots": len(content["source_work_ids"]),
        "examined_edition_roots": len(content["examined_edition_ids"]),
        "raw_span_occurrences": len(content["raw_span_occurrence_ids"]),
        "exact_span_roots": len(content["matched_span_root_ids"]),
        "raw_claim_occurrences": len(content["raw_claim_occurrence_ids"]),
        "candidate_warrant_roots": len(content["candidate_warrants"]),
        "independently_confirmed_warrant_roots": len(
            content["independently_confirmed_warrant_ids"]
        ),
        "inaccessible_citations": len(content["inaccessible_citations"]),
        "invalid_citations": 0,
        "non_resolving_citations": 0,
        "unresolved_citations": len(content["unresolved_citations"]),
        "unsupported_or_force_raised_claims": len(
            content["unsupported_or_force_raised_occurrence_ids"]
        ),
    }
    if lengths != EXPECTED_COUNTS or lengths != ledger["counts"]:
        raise SystemExit(f"Case 002 count drift: {lengths}")
    if set(candidate_ids) & PENDING_WARRANTS:
        raise SystemExit("candidate and pending warrant sets overlap")
    if set(rejected_ids) != set(
        review["semantic_disposition"]["no_credit_claim_occurrence_ids"]
    ):
        raise SystemExit("rejected claim binding drift")
    content["derived_counts"] = lengths
    content["disposition_counts"] = {
        "pending_warrant_roots": len(content["pending_warrant_ids"]),
        "independently_rejected_claim_occurrences": len(
            content["rejected_claim_occurrence_ids"]
        ),
        "em0029_review_supplement_spans": len(supplements["records"]),
    }
    return content


def build() -> dict[str, Any]:
    ledger = load(LEDGER_PATH)
    normalization = load(NORMALIZATION_PATH)
    source_readbacks = load(SOURCE_READBACKS_PATH)
    review = load(REVIEW_PATH)
    supplements = load_review_supplements(ledger, source_readbacks)
    if review["decision"] != "pass":
        raise SystemExit("accepted EM-0026 independent review is not a pass")
    if review["reproduced_counts"] != EXPECTED_COUNTS:
        raise SystemExit("reviewed EM-0026 count identity drift")
    if review["identity_checks"]["source_and_span_readbacks"]["result"] != "byte-identical":
        raise SystemExit("accepted EM-0026 readback identity is not preserved")

    works_by_id = {item["work_id"]: item for item in ledger["works"]}
    editions_by_id = {item["edition_id"]: item for item in ledger["editions"]}
    work_keys = {identity: key("work", identity) for identity in works_by_id}
    edition_keys = {identity: key("edition", identity) for identity in editions_by_id}
    spans_by_edition: dict[str, list[dict[str, Any]]] = {
        identity: [] for identity in editions_by_id
    }
    root_record: dict[str, dict[str, Any]] = {}
    occurrences_by_root: dict[str, list[str]] = {}
    for item in ledger["spans"]:
        if item["match_status"] not in MATCHED:
            continue
        root = item["span_root_id"]
        previous = root_record.get(root)
        if previous is not None and (
            previous["edition_id"], previous["locator"], previous["quote"]
        ) != (item["edition_id"], item["locator"], item["quote"]):
            raise SystemExit(f"span-root content drift: {root}")
        root_record.setdefault(root, item)
        occurrences_by_root.setdefault(root, []).append(item["span_occurrence_id"])
    for root, item in sorted(root_record.items()):
        spans_by_edition[item["edition_id"]].append(
            {
                "span_root_id": root,
                "locator": item["locator"],
                "text": item["quote"],
                "match_status": item["match_status"],
                "source_text_sha256": item["source_text_sha256"],
                "license_treatment": item["license_treatment"],
                "occurrence_ids": sorted(occurrences_by_root[root]),
            }
        )

    source_works = []
    for identity, item in sorted(works_by_id.items()):
        work_editions = [value for value in ledger["editions"] if value["work_id"] == identity]
        licenses = sorted({value["license"] for value in work_editions})
        uri = sorted(value["canonical_url"] for value in work_editions)[0]
        kind = "dataset" if identity.endswith("supplement") else "paper"
        if identity.endswith("repository"):
            kind = "webpage"
        source_works.append(
            {
                "key": work_keys[identity],
                "kind": kind,
                "title": item["title"],
                "creators": CREATORS[identity],
                "canonical_uri": uri,
                "license": "; ".join(licenses),
                "visibility": "public",
            }
        )
    audit_work_key = "work-em0026-audit-instrument"
    source_works.append(
        {
            "key": audit_work_key,
            "kind": "instrument",
            "title": "EM-0026 deterministic agent-citation evidence ledger",
            "creators": ["Epistemedia EM-0026 research process"],
            "canonical_uri": "https://github.com/yoheinakajima/epistemedia/tree/main/"
            "research/how-we-know/agent-citation-lineage",
            "license": "Repository metadata and derived audit relations under Apache-2.0; "
            "embedded source excerpts retain their recorded treatments",
            "visibility": "public",
        }
    )

    editions = []
    spans = []
    span_keys_by_occurrence: dict[str, str] = {}
    supplement_span_keys_by_warrant: dict[str, list[str]] = {}
    for identity, item in sorted(editions_by_id.items()):
        excerpts = sorted(spans_by_edition[identity], key=lambda value: value["span_root_id"])
        review_supplements = sorted(
            [record for record in supplements["records"] if record["edition_id"] == identity],
            key=lambda value: value["supplement_id"],
        )
        receipts = []
        seen_receipts = set()
        for citation in ledger["citations"]:
            if citation["edition_id"] != identity:
                continue
            readback = citation["readback"]
            signature = canonical_json(readback)
            if signature not in seen_receipts:
                seen_receipts.add(signature)
                receipts.append(readback)
        content = {
            "format": "epistemedia-quote-minimal-edition-projection-v0.1",
            "canonical_url": item["canonical_url"],
            "source_text_file": item["source_text_file"],
            "license": item["license"],
            "license_treatment": item["license_treatment"],
            "readback_receipts": sorted(receipts, key=canonical_json),
            "excerpts": excerpts,
            "review_supplements": review_supplements,
        }
        editions.append(
            edition(
                edition_keys[identity],
                work_keys[item["work_id"]],
                f"Quote-minimal projection of {identity}",
                content,
            )
        )
        for index, excerpt in enumerate(excerpts):
            span_key = key("span", excerpt["span_root_id"])
            spans.append(
                structured_span(
                    span_key,
                    edition_keys[identity],
                    f"/excerpts/{index}/text",
                    excerpt["locator"],
                    excerpt["text"],
                )
            )
            for occurrence in excerpt["occurrence_ids"]:
                span_keys_by_occurrence[occurrence] = span_key
        for index, supplement in enumerate(review_supplements):
            span_key = key("span-supplement", supplement["supplement_id"])
            spans.append(
                structured_span(
                    span_key,
                    edition_keys[identity],
                    f"/review_supplements/{index}/extent",
                    supplement["locator"],
                    supplement["extent"],
                )
            )
            supplement_span_keys_by_warrant.setdefault(
                supplement["warrant_id"], []
            ).append(span_key)

    audit = audit_content(ledger, normalization, review, supplements)
    audit_edition_key = "edition-em0026-audit-projection"
    editions.append(
        edition(
            audit_edition_key,
            audit_work_key,
            "Deterministic projection of accepted EM-0026 relations",
            audit,
        )
    )
    audit_spans: dict[str, str] = {}

    def add_audit_span(name: str, pointer: str, label: str, value: Any) -> str:
        span_key = f"span-audit-{name}"
        spans.append(structured_span(span_key, audit_edition_key, pointer, label, value))
        audit_spans[name] = span_key
        return span_key

    for index, report in enumerate(audit["reports"]):
        add_audit_span(
            f"report-{index + 1}",
            f"/reports/{index}",
            f"Captured report {report['run_id']}",
            report,
        )
    for index, warrant in enumerate(audit["candidate_warrants"]):
        add_audit_span(
            f"candidate-{index + 1}",
            f"/candidate_warrants/{index}",
            f"Candidate warrant {warrant['warrant_id']}",
            warrant,
        )
    for index, warrant_id in enumerate(audit["pending_warrant_ids"]):
        add_audit_span(
            f"pending-{index + 1}",
            f"/pending_warrant_ids/{index}",
            f"Pending warrant {warrant_id}",
            warrant_id,
        )
    add_audit_span(
        "counts",
        "/derived_counts",
        "Relation-derived packet counts",
        audit["derived_counts"],
    )
    add_audit_span(
        "dispositions",
        "/disposition_counts",
        "Relation-derived review disposition counts",
        audit["disposition_counts"],
    )
    add_audit_span(
        "unresolved",
        "/unresolved_citations",
        "All unresolved citation occurrences",
        audit["unresolved_citations"],
    )
    add_audit_span(
        "inaccessible",
        "/inaccessible_citations",
        "All inaccessible citation carriers",
        audit["inaccessible_citations"],
    )
    add_audit_span(
        "unsupported",
        "/unsupported_or_force_raised_occurrence_ids",
        "Unsupported or force-raised claim occurrences",
        audit["unsupported_or_force_raised_occurrence_ids"],
    )
    add_audit_span(
        "rejected",
        "/rejected_claim_occurrence_ids",
        "Independently rejected claim occurrences",
        audit["rejected_claim_occurrence_ids"],
    )
    add_audit_span(
        "capture-lineage",
        "/shared_capture_lineage",
        "Shared capture lineage",
        audit["shared_capture_lineage"],
    )
    add_audit_span(
        "source-boundary",
        "/source_dependence_boundary",
        "Source and derivation dependence boundary",
        audit["source_dependence_boundary"],
    )

    groups = normalization["claim_groups"]
    groups_by_id = {item["warrant_id"]: item for item in groups}
    candidate_ids = [item["warrant_id"] for item in ledger["candidate_warrants"]]
    target_key = "prop-agreement-not-independent-warrant"
    report_prop_key = "prop-report-citation-observation"
    unresolved_prop_key = "prop-unresolved-citations-no-credit"
    inaccessible_prop_key = "prop-inaccessible-carriers-no-credit"
    unsupported_prop_key = "prop-unsupported-claims-no-credit"
    rejected_prop_key = "prop-independently-rejected-claims-no-credit"
    counts_prop_key = "prop-relation-derived-counts"
    propositions = [
        {
            "key": target_key,
            "text": (
                "Separate agent reports do not by themselves supply independent evidentiary "
                "warrant when their prompt, runtime, retrieval, source, method, or derivation "
                "lineages overlap or remain unknown."
            ),
            "scope": "The eight public-by-design EM-0026 captures and evidence through 2026-08-22.",
            "visibility": "public",
        },
        {
            "key": report_prop_key,
            "text": "One frozen EM-0026 run produced a terminal citation-bearing report.",
            "scope": "One captured run artifact; no claim of independence or generality.",
            "visibility": "public",
        },
        {
            "key": unresolved_prop_key,
            "text": (
                "Citation occurrences with inaccessible carriers, unmatched spans, or unresolved "
                "identity or warrant corrections receive no evidentiary credit."
            ),
            "scope": "The accepted EM-0026 citation-occurrence ledger.",
            "visibility": "public",
        },
        {
            "key": unsupported_prop_key,
            "text": (
                "Agent claim occurrences strengthened beyond their linked source semantics remain "
                "visible and receive no warrant credit for the stronger wording."
            ),
            "scope": "The accepted EM-0026 correction and semantic-review records.",
            "visibility": "public",
        },
        {
            "key": inaccessible_prop_key,
            "text": (
                "Three cited carriers were inaccessible during accepted independent readback and "
                "receive no carrier-level credit even where another edition of the work exists."
            ),
            "scope": "The accepted EM-0026 citation-occurrence ledger.",
            "visibility": "public",
        },
        {
            "key": rejected_prop_key,
            "text": (
                "Nine claim occurrences were independently rejected because their captured spans "
                "did not entail the complete asserted proposition."
            ),
            "scope": "The accepted EM-0026 independent semantic review.",
            "visibility": "public",
        },
        {
            "key": counts_prop_key,
            "text": (
                "The accepted packet contains 8 reports, 48 citation occurrences, 30 cited URLs, "
                "27 resolving URL roots, 11 source works, 14 examined editions, 72 matched exact-"
                "span roots, 7 candidate warrant roots, 34 unresolved citations, and 20 "
                "unsupported or force-raised claim occurrences."
            ),
            "scope": "Counts derived from the accepted EM-0026 relation ledger.",
            "visibility": "public",
        },
    ]
    prop_by_warrant = {}
    for group in groups:
        prop_key = key("prop", group["warrant_id"])
        prop_by_warrant[group["warrant_id"]] = prop_key
        propositions.append(
            {
                "key": prop_key,
                "text": group["canonical_proposition"],
                "scope": (
                    f"Review status: {group['review_status']}; data root {group['data_root']}; "
                    f"method root {group['method_root']}; derivation root "
                    f"{group['derivation_root']}."
                ),
                "visibility": "public",
            }
        )

    assertions = []
    lineages = [
        {
            "key": "lineage-capture-dependence-unknown",
            "status": "unknown",
            "dimensions": ["model", "retrieval", "prompt", "other"],
            "depends_on": [],
            "basis_span_keys": [audit_spans["capture-lineage"]],
            "assertion_keys": [],
            "note": (
                "Unknown provider and retrieval dependencies remain; all reports share the exact "
                "prompt and one bounded capture program, so run multiplicity gets zero automatic "
                "independence credit."
            ),
            "visibility": "public",
        },
        {
            "key": "lineage-source-dependence-unknown",
            "status": "unknown",
            "dimensions": ["source", "data", "method", "retrieval", "other"],
            "depends_on": [],
            "basis_span_keys": [audit_spans["source-boundary"]],
            "assertion_keys": [],
            "note": (
                "Unknown residual independence remains across task data, judge methods, retrieval, "
                "source, edition, span, derivation, and upstream-citation lineages."
            ),
            "visibility": "public",
        },
    ]
    relations = []
    for index, report in enumerate(audit["reports"]):
        assertion_key = key("assertion", f"report:{report['run_id']}")
        lineage_key = key("lineage", f"report:{report['run_id']}")
        span_key = audit_spans[f"report-{index + 1}"]
        assertions.append(
            {
                "key": assertion_key,
                "proposition_key": report_prop_key,
                "actor": {"id": report["run_id"], "kind": "agent"},
                "stance": "asserts",
                "span_keys": [span_key],
                "lineage_key": lineage_key,
                "asserted_at": RETRIEVED_AT,
                "visibility": "public",
            }
        )
        lineages.append(
            {
                "key": lineage_key,
                "status": "known",
                "dimensions": ["model", "retrieval", "prompt"],
                "depends_on": ["lineage-capture-dependence-unknown"],
                "basis_span_keys": [span_key, audit_spans["capture-lineage"]],
                "assertion_keys": [assertion_key],
                "note": (
                    f"{report['run_id']} shares the frozen prompt and capture program; requested "
                    "profile does not establish an independent observer."
                ),
                "visibility": "public",
            }
        )
        relations.append(
            {
                "key": key("relation", f"report-dependence:{report['run_id']}"),
                "relation_type": "dependence",
                "from_ref": lineage_key,
                "to_ref": "lineage-capture-dependence-unknown",
                "basis_span_keys": [span_key, audit_spans["capture-lineage"]],
                "note": "This report is a captured observation, not an independent evidence root.",
                "visibility": "public",
            }
        )

    claims_by_id = {item["claim_occurrence_id"]: item for item in ledger["claims"]}
    for warrant_id in candidate_ids:
        group = groups_by_id[warrant_id]
        assertion_key = key("assertion", warrant_id)
        lineage_key = key("lineage", warrant_id)
        source_span_keys = sorted(
            {
                span_keys_by_occurrence[span_id]
                for occurrence in group["result_occurrences"]
                for span_id in claims_by_id[occurrence]["span_occurrence_ids"]
                if span_id in span_keys_by_occurrence
            }
            | set(supplement_span_keys_by_warrant.get(warrant_id, []))
        )
        if not source_span_keys:
            raise SystemExit(f"candidate warrant has no matched exact span: {warrant_id}")
        assertions.append(
            {
                "key": assertion_key,
                "proposition_key": prop_by_warrant[warrant_id],
                "actor": {"id": "+".join(group["work_ids"]), "kind": "collective"},
                "stance": "asserts",
                "span_keys": source_span_keys,
                "lineage_key": lineage_key,
                "asserted_at": RETRIEVED_AT,
                "visibility": "public",
            }
        )
        lineages.append(
            {
                "key": lineage_key,
                "status": "known",
                "dimensions": ["source", "data", "method", "retrieval", "other"],
                "depends_on": ["lineage-source-dependence-unknown"],
                "basis_span_keys": source_span_keys + [audit_spans["source-boundary"]],
                "assertion_keys": [assertion_key],
                "note": (
                    f"Candidate only: {group['data_root']}; {group['method_root']}; "
                    f"{group['derivation_root']}. Residual independence is unknown."
                ),
                "visibility": "public",
            }
        )
        relations.append(
            {
                "key": key("relation", f"candidate-support:{warrant_id}"),
                "relation_type": "support",
                "from_ref": assertion_key,
                "to_ref": prop_by_warrant[warrant_id],
                "basis_span_keys": source_span_keys,
                "note": group["canonical_proposition"],
                "visibility": "public",
            }
        )
        relations.append(
            {
                "key": key("relation", f"candidate-dependence:{warrant_id}"),
                "relation_type": "dependence",
                "from_ref": lineage_key,
                "to_ref": "lineage-source-dependence-unknown",
                "basis_span_keys": [audit_spans["source-boundary"]],
                "note": "Candidate warrant count is not an independent-program count.",
                "visibility": "public",
            }
        )

    for pending_index, warrant_id in enumerate(sorted(PENDING_WARRANTS)):
        group = groups_by_id[warrant_id]
        assertion_key = key("assertion", f"pending:{warrant_id}")
        lineage_key = key("lineage", f"pending:{warrant_id}")
        span_key = audit_spans[f"pending-{pending_index + 1}"]
        assertions.append(
            {
                "key": assertion_key,
                "proposition_key": prop_by_warrant[warrant_id],
                "actor": {"id": "EM-0026 independent semantic review", "kind": "service"},
                "stance": "questions",
                "span_keys": [span_key],
                "lineage_key": lineage_key,
                "asserted_at": RETRIEVED_AT,
                "visibility": "public",
            }
        )
        lineages.append(
            {
                "key": lineage_key,
                "status": "unknown",
                "dimensions": ["source", "method", "other"],
                "depends_on": [],
                "basis_span_keys": [span_key],
                "assertion_keys": [assertion_key],
                "note": f"Unknown warrant closure: {group['review_status']}.",
                "visibility": "public",
            }
        )
        relations.append(
            {
                "key": key("relation", f"pending:{warrant_id}"),
                "relation_type": "qualification",
                "from_ref": assertion_key,
                "to_ref": prop_by_warrant[warrant_id],
                "basis_span_keys": [span_key],
                "note": (
                    "The captured spans do not semantically close the normalized proposition; "
                    "the warrant remains pending and receives no credit."
                ),
                "visibility": "public",
            }
        )

    audit_assertions = [
        (
            "assertion-derived-counts",
            counts_prop_key,
            audit_spans["counts"],
            "Each displayed total is derived from typed packet records under the stored grammar.",
            "support",
            counts_prop_key,
        ),
        (
            "assertion-unresolved-citations",
            unresolved_prop_key,
            audit_spans["unresolved"],
            "The complete unresolved set remains visible and receives no warrant credit.",
            "undercutting",
            target_key,
        ),
        (
            "assertion-inaccessible-carriers",
            inaccessible_prop_key,
            audit_spans["inaccessible"],
            "The three inaccessible carrier occurrences remain visible and receive no credit.",
            "undercutting",
            target_key,
        ),
        (
            "assertion-unsupported-claims",
            unsupported_prop_key,
            audit_spans["unsupported"],
            "The complete unsupported or force-raised set remains visible and receives no credit.",
            "undercutting",
            target_key,
        ),
        (
            "assertion-independently-rejected-claims",
            rejected_prop_key,
            audit_spans["rejected"],
            "All nine independently rejected claims remain visible and receive no credit.",
            "undercutting",
            target_key,
        ),
    ]
    for assertion_key, proposition_key, span_key, note, relation_type, relation_target in (
        audit_assertions
    ):
        assertions.append(
            {
                "key": assertion_key,
                "proposition_key": proposition_key,
                "actor": {"id": "EM-0026 deterministic audit", "kind": "instrument"},
                "stance": "asserts",
                "span_keys": [span_key],
                "lineage_key": "lineage-em0026-audit",
                "asserted_at": RETRIEVED_AT,
                "visibility": "public",
            }
        )
        relations.append(
            {
                "key": key("relation", assertion_key),
                "relation_type": relation_type,
                "from_ref": assertion_key,
                "to_ref": relation_target,
                "basis_span_keys": [span_key],
                "note": note,
                "visibility": "public",
            }
        )
    lineages.append(
        {
            "key": "lineage-em0026-audit",
            "status": "known",
            "dimensions": ["apparatus", "other"],
            "depends_on": [],
            "basis_span_keys": [item[2] for item in audit_assertions],
            "assertion_keys": [item[0] for item in audit_assertions],
            "note": "Deterministic relation audit over the accepted EM-0026 packet.",
            "visibility": "public",
        }
    )

    report_assertion_keys = [
        key("assertion", f"report:{report['run_id']}") for report in audit["reports"]
    ]
    report_independence = independence_summary(
        stamp_dossier(
            {
                "format": DOSSIER_FORMAT,
                "title": "Temporary Case 002 lineage check",
                "question": "Do eight reports create eight independent evidence roots?",
                "scope": "Construction-time lineage assertion.",
                "stage": "fixture",
                "visibility": "public",
                "source_works": source_works,
                "editions": editions,
                "spans": spans,
                "propositions": propositions,
                "lineages": lineages,
                "assertions": assertions,
                "evidence_relations": relations,
                "claim_families": [
                    {
                        "key": "family-agent-citation-lineage",
                        "title": "Agent citation lineage",
                        "question": "Do repeated agent reports create independent warrant?",
                        "proposition_keys": [item["key"] for item in propositions],
                        "assertion_keys": [item["key"] for item in assertions],
                        "relation_keys": [item["key"] for item in relations],
                        "visibility": "public",
                    }
                ],
                "evaluations": [
                    {
                        "key": "evaluation-construction",
                        "claim_family_key": "family-agent-citation-lineage",
                        "policy_id": "em:application-policy:construction-v0.1",
                        "frontier": "research-candidate-em-0029",
                        "label": "Construction-only lineage check.",
                        "reason_codes": ["construction-only"],
                        "visibility": "public",
                    }
                ],
            }
        ),
        report_assertion_keys,
    )
    if report_independence["independent_lineage_count"] != 0:
        raise SystemExit("report multiplicity received automatic independence credit")
    if report_independence["unknown_lineage_count"] != 1:
        raise SystemExit("shared unknown capture lineage was not collapsed")

    family_key = "family-agent-citation-lineage"
    material = {
        "format": DOSSIER_FORMAT,
        "title": "When eight research agents agree, how many evidence roots are there?",
        "question": (
            "What empirical evidence published or publicly posted by 2026-08-22 measures "
            "whether citations produced by deep-research agents resolve and actually support "
            "the claims made from them?"
        ),
        "scope": (
            "Eight context-isolated public-by-design reports captured under one frozen prompt, "
            "plus the public source editions and exact spans they cited. This historical pilot "
            "does not estimate current or universal agent behavior."
        ),
        "stage": "draft",
        "visibility": "public",
        "source_works": source_works,
        "editions": editions,
        "spans": spans,
        "propositions": propositions,
        "lineages": lineages,
        "assertions": assertions,
        "evidence_relations": relations,
        "claim_families": [
            {
                "key": family_key,
                "title": "Report, citation, source, span, and warrant lineage",
                "question": (
                    "When multiple research-agent reports cite overlapping material, what does "
                    "their agreement add beyond the inspected source and warrant lineages?"
                ),
                "proposition_keys": [item["key"] for item in propositions],
                "assertion_keys": [item["key"] for item in assertions],
                "relation_keys": [item["key"] for item in relations],
                "visibility": "public",
            }
        ],
        "evaluations": [
            {
                "key": "evaluation-encyclopedia",
                "claim_family_key": family_key,
                "policy_id": "em:application-policy:encyclopedia-v0.1",
                "frontier": "research-candidate-em-0029",
                "label": (
                    "The bounded record contains empirical methods for URL resolution and "
                    "claim-to-source support, but the eight reports reuse overlapping capture, "
                    "source, method, and derivation lineages. Report agreement alone adds no "
                    "independent warrant beyond the inspected source record."
                ),
                "reason_codes": [
                    "citation-resolution-separated-from-support",
                    "shared-capture-lineage",
                    "candidate-warrants-scope-bounded",
                    "unresolved-citations-preserved",
                ],
                "visibility": "public",
            },
            {
                "key": "evaluation-skeptical",
                "claim_family_key": family_key,
                "policy_id": "em:application-policy:skeptical-v0.1",
                "frontier": "research-candidate-em-0029",
                "label": (
                    "This pilot cannot estimate current agent citation reliability: thirty-four "
                    "citation occurrences remain unresolved, twenty claims required correction "
                    "or no credit, four warrant groups remain pending, and zero warrant roots are "
                    "independently confirmed by the packet. Inspect the exact source span before "
                    "relying on a polished cited answer."
                ),
                "reason_codes": [
                    "no-representative-agent-sample",
                    "unresolved-citation-set-material",
                    "semantic-strengthening-no-credit",
                    "warrant-independence-unconfirmed",
                ],
                "visibility": "public",
            },
        ],
    }
    dossier = stamp_dossier(material)
    validate_dossier(dossier)
    return dossier


def verify_adversarial(dossier: dict[str, Any]) -> None:
    mutated = copy.deepcopy(dossier)
    mutated["spans"][0]["extent"]["value"] = "forged extent"
    try:
        validate_dossier(mutated)
    except DossierValidationError:
        pass
    else:
        raise SystemExit("forged span extent was accepted")

    mutated = copy.deepcopy(dossier)
    mutated["lineages"][0]["status"] = "known"
    try:
        validate_dossier(mutated)
    except DossierValidationError:
        pass
    else:
        raise SystemExit("unstamped lineage mutation was accepted")


def render(dossier: dict[str, Any]) -> str:
    return json.dumps(dossier, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    dossier = build()
    verify_adversarial(dossier)
    output = render(dossier)
    if args.check:
        if not CANDIDATE_PATH.is_file() or CANDIDATE_PATH.read_text() != output:
            raise SystemExit("candidate dossier differs from deterministic build")
    else:
        CANDIDATE_PATH.write_text(output)
    print(
        canonical_json(
            {
                "dossier_id": dossier["dossier_id"],
                "source_works": len(dossier["source_works"]) - 1,
                "examined_editions": len(dossier["editions"]) - 1,
                "exact_span_roots": len(root_span_keys(dossier)),
                "candidate_warrant_roots": EXPECTED_COUNTS["candidate_warrant_roots"],
                "independently_confirmed_warrant_roots": 0,
                "unresolved_citations": EXPECTED_COUNTS["unresolved_citations"],
                "em0029_review_supplement_spans": 3,
            }
        )
    )
    return 0


def root_span_keys(dossier: dict[str, Any]) -> list[str]:
    return [
        record["key"]
        for record in dossier["spans"]
        if not record["key"].startswith(("span-audit", "span-supplement"))
    ]


if __name__ == "__main__":
    raise SystemExit(main())
