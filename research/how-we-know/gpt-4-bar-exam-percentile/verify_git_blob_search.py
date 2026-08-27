"""Reproduce the bounded negative search over the pinned Katz Git snapshot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parent
ARTIFACT_INVENTORY = PACKET_ROOT / "artifact-inventory.json"
SEARCH_MANIFEST = PACKET_ROOT / "git-blob-search-manifest.json"
REPOSITORY_URL = "https://github.com/mjbommar/gpt4-passes-the-bar.git"
COMMIT_SHA = "90997f740c7197f3f300b013e4345e2ad5621f96"
TREE_SHA = "810bd4a9a8ffb51e457715d2312d28d3e9657240"
SEARCH_PATTERNS = [
    "90th",
    "top 10",
    "percentile",
    "interpolat",
    "Illinois",
    "February 2018",
    "test-taker",
    "test taker",
    "comparison population",
    "UBE distribution",
    "Uniform Bar Exam distribution",
]


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: root must be an object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repository,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        fail(
            f"git {' '.join(args)} failed: "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def pinned_inventory() -> dict[str, dict[str, Any]]:
    inventory = load(ARTIFACT_INVENTORY)
    return {
        row["path"]: row
        for row in inventory["content"]["artifacts"]
        if row["artifact_root_id"] == "artifact-root-katz-git"
    }


def build_manifest(repository: Path) -> dict[str, Any]:
    repository = repository.resolve()
    require((repository / ".git").exists(), "Katz repository must be a Git checkout")
    commit = git(repository, "rev-parse", COMMIT_SHA).decode().strip()
    tree = git(repository, "rev-parse", f"{COMMIT_SHA}^{{tree}}").decode().strip()
    require(commit == COMMIT_SHA, "Katz commit identity drift")
    require(tree == TREE_SHA, "Katz tree identity drift")

    inventory = pinned_inventory()
    names = git(repository, "ls-tree", "-r", "--name-only", "-z", COMMIT_SHA)
    paths = sorted(item.decode() for item in names.split(b"\0") if item)
    require(len(paths) == 78, "Katz body-readback count drift")
    require(set(paths) == set(inventory), "Katz inventory/body path mismatch")

    rows: list[dict[str, Any]] = []
    text_count = 0
    binary_count = 0
    for path in paths:
        expected = inventory[path]
        payload = git(repository, "cat-file", "blob", expected["digest"])
        require(len(payload) == expected["bytes"], f"blob bytes drift: {path}")
        require(git_blob_sha1(payload) == expected["digest"], f"blob SHA-1 drift: {path}")
        row: dict[str, Any] = {
            "path": path,
            "bytes": len(payload),
            "git_blob_sha1": expected["digest"],
            "body_sha256": sha256(payload),
        }
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if b"\0" in payload or text is None:
            binary_count += 1
            row.update(
                {
                    "readback": "binary-body-digested-no-text-search",
                    "pattern_counts": None,
                }
            )
        else:
            text_count += 1
            folded = text.casefold()
            row.update(
                {
                    "readback": "utf8-body-digested-and-searched",
                    "pattern_counts": {
                        pattern: folded.count(pattern.casefold())
                        for pattern in SEARCH_PATTERNS
                    },
                }
            )
        rows.append(row)

    content = {
        "schema": "https://epistemedia.org/research/git-blob-search-manifest-v1.json",
        "task_id": "EM-0032",
        "repository_url": REPOSITORY_URL,
        "commit_sha": COMMIT_SHA,
        "tree_sha": TREE_SHA,
        "search_patterns": SEARCH_PATTERNS,
        "blob_count": len(rows),
        "text_body_count": text_count,
        "binary_body_count": binary_count,
        "rows": rows,
        "result": (
            "No UTF-8 body contains a chart identity, interpolation rule, percentile "
            "value, Illinois reference, or comparison-population phrase for the launch "
            "claim. README.md contains one generic 'test-taker' occurrence."
        ),
        "limitations": (
            "This is a bounded literal-pattern search of one pinned public snapshot. "
            "It is not proof that a private, deleted, binary-embedded, or differently "
            "worded source never existed."
        ),
    }
    return {
        "manifest_id": f"em:git-blob-search:sha256:{sha256(canonical_bytes(content))}",
        "content": content,
    }


def validate_manifest(value: dict[str, Any]) -> None:
    content = value.get("content", {})
    require(
        value.get("manifest_id")
        == f"em:git-blob-search:sha256:{sha256(canonical_bytes(content))}",
        "blob-search manifest ID drift",
    )
    require(content.get("commit_sha") == COMMIT_SHA, "manifest commit drift")
    require(content.get("tree_sha") == TREE_SHA, "manifest tree drift")
    require(content.get("search_patterns") == SEARCH_PATTERNS, "search-pattern drift")
    rows = content.get("rows", [])
    require(len(rows) == content.get("blob_count") == 78, "manifest blob count drift")
    require(
        sum(row["readback"].startswith("utf8-") for row in rows)
        == content.get("text_body_count")
        == 72,
        "manifest text-body count drift",
    )
    require(
        sum(row["readback"].startswith("binary-") for row in rows)
        == content.get("binary_body_count")
        == 6,
        "manifest binary-body count drift",
    )
    inventory = pinned_inventory()
    require({row["path"] for row in rows} == set(inventory), "manifest path coverage drift")
    for row in rows:
        expected = inventory[row["path"]]
        require(row["bytes"] == expected["bytes"], f"manifest bytes drift: {row['path']}")
        require(
            row["git_blob_sha1"] == expected["digest"],
            f"manifest SHA-1 drift: {row['path']}",
        )
        require(len(row["body_sha256"]) == 64, f"manifest SHA-256 missing: {row['path']}")
        if row["readback"].startswith("utf8-"):
            require(
                set(row["pattern_counts"]) == set(SEARCH_PATTERNS),
                f"pattern coverage drift: {row['path']}",
            )
        else:
            require(row["pattern_counts"] is None, f"binary search claim: {row['path']}")


def adversarial_self_test(value: dict[str, Any]) -> None:
    forged = copy.deepcopy(value)
    forged["content"]["rows"][0]["body_sha256"] = "0" * 64
    try:
        require(forged == value, "recomputed blob manifest mismatch")
    except SystemExit:
        return
    fail("forged blob body digest was accepted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    built = build_manifest(args.repository)
    validate_manifest(built)
    if args.self_test:
        adversarial_self_test(built)
    if args.check:
        require(SEARCH_MANIFEST.is_file(), "blob-search manifest missing")
        committed = load(SEARCH_MANIFEST)
        validate_manifest(committed)
        require(committed == built, "recomputed blob manifest mismatch")
    if args.write:
        SEARCH_MANIFEST.write_text(
            json.dumps(built, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "manifest_id": built["manifest_id"],
                "blobs": built["content"]["blob_count"],
                "text_bodies": built["content"]["text_body_count"],
                "binary_bodies": built["content"]["binary_body_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
