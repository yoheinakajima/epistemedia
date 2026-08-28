#!/usr/bin/env python3
"""Build the deterministic Case 004 candidate dossier from accepted EM-0033 bytes.

The builder is deliberately offline.  It reads only the accepted research
packet and its independent-review receipt, then projects those reviewed
records into the repository's dossier-v0.1 interchange shape.
"""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from epistemedia.dossier import DOSSIER_FORMAT, stamp_dossier, validate_dossier

HERE = Path(__file__).resolve().parent
PACKET_PATH = HERE / "candidate-packet.json"
REVIEW_PATH = HERE / "independent-review-receipt.json"
SOURCE_RECORDS_PATH = HERE / "source-records.json"
OUTPUT_PATH = HERE / "candidate-dossier.json"

ACCEPTED_PACKET_SHA256 = "6253a8ece3bb3b5bfb393ec04ad4e0f14b88f567ddea2923300538eadb7c8cde"
ACCEPTED_REVIEW_SHA256 = "b70e6ae4f073004cc602860bf0a1c3976d6c7fb12c3440253e68a8ff20538d1b"
ACCEPTED_PACKET_ID = (
    "em:research-packet:sha256:a73dc29f0a0c3f05a112b7c392d115cfcc38a1136a683325bf74bebf0c6b2e40"
)
ACCEPTED_SOURCE_RECORDS_SHA256 = "0ac4f87236882d32aa6018e50600a79642b87acdf05e27c291514e770fda081c"
ASSERTED_AT = "2026-08-27T16:03:55Z"
EXPECTED_COUNTS = {
    "claims": 11,
    "derivations": 6,
    "follow_up_objects": 5,
    "lineage_edges": 11,
    "lineage_groups": 6,
    "participant_data_roots": 5,
    "propagation_objects": 3,
    "quote_minimal_spans": 40,
    "source_records": 12,
}
SOURCE_KIND = {
    "work-mehrabian-author-page": "webpage",
    "work-silent-messages": "book",
    "work-hampshire-pcc-deck-2022": "report",
    "work-birmingham-events-page-2020": "webpage",
}
URI_PRIORITY = (
    "doi",
    "landing",
    "catalog",
    "pubmed",
    "inspected_scan",
    "alternate_readback",
    "pdf",
)
CLAIM_LINEAGE = {
    "claim-popular-rule": "lineage-general-rule-synthesis",
    "claim-p1-tone-dominance": "lineage-participant-p1",
    "claim-p2-face-tone": "lineage-participant-p2",
    "claim-three-coefficient-proposal": "lineage-cross-study-proposal",
    "claim-seven-origin": "lineage-seven-origin-unknown",
    "claim-book-boundary": "lineage-silent-1971",
    "claim-1981-edition": "lineage-silent-1981-unknown",
    "claim-hegstrom-rebuttal": "lineage-hegstrom-rebuttal",
    "claim-related-context": "lineage-argyle-related-program",
    "claim-propagation": "lineage-propagation-synthesis",
    "claim-replication-search": "lineage-follow-up-synthesis",
}
DERIVATION_LINEAGE = {
    "derive-proposed-sum": "lineage-cross-study-proposal",
    "derive-proposed-facial-vocal-ratio": "lineage-cross-study-proposal",
    "derive-p2-facial-vocal-ratio": "lineage-cross-study-proposal",
    "derive-ratio-difference": "lineage-cross-study-proposal",
    "derive-implied-vocal-verbal-ratio": "lineage-seven-origin-unknown",
    "derive-p2-allocation-with-seven-reserved": "lineage-seven-origin-unknown",
}
DERIVATION_SPANS = {
    "derive-proposed-sum": ["span-ferris-proposal"],
    "derive-proposed-facial-vocal-ratio": ["span-ferris-proposal"],
    "derive-p2-facial-vocal-ratio": ["span-ferris-regression"],
    "derive-ratio-difference": ["span-ferris-regression", "span-ferris-proposal"],
    "derive-implied-vocal-verbal-ratio": ["span-ferris-proposal"],
    "derive-p2-allocation-with-seven-reserved": [
        "span-ferris-regression",
        "span-ferris-proposal",
    ],
}
EDGE_ENDPOINTS = {
    "edge-p1-p2-participant": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-speaker": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-author-social": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-grant": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-stimulus": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-material": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-method": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p1-p2-scale": ("lineage-participant-p1", "lineage-participant-p2"),
    "edge-p2-cites-p1": ("lineage-participant-p2", "lineage-participant-p1"),
    "edge-silent-messages-editions": (
        "lineage-silent-1971",
        "lineage-silent-1981-unknown",
    ),
    "edge-p1-p2-proposal-derivation": (
        "lineage-mehrabian-original-program",
        "lineage-cross-study-proposal",
    ),
}


