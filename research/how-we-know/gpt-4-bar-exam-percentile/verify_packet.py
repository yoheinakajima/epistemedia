"""Fail-closed verification for the EM-0032 candidate research packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import NormalDist, stdev
from typing import Any

from build_packet import build_packet

PACKET_ROOT = Path(__file__).resolve().parent
SOURCE_RECORDS = PACKET_ROOT / "source-records.json"
ARTIFACT_INVENTORY = PACKET_ROOT / "artifact-inventory.json"
CANDIDATE_PACKET = PACKET_ROOT / "candidate-packet.json"
DEFAULT_REVIEW_RECEIPT = PACKET_ROOT / "independent-review-receipt.json"

EXPECTED_PACKET_ID = (
    "em:research-packet:sha256:3302c2c7282699e52ab53d670a83ded21f2a43de7685604075a1eed8a2f63ae1"
)
EXPECTED_SOURCE_CAPTURE_IDENTITIES = {
    "source-openai-v1": (
        5229731,
        "053056a10114d22e4c47b6b5be25e54c320b5f1beeae7466e8638dac0f5f5f66",
    ),
    "source-openai-v6": (
        5245564,
        "c33a66dadca2388d7b172d6293b00dc32b71110c6f38fafe0d41112e61be7774",
    ),
    "source-katz-vor": (117084, "d5a7b3d5cba67eb070f13e5e72700a11b2f081af664aad197acb37427aa47264"),
    "source-katz-ssrn": (16942, "146a68d349dae70ece09fefe79cd04808a40afb8f1e19a4c63941678330cb90b"),
    "source-katz-git-tree": (
        29311,
        "9541fd9b9677738aae5fac3048eaa5efc2a23ff5a97ecedec74492eb451e86fb",
    ),
    "source-katz-figshare": (
        4917,
        "ce59483bb4dae6871cadf3afa9d650e00d4c524b75083f0c43706436d1220ba6",
    ),
    "source-illinois-feb-2018": (
        41491,
        "500d734d54cfaae23b94a988469a8a626fc71abefd5793424bfbe83aabe9e1b7",
    ),
    "source-illinois-jul-2018": (
        41047,
        "9b4251dc1147789eceb9e4e4b3cbdb4e98ab4634f286e8f4d8917d4e0970a299",
    ),
    "source-illinois-feb-2019": (
        40394,
        "b313a414728db06d9170f79f0177927a3343e3744fc39ba3cadaff1fddc27faa",
    ),
    "source-ncbe-ube-mechanics": (
        63952,
        "359f8d4e94e128480fe474f07e87a0b019ff20f4cd6041d0b7bfe904b8a84628",
    ),
    "source-ncbe-mbe-2022": (
        278417,
        "f21c45a6e9d1c1b3a5a538ff4bc5b28751928fac53cb5d174e6ec64488c6b784",
    ),
    "source-ncbe-snapshot-2022": (
        188472,
        "391deeac882bfe4dfb69a58e852c465ffbcc9e1d2e0a8557208f82cf795309a0",
    ),
    "source-ncbe-first-repeat-2022": (
        372700,
        "d5edc89f2c781ab7a795602cdc4a6b42b3da457f13972c8660db9a2b976df448",
    ),
    "source-martinez-vor": (
        869291,
        "79cc616af2bf287b782c91eaa439ec662a2e8c1db82352c246a74f3ac22cc801",
    ),
    "source-martinez-osf": (
        3696,
        "06c756ef9d72bce0e92e821917bd5ca02fa1d5089b965689a2dd4f4d28f15bf5",
    ),
    "source-ncbe-ube-2022": (
        260280,
        "eb3e0b45cd4496cfc15669c267f25107c27e31489ece46dd43def1356a966e52",
    ),
    "source-ny-passrates-2022": (
        65751,
        "9cddfa2dbe71b11e01a5ee24a328952cdb8c6a81ee140e83a8a1713aa4c17088",
    ),
    "source-reshetar-2022": (
        218131,
        "174a5adc50f0235f70ebea3b6c4ed85fbe91df8c18d8144286876fe6b95e70bd",
    ),
    "source-martinez-analysis-new": (
        12730,
        "e73b60d3bcba8075b8e513f53d079541ca11b32fa68a8a1201a6442644add588",
    ),
}


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot parse {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def identity(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def close(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return abs(actual - expected) <= tolerance


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

    bins = [
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
    values = [score for score, count in bins for _ in range(count)]
    mbe_sd = stdev(values)
    ube_sd = (266.0 - 287.6) / NormalDist().inv_cdf(0.27)
    ube = NormalDist(287.6, ube_sd)
    mbe = NormalDist(143.8, mbe_sd)

    parameters = derivations["derive-martinez-parameters"]["results"]
    require(close(parameters["sample_mbe_sd"], mbe_sd), "MBE SD drift")
    require(close(parameters["derived_ube_sd"], ube_sd), "UBE SD drift")
    expected = {
        "derive-martinez-first-time-ube": 100 * ube.cdf(298),
        "derive-martinez-passers-ube": (100 * (ube.cdf(298) - ube.cdf(270)) / (1 - ube.cdf(270))),
        "derive-martinez-first-time-mbe": 100 * mbe.cdf(158),
        "derive-martinez-passers-mbe": (100 * (mbe.cdf(158) - mbe.cdf(135)) / (1 - mbe.cdf(135))),
        "derive-martinez-first-time-essay": 100 * mbe.cdf(140),
        "derive-martinez-passers-essay": (100 * (mbe.cdf(140) - mbe.cdf(135)) / (1 - mbe.cdf(135))),
    }
    for derivation_id, expected_value in expected.items():
        require(
            close(derivations[derivation_id]["result_percentile"], expected_value),
            f"Martinez derivation drift: {derivation_id}",
        )


def verify_packet() -> dict[str, Any]:
    source_records = load(SOURCE_RECORDS)
    artifact_inventory = load(ARTIFACT_INVENTORY)
    packet = load(CANDIDATE_PACKET)
    require(packet == build_packet(), "candidate packet deterministic rebuild drift")
    require(packet["packet_id"] == EXPECTED_PACKET_ID, "candidate packet ID drift")

    sources = {item["source_id"]: item for item in packet["content"]["source_records"]["sources"]}
    require(set(sources) == set(EXPECTED_SOURCE_CAPTURE_IDENTITIES), "source set drift")
    for source_id, (expected_bytes, expected_digest) in EXPECTED_SOURCE_CAPTURE_IDENTITIES.items():
        source = sources[source_id]
        require(source["captured_bytes"] == expected_bytes, f"bytes drift: {source_id}")
        require(source["captured_sha256"] == expected_digest, f"digest drift: {source_id}")

    require(len(source_records["core_source_ids"]) == 15, "core source count drift")
    spans = [span for source in sources.values() for span in source["spans"]]
    require(len(spans) == 32, "quote-minimal span count drift")
    require(all(span["quote"].strip() for span in spans), "empty quote-minimal span")
    require(len(source_records["claims"]) == 8, "claim count drift")
    require(len(source_records["lineages"]) == 5, "lineage count drift")

    negative_searches = source_records["negative_searches"]
    require(len(negative_searches) == 1, "negative-search count drift")
    search = negative_searches[0]
    require(search["status"] == "unresolved-no-credit", "launch source was inferred")
    require("not proof" in search["limitations"], "bounded-search limitation missing")
    require(
        source_records["recommendation"]["author"] == "GO",
        "author recommendation drift",
    )
    require(
        source_records["recommendation"]["independent_review"] == "pending",
        "source record improperly self-approves",
    )

    artifacts = artifact_inventory["content"]["artifacts"]
    require(len(artifacts) == 89, "artifact count drift")
    root_counts = {
        root_id: sum(item["artifact_root_id"] == root_id for item in artifacts)
        for root_id in {
            "artifact-root-katz-git",
            "artifact-root-katz-figshare",
            "artifact-root-martinez-osf",
        }
    }
    require(
        root_counts
        == {
            "artifact-root-katz-git": 78,
            "artifact-root-katz-figshare": 1,
            "artifact-root-martinez-osf": 10,
        },
        "artifact root count drift",
    )
    require(
        all(item["independent_evidence_credit"] == 0 for item in artifacts),
        "artifact mirrors received independent evidence credit",
    )
    require(
        sum(
            item["bytes"]
            for item in artifacts
            if item["artifact_root_id"] == "artifact-root-martinez-osf"
        )
        == 34_906_996,
        "OSF inventory bytes drift",
    )
    independently_recompute_derivations(packet)
    return {
        "packet_id": packet["packet_id"],
        "source_records": identity(SOURCE_RECORDS),
        "artifact_inventory": identity(ARTIFACT_INVENTORY),
        "candidate_packet": identity(CANDIDATE_PACKET),
        "sources": len(sources),
        "core_sources": len(source_records["core_source_ids"]),
        "spans": len(spans),
        "artifacts": len(artifacts),
        "author_recommendation": source_records["recommendation"]["author"],
    }


def verify_review(receipt_path: Path, packet_summary: dict[str, Any]) -> dict[str, Any]:
    require(receipt_path.is_file(), "independent review receipt missing")
    receipt = load(receipt_path)
    require(receipt.get("task_id") == "EM-0032", "review task mismatch")
    require(receipt.get("decision") == "pass", "independent review did not pass")
    require(
        receipt.get("recommendation") == packet_summary["author_recommendation"],
        "independent recommendation differs from reviewed packet",
    )
    require(receipt.get("packet_id") == packet_summary["packet_id"], "review packet mismatch")
    for key in ("source_records", "artifact_inventory", "candidate_packet"):
        require(receipt.get("bindings", {}).get(key) == packet_summary[key], f"review {key} drift")
    independence = receipt.get("independence", {})
    require(independence.get("fresh_clone") is True, "review was not fresh-clone")
    require(independence.get("reviewer_was_author") is False, "reviewer was author")
    require(
        independence.get("independent_public_retrieval") is True,
        "review did not independently retrieve public sources",
    )
    coverage = receipt.get("coverage", {})
    require(
        coverage.get("source_ids") == sorted(EXPECTED_SOURCE_CAPTURE_IDENTITIES),
        "source review coverage drift",
    )
    require(coverage.get("span_count") == 32, "span review coverage drift")
    require(coverage.get("artifact_count") == 89, "artifact review coverage drift")
    require(coverage.get("derivation_count") == 10, "derivation review coverage drift")
    require(coverage.get("lineage_count") == 5, "lineage review coverage drift")
    require(receipt.get("complete") is True, "review receipt is incomplete")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-receipt", type=Path, default=DEFAULT_REVIEW_RECEIPT)
    parser.add_argument("--require-review", action="store_true")
    args = parser.parse_args()
    summary = verify_packet()
    review = None
    if args.review_receipt.is_file() or args.require_review:
        review = verify_review(args.review_receipt, summary)
    summary["independent_review_complete"] = review is not None
    if review is not None:
        summary["reviewer"] = review["reviewer"]["id"]
        summary["review_decision"] = review["decision"]
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
