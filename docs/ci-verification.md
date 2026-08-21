# Validation workflow

Epistemedia's contribution CI is defined in `.github/workflows/ci.yml` and appears in GitHub Actions as **Validate**.

It runs on every pull request, every push to `main`, and explicit manual dispatch. The `check` job:

1. installs the project in a clean GitHub-hosted runner;
2. validates accepted repository inputs;
3. rebuilds the disclosure-safe public projection;
4. runs the full test suite;
5. audits the public projection;
6. proves a second build is byte-identical; and
7. rejects uncommitted tracked or generated-state drift.

This document was added through a pull request to exercise the same public contribution boundary that future human and agent contributions use.
