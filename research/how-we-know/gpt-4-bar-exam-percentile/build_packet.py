"""Build the deterministic EM-0032 GPT-4 bar-exam research packet.

Network retrieval is deliberately outside deterministic validation. The capture
subcommand converts already-downloaded authoritative metadata into a frozen
89-file inventory. The default build consumes only committed inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import NormalDist, stdev
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parent
SOURCE_RECORDS = PACKET_ROOT / "source-records.json"
ARTIFACT_INVENTORY = PACKET_ROOT / "artifact-inventory.json"
GIT_BLOB_SEARCH_MANIFEST = PACKET_ROOT / "git-blob-search-manifest.json"
CANDIDATE_PACKET = PACKET_ROOT / "candidate-packet.json"

EXPECTED_CORE_SOURCE_COUNT = 15
EXPECTED_SOURCE_COUNT = 19
EXPECTED_ARTIFACT_ROOT_COUNTS = {
    "artifact-root-katz-git": 78,
    "artifact-root-katz-figshare": 1,
    "artifact-root-martinez-osf": 10,
}
EXPECTED_OSF_TOTAL_BYTES = 34_906_996
EXPECTED_PARENT_SPAN_COUNT = 35
REQUIRED_LINEAGE_EDGE_TYPES = {
    "data",
    "model",
    "author-social",
    "method",
    "material",
    "benchmark",
    "score",
    "comparison-class",
    "citation",
    "derivation",
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


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": digest_bytes(payload)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def span_unit_ids(span: dict[str, Any]) -> list[str]:
    return [
        *[item["segment_id"] for item in span.get("segments", [])],
        *[item["cell_id"] for item in span.get("cells", [])],
        *[item["line_id"] for item in span.get("code_lines", [])],
    ]


def span_extent(span: dict[str, Any]) -> Any:
    if "quote" in span:
        return {"quote": span["quote"]}
    return {
        key: span[key]
        for key in ("segments", "cells", "code_lines")
        if key in span
    }


def inventory_id(content: dict[str, Any]) -> str:
    return f"em:artifact-inventory:sha256:{digest_bytes(canonical_bytes(content))}"


def packet_id(content: dict[str, Any]) -> str:
    return f"em:research-packet:sha256:{digest_bytes(canonical_bytes(content))}"


def capture_inventory(args: argparse.Namespace) -> dict[str, Any]:
    katz_tree = load(args.katz_tree)
    figshare = load(args.figshare)
    osf_node = load(args.osf_node)
    osf_root = load(args.osf_root)
    osf_prompting = load(args.osf_prompting)
    osf_analysis = load(args.osf_analysis)
    osf_data = load(args.osf_data)

    require(
        katz_tree.get("sha") == "810bd4a9a8ffb51e457715d2312d28d3e9657240",
        "Katz Git tree identity drift",
    )
    require(katz_tree.get("truncated") is False, "Katz Git tree is truncated")
    git_blobs = [item for item in katz_tree["tree"] if item.get("type") == "blob"]
    require(len(git_blobs) == 78, "Katz Git blob count drift")

    artifacts: list[dict[str, Any]] = []
    for item in sorted(git_blobs, key=lambda value: value["path"]):
        artifacts.append(
            {
                "artifact_id": f"katz-git:path-sha256:{digest_bytes(item['path'].encode())}",
                "artifact_root_id": "artifact-root-katz-git",
                "path": item["path"],
                "bytes": item["size"],
                "digest_algorithm": "git-blob-sha1",
                "digest": item["sha"],
                "metadata_url": item["url"],
                "retrieval_status": "metadata-verified",
                "license_treatment": "no repository license; link or quote minimally",
                "independent_evidence_credit": 0,
            }
        )

    require(figshare.get("id") == 25018513, "Figshare article identity drift")
    require(figshare.get("doi") == "10.6084/m9.figshare.25018513.v1", "Figshare DOI drift")
    require(len(figshare.get("files", [])) == 1, "Figshare file count drift")
    figshare_file = figshare["files"][0]
    require(figshare_file["size"] == 178633, "Figshare file bytes drift")
    require(
        figshare_file["computed_md5"] == "71f8e1e205fb05f847f5a894cc14cf40",
        "Figshare file MD5 drift",
    )
    artifacts.append(
        {
            "artifact_id": f"katz-figshare:{figshare_file['id']}",
            "artifact_root_id": "artifact-root-katz-figshare",
            "path": figshare_file["name"],
            "bytes": figshare_file["size"],
            "digest_algorithm": "md5",
            "digest": figshare_file["computed_md5"],
            "captured_sha256": ("bb712ea0b668e6e143aef39103f3e03e43e5b916015efb301a5e4a1edb2aafc5"),
            "download_url": figshare_file["download_url"],
            "retrieval_status": "artifact-independently-retrieved",
            "license_treatment": "CC BY 4.0 at article/file scope",
            "independent_evidence_credit": 0,
        }
    )

    require(osf_node["data"]["id"] == "c8ygu", "OSF node identity drift")
    require(osf_node["data"]["attributes"]["public"] is False, "OSF public flag drift")
    require(
        osf_node["data"]["relationships"].get("license", {}).get("data") is None,
        "OSF node license drift",
    )
    osf_files = []
    for document in (osf_root, osf_prompting, osf_analysis, osf_data):
        values = document["data"] if isinstance(document["data"], list) else []
        osf_files.extend(
            item for item in values if item.get("attributes", {}).get("kind") == "file"
        )
    require(len(osf_files) == 10, "OSF file count drift")
    require(
        sum(item["attributes"]["size"] for item in osf_files) == EXPECTED_OSF_TOTAL_BYTES,
        "OSF total bytes drift",
    )
    for item in sorted(osf_files, key=lambda value: value["attributes"]["name"]):
        attributes = item["attributes"]
        digest = attributes["extra"]["hashes"]["sha256"]
        artifacts.append(
            {
                "artifact_id": f"martinez-osf:{item['id']}",
                "artifact_root_id": "artifact-root-martinez-osf",
                "path": attributes["name"],
                "bytes": attributes["size"],
                "digest_algorithm": "sha256",
                "digest": digest,
                "download_url": item["links"]["download"],
                "retrieval_status": "metadata-verified",
                "license_treatment": (
                    "anonymous view-only capability; no node/file license confirmed"
                ),
                "independent_evidence_credit": 0,
            }
        )

    content = {
        "schema": "https://epistemedia.org/research/artifact-inventory-v1.json",
        "task_id": "EM-0032",
        "captured_at": "2026-08-27T05:48:35Z",
        "artifact_roots": [
            {
                "artifact_root_id": "artifact-root-katz-git",
                "source_id": "source-katz-git-snapshot",
                "commit_sha": "90997f740c7197f3f300b013e4345e2ad5621f96",
                "tree_sha": "810bd4a9a8ffb51e457715d2312d28d3e9657240",
                "expected_files": 78,
                "independence": "same Katz/OpenAI experiment root",
            },
            {
                "artifact_root_id": "artifact-root-katz-figshare",
                "source_id": "source-katz-figshare",
                "expected_files": 1,
                "independence": "same Katz/OpenAI experiment root",
            },
            {
                "artifact_root_id": "artifact-root-martinez-osf",
                "source_id": "source-martinez-osf",
                "expected_files": 10,
                "independence": "same Martinez re-analysis root",
            },
        ],
        "capture_receipts": [
            {"name": args.katz_tree.name, **identity(args.katz_tree)},
            {"name": args.figshare.name, **identity(args.figshare)},
            {"name": args.osf_node.name, **identity(args.osf_node)},
            {"name": args.osf_root.name, **identity(args.osf_root)},
            {"name": args.osf_prompting.name, **identity(args.osf_prompting)},
            {"name": args.osf_analysis.name, **identity(args.osf_analysis)},
            {"name": args.osf_data.name, **identity(args.osf_data)},
        ],
        "artifacts": artifacts,
        "limitations": [
            (
                "Git object IDs bind blobs using Git's SHA-1 object identity; the "
                "separate pinned blob-search manifest also binds all 78 bodies by "
                "SHA-256, searches 72 UTF-8 bodies, and retains 6 binary bodies as "
                "no-text-search records."
            ),
            (
                "Figshare supplies MD5; the sole PDF was also independently retrieved "
                "and SHA-256-bound."
            ),
            (
                "OSF supplies SHA-256 metadata, but only three quote-minimal files were "
                "independently downloaded; no unlicensed full artifacts are committed."
            ),
            (
                "The inventory verifies file identity and completeness, not the "
                "scientific validity of every artifact."
            ),
        ],
    }
    return {"inventory_id": inventory_id(content), "content": content}


def july_mbe_distribution() -> list[int]:
    return [score for score, count in JULY_MBE_BINS for _ in range(count)]


def conditional_percentile(
    distribution: NormalDist,
    score: float,
    lower_bound: float,
) -> float:
    numerator = distribution.cdf(score) - distribution.cdf(lower_bound)
    denominator = 1 - distribution.cdf(lower_bound)
    return 100 * numerator / denominator


def build_derivations() -> list[dict[str, Any]]:
    interpolation_specs = [
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
    derivations = []
    for derivation_id, at_290, at_300, span_id, cell_ids in interpolation_specs:
        result = at_290 + ((298 - 290) / (300 - 290)) * (at_300 - at_290)
        derivations.append(
            {
                "derivation_id": derivation_id,
                "method": "reviewer sensitivity only: linear interpolation",
                "equation": "p298 = p290 + ((298 - 290) / 10) * (p300 - p290)",
                "inputs": {"score": 298, "p290": at_290, "p300": at_300},
                "input_span_ids": [span_id],
                "input_cell_ids": cell_ids,
                "result_percentile": result,
                "uncertainty": (
                    "Neither Illinois nor OpenAI disclosed this interpolation; it cannot "
                    "be attributed as the launch method."
                ),
            }
        )

    mbe_values = july_mbe_distribution()
    mbe_sd = stdev(mbe_values)
    z_27 = NormalDist().inv_cdf(0.27)
    ube_sd = (266.0 - 287.6) / z_27
    ube_distribution = NormalDist(287.6, ube_sd)
    mbe_distribution = NormalDist(143.8, mbe_sd)
    derivations.extend(
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
                "results": {
                    "z_at_0_27": z_27,
                    "derived_ube_sd": ube_sd,
                    "sample_mbe_sd": mbe_sd,
                },
                "uncertainty": (
                    "The UBE distribution is inferred from aggregate inputs and normality; "
                    "the essay mean/SD are assumed rather than observed."
                ),
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
                "result_percentile": conditional_percentile(
                    ube_distribution,
                    298,
                    270,
                ),
                "comparison_population": "modeled first-time scores at or above 270",
                "depends_on": ["derive-martinez-parameters"],
                "uncertainty": (
                    "The script uses 270 for this filter after using New York's 266 "
                    "cutoff to infer UBE SD."
                ),
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
                "result_percentile": conditional_percentile(
                    mbe_distribution,
                    158,
                    135,
                ),
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
                "result_percentile": conditional_percentile(
                    mbe_distribution,
                    140,
                    135,
                ),
                "comparison_population": "modeled essay scores at or above 135",
                "depends_on": ["derive-martinez-parameters"],
            },
        ]
    )
    return derivations


def validate_inputs(
    source_records: dict[str, Any],
    artifact_inventory: dict[str, Any],
    git_blob_search: dict[str, Any],
) -> None:
    sources = source_records["sources"]
    require(len(sources) == EXPECTED_SOURCE_COUNT, "source object count drift")
    source_ids = [item["source_id"] for item in sources]
    require(len(source_ids) == len(set(source_ids)), "duplicate source ID")
    require(
        len(source_records["core_source_ids"]) == EXPECTED_CORE_SOURCE_COUNT,
        "core source count drift",
    )
    require(
        set(source_records["core_source_ids"])
        == {item["source_id"] for item in sources if item["core"]},
        "core source set drift",
    )
    for source in sources:
        require(source["captured_bytes"] > 0, f"missing capture bytes: {source['source_id']}")
        require(
            len(source["captured_sha256"]) == 64,
            f"invalid capture digest: {source['source_id']}",
        )

    spans = [span for source in sources for span in source["spans"]]
    span_ids = [span["span_id"] for span in spans]
    require(len(spans) == EXPECTED_PARENT_SPAN_COUNT, "parent span count drift")
    require(len(span_ids) == len(set(span_ids)), "duplicate span ID")
    unit_ids = [unit_id for span in spans for unit_id in span_unit_ids(span)]
    require(len(unit_ids) == len(set(unit_ids)), "duplicate span unit ID")
    require(not set(span_ids).intersection(unit_ids), "parent and unit span IDs overlap")
    allowed_formats = {
        "exact-contiguous-text",
        "exact-segments",
        "table-cell-transcription",
        "code-segment-transcription",
        "code-table-transcription",
    }
    for span in spans:
        span_format = span.get("format", "exact-contiguous-text")
        require(span_format in allowed_formats, f"unknown span format: {span['span_id']}")
        require(bool(span_extent(span)), f"span lacks exact extent: {span['span_id']}")
        if span_format == "exact-contiguous-text":
            require(
                isinstance(span.get("quote"), str) and span["quote"].strip(),
                f"exact span lacks quote: {span['span_id']}",
            )
        else:
            require("quote" not in span, f"transcribed span has fake quote: {span['span_id']}")
            require(span_unit_ids(span), f"transcribed span lacks typed units: {span['span_id']}")

    derivations = build_derivations()
    derivation_ids = {item["derivation_id"] for item in derivations}
    for claim in source_records["claims"]:
        require(claim["span_ids"], f"claim lacks spans: {claim['claim_id']}")
        require(
            set(claim["span_ids"]).issubset(span_ids),
            f"claim has unknown spans: {claim['claim_id']}",
        )
        require(
            set(claim.get("derivation_ids", [])).issubset(derivation_ids),
            f"claim has unknown derivation: {claim['claim_id']}",
        )
    for derivation in derivations:
        require(
            set(derivation.get("input_span_ids", [])).issubset(span_ids),
            f"derivation has unknown parent span: {derivation['derivation_id']}",
        )
        require(
            set(derivation.get("input_cell_ids", [])).issubset(unit_ids),
            f"derivation has unknown cell: {derivation['derivation_id']}",
        )
    parameters = next(
        item for item in derivations if item["derivation_id"] == "derive-martinez-parameters"
    )
    require(
        parameters["input_cell_ids"][: len(JULY_MBE_CELL_IDS)] == JULY_MBE_CELL_IDS,
        "July MBE cell provenance drift",
    )

    inventory_content = artifact_inventory["content"]
    require(
        artifact_inventory["inventory_id"] == inventory_id(inventory_content),
        "artifact inventory ID drift",
    )
    artifacts = inventory_content["artifacts"]
    require(len(artifacts) == 89, "artifact inventory must contain 89 files")
    artifact_ids = [item["artifact_id"] for item in artifacts]
    require(len(artifact_ids) == len(set(artifact_ids)), "duplicate artifact ID")
    root_counts = {
        root_id: sum(item["artifact_root_id"] == root_id for item in artifacts)
        for root_id in EXPECTED_ARTIFACT_ROOT_COUNTS
    }
    require(root_counts == EXPECTED_ARTIFACT_ROOT_COUNTS, "artifact root counts drift")
    require(
        all(item["independent_evidence_credit"] == 0 for item in artifacts),
        "mechanical artifacts must not receive independent evidence credit",
    )
    osf_bytes = sum(
        item["bytes"]
        for item in artifacts
        if item["artifact_root_id"] == "artifact-root-martinez-osf"
    )
    require(osf_bytes == EXPECTED_OSF_TOTAL_BYTES, "OSF artifact bytes drift")

    search_content = git_blob_search["content"]
    require(
        search_content["commit_sha"]
        == "90997f740c7197f3f300b013e4345e2ad5621f96",
        "Git body-search commit drift",
    )
    require(
        search_content["tree_sha"]
        == "810bd4a9a8ffb51e457715d2312d28d3e9657240",
        "Git body-search tree drift",
    )
    require(search_content["blob_count"] == 78, "Git body-search blob count drift")
    require(search_content["text_body_count"] == 72, "Git body-search text count drift")
    require(search_content["binary_body_count"] == 6, "Git body-search binary count drift")
    require(
        git_blob_search["manifest_id"]
        == f"em:git-blob-search:sha256:{digest_bytes(canonical_bytes(search_content))}",
        "Git body-search manifest ID drift",
    )
    require(
        source_records["negative_searches"][0]["git_blob_search_manifest_id"]
        == git_blob_search["manifest_id"],
        "negative-search manifest binding drift",
    )
    git_artifacts = {
        item["path"]: item
        for item in artifacts
        if item["artifact_root_id"] == "artifact-root-katz-git"
    }
    require(
        {row["path"] for row in search_content["rows"]} == set(git_artifacts),
        "Git body-search artifact coverage drift",
    )
    for row in search_content["rows"]:
        artifact = git_artifacts[row["path"]]
        require(row["bytes"] == artifact["bytes"], "Git body-search byte drift")
        require(row["git_blob_sha1"] == artifact["digest"], "Git body-search SHA-1 drift")

    lineages = source_records["lineages"]
    lineage_ids = {lineage["lineage_id"] for lineage in lineages}
    require(len(lineage_ids) == 5, "lineage root count drift")
    require(
        {lineage["root_type"] for lineage in lineages}
        == {"performance", "analysis", "comparison-data"},
        "lineage root-type drift",
    )
    lineage_source_ids = {
        source_id for lineage in lineages for source_id in lineage["source_ids"]
    }
    require(lineage_source_ids == set(source_ids), "source-to-lineage closure drift")
    source_span_ids = {
        source["source_id"]: {span["span_id"] for span in source["spans"]}
        for source in sources
    }
    endpoints = set(source_ids) | lineage_ids
    edges = source_records["lineage_edges"]
    edge_ids = [edge["edge_id"] for edge in edges]
    require(len(edges) == 10, "lineage edge count drift")
    require(len(edge_ids) == len(set(edge_ids)), "duplicate lineage edge ID")
    require(
        {edge["edge_type"] for edge in edges} == REQUIRED_LINEAGE_EDGE_TYPES,
        "lineage edge-type drift",
    )
    for edge in edges:
        require(
            set(edge["from_ids"] + edge["to_ids"]).issubset(endpoints),
            f"lineage edge endpoint drift: {edge['edge_id']}",
        )
        require(edge["evidence"], f"lineage edge lacks evidence: {edge['edge_id']}")
        for evidence in edge["evidence"]:
            source_id = evidence["source_id"]
            require(source_id in source_span_ids, f"unknown edge source: {edge['edge_id']}")
            require(
                set(evidence["span_ids"]).issubset(source_span_ids[source_id]),
                f"edge span ownership drift: {edge['edge_id']}",
            )
            require(evidence["finding"].strip(), f"edge finding blank: {edge['edge_id']}")
            require(
                evidence["independence_effect"].strip(),
                f"edge independence effect blank: {edge['edge_id']}",
            )
    recommendation = source_records["recommendation"]
    require(recommendation["author"] in {"GO", "HOLD", "FAIL"}, "invalid recommendation")
    require(
        recommendation["independent_review"] == "pending",
        "source record must remain pending until independent review",
    )


def build_packet() -> dict[str, Any]:
    source_records = load(SOURCE_RECORDS)
    artifact_inventory = load(ARTIFACT_INVENTORY)
    git_blob_search = load(GIT_BLOB_SEARCH_MANIFEST)
    validate_inputs(source_records, artifact_inventory, git_blob_search)
    content = {
        "schema": "https://epistemedia.org/research/gpt4-bar-percentile-packet-v1.json",
        "task_id": "EM-0032",
        "evidence_cutoff": source_records["evidence_cutoff"],
        "target_question": source_records["target_question"],
        "input_receipts": {
            "source_records": identity(SOURCE_RECORDS),
            "artifact_inventory": identity(ARTIFACT_INVENTORY),
            "git_blob_search_manifest": identity(GIT_BLOB_SEARCH_MANIFEST),
        },
        "source_records": source_records,
        "artifact_inventory": artifact_inventory,
        "git_blob_search_manifest": git_blob_search,
        "derivations": build_derivations(),
        "counts": {
            "sources": len(source_records["sources"]),
            "core_sources": len(source_records["core_source_ids"]),
            "parent_spans": len(
                [span for source in source_records["sources"] for span in source["spans"]]
            ),
            "typed_span_units": len(
                [
                    unit_id
                    for source in source_records["sources"]
                    for span in source["spans"]
                    for unit_id in span_unit_ids(span)
                ]
            ),
            "calculations": len(build_derivations()),
            "lineage_roots": len(source_records["lineages"]),
            "lineage_edges": len(source_records["lineage_edges"]),
            "git_blob_bodies": git_blob_search["content"]["blob_count"],
            "git_blob_text_bodies": git_blob_search["content"]["text_body_count"],
            "git_blob_binary_bodies": git_blob_search["content"]["binary_body_count"],
        },
        "decision": {
            "author_recommendation": source_records["recommendation"]["author"],
            "independent_review_status": "pending",
            "meaning": source_records["recommendation"]["scope"],
        },
    }
    return {"packet_id": packet_id(content), "content": content}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--capture-artifacts", action="store_true")
    parser.add_argument("--katz-tree", type=Path)
    parser.add_argument("--figshare", type=Path)
    parser.add_argument("--osf-node", type=Path)
    parser.add_argument("--osf-root", type=Path)
    parser.add_argument("--osf-prompting", type=Path)
    parser.add_argument("--osf-analysis", type=Path)
    parser.add_argument("--osf-data", type=Path)
    args = parser.parse_args()

    if args.capture_artifacts:
        for field in (
            "katz_tree",
            "figshare",
            "osf_node",
            "osf_root",
            "osf_prompting",
            "osf_analysis",
            "osf_data",
        ):
            require(getattr(args, field) is not None, f"--{field.replace('_', '-')} is required")
        inventory = capture_inventory(args)
        if args.check:
            require(ARTIFACT_INVENTORY.is_file(), "artifact inventory missing")
            require(load(ARTIFACT_INVENTORY) == inventory, "artifact inventory drift")
        else:
            write_json(ARTIFACT_INVENTORY, inventory)
        print(
            json.dumps(
                {
                    "inventory_id": inventory["inventory_id"],
                    "files": len(inventory["content"]["artifacts"]),
                },
                sort_keys=True,
            )
        )
        return

    packet = build_packet()
    if args.check:
        require(CANDIDATE_PACKET.is_file(), "candidate packet missing")
        require(load(CANDIDATE_PACKET) == packet, "candidate packet drift")
    else:
        write_json(CANDIDATE_PACKET, packet)
    print(
        json.dumps(
            {
                "packet_id": packet["packet_id"],
                "sources": len(packet["content"]["source_records"]["sources"]),
                "core_sources": len(packet["content"]["source_records"]["core_source_ids"]),
                "artifacts": len(packet["content"]["artifact_inventory"]["content"]["artifacts"]),
                "author_recommendation": packet["content"]["decision"]["author_recommendation"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
