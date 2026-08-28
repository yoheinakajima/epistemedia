#!/usr/bin/env python3
"""Fail-closed validation for the EM-0034 Case 003 candidate dossier."""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from build_candidate import (
    ACCEPTED_PACKET_ID,
    ARTIFACT_INVENTORY_PATH,
    GIT_SEARCH_PATH,
    OUTPUT_PATH,
    PACKET_PATH,
    REVIEW_PATH,
    SOURCE_RECORDS_PATH,
    build_candidate,
    canonical_json,
    dossier_key,
    reproduce_derivations,
    sha256_bytes,
)

from epistemedia.dossier import validate_dossier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOSSIER_DOC_PATH = HERE / "DOSSIER.md"
PLAN_PATH = ROOT / "docs/execution-plans/EM-0034.md"
DEFAULT_REVIEW_RECEIPT = HERE / "independent-em0034-review-receipt.json"
REVIEW_FORMAT = "epistemedia-independent-dossier-review-v1"
REPOSITORY_URL = "https://github.com/yoheinakajima/epistemedia"
ACCEPTED_EM0032_COMMIT = "700a822f38d00d13cc0661fd577bdb7e6e5b34dd"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ACCEPTED_PATHS = (
    "docs/execution-plans/EM-0032.md",
    "docs/research/case-003-gpt-4-bar-exam-percentile.md",
    "research/how-we-know/gpt-4-bar-exam-percentile/README.md",
    "research/how-we-know/gpt-4-bar-exam-percentile/artifact-inventory.json",
    "research/how-we-know/gpt-4-bar-exam-percentile/build_packet.py",
    "research/how-we-know/gpt-4-bar-exam-percentile/candidate-packet.json",
    "research/how-we-know/gpt-4-bar-exam-percentile/git-blob-search-manifest.json",
    "research/how-we-know/gpt-4-bar-exam-percentile/independent-review-receipt.json",
    "research/how-we-know/gpt-4-bar-exam-percentile/normalize_html_visible_text.py",
    "research/how-we-know/gpt-4-bar-exam-percentile/source-records.json",
    "research/how-we-know/gpt-4-bar-exam-percentile/verify_git_blob_search.py",
    "research/how-we-know/gpt-4-bar-exam-percentile/verify_packet.py",
    "runs/proposals/20260827T015840Z-47595685f3a5.json",
    "runs/proposals/20260827T155153Z-29d70e6b9e44.json",
    "runs/proposals/20260827T193633Z-20e2fc3af0dd.json",
    "runs/proposals/20260827T211411Z-db2c00b6869a.json",
    "runs/proposals/20260827T213645Z-2080bbbc9450.json",
)


