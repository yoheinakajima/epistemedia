# Production Domain Topology

The accepted deployment topology is:

| Domain | Service | Build authority |
| --- | --- | --- |
| `epistemedia.com` | Static human site, docs, Markdown twins, discovery, release manifests | GitHub Pages workflow from accepted `main` |
| `www.epistemedia.com` | Redirect to apex | DNS / edge configuration |
| `api.epistemedia.com` | Anonymous bounded public REST API | Container built from an accepted tag |
| `mcp.epistemedia.com` | Read-only Streamable HTTP MCP | The same gateway image and public catalog as the API |

DNS records are external authority and are not canonical until a production run receipt records the actual provider configuration, observed TLS certificates, redirects, endpoint manifests, accepted commit, catalog ID, and frontier.

## Deployment invariants

- The custom domain does not participate in canonical catalog identity.
- Human, API, and MCP deployments expose the same catalog and frontier.
- The static site cannot mutate accepted knowledge.
- The API/MCP runtime has no GitHub integration, package publishing, signing, or contribution-admission credential.
- Anonymous reads are isolated from authenticated proposal surfaces.
- HTTPS is mandatory.
- Production smoke tests compare catalog, frontier, object digests, topic projections, error behavior, and disclosure findings across domains.

Use `tasks/contracts/EM-0003.json` for the bounded activation task. Do not invent DNS completion or service availability; record it only after direct verification.
