# Validation workflow

Epistemedia's contribution CI is defined in `.github/workflows/ci.yml` and appears in GitHub Actions as **Validate**.

It runs on every pull request, every push to `main`, and explicit manual dispatch. The `check` job:

1. installs the project in a clean GitHub-hosted runner;
2. invokes the same `make check` contract used locally;
3. snapshots the candidate source-tree state;
4. validates accepted repository inputs;
5. builds the disclosure-safe public projection;
6. runs the full test suite;
7. audits the public projection;
8. proves an independent second build is byte-identical; and
9. rejects any source-tree change introduced while validation ran.

`generated/public/` is ignored, disposable compiler output. It is not committed state. Its
`generated_at` metadata is derived from the accepted Git commit time so the same accepted inputs
produce the same bytes locally, in CI, and during deployment. Provider deployment time is recorded
separately by the workflow run and activation receipt.

This document was added through a pull request to exercise the same public contribution boundary that future human and agent contributions use.
