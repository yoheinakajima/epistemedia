# Production Domain Topology

The accepted deployment topology is:

| Domain | Service | Build authority |
| --- | --- | --- |
| `epistemedia.org` | Canonical static human site, docs, Markdown twins, discovery, release manifests | GitHub Pages workflow from accepted `main` |
| `www.epistemedia.org` | Redirect to canonical apex | DNS / edge configuration |
| `api.epistemedia.org` | Anonymous bounded public REST API | Container built from an accepted tag |
| `mcp.epistemedia.org` | Read-only Streamable HTTP MCP | The same gateway image and public catalog as the API |
| `episte.media` and `www.episte.media` | Path-preserving redirect to `https://epistemedia.org` | DNS / redirect service |

DNS records are external authority and are not canonical until a production run receipt records the actual provider configuration, observed TLS certificates, redirects, endpoint manifests, accepted commit, catalog ID, and frontier.

Current read-back: the v0.2.0 public-gateway receipt records verified CNAME, TLS, REST, and MCP
identity for `api.epistemedia.org` and `mcp.epistemedia.org`. The `episte.media` redirect remains
reserved and unverified. See
[`ops/activation/2026-09-01-v0.2.0-public-gateway.md`](../activation/2026-09-01-v0.2.0-public-gateway.md).

## Deployment invariants

- The custom domain does not participate in canonical catalog identity.
- Human, API, and MCP deployments expose the same catalog and frontier.
- The static site cannot mutate accepted knowledge.
- The API/MCP runtime has no GitHub integration, package publishing, signing, or contribution-admission credential.
- Anonymous reads are isolated from authenticated proposal surfaces.
- HTTPS is mandatory.
- Production smoke tests compare catalog, frontier, object digests, topic projections, error behavior, and disclosure findings across domains.

Use `tasks/contracts/EM-0008.json` for the bounded activation task. Do not invent DNS completion or service availability; record it only after direct verification.
