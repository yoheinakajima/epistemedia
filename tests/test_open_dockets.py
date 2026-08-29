from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from test_research_kit import valid_proposal

from epistemedia.cli import main
from epistemedia.core import build_public
from epistemedia.open_dockets import (
    REVIEW_FORMAT,
    load_open_dockets,
    prepare_submission,
    trace_template,
    validate_action_trace,
    validate_submission_directory,
)
from epistemedia.server import Gateway, Request, tool_definitions

ROOT = Path(__file__).resolve().parents[1]


def prompt_digest(character: str) -> str:
    return character * 64


def prepared(tmp_path: Path) -> tuple[dict, dict, dict]:
    bundle = valid_proposal()
    trace = trace_template()
    result = prepare_submission(
        tmp_path,
        bundle,
        trace,
        agent_id="claude-cold-start",
        model_family="claude",
        run_id="claude-run-001",
        prompt_sha256=prompt_digest("1"),
        submitted_at="2026-08-29T20:00:00Z",
    )
    return bundle, trace, result


def review_for(bundle: dict, intake: dict, *, model_family: str = "codex") -> dict:
    return {
        "format": REVIEW_FORMAT,
        "decision": "pass",
        "reviewed_at": "2026-08-29T21:00:00Z",
        "binding": {
            "proposal_id": intake["proposal_id"],
            "proposal_sha256": intake["proposal_sha256"],
            "proposal_bytes": intake["proposal_bytes"],
            "source_pr_number": 100,
            "source_pr_head": "a" * 40,
            "source_pr_url": "https://github.com/yoheinakajima/epistemedia/pull/100",
        },
        "reviewer": {
            "agent_id": "codex-independent-reviewer",
            "model_family": model_family,
            "run_id": "codex-review-001",
            "prompt_sha256": prompt_digest("2"),
            "fresh_clone": True,
            "author_notes_seen": False,
            "authoring_agent_artifacts_used": False,
        },
        "source_reviews": [
            {
                "source_id": source["source_id"],
                "retrieved_url": source["url"],
                "artifact_sha256": "b" * 64,
                "retrieval_status": "independently-retrieved",
                "spans": [
                    {
                        "span_id": span["span_id"],
                        "located": True,
                        "quote_sha256": hashlib.sha256(
                            span["quote"].encode("utf-8")
                        ).hexdigest(),
                        "locator_checked": True,
                        "disposition": "credit-as-bounded",
                    }
                    for span in source["exact_spans"]
                ],
            }
            for source in bundle["sources"]
        ],
        "public": {
            "slug": "test-open-docket",
            "title": "A testable open docket",
            "why_it_matters": "A familiar claim should retain its exact comparison and source.",
            "bounded_reading": "The source supports only the bounded proposition tested here.",
            "practical_reading": "Use the packet as a source map, not as a universal verdict.",
        },
        "limitations": ["One-source test fixture only."],
    }


