# Container release-readiness evidence

Status: locally and statically validated; image build and publication not run.

Task `EM-0014` bounds the container context and preserves accepted release
identity without shipping the repository Git directory. This record separates
what was verified from the remaining provider and owner gates.

## Verified configuration

- `.dockerignore` excludes VCS metadata, Python and JavaScript environments,
  caches, editor state, disposable projections, local realms, environment
  files, private-key formats, and credential- or secret-named files.
- The Dockerfile copies the declared accepted public inputs rather than the
  whole checkout.
- The image requires an exact 40-character lowercase accepted commit and a
  non-negative accepted commit timestamp as build arguments.
- Repository Git state takes precedence in a checkout. The validated build
  fallback is used only when Git state is unavailable, as it is in the image.
- The protected container workflow derives both values from the verified
  release tag before passing them to BuildKit.
- Existing non-root execution, application request limits, Compose resource
  limits, read-only filesystem posture, dropped capabilities, provenance, and
  SBOM settings remain present.

Static and Python-level evaluation covers context exclusions, forbidden broad
copy behavior, malformed identity rejection, Git-over-fallback precedence,
timestamp fallback, release-workflow propagation, and the existing workflow
security contract.

## Observed limitation

No `docker`, `podman`, `nerdctl`, or `buildah` executable was available in the
development environment. No image was built, started, pushed, signed, or
published. A Docker-compatible build plus `/healthz`, API identity, MCP
identity, non-root, and filesystem smoke test remains mandatory before the
first GHCR publication.

No release tag or registry identity is authorized by this record. GHCR,
GitHub Release, PyPI, and MCP Registry publication remain separate irreversible
owner decisions.
