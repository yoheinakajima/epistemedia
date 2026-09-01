from __future__ import annotations

import copy
import hashlib
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from test_research_kit import valid_proposal

from epistemedia.cli import main
from epistemedia.core import build_public
from epistemedia.open_dockets import (
    CONTROLLER_ATTESTATION_FORMAT,
    PROMOTION_RECEIPT_FORMAT,
    REVIEW_FORMAT,
    docket_html,
    docket_markdown,
    load_open_dockets,
    prepare_submission,
    trace_template,
    validate_action_trace,
    validate_question_novelty,
    validate_submission_directory,
    validate_trace_against_bundle,
)
from epistemedia.research_kit import validate_proposal
from epistemedia.server import Gateway, Request, tool_definitions
from ops import validate_promotion_pr as promotion_validator
from ops import validate_submission_pr as submission_validator
from ops.classify_docket_pr import classify_paths

ROOT = Path(__file__).resolve().parents[1]


def prompt_digest(character: str) -> str:
    return character * 64


def trace_for(bundle: dict) -> dict:
    trace = trace_template()
    attempts = {item["source_id"]: item for item in bundle["retrieval_attempts"]}
    for source in bundle["sources"]:
        attempt = attempts[source["source_id"]]
        trace["events"].append(
            {
                "sequence": len(trace["events"]) + 1,
                "action": "retrieve-source",
                "target": source["url"],
                "status": "completed" if attempt["outcome"] == "retrieved" else "failed",
                "artifact_sha256": attempt["artifact_sha256"],
                "note": "source-payload-omitted",
            }
        )
    return trace


def seed_prior_art(root: Path) -> None:
    dossier = root / "research" / "how-we-know" / "fixture" / "dossier.json"
    dossier.parent.mkdir(parents=True, exist_ok=True)
    dossier.write_text(
        json.dumps({"question": "Does a fixture sample change color under blue light?"})
    )
    manifests = root / "catalog" / "dossiers"
    manifests.mkdir(parents=True, exist_ok=True)
    (manifests / "fixture-color-change.json").write_text(
        json.dumps(
            {
                "dossier_path": "research/how-we-know/fixture/dossier.json",
                "slug": "fixture-color-change",
            }
        )
    )


def committed_submission(tmp_path: Path) -> tuple[Path, str, str]:
    repository = tmp_path / "repo"
    repository.mkdir()

    def run_git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repository), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test Contributor")
    run_git("config", "user.email", "contributor@example.invalid")
    (repository / "README.md").write_text("accepted base\n")
    run_git("add", "README.md")
    run_git("commit", "-m", "base")
    base = run_git("rev-parse", "HEAD")
    prepared(repository)
    run_git("add", "research/open-dockets/submissions")
    run_git("commit", "-m", "submit docket")
    return repository, base, run_git("rev-parse", "HEAD")


def prepared(tmp_path: Path) -> tuple[dict, dict, dict]:
    seed_prior_art(tmp_path)
    bundle = valid_proposal()
    trace = trace_for(bundle)
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


def controller_attestation(intake: dict) -> dict:
    return {
        "format": CONTROLLER_ATTESTATION_FORMAT,
        "observed_at": "2026-08-29T20:30:00Z",
        "source_pr_number": 100,
        "source_pr_head": "a" * 40,
        "session_identity_sha256": "9" * 64,
        "provider": "anthropic",
        "model_family": "claude",
        "model_label": "Claude Opus 5",
        "effort": "high",
        "observation_source": "controller-visible-session-metadata",
        "unavailable_fields": [],
        "attestor": "epistemedia-control-room",
    }