class VerificationError(ValueError):
    """Raised when candidate or receipt validation fails closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: must contain an object")
    return value


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def file_identity(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def verify_accepted_bytes() -> None:
    for relative in ACCEPTED_PATHS:
        path = ROOT / relative
        require(path.is_file(), f"accepted EM-0032 artifact missing: {relative}")
        accepted = git_bytes("show", f"{ACCEPTED_EM0032_COMMIT}:{relative}")
        require(path.read_bytes() == accepted, f"accepted EM-0032 byte drift: {relative}")


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


def expected_bindings() -> list[dict[str, Any]]:
    return [
        file_identity(PACKET_PATH),
        file_identity(REVIEW_PATH),
        file_identity(SOURCE_RECORDS_PATH),
        file_identity(ARTIFACT_INVENTORY_PATH),
        file_identity(GIT_SEARCH_PATH),
    ]


def verify_candidate_document(
    dossier: dict[str, Any], packet: dict[str, Any], *, require_exact_build: bool
) -> dict[str, Any]:
    validate_dossier(dossier)
    if require_exact_build:
        require(dossier == build_candidate(), "candidate differs from deterministic build")
    require(packet.get("packet_id") == ACCEPTED_PACKET_ID, "accepted packet ID drift")
    content = packet["content"]
    source_register = content["source_records"]
    sources = source_register["sources"]
    claims = source_register["claims"]
    derivations = content["derivations"]
    lineages = source_register["lineages"]
    edges = source_register["lineage_edges"]
    require(derivations == reproduce_derivations(), "calculation reproduction drift")
    require(dossier["stage"] == "draft", "candidate must remain draft")
    require(
        all(
            marker in dossier["scope"]
            for marker in ("not admitted", "not featured", "not live", "not published")
        ),
        "candidate admission boundary drift",
    )

    expected_work_keys = {source["work_id"] for source in sources}
    expected_edition_keys = {dossier_key(source["edition_id"]) for source in sources}
    expected_span_keys = {span["span_id"] for source in sources for span in source["spans"]}
    expected_claim_keys = {claim["claim_id"] for claim in claims}
    expected_calculation_keys = {item["derivation_id"] for item in derivations}
    expected_proposition_keys = (
        expected_claim_keys
        | expected_calculation_keys
        | {
            "prop-reviewed-source-register",
            "prop-encyclopedia-evaluation",
            "prop-skeptical-evaluation",
        }
    )
    expected_lineage_keys = {item["lineage_id"] for item in lineages} | {
        "lineage-reviewed-source-register",
        "lineage-evaluation-synthesis",
    }
    expected_edge_keys = {item["edge_id"] for item in edges}
    expected_assertion_keys = {
        f"assertion-{key}" for key in expected_claim_keys | expected_calculation_keys
    } | {
        "assertion-reviewed-source-register",
        "assertion-encyclopedia-evaluation",
        "assertion-skeptical-evaluation",
    }
    expected_relation_keys = {
        f"relation-{key}" for key in expected_assertion_keys
    } | expected_edge_keys

    actual_sets = {
        "source_work_keys": {item["key"] for item in dossier["source_works"]},
        "edition_keys": {item["key"] for item in dossier["editions"]},
        "span_keys": {item["key"] for item in dossier["spans"]},
        "proposition_keys": {item["key"] for item in dossier["propositions"]},
        "lineage_keys": {item["key"] for item in dossier["lineages"]},
        "assertion_keys": {item["key"] for item in dossier["assertions"]},
        "relation_keys": {item["key"] for item in dossier["evidence_relations"]},
        "calculation_ids": expected_calculation_keys,
        "lineage_edge_ids": expected_edge_keys,
    }
    expected_sets = {
        "source_work_keys": expected_work_keys,
        "edition_keys": expected_edition_keys,
        "span_keys": expected_span_keys,
        "proposition_keys": expected_proposition_keys,
        "lineage_keys": expected_lineage_keys,
        "assertion_keys": expected_assertion_keys,
        "relation_keys": expected_relation_keys,
        "calculation_ids": expected_calculation_keys,
        "lineage_edge_ids": expected_edge_keys,
    }
    for key in expected_sets:
        require(actual_sets[key] == expected_sets[key], f"{key} identity drift")

    assertions = {item["key"]: item for item in dossier["assertions"]}
    spans = {item["key"] for item in dossier["spans"]}
    for claim in claims:
        assertion = assertions[f"assertion-{claim['claim_id']}"]
        require(
            set(assertion["span_keys"]) == set(claim["span_ids"]),
            f"claim span closure drift: {claim['claim_id']}",
        )
    parameter_spans = set(
        next(item for item in derivations if item["derivation_id"] == "derive-martinez-parameters")[
            "input_span_ids"
        ]
    )
    for derivation in derivations:
        expected = set(derivation.get("input_span_ids", parameter_spans))
        assertion = assertions[f"assertion-{derivation['derivation_id']}"]
        require(
            set(assertion["span_keys"]) == expected,
            f"calculation span closure drift: {derivation['derivation_id']}",
        )
    relations = {item["key"]: item for item in dossier["evidence_relations"]}
    for edge in edges:
        relation = relations[edge["edge_id"]]
        expected_basis = {span for evidence in edge["evidence"] for span in evidence["span_ids"]}
        require(
            set(relation["basis_span_keys"]) == expected_basis,
            f"typed edge evidence drift: {edge['edge_id']}",
        )
        require(
            set(relation["basis_span_keys"]) <= spans, f"typed edge missing span: {edge['edge_id']}"
        )
        require(
            edge["edge_type"] in relation["note"], f"typed edge dimension drift: {edge['edge_id']}"
        )

    root_count = sum(item["independent_roots"] for item in lineages)
    require(root_count == 7, "five lineage groups must retain seven independent roots")
    model_root = next(
        item for item in lineages if item["lineage_id"] == "lineage-model-performance-root"
    )
    require(
        model_root["independent_roots"] == 1,
        "documents must not inflate the model-performance root",
    )
    dossier_lineages = {item["key"]: item for item in dossier["lineages"]}
    for lineage in lineages:
        projected = dossier_lineages[lineage["lineage_id"]]
        require(
            f"independent_roots={lineage['independent_roots']}" in projected["note"],
            f"projected independent-root count drift: {lineage['lineage_id']}",
        )
    propositions = {item["key"]: item for item in dossier["propositions"]}
    require(
        "298" in propositions["claim-launch-score-label"]["text"]
        and "90th" in propositions["claim-launch-score-label"]["text"],
        "launch score boundary drift",
    )
    require(
        "297" in propositions["claim-score-discrepancy"]["text"]
        and "298" in propositions["claim-score-discrepancy"]["text"],
        "297/298 discrepancy lost",
    )
    require(
        "45/48" in propositions["claim-martinez-passers-conflict"]["text"], "45/48 discrepancy lost"
    )
    require(
        "practicing lawyers" in propositions["claim-no-lawyer-rank"]["text"],
        "lawyer-comparator boundary lost",
    )

    evaluations = {item["policy_id"]: item for item in dossier["evaluations"]}
    require(
        set(evaluations) == {"epistemedia-encyclopedia-v1", "epistemedia-skeptical-v1"},
        "policy identity drift",
    )
    encyclopedia = evaluations["epistemedia-encyclopedia-v1"]
    skeptical = evaluations["epistemedia-skeptical-v1"]
    require(
        encyclopedia["frontier"] == skeptical["frontier"] == ACCEPTED_PACKET_ID,
        "policy source graph drift",
    )
    require(
        encyclopedia["label"] != skeptical["label"]
        and encyclopedia["reason_codes"] != skeptical["reason_codes"],
        "policy views are not materially distinct",
    )

    dossier_identity = file_identity(OUTPUT_PATH)
    return {
        "dossier_id": dossier["dossier_id"],
        "candidate_dossier": dossier_identity,
        "accepted_packet_id": ACCEPTED_PACKET_ID,
        "accepted_bindings": expected_bindings(),
        "source_graph_sha256": graph_digest(dossier),
        "counts": {
            "source_works": len(expected_work_keys),
            "editions": len(expected_edition_keys),
            "spans": len(expected_span_keys),
            "claims": len(expected_claim_keys),
            "calculations": len(expected_calculation_keys),
            "lineage_groups": len(lineages),
            "independent_roots": root_count,
            "lineage_edges": len(expected_edge_keys),
            "propositions": len(expected_proposition_keys),
            "assertions": len(expected_assertion_keys),
            "relations": len(expected_relation_keys),
            "evaluations": len(dossier["evaluations"]),
        },
        "coverage": {key: sorted(value) for key, value in actual_sets.items()},
    }


def verify_candidate_documentation(summary: dict[str, Any]) -> list[dict[str, Any]]:
    require(DOSSIER_DOC_PATH.is_file(), "DOSSIER.md missing")
    require(PLAN_PATH.is_file(), "EM-0034 execution plan missing")
    dossier_text = DOSSIER_DOC_PATH.read_text(encoding="utf-8")
    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    for token in (
        summary["dossier_id"],
        summary["candidate_dossier"]["sha256"],
        ACCEPTED_PACKET_ID,
        summary["source_graph_sha256"],
    ):
        require(token in dossier_text, f"DOSSIER.md identity drift: {token}")
    for token in (
        summary["dossier_id"],
        summary["candidate_dossier"]["sha256"],
        ACCEPTED_PACKET_ID,
    ):
        require(token in plan_text, f"EM-0034 plan identity drift: {token}")
    require(
        "independent EM-0034 dossier review pending" in dossier_text,
        "DOSSIER.md must keep review pending",
    )
    require(
        "fresh-clone independent dossier review pending" in plan_text,
        "plan must keep review pending",
    )
    return [file_identity(DOSSIER_DOC_PATH), file_identity(PLAN_PATH)]


def require_timestamp(value: Any, context: str) -> datetime:
    require(isinstance(value, str) and value, f"{context}: missing timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerificationError(f"{context}: invalid timestamp") from exc
    require(parsed.tzinfo is not None, f"{context}: timezone missing")
    return parsed


def validate_commands(commands: Any) -> None:
    require(isinstance(commands, list) and len(commands) >= 5, "review commands incomplete")
    seen = "\n".join(" ".join(item.get("argv", [])) for item in commands if isinstance(item, dict))
    for item in commands:
        require(
            isinstance(item, dict) and set(item) == {"argv", "exit_code", "stdout_sha256"},
            "review command fields differ",
        )
        require(
            isinstance(item["argv"], list)
            and all(isinstance(arg, str) and arg for arg in item["argv"]),
            "review argv invalid",
        )
        require(item["exit_code"] == 0, "review command did not pass")
        require(
            isinstance(item["stdout_sha256"], str) and SHA_RE.fullmatch(item["stdout_sha256"]),
            "review command digest invalid",
        )
    for marker in ("build_candidate.py", "verify_candidate.py", "pytest", "ruff", "make check"):
        require(marker in seen, f"required review command missing: {marker}")


def validate_review_receipt(
    receipt: dict[str, Any], summary: dict[str, Any], *, require_git_binding: bool
) -> None:
    fields = {
        "format",
        "task_id",
        "repository",
        "reviewer",
        "decision",
        "complete",
        "started_at",
        "completed_at",
        "reviewed",
        "accepted_bindings",
        "coverage",
        "commands",
        "limitations",
        "findings",
        "git_state",
    }
    require(set(receipt) == fields, "review receipt exact fields differ")
    require(
        receipt["format"] == REVIEW_FORMAT and receipt["task_id"] == "EM-0034",
        "review identity drift",
    )
    require(receipt["repository"] == REPOSITORY_URL, "review repository drift")
    reviewer = receipt["reviewer"]
    require(
        isinstance(reviewer, dict)
        and set(reviewer)
        == {"id", "independent", "authored_candidate", "fresh_clone", "model_family"},
        "reviewer fields differ",
    )
    require(
        reviewer["independent"] is True
        and reviewer["authored_candidate"] is False
        and reviewer["fresh_clone"] is True,
        "reviewer independence failed",
    )
    require(
        reviewer["id"] != "codex-em0034-builder"
        and isinstance(reviewer["model_family"], str)
        and reviewer["model_family"],
        "reviewer identity invalid",
    )
    require(
        receipt["decision"] == "pass" and receipt["complete"] is True,
        "review is not a complete pass",
    )
    require(
        require_timestamp(receipt["started_at"], "started_at")
        <= require_timestamp(receipt["completed_at"], "completed_at"),
        "review timestamp order invalid",
    )
    reviewed = receipt["reviewed"]
    require(
        isinstance(reviewed, dict)
        and set(reviewed) == {"base", "head", "tree", "dossier", "source_graph_sha256"},
        "reviewed fields differ",
    )
    for key in ("base", "head", "tree"):
        require(
            isinstance(reviewed[key], str) and COMMIT_RE.fullmatch(reviewed[key]),
            f"reviewed {key} invalid",
        )
    require(
        reviewed["dossier"]
        == {**summary["candidate_dossier"], "dossier_id": summary["dossier_id"]},
        "reviewed dossier binding drift",
    )
    require(
        reviewed["source_graph_sha256"] == summary["source_graph_sha256"],
        "reviewed graph binding drift",
    )
    require(
        receipt["accepted_bindings"] == summary["accepted_bindings"],
        "accepted artifact binding drift",
    )
    require(receipt["coverage"] == summary["coverage"], "review coverage drift")
    validate_commands(receipt["commands"])
    require(
        isinstance(receipt["limitations"], list)
        and any("current" in item.lower() for item in receipt["limitations"]),
        "current-model limitation missing",
    )
    require(isinstance(receipt["findings"], list), "findings must be an array")
    git_state = receipt["git_state"]
    require(
        isinstance(git_state, dict)
        and set(git_state)
        == {
            "pre_clean",
            "post_clean",
            "origin_main",
            "receipt_commit",
            "receipt_tree",
            "receipt_path",
        },
        "git-state fields differ",
    )
    require(
        git_state["pre_clean"] is True and git_state["post_clean"] is True,
        "review worktree not clean",
    )
    require(
        git_state["receipt_path"] == DEFAULT_REVIEW_RECEIPT.relative_to(ROOT).as_posix(),
        "receipt path drift",
    )
    for key in ("origin_main", "receipt_commit", "receipt_tree"):
        require(
            isinstance(git_state[key], str) and COMMIT_RE.fullmatch(git_state[key]),
            f"git-state {key} invalid",
        )
    require(git_state["origin_main"] == reviewed["base"], "reviewed base is stale")
    if require_git_binding:
        require(
            git_text("rev-parse", "HEAD") == git_state["receipt_commit"],
            "receipt commit is not HEAD",
        )
        require(
            git_text("rev-parse", "HEAD^{tree}") == git_state["receipt_tree"], "receipt tree drift"
        )
        require(
            git_text("rev-parse", "HEAD^") == reviewed["head"],
            "receipt is not sole child of reviewed head",
        )
        require(
            git_text("rev-parse", f"{reviewed['head']}^{{tree}}") == reviewed["tree"],
            "reviewed tree drift",
        )
        require(
            git_text("rev-parse", "origin/main") == reviewed["base"],
            "reviewed base no longer current",
        )
        changed = git_text(
            "diff", "--name-only", reviewed["head"], git_state["receipt_commit"]
        ).splitlines()
        require(
            changed == [git_state["receipt_path"]], "receipt child changed more than the receipt"
        )
        require(git_text("status", "--porcelain") == "", "post-review tracked state is not clean")


def valid_review_fixture(summary: dict[str, Any]) -> dict[str, Any]:
    zeros40 = "0" * 40
    zeros64 = "0" * 64
    return {
        "format": REVIEW_FORMAT,
        "task_id": "EM-0034",
        "repository": REPOSITORY_URL,
        "reviewer": {
            "id": "independent-fixture",
            "independent": True,
            "authored_candidate": False,
            "fresh_clone": True,
            "model_family": "independent-test-family",
        },
        "decision": "pass",
        "complete": True,
        "started_at": "2026-08-28T00:00:00Z",
        "completed_at": "2026-08-28T00:01:00Z",
        "reviewed": {
            "base": zeros40,
            "head": "1" * 40,
            "tree": "2" * 40,
            "dossier": {**summary["candidate_dossier"], "dossier_id": summary["dossier_id"]},
            "source_graph_sha256": summary["source_graph_sha256"],
        },
        "accepted_bindings": summary["accepted_bindings"],
        "coverage": summary["coverage"],
        "commands": [
            {
                "argv": ["python", "build_candidate.py", "--check"],
                "exit_code": 0,
                "stdout_sha256": zeros64,
            },
            {
                "argv": ["python", "verify_candidate.py", "--self-test"],
                "exit_code": 0,
                "stdout_sha256": zeros64,
            },
            {"argv": ["python", "-m", "pytest"], "exit_code": 0, "stdout_sha256": zeros64},
            {"argv": ["ruff", "check"], "exit_code": 0, "stdout_sha256": zeros64},
            {"argv": ["make check"], "exit_code": 0, "stdout_sha256": zeros64},
        ],
        "limitations": [
            "This review does not establish current model behavior or general legal competence."
        ],
        "findings": [],
        "git_state": {
            "pre_clean": True,
            "post_clean": True,
            "origin_main": zeros40,
            "receipt_commit": "3" * 40,
            "receipt_tree": "4" * 40,
            "receipt_path": DEFAULT_REVIEW_RECEIPT.relative_to(ROOT).as_posix(),
        },
    }


def run_adversarial_self_test(summary: dict[str, Any]) -> None:
    fixture = valid_review_fixture(summary)
    validate_review_receipt(fixture, summary, require_git_binding=False)
    mutations = []
    for mutate in (
        lambda item: item.update(decision="fail"),
        lambda item: item["reviewer"].update(independent=False),
        lambda item: item["reviewer"].update(authored_candidate=True),
        lambda item: item["reviewed"]["dossier"].update(sha256="0" * 64),
        lambda item: item["reviewed"].update(source_graph_sha256="0" * 64),
        lambda item: item["coverage"]["span_keys"].pop(),
        lambda item: item["accepted_bindings"].pop(),
        lambda item: item["commands"].pop(),
        lambda item: item["limitations"].clear(),
        lambda item: item["git_state"].update(origin_main="9" * 40),
    ):
        forged = copy.deepcopy(fixture)
        mutate(forged)
        mutations.append(forged)
    for forged in mutations:
        try:
            validate_review_receipt(forged, summary, require_git_binding=False)
        except VerificationError:
            continue
        raise VerificationError("adversarial review-receipt mutation was accepted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--require-review", action="store_true")
    parser.add_argument("--review-receipt", type=Path, default=DEFAULT_REVIEW_RECEIPT)
    args = parser.parse_args()
    verify_accepted_bytes()
    packet = load(PACKET_PATH)
    dossier = load(OUTPUT_PATH)
    summary = verify_candidate_document(dossier, packet, require_exact_build=True)
    summary["candidate_documentation"] = verify_candidate_documentation(summary)
    if args.self_test:
        run_adversarial_self_test(summary)
    review_complete = False
    if args.review_receipt.is_file():
        validate_review_receipt(load(args.review_receipt), summary, require_git_binding=True)
        review_complete = True
    if args.require_review and not review_complete:
        raise SystemExit("independent EM-0034 review receipt is required")
    summary["independent_review_complete"] = review_complete
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
