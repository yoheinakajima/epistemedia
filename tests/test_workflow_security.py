from __future__ import annotations

import re
from pathlib import Path


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
