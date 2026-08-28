#!/usr/bin/env python3
"""Build the deterministic Case 003 dossier from accepted EM-0032 bytes."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import NormalDist, stdev
from typing import Any

from epistemedia.dossier import DOSSIER_FORMAT, stamp_dossier, validate_dossier

HERE = Path(__file__).resolve().parent
PACKET_PATH = HERE / "candidate-packet.json"
REVIEW_PATH = HERE / "independent-review-receipt.json"
SOURCE_RECORDS_PATH = HERE / "source-records.json"
ARTIFACT_INVENTORY_PATH = HERE / "artifact-inventory.json"
GIT_SEARCH_PATH = HERE / "git-blob-search-manifest.json"
OUTPUT_PATH = HERE / "candidate-dossier.json"

ACCEPTED_PACKET_SHA256 = "07dec44bc2cf893b19ba6307e34aef60b6127b5e881e319ff4132c8e69972d1a"
ACCEPTED_REVIEW_SHA256 = "0606e98ed7ff98f1d0e69509db5edcd8dce774c62c48981bd5aec8f23a95ad20"
ACCEPTED_SOURCE_RECORDS_SHA256 = "385bbc193be495597ef0fe2a675220ca443297e673b32947c8d8ffcd1a6366da"
ACCEPTED_ARTIFACT_INVENTORY_SHA256 = (
    "f9e45045831a15fcb40c7f542c73651e5dc63ba081b145d00260bee91192c25b"
)
ACCEPTED_GIT_SEARCH_SHA256 = "708657f61bc759f3a5b439affde1a677177859b50a8bc960012b81dcebcdb122"
ACCEPTED_PACKET_ID = (
    "em:research-packet:sha256:535d07e59563b12f66e590c31b0d53a21db1a8dfce1487129a54c5e86b9fd55b"
)
ASSERTED_AT = "2026-08-28T00:39:59Z"
CALCULATION_WORK_KEY = "work-em0032-calculation-register"
CALCULATION_EDITION_KEY = "edition-em0032-calculation-register"
EXPECTED_COUNTS = {
    "calculations": 10,
    "core_sources": 15,
    "git_blob_binary_bodies": 6,
    "git_blob_bodies": 78,
    "git_blob_text_bodies": 72,
    "lineage_edges": 10,
    "lineage_roots": 5,
    "parent_spans": 35,
    "sources": 19,
    "typed_span_units": 76,
}
JULY_MBE_BINS = [
    (85, 2),
    (90, 2),
    (95, 5),
    (100, 6),
    (105, 13),
    (110, 22),
    (115, 33),
    (120, 56),
    (125, 73),
    (130, 78),
    (135, 104),
    (140, 96),
    (145, 101),
    (150, 99),
    (155, 99),
    (160, 79),
    (165, 64),
    (170, 38),
    (175, 22),
    (180, 8),
    (185, 2),
]
JULY_MBE_CELL_IDS = [f"cell-martinez-july-mbe-{score}" for score, _ in JULY_MBE_BINS]
CLAIM_LINEAGE = {
    "claim-launch-score-label": "lineage-model-performance-root",
    "claim-launch-comparison-unspecified": "lineage-model-performance-root",
    "claim-score-discrepancy": "lineage-model-performance-root",
    "claim-february-sensitive": "lineage-illinois-comparison-root",
    "claim-july-sensitive": "lineage-illinois-comparison-root",
    "claim-martinez-first-time": "lineage-martinez-analysis-root",
    "claim-martinez-passers-conflict": "lineage-martinez-analysis-root",
    "claim-no-lawyer-rank": "lineage-model-performance-root",
}
DERIVATION_LINEAGE = {
    "derive-illinois-feb-2018-298": "lineage-illinois-comparison-root",
    "derive-illinois-jul-2018-298": "lineage-illinois-comparison-root",
    "derive-illinois-feb-2019-298": "lineage-illinois-comparison-root",
    "derive-martinez-parameters": "lineage-martinez-analysis-root",
    "derive-martinez-first-time-ube": "lineage-martinez-analysis-root",
    "derive-martinez-passers-ube": "lineage-martinez-analysis-root",
    "derive-martinez-first-time-mbe": "lineage-martinez-analysis-root",
    "derive-martinez-passers-mbe": "lineage-martinez-analysis-root",
    "derive-martinez-first-time-essay": "lineage-martinez-analysis-root",
    "derive-martinez-passers-essay": "lineage-martinez-analysis-root",
}
LINEAGE_DEPENDS_ON = {
    "lineage-model-performance-root": [],
    "lineage-illinois-comparison-root": [],
    "lineage-ncbe-comparison-root": [],
    "lineage-new-york-pass-rate-root": [],
    "lineage-martinez-analysis-root": [
        "lineage-model-performance-root",
        "lineage-illinois-comparison-root",
        "lineage-ncbe-comparison-root",
        "lineage-new-york-pass-rate-root",
    ],
}
LINEAGE_DIMENSIONS = {
    "performance": ["data", "method", "model", "social"],
    "analysis": ["data", "method", "model", "source"],
    "comparison-data": ["data", "source"],
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else canonical_json(value)
    return "sha256:" + sha256_bytes(raw)


def dossier_key(value: str) -> str:
    """Map an accepted external identifier into the dossier key alphabet."""

    return value.replace(".", "-")


def collect_cells(value: Any, cells: dict[str, dict[str, Any]]) -> None:
    """Index exact accepted table and code cells without altering their values."""

    if isinstance(value, dict):
        cell_id = value.get("cell_id")
        if isinstance(cell_id, str):
            prior = cells.setdefault(cell_id, value)
            if prior != value:
                raise ValueError(f"conflicting accepted cell identity: {cell_id}")
        for child in value.values():
            collect_cells(child, cells)
    elif isinstance(value, list):
        for child in value:
            collect_cells(child, cells)


def expanded_edge_relations(
    edge: dict[str, Any], source_to_lineage: dict[str, str]
) -> list[dict[str, str]]:
    """Return every accepted typed-edge endpoint as a dossier relation."""

    mapped_from = [source_to_lineage.get(item, item) for item in edge["from_ids"]]
    mapped_to = [source_to_lineage.get(item, item) for item in edge["to_ids"]]
    pairs = [(from_ref, to_ref) for from_ref in mapped_from for to_ref in mapped_to]
    return [
        {
            "key": edge["edge_id"] if len(pairs) == 1 else f"{edge['edge_id']}--{index}",
            "from_ref": from_ref,
            "to_ref": to_ref,
        }
        for index, (from_ref, to_ref) in enumerate(pairs, 1)
    ]


def load_accepted(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected_sha256:
        raise ValueError(f"{path.name} changed: expected {expected_sha256}, observed {actual}")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def conditional_percentile(distribution: NormalDist, score: float, lower: float) -> float:
    return 100 * (distribution.cdf(score) - distribution.cdf(lower)) / (1 - distribution.cdf(lower))


def reproduce_derivations() -> list[dict[str, Any]]:
    specs = [
        (
            "derive-illinois-feb-2018-298",
            85.0,
            90.0,
            "span-illinois-feb-2018-anchors",
            ["cell-illinois-feb-2018-290", "cell-illinois-feb-2018-300"],
        ),
        (
            "derive-illinois-jul-2018-298",
            59.0,
            70.0,
            "span-illinois-jul-2018-anchors",
            ["cell-illinois-jul-2018-290", "cell-illinois-jul-2018-300"],
        ),
        (
            "derive-illinois-feb-2019-298",
            83.0,
            90.0,
            "span-illinois-feb-2019-anchors",
            ["cell-illinois-feb-2019-290", "cell-illinois-feb-2019-300"],
        ),
    ]
    result: list[dict[str, Any]] = []
    for derivation_id, p290, p300, span_id, cell_ids in specs:
        result.append(
            {
                "derivation_id": derivation_id,
                "method": "reviewer sensitivity only: linear interpolation",
                "equation": "p298 = p290 + ((298 - 290) / 10) * (p300 - p290)",
                "inputs": {"score": 298, "p290": p290, "p300": p300},
                "input_span_ids": [span_id],
                "input_cell_ids": cell_ids,
                "result_percentile": p290 + 0.8 * (p300 - p290),
                "uncertainty": "Neither Illinois nor OpenAI disclosed this interpolation; it cannot be attributed as the launch method.",
            }
        )
    mbe_values = [score for score, count in JULY_MBE_BINS for _ in range(count)]
    mbe_sd = stdev(mbe_values)
    z_27 = NormalDist().inv_cdf(0.27)
    ube_sd = (266.0 - 287.6) / z_27
    ube_distribution = NormalDist(287.6, ube_sd)
    mbe_distribution = NormalDist(143.8, mbe_sd)
    result.extend(
        [
            {
                "derivation_id": "derive-martinez-parameters",
                "method": "analytic reproduction of the executable OSF inputs",
                "inputs": {
                    "first_time_mbe_mean": 143.8,
                    "assumed_first_time_essay_mean": 143.8,
                    "assumed_first_time_ube_mean": 287.6,
                    "new_york_cutoff": 266.0,
                    "new_york_nonpass_proportion": 0.27,
                    "july_mbe_binned_observations": len(mbe_values),
                },
                "input_span_ids": [
                    "span-reshetar-first-time-mean",
                    "span-martinez-mean-assumption",
                    "span-martinez-script-july-mbe-distribution",
                    "span-martinez-script-ube-sd",
                    "span-ncbe-ny-cutoff-2022",
                    "span-ny-first-timers-2022",
                ],
                "input_cell_ids": [
                    *JULY_MBE_CELL_IDS,
                    "cell-ncbe-ube-score-266",
                    "cell-ny-first-timers-rate",
                ],
                "results": {"z_at_0_27": z_27, "derived_ube_sd": ube_sd, "sample_mbe_sd": mbe_sd},
                "uncertainty": "The UBE distribution is inferred from aggregate inputs and normality; the essay mean/SD are assumed rather than observed.",
            },
            {
                "derivation_id": "derive-martinez-first-time-ube",
                "method": "normal CDF at score 298",
                "equation": "100 * Phi((298 - 287.6) / derived_ube_sd)",
                "result_percentile": 100 * ube_distribution.cdf(298),
                "comparison_population": "modeled first-time UBE takers",
                "depends_on": ["derive-martinez-parameters"],
            },
            {
                "derivation_id": "derive-martinez-passers-ube",
                "method": "normal CDF conditional on modeled UBE score >= 270",
                "equation": "100 * (F(298) - F(270)) / (1 - F(270))",
                "result_percentile": conditional_percentile(ube_distribution, 298, 270),
                "comparison_population": "modeled first-time scores at or above 270",
                "depends_on": ["derive-martinez-parameters"],
                "uncertainty": "The script uses 270 for this filter after using New York's 266 cutoff to infer UBE SD.",
            },
            {
                "derivation_id": "derive-martinez-first-time-mbe",
                "method": "normal CDF at MBE score 158",
                "result_percentile": 100 * mbe_distribution.cdf(158),
                "comparison_population": "modeled first-time MBE takers",
                "depends_on": ["derive-martinez-parameters"],
            },
            {
                "derivation_id": "derive-martinez-passers-mbe",
                "method": "normal CDF conditional on modeled MBE score >= 135",
                "result_percentile": conditional_percentile(mbe_distribution, 158, 135),
                "comparison_population": "modeled MBE scores at or above 135",
                "depends_on": ["derive-martinez-parameters"],
            },
            {
                "derivation_id": "derive-martinez-first-time-essay",
                "method": "normal CDF at essay score 140 using assumed MBE distribution",
                "result_percentile": 100 * mbe_distribution.cdf(140),
                "comparison_population": "modeled first-time essay scores",
                "depends_on": ["derive-martinez-parameters"],
            },
            {
                "derivation_id": "derive-martinez-passers-essay",
                "method": "normal CDF conditional on modeled essay score >= 135",
                "result_percentile": conditional_percentile(mbe_distribution, 140, 135),
                "comparison_population": "modeled essay scores at or above 135",
                "depends_on": ["derive-martinez-parameters"],
            },
        ]
    )
    return result


def source_kind(source: dict[str, Any]) -> str:
    if "book" in source.get("role", "").lower():
        return "book"
    if source["media_type"] in {"application/json", "text/csv", "text/plain"}:
        return "dataset"
    if source["media_type"] == "text/html":
        return "webpage"
    if (
        "statistics" in source["title"].lower()
        or "percentile equivalents" in source["title"].lower()
    ):
        return "report"
    return "paper"


def build_candidate() -> dict[str, Any]:
    packet = load_accepted(PACKET_PATH, ACCEPTED_PACKET_SHA256)
    review = load_accepted(REVIEW_PATH, ACCEPTED_REVIEW_SHA256)
    source_register = load_accepted(SOURCE_RECORDS_PATH, ACCEPTED_SOURCE_RECORDS_SHA256)
    artifact_inventory = load_accepted(ARTIFACT_INVENTORY_PATH, ACCEPTED_ARTIFACT_INVENTORY_SHA256)
    git_search = load_accepted(GIT_SEARCH_PATH, ACCEPTED_GIT_SEARCH_SHA256)
    if packet.get("packet_id") != ACCEPTED_PACKET_ID:
        raise ValueError("accepted packet ID drift")
    if (
        review.get("decision") != "pass"
        or review.get("recommendation") != "GO"
        or review.get("complete") is not True
        or review.get("task_id") != "EM-0032"
    ):
        raise ValueError("accepted EM-0032 review is not a complete passing GO receipt")
    bindings = review.get("bindings", {})
    expected_bindings = {
        "candidate_packet": (PACKET_PATH, ACCEPTED_PACKET_SHA256),
        "source_records": (SOURCE_RECORDS_PATH, ACCEPTED_SOURCE_RECORDS_SHA256),
        "artifact_inventory": (ARTIFACT_INVENTORY_PATH, ACCEPTED_ARTIFACT_INVENTORY_SHA256),
        "git_blob_search_manifest": (GIT_SEARCH_PATH, ACCEPTED_GIT_SEARCH_SHA256),
    }
    for key, (path, sha) in expected_bindings.items():
        if bindings.get(key) != {"bytes": len(path.read_bytes()), "sha256": sha}:
            raise ValueError(f"independent-review binding drift: {key}")
    content = packet.get("content")
    if not isinstance(content, dict) or content.get("source_records") != source_register:
        raise ValueError("packet/source-register identity drift")
    if (
        content.get("artifact_inventory") != artifact_inventory
        or content.get("git_blob_search_manifest") != git_search
    ):
        raise ValueError("packet artifact identity drift")
    if content.get("counts") != EXPECTED_COUNTS:
        raise ValueError("accepted count identity drift")
    if content.get("derivations") != reproduce_derivations():
        raise ValueError("accepted calculation reproduction drift")

    sources = source_register["sources"]
    claims = source_register["claims"]
    lineages_input = source_register["lineages"]
    edges_input = source_register["lineage_edges"]
    if (
        len(sources) != EXPECTED_COUNTS["sources"]
        or len(claims) != 8
        or len(lineages_input) != 5
        or len(edges_input) != 10
    ):
        raise ValueError("accepted relation-derived shape drift")
    if sum(len(source["spans"]) for source in sources) != EXPECTED_COUNTS["parent_spans"]:
        raise ValueError("accepted parent-span count drift")

    works: dict[str, list[dict[str, Any]]] = {}
    source_to_lineage: dict[str, str] = {}
    for lineage in lineages_input:
        for source_id in lineage["source_ids"]:
            if source_id in source_to_lineage:
                raise ValueError(f"source belongs to multiple lineages: {source_id}")
            source_to_lineage[source_id] = lineage["lineage_id"]
    for source in sources:
        works.setdefault(source["work_id"], []).append(source)
    if set(source_to_lineage) != {source["source_id"] for source in sources}:
        raise ValueError("lineage/source closure drift")

    source_works = []
    for work_id, records in sorted(works.items()):
        first = sorted(records, key=lambda item: item["source_id"])[0]
        source_works.append(
            {
                "key": work_id,
                "kind": source_kind(first),
                "title": first["title"],
                "creators": [first["authors_or_org"]],
                "canonical_uri": first["url"],
                "license": "; ".join(sorted({item["license"] for item in records})),
                "visibility": "public",
            }
        )
    cell_index: dict[str, dict[str, Any]] = {}
    collect_cells(source_register, cell_index)
    calculation_records = []
    for calculation in content["derivations"]:
        cell_ids = calculation.get("input_cell_ids", [])
        missing = [cell_id for cell_id in cell_ids if cell_id not in cell_index]
        if missing:
            raise ValueError(
                f"calculation input-cell closure drift: {calculation['derivation_id']} {missing}"
            )
        calculation_records.append(
            {
                "derivation": calculation,
                "resolved_input_cells": [cell_index[cell_id] for cell_id in cell_ids],
            }
        )
    source_works.append(
        {
            "key": CALCULATION_WORK_KEY,
            "kind": "dataset",
            "title": "EM-0032 accepted calculation and input-cell register",
            "creators": ["Epistemedia deterministic dossier compiler"],
            "canonical_uri": (
                "https://github.com/yoheinakajima/epistemedia/blob/"
                "700a822f38d00d13cc0661fd577bdb7e6e5b34dd/"
                "research/how-we-know/gpt-4-bar-exam-percentile/candidate-packet.json"
            ),
            "license": (
                "Repository instrumentation under Apache-2.0; accepted source licenses "
                "remain attached to their source editions"
            ),
            "visibility": "public",
        }
    )

    editions = []
    spans = []
    spans_by_source: dict[str, list[str]] = {}
    span_ids: set[str] = set()
    for source in sorted(sources, key=lambda item: item["source_id"]):
        edition_content = {
            "format": "epistemedia-em0032-source-record-projection-v1",
            "accepted_packet_id": ACCEPTED_PACKET_ID,
            "source_record": source,
        }
        encoded = canonical_json(edition_content)
        editions.append(
            {
                "key": dossier_key(source["edition_id"]),
                "work_key": source["work_id"],
                "edition_label": f"Reviewed source-record projection of {source['edition_id']}",
                "media_type": "application/json",
                "retrieved_at": source["retrieved_at"],
                "content": edition_content,
                "content_digest": "sha256:" + sha256_bytes(encoded),
                "content_length": len(encoded),
                "visibility": "public",
            }
        )
        source_spans = []
        for index, span in enumerate(source["spans"]):
            span_id = span["span_id"]
            if span_id in span_ids:
                raise ValueError(f"duplicate span ID: {span_id}")
            span_ids.add(span_id)
            source_spans.append(span_id)
            spans.append(
                {
                    "key": span_id,
                    "edition_key": dossier_key(source["edition_id"]),
                    "locator": {
                        "type": "json-pointer",
                        "pointer": f"/source_record/spans/{index}",
                        "label": span["locator"],
                    },
                    "extent": {"type": "json-value", "value": span},
                    "digest": digest(span),
                    "visibility": "public",
                }
            )
        spans_by_source[source["source_id"]] = source_spans

    calculation_content = {
        "format": "epistemedia-em0032-calculation-register-v1",
        "accepted_packet_id": ACCEPTED_PACKET_ID,
        "records": calculation_records,
    }
    calculation_encoded = canonical_json(calculation_content)
    editions.append(
        {
            "key": CALCULATION_EDITION_KEY,
            "work_key": CALCULATION_WORK_KEY,
            "edition_label": "Exact accepted EM-0032 derivations and resolved input cells",
            "media_type": "application/json",
            "retrieved_at": ASSERTED_AT,
            "content": calculation_content,
            "content_digest": "sha256:" + sha256_bytes(calculation_encoded),
            "content_length": len(calculation_encoded),
            "visibility": "public",
        }
    )
    calculation_span_ids: dict[str, str] = {}
    for index, record in enumerate(calculation_records):
        derivation_id = record["derivation"]["derivation_id"]
        span_key = f"span-calculation-{derivation_id}"
        calculation_span_ids[derivation_id] = span_key
        if span_key in span_ids:
            raise ValueError(f"duplicate calculation span ID: {span_key}")
        span_ids.add(span_key)
        spans.append(
            {
                "key": span_key,
                "edition_key": CALCULATION_EDITION_KEY,
                "locator": {
                    "type": "json-pointer",
                    "pointer": f"/records/{index}",
                    "label": f"accepted derivation and input cells: {derivation_id}",
                },
                "extent": {"type": "json-value", "value": record},
                "digest": digest(record),
                "visibility": "public",
            }
        )

    lineages = []
    for lineage in lineages_input:
        basis = sorted(
            {span for source_id in lineage["source_ids"] for span in spans_by_source[source_id]}
        )
        lineages.append(
            {
                "key": lineage["lineage_id"],
                "status": "known",
                "dimensions": LINEAGE_DIMENSIONS[lineage["root_type"]],
                "depends_on": LINEAGE_DEPENDS_ON[lineage["lineage_id"]],
                "basis_span_keys": basis,
                "assertion_keys": [],
                "note": f"{lineage['unit']}; independent_roots={lineage['independent_roots']}; dependence={' | '.join(lineage['dependence'])}",
                "visibility": "public",
            }
        )
    lineages.extend(
        [
            {
                "key": "lineage-reviewed-source-register",
                "status": "known",
                "dimensions": ["source", "retrieval"],
                "depends_on": sorted(LINEAGE_DEPENDS_ON),
                "basis_span_keys": sorted(span_ids),
                "assertion_keys": [],
                "note": "Relation-derived disclosure-safe projection of the exact reviewed EM-0032 register.",
                "visibility": "public",
            },
            {
                "key": "lineage-evaluation-synthesis",
                "status": "known",
                "dimensions": ["source", "model", "method"],
                "depends_on": sorted(LINEAGE_DEPENDS_ON),
                "basis_span_keys": sorted(span_ids),
                "assertion_keys": [],
                "note": "Policy-relative synthesis over one unchanged source graph; no new empirical root.",
                "visibility": "public",
            },
        ]
    )
    lineages_by_key = {item["key"]: item for item in lineages}

    propositions = [
        {
            "key": claim["claim_id"],
            "text": claim["proposition"],
            "scope": f"Accepted EM-0032 {claim['kind']}; evidence cutoff {source_register['evidence_cutoff']}.",
            "visibility": "public",
        }
        for claim in claims
    ]
    calculation_records_by_id = {
        record["derivation"]["derivation_id"]: record for record in calculation_records
    }
    for calculation in content["derivations"]:
        value = calculation.get("results", calculation.get("result_percentile"))
        record = calculation_records_by_id[calculation["derivation_id"]]
        propositions.append(
            {
                "key": calculation["derivation_id"],
                "text": (
                    f"{calculation['method']}: "
                    f"{json.dumps(value, sort_keys=True, separators=(',', ':'))}; "
                    f"equation={json.dumps(calculation.get('equation'))}; "
                    f"comparison_population={json.dumps(calculation.get('comparison_population'))}; "
                    f"depends_on={json.dumps(calculation.get('depends_on', []), separators=(',', ':'))}."
                ),
                "scope": (
                    "Mechanical reproduction of accepted EM-0032 inputs and exact input-cell "
                    f"register; uncertainty={json.dumps(calculation.get('uncertainty'))}; "
                    f"resolved_input_cells={len(record['resolved_input_cells'])}; not an "
                    "additional model-performance experiment."
                ),
                "visibility": "public",
            }
        )
    propositions.extend(
        [
            {
                "key": "prop-reviewed-source-register",
                "text": f"The accepted packet contains {len(sources)} source editions across {len(works)} source works, {EXPECTED_COUNTS['parent_spans']} parent spans, {len(content['derivations'])} structured calculation records, {len(claims)} bounded claims, {len(lineages_input)} lineage groups, and {len(edges_input)} typed dependence-edge groups.",
                "scope": "Counts are relation-derived from the exact accepted packet.",
                "visibility": "public",
            },
            {
                "key": "prop-encyclopedia-evaluation",
                "text": "GPT-4 received a historical simulated UBE score reported as 298 and approximately 90th percentile, but percentile meaning changes with administration and comparison population.",
                "scope": "Encyclopedia policy documents the historical result while preserving comparison-class and score-version boundaries.",
                "visibility": "public",
            },
            {
                "key": "prop-skeptical-evaluation",
                "text": "Withhold a general 90th-percentile or lawyer-quality claim: the launch comparison distribution is unresolved, the same score ranges from about 68th to 89th in official Illinois sensitivities, and the modeled re-analysis preserves 45/48 and other assumption-dependent results.",
                "scope": "Skeptical policy gives no present-product, practicing-lawyer, or general legal-competence inference.",
                "visibility": "public",
            },
        ]
    )

    derivation_by_id = {item["derivation_id"]: item for item in content["derivations"]}
    parameter_spans = derivation_by_id["derive-martinez-parameters"]["input_span_ids"]
    assertions: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []

    def add_assertion(
        key: str,
        proposition: str,
        lineage: str,
        basis: list[str],
        actor: str,
        relation_type: str = "support",
    ) -> None:
        basis = sorted(set(basis))
        if not basis or any(item not in span_ids for item in basis):
            raise ValueError(f"{key} lacks exact reviewed span closure")
        assertions.append(
            {
                "key": key,
                "proposition_key": proposition,
                "actor": {"id": actor, "kind": "collective"},
                "stance": "asserts",
                "span_keys": basis,
                "lineage_key": lineage,
                "asserted_at": ASSERTED_AT,
                "visibility": "public",
            }
        )
        lineages_by_key[lineage]["assertion_keys"].append(key)
        relations.append(
            {
                "key": f"relation-{key}",
                "relation_type": relation_type,
                "from_ref": basis[0],
                "to_ref": proposition,
                "basis_span_keys": basis,
                "note": "Material proposition closes over the listed exact reviewed spans.",
                "visibility": "public",
            }
        )

    for claim in claims:
        add_assertion(
            f"assertion-{claim['claim_id']}",
            claim["claim_id"],
            CLAIM_LINEAGE[claim["claim_id"]],
            claim["span_ids"],
            "accepted-em0032-reviewed-record",
        )
    for derivation in content["derivations"]:
        basis = [
            *derivation.get("input_span_ids", parameter_spans),
            calculation_span_ids[derivation["derivation_id"]],
        ]
        add_assertion(
            f"assertion-{derivation['derivation_id']}",
            derivation["derivation_id"],
            DERIVATION_LINEAGE[derivation["derivation_id"]],
            basis,
            "em0034-deterministic-calculator",
        )
    add_assertion(
        "assertion-reviewed-source-register",
        "prop-reviewed-source-register",
        "lineage-reviewed-source-register",
        sorted(span_ids),
        "em0034-relation-counter",
    )
    add_assertion(
        "assertion-encyclopedia-evaluation",
        "prop-encyclopedia-evaluation",
        "lineage-evaluation-synthesis",
        [
            "span-openai-v1-table-score",
            "span-katz-vor-score-discrepancy",
            "span-illinois-feb-2018-anchors",
            "span-illinois-jul-2018-anchors",
            "span-martinez-table-45",
            "span-martinez-discussion-48",
        ],
        "em0034-encyclopedia-policy",
    )
    add_assertion(
        "assertion-skeptical-evaluation",
        "prop-skeptical-evaluation",
        "lineage-evaluation-synthesis",
        [
            "span-openai-v1-scoring",
            "span-katz-vor-percentile-boundary",
            "span-illinois-feb-2018-anchors",
            "span-illinois-jul-2018-anchors",
            "span-martinez-model-assumptions",
            "span-martinez-results-45",
            "span-martinez-discussion-48",
            "span-martinez-script-thresholds",
        ],
        "em0034-skeptical-policy",
        "undercutting",
    )

    edge_ids = {edge["edge_id"] for edge in edges_input}
    if len(edge_ids) != 10:
        raise ValueError("typed edge identity drift")
    for edge in sorted(edges_input, key=lambda item: item["edge_id"]):
        basis = sorted({span for evidence in edge["evidence"] for span in evidence["span_ids"]})
        mapped_from = [source_to_lineage.get(item, item) for item in edge["from_ids"]]
        mapped_to = [source_to_lineage.get(item, item) for item in edge["to_ids"]]
        if (
            not mapped_from
            or not mapped_to
            or any(item not in lineages_by_key for item in [*mapped_from, *mapped_to])
        ):
            raise ValueError(f"edge endpoint closure drift: {edge['edge_id']}")
        for relation in expanded_edge_relations(edge, source_to_lineage):
            relations.append(
                {
                    **relation,
                    "relation_type": "dependence",
                    "basis_span_keys": basis,
                    "note": f"accepted_edge_id={edge['edge_id']}; accepted_dimension={edge['edge_type']}; from={','.join(mapped_from)}; to={','.join(mapped_to)}; effects={' | '.join(item['independence_effect'] for item in edge['evidence'])}",
                    "visibility": "public",
                }
            )
    for lineage in lineages:
        lineage["assertion_keys"].sort()

    family_key = "family-gpt4-bar-exam-percentile"
    families = [
        {
            "key": family_key,
            "title": "GPT-4 bar-exam percentile: one score, multiple comparison classes",
            "question": source_register["target_question"],
            "proposition_keys": [item["key"] for item in propositions],
            "assertion_keys": [item["key"] for item in assertions],
            "relation_keys": [item["key"] for item in relations],
            "visibility": "public",
        }
    ]
    evaluations = [
        {
            "key": "evaluation-encyclopedia",
            "claim_family_key": family_key,
            "policy_id": "epistemedia-encyclopedia-v1",
            "frontier": ACCEPTED_PACKET_ID,
            "label": "historical simulated score documented; percentile is comparison-class dependent",
            "reason_codes": [
                "historical-score-preserved",
                "score-297-298-boundary",
                "comparison-populations-separated",
                "current-product-inference-withheld",
            ],
            "visibility": "public",
        },
        {
            "key": "evaluation-skeptical",
            "claim_family_key": family_key,
            "policy_id": "epistemedia-skeptical-v1",
            "frontier": ACCEPTED_PACKET_ID,
            "label": "withhold general 90th-percentile and lawyer-quality claims",
            "reason_codes": [
                "launch-distribution-unresolved",
                "administration-sensitivity-material",
                "martinez-assumptions-material",
                "45-48-conflict-retained",
                "no-practicing-lawyer-comparator",
            ],
            "visibility": "public",
        },
    ]
    material = {
        "format": DOSSIER_FORMAT,
        "title": "Case 003: What GPT-4's 90th-percentile bar-exam claim compared",
        "question": source_register["target_question"],
        "scope": f"Evidence through {source_register['evidence_cutoff']}; disclosure-safe candidate derived only from accepted EM-0032 bytes. It is not admitted, not featured, not live, and not published, and it does not describe current model behavior or general legal competence.",
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
