"""Fail-closed verification for the frozen EM-0026 trace protocol and captures."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKET_ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = PACKET_ROOT / "protocol.json"
TARGET_PATH = PACKET_ROOT / "target-decision.json"
PROMPT_PATH = PACKET_ROOT / "frozen-prompt.md"
TEMPLATE_PATH = PACKET_ROOT / "trace-record-template.json"
TRACES_PATH = PACKET_ROOT / "traces"


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


def verify_frozen_inputs() -> tuple[dict[str, Any], list[str]]:
    protocol = load_json(PROTOCOL_PATH)
    target = load_json(TARGET_PATH)
    template = load_json(TEMPLATE_PATH)
    prompt_sha256, prompt_bytes = identity(PROMPT_PATH)
    target_sha256, target_bytes = identity(TARGET_PATH)

    require(protocol.get("task_id") == "EM-0026", "protocol task mismatch")
    require(protocol.get("status") == "frozen-before-traces", "protocol is not frozen")
    require(target.get("status") == "frozen-before-traces", "target decision is not frozen")
    require(target.get("decision") == "proceed", "target decision does not permit collection")
    require(protocol.get("evidence_cutoff") == target.get("evidence_cutoff"), "cutoff mismatch")
    require(protocol.get("prompt_sha256") == prompt_sha256, "frozen prompt digest drift")
    require(protocol.get("prompt_bytes") == prompt_bytes, "frozen prompt byte-count drift")
    require(protocol.get("target_decision_sha256") == target_sha256, "target digest drift")
    require(protocol.get("target_decision_bytes") == target_bytes, "target byte-count drift")
    prompt_text = "\n".join(
        line.removeprefix("> ") for line in PROMPT_PATH.read_text().splitlines()
    )
    require(
        normalized_text(target["question"]) in normalized_text(prompt_text),
        "target question missing from prompt",
    )

    matrix = protocol.get("capture_matrix")
    require(isinstance(matrix, list) and len(matrix) == 8, "capture matrix must have eight slots")
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
    require(
        template.get("protocol_id") == protocol.get("protocol_id"),
        "template protocol mismatch",
    )
    require(template.get("prompt", {}).get("sha256") == prompt_sha256, "template prompt drift")
    require(template.get("prompt", {}).get("bytes") == prompt_bytes, "template prompt bytes drift")
    require(template.get("inherited_conversation_turns") == 0, "template context drift")
    return protocol, run_ids


def verify_traces(protocol: dict[str, Any], run_ids: list[str], require_complete: bool) -> int:
    trace_files = sorted(TRACES_PATH.glob("*.json")) if TRACES_PATH.exists() else []
    if require_complete:
        require(len(trace_files) == 8, "complete packet requires exactly eight trace records")
    seen: set[str] = set()
    prompt_sha256 = protocol["prompt_sha256"]
    prompt_bytes = protocol["prompt_bytes"]
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
            trace.get("prompt", {}).get("sha256") == prompt_sha256,
            f"prompt drift for {run_id}",
        )
        require(
            trace.get("prompt", {}).get("bytes") == prompt_bytes,
            f"prompt bytes drift for {run_id}",
        )
        answer = trace.get("answer", {})
        answer_path = answer.get("path")
        if trace.get("status") == "completed":
            require(
                isinstance(answer_path, str) and answer_path != "unknown",
                f"missing answer for {run_id}",
            )
            candidate = REPO_ROOT / answer_path
            require(candidate.is_file(), f"answer artifact missing for {run_id}")
            answer_sha256, answer_bytes = identity(candidate)
            require(answer.get("sha256") == answer_sha256, f"answer digest drift for {run_id}")
            require(answer.get("bytes") == answer_bytes, f"answer byte-count drift for {run_id}")
    if require_complete:
        require(seen == set(run_ids), "trace records do not close the frozen matrix")
    return len(trace_files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-traces", action="store_true")
    args = parser.parse_args()
    protocol, run_ids = verify_frozen_inputs()
    trace_count = verify_traces(protocol, run_ids, args.require_traces)
    print(
        json.dumps(
            {
                "protocol_valid": True,
                "protocol_id": protocol["protocol_id"],
                "frozen_run_slots": len(run_ids),
                "captured_trace_records": trace_count,
                "trace_matrix_complete": trace_count == len(run_ids),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
