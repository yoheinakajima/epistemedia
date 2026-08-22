# Default-hostname Pages activation evidence — 2026-08-22

Observed between `2026-08-22T01:39:00Z` and `2026-08-22T01:47:29Z` unless a more specific timestamp is listed. GitHub facts came from authenticated API read-back, DNS facts from public recursive resolution, and route facts from external HTTPS requests. Configuration alone is not treated as live-service evidence.

This record advances EM-0008. It does not complete custom-domain, API/MCP runtime, container, release, PyPI, or registry activation.

## Accepted repository state

- Repository: `yoheinakajima/epistemedia`
- Visibility: public
- Default branch: `main`
- Accepted commit: `f1bcff0317a8e65003326544d844c120a61fb00d`
- Post-merge Validate run: `32544046164`
- Required `check` job: `96959294642`
- Validate conclusion: `success`
- Local accepted-state result: `make check PYTHON='PYTHONPATH=src .venv/bin/python'` passed validation, 36 tests, disclosure audit, independent deterministic rebuild comparison, and source-tree drift detection

Repository settings read back as:

- squash merge enabled; merge commits and rebase merge disabled;
- auto-merge, branch-update suggestions, and automatic merged-branch deletion enabled;
- Issues and Discussions enabled; Projects and Wiki disabled;
- description: `Knowledge that can show its work: an open, federated knowledge system for humans and agents.`;
- homepage: `https://yoheinakajima.github.io/epistemedia/`;
- the ten declared topics are present;
- private vulnerability reporting enabled;
- custom social preview not yet configured.

## Protected contribution path

Ruleset `main-protection` (`21168452`) remains active and targets `~DEFAULT_BRANCH`. It requires a pull request, conversation resolution, strict current-branch status check `check`, linear history, and squash-only merge; it blocks deletion and non-fast-forward updates. The repository-administrator role is the sole always-bypass actor class. No bypass was used for the work below.

The earlier proof PRs `#3`, `#5`, and `#6` are recorded in [`2026-08-21-repository-baseline.md`](2026-08-21-repository-baseline.md). The activation and hardening sequence continued as follows:

| PR | Scope | Candidate | Required run / job | Squash commit |
| --- | --- | --- | --- | --- |
| `#7` | Canonical-domain and workflow hardening | `c96dc1d9606e0f8ddac0f723cbc4dfa27242178b` | `32536644320` / `96938717482` | `ae629880a571c559809ee2333eaa80ca2fe81777` |
| `#8` | Hidden Pages routes and current action runtime | `afb0897347f7061c6953188a3d61f51bc0df1641` | `32539394299` / `96946243900` | `7b2ec540882c7a1521d4b24c1ee135d7818644d0` |
| `#9` | Static object routes | `390e163981836339677b3f211684b623e8a9e105` | `32539740611` / `96947257533` | `ba71ed4e798d4c8597f2f7046113a6456dca1d36` |
| `#10` | Page-level canonical URLs | `e8f798d0539c68c7307803dd5b7b72005f7c4ebb` | `32540105239` / `96948333812` | `abf3077bd9f8df96efee811062bbfa7b12b1cd9c` |
| `#11` | Mobile identity wrapping | `3f956d6fd2ac80329046053d02c2c890613e35ee` | `32541235272` / `96951524091` | `914d495f8336799747b8fe1b5aaa72a8a31280be` |
| `#12` | Register launch-hardening tasks | `c674c3ac01c4b618dc2b71973fdeef00ccba333f` | `32540516403` / `96949494174` | `a6740048f0f991b459b216c3d93bd54352d263ab` |
| `#13` | Deterministic generated-state contract | `08e1ba1d9c202839625c377a25931e2255e2affb` | `32541002372` / `96950875668` | `78a8ebbca8d1cd82ed4687e3fcecf0a6c4f062e8` |
| `#14` | Register legacy clock-hook removal | `ad00c3ccbcc2682941008aaa1e46581373af872c` | `32540918726` / `96950636245` | `786ad7ca59586b25b7259496ad85d633570768f9` |
| `#15` | Remove legacy clock injection | `b2b167d1f2c3ccea196cd2bdfcf402796785d647` | `32541143255` / `96951265601` | `43ac0d1e8aec79c34e50f97bc28800f2cc5c948b` |
| `#16` | Canonical Apache-2.0 license | `86d3ff9e0844d59731b29ddecffd6b47a5717850` | `32541711942` / `96952857828` | `4797a089471d9ae99126253574e50b2d7e108f79` |
| `#17` | Register API/MCP hardening | `b82412672baaefe17b448a8ad9268307a95cbf61` | `32542245785` / `96954355093` | `c62309ed52b3451610de6345a4213202a8e44d21` |
| `#18` | API identity and MCP 2026-07-28 hardening | `ac1e1c3d4a83c48e3f3c0cb4c0305f5e1ff920cf` | `32544002123` / `96959167075` | `f1bcff0317a8e65003326544d844c120a61fb00d` |

