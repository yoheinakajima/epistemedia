#!/usr/bin/env python3
"""Fail-closed validation for the EM-0035 Case 004 candidate dossier."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from build_candidate import (
    ACCEPTED_PACKET_ID,
    ACCEPTED_PACKET_SHA256,
    ACCEPTED_REVIEW_SHA256,
    ACCEPTED_SOURCE_RECORDS_SHA256,
    CLAIM_LINEAGE,
    DERIVATION_LINEAGE,
    DERIVATION_SPANS,
    EDGE_ENDPOINTS,
    OUTPUT_PATH,
    PACKET_PATH,
    REVIEW_PATH,
    SOURCE_RECORDS_PATH,
    build_candidate,
    canonical_json,
    digest,
    sha256_bytes,
)

from epistemedia.dossier import validate_dossier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOSSIER_DOC_PATH = HERE / "DOSSIER.md"
PLAN_PATH = ROOT / "docs/execution-plans/EM-0035.md"
DEFAULT_REVIEW_RECEIPT = HERE / "independent-em0035-review-receipt.json"
REVIEW_FORMAT = "epistemedia-independent-dossier-review-v1"
REPOSITORY_URL = "https://github.com/yoheinakajima/epistemedia"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ACCEPTED_ARTIFACTS = {
    "research/how-we-know/mehrabian-7-38-55/README.md": (
        4043,
        "c9f576ddad5127111a56d41a8615ca4e2e417e38357814b6c643475017ac9d5d",
    ),
    "research/how-we-know/mehrabian-7-38-55/build_packet.py": (
        9432,
        "e26fe4d96b23249f5a293b657e9477709523008e85d80f5ad7aad4dc6ebf0769",
    ),
    "research/how-we-know/mehrabian-7-38-55/candidate-packet.json": (
        65077,
        ACCEPTED_PACKET_SHA256,
    ),
    "research/how-we-know/mehrabian-7-38-55/independent-review-receipt.json": (
        37799,
        ACCEPTED_REVIEW_SHA256,
    ),
    "research/how-we-know/mehrabian-7-38-55/source-records.json": (
        53857,
        ACCEPTED_SOURCE_RECORDS_SHA256,
    ),
    "research/how-we-know/mehrabian-7-38-55/verify_packet.py": (
        33093,
        "88269c6f949641ec6282b5df20ab6c4aafe531b258002a3302ccd35f1082cdcf",
    ),
    "docs/execution-plans/EM-0033.md": (
        4182,
        "b1230d3c41c9b432e85f1c726be44596ff90e48f2b42858e8fa8430819b3a431",
    ),
    "docs/research/case-004-mehrabian-7-38-55.md": (
        2106,
        "7e0d8e8d928476c3080a52d1d0b22253962698ddbe49e4cbbf60b07d07734fa4",
    ),
    "runs/proposals/20260827T155422Z-a2984526d9f4.json": (
        310,
        "4e4bf31858c968839794018f6f1d09856c55e6fa5184af3898936aeaa6423ac8",
    ),
    "runs/proposals/20260827T170854Z-2974d169d36f.json": (
        557,
        "fc91c5f159ca331da945be4197aa41c736eb428706827686ab9e7789a6c48b28",
    ),
    "runs/proposals/20260827T172115Z-97e661f58a1c.json": (
        503,
        "351525bb1c6b428303fdeb84440e2273d86fe6d01b1d27dc8250a4bdcd1e3a91",
    ),
    "runs/proposals/20260827T172604Z-5b18b377667e.json": (
        544,
        "8e9c64c1f6183270b273559dbd0d70f777f27ccf8fbeb3fd9beed5d883e5530b",
    ),
    "runs/proposals/20260827T175233Z-b8bd994aec7e.json": (
        456,
        "01a039d2578589d7d63b18aaadeb745722dc72e7438503ca350023c0314ef01e",
    ),
}


class VerificationError(ValueError):
    """Raised when a candidate or review receipt fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: must contain an object")
    return value


