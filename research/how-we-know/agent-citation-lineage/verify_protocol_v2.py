"""Fail-closed verification for the frozen EM-0026 v2 trace protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKET_ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = PACKET_ROOT / "protocol-v2.json"
TARGET_PATH = PACKET_ROOT / "target-decision.json"
PROMPT_PATH = PACKET_ROOT / "frozen-prompt-v2.md"
TEMPLATE_PATH = PACKET_ROOT / "trace-record-template-v2.json"
V1_PROTOCOL_PATH = PACKET_ROOT / "protocol.json"
FAILED_PREFLIGHT_PATH = (
    PACKET_ROOT / "failed-preflight" / "20260823T031151Z-v1-transport.json"
)

ANSWER_KEYS = {
    "question",
    "cutoff",
    "answer",
    "results",
    "sources",
    "counterevidence",
    "limitations",
    "unresolved",
    "search_notes",
}
RESULT_KEYS = {
    "result_id",
    "proposition",
    "reported_value",
    "scope",
    "source_ids",
    "exact_span_ids",
    "interpretation",
}
SOURCE_KEYS = {
    "source_id",
    "url",
    "title",
    "authors_or_org",
    "date",
    "identifier",
    "edition",
    "retrieval_status",
    "media_type",
    "license",
    "exact_spans",
}
SPAN_KEYS = {"span_id", "locator", "quote", "supports"}


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path.relative_to(REPO_ROOT)}: {exc}")
    require(isinstance(value, dict), f"{path.relative_to(REPO_ROOT)} must contain an object")
    return value


def identity(path: Path) -> tuple[str, int]:
    payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest(), len(payload)


def normalized_text(value: str) -> str:
    return " ".join(value.split())


def require_identity(
    protocol: dict[str, Any], path: Path, prefix: str, label: str
) -> None:
    digest, byte_count = identity(path)
    require(protocol.get(f"{prefix}_sha256") == digest, f"{label} digest drift")
    require(protocol.get(f"{prefix}_bytes") == byte_count, f"{label} byte-count drift")


def verify_frozen_inputs() -> tuple[dict[str, Any], list[str], Path]:
    protocol = load_json(PROTOCOL_PATH)
    target = load_json(TARGET_PATH)
    template = load_json(TEMPLATE_PATH)
    failed_preflight = load_json(FAILED_PREFLIGHT_PATH)

    require(protocol.get("task_id") == "EM-0026", "protocol task mismatch")
    require(protocol.get("protocol_id") == "em-0026-agent-citation-trace-v2", "protocol ID drift")
    require(protocol.get("status") == "frozen-before-traces", "protocol is not frozen")
    require(target.get("status") == "frozen-before-traces", "target decision is not frozen")
    require(target.get("decision") == "proceed", "target decision does not permit collection")
    require(protocol.get("evidence_cutoff") == target.get("evidence_cutoff"), "cutoff mismatch")
    require(
        protocol.get("supersedes_failed_protocol")
        == failed_preflight.get("protocol_id")
        == "em-0026-agent-citation-trace-v1",
        "failed v1 protocol linkage mismatch",
    )
    require(
        failed_preflight.get("status") == "aborted-before-final-answer-capture",
        "v1 failure status drift",
    )
    require(failed_preflight.get("answers_captured") == 0, "v1 answer count drift")
    require(failed_preflight.get("citations_admitted") == 0, "v1 citation count drift")
    require(failed_preflight.get("replacement_runs_started") is False, "v1 replacement drift")

    require_identity(protocol, PROMPT_PATH, "prompt", "frozen v2 prompt")
    require_identity(protocol, TARGET_PATH, "target_decision", "target decision")
    require_identity(
        protocol,
        V1_PROTOCOL_PATH,
        "supersedes_failed_protocol",
        "superseded v1 protocol",
    )
    require_identity(
        protocol,
        FAILED_PREFLIGHT_PATH,
        "failed_preflight",
        "v1 failed-preflight record",
    )

    prompt_text = "\n".join(
        line.removeprefix("> ") for line in PROMPT_PATH.read_text().splitlines()
    )
    require(
        normalized_text(target["question"]) in normalized_text(prompt_text),
        "target question missing from prompt",
    )

    matrix = protocol.get("capture_matrix")
    require(isinstance(matrix, list) and len(matrix) == 8, "capture matrix must have eight slots")
    require(all(isinstance(item, dict) for item in matrix), "capture slots must be objects")
    run_ids = [item.get("run_id") for item in matrix]
    require(len(set(run_ids)) == 8, "capture matrix run IDs must be unique")
    require(
        Counter(item.get("requested_model_profile") for item in matrix)
        == Counter({"gpt-5.6-sol": 4, "gpt-5.6-terra": 4}),
        "capture matrix must contain four runs per frozen profile",
    )
    require(
        all(item.get("requested_reasoning_effort") == "high" for item in matrix),
        "all capture slots must request high reasoning effort",
    )
    controls = protocol.get("run_controls", {})
    require(controls.get("inherited_conversation_turns") == 0, "context isolation drift")
    require(controls.get("same_prompt_for_every_run") is True, "prompt equality is not required")
    require(controls.get("replacement_runs") == "forbidden", "replacement runs are not forbidden")

    prompt_sha256, prompt_bytes = identity(PROMPT_PATH)
    require(
        template.get("protocol_id") == protocol.get("protocol_id"),
        "template protocol mismatch",
    )
    require(template.get("prompt", {}).get("sha256") == prompt_sha256, "template prompt drift")
    require(template.get("prompt", {}).get("bytes") == prompt_bytes, "template prompt bytes drift")
    require(template.get("inherited_conversation_turns") == 0, "template context drift")

    trace_relative = protocol.get("trace_directory")
    require(isinstance(trace_relative, str), "trace directory is not declared")
    trace_path = REPO_ROOT / trace_relative
    require(
        trace_path.resolve().is_relative_to(PACKET_ROOT.resolve()),
        "trace directory escapes the research packet",
    )
    return protocol, run_ids, trace_path


def verify_answer_shape(answer_path: Path, run_id: str) -> None:
    answer = load_json(answer_path)
    require(answer.keys() >= ANSWER_KEYS, f"missing required answer keys for {run_id}")
    for key in ("results", "sources", "counterevidence", "limitations", "unresolved"):
        require(isinstance(answer[key], list), f"answer {key} must be an array for {run_id}")
    for result in answer["results"]:
        require(isinstance(result, dict), f"result must be an object for {run_id}")
        require(result.keys() >= RESULT_KEYS, f"result fields missing for {run_id}")
    for source in answer["sources"]:
        require(isinstance(source, dict), f"source must be an object for {run_id}")
        require(source.keys() >= SOURCE_KEYS, f"source fields missing for {run_id}")
        require(
            isinstance(source["exact_spans"], list),
            f"source spans must be an array for {run_id}",
        )
        for span in source["exact_spans"]:
            require(isinstance(span, dict), f"span must be an object for {run_id}")
            require(span.keys() >= SPAN_KEYS, f"span fields missing for {run_id}")


def verify_traces(
    protocol: dict[str, Any], run_ids: list[str], trace_path: Path, require_complete: bool
) -> int:
    trace_files = sorted(trace_path.glob("*.json")) if trace_path.exists() else []
    if require_complete:
        require(len(trace_files) == 8, "complete packet requires exactly eight trace records")
    seen: set[str] = set()
    matrix = {item["run_id"]: item for item in protocol["capture_matrix"]}
    terminal = {"completed", "failed", "refused", "empty", "malformed", "incomplete"}
    for path in trace_files:
        trace = load_json(path)
        run_id = trace.get("run_id")
        require(run_id in run_ids, f"unexpected trace run ID in {path.name}")
        require(run_id not in seen, f"duplicate trace record for {run_id}")
        seen.add(run_id)
        require(trace.get("task_id") == "EM-0026", f"task mismatch for {run_id}")
        require(
            trace.get("protocol_id") == protocol["protocol_id"],
            f"protocol mismatch for {run_id}",
        )
        require(
            isinstance(trace.get("protocol_commit"), str)
            and len(trace["protocol_commit"]) == 40
            and all(character in "0123456789abcdef" for character in trace["protocol_commit"]),
            f"protocol commit is not an exact SHA for {run_id}",
        )
        require(trace.get("status") in terminal, f"nonterminal status for {run_id}")
        require(trace.get("replacement_for") is None, f"replacement trace forbidden for {run_id}")
        require(trace.get("inherited_conversation_turns") == 0, f"context drift for {run_id}")
        require(
            trace.get("requested_model_profile") == matrix[run_id]["requested_model_profile"],
            f"model-profile mismatch for {run_id}",
        )
        require(
            trace.get("requested_reasoning_effort")
            == matrix[run_id]["requested_reasoning_effort"],
            f"reasoning-effort mismatch for {run_id}",
        )
        require(
            trace.get("prompt", {}).get("sha256") == protocol["prompt_sha256"],
            f"prompt drift for {run_id}",
        )
        require(
            trace.get("prompt", {}).get("bytes") == protocol["prompt_bytes"],
            f"prompt bytes drift for {run_id}",
        )
        disclosure = trace.get("disclosure_review", {})
        for key in (
            "hidden_reasoning_included",
            "private_context_included",
            "credentials_or_account_state_included",
            "personal_data_included",
        ):
            require(disclosure.get(key) is False, f"disclosure boundary failed for {run_id}: {key}")

        answer = trace.get("answer", {})
        answer_path = answer.get("path")
        if isinstance(answer_path, str) and answer_path != "unknown":
            candidate = REPO_ROOT / answer_path
            require(candidate.is_file(), f"answer artifact missing for {run_id}")
            answer_sha256, answer_bytes = identity(candidate)
            require(answer.get("sha256") == answer_sha256, f"answer digest drift for {run_id}")
            require(answer.get("bytes") == answer_bytes, f"answer byte-count drift for {run_id}")
            if answer.get("json_valid") is True:
                verify_answer_shape(candidate, run_id)
        if trace.get("status") == "completed":
            require(
                isinstance(answer_path, str) and answer_path != "unknown",
                f"completed trace lacks answer artifact for {run_id}",
            )
            require(
                answer.get("json_valid") is True,
                f"completed trace is not valid JSON for {run_id}",
            )
    if require_complete:
        require(seen == set(run_ids), "trace records do not close the frozen matrix")
    return len(trace_files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-traces", action="store_true")
    args = parser.parse_args()
    protocol, run_ids, trace_path = verify_frozen_inputs()
    trace_count = verify_traces(protocol, run_ids, trace_path, args.require_traces)
    print(
        json.dumps(
            {
                "protocol_valid": True,
                "protocol_id": protocol["protocol_id"],
                "superseded_protocol": protocol["supersedes_failed_protocol"],
                "frozen_run_slots": len(run_ids),
                "captured_trace_records": trace_count,
                "trace_matrix_complete": trace_count == len(run_ids),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