Each required check concluded `success`, each PR was squash-merged through the ruleset, and each source branch was deleted.

## Actions and security settings

Actions read-back confirms:

- default workflow token permission is `read`;
- Actions-created pull-request approval is disabled;
- allowed actions mode is `selected`;
- SHA pinning is required;
- GitHub-owned actions are allowed;
- the only additional patterns are the declared Docker and PyPA publishing actions.

The `github-pages` environment accepts protected branches. The `ghcr`, `github-release`, and `pypi` environments require the repository owner as reviewer and a protected branch. Publication workflows remain manually dispatched and were not run as release tests.

Security analysis had dependency vulnerability alerts, automated security fixes, secret scanning, and secret push protection disabled at read-back. They were enabled through the repository administration API. Post-change read-back returned:

- dependency vulnerability alerts: HTTP `204 No Content` (enabled);
- automated security fixes: `enabled: true`, `paused: false`;
- Dependabot security updates: `enabled`;
- secret scanning: `enabled`;
- secret scanning push protection: `enabled`;
- current Dependabot alert count: `0`;
- current secret-scanning alert count: `0`.

Non-provider-pattern secret scanning and validity checks remain disabled; no entitlement or need was assumed for those optional modes.

## License evidence

- `LICENSE` SHA-256: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`
- GitHub license read-back: `Apache License 2.0`, SPDX `Apache-2.0`
- GitHub license blob: `d645695673349e3947e8e5ae42332d0ac3164cd7`
- Built wheel metadata: `License-Expression: Apache-2.0` and `License-File: LICENSE`
- Wheel and source distribution both include `LICENSE`

This verifies project metadata consistency; it is not an authorship or third-party-content attestation.

## Default-hostname Pages deployment

The manually dispatched bootstrap deployment completed successfully:

- workflow: `publish-pages`
- run: `32544087626`, conclusion `success`
- build job: `96959412606`, conclusion `success`
- deploy job: `96959454771`, conclusion `success`
- GitHub deployment: `6031979177`
- successful deployment status: `17149009818`
- deployed commit: `f1bcff0317a8e65003326544d844c120a61fb00d`
- provider URL: <https://yoheinakajima.github.io/epistemedia/>
- deployment completed: `2026-08-22T01:40:29Z`

Pages API read-back reports workflow build mode, HTTPS enforced, public visibility, and `cname: null`. The bootstrap job proved that no `CNAME` file entered the artifact.

Published artifact identity:

- catalog: `em:catalog:sha256:73fc4af4524e03730cb37faa5f76e7b04805b48db7d0de669eeb4a7ab31ed5d8`
- frontier: `em:frontier:sha256:4f780876bc22add90a1c56418e6b7397dabc3fd1aa2a1ba6936c8581c6ce8172`
- release manifest: `em:release-manifest:sha256:7daed819d06c6c6a73aa6d8ca4771ab0d82726d45a9600cbb61e39ff0345d13b`
- compiler: `epistemedia/0.2.0`
- accepted source time: `2026-08-22T01:39:00Z`
- files: `470`

External HTTPS requests returned `200` with the expected content type for all required routes:

| Representation | Routes |
| --- | --- |
| HTML | `/`, `/docs/`, `/topics/epistemedia/`, `/topics/epistemedia/evidence-first/`, representative double-encoded object route |
| Markdown | `/index.md`, `/docs/index.md`, `/topics/epistemedia/index.md`, `/topics/epistemedia/evidence-first/index.md`, representative object twin |
| Agent text | `/llms.txt`, `/llms-full.txt`, `/docs/llms.txt` |
| JSON | `/.well-known/epistemedia.json`, representative object twin |
| Discovery | `/robots.txt`, `/sitemap.xml` |

The root and docs HTML declare canonical URLs at the default GitHub hostname. At an explicit `390 × 844` viewport, the document and body widths were both `390`, no element overflowed, the navigation and hero rendered visibly, all 11 topic cards were present, and the accepted commit appeared in the page.

The public discovery document names the planned `api.epistemedia.org` and `mcp.epistemedia.org` destinations. Those hostnames have no A, AAAA, or CNAME record and have not passed HTTPS read-back. They are not live-service evidence; the repository README labels them planned production destinations.

## Domain and DNS boundary

Owner direction remains:

- `epistemedia.org` is the canonical human and future identifier domain;
- `api.epistemedia.org` and `mcp.epistemedia.org` are future service domains;
- `episte.media` is a path-preserving sharing redirect only.

Public DNS is still registrar parking state:

| Name | Observed records |
| --- | --- |
| `epistemedia.org` | NS `ns57.domaincontrol.com`, `ns58.domaincontrol.com`; A `15.197.148.33`, `3.33.130.190`; no AAAA |
| `www.epistemedia.org` | CNAME `epistemedia.org` |
| `episte.media` | NS `ns01.domaincontrol.com`, `ns02.domaincontrol.com`; A `15.197.148.33`, `3.33.130.190`; no AAAA |
| `www.episte.media` | CNAME `episte.media` |
| GitHub Pages verification TXT names | no record observed for either domain |
| `api.epistemedia.org`, `mcp.epistemedia.org` | no A, AAAA, or CNAME record |

No DNS record was changed. GitHub account-level domain verification must produce the exact TXT challenge before registrar edits. The repository Pages custom-domain field must remain unset until that TXT record is published and read back.

## `prepublic-ready` decision

The remote branch still points to commit `9cf66ef15fc842531619364529086d6061dc7aab`, tree `c3be9b724f3b15e6864c86974bd1e865eb10e007`. It is an ancestor of `main`. The promoted tree `03bc33f8dc1de76abc871bfd23cd2e2f853bc623` is preserved by ancestor commit `986e33a09658f1c0fdb0c67668681201ac0ff080`, which is also reachable from `main`. No active workflow references the branch.

The branch no longer serves a declared recovery purpose. This accepted record authorizes deletion of the exact remote ref `refs/heads/prepublic-ready` after this record merges. No tag is required because both commits remain in accepted `main` history and their immutable identities are recorded here and in the earlier baseline. Actual deletion and provider read-back must be appended after the deletion; they must not be backfilled into this record.

## Remaining limitations and owner boundaries

- Account-level verification for `epistemedia.org` has not yet created a TXT challenge.
- The Pages custom domain and DNS have not been changed.
- `episte.media` does not yet provide a path-preserving redirect.
- The public API and remote MCP runtime are locally hardened but not hosted; the Docker daemon was unavailable for a local image build.
- A custom repository social preview is not configured.
- GHCR, GitHub Releases, PyPI, and MCP Registry publication have not occurred.
- PyPI returned `404` for the `epistemedia` project name during readiness read-back; availability is not a reservation.
- Protected `epistemedia.com` identifier namespaces remain unchanged. EM-0009 requires the governance path, compatibility mapping, replay testing, and independent evaluation.
- No non-administrator credential was available for a direct-push rejection probe; active ruleset read-back is the evidence for that boundary.