def require_exact_fields(value: Any, fields: set[str], context: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{context}: must be an object")
    require(set(value) == fields, f"{context}: exact fields differ")
    return value


def require_timestamp(value: Any, context: str) -> datetime:
    require(isinstance(value, str) and value, f"{context}: timestamp missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerificationError(f"{context}: invalid timestamp") from exc
    require(parsed.tzinfo is not None, f"{context}: timezone missing")
    return parsed


def require_sha(value: Any, pattern: re.Pattern[str], context: str) -> str:
    require(isinstance(value, str) and pattern.fullmatch(value) is not None, context)
    return value


def require_exact_coverage(actual: Any, expected: set[str], context: str) -> None:
    require(isinstance(actual, list), f"{context}: must be an array")
    require(
        len(actual) == len(set(actual)) and set(actual) == expected,
        f"{context}: incomplete, duplicate, or extra identities",
    )


def file_identity(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def verify_accepted_bytes() -> None:
    for relative, (expected_bytes, expected_sha) in ACCEPTED_ARTIFACTS.items():
        path = ROOT / relative
        require(path.is_file(), f"accepted EM-0033 artifact missing: {relative}")
        payload = path.read_bytes()
        require(len(payload) == expected_bytes, f"accepted artifact byte drift: {relative}")
        require(
            sha256_bytes(payload) == expected_sha, f"accepted artifact digest drift: {relative}"
        )


def verify_candidate_documentation(summary: dict[str, Any]) -> list[dict[str, Any]]:
    require(DOSSIER_DOC_PATH.is_file(), "candidate dossier documentation missing")
    require(PLAN_PATH.is_file(), "EM-0035 execution plan missing")
    dossier_text = DOSSIER_DOC_PATH.read_text(encoding="utf-8")
    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    identity_tokens = (
        summary["dossier_id"],
        summary["candidate_dossier"]["sha256"],
        ACCEPTED_PACKET_ID,
        summary["source_graph_sha256"],
    )
    for token in identity_tokens:
        require(token in dossier_text, f"DOSSIER.md identity drift: {token}")
    for token in identity_tokens[:3]:
        require(token in plan_text, f"EM-0035 plan identity drift: {token}")
    count_tokens = {
        str(value)
        for value in (
            *summary["dossier_counts"].values(),
            *summary["accepted_relation_counts"].values(),
        )
    }
    require(
        all(token in dossier_text for token in count_tokens),
        "DOSSIER.md displayed count drift",
    )
    require(
        "independent EM-0035 dossier review pending" in dossier_text
        and "fresh-clone independent dossier review pending" in plan_text,
        "candidate documentation must keep independent review pending",
    )
    return [file_identity(DOSSIER_DOC_PATH), file_identity(PLAN_PATH)]


def expected_calculation_results() -> dict[str, Any]:
    proposed_ratio = 0.55 / 0.38
    p2_ratio = 1.50 / 1.03
    remaining = 1.0 - 0.07
    return {
        "derive-proposed-sum": 0.07 + 0.38 + 0.55,
        "derive-proposed-facial-vocal-ratio": proposed_ratio,
        "derive-p2-facial-vocal-ratio": p2_ratio,
        "derive-ratio-difference": abs(p2_ratio - proposed_ratio),
        "derive-implied-vocal-verbal-ratio": 0.38 / 0.07,
        "derive-p2-allocation-with-seven-reserved": {
            "verbal": 0.07,
            "vocal": remaining * 1.03 / (1.50 + 1.03),
            "facial": remaining * 1.50 / (1.50 + 1.03),
        },
    }


def graph_digest(dossier: dict[str, Any]) -> str:
    fields = (
        "source_works",
        "editions",
        "spans",
        "lineages",
        "assertions",
        "evidence_relations",
        "claim_families",
    )
    return sha256_bytes(canonical_json({field: dossier[field] for field in fields}))


def verify_candidate_document(
    dossier: dict[str, Any],
    packet: dict[str, Any],
    *,
    require_exact_build: bool,
) -> dict[str, Any]:
    validate_dossier(dossier)
    if require_exact_build:
        require(dossier == build_candidate(), "candidate dossier differs from deterministic build")
    content = packet["content"]
    require(packet["packet_id"] == ACCEPTED_PACKET_ID, "accepted packet ID drift")
    require(dossier["stage"] == "draft", "candidate must remain draft")
    require(dossier["visibility"] == "public", "candidate must be disclosure-safe public data")
    require(
        all(
            marker in dossier["scope"]
            for marker in ("not admitted", "not featured", "not live", "not published")
        ),
        "candidate scope must preserve admission and publication boundaries",
    )

    sources = content["source_records"]
    sources_by_edition = {source["edition_id"]: source for source in sources}
    works_by_id: dict[str, list[dict[str, Any]]] = {}
    for source in sources:
        works_by_id.setdefault(source["work_id"], []).append(source)
    dossier_works = {item["key"]: item for item in dossier["source_works"]}
    dossier_editions = {item["key"]: item for item in dossier["editions"]}
    dossier_spans = {item["key"]: item for item in dossier["spans"]}
    require(set(dossier_works) == set(works_by_id), "source-work identity set drift")
    require(set(dossier_editions) == set(sources_by_edition), "edition identity set drift")

    expected_span_ids = {span["span_id"] for source in sources for span in source["spans"]}
    require(set(dossier_spans) == expected_span_ids, "parent-span identity set drift")
    for edition_key, source in sources_by_edition.items():
        edition = dossier_editions[edition_key]
        require(edition["work_key"] == source["work_id"], f"{edition_key}: work drift")
        require(
            edition["content"]["accepted_packet_id"] == ACCEPTED_PACKET_ID,
            f"{edition_key}: packet binding drift",
        )
        require(
            edition["content"]["source_record"] == source,
            f"{edition_key}: accepted source-record projection drift",
        )
        for index, span in enumerate(source["spans"]):
            span_key = span["span_id"]
            projected = dossier_spans[span_key]
            require(projected["edition_key"] == edition_key, f"{span_key}: edition drift")
            require(
                projected["locator"]["pointer"] == f"/source_record/spans/{index}",
                f"{span_key}: parent-span pointer drift",
            )
            require(projected["extent"]["value"] == span, f"{span_key}: extent drift")
            require(projected["digest"] == digest(span), f"{span_key}: digest drift")
            require(
                span["quote_sha256"] == sha256_bytes(span["quote"].encode("utf-8")),
                f"{span_key}: accepted quote digest drift",
            )

    claims = {item["claim_id"]: item for item in content["claims"]}
    derivations = {item["derivation_id"]: item for item in content["derivations"]}
    propositions = {item["key"]: item for item in dossier["propositions"]}
    require(set(claims).issubset(propositions), "accepted claim proposition missing")
    require(set(derivations).issubset(propositions), "accepted calculation proposition missing")
    for claim_id, claim in claims.items():
        require(
            propositions[claim_id]["text"] == claim["proposition"],
            f"{claim_id}: proposition text drift",
        )
    reproduced = expected_calculation_results()
    require(set(reproduced) == set(derivations), "calculation identity set drift")
    for derivation_id, result in reproduced.items():
        require(
            derivations[derivation_id]["result"] == result,
            f"{derivation_id}: calculation does not reproduce",
        )
        require(
            DERIVATION_LINEAGE[derivation_id] in {item["key"] for item in dossier["lineages"]},
            f"{derivation_id}: calculation lineage missing",
        )

    assertions = {item["key"]: item for item in dossier["assertions"]}
    assertions_by_proposition: dict[str, list[dict[str, Any]]] = {}
    for assertion in assertions.values():
        assertions_by_proposition.setdefault(assertion["proposition_key"], []).append(assertion)
    material_proposition_keys = set(propositions)
    require(
        set(assertions_by_proposition) == material_proposition_keys,
        "every material proposition must have assertion closure",
    )
    require(
        all(
            len(items) == 1 and items[0]["span_keys"]
            for items in assertions_by_proposition.values()
        ),
        "material propositions require exactly one non-empty span-bound assertion",
    )
    for claim_id, claim in claims.items():
        assertion = assertions_by_proposition[claim_id][0]
        require(assertion["span_keys"] == claim["span_ids"], f"{claim_id}: span closure drift")
        require(
            assertion["lineage_key"] == CLAIM_LINEAGE[claim_id],
            f"{claim_id}: lineage closure drift",
        )
    for derivation_id in derivations:
        assertion = assertions_by_proposition[derivation_id][0]
        require(
            assertion["span_keys"] == DERIVATION_SPANS[derivation_id],
            f"{derivation_id}: input-span closure drift",
        )

    lineages = {item["key"]: item for item in dossier["lineages"]}
    participant_roots = {
        "lineage-participant-p1",
        "lineage-participant-p2",
        "lineage-hegstrom-rebuttal",
        "lineage-participant-argyle-1970",
        "lineage-participant-argyle-1971",
    }
    observed_participant_roots = {
        key
        for key, lineage in lineages.items()
        if "data" in lineage["dimensions"] and not lineage["depends_on"]
    }
    require(
        observed_participant_roots == participant_roots,
        "five participant-data roots are not kept distinct",
    )
    require(
        lineages["lineage-seven-origin-unknown"]["status"] == "unknown",
        "missing .07 derivation must remain unknown",
    )
    require(
        lineages["lineage-silent-1981-unknown"]["status"] == "unknown",
        "uncollated 1981 formula-page continuity must remain unknown",
    )

    relations = {item["key"]: item for item in dossier["evidence_relations"]}
    accepted_edges = {item["edge_id"]: item for item in content["lineage_edges"]}
    require(set(accepted_edges) == set(EDGE_ENDPOINTS), "accepted lineage-edge set drift")
    for edge_id, edge in accepted_edges.items():
        relation = relations.get(edge_id)
        require(relation is not None, f"{edge_id}: typed dependence missing")
        require(relation["relation_type"] == "dependence", f"{edge_id}: wrong relation type")
        require(
            (relation["from_ref"], relation["to_ref"]) == EDGE_ENDPOINTS[edge_id],
            f"{edge_id}: lineage endpoints drift",
        )
        require(
            relation["basis_span_keys"] == edge["evidence_span_ids"],
            f"{edge_id}: evidence-span closure drift",
        )
        require(
            relation["note"]
            == (
                f"accepted_dimension={edge['dimension']}; "
                f"accepted_status={edge['status']}; "
                f"effect={edge['effect_on_independence']}"
            ),
            f"{edge_id}: typed dependence metadata drift",
        )
    relation_targets = {
        item["to_ref"]
        for item in relations.values()
        if item["relation_type"] in {"support", "rebuttal", "qualification", "undercutting"}
    }
    require(
        material_proposition_keys.issubset(relation_targets),
        "material sentence lacks an explicit evidence relation",
    )
    referenced_spans = {
        span_key for assertion in assertions.values() for span_key in assertion["span_keys"]
    } | {span_key for relation in relations.values() for span_key in relation["basis_span_keys"]}
    require(referenced_spans == expected_span_ids, "complete parent-span coverage drift")

    require(
        all(item["scientific_rule_evidence_credit"] == 0 for item in content["propagation_ledger"]),
        "propagation objects must receive zero scientific-rule credit",
    )
    evaluations = {item["policy_id"]: item for item in dossier["evaluations"]}
    require(
        set(evaluations) == {"epistemedia-encyclopedia-v1", "epistemedia-skeptical-v1"},
        "policy evaluation set drift",
    )
    encyclopedia = evaluations["epistemedia-encyclopedia-v1"]
    skeptical = evaluations["epistemedia-skeptical-v1"]
    require(
        encyclopedia["claim_family_key"] == skeptical["claim_family_key"]
        and encyclopedia["frontier"] == skeptical["frontier"] == ACCEPTED_PACKET_ID,
        "policy views do not share one unchanged source graph",
    )
    require(
        encyclopedia["label"] != skeptical["label"]
        and set(encyclopedia["reason_codes"]).isdisjoint(skeptical["reason_codes"]),
        "encyclopedia and skeptical evaluations are not materially distinct",
    )

    ids = {
        "source_work_keys": set(dossier_works),
        "edition_keys": set(dossier_editions),
        "span_keys": expected_span_ids,
        "proposition_keys": material_proposition_keys,
        "lineage_keys": set(lineages),
        "assertion_keys": set(assertions),
        "relation_keys": set(relations),
        "evaluation_keys": {item["key"] for item in dossier["evaluations"]},
        "accepted_claim_ids": set(claims),
        "accepted_derivation_ids": set(derivations),
        "accepted_lineage_edge_ids": set(accepted_edges),
        "propagation_ids": {item["object_id"] for item in content["propagation_ledger"]},
        "follow_up_source_ids": {item["source_id"] for item in content["follow_up_ledger"]},
    }
    return {
        "dossier_id": dossier["dossier_id"],
        "candidate_dossier": file_identity(OUTPUT_PATH),
        "accepted_packet": file_identity(PACKET_PATH),
        "accepted_review": file_identity(REVIEW_PATH),
        "accepted_source_records": file_identity(SOURCE_RECORDS_PATH),
        "source_graph_sha256": graph_digest(dossier),
        "dossier_counts": {
            "source_works": len(dossier["source_works"]),
            "editions": len(dossier["editions"]),
            "spans": len(dossier["spans"]),
            "propositions": len(dossier["propositions"]),
            "lineages": len(dossier["lineages"]),
            "assertions": len(dossier["assertions"]),
            "evidence_relations": len(dossier["evidence_relations"]),
            "claim_families": len(dossier["claim_families"]),
            "evaluations": len(dossier["evaluations"]),
        },
        "accepted_relation_counts": content["counts"],
        "counts": {key: len(value) for key, value in ids.items()},
        "ids": ids,
    }


def verify_candidate() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    verify_accepted_bytes()
    packet = load(PACKET_PATH)
    require(OUTPUT_PATH.is_file(), "candidate dossier missing")
    dossier = load(OUTPUT_PATH)
    summary = verify_candidate_document(dossier, packet, require_exact_build=True)
    summary["candidate_documentation"] = verify_candidate_documentation(summary)
    return dossier, packet, summary


def expected_review_results(
    dossier: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    content = packet["content"]
    sources = content["source_records"]
    span_to_source = {span["span_id"]: source for source in sources for span in source["spans"]}
    spans = {span["span_id"]: span for source in sources for span in source["spans"]}
    assertions_by_proposition: dict[str, list[dict[str, Any]]] = {}
    for assertion in dossier["assertions"]:
        assertions_by_proposition.setdefault(assertion["proposition_key"], []).append(assertion)
    relations_by_target: dict[str, list[dict[str, Any]]] = {}
    for relation in dossier["evidence_relations"]:
        relations_by_target.setdefault(relation["to_ref"], []).append(relation)
    return {
        "sources": [
            {
                "source_id": source["source_id"],
                "work_key": source["work_id"],
                "edition_key": source["edition_id"],
                "capture_ids": sorted(item["capture_id"] for item in source["captures"]),
                "span_keys": sorted(item["span_id"] for item in source["spans"]),
                "identity_checked": True,
                "access_and_gap_checked": True,
                "license_treatment_checked": True,
                "status": "pass",
            }
            for source in sorted(sources, key=lambda item: item["source_id"])
        ],
        "spans": [
            {
                "span_key": span_key,
                "source_id": span_to_source[span_key]["source_id"],
                "edition_key": span_to_source[span_key]["edition_id"],
                "parent_span_digest": digest(spans[span_key]),
                "quote_sha256": spans[span_key]["quote_sha256"],
                "locator_checked": True,
                "segment_or_field_checked": True,
                "retrieval_identity_checked": True,
                "license_treatment_checked": True,
                "status": "pass",
            }
            for span_key in sorted(spans)
        ],
        "calculations": [
            {
                "derivation_id": item["derivation_id"],
                "expected_result_sha256": sha256_bytes(canonical_json(item["result"])),
                "observed_result_sha256": sha256_bytes(
                    canonical_json(expected_calculation_results()[item["derivation_id"]])
                ),
                "reproduced": True,
                "status": "pass",
            }
            for item in sorted(content["derivations"], key=lambda value: value["derivation_id"])
        ],
        "lineages": [
            {
                "lineage_key": lineage["key"],
                "basis_span_keys": sorted(lineage["basis_span_keys"]),
                "depends_on": sorted(lineage["depends_on"]),
                "dependence_checked": True,
                "status": "pass",
            }
            for lineage in sorted(dossier["lineages"], key=lambda item: item["key"])
        ],
        "propositions": [
            {
                "proposition_key": proposition["key"],
                "assertion_keys": sorted(
                    item["key"] for item in assertions_by_proposition.get(proposition["key"], [])
                ),
                "span_keys": sorted(
                    {
                        span_key
                        for item in assertions_by_proposition.get(proposition["key"], [])
                        for span_key in item["span_keys"]
                    }
                ),
                "relation_keys": sorted(
                    item["key"] for item in relations_by_target.get(proposition["key"], [])
                ),
                "sentence_closure_checked": True,
                "status": "pass",
            }
            for proposition in sorted(dossier["propositions"], key=lambda item: item["key"])
        ],
        "counts": {
            "expected_dossier_counts": summary["dossier_counts"],
            "observed_dossier_counts": summary["dossier_counts"],
            "expected_accepted_relation_counts": summary["accepted_relation_counts"],
            "observed_accepted_relation_counts": summary["accepted_relation_counts"],
            "relation_derived": True,
            "status": "pass",
        },
        "evaluations": [
            {
                "evaluation_key": evaluation["key"],
                "source_graph_sha256": summary["source_graph_sha256"],
                "reason_codes": evaluation["reason_codes"],
                "same_source_graph_checked": True,
                "materially_distinct_checked": True,
                "status": "pass",
            }
            for evaluation in sorted(dossier["evaluations"], key=lambda item: item["key"])
        ],
    }


def validate_commands(commands: Any) -> None:
    require(isinstance(commands, list) and commands, "receipt.commands: must be non-empty")
    signatures: set[tuple[str, ...]] = set()
    fields = {
        "argv",
        "cwd",
        "started_at",
        "completed_at",
        "exit_code",
        "stdout_sha256",
        "stderr_sha256",
    }
    for index, command in enumerate(commands):
        context = f"receipt.commands[{index}]"
        require_exact_fields(command, fields, context)
        argv = command["argv"]
        require(
            isinstance(argv, list)
            and argv
            and all(isinstance(item, str) and item for item in argv),
            f"{context}.argv: invalid",
        )
        require(isinstance(command["cwd"], str) and command["cwd"], f"{context}.cwd")
        started = require_timestamp(command["started_at"], f"{context}.started_at")
        completed = require_timestamp(command["completed_at"], f"{context}.completed_at")
        require(completed >= started, f"{context}: completion precedes start")
        require(command["exit_code"] == 0, f"{context}: nonzero exit")
        require_sha(command["stdout_sha256"], SHA_RE, f"{context}.stdout_sha256")
        require_sha(command["stderr_sha256"], SHA_RE, f"{context}.stderr_sha256")
        signatures.add(tuple(argv))
    requirements = (
        lambda argv: (
            any(item.endswith("build_candidate.py") for item in argv) and "--check" in argv
        ),
        lambda argv: (
            any(item.endswith("verify_candidate.py") for item in argv) and "--self-test" in argv
        ),
        lambda argv: "ruff" in argv and "check" in argv,
        lambda argv: argv[-2:] == ("make", "check") or argv == ("make", "check"),
    )
    require(
        all(any(predicate(argv) for argv in signatures) for predicate in requirements),
        "receipt.commands: deterministic build, verifier self-test, Ruff, or make check missing",
    )


def git_text(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def validate_review_receipt(
    receipt: dict[str, Any],
    dossier: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    *,
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
            "decision",
            "complete",
        },
        "receipt",
    )
    require(receipt["format"] == REVIEW_FORMAT, "receipt.format: unsupported")
    require(receipt["task_id"] == "EM-0035", "receipt.task_id: mismatch")
    started = require_timestamp(receipt["started_at"], "receipt.started_at")
    completed = require_timestamp(receipt["completed_at"], "receipt.completed_at")
    require(completed >= started, "receipt completion precedes start")

    reviewer = require_exact_fields(
        receipt["reviewer"],
        {
            "id",
            "role",
            "author_agent_id",
            "fresh_clone",
            "reviewer_was_author",
            "authoring_notes_used_as_evidence",
            "notes",
        },
        "receipt.reviewer",
    )
    require(
        isinstance(reviewer["id"], str)
        and reviewer["id"]
        and reviewer["id"] != "codex-em0035-author",
        "receipt.reviewer.id: reviewer must be independently identified",
    )
    require(
        reviewer["author_agent_id"] == "codex-em0035-author",
        "receipt.reviewer.author_agent_id: mismatch",
    )
    require(
        reviewer["role"] == "independent-reviewer",
        "receipt.reviewer.role: mismatch",
    )
    require(reviewer["fresh_clone"] is True, "receipt reviewer did not use a fresh clone")
    require(
        reviewer["reviewer_was_author"] is False,
        "receipt reviewer must not be the author",
    )
    require(
        reviewer["authoring_notes_used_as_evidence"] is False,
        "authoring notes cannot substitute for independent evidence",
    )
    require(
        isinstance(reviewer["notes"], str) and reviewer["notes"].strip(),
        "receipt.reviewer.notes: missing",
    )

    expected_bindings = {
        "candidate_dossier": {
            **summary["candidate_dossier"],
            "dossier_id": summary["dossier_id"],
        },
        "accepted_packet": {
            **summary["accepted_packet"],
            "packet_id": ACCEPTED_PACKET_ID,
        },
        "accepted_em0033_review": summary["accepted_review"],
        "accepted_source_records": summary["accepted_source_records"],
        "candidate_documentation": summary["candidate_documentation"],
    }
    require(
        receipt["bindings"] == expected_bindings,
        "receipt bindings do not match exact candidate and accepted bytes",
    )

    coverage = require_exact_fields(receipt["coverage"], set(summary["ids"]), "receipt.coverage")
    for name, expected in summary["ids"].items():
        require_exact_coverage(coverage[name], expected, f"receipt.coverage.{name}")
    require(
        receipt["review_results"] == expected_review_results(dossier, packet, summary),
        "receipt review_results are incomplete, stale, duplicated, or non-passing",
    )
    validate_commands(receipt["commands"])

    findings = receipt["findings"]
    require(isinstance(findings, list), "receipt.findings: must be an array")
    for index, finding in enumerate(findings):
        require_exact_fields(finding, {"severity", "status", "text"}, f"receipt.findings[{index}]")
        require(
            finding["severity"] in {"material", "minor", "informational"},
            f"receipt.findings[{index}].severity: invalid",
        )
        require(
            finding["status"] in {"resolved", "informational"},
            f"receipt.findings[{index}]: unresolved finding",
        )
        require(
            isinstance(finding["text"], str) and finding["text"].strip(),
            f"receipt.findings[{index}].text: missing",
        )
    limitations = receipt["limitations"]
    require(
        isinstance(limitations, list)
        and limitations
        and all(isinstance(item, str) and item.strip() for item in limitations),
        "receipt.limitations: non-empty limitations required",
    )
    require(receipt["decision"] == "pass", "receipt.decision: must be pass")
    require(receipt["complete"] is True, "receipt.complete: must be true")

    repository = require_exact_fields(
        receipt["repository"],
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
    require(
        isinstance(repository["pull_request"], int)
        and not isinstance(repository["pull_request"], bool)
        and repository["pull_request"] > 0,
        "receipt pull request invalid",
    )
    require(
        isinstance(repository["branch"], str) and repository["branch"],
        "receipt branch missing",
    )
    base = require_sha(repository["reviewed_base"], COMMIT_RE, "receipt reviewed base invalid")
    head = require_sha(
        repository["reviewed_author_head"],
        COMMIT_RE,
        "receipt reviewed author head invalid",
    )
    tree = require_sha(
        repository["reviewed_author_tree"],
        COMMIT_RE,
        "receipt reviewed author tree invalid",
    )
    require_sha(repository["diff_sha256"], SHA_RE, "receipt diff digest invalid")

    git_state = require_exact_fields(
        receipt["git_state"],
        {
            "fresh_clone",
            "pre_review_clean",
            "post_review_clean",
            "unchanged_during_review",
            "pre_review_head",
            "post_review_head",
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

    if not check_git:
        return
    require(git_text("rev-parse", f"{head}^{{tree}}") == tree, "reviewed tree mismatch")
    require(git_text("merge-base", base, head) == base, "reviewed base is not merge-base")
    origin_main = git_text("rev-parse", "origin/main")
    require(origin_main == base, "reviewed base is stale")
    require(
        git_text("merge-base", origin_main, head) == origin_main,
        "main is not an ancestor of reviewed author head",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", head, "HEAD"],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0,
        "reviewed author head is not an ancestor of receipt head",
    )
    receipt_relative = DEFAULT_REVIEW_RECEIPT.relative_to(ROOT).as_posix()
    changed_after = set(filter(None, git_text("diff", "--name-only", head, "HEAD").splitlines()))
    require(
        changed_after == {receipt_relative},
        "candidate or non-receipt path changed after independent review",
    )
    diff = git_bytes("diff", "--binary", "--full-index", "--no-ext-diff", base, head)
    require(
        sha256_bytes(diff) == repository["diff_sha256"],
        "reviewed diff digest mismatch",
    )
    require(not git_text("status", "--porcelain"), "review checkout is not clean")
    require(
        bool(git_text("ls-files", "--error-unmatch", receipt_relative, check=False)),
        "independent review receipt must be tracked",
    )


def valid_review_fixture(
    dossier: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    now = "2026-08-27T00:00:00Z"
    empty_sha = hashlib.sha256(b"").hexdigest()
    command_argv = [
        [
            "python",
            "research/how-we-know/mehrabian-7-38-55/build_candidate.py",
            "--check",
        ],
        [
            "python",
            "research/how-we-know/mehrabian-7-38-55/verify_candidate.py",
            "--self-test",
        ],
        [
            "python",
            "-m",
            "ruff",
            "check",
            "research/how-we-know/mehrabian-7-38-55",
        ],
        ["make", "check"],
    ]
    return {
        "format": REVIEW_FORMAT,
        "task_id": "EM-0035",
        "reviewer": {
            "id": "codex-independent-em0035-reviewer",
            "role": "independent-reviewer",
            "author_agent_id": "codex-em0035-author",
            "fresh_clone": True,
            "reviewer_was_author": False,
            "authoring_notes_used_as_evidence": False,
            "notes": "Shape-only adversarial fixture; no review claim is inferred.",
        },
        "repository": {
            "url": REPOSITORY_URL,
            "pull_request": 1,
            "branch": "fixture",
            "reviewed_base": "0" * 40,
            "reviewed_author_head": "1" * 40,
            "reviewed_author_tree": "2" * 40,
            "diff_sha256": empty_sha,
        },
        "started_at": now,
        "completed_at": now,
        "git_state": {
            "fresh_clone": True,
            "pre_review_clean": True,
            "post_review_clean": True,
            "unchanged_during_review": True,
            "pre_review_head": "1" * 40,
            "post_review_head": "1" * 40,
        },
        "bindings": {
            "candidate_dossier": {
                **summary["candidate_dossier"],
                "dossier_id": summary["dossier_id"],
            },
            "accepted_packet": {
                **summary["accepted_packet"],
                "packet_id": ACCEPTED_PACKET_ID,
            },
            "accepted_em0033_review": summary["accepted_review"],
            "accepted_source_records": summary["accepted_source_records"],
            "candidate_documentation": summary["candidate_documentation"],
        },
        "coverage": {name: sorted(values) for name, values in summary["ids"].items()},
        "review_results": expected_review_results(dossier, packet, summary),
        "commands": [
            {
                "argv": argv,
                "cwd": ".",
                "started_at": now,
                "completed_at": now,
                "exit_code": 0,
                "stdout_sha256": empty_sha,
                "stderr_sha256": empty_sha,
            }
            for argv in command_argv
        ],
        "findings": [],
        "limitations": ["Shape-only fixture; the scientific evidence remains bounded by EM-0033."],
        "decision": "pass",
        "complete": True,
    }


def run_adversarial_self_test(
    dossier: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    fixture = valid_review_fixture(dossier, packet, summary)
    validate_review_receipt(fixture, dossier, packet, summary, check_git=False)

    mutations = [
        lambda value: value["reviewer"].update({"reviewer_was_author": True}),
        lambda value: value["reviewer"].update({"authoring_notes_used_as_evidence": True}),
        lambda value: value["reviewer"].update({"id": value["reviewer"]["author_agent_id"]}),
        lambda value: value["bindings"]["candidate_dossier"].update({"sha256": "0" * 64}),
        lambda value: value["coverage"]["span_keys"].pop(),
        lambda value: value["coverage"]["relation_keys"].append(
            value["coverage"]["relation_keys"][0]
        ),
        lambda value: value["review_results"]["sources"].pop(),
        lambda value: value["review_results"]["spans"][0].update({"locator_checked": False}),
        lambda value: value["review_results"]["calculations"][0].update({"reproduced": False}),
        lambda value: value["review_results"]["lineages"][0]["basis_span_keys"].pop(),
        lambda value: value["review_results"]["propositions"][0].update(
            {"sentence_closure_checked": False}
        ),
        lambda value: value["review_results"]["counts"].update({"relation_derived": False}),
        lambda value: value["review_results"]["evaluations"][0].update(
            {"materially_distinct_checked": False}
        ),
        lambda value: value["commands"].pop(),
        lambda value: value["git_state"].update({"post_review_clean": False}),
        lambda value: value.update(
            {"findings": [{"severity": "material", "status": "open", "text": "gap"}]}
        ),
        lambda value: value.update({"limitations": []}),
        lambda value: value.update({"decision": "changes-required"}),
        lambda value: value.update({"complete": False}),
        lambda value: value.update(
            {
                "started_at": "2026-08-27T01:00:00Z",
                "completed_at": "2026-08-27T00:00:00Z",
            }
        ),
    ]
    for index, mutate in enumerate(mutations):
        forged = copy.deepcopy(fixture)
        mutate(forged)
        try:
            validate_review_receipt(forged, dossier, packet, summary, check_git=False)
        except VerificationError:
            continue
        raise VerificationError(f"adversarial receipt mutation {index} was accepted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-receipt", type=Path, default=DEFAULT_REVIEW_RECEIPT)
    parser.add_argument("--require-review", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        dossier, packet, summary = verify_candidate()
        if args.self_test:
            run_adversarial_self_test(dossier, packet, summary)
            summary["adversarial_tests"] = "passed"
        receipt = None
        if args.review_receipt.is_file() or args.require_review:
            require(args.review_receipt.is_file(), "independent EM-0035 review receipt missing")
            receipt = load(args.review_receipt)
            validate_review_receipt(receipt, dossier, packet, summary, check_git=True)
        summary["independent_review_complete"] = receipt is not None
        if receipt is not None:
            summary["reviewer"] = receipt["reviewer"]["id"]
            summary["review_decision"] = receipt["decision"]
        summary["ids"] = {name: sorted(values) for name, values in summary["ids"].items()}
        print(json.dumps(summary, indent=2, sort_keys=True))
    except VerificationError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
