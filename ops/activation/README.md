# Activation boundary

This directory contains owner-controlled activation checklists. Contributor agents may improve the documentation through pull requests, but they cannot change repository visibility, GitHub account policy, branch rulesets, environment protection, DNS, package-publisher identity, or external provider credentials.

Current evidence:

- [`2026-09-01-v0.2.0-public-gateway.md`](2026-09-01-v0.2.0-public-gateway.md) records the public
  tag and GHCR digest, free Render service, verified API/MCP DNS and TLS, exact release-identity
  parity, read-only security probes, and remaining submission, registry, package, and redirect
  boundaries.
- [`2026-08-22-custom-domain.md`](2026-08-22-custom-domain.md) records the verified `epistemedia.org` DNS set, HTTPS enforcement, canonical-domain Pages deployment, live route validation, and remaining redirect and runtime boundaries.
- [`2026-08-22-package-readiness.md`](2026-08-22-package-readiness.md) records the corrected clean-wheel CLI smoke test and the still-blocked publication identities.
- [`2026-08-22-social-preview.md`](2026-08-22-social-preview.md) records the locally verified social-preview asset and the still-pending GitHub upload.
- [`2026-08-22-container-readiness.md`](2026-08-22-container-readiness.md) records the bounded container context and the still-unrun Docker and publication gates.
- [`2026-08-22-prepublic-branch-cleanup.md`](2026-08-22-prepublic-branch-cleanup.md) records the authorized deletion and provider read-back for the obsolete `prepublic-ready` branch.
- [`2026-08-22-pages-bootstrap.md`](2026-08-22-pages-bootstrap.md) records the protected contribution path, repository hardening, license correction, default-hostname Pages deployment, live route validation, and remaining owner boundaries.
- [`2026-08-21-repository-baseline.md`](2026-08-21-repository-baseline.md) is the earlier immutable baseline.

`PRE_PUBLIC_OWNER_CHECKLIST.md` and `docs/pre-public-owner-handoff.md` are archived bootstrap instructions, not current state.
