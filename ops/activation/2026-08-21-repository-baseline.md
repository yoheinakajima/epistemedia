# Repository activation evidence — 2026-08-21

Observed at `2026-08-21T23:16:34Z` unless a more specific timestamp is listed. GitHub facts below came from authenticated API read-back; DNS facts came from public recursive resolution. A committed workflow or configuration file is not treated as evidence that a service is live.

## Accepted repository state

- Repository: `yoheinakajima/epistemedia`
- Visibility: public
- Default branch: `main`
- Accepted commit: `15a7f163ebfd387964e8a99cb4b94748cadd4aac`
- Post-merge Validate run: `32535980251`, conclusion `success`
- Merge policy: squash enabled; merge commits and rebase merging disabled; auto-merge and merged-branch deletion enabled
- Actions default token permission: read
- Actions-created pull-request approvals: disabled
- Private vulnerability reporting: enabled

Repository metadata was changed through the administration API after read-back. Before the change, description and topics were empty, Discussions was off, and Projects and Wiki were on. After the change:

- description: `Knowledge that can show its work: an open, federated knowledge system for humans and agents.`
- topics: `ai-agents`, `collective-intelligence`, `deep-research`, `epistemology`, `event-sourcing`, `knowledge-graph`, `local-first`, `mcp`, `open-knowledge`, `provenance`
- Issues and Discussions: enabled
- Projects and Wiki: disabled
- homepage: deliberately unset until a Pages deployment passes external read-back
- social preview: not yet configured

## Protected contribution path

Ruleset `main-protection` (`21168452`) is active and targets `~DEFAULT_BRANCH`. API read-back confirms:

- pull request required with zero bootstrap approvals;
- all review conversations must be resolved;
- squash is the only allowed merge method;
- required check `check` with strict up-to-date enforcement;
- linear history required;
- deletion and non-fast-forward updates blocked;
- repository-administrator role is the only always-bypass actor class.

The governed path was exercised without administrator bypass:

| Pull request | Scope | Required run | Merge commit | Result |
| --- | --- | --- | --- | --- |
| `#3` | Document the Validate contribution gate | required `check` passed | `d01f5cd2e6226062801fc39f1fabd74c9ea70278` | squash-merged; branch deleted; main run `32531352887` passed |
| `#5` | Register the owned `episte.media` correction | `32534537700` passed | `2b784a3eb5b0edcb72a05263750ca8d033cba694` | squash-merged; branch deleted; main run `32534588461` passed |
| `#6` | Select canonical and sharing domains | `32535929185` passed | `15a7f163ebfd387964e8a99cb4b94748cadd4aac` | squash-merged; branch deleted; main run `32535980251` passed |

The ruleset configuration is direct evidence that a non-bypass actor cannot update `main` without a current pull request and successful `check`. A separate non-administrator direct-push probe has not been performed because no such authenticated actor is available in this environment.

## Domain decision and DNS read-back

Owner direction selects:

- `epistemedia.org` as the canonical human and identifier domain;
- `api.epistemedia.org` and `mcp.epistemedia.org` as service domains;
- `episte.media` as a path-preserving sharing redirect only.

Current DNS is registrar bootstrap state, not project activation:

| Name | Observed state |
| --- | --- |
| `epistemedia.org` | NS `ns57.domaincontrol.com`, `ns58.domaincontrol.com`; A `15.197.148.33`, `3.33.130.190`; no AAAA |
| `www.epistemedia.org` | CNAME to `epistemedia.org` |
| `episte.media` | NS `ns01.domaincontrol.com`, `ns02.domaincontrol.com`; no apex A or AAAA |
| `www.episte.media` | CNAME to `episte.media` |
| GitHub Pages verification TXT names | no records observed for either domain |

No DNS record has been changed by this activation work. The `.org` A records are registrar parking addresses and must not be described as the Epistemedia site.

## Known pre-deployment gaps

- GitHub Pages API returns `404 Not Found`; Pages is not enabled and no Pages URL is live.
- GitHub detects `LICENSE` as `Other` / `NOASSERTION`; canonical Apache-2.0 text still needs a bounded correction.
- Repository Actions policy currently allows all actions and does not require SHA pinning. Workflow dependencies are being pinned in the EM-0008 implementation before narrowing the repository-level allowlist.
- `generated/public/` is ignored and disposable. CI proves two builds are byte-identical and rejects source-tree drift, but the local `make check` message still incorrectly implies the generated directory is committed. That contract needs a separate bounded correction.
- `prepublic-ready` still exists at commit `9cf66ef15fc842531619364529086d6061dc7aab`, tree `c3be9b724f3b15e6864c86974bd1e865eb10e007`, and is an ancestor of `main`. The immutable promoted tree `03bc33f8dc1de76abc871bfd23cd2e2f853bc623` remains reachable from commit `986e33a09658f1c0fdb0c67668681201ac0ff080`. The branch has not been deleted pending an accepted cleanup record.
- Protected identifiers still use the historical `epistemedia.com` namespace. EM-0009, independent evaluation, replay testing, and an explicit compatibility map are required before changing them.
- API/MCP hosting, GHCR, GitHub Releases, PyPI, and MCP Registry have not been activated.
