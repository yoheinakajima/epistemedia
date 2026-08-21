# Pre-public owner handoff

This document starts at the GitHub account boundary. The code, tests, deterministic site compiler, API/MCP gateway, CLI package, workflows, and provider declarations are prepared before this point.

## Verify promotion

1. Confirm branch `prepublic-ready` exists.
2. Confirm `main` contains the complete repository rather than the placeholder README.
3. The promoted Git tree is `03bc33f8dc1de76abc871bfd23cd2e2f853bc623`.
4. If the verification branch is absent, run the manual workflow **Promote validated Epistemedia pre-public tree** on `main` and check again.

## Make the repository public

Open **Settings → General → Danger Zone → Change repository visibility**, choose **Public**, confirm `yoheinakajima/epistemedia`, then verify the repository from a logged-out browser.

## Configure merge behavior

Under **Settings → General → Pull Requests**:

- enable squash merging;
- disable merge commits;
- disable rebase merging;
- enable auto-merge;
- automatically delete head branches.

## Configure Actions

Under **Settings → Actions → General**:

- allow the GitHub-authored, verified, and explicitly pinned actions used by the committed workflows;
- set default workflow permissions to read repository contents and packages;
- keep **Allow GitHub Actions to create and approve pull requests** disabled.

Manually run the CI workflow on `main`. Do not enable Pages, container publishing, release publishing, PyPI, DNS, or MCP Registry publication yet.

## Protect `main`

After the first successful CI run has registered the exact check names, create an active branch ruleset targeting the default branch:

- require pull requests;
- require the successful CI checks;
- require branches to be up to date;
- require linear history;
- block force pushes;
- block deletion;
- do not grant routine contributor agents bypass authority.

## Stop point

Stop after the repository is public, untrusted CI is green, and `main` is protected. Pages, `epistemedia.com`, API/MCP deployment, GHCR, GitHub Releases, PyPI Trusted Publishing, and MCP Registry publication are the next activation phase.
