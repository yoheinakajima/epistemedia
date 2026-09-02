from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from ops.classify_attestation_pr import (
    classify_attestation_changes,
    classify_attestation_paths,
    exact_git_changes,
    pull_request_identity,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SHA_PIN = re.compile(r"^\s*- uses: [^\s@]+@[0-9a-f]{40}(?:\s+#.*)?$", re.MULTILINE)
USES_LINE = re.compile(r"^\s*- uses: .+$", re.MULTILINE)


def workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text()


def test_all_actions_are_pinned_and_untrusted_code_has_no_privileged_trigger() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text()
        assert "pull_request_target:" not in text
        uses = USES_LINE.findall(text)
        assert uses
        assert len(SHA_PIN.findall(text)) == len(uses), path


def test_checkout_never_persists_credentials() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text()
        assert text.count("actions/checkout@") == text.count("persist-credentials: false"), path


def test_pages_bootstrap_is_manual_and_has_no_custom_domain_side_effect() -> None:
    text = workflow("pages.yml")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "default: bootstrap" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "https://yoheinakajima.github.io/epistemedia" in text
    assert "https://epistemedia.org" in text
    assert "if: inputs.deployment_mode == 'custom-domain'" in text
    assert "run: printf '%s\\n' epistemedia.org > generated/public/CNAME" in text
    assert "if: inputs.deployment_mode == 'bootstrap'" in text
    assert "run: test ! -e generated/public/CNAME" in text
    assert "include-hidden-files: true" in text


def test_irreversible_publication_workflows_are_manual_and_confirmed() -> None:
    container = workflow("container.yml")
    release = workflow("release.yml")
    for text in (container, release):
        assert "workflow_dispatch:" in text
        assert "\n  push:" not in text
        assert "ref: ${{ inputs.tag }}" in text
        assert "github.ref == 'refs/heads/main'" in text
        assert "git merge-base --is-ancestor \"$RELEASE_SHA\" origin/main" in text
        assert "test \"$(git rev-parse HEAD)\" = \"$RELEASE_SHA\"" in text

    assert "inputs.confirm_publish" in container
    assert "confirm_publish:" in container
    assert "environment: ghcr" in container
    assert 'SOURCE_EPOCH="$(git show -s --format=%ct "$RELEASE_SHA")"' in container
    assert "EPISTEMEDIA_ACCEPTED_COMMIT=${{ steps.release.outputs.sha }}" in container
    assert "SOURCE_DATE_EPOCH=${{ steps.release.outputs.source_epoch }}" in container
    assert "if: inputs.publish_github_release" in release
    assert "if: inputs.publish_pypi" in release
    assert "environment: github-release" in release
    assert "environment:\n      name: pypi" in release
    assert "skip-existing" not in release


def test_pull_request_validation_has_no_secret_or_write_authority() -> None:
    text = workflow("ci.yml")
    assert "pull_request:" in text
    assert "ref: ${{ github.event.pull_request.head.sha || github.sha }}" in text
    assert "secrets." not in text
    for permission in ("checks: read", "contents: read", "pull-requests: read"):
        assert permission in text
    for permission in ("checks: write", "contents: write", "pull-requests: write"):
        assert permission not in text
    assert "run: make check" in text


def test_attestation_workflow_is_a_secretless_noop_for_ordinary_prs() -> None:
    assert classify_attestation_paths(
        ["README.md", "docs/api-mcp-cli.md", "tests/test_interfaces.py"]
    ) == {"mode": "ordinary", "eligible": False, "parent": None}

    text = workflow("approve-open-docket-promotion.yml")
    assert 'gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}" > "$pr_file"' in text
    assert "refs/pull/${PR_NUMBER}/head" in text
    assert '[[ "$(git rev-parse FETCH_HEAD)" == "$REVIEWED_HEAD" ]]' in text
    assert "--reviewed-head \"$REVIEWED_HEAD\"" in text
    assert "pulls/${PR_NUMBER}/files" not in text
    assert "python3 ops/classify_attestation_pr.py" in text
    assert text.count("if: steps.classify.outputs.eligible == 'true'") == 2
    sign_step = text.split("- name: Sign the exact promotion receipt head", 1)[1]
    assert '[[ "$pr_state" == "open" ]]' in sign_step
    assert '[[ "$current_base" == "${{ steps.classify.outputs.base }}" ]]' in sign_step
    assert '[[ "$current_head" == "$REVIEWED_HEAD" ]]' in sign_step
    token_step = text.split(
        "- name: Create short-lived review-gate App token", 1
    )[1].split("- name: Sign the exact promotion receipt head", 1)[0]
    assert "if: steps.classify.outputs.eligible == 'true'" in token_step
    assert "secrets.REVIEW_GATE_APP_PRIVATE_KEY" in token_step


def test_attestation_classifier_accepts_only_one_exact_receipt_child() -> None:
    parent = "research/open-dockets/example-claim"
    exact = [
        f"{parent}/{name}"
        for name in (
            "controller-attestation.json",
            "intake.json",
            "proposal.json",
            "promotion-receipt.json",
            "review.json",
        )
    ]
    assert classify_attestation_paths(exact) == {
        "mode": "promotion",
        "eligible": True,
        "parent": parent,
    }

    invalid_fixtures = [
        exact[:-1],
        exact + ["README.md"],
        [path.replace("example-claim", "submissions/example-claim") for path in exact],
        [path.replace("example-claim", "submissions") for path in exact],
        [*exact[:-1], f"{parent}/author-supplied-review.json"],
        [*exact[:-1], "research/open-dockets/another-claim/review.json"],
    ]
    for paths in invalid_fixtures:
        try:
            classify_attestation_paths(paths)
        except ValueError:
            pass
        else:
            raise AssertionError(f"docket-sensitive fixture did not fail closed: {paths}")

    assert classify_attestation_changes([("A", path) for path in exact])["eligible"]
    with pytest.raises(ValueError, match="newly added"):
        classify_attestation_changes(
            [("D", exact[0]), ("A", "README.md")]
        )


def test_attestation_diff_is_bound_to_immutable_base_and_head(tmp_path: Path) -> None:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    (tmp_path / "README.md").write_text("base\n")
    git("add", "README.md")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD")

    (tmp_path / "README.md").write_text("ordinary head\n")
    git("commit", "-am", "ordinary")
    reviewed_head = git("rev-parse", "HEAD")
    docket = tmp_path / "research" / "open-dockets" / "later"
    docket.mkdir(parents=True)
    for name in (
        "controller-attestation.json",
        "intake.json",
        "proposal.json",
        "promotion-receipt.json",
        "review.json",
    ):
        (docket / name).write_text("{}\n")
    git("add", "research")
    git("commit", "-m", "later mutable head")
    later_head = git("rev-parse", "HEAD")

    changes = exact_git_changes(tmp_path, base, reviewed_head)
    assert changes == [("M", "README.md")]
    assert classify_attestation_changes(changes) == {
        "mode": "ordinary",
        "eligible": False,
        "parent": None,
    }
    with pytest.raises(ValueError, match="moved"):
        pull_request_identity(
            {"state": "open", "base": {"sha": base}, "head": {"sha": later_head}},
            reviewed_head,
        )


def test_validation_does_not_inject_a_global_clock() -> None:
    assert not (ROOT / "usercustomize.py").exists()
    assert not (ROOT / "src" / "usercustomize.py").exists()


def test_active_deployment_configuration_uses_controlled_domain() -> None:
    paths = [
        ROOT / "pyproject.toml",
        ROOT / "server.json",
        ROOT / "src" / "epistemedia" / "server.py",
        ROOT / "ops" / "hosting" / "dns.md",
    ]
    for path in paths:
        text = path.read_text()
        assert "epistemedia.org" in text
        assert "https://epistemedia.com" not in text, path
