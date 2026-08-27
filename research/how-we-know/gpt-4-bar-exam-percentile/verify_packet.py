"""Fail-closed verification for the EM-0032 candidate research packet."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import NormalDist, stdev
from typing import Any

from build_packet import (
    JULY_MBE_BINS,
    REQUIRED_LINEAGE_EDGE_TYPES,
    build_packet,
    canonical_bytes,
)
from normalize_html_visible_text import normalize_html_visible_text
from verify_git_blob_search import validate_manifest as validate_git_blob_manifest

PACKET_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKET_ROOT.parents[2]
SOURCE_RECORDS = PACKET_ROOT / "source-records.json"
ARTIFACT_INVENTORY = PACKET_ROOT / "artifact-inventory.json"
GIT_BLOB_SEARCH_MANIFEST = PACKET_ROOT / "git-blob-search-manifest.json"
CANDIDATE_PACKET = PACKET_ROOT / "candidate-packet.json"
DEFAULT_REVIEW_RECEIPT = PACKET_ROOT / "independent-review-receipt.json"
REPOSITORY_URL = "https://github.com/yoheinakajima/epistemedia"
REVIEW_FORMAT = "epistemedia-independent-research-review-v1"
AUTHOR_IDS = {"codex-builder"}
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
HTML_SEMANTIC_SOURCE_IDS = {
    "source-ncbe-first-repeat-2022",
    "source-ncbe-mbe-2022",
    "source-ncbe-snapshot-2022",
    "source-ncbe-ube-mechanics",
    "source-reshetar-testing-column-2022",
}

EXPECTED_PACKET_ID = (
    "em:research-packet:sha256:9a305d480fa08b90a1fc605963a6ec90974e848c96a74668fa7f1844e579be6e"
)
EXPECTED_SOURCE_RECORDS = {
    "bytes": 64_380,
    "sha256": "899bbdcc0a5cfcf1e569427aaa89a5fcae8d8ebcca44b99de5923337790836d8",
}
EXPECTED_ARTIFACT_INVENTORY = {
    "bytes": 62_565,
    "sha256": "f9e45045831a15fcb40c7f542c73651e5dc63ba081b145d00260bee91192c25b",
}
EXPECTED_GIT_BLOB_SEARCH = {
    "bytes": 51_950,
    "sha256": "708657f61bc759f3a5b439affde1a677177859b50a8bc960012b81dcebcdb122",
}
EXPECTED_GIT_BLOB_SEARCH_ID = (
    "em:git-blob-search:sha256:545908f30ba849c42c860185f92612f4d52a53b4f13b3c3ca5672213e23ba996"
)
EXPECTED_CANDIDATE_PACKET = {
    "bytes": 210_541,
    "sha256": "b107c7b61226af46142df6b104bb620d7dee2e44ada7c8072fad4def16782f5d",
}
EXPECTED_ARTIFACT_INVENTORY_ID = (
    "em:artifact-inventory:sha256:17f52a5509fded7e75b08201f61122d09c7626443857c94f8727c85c0824e61c"
)
EXPECTED_SOURCE_IDS = {
    "source-illinois-feb-2018",
    "source-illinois-feb-2019",
    "source-illinois-jul-2018",
    "source-katz-figshare",
    "source-katz-git-snapshot",
    "source-katz-ssrn",
    "source-katz-vor",
    "source-reshetar-testing-column-2022",
    "source-martinez-analysis-new",
    "source-martinez-osf",
    "source-martinez-vor",
    "source-ncbe-first-repeat-2022",
    "source-ncbe-mbe-2022",
    "source-ncbe-snapshot-2022",
    "source-ncbe-ube-2022",
    "source-ncbe-ube-mechanics",
    "source-ny-passrates-2022",
    "source-openai-v1",
    "source-openai-v6",
}
EXPECTED_LINEAGE_EDGE_IDS = {
    "edge-author-social-collaboration",
    "edge-benchmark-illinois-charts",
    "edge-citation-katz-to-martinez",
    "edge-comparison-class-first-time-passers",
    "edge-data-reported-score-reuse",
    "edge-derivation-comparison-inputs",
    "edge-material-shared-exam-items",
    "edge-method-single-free-response-run",
    "edge-model-historical-snapshots",
    "edge-score-component-composite",
}
EXPECTED_SOURCE_CAPTURE_IDENTITIES = {
    "source-openai-v1": (
        5_229_731,
        "053056a10114d22e4c47b6b5be25e54c320b5f1beeae7466e8638dac0f5f5f66",
    ),
    "source-openai-v6": (
        5_245_564,
        "c33a66dadca2388d7b172d6293b00dc32b71110c6f38fafe0d41112e61be7774",
    ),
    "source-katz-vor": (
        117_084,
        "d5a7b3d5cba67eb070f13e5e72700a11b2f081af664aad197acb37427aa47264",
    ),
    "source-katz-ssrn": (
        16_942,
        "146a68d349dae70ece09fefe79cd04808a40afb8f1e19a4c63941678330cb90b",
    ),
    "source-katz-git-snapshot": (
        29_311,
        "9541fd9b9677738aae5fac3048eaa5efc2a23ff5a97ecedec74492eb451e86fb",
    ),
    "source-katz-figshare": (
        4_917,
        "ce59483bb4dae6871cadf3afa9d650e00d4c524b75083f0c43706436d1220ba6",
    ),
    "source-illinois-feb-2018": (
        41_491,
        "500d734d54cfaae23b94a988469a8a626fc71abefd5793424bfbe83aabe9e1b7",
    ),
    "source-illinois-jul-2018": (
        41_047,
        "9b4251dc1147789eceb9e4e4b3cbdb4e98ab4634f286e8f4d8917d4e0970a299",
    ),
    "source-illinois-feb-2019": (
        40_394,
        "b313a414728db06d9170f79f0177927a3343e3744fc39ba3cadaff1fddc27faa",
    ),
    "source-ncbe-ube-mechanics": (
        63_952,
        "359f8d4e94e128480fe474f07e87a0b019ff20f4cd6041d0b7bfe904b8a84628",
    ),
    "source-ncbe-mbe-2022": (
        278_417,
        "f21c45a6e9d1c1b3a5a538ff4bc5b28751928fac53cb5d174e6ec64488c6b784",
    ),
    "source-ncbe-snapshot-2022": (
        188_472,
        "391deeac882bfe4dfb69a58e852c465ffbcc9e1d2e0a8557208f82cf795309a0",
    ),
    "source-ncbe-first-repeat-2022": (
        372_700,
        "d5edc89f2c781ab7a795602cdc4a6b42b3da457f13972c8660db9a2b976df448",
    ),
    "source-martinez-vor": (
        888_663,
        "bbab759cb88e93a5216936af1edb2726eb8eb0edde3148d18c1093bed9226e76",
    ),
    "source-martinez-osf": (
        3_696,
        "06c756ef9d72bce0e92e821917bd5ca02fa1d5089b965689a2dd4f4d28f15bf5",
    ),
    "source-ncbe-ube-2022": (
        260_280,
        "eb3e0b45cd4496cfc15669c267f25107c27e31489ece46dd43def1356a966e52",
    ),
    "source-ny-passrates-2022": (
        65_751,
        "9cddfa2dbe71b11e01a5ee24a328952cdb8c6a81ee140e83a8a1713aa4c17088",
    ),
    "source-reshetar-testing-column-2022": (
        218_131,
        "174a5adc50f0235f70ebea3b6c4ed85fbe91df8c18d8144286876fe6b95e70bd",
    ),
    "source-martinez-analysis-new": (
        12_730,
        "e73b60d3bcba8075b8e513f53d079541ca11b32fa68a8a1201a6442644add588",
    ),
}
EXPECTED_SEMANTIC_CAPTURES = {
    "source-katz-git-snapshot": (
        23_967,
        "77eed8a0e0bacf7ded2368209120bd7d2e1390419ece9421373bc9c696f83105",
    ),
    "source-reshetar-testing-column-2022": (
        12_498,
        "2222ea3b0110bcc02c189bb5d79ee9264ada557b2edae09077d985d472da92f6",
    ),
    "source-martinez-osf": (
        3_697,
        "b18212bf119cd65f826d137a1306a266b446de193618822fcdcea3eae0903a6f",
    ),
    "source-ncbe-first-repeat-2022": (
        18_887,
        "28a6ddf863f104d59b23674ed11a46951b87e088f4774c277f642e6d077e582d",
    ),
    "source-ncbe-mbe-2022": (
        4_767,
        "d738481ea3a38e6da39748d47aacc1291112766ec4720917ad0529a02a1f491e",
    ),
    "source-ncbe-snapshot-2022": (
        5_449,
        "d1373f31770be2bbecb821047ef0ea95cb0c50e6088e0c26322de921cf797917",
    ),
    "source-ncbe-ube-mechanics": (
        1_123,
        "c7484bfc7a063ddde35b93e488f95c0e33894106e5f90df2b66cab9cb18837b7",
    ),
}


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    require(isinstance(value, dict), f"{path}: root must be an object")
    return value


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_value(value: Any) -> str:
    return sha256(canonical_bytes(value))


def identity(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": sha256(payload)}


def collapsed_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def span_text_values(span: dict[str, Any]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if isinstance(span.get("quote"), str):
        values.append((span["span_id"], span["quote"]))
    for field, id_field in (
        ("segments", "segment_id"),
        ("cells", "cell_id"),
        ("code_lines", "line_id"),
    ):
        for row in span.get(field, []):
            if isinstance(row.get("text"), str):
                values.append((row[id_field], row["text"]))
    return values


def verify_html_captures(
    source_records: dict[str, Any],
    captures_dir: Path | None,
    *,
    require_captures: bool,
) -> bool:
    if captures_dir is None:
        require(not require_captures, "--captures-dir is required with --require-captures")
        return False
    require(captures_dir.is_dir(), "HTML captures directory missing")
    sources = {source["source_id"]: source for source in source_records["sources"]}
    actual_names = {path.name for path in captures_dir.glob("*.body")}
    expected_names = {f"{source_id}.body" for source_id in HTML_SEMANTIC_SOURCE_IDS}
    require(actual_names == expected_names, "HTML capture file set drift")
    for source_id in sorted(HTML_SEMANTIC_SOURCE_IDS):
        source = sources[source_id]
        path = captures_dir / f"{source_id}.body"
        payload = path.read_bytes()
        allowed_identities = {
            (source["captured_bytes"], source["captured_sha256"]),
            *{
                (row["bytes"], row["sha256"])
                for row in source.get("capture_observations", [])
            },
        }
        require(
            (len(payload), sha256(payload)) in allowed_identities,
            f"unrecorded HTML capture identity: {source_id}",
        )
        semantic = source["semantic_capture"]
        normalized = normalize_html_visible_text(payload, root_id=semantic["root_id"])
        require(len(normalized) == semantic["bytes"], f"semantic bytes drift: {source_id}")
        require(sha256(normalized) == semantic["sha256"], f"semantic hash drift: {source_id}")
        visible_text = normalized.decode("utf-8")
        for span in source["spans"]:
            for unit_id, value in span_text_values(span):
                require(
                    collapsed_text(value) in visible_text,
                    f"semantic extent missing: {source_id}/{unit_id}",
                )
    return True


def git_bytes(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if check and result.returncode != 0:
        fail(
            f"git {' '.join(args)} failed: "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def git_text(*args: str, check: bool = True) -> str:
    return git_bytes(*args, check=check).decode().strip()


def require_exact_fields(value: Any, fields: set[str], context: str) -> None:
    require(isinstance(value, dict), f"{context}: must be an object")
    actual = set(value)
    require(actual == fields, f"{context}: fields differ: {sorted(actual ^ fields)}")


def require_string(value: Any, context: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{context}: must be a string")
    return value


def require_sha256(value: Any, context: str) -> str:
    require_string(value, context)
    require(bool(re.fullmatch(r"[0-9a-f]{64}", value)), f"{context}: invalid SHA-256")
    return value


def require_commit(value: Any, context: str) -> str:
    require_string(value, context)
    require(bool(re.fullmatch(r"[0-9a-f]{40}", value)), f"{context}: invalid Git identity")
    return value


def require_timestamp(value: Any, context: str) -> datetime:
    require_string(value, context)
    require(value.endswith("Z"), f"{context}: must use UTC Z suffix")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"{context}: invalid timestamp: {exc}")
    require(parsed.utcoffset() == timedelta(0), f"{context}: must be UTC")
    require(
        parsed <= datetime.now(UTC) + timedelta(minutes=5),
        f"{context}: timestamp is in the future",
    )
    return parsed


def close(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return abs(actual - expected) <= tolerance


def output_value(derivation: dict[str, Any]) -> Any:
    if "results" in derivation:
        return derivation["results"]
    require("result_percentile" in derivation, "derivation lacks output")
    return derivation["result_percentile"]


def input_value(derivation: dict[str, Any]) -> dict[str, Any]:
    return {
        key: derivation.get(key)
        for key in (
            "method",
            "equation",
            "inputs",
            "input_span_ids",
            "input_cell_ids",
            "depends_on",
            "comparison_population",
        )
        if key in derivation
    }


def collect_review_records(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    content = packet["content"]
    sources: dict[str, Any] = {}
    spans: dict[str, Any] = {}
    for source in content["source_records"]["sources"]:
        source_id = source["source_id"]
        semantic = source.get("semantic_capture")
        sources[source_id] = {
            "record_sha256": digest_value(source),
            "semantic_capture_sha256": semantic["sha256"] if semantic else None,
        }
        for span in source["spans"]:
            parent_id = span["span_id"]
            spans[parent_id] = {
                "source_id": source_id,
                "record_sha256": digest_value(span),
                "parent_span_id": parent_id,
                "unit_type": "parent",
            }
            for key, id_key, unit_type in (
                ("segments", "segment_id", "segment"),
                ("cells", "cell_id", "cell"),
                ("code_lines", "line_id", "code-line"),
            ):
                for unit in span.get(key, []):
                    unit_id = unit[id_key]
                    spans[unit_id] = {
                        "source_id": source_id,
                        "record_sha256": digest_value(
                            {
                                "parent_span_id": parent_id,
                                "unit_type": unit_type,
                                "record": unit,
                            }
                        ),
                        "parent_span_id": parent_id,
                        "unit_type": unit_type,
                    }
    calculations = {
        item["derivation_id"]: {
            "input_sha256": digest_value(input_value(item)),
            "output_sha256": digest_value(output_value(item)),
        }
        for item in content["derivations"]
    }
    roots = {
        item["lineage_id"]: {
            "record_sha256": digest_value(item),
            "root_type": item["root_type"],
        }
        for item in content["source_records"]["lineages"]
    }
    edges = {
        item["edge_id"]: {
            "record_sha256": digest_value(item),
            "edge_type": item["edge_type"],
        }
        for item in content["source_records"]["lineage_edges"]
    }
    return {
        "sources": sources,
        "spans": spans,
        "calculations": calculations,
        "lineage_roots": roots,
        "lineage_edges": edges,
    }


def independently_recompute_derivations(packet: dict[str, Any]) -> None:
    derivations = {item["derivation_id"]: item for item in packet["content"]["derivations"]}
    expected_interpolations = {
        "derive-illinois-feb-2018-298": 89.0,
        "derive-illinois-jul-2018-298": 67.8,
        "derive-illinois-feb-2019-298": 88.6,
    }
    for derivation_id, expected in expected_interpolations.items():
        require(
            close(derivations[derivation_id]["result_percentile"], expected),
            f"interpolation drift: {derivation_id}",
        )
    values = [score for score, count in JULY_MBE_BINS for _ in range(count)]
    mbe_sd = stdev(values)
    ube_sd = (266.0 - 287.6) / NormalDist().inv_cdf(0.27)
    ube = NormalDist(287.6, ube_sd)
    mbe = NormalDist(143.8, mbe_sd)
    parameters = derivations["derive-martinez-parameters"]["results"]
    require(close(parameters["sample_mbe_sd"], mbe_sd), "MBE SD drift")
    require(close(parameters["derived_ube_sd"], ube_sd), "UBE SD drift")
    expected = {
        "derive-martinez-first-time-ube": 100 * ube.cdf(298),
        "derive-martinez-passers-ube": (
            100 * (ube.cdf(298) - ube.cdf(270)) / (1 - ube.cdf(270))
        ),
        "derive-martinez-first-time-mbe": 100 * mbe.cdf(158),
        "derive-martinez-passers-mbe": (
            100 * (mbe.cdf(158) - mbe.cdf(135)) / (1 - mbe.cdf(135))
        ),
        "derive-martinez-first-time-essay": 100 * mbe.cdf(140),
        "derive-martinez-passers-essay": (
            100 * (mbe.cdf(140) - mbe.cdf(135)) / (1 - mbe.cdf(135))
        ),
    }
    for derivation_id, expected_value in expected.items():
        require(
            close(derivations[derivation_id]["result_percentile"], expected_value),
            f"Martinez derivation drift: {derivation_id}",
        )


def verify_packet(
    captures_dir: Path | None = None,
    *,
    require_captures: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_records = load(SOURCE_RECORDS)
    artifact_inventory = load(ARTIFACT_INVENTORY)
    git_blob_search = load(GIT_BLOB_SEARCH_MANIFEST)
    packet = load(CANDIDATE_PACKET)
    require(packet == build_packet(), "candidate packet deterministic rebuild drift")
    require(packet["packet_id"] == EXPECTED_PACKET_ID, "candidate packet ID drift")
    require(identity(SOURCE_RECORDS) == EXPECTED_SOURCE_RECORDS, "source-record drift")
    require(
        identity(ARTIFACT_INVENTORY) == EXPECTED_ARTIFACT_INVENTORY,
        "artifact-inventory drift",
    )
    require(
        identity(GIT_BLOB_SEARCH_MANIFEST) == EXPECTED_GIT_BLOB_SEARCH,
        "Git blob-search manifest drift",
    )
    validate_git_blob_manifest(git_blob_search)
    require(
        git_blob_search["manifest_id"] == EXPECTED_GIT_BLOB_SEARCH_ID,
        "Git blob-search manifest ID drift",
    )
    require(identity(CANDIDATE_PACKET) == EXPECTED_CANDIDATE_PACKET, "packet bytes drift")
    require(
        artifact_inventory["inventory_id"] == EXPECTED_ARTIFACT_INVENTORY_ID,
        "artifact inventory ID drift",
    )

    sources = {item["source_id"]: item for item in source_records["sources"]}
    require(set(sources) == EXPECTED_SOURCE_IDS, "source set drift")
    reshetar = sources["source-reshetar-testing-column-2022"]
    require(
        reshetar["authors_or_org"]
        == "Rosemary Reshetar, EdD / National Conference of Bar Examiners",
        "testing-column visible byline drift",
    )
    require(
        reshetar["attribution_conflict"]
        == {
            "visible_print_byline": "Rosemary Reshetar, EdD",
            "html_json_ld_author": "Jim Leach",
            "treatment": (
                "Use the visible print byline for work attribution; retain the "
                "conflicting JSON-LD site metadata without silently treating it "
                "as authorship."
            ),
        },
        "testing-column attribution conflict drift",
    )
    martinez = sources["source-martinez-vor"]
    require(
        martinez["url"]
        == "https://scholarship.law.tamu.edu/cgi/viewcontent.cgi?article=3387&context=facscholar",
        "Martinez institutional carrier URL drift",
    )
    require(
        martinez["carrier"]["span_readback_ids"]
        == [span["span_id"] for span in martinez["spans"]],
        "Martinez carrier span coverage drift",
    )
    for source_id, expected in EXPECTED_SOURCE_CAPTURE_IDENTITIES.items():
        source = sources[source_id]
        require(source["captured_bytes"] == expected[0], f"bytes drift: {source_id}")
        require(source["captured_sha256"] == expected[1], f"digest drift: {source_id}")
    for source_id, expected in EXPECTED_SEMANTIC_CAPTURES.items():
        semantic = sources[source_id].get("semantic_capture", {})
        require(semantic.get("bytes") == expected[0], f"semantic bytes drift: {source_id}")
        require(semantic.get("sha256") == expected[1], f"semantic digest drift: {source_id}")
        require(semantic.get("normalizer_id"), f"normalizer missing: {source_id}")
        require(semantic.get("command"), f"normalizer command missing: {source_id}")

    counts = packet["content"]["counts"]
    require(
        counts
        == {
            "sources": 19,
            "core_sources": 15,
            "parent_spans": 35,
            "typed_span_units": 76,
            "calculations": 10,
            "lineage_roots": 5,
            "lineage_edges": 10,
            "git_blob_bodies": 78,
            "git_blob_text_bodies": 72,
            "git_blob_binary_bodies": 6,
        },
        "packet count drift",
    )
    edges = source_records["lineage_edges"]
    require({item["edge_id"] for item in edges} == EXPECTED_LINEAGE_EDGE_IDS, "edge set drift")
    require(
        {item["edge_type"] for item in edges} == REQUIRED_LINEAGE_EDGE_TYPES,
        "edge type drift",
    )
    git_root = next(
        item
        for item in artifact_inventory["content"]["artifact_roots"]
        if item["artifact_root_id"] == "artifact-root-katz-git"
    )
    require(
        git_root["source_id"] == "source-katz-git-snapshot",
        "Katz inventory source drift",
    )
    require(
        git_root["commit_sha"] == "90997f740c7197f3f300b013e4345e2ad5621f96",
        "Katz commit drift",
    )
    require(
        git_root["tree_sha"] == "810bd4a9a8ffb51e457715d2312d28d3e9657240",
        "Katz tree drift",
    )
    require(source_records["recommendation"]["author"] == "GO", "recommendation drift")
    require(
        source_records["recommendation"]["independent_review"] == "pending",
        "candidate packet self-approved",
    )
    require(not list(PACKET_ROOT.glob("*.pdf")), "restricted PDF committed")
    require(not list(PACKET_ROOT.glob("*.html")), "raw HTML committed")
    require(not list(PACKET_ROOT.glob("*.xml")), "raw XML committed")
    captures_recomputed = verify_html_captures(
        source_records,
        captures_dir,
        require_captures=require_captures,
    )
    independently_recompute_derivations(packet)
    records = collect_review_records(packet)
    return packet, {
        "packet_id": packet["packet_id"],
        "source_records": identity(SOURCE_RECORDS),
        "artifact_inventory": identity(ARTIFACT_INVENTORY),
        "artifact_inventory_id": artifact_inventory["inventory_id"],
        "git_blob_search_manifest": identity(GIT_BLOB_SEARCH_MANIFEST),
        "git_blob_search_manifest_id": git_blob_search["manifest_id"],
        "candidate_packet": identity(CANDIDATE_PACKET),
        "records": records,
        "counts": counts,
        "author_recommendation": source_records["recommendation"]["author"],
        "html_semantic_captures_recomputed": captures_recomputed,
    }


def require_exact_coverage(actual: Any, expected: set[str], context: str) -> None:
    require(isinstance(actual, list), f"{context}: must be an array")
    require(actual == sorted(expected), f"{context}: incomplete or unsorted coverage")


def command_record_digest(command: dict[str, Any]) -> str:
    return digest_value({key: value for key, value in command.items() if key != "record_sha256"})


def validate_commands(commands: Any) -> None:
    require(isinstance(commands, list) and commands, "receipt.commands: must be non-empty")
    command_ids = set()
    for index, command in enumerate(commands):
        context = f"receipt.commands[{index}]"
        require_exact_fields(
            command,
            {
                "command_id",
                "argv",
                "cwd",
                "started_at",
                "completed_at",
                "exit_code",
                "stdout_sha256",
                "stderr_sha256",
                "record_sha256",
            },
            context,
        )
        command_id = require_string(command["command_id"], f"{context}.command_id")
        require(command_id not in command_ids, f"{context}.command_id: duplicate")
        command_ids.add(command_id)
        argv = command["argv"]
        require(
            isinstance(argv, list)
            and argv
            and all(isinstance(item, str) and item for item in argv),
            f"{context}.argv: invalid",
        )
        cwd = require_string(command["cwd"], f"{context}.cwd")
        require(not Path(cwd).is_absolute(), f"{context}.cwd: must be relative")
        started = require_timestamp(command["started_at"], f"{context}.started_at")
        completed = require_timestamp(command["completed_at"], f"{context}.completed_at")
        require(completed >= started, f"{context}: completion precedes start")
        require(command["exit_code"] == 0, f"{context}.exit_code: must be zero")
        require_sha256(command["stdout_sha256"], f"{context}.stdout_sha256")
        require_sha256(command["stderr_sha256"], f"{context}.stderr_sha256")
        require(
            command["record_sha256"] == command_record_digest(command),
            f"{context}.record_sha256: mismatch",
        )
    require(
        {"packet-build", "packet-verify", "repository-check"}.issubset(command_ids),
        "receipt.commands: required command missing",
    )


def validate_result_rows(
    rows: Any,
    expected: dict[str, Any],
    id_field: str,
    required_fields: set[str],
    context: str,
    validator: Callable[[dict[str, Any], dict[str, Any], str], None],
) -> None:
    require(isinstance(rows, list), f"{context}: must be an array")
    require(len(rows) == len(expected), f"{context}: cardinality drift")
    ids = [row.get(id_field) for row in rows]
    require(len(ids) == len(set(ids)), f"{context}: duplicate ID")
    require(set(ids) == set(expected), f"{context}: coverage drift")
    for index, row in enumerate(rows):
        row_context = f"{context}[{index}]"
        require_exact_fields(row, required_fields, row_context)
        validator(row, expected[row[id_field]], row_context)


def validate_review_results(results: Any, summary: dict[str, Any]) -> None:
    require_exact_fields(
        results,
        {"sources", "spans", "calculations", "lineage_roots", "lineage_edges"},
        "review_results",
    )
    records = summary["records"]

    def source_row(row: dict[str, Any], expected: dict[str, Any], context: str) -> None:
        require(
            row["source_record_sha256"] == expected["record_sha256"],
            f"{context}.source_record_sha256: mismatch",
        )
        require(
            row["semantic_capture_sha256"] == expected["semantic_capture_sha256"],
            f"{context}.semantic_capture_sha256: mismatch",
        )
        for field in ("retrieval_assessment", "capture_assessment", "finding", "limitation"):
            require_string(row[field], f"{context}.{field}")

    validate_result_rows(
        results["sources"],
        records["sources"],
        "source_id",
        {
            "source_id",
            "source_record_sha256",
            "semantic_capture_sha256",
            "retrieval_assessment",
            "capture_assessment",
            "finding",
            "limitation",
        },
        "review_results.sources",
        source_row,
    )

    def span_row(row: dict[str, Any], expected: dict[str, Any], context: str) -> None:
        require(row["source_id"] == expected["source_id"], f"{context}.source_id: mismatch")
        require(
            row["record_sha256"] == expected["record_sha256"],
            f"{context}.record_sha256: mismatch",
        )
        require(
            row["parent_span_id"] == expected["parent_span_id"],
            f"{context}.parent_span_id: mismatch",
        )
        require(row["unit_type"] == expected["unit_type"], f"{context}.unit_type: mismatch")
        require_string(row["verification"], f"{context}.verification")
        require_string(row["finding"], f"{context}.finding")
        require(row["match"] is True, f"{context}.match: must be true")

    validate_result_rows(
        results["spans"],
        records["spans"],
        "span_id",
        {
            "span_id",
            "source_id",
            "record_sha256",
            "parent_span_id",
            "unit_type",
            "verification",
            "finding",
            "match",
        },
        "review_results.spans",
        span_row,
    )

    def calculation_row(
        row: dict[str, Any], expected: dict[str, Any], context: str
    ) -> None:
        require(row["input_sha256"] == expected["input_sha256"], f"{context}: input drift")
        require(row["output_sha256"] == expected["output_sha256"], f"{context}: output drift")
        require(row["reproduced"] is True, f"{context}.reproduced: must be true")
        require_string(row["finding"], f"{context}.finding")

    validate_result_rows(
        results["calculations"],
        records["calculations"],
        "calculation_id",
        {"calculation_id", "input_sha256", "output_sha256", "reproduced", "finding"},
        "review_results.calculations",
        calculation_row,
    )

    def root_row(row: dict[str, Any], expected: dict[str, Any], context: str) -> None:
        require(row["record_sha256"] == expected["record_sha256"], f"{context}: digest drift")
        require(row["root_type"] == expected["root_type"], f"{context}: root type drift")
        require_string(row["finding"], f"{context}.finding")
        require(row["status"] == "pass", f"{context}.status: must be pass")

    validate_result_rows(
        results["lineage_roots"],
        records["lineage_roots"],
        "lineage_id",
        {"lineage_id", "record_sha256", "root_type", "finding", "status"},
        "review_results.lineage_roots",
        root_row,
    )

    def edge_row(row: dict[str, Any], expected: dict[str, Any], context: str) -> None:
        require(row["record_sha256"] == expected["record_sha256"], f"{context}: digest drift")
        require(row["edge_type"] == expected["edge_type"], f"{context}: edge type drift")
        require_string(row["finding"], f"{context}.finding")
        require(row["status"] == "pass", f"{context}.status: must be pass")

    validate_result_rows(
        results["lineage_edges"],
        records["lineage_edges"],
        "edge_id",
        {"edge_id", "record_sha256", "edge_type", "finding", "status"},
        "review_results.lineage_edges",
        edge_row,
    )


def validate_git_binding(repository: dict[str, Any], head: str, tree: str) -> None:
    require(git_text("rev-parse", f"{head}^{{tree}}") == tree, "reviewed tree mismatch")
    require(repository["reviewed_author_head"] == head, "reviewed author head mismatch")
    require(repository["reviewed_author_tree"] == tree, "reviewed author tree mismatch")


def validate_receipt_document(
    receipt: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    *,
    expected_base: str,
    expected_author_head: str,
    expected_author_tree: str,
    expected_reviewer_id: str,
    check_git: bool,
) -> None:
    require_exact_fields(
        receipt,
        {
            "format",
            "task_id",
            "reviewer",
            "repository",
            "started_at",
            "completed_at",
            "git_state",
            "bindings",
            "coverage",
            "review_results",
            "commands",
            "findings",
            "limitations",
            "recommendation",
            "decision",
            "complete",
        },
        "receipt",
    )
    require(receipt["format"] == REVIEW_FORMAT, "receipt.format: unsupported")
    require(receipt["task_id"] == "EM-0032", "receipt.task_id: mismatch")
    started = require_timestamp(receipt["started_at"], "receipt.started_at")
    completed = require_timestamp(receipt["completed_at"], "receipt.completed_at")
    require(completed >= started, "receipt: completion precedes start")

    reviewer = receipt["reviewer"]
    require_exact_fields(
        reviewer,
        {
            "id",
            "role",
            "author_ids",
            "reviewer_is_author",
            "fresh_clone",
            "independent_public_retrieval",
            "authoring_notes_used_as_evidence",
            "notes",
        },
        "receipt.reviewer",
    )
    reviewer_id = require_string(reviewer["id"], "receipt.reviewer.id")
    require(reviewer_id == expected_reviewer_id, "receipt.reviewer.id: expected-ID mismatch")
    require(reviewer["role"] == "independent-reviewer", "receipt.reviewer.role: mismatch")
    require(reviewer["author_ids"] == sorted(AUTHOR_IDS), "receipt.reviewer.author_ids: drift")
    require(reviewer_id not in AUTHOR_IDS, "receipt.reviewer.id equals author")
    require(reviewer["reviewer_is_author"] is False, "receipt reviewer self-authored")
    require(reviewer["fresh_clone"] is True, "receipt reviewer did not use fresh clone")
    require(
        reviewer["independent_public_retrieval"] is True,
        "receipt reviewer did not independently retrieve public sources",
    )
    require(
        reviewer["authoring_notes_used_as_evidence"] is False,
        "receipt reviewer used authoring notes as evidence",
    )
    require_string(reviewer["notes"], "receipt.reviewer.notes")

    repository = receipt["repository"]
    require_exact_fields(
        repository,
        {
            "url",
            "pull_request",
            "branch",
            "reviewed_base",
            "reviewed_author_head",
            "reviewed_author_tree",
            "diff_sha256",
        },
        "receipt.repository",
    )
    require(repository["url"] == REPOSITORY_URL, "receipt repository URL mismatch")
    require(isinstance(repository["pull_request"], int) and repository["pull_request"] > 0,
            "receipt pull request invalid")
    require_string(repository["branch"], "receipt.repository.branch")
    base = require_commit(repository["reviewed_base"], "receipt.repository.reviewed_base")
    head = require_commit(
        repository["reviewed_author_head"], "receipt.repository.reviewed_author_head"
    )
    tree = require_commit(
        repository["reviewed_author_tree"], "receipt.repository.reviewed_author_tree"
    )
    require(base == expected_base, "receipt reviewed base mismatch")
    require(head == expected_author_head, "receipt reviewed head mismatch")
    require(tree == expected_author_tree, "receipt reviewed tree mismatch")
    require_sha256(repository["diff_sha256"], "receipt.repository.diff_sha256")

    bindings = receipt["bindings"]
    require_exact_fields(
        bindings,
        {
            "packet_id",
            "source_records",
            "artifact_inventory",
            "artifact_inventory_id",
            "git_blob_search_manifest",
            "git_blob_search_manifest_id",
            "candidate_packet",
        },
        "receipt.bindings",
    )
    for key in (
        "packet_id",
        "source_records",
        "artifact_inventory",
        "artifact_inventory_id",
        "git_blob_search_manifest",
        "git_blob_search_manifest_id",
        "candidate_packet",
    ):
        require(bindings[key] == summary[key], f"receipt binding drift: {key}")

    coverage = receipt["coverage"]
    require_exact_fields(
        coverage,
        {
            "source_ids",
            "span_ids",
            "calculation_ids",
            "lineage_root_ids",
            "lineage_edge_ids",
        },
        "receipt.coverage",
    )
    coverage_map = {
        "source_ids": set(summary["records"]["sources"]),
        "span_ids": set(summary["records"]["spans"]),
        "calculation_ids": set(summary["records"]["calculations"]),
        "lineage_root_ids": set(summary["records"]["lineage_roots"]),
        "lineage_edge_ids": set(summary["records"]["lineage_edges"]),
    }
    for key, expected in coverage_map.items():
        require_exact_coverage(coverage[key], expected, f"receipt.coverage.{key}")
    validate_review_results(receipt["review_results"], summary)
    validate_commands(receipt["commands"])

    findings = receipt["findings"]
    require(isinstance(findings, list), "receipt.findings: must be an array")
    for index, finding in enumerate(findings):
        require_exact_fields(finding, {"severity", "status", "text"}, f"findings[{index}]")
        require(finding["status"] in {"resolved", "informational"}, "unresolved finding")
        require(finding["severity"] in {"material", "minor", "informational"}, "bad severity")
        require_string(finding["text"], f"findings[{index}].text")
    limitations = receipt["limitations"]
    require(
        isinstance(limitations, list)
        and limitations
        and all(isinstance(item, str) and item.strip() for item in limitations),
        "receipt.limitations: must be non-empty",
    )
    require(receipt["recommendation"] == summary["author_recommendation"], "review differs")
    require(receipt["decision"] == "pass", "receipt.decision: must be pass")
    require(receipt["complete"] is True, "receipt.complete: must be true")

    git_state = receipt["git_state"]
    require_exact_fields(
        git_state,
        {
            "fresh_clone",
            "pre_review_clean",
            "post_review_clean",
            "unchanged_during_review",
            "pre_review_head",
            "post_review_head",
            "pre_review_tree",
            "post_review_tree",
            "pre_status_sha256",
            "post_status_sha256",
        },
        "receipt.git_state",
    )
    for field in (
        "fresh_clone",
        "pre_review_clean",
        "post_review_clean",
        "unchanged_during_review",
    ):
        require(git_state[field] is True, f"receipt.git_state.{field}: must be true")
    require(git_state["pre_review_head"] == head, "pre-review head mismatch")
    require(git_state["post_review_head"] == head, "post-review head mismatch")
    require(git_state["pre_review_tree"] == tree, "pre-review tree mismatch")
    require(git_state["post_review_tree"] == tree, "post-review tree mismatch")
    require(git_state["pre_status_sha256"] == EMPTY_SHA256, "pre-review state dirty")
    require(git_state["post_status_sha256"] == EMPTY_SHA256, "post-review state dirty")

    if not check_git:
        return
    validate_git_binding(repository, expected_author_head, expected_author_tree)
    require(git_text("merge-base", base, head) == base, "reviewed base is not merge-base")
    require(git_text("rev-parse", "origin/main") == base, "reviewed base is stale")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", head, "HEAD"],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
        == 0,
        "reviewed author head is not an ancestor of HEAD",
    )
    changed_after = set(filter(None, git_text("diff", "--name-only", head, "HEAD").splitlines()))
    receipt_rel = str(DEFAULT_REVIEW_RECEIPT.relative_to(REPO_ROOT))
    require(changed_after == {receipt_rel}, "candidate changed after independent review")
    diff = git_bytes("diff", "--binary", "--full-index", "--no-ext-diff", base, head)
    require(sha256(diff) == repository["diff_sha256"], "review diff digest mismatch")
    require(not git_text("status", "--porcelain"), "current repository state is dirty")
    tracked = git_text("ls-files", "--error-unmatch", receipt_rel, check=False)
    require(bool(tracked), "independent receipt must be tracked")


def command_fixture(command_id: str, argv: list[str], now: str) -> dict[str, Any]:
    record = {
        "command_id": command_id,
        "argv": argv,
        "cwd": ".",
        "started_at": now,
        "completed_at": now,
        "exit_code": 0,
        "stdout_sha256": EMPTY_SHA256,
        "stderr_sha256": EMPTY_SHA256,
    }
    record["record_sha256"] = command_record_digest(record)
    return record


def valid_shape_fixture(
    summary: dict[str, Any],
    base: str,
    head: str,
    tree: str,
    reviewer_id: str,
) -> dict[str, Any]:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = summary["records"]
    return {
        "format": REVIEW_FORMAT,
        "task_id": "EM-0032",
        "reviewer": {
            "id": reviewer_id,
            "role": "independent-reviewer",
            "author_ids": sorted(AUTHOR_IDS),
            "reviewer_is_author": False,
            "fresh_clone": True,
            "independent_public_retrieval": True,
            "authoring_notes_used_as_evidence": False,
            "notes": "Shape-only adversarial fixture.",
        },
        "repository": {
            "url": REPOSITORY_URL,
            "pull_request": 57,
            "branch": "fixture",
            "reviewed_base": base,
            "reviewed_author_head": head,
            "reviewed_author_tree": tree,
            "diff_sha256": EMPTY_SHA256,
        },
        "started_at": now,
        "completed_at": now,
        "git_state": {
            "fresh_clone": True,
            "pre_review_clean": True,
            "post_review_clean": True,
            "unchanged_during_review": True,
            "pre_review_head": head,
            "post_review_head": head,
            "pre_review_tree": tree,
            "post_review_tree": tree,
            "pre_status_sha256": EMPTY_SHA256,
            "post_status_sha256": EMPTY_SHA256,
        },
        "bindings": {
            "packet_id": summary["packet_id"],
            "source_records": summary["source_records"],
            "artifact_inventory": summary["artifact_inventory"],
            "artifact_inventory_id": summary["artifact_inventory_id"],
            "git_blob_search_manifest": summary["git_blob_search_manifest"],
            "git_blob_search_manifest_id": summary["git_blob_search_manifest_id"],
            "candidate_packet": summary["candidate_packet"],
        },
        "coverage": {
            "source_ids": sorted(records["sources"]),
            "span_ids": sorted(records["spans"]),
            "calculation_ids": sorted(records["calculations"]),
            "lineage_root_ids": sorted(records["lineage_roots"]),
            "lineage_edge_ids": sorted(records["lineage_edges"]),
        },
        "review_results": {
            "sources": [
                {
                    "source_id": source_id,
                    "source_record_sha256": item["record_sha256"],
                    "semantic_capture_sha256": item["semantic_capture_sha256"],
                    "retrieval_assessment": "fixture-pass",
                    "capture_assessment": "fixture-pass",
                    "finding": "Fixture finding.",
                    "limitation": "Fixture limitation.",
                }
                for source_id, item in sorted(records["sources"].items())
            ],
            "spans": [
                {
                    "span_id": span_id,
                    "source_id": item["source_id"],
                    "record_sha256": item["record_sha256"],
                    "parent_span_id": item["parent_span_id"],
                    "unit_type": item["unit_type"],
                    "verification": "fixture",
                    "finding": "Fixture finding.",
                    "match": True,
                }
                for span_id, item in sorted(records["spans"].items())
            ],
            "calculations": [
                {
                    "calculation_id": calculation_id,
                    "input_sha256": item["input_sha256"],
                    "output_sha256": item["output_sha256"],
                    "reproduced": True,
                    "finding": "Fixture finding.",
                }
                for calculation_id, item in sorted(records["calculations"].items())
            ],
            "lineage_roots": [
                {
                    "lineage_id": lineage_id,
                    "record_sha256": item["record_sha256"],
                    "root_type": item["root_type"],
                    "finding": "Fixture finding.",
                    "status": "pass",
                }
                for lineage_id, item in sorted(records["lineage_roots"].items())
            ],
            "lineage_edges": [
                {
                    "edge_id": edge_id,
                    "record_sha256": item["record_sha256"],
                    "edge_type": item["edge_type"],
                    "finding": "Fixture finding.",
                    "status": "pass",
                }
                for edge_id, item in sorted(records["lineage_edges"].items())
            ],
        },
        "commands": [
            command_fixture("packet-build", ["python", "build_packet.py", "--check"], now),
            command_fixture("packet-verify", ["python", "verify_packet.py"], now),
            command_fixture("repository-check", ["make", "check"], now),
        ],
        "findings": [],
        "limitations": ["Shape-only fixture; no empirical pass is inferred."],
        "recommendation": summary["author_recommendation"],
        "decision": "pass",
        "complete": True,
    }


def run_adversarial_self_test(packet: dict[str, Any], summary: dict[str, Any]) -> None:
    html_fixture = (
        b'<div id="target">kept<script>hidden</script><span>text</span></div>'
        b'<div>outside</div>'
    )
    require(
        normalize_html_visible_text(html_fixture, root_id="target") == b"kept text",
        "HTML normalizer selected excluded or out-of-root text",
    )
    try:
        normalize_html_visible_text(
            b'<div id="target">one</div><div id="target">two</div>',
            root_id="target",
        )
    except ValueError:
        pass
    else:
        fail("HTML normalizer accepted duplicate root IDs")

    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    base = git_text("rev-parse", "HEAD^")
    reviewer_id = "codex-independent-em0032-reviewer"
    fixture = valid_shape_fixture(summary, base, head, tree, reviewer_id)
    kwargs = {
        "expected_base": base,
        "expected_author_head": head,
        "expected_author_tree": tree,
        "expected_reviewer_id": reviewer_id,
        "check_git": False,
    }
    validate_receipt_document(fixture, packet, summary, **kwargs)

    def remove(field_path: tuple[str, ...]) -> Callable[[dict[str, Any]], None]:
        def mutate(value: dict[str, Any]) -> None:
            target: Any = value
            for field in field_path[:-1]:
                target = target[field]
            target.pop(field_path[-1])

        return mutate

    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("missing-base", remove(("repository", "reviewed_base"))),
        ("wrong-base", lambda v: v["repository"].update({"reviewed_base": "0" * 40})),
        ("missing-head", remove(("repository", "reviewed_author_head"))),
        ("wrong-head", lambda v: v["repository"].update({"reviewed_author_head": "0" * 40})),
        ("missing-tree", remove(("repository", "reviewed_author_tree"))),
        ("wrong-tree", lambda v: v["repository"].update({"reviewed_author_tree": "0" * 40})),
        ("wrong-packet", lambda v: v["bindings"].update({"packet_id": "stale"})),
        (
            "wrong-inventory",
            lambda v: v["bindings"]["artifact_inventory"].update({"sha256": "0" * 64}),
        ),
        (
            "wrong-source-records",
            lambda v: v["bindings"]["source_records"].update({"sha256": "0" * 64}),
        ),
        (
            "wrong-candidate",
            lambda v: v["bindings"]["candidate_packet"].update({"sha256": "0" * 64}),
        ),
        ("missing-reviewer", remove(("reviewer", "id"))),
        ("wrong-reviewer", lambda v: v["reviewer"].update({"id": "wrong-reviewer"})),
        ("reviewer-is-author", lambda v: v["reviewer"].update({"id": "codex-builder"})),
        (
            "false-nonauthor",
            lambda v: v["reviewer"].update({"reviewer_is_author": True}),
        ),
        ("false-fresh-clone", lambda v: v["reviewer"].update({"fresh_clone": False})),
        ("missing-start", remove(("started_at",))),
        ("malformed-time", lambda v: v.update({"started_at": "not-a-time"})),
        (
            "non-utc-time",
            lambda v: v.update({"started_at": "2026-08-27T00:00:00+01:00"}),
        ),
        (
            "reversed-time",
            lambda v: v.update(
                {
                    "started_at": "2026-08-27T00:01:00Z",
                    "completed_at": "2026-08-27T00:00:00Z",
                }
            ),
        ),
        (
            "future-time",
            lambda v: v.update({"completed_at": "2999-01-01T00:00:00Z"}),
        ),
        ("missing-command", lambda v: v["commands"].pop()),
        (
            "nonzero-command",
            lambda v: v["commands"][0].update({"exit_code": 1}),
        ),
        (
            "bad-stdout",
            lambda v: v["commands"][0].update({"stdout_sha256": "bad"}),
        ),
        (
            "bad-stderr",
            lambda v: v["commands"][0].update({"stderr_sha256": "bad"}),
        ),
        (
            "bad-command-digest",
            lambda v: v["commands"][0].update({"record_sha256": "0" * 64}),
        ),
        ("missing-source", lambda v: v["review_results"]["sources"].pop()),
        (
            "duplicate-source",
            lambda v: v["review_results"]["sources"].append(
                copy.deepcopy(v["review_results"]["sources"][0])
            ),
        ),
        (
            "unknown-source",
            lambda v: v["review_results"]["sources"][0].update({"source_id": "unknown"}),
        ),
        (
            "missing-source-finding",
            lambda v: v["review_results"]["sources"][0].update({"finding": ""}),
        ),
        (
            "wrong-semantic-digest",
            lambda v: next(
                row
                for row in v["review_results"]["sources"]
                if row["semantic_capture_sha256"] is not None
            ).update({"semantic_capture_sha256": "0" * 64}),
        ),
        ("missing-span", lambda v: v["review_results"]["spans"].pop()),
        (
            "duplicate-span",
            lambda v: v["review_results"]["spans"].append(
                copy.deepcopy(v["review_results"]["spans"][0])
            ),
        ),
        (
            "unknown-span",
            lambda v: v["review_results"]["spans"][0].update({"span_id": "unknown"}),
        ),
        (
            "missing-span-finding",
            lambda v: v["review_results"]["spans"][0].update({"finding": ""}),
        ),
        ("missing-calculation", lambda v: v["review_results"]["calculations"].pop()),
        (
            "duplicate-calculation",
            lambda v: v["review_results"]["calculations"].append(
                copy.deepcopy(v["review_results"]["calculations"][0])
            ),
        ),
        (
            "wrong-calculation-output",
            lambda v: v["review_results"]["calculations"][0].update(
                {"output_sha256": "0" * 64}
            ),
        ),
        ("missing-lineage-root", lambda v: v["review_results"]["lineage_roots"].pop()),
        ("missing-lineage-edge", lambda v: v["review_results"]["lineage_edges"].pop()),
        (
            "wrong-edge-type",
            lambda v: v["review_results"]["lineage_edges"][0].update(
                {"edge_type": "unknown"}
            ),
        ),
        ("blank-limitations", lambda v: v.update({"limitations": []})),
        (
            "dirty-pre-state",
            lambda v: v["git_state"].update({"pre_review_clean": False}),
        ),
        (
            "dirty-post-state",
            lambda v: v["git_state"].update({"post_review_clean": False}),
        ),
        (
            "wrong-status-digest",
            lambda v: v["git_state"].update({"post_status_sha256": "0" * 64}),
        ),
        (
            "pre-head-mismatch",
            lambda v: v["git_state"].update({"pre_review_head": "0" * 40}),
        ),
        (
            "post-tree-mismatch",
            lambda v: v["git_state"].update({"post_review_tree": "0" * 40}),
        ),
        (
            "count-only-coverage",
            lambda v: v.update(
                {
                    "coverage": {
                        "source_count": len(summary["records"]["sources"]),
                        "span_count": len(summary["records"]["spans"]),
                    }
                }
            ),
        ),
    ]
    for label, mutate in mutations:
        forged = copy.deepcopy(fixture)
        mutate(forged)
        try:
            validate_receipt_document(forged, packet, summary, **kwargs)
        except SystemExit:
            continue
        fail(f"adversarial receipt mutation accepted: {label}")

    forged_repository = copy.deepcopy(fixture["repository"])
    forged_repository["reviewed_author_tree"] = "0" * 40
    try:
        validate_git_binding(forged_repository, head, "0" * 40)
    except SystemExit:
        return
    fail("adversarial Git head-to-tree mismatch was accepted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-receipt", type=Path, default=DEFAULT_REVIEW_RECEIPT)
    parser.add_argument("--require-review", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--captures-dir", type=Path)
    parser.add_argument("--require-captures", action="store_true")
    parser.add_argument("--expected-base")
    parser.add_argument("--expected-author-head")
    parser.add_argument("--expected-author-tree")
    parser.add_argument("--expected-reviewer-id")
    args = parser.parse_args()
    packet, summary = verify_packet(
        args.captures_dir,
        require_captures=args.require_captures,
    )
    if args.self_test:
        run_adversarial_self_test(packet, summary)
        summary["adversarial_receipt_tests"] = "passed"
    review = None
    if args.require_review:
        require(
            summary["html_semantic_captures_recomputed"] is True,
            "independent review requires recomputed HTML semantic captures",
        )
    if args.review_receipt.is_file() or args.require_review:
        require(args.review_receipt.is_file(), "independent review receipt missing")
        for field in (
            "expected_base",
            "expected_author_head",
            "expected_author_tree",
            "expected_reviewer_id",
        ):
            require(getattr(args, field), f"--{field.replace('_', '-')} is required")
        review = load(args.review_receipt)
        validate_receipt_document(
            review,
            packet,
            summary,
            expected_base=args.expected_base,
            expected_author_head=args.expected_author_head,
            expected_author_tree=args.expected_author_tree,
            expected_reviewer_id=args.expected_reviewer_id,
            check_git=True,
        )
    summary["independent_review_complete"] = review is not None
    if review is not None:
        summary["reviewer"] = review["reviewer"]["id"]
        summary["review_decision"] = review["decision"]
    summary.pop("records")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
