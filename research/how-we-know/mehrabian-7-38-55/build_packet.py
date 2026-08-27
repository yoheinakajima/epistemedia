"""Build the deterministic EM-0033 Mehrabian research packet."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parent
SOURCE_RECORDS = PACKET_ROOT / "source-records.json"
CANDIDATE_PACKET = PACKET_ROOT / "candidate-packet.json"

REQUIRED_LINEAGE_DIMENSIONS = {
    "participant",
    "speaker",
    "author",
    "grant",
    "stimulus",
    "material",
    "method",
    "scale",
    "citation",
    "book-edition",
    "derivation",
}


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


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_source_records(content: dict[str, Any]) -> None:
    sources = content.get("source_records", [])
    require(isinstance(sources, list) and sources, "source records missing")
    source_ids = [item.get("source_id") for item in sources]
    require(len(source_ids) == len(set(source_ids)), "duplicate source ID")

    spans = [span for source in sources for span in source.get("spans", [])]
    span_ids = [span.get("span_id") for span in spans]
    require(len(span_ids) == len(set(span_ids)), "duplicate span ID")
    require(all(isinstance(item, str) and item for item in span_ids), "invalid span ID")
    span_id_set = set(span_ids)
    for span in spans:
        quote = span.get("quote")
        require(isinstance(quote, str) and quote.strip(), f"empty quote: {span['span_id']}")
        kind = span.get("span_kind", "contiguous_quote")
        if kind == "contiguous_quote":
            require(" ... " not in quote, f"undeclared omission: {span['span_id']}")
        elif kind == "verbatim_segments":
            segments = span.get("segments")
            require(
                isinstance(segments, list)
                and len(segments) >= 2
                and all(isinstance(item, str) and item.strip() for item in segments),
                f"invalid segments: {span['span_id']}",
            )
            require(quote == " ... ".join(segments), f"segment rendering drift: {span['span_id']}")
        elif kind == "structured_transcription":
            fields = span.get("fields")
            require(isinstance(fields, dict) and fields, f"missing fields: {span['span_id']}")
        else:
            raise SystemExit(f"unknown span kind: {span['span_id']}")

    claims = content.get("claims", [])
    claim_ids = [item.get("claim_id") for item in claims]
    require(len(claim_ids) == len(set(claim_ids)), "duplicate claim ID")
    for claim in claims:
        cited = claim.get("span_ids", [])
        require(cited and set(cited) <= span_id_set, f"claim span gap: {claim['claim_id']}")

    edges = content.get("lineage_edges", [])
    edge_ids = [item.get("edge_id") for item in edges]
    require(len(edge_ids) == len(set(edge_ids)), "duplicate lineage edge ID")
    require(
        {item.get("dimension") for item in edges} == REQUIRED_LINEAGE_DIMENSIONS,
        "lineage dimension coverage drift",
    )
    for edge in edges:
        require(
            edge.get("from_ids") and edge.get("to_ids"),
            f"lineage endpoint gap: {edge['edge_id']}",
        )
        cited = edge.get("evidence_span_ids", [])
        require(cited and set(cited) <= span_id_set, f"lineage evidence gap: {edge['edge_id']}")
        require(edge.get("status"), f"lineage status gap: {edge['edge_id']}")
        require(edge.get("effect_on_independence"), f"lineage effect gap: {edge['edge_id']}")

    require(
        all(
            item.get("scientific_rule_evidence_credit") == 0
            for item in content["propagation_ledger"]
        ),
        "propagation object received scientific evidence credit",
    )
    require(
        content["derivation_inputs"].get("origin_of_verbal_coefficient") == "unresolved-no-credit",
        "missing seven-percent derivation was inferred",
    )


def build_derivations(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    verbal = float(inputs["proposed_verbal"])
    vocal = float(inputs["proposed_vocal"])
    facial = float(inputs["proposed_facial"])
    p2_facial = float(inputs["p2_facial_coefficient"])
    p2_vocal = float(inputs["p2_vocal_coefficient"])
    p2_ratio = p2_facial / p2_vocal
    proposed_ratio = facial / vocal
    remaining = 1.0 - verbal
    p2_allocated_facial = remaining * p2_facial / (p2_facial + p2_vocal)
    p2_allocated_vocal = remaining * p2_vocal / (p2_facial + p2_vocal)
    return [
        {
            "derivation_id": "derive-proposed-sum",
            "equation": "0.07 + 0.38 + 0.55",
            "inputs": [verbal, vocal, facial],
            "result": verbal + vocal + facial,
            "interpretation": "The printed proposal is normalized to one.",
        },
        {
            "derivation_id": "derive-proposed-facial-vocal-ratio",
            "equation": "0.55 / 0.38",
            "inputs": [facial, vocal],
            "result": proposed_ratio,
            "interpretation": "Facial-to-vocal ratio implied by the printed proposal.",
        },
        {
            "derivation_id": "derive-p2-facial-vocal-ratio",
            "equation": "1.50 / 1.03",
            "inputs": [p2_facial, p2_vocal],
            "result": p2_ratio,
            "interpretation": "Facial-to-vocal ratio from P2's reported regression.",
        },
        {
            "derivation_id": "derive-ratio-difference",
            "equation": "abs((1.50 / 1.03) - (0.55 / 0.38))",
            "inputs": [p2_ratio, proposed_ratio],
            "result": abs(p2_ratio - proposed_ratio),
            "interpretation": (
                "The reported regression and printed proposal are close, not identical."
            ),
        },
        {
            "derivation_id": "derive-implied-vocal-verbal-ratio",
            "equation": "0.38 / 0.07",
            "inputs": [vocal, verbal],
            "result": vocal / verbal,
            "interpretation": (
                "Reverse-engineered ratio implied by the proposal; it does not recover "
                "the missing source derivation of 0.07."
            ),
        },
        {
            "derivation_id": "derive-p2-allocation-with-seven-reserved",
            "equation": "allocate 0.93 in the ratio 1.50:1.03",
            "inputs": {
                "reserved_verbal": verbal,
                "remaining": remaining,
                "p2_facial": p2_facial,
                "p2_vocal": p2_vocal,
            },
            "result": {
                "verbal": verbal,
                "vocal": p2_allocated_vocal,
                "facial": p2_allocated_facial,
            },
            "interpretation": (
                "Sensitivity reconstruction only. Reserving 0.07 is an assumption, not "
                "a derivation supplied by P1 or P2."
            ),
        },
    ]


def build_packet() -> dict[str, Any]:
    source_records = load(SOURCE_RECORDS)
    content = copy.deepcopy(source_records)
    validate_source_records(content)
    spans = []
    for source in content["source_records"]:
        for span in source.get("spans", []):
            span["quote_sha256"] = digest_bytes(span["quote"].encode())
            spans.append(span)
    derivations = build_derivations(content["derivation_inputs"])
    content["derivations"] = derivations
    content["counts"] = {
        "source_records": len(content["source_records"]),
        "quote_minimal_spans": len(spans),
        "claims": len(content["claims"]),
        "derivations": len(derivations),
        "lineage_groups": len(content["lineages"]),
        "lineage_edges": len(content["lineage_edges"]),
        "propagation_objects": len(content["propagation_ledger"]),
        "follow_up_objects": len(content["follow_up_ledger"]),
        "participant_data_roots": sum(
            item["participant_data_roots"] for item in content["lineages"]
        ),
    }
    content["source_records_identity"] = identity(SOURCE_RECORDS)
    packet_id = f"em:research-packet:sha256:{digest_bytes(canonical_bytes(content))}"
    return {"packet_id": packet_id, "content": content}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    built = build_packet()
    rendered = json.dumps(built, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        require(CANDIDATE_PACKET.is_file(), "candidate packet missing")
        require(CANDIDATE_PACKET.read_text() == rendered, "candidate packet drift")
    else:
        CANDIDATE_PACKET.write_text(rendered)
    print(
        json.dumps(
            {"packet_id": built["packet_id"], **built["content"]["counts"]},
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