def canonical_json(value: Any) -> bytes:
    """Return the repository's stable JSON encoding."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else canonical_json(value)
    return "sha256:" + sha256_bytes(raw)


def canonical_uri(record: dict[str, Any]) -> str:
    urls = record.get("urls")
    if not isinstance(urls, dict):
        raise ValueError(f"{record.get('source_id')} has no URL register")
    for role in URI_PRIORITY:
        value = urls.get(role)
        if isinstance(value, str) and value:
            return value
    raise ValueError(f"{record.get('source_id')} has no canonical URI")


def edition_record(
    source: dict[str, Any],
    captured_at: str,
) -> dict[str, Any]:
    content = {
        "format": "epistemedia-em0033-source-record-projection-v1",
        "accepted_packet_id": ACCEPTED_PACKET_ID,
        "source_record": source,
    }
    encoded = canonical_json(content)
    return {
        "key": source["edition_id"],
        "work_key": source["work_id"],
        "edition_label": f"Reviewed source-record projection of {source['edition_id']}",
        "media_type": "application/json",
        "retrieved_at": captured_at,
        "content": content,
        "content_digest": "sha256:" + sha256_bytes(encoded),
        "content_length": len(encoded),
        "visibility": "public",
    }


def span_record(
    source: dict[str, Any],
    index: int,
    span: dict[str, Any],
) -> dict[str, Any]:
    return {
        "key": span["span_id"],
        "edition_key": source["edition_id"],
        "locator": {
            "type": "json-pointer",
            "pointer": f"/source_record/spans/{index}",
            "label": span["locator"],
        },
        "extent": {"type": "json-value", "value": span},
        "digest": digest(span),
        "visibility": "public",
    }


def lineage_record(
    lineage_key: str,
    *,
    status: str,
    dimensions: list[str],
    depends_on: list[str],
    basis_span_keys: list[str],
    note: str,
) -> dict[str, Any]:
    return {
        "key": lineage_key,
        "status": status,
        "dimensions": dimensions,
        "depends_on": depends_on,
        "basis_span_keys": sorted(set(basis_span_keys)),
        "assertion_keys": [],
        "note": note,
        "visibility": "public",
    }


def make_lineages(spans_by_source: dict[str, list[str]]) -> list[dict[str, Any]]:
    roots = [
        (
            "lineage-participant-p1",
            "source-mehrabian-wiener-1967",
            "known",
            ["data", "method", "apparatus", "social"],
            "First 1967 paper: one reported participant-data root for the words-and-tone task.",
        ),
        (
            "lineage-participant-p2",
            "source-mehrabian-ferris-1967",
            "known",
            ["data", "method", "apparatus", "social"],
            "Second 1967 paper: a distinct reported participant-data root for the face-and-tone task; person-level overlap is not disclosed.",
        ),
        (
            "lineage-author-qualification",
            "source-mehrabian-author-qualification",
            "known",
            ["source", "social"],
            "Later author interpretation and qualification; it supplies no new participant evidence.",
        ),
        (
            "lineage-silent-1971",
            "source-silent-messages-1971",
            "known",
            ["source", "model"],
            "Inspected 1971 book edition, represented only by reviewed quote-minimal spans and capture identity.",
        ),
        (
            "lineage-silent-1981-unknown",
            "source-silent-messages-1981",
            "unknown",
            ["source", "retrieval"],
            "The 1981 second-edition identity is known, but formula-page continuity is unknown because the edition was not textually collated.",
        ),
        (
            "lineage-hegstrom-rebuttal",
            "source-hegstrom-1979",
            "known",
            ["data", "method", "source"],
            "Separate reported participant-data root and direct all-channel rebuttal; full-text participant and material details remain unavailable.",
        ),
        (
            "lineage-participant-argyle-1970",
            "source-argyle-1970",
            "known",
            ["data", "method", "source"],
            "Reported participant-data root for the 1970 superiority/inferiority experiment.",
        ),
        (
            "lineage-participant-argyle-1971",
            "source-argyle-1971",
            "known",
            ["data", "method", "source"],
            "Reported participant-data root for the 1971 friendly/hostile experiments.",
        ),
        (
            "lineage-lapakko-1997",
            "source-lapakko-1997",
            "known",
            ["source", "method", "social"],
            "Methodological critique source; no new participant evidence is credited.",
        ),
        (
            "lineage-lapakko-2007",
            "source-lapakko-2007",
            "known",
            ["source", "method", "social"],
            "Bounded propagation study and critique; circulation receives zero scientific-rule credit.",
        ),
        (
            "lineage-hampshire-propagation",
            "source-hampshire-pcc-2022",
            "known",
            ["source", "social"],
            "Institutional recirculation object with zero scientific-rule evidence credit.",
        ),
        (
            "lineage-birmingham-propagation",
            "source-birmingham-events-2020",
            "known",
            ["source", "social"],
            "Institutional recirculation object with zero scientific-rule evidence credit.",
        ),
    ]
    result = [
        lineage_record(
            lineage_key,
            status=status,
            dimensions=dimensions,
            depends_on=[],
            basis_span_keys=spans_by_source[source_id],
            note=note,
        )
        for lineage_key, source_id, status, dimensions, note in roots
    ]

    def spans(*source_ids: str) -> list[str]:
        return [span_key for source_id in source_ids for span_key in spans_by_source[source_id]]

    result.extend(
        [
            lineage_record(
                "lineage-mehrabian-original-program",
                status="known",
                dimensions=["data", "method", "apparatus", "model", "social"],
                depends_on=["lineage-participant-p1", "lineage-participant-p2"],
                basis_span_keys=spans(
                    "source-mehrabian-wiener-1967",
                    "source-mehrabian-ferris-1967",
                ),
                note="Two distinct reported participant groups within one linked UCLA author, grant, material, method, scale, citation, and derivation program.",
            ),
            lineage_record(
                "lineage-mehrabian-interpretation",
                status="known",
                dimensions=["source", "model", "retrieval", "social"],
                depends_on=[
                    "lineage-silent-1971",
                    "lineage-silent-1981-unknown",
                    "lineage-author-qualification",
                ],
                basis_span_keys=spans(
                    "source-silent-messages-1971",
                    "source-silent-messages-1981",
                    "source-mehrabian-author-qualification",
                ),
                note="One authorial interpretation and book-edition lineage; it supplies no new participant evidence and preserves the unknown 1981 formula-page comparison.",
            ),
            lineage_record(
                "lineage-argyle-related-program",
                status="known",
                dimensions=["data", "method", "source", "social"],
                depends_on=[
                    "lineage-participant-argyle-1970",
                    "lineage-participant-argyle-1971",
                ],
                basis_span_keys=spans("source-argyle-1970", "source-argyle-1971"),
                note="Two related Oxford studies with shared author/program and different attitude dimensions; related boundary evidence, not exact replication.",
            ),
            lineage_record(
                "lineage-lapakko-critique-propagation",
                status="known",
                dimensions=["source", "method", "social"],
                depends_on=["lineage-lapakko-1997", "lineage-lapakko-2007"],
                basis_span_keys=spans("source-lapakko-1997", "source-lapakko-2007"),
                note="Same-author critique program; the 2007 bounded website sample measures circulation, not scientific effect.",
            ),
            lineage_record(
                "lineage-institutional-recirculation",
                status="known",
                dimensions=["source", "social"],
                depends_on=[
                    "lineage-hampshire-propagation",
                    "lineage-birmingham-propagation",
                ],
                basis_span_keys=spans(
                    "source-hampshire-pcc-2022",
                    "source-birmingham-events-2020",
                ),
                note="Separate institutional recirculation objects, each assigned zero empirical evidence credit.",
            ),
            lineage_record(
                "lineage-cross-study-proposal",
                status="known",
                dimensions=["data", "method", "model", "source", "social"],
                depends_on=["lineage-mehrabian-original-program"],
                basis_span_keys=[
                    "span-ferris-citation-p1",
                    "span-ferris-design",
                    "span-ferris-regression",
                    "span-ferris-proposal",
                ],
                note="The later .07/.38/.55 proposal combines the two linked 1967 studies; it is not a third participant-data root or one three-channel experiment.",
            ),
            lineage_record(
                "lineage-seven-origin-unknown",
                status="unknown",
                dimensions=["model", "source"],
                depends_on=["lineage-cross-study-proposal"],
                basis_span_keys=[
                    "span-ferris-regression",
                    "span-ferris-proposal",
                    "span-silent-1971-liking",
                ],
                note="The exact source derivation of the .07 verbal coefficient remains unknown and receives no credit; reverse engineering is sensitivity analysis only.",
            ),
            lineage_record(
                "lineage-propagation-synthesis",
                status="known",
                dimensions=["source", "method", "social"],
                depends_on=[
                    "lineage-lapakko-critique-propagation",
                    "lineage-institutional-recirculation",
                ],
                basis_span_keys=spans(
                    "source-lapakko-2007",
                    "source-hampshire-pcc-2022",
                    "source-birmingham-events-2020",
                ),
                note="Circulation synthesis only; every propagation object remains at zero scientific-rule evidence credit.",
            ),
            lineage_record(
                "lineage-follow-up-synthesis",
                status="known",
                dimensions=["data", "method", "source", "social"],
                depends_on=[
                    "lineage-hegstrom-rebuttal",
                    "lineage-argyle-related-program",
                    "lineage-lapakko-1997",
                ],
                basis_span_keys=spans(
                    "source-hegstrom-1979",
                    "source-argyle-1970",
                    "source-argyle-1971",
                    "source-lapakko-1997",
                ),
                note="A direct all-channel rebuttal, related context-dependent studies, and critique remain separate; no exhaustive replication claim is made.",
            ),
            lineage_record(
                "lineage-general-rule-synthesis",
                status="known",
                dimensions=["data", "method", "model", "source", "social"],
                depends_on=[
                    "lineage-cross-study-proposal",
                    "lineage-mehrabian-interpretation",
                    "lineage-hegstrom-rebuttal",
                    "lineage-argyle-related-program",
                    "lineage-propagation-synthesis",
                ],
                basis_span_keys=sorted(
                    {
                        span_key
                        for source_spans in spans_by_source.values()
                        for span_key in source_spans
                    }
                ),
                note="Synthesis retains narrow experimental results, later qualification, direct rebuttal, and zero-credit recirculation without promoting a universal communication rule.",
            ),
            lineage_record(
                "lineage-reviewed-source-register",
                status="known",
                dimensions=["source", "retrieval", "other"],
                depends_on=[
                    "lineage-mehrabian-original-program",
                    "lineage-mehrabian-interpretation",
                    "lineage-hegstrom-rebuttal",
                    "lineage-argyle-related-program",
                    "lineage-lapakko-critique-propagation",
                    "lineage-institutional-recirculation",
                ],
                basis_span_keys=sorted(
                    {
                        span_key
                        for source_spans in spans_by_source.values()
                        for span_key in source_spans
                    }
                ),
                note="Relation-derived register of the accepted packet's source, edition, span, claim, calculation, lineage, propagation, and follow-up objects.",
            ),
        ]
    )
    return result


def load_accepted_json(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected_sha256:
        raise ValueError(f"{path.name} changed: expected {expected_sha256}, observed {actual}")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def build_candidate() -> dict[str, Any]:
    packet = load_accepted_json(PACKET_PATH, ACCEPTED_PACKET_SHA256)
    review = load_accepted_json(REVIEW_PATH, ACCEPTED_REVIEW_SHA256)
    source_register = load_accepted_json(SOURCE_RECORDS_PATH, ACCEPTED_SOURCE_RECORDS_SHA256)
    if packet.get("packet_id") != ACCEPTED_PACKET_ID:
        raise ValueError("accepted packet ID does not match the bound EM-0033 packet")
    if (
        review.get("decision") != "pass"
        or review.get("recommendation") != "GO"
        or review.get("complete") is not True
        or review.get("task_id") != "EM-0033"
    ):
        raise ValueError("accepted independent review is not a passing GO receipt")
    bindings = review.get("bindings")
    if not isinstance(bindings, dict):
        raise ValueError("accepted independent review has no bindings")
    if bindings.get("packet_id") != ACCEPTED_PACKET_ID:
        raise ValueError("independent review packet-ID binding drift")
    if bindings.get("candidate_packet") != {
        "bytes": len(PACKET_PATH.read_bytes()),
        "sha256": ACCEPTED_PACKET_SHA256,
    }:
        raise ValueError("independent review packet-byte binding drift")
    if bindings.get("source_records") != {
        "bytes": len(SOURCE_RECORDS_PATH.read_bytes()),
        "sha256": ACCEPTED_SOURCE_RECORDS_SHA256,
    }:
        raise ValueError("independent review source-register binding drift")

    content = packet.get("content")
    if not isinstance(content, dict):
        raise ValueError("accepted packet content must be an object")
    projected_register = copy.deepcopy(source_register)
    for source in projected_register["source_records"]:
        for span in source["spans"]:
            span["quote_sha256"] = sha256_bytes(span["quote"].encode("utf-8"))
    for field, value in projected_register.items():
        if field in content and content[field] != value:
            raise ValueError(f"accepted packet/source-register drift at {field}")
    sources = content.get("source_records")
    if not isinstance(sources, list):
        raise ValueError("accepted packet source_records must be an array")

    derived_counts = {
        "claims": len(content["claims"]),
        "derivations": len(content["derivations"]),
        "follow_up_objects": len(content["follow_up_ledger"]),
        "lineage_edges": len(content["lineage_edges"]),
        "lineage_groups": len(content["lineages"]),
        "participant_data_roots": sum(
            item["participant_data_roots"] for item in content["lineages"]
        ),
        "propagation_objects": len(content["propagation_ledger"]),
        "quote_minimal_spans": sum(len(source["spans"]) for source in sources),
        "source_records": len(sources),
    }
    if derived_counts != EXPECTED_COUNTS or content.get("counts") != derived_counts:
        raise ValueError("accepted relation-derived count identity drift")
    if any(
        item.get("scientific_rule_evidence_credit") != 0 for item in content["propagation_ledger"]
    ):
        raise ValueError("propagation object received scientific-rule evidence credit")

    sources_by_id = {source["source_id"]: source for source in sources}
    if len(sources_by_id) != len(sources):
        raise ValueError("duplicate accepted source ID")
    works: dict[str, list[dict[str, Any]]] = {}
    for source in sources:
        works.setdefault(source["work_id"], []).append(source)

    source_works = []
    for work_id, records in sorted(works.items()):
        ordered = sorted(records, key=lambda item: item["source_id"])
        first = ordered[0]
        licenses = sorted({item["license_treatment"] for item in records})
        source_works.append(
            {
                "key": work_id,
                "kind": SOURCE_KIND.get(work_id, "paper"),
                "title": first["title"],
                "creators": first["authors"],
                "canonical_uri": canonical_uri(first),
                "license": "; ".join(licenses),
                "visibility": "public",
            }
        )

    editions = []
    spans = []
    spans_by_source: dict[str, list[str]] = {}
    span_ids: set[str] = set()
    for source in sorted(sources, key=lambda item: item["source_id"]):
        editions.append(edition_record(source, content["captured_at"]))
        source_span_keys = []
        for index, span in enumerate(source["spans"]):
            span_key = span["span_id"]
            if span_key in span_ids:
                raise ValueError(f"duplicate accepted span ID: {span_key}")
            span_ids.add(span_key)
            source_span_keys.append(span_key)
            spans.append(span_record(source, index, span))
        spans_by_source[source["source_id"]] = source_span_keys
    if len(spans) != EXPECTED_COUNTS["quote_minimal_spans"]:
        raise ValueError("accepted parent-span count drift")

    propositions = [
        {
            "key": claim["claim_id"],
            "text": claim["proposition"],
            "scope": (
                f"Accepted EM-0033 status: {claim['status']}; "
                f"evidence cutoff {content['evidence_cutoff']}."
            ),
            "visibility": "public",
        }
        for claim in content["claims"]
    ]
    for calculation in content["derivations"]:
        result_text = json.dumps(
            calculation["result"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        propositions.append(
            {
                "key": calculation["derivation_id"],
                "text": (
                    f"{calculation['interpretation']} "
                    f"Calculation: {calculation['equation']} = {result_text}."
                ),
                "scope": (
                    "Mechanical reproduction from accepted EM-0033 inputs; "
                    "not a new empirical estimate."
                ),
                "visibility": "public",
            }
        )

    unique_work_count = len(works)
    edition_count = len({source["edition_id"] for source in sources})
    propositions.extend(
        [
            {
                "key": "prop-reviewed-source-register",
                "text": (
                    f"The accepted packet contains {len(sources)} source records, "
                    f"{unique_work_count} source works, {edition_count} editions, "
                    f"{len(spans)} parent spans, {len(content['claims'])} claims, "
                    f"{len(content['derivations'])} calculations, "
                    f"{len(content['lineages'])} lineage groups, "
                    f"{derived_counts['participant_data_roots']} participant-data roots, "
                    f"{len(content['lineage_edges'])} typed lineage edges, "
                    f"{len(content['propagation_ledger'])} propagation objects, and "
                    f"{len(content['follow_up_ledger'])} follow-up dispositions."
                ),
                "scope": "Counts derived from accepted packet relations, never editorial totals.",
                "visibility": "public",
            },
            {
                "key": "prop-encyclopedia-evaluation",
                "text": (
                    "The historically defensible account is a narrow cross-study weighting "
                    "proposal over inconsistent feelings-and-attitudes tasks, with the two "
                    "1967 participant roots and later interpretation kept distinct."
                ),
                "scope": "Encyclopedia policy: document the bounded historical proposal and its limits.",
                "visibility": "public",
            },
            {
                "key": "prop-skeptical-evaluation",
                "text": (
                    "A universal 93-percent rule should be withheld because no reviewed "
                    "three-channel experiment established it, the .07 origin is unresolved, "
                    "and direct all-channel evidence reported message-specific equations."
                ),
                "scope": "Skeptical policy: withhold broad causal or universal interpretation.",
                "visibility": "public",
            },
        ]
    )

    lineages = make_lineages(spans_by_source)
    lineages_by_key = {lineage["key"]: lineage for lineage in lineages}
    if len(lineages_by_key) != len(lineages):
        raise ValueError("duplicate dossier lineage key")
    assertions: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []

    def add_assertion(
        assertion_key: str,
        proposition_key: str,
        lineage_key: str,
        source_span_keys: list[str],
        *,
        actor_id: str = "accepted-em0033-reviewed-record",
        stance: str = "asserts",
        relation_type: str = "support",
    ) -> None:
        if not source_span_keys or any(key not in span_ids for key in source_span_keys):
            raise ValueError(f"{assertion_key} lacks exact accepted span closure")
        assertion = {
            "key": assertion_key,
            "proposition_key": proposition_key,
            "actor": {"id": actor_id, "kind": "collective"},
            "stance": stance,
            "span_keys": source_span_keys,
            "lineage_key": lineage_key,
            "asserted_at": ASSERTED_AT,
            "visibility": "public",
        }
        assertions.append(assertion)
        lineages_by_key[lineage_key]["assertion_keys"].append(assertion_key)
        relations.append(
            {
                "key": f"relation-{assertion_key}",
                "relation_type": relation_type,
                "from_ref": source_span_keys[0],
                "to_ref": proposition_key,
                "basis_span_keys": source_span_keys,
                "note": "Material proposition closes over the listed exact reviewed parent spans.",
                "visibility": "public",
            }
        )

    for claim in content["claims"]:
        claim_id = claim["claim_id"]
        add_assertion(
            "assertion-" + claim_id.removeprefix("claim-"),
            claim_id,
            CLAIM_LINEAGE[claim_id],
            claim["span_ids"],
        )
    for calculation in content["derivations"]:
        derivation_id = calculation["derivation_id"]
        add_assertion(
            "assertion-" + derivation_id,
            derivation_id,
            DERIVATION_LINEAGE[derivation_id],
            DERIVATION_SPANS[derivation_id],
            actor_id="em0033-deterministic-calculator",
        )

    all_span_keys = sorted(span_ids)
    add_assertion(
        "assertion-reviewed-source-register",
        "prop-reviewed-source-register",
        "lineage-reviewed-source-register",
        all_span_keys,
        actor_id="em0035-relation-counter",
    )
    add_assertion(
        "assertion-encyclopedia-evaluation",
        "prop-encyclopedia-evaluation",
        "lineage-general-rule-synthesis",
        [
            "span-wiener-target",
            "span-ferris-target",
            "span-ferris-design",
            "span-ferris-proposal",
            "span-silent-1971-boundary",
            "span-author-qualification",
        ],
        actor_id="em0035-encyclopedia-policy",
    )
    add_assertion(
        "assertion-skeptical-evaluation",
        "prop-skeptical-evaluation",
        "lineage-general-rule-synthesis",
        [
            "span-wiener-target",
            "span-ferris-target",
            "span-ferris-design",
            "span-ferris-proposal",
            "span-hegstrom-result",
            "span-lapakko-1997-abstract",
        ],
        actor_id="em0035-skeptical-policy",
    )

    relations.extend(
        [
            {
                "key": "relation-author-qualification",
                "relation_type": "qualification",
                "from_ref": "span-author-qualification",
                "to_ref": "claim-popular-rule",
                "basis_span_keys": ["span-author-qualification"],
                "note": "The author's later statement limits the formula to inconsistent feelings and attitudes.",
                "visibility": "public",
            },
            {
                "key": "relation-hegstrom-direct-rebuttal",
                "relation_type": "rebuttal",
                "from_ref": "span-hegstrom-result",
                "to_ref": "claim-popular-rule",
                "basis_span_keys": ["span-hegstrom-design", "span-hegstrom-result"],
                "note": "The direct all-channel reconsideration reports message-specific equations unlike a fixed universal rule.",
                "visibility": "public",
            },
            {
                "key": "relation-lapakko-method-undercutting",
                "relation_type": "undercutting",
                "from_ref": "span-lapakko-1997-abstract",
                "to_ref": "claim-popular-rule",
                "basis_span_keys": ["span-lapakko-1997-abstract"],
                "note": "The methodological critique says the limitations do not warrant a precise general formula.",
                "visibility": "public",
            },
            {
                "key": "relation-argyle-context-qualification",
                "relation_type": "qualification",
                "from_ref": "span-argyle-1970-abstract",
                "to_ref": "claim-related-context",
                "basis_span_keys": [
                    "span-argyle-1970-abstract",
                    "span-argyle-1971-experiment-one",
                    "span-argyle-1971-experiment-two",
                ],
                "note": "Related tasks produce materially different ratios and therefore qualify any fixed cross-context weighting.",
                "visibility": "public",
            },
        ]
    )
    edges_by_id = {edge["edge_id"]: edge for edge in content["lineage_edges"]}
    if set(edges_by_id) != set(EDGE_ENDPOINTS):
        raise ValueError("accepted typed-lineage edge identity drift")
    for edge_id in sorted(edges_by_id):
        edge = edges_by_id[edge_id]
        from_ref, to_ref = EDGE_ENDPOINTS[edge_id]
        relations.append(
            {
                "key": edge_id,
                "relation_type": "dependence",
                "from_ref": from_ref,
                "to_ref": to_ref,
                "basis_span_keys": edge["evidence_span_ids"],
                "note": (
                    f"accepted_dimension={edge['dimension']}; "
                    f"accepted_status={edge['status']}; "
                    f"effect={edge['effect_on_independence']}"
                ),
                "visibility": "public",
            }
        )

    for lineage in lineages:
        lineage["assertion_keys"].sort()
    proposition_keys = [item["key"] for item in propositions]
    assertion_keys = [item["key"] for item in assertions]
    relation_keys = [item["key"] for item in relations]
    family_key = "family-mehrabian-7-38-55"
    families = [
        {
            "key": family_key,
            "title": "Mehrabian 7-38-55: narrow findings, later integration, and overgeneralization",
            "question": content["question"],
            "proposition_keys": proposition_keys,
            "assertion_keys": assertion_keys,
            "relation_keys": relation_keys,
            "visibility": "public",
        }
    ]
    evaluations = [
        {
            "key": "evaluation-encyclopedia",
            "claim_family_key": family_key,
            "policy_id": "epistemedia-encyclopedia-v1",
            "frontier": ACCEPTED_PACKET_ID,
            "label": "documented narrow historical proposal with explicit experiment and edition boundaries",
            "reason_codes": [
                "historical-proposal-documented",
                "two-participant-roots-kept-distinct",
                "cross-study-integration-not-one-experiment",
                "scope-qualification-retained",
            ],
            "visibility": "public",
        },
        {
            "key": "evaluation-skeptical",
            "claim_family_key": family_key,
            "policy_id": "epistemedia-skeptical-v1",
            "frontier": ACCEPTED_PACKET_ID,
            "label": "withhold universal rule and withhold recovered-origin claim for the seven-percent coefficient",
            "reason_codes": [
                "no-reviewed-three-channel-test",
                "seven-percent-origin-unresolved",
                "direct-rebuttal-message-specific",
                "propagation-zero-truth-credit",
                "second-edition-formula-pages-uncollated",
            ],
            "visibility": "public",
        },
    ]
    material = {
        "format": DOSSIER_FORMAT,
        "title": "Case 004: What the Mehrabian 7-38-55 weighting did and did not show",
        "question": content["question"],
        "scope": (
            f"Evidence through {content['evidence_cutoff']}; a disclosure-safe research "
            "candidate derived only from the accepted EM-0033 packet. It is not admitted, "
            "not featured, not live, not published, and not evidence for a universal "
            "communication rule."
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
        "claim_families": families,
        "evaluations": evaluations,
    }
    return stamp_dossier(material)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    candidate = build_candidate()
    validate_dossier(candidate)
    rendered = (
        json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
    )
    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_bytes() != rendered:
            raise SystemExit("candidate dossier differs from deterministic build")
    else:
        OUTPUT_PATH.write_bytes(rendered)


if __name__ == "__main__":
    main()
