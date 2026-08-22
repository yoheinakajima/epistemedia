# Owner activation checklist

> **Archived bootstrap checklist.** These gates have been completed and superseded by the provider read-back in [`2026-08-22-pages-bootstrap.md`](2026-08-22-pages-bootstrap.md). The unchecked boxes below preserve the original owner handoff; they are not current work state.

- [ ] Verify `prepublic-ready` exists and `main` contains the full implementation.
- [ ] Make `yoheinakajima/epistemedia` public.
- [ ] Verify the public repository from a logged-out browser.
- [ ] Enable squash-only merging, auto-merge, and automatic branch deletion.
- [ ] Set Actions default permissions to read repository contents and packages.
- [ ] Keep Actions-created/approved pull requests disabled.
- [ ] Run CI manually on `main` and inspect every job.
- [ ] Create an active `main` ruleset using the exact successful CI check names.
- [ ] Require pull requests, up-to-date branches, linear history, and block force pushes/deletion.
- [ ] Test one fork pull request and confirm no secrets are exposed.
- [ ] Stop before Pages, domain DNS, API/MCP deployment, GHCR, releases, PyPI, or MCP Registry activation.