def review_for(
    bundle: dict,
    intake: dict,
    attestation: dict,
    *,
    model_family: str = "codex",
) -> dict:
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
            "controller_attestation_sha256": hashlib.sha256(
                (json.dumps(attestation, indent=2, sort_keys=True) + "\n").encode()
            ).hexdigest(),
        },
        "reviewer": {
            "agent_id": "codex-independent-reviewer",
            "model_family": model_family,
            "run_id": "codex-review-001",
            "prompt_sha256": prompt_digest("2"),
            "fresh_clone": True,
            "author_notes_seen": False,
            "authoring_agent_artifacts_used": False,
            "toolchain": ["browser-cdp", "sha256sum"],
            "source_artifact_sha256s": ["b" * 64],
        },
        "source_reviews": [
            {
                "source_id": source["source_id"],
                "retrieved_url": source["url"],
                "artifact_sha256": "b" * 64,
                "retrieval_status": "independently-retrieved",
                "license_checked": True,
                "license_disposition": "confirmed-known",
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
        "claim_atom_reviews": [
            {
                "atom_id": atom["atom_id"],
                "text_sha256": hashlib.sha256(atom["text"].encode()).hexdigest(),
                "source_span_checked": atom["status"] in {"supported", "qualified"},
                "disposition": (
                    "credit-as-bounded"
                    if atom["status"] in {"supported", "qualified"}
                    else f"retain-as-{atom['status']}"
                ),
            }
            for result in bundle["results"]
            for atom in result["claim_atoms"]
        ],
        "calculation_reviews": [
            {
                "calculation_id": item["calculation_id"],
                "equation_checked": True,
                "inputs_checked": True,
                "input_pointers_checked": True,
                "dependency_edges_checked": True,
                "output_reproduced": True,
                "disposition": "credit-as-bounded",
            }
            for item in bundle["calculations"]
        ],
        "retrieval_attempt_reviews": [
            {
                "attempt_id": item["attempt_id"],
                "url_checked": True,
                "time_checked": True,
                "outcome_checked": True,
                "disposition": (
                    "independently-retrieved"
                    if item["outcome"] == "retrieved"
                    else "retained-failed-attempt"
                ),
            }
            for item in bundle["retrieval_attempts"]
        ],
        "dependency_reviews": [
            {
                "dependency_id": item["dependency_id"],
                "kind_checked": True,
                "source_span_checked": True,
                "disposition": "credit-as-bounded",
            }
            for item in bundle["dependencies"]
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
    attestation = controller_attestation(intake)
    (destination / "controller-attestation.json").write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    review = review_for(bundle, intake, attestation, model_family=model_family)
    (destination / "review.json").write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "format": PROMOTION_RECEIPT_FORMAT,
        "decision": "pass",
        "recorded_at": "2026-08-29T21:10:00Z",
        "reviewed_head": "c" * 40,
        "reviewed_tree": "d" * 40,
        "source_pr_number": review["binding"]["source_pr_number"],
        "source_pr_head": review["binding"]["source_pr_head"],
        "proposal_sha256": hashlib.sha256(
            (destination / "proposal.json").read_bytes()
        ).hexdigest(),
        "review_sha256": hashlib.sha256(
            (destination / "review.json").read_bytes()
        ).hexdigest(),
        "controller_attestation_sha256": hashlib.sha256(
            (destination / "controller-attestation.json").read_bytes()
        ).hexdigest(),
        "reviewer": review["reviewer"],
    }
    (destination / "promotion-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
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
    seed_prior_art(tmp_path)
    bundle = valid_proposal()
    (tmp_path / "proposal.json").write_text(json.dumps(bundle))
    (tmp_path / "trace.json").write_text(json.dumps(trace_for(bundle)))
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
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["submitted"] is False
    assert result["admitted"] is False
    assert result["next_steps"][-1].startswith("gh pr create --draft")
    submitted_proposal = json.loads(
        (tmp_path / result["directory"] / "proposal.json").read_text()
    )
    assert submitted_proposal["runtime"]["completed_at"] != bundle["runtime"]["completed_at"]
    assert not (tmp_path / ".git").exists()


def test_local_submission_chronology_fails_closed(tmp_path: Path) -> None:
    seed_prior_art(tmp_path)
    bundle = valid_proposal()
    with pytest.raises(
        ValueError,
        match="runtime completed_at must not follow intake submitted_at",
    ):
        prepare_submission(
            tmp_path,
            bundle,
            trace_for(bundle),
            agent_id="claude-cold-start",
            model_family="claude",
            run_id="claude-run-001",
            prompt_sha256=prompt_digest("1"),
            submitted_at="2026-08-28T23:59:59Z",
        )


def test_subject_aware_prior_art_rejects_restatements_without_generic_collision() -> None:
    exact = validate_question_novelty(
        ROOT,
        "Did GPT-4 score in approximately the 90th percentile of test takers on the Uniform Bar Examination?",
    )
    assert exact == [
        "proposal question closely restates accepted dossier gpt-4-bar-exam-percentile"
    ]

    paraphrase = validate_question_novelty(
        ROOT,
        "How was GPT-4 ranked near the ninetieth percentile after a simulated bar test?",
    )
    assert paraphrase == [
        "proposal question closely restates accepted dossier gpt-4-bar-exam-percentile"
    ]

    unrelated = validate_question_novelty(
        ROOT,
        "What primary evidence supports a general rule for communication weighting in neural networks?",
    )
    assert unrelated == []


def test_prior_art_comparison_fails_closed_on_malformed_accepted_records(
    tmp_path: Path,
) -> None:
    seed_prior_art(tmp_path)
    manifest = tmp_path / "catalog" / "dossiers" / "fixture-color-change.json"
    manifest.write_text("{not-json")
    assert any(
        "manifest is unreadable or malformed" in error
        for error in validate_question_novelty(tmp_path, "Does a novel claim hold?")
    )

    seed_prior_art(tmp_path)
    dossier = tmp_path / "research" / "how-we-know" / "fixture" / "dossier.json"
    dossier.write_text(json.dumps({"question": ""}))
    assert any(
        "record question must be a non-empty string" in error
        for error in validate_question_novelty(tmp_path, "Does a novel claim hold?")
    )

    seed_prior_art(tmp_path)
    dossier.unlink()
    assert any(
        "record is missing or is not a regular file" in error
        for error in validate_question_novelty(tmp_path, "Does a novel claim hold?")
    )


def test_prior_art_comparison_fails_closed_on_malformed_reviewed_docket(
    tmp_path: Path,
) -> None:
    seed_prior_art(tmp_path)
    reviewed = tmp_path / "research" / "open-dockets" / "reviewed-fixture"
    reviewed.mkdir(parents=True)
    (reviewed / "proposal.json").write_text("[]")
    assert any(
        "reviewed open docket reviewed-fixture record must be a JSON object" in error
        for error in validate_question_novelty(tmp_path, "Does a novel claim hold?")
    )


def test_prior_art_comparison_fails_closed_on_broken_reviewed_root_symlink(
    tmp_path: Path,
) -> None:
    seed_prior_art(tmp_path)
    accepted_root = tmp_path / "research" / "open-dockets"
    accepted_root.symlink_to(tmp_path / "missing-reviewed-root", target_is_directory=True)
    assert validate_question_novelty(tmp_path, "Does a novel claim hold?") == [
        "reviewed open-docket root is a symlink: research/open-dockets"
    ]


def test_prior_art_comparison_fails_closed_on_reviewed_docket_symlink(
    tmp_path: Path,
) -> None:
    seed_prior_art(tmp_path)
    accepted_root = tmp_path / "research" / "open-dockets"
    accepted_root.mkdir(parents=True)
    external = tmp_path / "external-reviewed-docket"
    external.mkdir()
    (external / "proposal.json").write_text(
        json.dumps({"question": "Does an external reviewed claim hold?"})
    )
    (accepted_root / "linked-reviewed-docket").symlink_to(
        external, target_is_directory=True
    )
    assert validate_question_novelty(tmp_path, "Does a novel claim hold?") == [
        "reviewed open docket linked-reviewed-docket path must not be a symlink"
    ]


def test_accepted_base_submission_validator_closes_server_chronology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, base, head = committed_submission(tmp_path)

    monkeypatch.setenv("CURRENT_PR_NUMBER", "100")
    monkeypatch.setenv("GITHUB_REPOSITORY", "yoheinakajima/epistemedia")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_github_json(path: str):
        if path == "pulls/100":
            return {
                "head": {"sha": head},
                "base": {"sha": base},
                "state": "open",
                "draft": True,
                "created_at": "2026-08-29T20:02:00Z",
            }
        if path == f"commits/{head}":
            return {
                "commit": {
                    "author": {"date": "2026-08-29T19:59:00Z"},
                    "committer": {"date": "2026-08-29T20:01:00Z"},
                }
            }
        if path == f"commits/{base}":
            return {
                "commit": {
                    "committer": {"date": "2026-08-28T00:00:00Z"},
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(submission_validator, "github_json", fake_github_json)
    result = submission_validator.validate(repository, base)
    assert result["valid"] is False
    assert any("chronology must satisfy" in error for error in result["errors"])


def test_server_chronology_isolates_accepted_base_after_runtime_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, base, head = committed_submission(tmp_path)
    monkeypatch.setenv("CURRENT_PR_NUMBER", "100")
    monkeypatch.setenv("GITHUB_REPOSITORY", "yoheinakajima/epistemedia")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_github_json(path: str):
        if path == "pulls/100":
            return {
                "head": {"sha": head},
                "base": {"sha": base},
                "state": "open",
                "draft": True,
                "created_at": "2026-08-29T20:02:00Z",
            }
        if path == f"commits/{head}":
            return {
                "commit": {
                    "author": {"date": "2026-08-29T20:00:30Z"},
                    "committer": {"date": "2026-08-29T20:01:00Z"},
                }
            }
        if path == f"commits/{base}":
            return {
                "commit": {
                    "committer": {"date": "2026-08-29T00:00:30Z"},
                }
            }
        raise AssertionError(path)

    monkeypatch.setattr(submission_validator, "github_json", fake_github_json)
    result = submission_validator.validate(repository, base)
    assert result["valid"] is False
    assert result["errors"] == [
        "chronology must satisfy accepted base commit <= runtime start <= completion <= intake submission <= commit author <= commit committer <= server PR creation"
    ]


@pytest.mark.parametrize("base_time", [None, "2026-13-29T00:00:00Z"])
def test_server_chronology_rejects_missing_or_malformed_base_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, base_time: str | None
) -> None:
    repository, base, head = committed_submission(tmp_path)
    monkeypatch.setenv("CURRENT_PR_NUMBER", "100")
    monkeypatch.setenv("GITHUB_REPOSITORY", "yoheinakajima/epistemedia")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_github_json(path: str):
        if path == "pulls/100":
            return {
                "head": {"sha": head},
                "base": {"sha": base},
                "state": "open",
                "draft": True,
                "created_at": "2026-08-29T20:02:00Z",
            }
        if path == f"commits/{head}":
            return {
                "commit": {
                    "author": {"date": "2026-08-29T20:00:30Z"},
                    "committer": {"date": "2026-08-29T20:01:00Z"},
                }
            }
        if path == f"commits/{base}":
            return {"commit": {"committer": {"date": base_time}}}
        raise AssertionError(path)

    monkeypatch.setattr(submission_validator, "github_json", fake_github_json)
    result = submission_validator.validate(repository, base)
    assert result["valid"] is False
    assert result["errors"] == [
        "accepted base commit committer time must use canonical UTC YYYY-MM-DDTHH:MM:SSZ"
        if base_time is None
        else "accepted base commit committer time is not a valid timestamp"
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["events"][0].update(note="chain-of-thought: private"),
        lambda value: value["events"][0].update(note="system prompt follows"),
        lambda value: value["events"][0].update(note="Read /Users/alice/private.txt"),
        lambda value: value["events"][0].update(note="Read /tmp/private-source.txt"),
        lambda value: value["events"][0].update(note="Read ../../private-source.txt"),
        lambda value: value["events"][0].update(note=r"Read D:\Temp\private-source.txt"),
        lambda value: value["events"][0].update(note="Contact alice@example.org"),
        lambda value: value["events"][0].update(note="x" * 2_049),
        lambda value: value["failures"].append("x" * 100_000),
        lambda value: (
            value["failures"].extend(["x" * 200] * 25),
            value["interventions"].extend(["y" * 200] * 25),
        ),
        lambda value: value["events"][0].update(note="github_pat_" + "a" * 24),
        lambda value: value["events"][0].update(artifact_sha256="not-a-digest"),
        lambda value: value["events"].append(copy.deepcopy(value["events"][0])),
        lambda value: value["cost"].update(currency="SOURCE_PAYLOAD_" * 500),
        lambda value: value["cost"].update(basis="SOURCE_PAYLOAD_" * 500),
        lambda value: value["cost"].update(amount=True),
        lambda value: value["cost"].update(amount=float("nan")),
        lambda value: value["cost"].update(amount=float("inf")),
        lambda value: value["cost"].update(amount=1_000_001),
    ],
)
def test_disclosure_safe_trace_fails_closed(mutation) -> None:
    trace = trace_template()
    mutation(trace)
    assert validate_action_trace(trace)


def test_every_retrieval_target_is_bound_even_when_retrieval_fails() -> None:
    bundle = valid_proposal()
    trace = trace_for(bundle)
    trace["events"].append(
        {
            "sequence": len(trace["events"]) + 1,
            "action": "retrieve-source",
            "target": "SOURCE_PAYLOAD_" * 100,
            "status": "failed",
            "artifact_sha256": "none",
            "note": "source-payload-omitted",
        }
    )
    assert validate_action_trace(trace) == []
    assert validate_trace_against_bundle(trace, bundle)


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


def test_controller_observed_model_must_match_contributor(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    attestation_path = destination / "controller-attestation.json"
    attestation = json.loads(attestation_path.read_text())
    attestation["model_family"] = "gemini"
    attestation_path.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n")
    _, errors = load_open_dockets(tmp_path)
    assert any(
        "known controller-observed model family must match" in error
        for error in errors
    )


def test_unknown_controller_model_earns_no_independence_credit(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    attestation_path = destination / "controller-attestation.json"
    attestation = json.loads(attestation_path.read_text())
    attestation["model_family"] = "unknown"
    attestation["unavailable_fields"] = ["model_family"]
    attestation_path.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n")

    review_path = destination / "review.json"
    review = json.loads(review_path.read_text())
    review["binding"]["controller_attestation_sha256"] = hashlib.sha256(
        attestation_path.read_bytes()
    ).hexdigest()
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")

    receipt_path = destination / "promotion-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["controller_attestation_sha256"] = hashlib.sha256(
        attestation_path.read_bytes()
    ).hexdigest()
    receipt["review_sha256"] = hashlib.sha256(review_path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    _, errors = load_open_dockets(tmp_path)
    assert any(
        "unresolved controller-observed model identity earns no reviewer-independence credit"
        in error
        for error in errors
    )


def test_model_family_comparison_is_case_insensitive(tmp_path: Path) -> None:
    promote(tmp_path, model_family="Claude")
    _, errors = load_open_dockets(tmp_path)
    assert any("after normalization" in error for error in errors)
    assert any("canonical lowercase" in error for error in errors)


def test_reviewer_identity_and_artifact_set_are_typed_and_exact(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    review_path = destination / "review.json"
    review = json.loads(review_path.read_text())
    review["reviewer"]["agent_id"] = 1
    review["reviewer"]["source_artifact_sha256s"] = ["c" * 64]
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    _, errors = load_open_dockets(tmp_path)
    assert any("agent_id must be a meaningful string" in error for error in errors)
    assert any("source-artifact set does not exactly match" in error for error in errors)


def test_toolchain_separation_rejects_normalized_overlap_even_with_extra_tools(
    tmp_path: Path,
) -> None:
    destination = promote(tmp_path)
    proposal = json.loads((destination / "proposal.json").read_text())
    review_path = destination / "review.json"
    review = json.loads(review_path.read_text())
    review["reviewer"]["toolchain"] = [
        re.sub(r"\s+", "-", item.upper())
        for item in proposal["runtime"]["toolchain"]
    ] + ["extra-review-label"]
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    _, errors = load_open_dockets(tmp_path)
    assert any("toolchain must be disjoint" in error for error in errors)


def test_missing_span_review_fails_closed(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    review = json.loads((destination / "review.json").read_text())
    review["source_reviews"][0]["spans"] = []
    (destination / "review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    dockets, errors = load_open_dockets(tmp_path)
    assert dockets == []
    assert any("coverage does not exactly match" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("claim_atom_reviews", "claim atom review coverage does not exactly match"),
        (
            "retrieval_attempt_reviews",
            "retrieval attempt review coverage does not exactly match",
        ),
    ],
)
def test_new_review_surfaces_require_exact_coverage(
    tmp_path: Path, field: str, expected: str
) -> None:
    destination = promote(tmp_path)
    review_path = destination / "review.json"
    review = json.loads(review_path.read_text())
    review[field] = []
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    dockets, errors = load_open_dockets(tmp_path)
    assert dockets == []
    assert any(expected in error for error in errors)


def test_forged_quote_digest_fails_closed(tmp_path: Path) -> None:
    destination = promote(tmp_path)
    review = json.loads((destination / "review.json").read_text())
    review["source_reviews"][0]["spans"][0]["quote_sha256"] = "c" * 64
    (destination / "review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    dockets, errors = load_open_dockets(tmp_path)
    assert dockets == []
    assert any("quote digest does not match" in error for error in errors)


def test_duplicate_accepted_proposal_fails_closed(tmp_path: Path) -> None:
    first = promote(tmp_path)
    second = tmp_path / "research" / "open-dockets" / "second-open-docket"
    shutil.copytree(first, second)
    review = json.loads((second / "review.json").read_text())
    review["public"]["slug"] = "second-open-docket"
    (second / "review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    receipt = json.loads((second / "promotion-receipt.json").read_text())
    receipt["review_sha256"] = hashlib.sha256((second / "review.json").read_bytes()).hexdigest()
    (second / "promotion-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    _, errors = load_open_dockets(tmp_path)
    assert any("duplicates accepted docket" in error for error in errors)


def test_calculation_and_dependency_closure_are_required() -> None:
    bundle = valid_proposal()
    bundle["results"][0]["dependency_ids"] = []
    assert any(
        "must retain at least one typed dependence" in error
        for error in validate_proposal(bundle)["errors"]
    )

    calculated = valid_proposal()
    calculated["results"][0]["calculation_ids"] = ["calc-1"]
    calculated["calculations"] = [
        {
            "calculation_id": "calc-1",
            "equation": "numerator / denominator",
            "inputs": [
                {
                    "input_id": "numerator",
                    "name": "numerator",
                    "value": "1",
                    "origin": "source-span",
                    "source_id": "source-1",
                    "span_id": "missing-span",
                    "json_pointer": "/results/numerator",
                }
            ],
            "output": "1",
            "uncertainty": "Bounded fixture.",
            "depends_on": [],
        }
    ]
    assert any(
        "does not bind an existing source/span pair" in error
        for error in validate_proposal(calculated)["errors"]
    )


def test_human_open_docket_projection_retains_full_reviewable_record(tmp_path: Path) -> None:
    promote(tmp_path)
    dockets, errors = load_open_dockets(tmp_path)
    assert errors == []
    data = dockets[0].projection("https://epistemedia.org")
    markdown = docket_markdown(data)
    rendered = docket_html(data)
    for label in (
        "Calculations",
        "Typed dependencies",
        "Counterevidence",
        "Negative results",
        "Lineage",
        "Independent review receipt",
        "Edition",
        "License",
    ):
        assert label in markdown
    for label in (
        "Calculations",
        "Typed dependencies",
        "Counterevidence",
        "Negative results",
        "Lineage",
        "Independent review receipt",
    ):
        assert label in rendered
    for value in (
        data["lineage"]["prompt_sha256"],
        data["lineage"]["run_identity"],
        data["lineage"]["provider_model_identity"],
        data["lineage"]["retrieval_environment"],
    ):
        assert f"<code>{html.escape(str(value))}</code>" in rendered


def test_public_build_exposes_submit_and_current_open_docket_routes(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    home = (public / "index.html").read_text()
    home_markdown = (public / "index.md").read_text()
    how_we_know = (public / "how-we-know" / "index.html").read_text()
    how_we_know_markdown = (public / "how-we-know" / "index.md").read_text()
    how_we_know_json = json.loads(
        (public / "how-we-know" / "index.json").read_text()
    )
    agents = (public / "agents" / "index.html").read_text()
    agents_markdown = (public / "agents" / "index.md").read_text()
    agents_json = json.loads((public / "agents" / "index.json").read_text())
    submit = (public / "agents" / "submit" / "index.html").read_text()
    submit_markdown = (public / "agents" / "submit" / "index.md").read_text()
    llms = (public / "llms.txt").read_text()
    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    dockets, errors = load_open_dockets(ROOT)
    assert errors == []
    assert dockets
    first = dockets[0].projection("https://epistemedia.org")
    docket_url = first["representations"]["html"]
    docket_markdown_url = first["representations"]["markdown"]
    docket_json_url = first["representations"]["json"]
    assert "Point an agent here" in submit
    assert "separate reviewer" in submit
    assert f'href="{docket_url}"' in home
    assert f'href="{docket_url}"' in how_we_know
    assert f'href="{docket_url}"' in agents
    assert 'href="https://epistemedia.org/open-dockets/"' in submit
    assert docket_markdown_url in home_markdown
    assert docket_markdown_url in how_we_know_markdown
    assert docket_markdown_url in agents_markdown
    assert "[reviewed open-docket library]" in submit_markdown
    assert "/agents/submit/" in llms
    assert docket_markdown_url in llms
    assert docket_json_url in llms
    assert discovery["agent_research"]["github_submission_available"] is True
    assert discovery["open_dockets"]["count"] == len(dockets)
    assert how_we_know_json["data"]["reviewed_open_dockets"]["count"] == len(
        dockets
    )
    assert agents_json["data"]["reviewed_open_dockets"]["count"] == len(dockets)
    assert "remain distinct from numbered How We Know cases" in how_we_know
    assert (public / "open-dockets" / "index.html").is_file()


def test_ci_uses_base_validator_for_submission_only_pull_requests() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "classify_docket_pr.py" in workflow
    assert "ref: ${{ github.event.pull_request.base.sha || github.sha }}" in workflow
    assert "PYTHONPATH: validator/src" in workflow
    assert "python validator/ops/validate_submission_pr.py" in workflow
    assert "python validator/ops/validate_promotion_pr.py" in workflow
    assert "Validate and block untrusted submission" in workflow
    assert "steps.classify.outputs.mode == 'promotion'" in workflow
    assert "persist-credentials: false" in workflow
    assert "pull_request_target" not in workflow
    assert "checks: read" in workflow
    assert "checks: write" not in workflow
    assert "cache-dependency-path: candidate/pyproject.toml" in workflow
    assert "--diff-filter" not in (ROOT / "ops" / "validate_submission_pr.py").read_text()


def test_sensitive_mixed_paths_never_execute_candidate_code() -> None:
    submission = "research/open-dockets/submissions/test/proposal.json"
    promotion = "research/open-dockets/test/review.json"
    assert classify_paths([submission, "pyproject.toml"]) == "submission"
    assert classify_paths([promotion, "pyproject.toml"]) == "promotion"
    assert classify_paths([submission, promotion]) == "submission"
    assert classify_paths(["README.md"]) == "normal"


def test_ci_bootstrap_rejects_docket_paths_until_classifier_is_accepted() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "if [[ -f validator/ops/classify_docket_pr.py ]]" in workflow
    assert "mapfile -t bootstrap_paths" in workflow
    assert '[[ "$path" == research/open-dockets/* ]]' in workflow
    assert "grep -q '^research/open-dockets/'" not in workflow
    assert "accepted base lacks the docket classifier; rejecting sensitive diff" in workflow
    assert workflow.index('[[ "$path" == research/open-dockets/* ]]') < workflow.index(
        'echo "mode=normal"'
    )


def test_trusted_post_check_workflow_can_only_sign_exact_promotions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "approve-open-docket-promotion.yml").read_text()
    assert "workflow_run:" in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1" in workflow
    assert "permission-checks: write" in workflow
    assert "pull-requests: write" not in workflow
    assert "contents: write" not in workflow
    assert "check-runs" in workflow
    assert "independent-review" in workflow
    assert "gh pr review" not in workflow
    assert "gh pr merge" not in workflow
    assert "${#paths[@]} -eq 5" in workflow
    assert "pull_request_target" not in workflow


def test_independent_fetch_rejects_private_dns_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        promotion_validator.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (promotion_validator.socket.AF_INET, 1, 6, "", ("127.0.0.1", 443))
        ],
    )
    with pytest.raises(ValueError, match="non-public address"):
        promotion_validator.fetch_public("https://example.org/source")


def test_independent_fetch_pins_dns_disables_redirects_and_bounds_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        promotion_validator.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (promotion_validator.socket.AF_INET, 1, 6, "", ("93.184.216.34", 443))
        ],
    )
    observed: list[str] = []

    def fake_run(args, **kwargs):
        observed.extend(args)
        Path(args[args.index("--output") + 1]).write_bytes(b"bounded artifact")
        return subprocess.CompletedProcess(args, 0, stdout="200", stderr="")

    monkeypatch.setattr(promotion_validator.subprocess, "run", fake_run)
    assert promotion_validator.fetch_public(
        "https://example.org/source", max_bytes=1234
    ) == b"bounded artifact"
    assert "example.org:443:93.184.216.34" in observed
    assert observed[observed.index("--max-filesize") + 1] == "1234"
    assert "--location" not in observed
    assert observed[observed.index("--noproxy") + 1] == "*"

    def fake_redirect(args, **kwargs):
        Path(args[args.index("--output") + 1]).write_bytes(b"")
        return subprocess.CompletedProcess(args, 0, stdout="302", stderr="")

    monkeypatch.setattr(promotion_validator.subprocess, "run", fake_redirect)
    with pytest.raises(ValueError, match="final public carrier"):
        promotion_validator.fetch_public("https://example.org/source")


def test_accepted_base_promotion_validator_closes_git_and_live_source_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    def run_git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repository), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    run_git("init", "-b", "main")
    run_git("config", "user.name", "Test Integrator")
    run_git("config", "user.email", "integrator@example.invalid")
    (repository / "README.md").write_text("accepted base\n")
    run_git("add", "README.md")
    run_git("commit", "-m", "base")
    source_base = run_git("rev-parse", "HEAD")
    (repository / "CHANGELOG.md").write_text("accepted after submission\n")
    run_git("add", "CHANGELOG.md")
    run_git("commit", "-m", "advance accepted main")
    base = run_git("rev-parse", "HEAD")
    non_ancestor = run_git(
        "commit-tree", run_git("rev-parse", "HEAD^{tree}"), "-m", "unrelated root"
    )

    destination = promote(repository)
    submission = next((repository / "research" / "open-dockets" / "submissions").iterdir())
    artifact = b"The bounded result was observed."
    artifact_digest = hashlib.sha256(artifact).hexdigest()
    for intake_path in (submission / "intake.json", destination / "intake.json"):
        intake = json.loads(intake_path.read_text())
        intake["trace"]["events"][1]["artifact_sha256"] = artifact_digest
        intake_path.write_text(json.dumps(intake, indent=2, sort_keys=True) + "\n")
    review_path = destination / "review.json"
    review = json.loads(review_path.read_text())
    review["source_reviews"][0]["artifact_sha256"] = artifact_digest
    review["reviewer"]["source_artifact_sha256s"] = [artifact_digest]
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    receipt_path = destination / "promotion-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt_path.unlink()
    source_files = {
        name: (submission / name).read_bytes()
        for name in ("PR_BODY.md", "intake.json", "proposal.json")
    }
    shutil.rmtree(repository / "research" / "open-dockets" / "submissions")
    run_git("add", str(destination.relative_to(repository)))
    run_git("commit", "-m", "promote reviewed docket")
    reviewed_head = run_git("rev-parse", "HEAD")
    reviewed_tree = run_git("rev-parse", "HEAD^{tree}")
    receipt.update(
        {
            "reviewed_head": reviewed_head,
            "reviewed_tree": reviewed_tree,
            "proposal_sha256": hashlib.sha256(
                (destination / "proposal.json").read_bytes()
            ).hexdigest(),
            "review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
            "reviewer": review["reviewer"],
        }
    )
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    run_git("add", str(receipt_path.relative_to(repository)))
    run_git("commit", "-m", "receipt")
    head = run_git("rev-parse", "HEAD")

    monkeypatch.setenv("CANDIDATE_SHA", head)
    monkeypatch.setenv("CURRENT_PR_NUMBER", "200")
    monkeypatch.setenv("GITHUB_REPOSITORY", "yoheinakajima/epistemedia")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    expected_external_id = promotion_validator.evidence_review_external_id(
        hashlib.sha256(review_path.read_bytes()).hexdigest(),
        hashlib.sha256(
            (destination / "controller-attestation.json").read_bytes()
        ).hexdigest(),
    )
    review_gate = {
        "present": True,
        "app_id": 4_766_776,
        "external_id": expected_external_id,
    }
    source_pr_base = {"sha": source_base}

    def fake_github_json(path: str):
        if path == f"commits/{reviewed_head}/check-runs?per_page=100":
            return {
                "check_runs": (
                    [
                        {
                            "name": "independent-evidence-review",
                            "head_sha": reviewed_head,
                            "status": "completed",
                            "conclusion": "success",
                            "external_id": review_gate["external_id"],
                            "app": {"id": review_gate["app_id"]},
                        }
                    ]
                    if review_gate["present"]
                    else []
                )
            }
        if path == "pulls/100":
            return {
                "html_url": "https://github.com/yoheinakajima/epistemedia/pull/100",
                "head": {"sha": "a" * 40},
                "base": {"sha": source_pr_base["sha"]},
                "state": "open",
                "draft": True,
                "created_at": "2026-08-29T20:12:00Z",
            }
        if path == "commits/" + "a" * 40:
            return {
                "commit": {
                    "author": {"date": "2026-08-29T20:10:00Z"},
                    "committer": {"date": "2026-08-29T20:11:00Z"},
                }
            }
        if path.startswith("pulls/100/files"):
            parent = "research/open-dockets/submissions/source"
            return [
                {"filename": f"{parent}/{name}", "status": "added"}
                for name in ("PR_BODY.md", "intake.json", "proposal.json")
            ]
        raise AssertionError(path)

    monkeypatch.setattr(promotion_validator, "github_json", fake_github_json)
    monkeypatch.setattr(
        promotion_validator,
        "github_file",
        lambda path, ref: source_files[Path(path).name],
    )
    monkeypatch.setattr(
        promotion_validator, "fetch_public", lambda url, **kwargs: artifact
    )
    result = promotion_validator.validate(repository, base)
    assert result["valid"] is True, result["errors"]

    for invalid_source_base in ("HEAD^", base[:7], non_ancestor, "f" * 40):
        source_pr_base["sha"] = invalid_source_base
        result = promotion_validator.validate(repository, base)
        assert result["valid"] is False
        assert any(
            "source pull request base is not an ancestor of the promotion base" in error
            for error in result["errors"]
        )
    source_pr_base["sha"] = source_base

    for field, forged in (
        ("present", False),
        ("app_id", 1),
        ("external_id", "epistemedia-review-v1:" + "0" * 129),
    ):
        original = review_gate[field]
        review_gate[field] = forged
        result = promotion_validator.validate(repository, base)
        assert result["valid"] is False
        assert any(
            "lacks the App-signed independent evidence-review binding" in error
            for error in result["errors"]
        )
        review_gate[field] = original

    receipt["reviewed_head"] = "f" * 40
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    run_git("add", str(receipt_path.relative_to(repository)))
    run_git("commit", "--amend", "--no-edit")
    monkeypatch.setenv("CANDIDATE_SHA", run_git("rev-parse", "HEAD"))
    result = promotion_validator.validate(repository, base)
    assert result["valid"] is False
    assert any("receipt does not bind" in error for error in result["errors"])


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


def test_submission_binds_and_sanitizes_pr_body(tmp_path: Path) -> None:
    _, _, result = prepared(tmp_path)
    directory = result["directory"]
    (directory / "PR_BODY.md").write_text("chain-of-thought github_pat_" + "a" * 30)
    errors = validate_submission_directory(directory)
    assert any("pr_body_sha256" in error for error in errors)
    assert any("PR_BODY.md contains prohibited" in error for error in errors)


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

    expected_dockets = gateway.call_tool("list_open_dockets", {})
    assert isinstance(expected_dockets, list)
    status, _, response = gateway.handle_api(
        Request("GET", "/v1/open-dockets", {}, {}, b"")
    )
    assert status == 200
    assert response["data"] == expected_dockets
    assert main(["--root", str(ROOT), "open-dockets", "list"]) == 0
    assert json.loads(capsys.readouterr().out)["data"] == expected_dockets
    names = {tool["name"] for tool in tool_definitions()}
    assert {"get_docket_submission_guide", "list_open_dockets", "get_open_docket"} <= names
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in tool_definitions())
    assert not any(word in name for name in names for word in ("submit", "admit", "merge"))


def test_markdown_projection_escapes_raw_html_and_uses_a_safe_dynamic_fence(
    tmp_path: Path,
) -> None:
    promote(tmp_path)
    dockets, errors = load_open_dockets(tmp_path)
    assert errors == []
    projection = dockets[0].projection("https://epistemedia.org")
    dangerous = "bounded </script> text\n```\n# injected heading"
    projection["sources"][0]["exact_spans"][0]["quote"] = dangerous
    projection["sources"][0]["title"] = "safe](javascript:alert(1))"
    markdown = docket_markdown(projection)
    assert "</script>" not in markdown
    human, tail = markdown.split("## Complete machine record", 1)
    assert "\n# injected heading" not in human
    assert "[safe](javascript:alert(1))" not in human
    assert "safe\\]\\(javascript:alert\\(1\\)\\)" in human
    opening = next(line for line in tail.splitlines() if line.endswith("json"))
    fence = opening.removesuffix("json")
    encoded = tail.split(opening, 1)[1].split(fence, 1)[0].strip()
    assert json.loads(encoded)["sources"][0]["exact_spans"][0]["quote"] == dangerous