def promote(tmp_path: Path, *, model_family: str = "codex") -> Path:
    bundle, _, result = prepared(tmp_path)
    submission = result["directory"]
    intake = json.loads((submission / "intake.json").read_text())
    destination = tmp_path / "research" / "open-dockets" / "test-open-docket"
    destination.mkdir(parents=True)
    shutil.copy2(submission / "proposal.json", destination / "proposal.json")
    shutil.copy2(submission / "intake.json", destination / "intake.json")
    (destination / "review.json").write_text(
        json.dumps(review_for(bundle, intake, model_family=model_family), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return destination


def test_submission_is_deterministic_untrusted_and_not_admitted(tmp_path: Path) -> None:
    _, _, result = prepared(tmp_path)
    directory = result["directory"]
    assert {path.name for path in directory.iterdir()} == {
        "PR_BODY.md",
        "intake.json",
        "proposal.json",
    }
    assert validate_submission_directory(directory) == []
    intake = json.loads((directory / "intake.json").read_text())
    assert intake["status"] == "submitted-for-independent-review"
    assert intake["credit"].startswith("zero")
    assert "must not be merged" in (directory / "PR_BODY.md").read_text()


def test_cli_prepares_submission_but_performs_no_git_or_review_action(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "proposal.json").write_text(json.dumps(valid_proposal()))
    (tmp_path / "trace.json").write_text(json.dumps(trace_template()))
    assert (
        main(
            [
                "--root",
                str(tmp_path),
                "research",
                "submit",
                "proposal.json",
                "--trace",
                "trace.json",
                "--agent-id",
                "claude-cold-start",
                "--model-family",
                "claude",
                "--run-id",
                "run-1",
                "--prompt-sha256",
                prompt_digest("1"),
                "--submitted-at",
                "2026-08-29T20:00:00Z",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["submitted"] is False
    assert result["admitted"] is False
    assert result["next_steps"][-1].startswith("gh pr create --draft")
    assert not (tmp_path / ".git").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["events"][0].update(note="chain-of-thought: private"),
        lambda value: value["events"][0].update(note="system prompt follows"),
        lambda value: value["events"][0].update(note="Read /Users/alice/private.txt"),
        lambda value: value["events"][0].update(note="github_pat_" + "a" * 24),
        lambda value: value["events"][0].update(artifact_sha256="not-a-digest"),
        lambda value: value["events"].append(copy.deepcopy(value["events"][0])),
    ],
)
def test_disclosure_safe_trace_fails_closed(mutation) -> None:
    trace = trace_template()
    mutation(trace)
    assert validate_action_trace(trace)


def test_independent_promotion_closes_every_source_and_span(tmp_path: Path) -> None:
    promote(tmp_path)
    dockets, errors = load_open_dockets(tmp_path)
    assert errors == []
    assert len(dockets) == 1
    projection = dockets[0].projection("https://epistemedia.org")
    assert projection["status"] == "independently-reviewed-open-docket"
    assert projection["review"]["reviewer"]["model_family"] == "codex"
    assert projection["representations"]["html"].endswith("/open-dockets/test-open-docket/")


def test_same_model_family_cannot_review_its_own_submission(tmp_path: Path) -> None:
    promote(tmp_path, model_family="claude")
    dockets, errors = load_open_dockets(tmp_path)
    assert dockets == []
    assert any("model_family must differ" in error for error in errors)


def test_missing_span_review_fails_closed(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    review = json.loads((destination / "review.json").read_text())
    review["source_reviews"][0]["spans"] = []
    (destination / "review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    dockets, errors = load_open_dockets(tmp_path)
    assert dockets == []
    assert any("coverage does not exactly match" in error for error in errors)


def test_forged_quote_digest_fails_closed(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    review = json.loads((destination / "review.json").read_text())
    review["source_reviews"][0]["spans"][0]["quote_sha256"] = "c" * 64
    (destination / "review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    dockets, errors = load_open_dockets(tmp_path)
    assert dockets == []
    assert any("quote digest does not match" in error for error in errors)


def test_public_build_exposes_submit_and_empty_open_docket_routes(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    submit = (public / "agents" / "submit" / "index.html").read_text()
    llms = (public / "llms.txt").read_text()
    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    assert "Point an agent here" in submit
    assert "separate reviewer" in submit
    assert "/agents/submit/" in llms
    assert discovery["agent_research"]["github_submission_available"] is True
    assert discovery["open_dockets"]["count"] == 0
    assert (public / "open-dockets" / "index.html").is_file()


def test_ci_uses_base_validator_for_submission_only_pull_requests() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "submission_only" in workflow
    assert "ref: ${{ github.event.pull_request.base.sha }}" in workflow
    assert "PYTHONPATH: validator/src" in workflow
    assert "python validator/ops/validate_submission_pr.py" in workflow
    assert "persist-credentials: false" in workflow
    assert "pull_request_target" not in workflow
    assert "cache-dependency-path: candidate/pyproject.toml" in workflow
    assert "--diff-filter" not in (ROOT / "ops" / "validate_submission_pr.py").read_text()


def test_submission_rejects_symlinks_and_mutated_credit_boundary(tmp_path: Path) -> None:
    _, _, result = prepared(tmp_path)
    directory = result["directory"]
    intake = json.loads((directory / "intake.json").read_text())
    intake["credit"] = "accepted"
    (directory / "intake.json").write_text(json.dumps(intake))
    assert any("credit boundary" in error for error in validate_submission_directory(directory))

    (directory / "intake.json").unlink()
    (directory / "intake.json").symlink_to(directory / "proposal.json")
    assert any("non-symlink" in error for error in validate_submission_directory(directory))


def test_review_pr_url_must_bind_the_exact_pr_number(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    review_path = destination / "review.json"
    review = json.loads(review_path.read_text())
    review["binding"]["source_pr_url"] = (
        "https://github.com/yoheinakajima/epistemedia/pull/101"
    )
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    _, errors = load_open_dockets(tmp_path)
    assert any("source PR URL is invalid" in error for error in errors)


def test_submission_guide_and_open_dockets_have_read_only_interface_parity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    gateway = Gateway(ROOT)
    guide = gateway.call_tool("get_docket_submission_guide", {})
    assert guide == gateway.read_resource("epistemedia://research/submission-guide")
    status, _, response = gateway.handle_api(
        Request("GET", "/v1/research/submission-guide", {}, {}, b"")
    )
    assert status == 200
    assert response["data"] == guide
    assert main(["--root", str(ROOT), "research", "submission-guide"]) == 0
    assert json.loads(capsys.readouterr().out) == guide

    assert gateway.call_tool("list_open_dockets", {}) == []
    status, _, response = gateway.handle_api(
        Request("GET", "/v1/open-dockets", {}, {}, b"")
    )
    assert status == 200
    assert response["data"] == []
    names = {tool["name"] for tool in tool_definitions()}
    assert {"get_docket_submission_guide", "list_open_dockets", "get_open_docket"} <= names
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in tool_definitions())
    assert not any(word in name for name in names for word in ("submit", "admit", "merge"))
