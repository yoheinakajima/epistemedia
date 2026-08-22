# Canonical-domain Pages activation evidence — 2026-08-22

Observed between `2026-08-22T04:17:00Z` and `2026-08-22T04:36:50Z` unless a more specific timestamp is listed. GitHub facts came from authenticated API and settings read-back, DNS facts from the GoDaddy record table plus authoritative and public recursive queries, and route facts from external HTTPS requests. Configuration alone is not treated as live-service evidence.

This record advances EM-0008 and proves the canonical static human-site milestone. It does not complete the `episte.media` redirect, hosted API or MCP runtime, container or package publication, or protected identifier-namespace migration.

## Accepted source and deployment

- Repository: `yoheinakajima/epistemedia`
- Accepted branch and commit: `main` at `fd601133040a8366ce19137f123eb9fd5d173de6`
- Workflow: `publish-pages`, manually dispatched with `deployment_mode=custom-domain`
- Workflow run: `32551930809`, conclusion `success`
- Build job: `96979984213`, conclusion `success`
- Deploy job: `96980043045`, conclusion `success`
- GitHub deployment: `6033216508`
- Successful deployment status: `17152329470`
- Deployment completed: `2026-08-22T04:32:21Z`
- Provider URL: <https://epistemedia.org/>

The build job passed validation, deterministic public compilation, all tests, disclosure audit, custom-domain `CNAME` attachment, Pages configuration, and artifact upload. The deploy job completed through the protected `github-pages` environment. No candidate branch or deployment credential changed accepted repository history.

GitHub Pages API read-back reports:

- build type `workflow`;
- custom domain `epistemedia.org`;
- account protection state `verified`;
- `pending_domain_unverified_at: null`;
- HTTPS enforcement `true`;
- public URL `https://epistemedia.org/`.

The repository homepage changed from the proved bootstrap URL `https://yoheinakajima.github.io/epistemedia/` to `https://epistemedia.org/` only after the custom-domain deployment passed provider read-back.

## Account verification and DNS

GitHub generated the account-level Pages ownership challenge for `epistemedia.org`. The exact TXT record was published at GoDaddy, read back from both authoritative nameservers, and accepted by GitHub. The personal-account Pages settings then displayed `epistemedia.org — Verified`. The TXT record remains in DNS as GitHub requires for continued ownership protection.

The authoritative DNS set is:

| Type | Name | Value | GoDaddy TTL |
| --- | --- | --- | --- |
| `A` | `@` | `185.199.108.153` | 600 seconds |
| `A` | `@` | `185.199.109.153` | 600 seconds |
| `A` | `@` | `185.199.110.153` | 600 seconds |
| `A` | `@` | `185.199.111.153` | 600 seconds |
| `AAAA` | `@` | `2606:50c0:8000::153` | 600 seconds |
| `AAAA` | `@` | `2606:50c0:8001::153` | 600 seconds |
| `AAAA` | `@` | `2606:50c0:8002::153` | 600 seconds |
| `AAAA` | `@` | `2606:50c0:8003::153` | 600 seconds |
| `CNAME` | `www` | `yoheinakajima.github.io.` | 1 hour |
| `TXT` | `_github-pages-challenge-yoheinakajima` | `9829aa0105a1256ed664d2f75e7f51` | 1 hour |

Nameservers remain `ns57.domaincontrol.com` and `ns58.domaincontrol.com`. The SOA, `_domainconnect` CNAME, and existing `_dmarc` TXT record were preserved. The registrar parking A record and apex-directed `www` CNAME were the only existing routing records replaced.

Direct queries to both authoritative nameservers returned the four GitHub Pages IPv4 values, four IPv6 values, verification TXT value, and `www` CNAME above. Public recursive read-back from Cloudflare `1.1.1.1` and Google `8.8.8.8` returned the same set during the observation window. GitHub's repository settings subsequently reported `DNS check successful`.

## HTTPS, canonical URLs, and redirects

GitHub issued a certificate for `epistemedia.org`, enabled the HTTPS control, and accepted HTTPS enforcement. Pages API read-back independently reports `https_enforced: true` and `html_url: https://epistemedia.org/`.

External requests against GitHub Pages edges observed:

- `https://epistemedia.org/` returned HTTPS `200` from `GitHub.com`;
- `https://www.epistemedia.org/` returned one `301` with `Location: https://epistemedia.org/`;
- `/.well-known/epistemedia.json` returned `application/json` and names `https://epistemedia.org` as the human surface;
- root HTML declares `<link rel="canonical" href="https://epistemedia.org/">`;
- sitemap entries use the `https://epistemedia.org/` origin and do not retain the bootstrap GitHub project path.

Immediate client caches can retain pre-change answers until their TTLs expire. Provider, authoritative, two public-recursive, GitHub DNS-check, TLS, and HTTP read-back all passed; this is not a claim that every resolver worldwide had converged during the observation window.

## Published artifact identity

- Release manifest: `em:release-manifest:sha256:777d29c14de765b283c04e56cb9e2d5b7f349179060df6126ab3f3a9cfb3d45b`
- Catalog: `em:catalog:sha256:e67bd0b52f36e501b7f7805a11710f9e9e6a3992619072f2f7dc91e84bd85856`
- Frontier: `em:frontier:sha256:df7de8a263225a86ab1bf66f21e2e55dd56368aa6440e49849f02b1d5ecd126f`
- Commit: `fd601133040a8366ce19137f123eb9fd5d173de6`
- Compiler: `epistemedia/0.2.0`
- Deterministic generated time: `2026-08-22T03:54:27Z`
- Files: `479`
- Base URL: `https://epistemedia.org`
- Planned API URL: `https://api.epistemedia.org/v1`
- Planned MCP URL: `https://mcp.epistemedia.org/mcp`

The catalog and frontier match the accepted source and the previously proved bootstrap projection. The release-manifest identity differs because deployment-specific canonical URLs changed to the accepted production origin; knowledge identity did not change.

The discovery document still references protected schema identifiers under `epistemedia.com`. That is expected historical and protocol state, not a domain-activation defect. EM-0009 exclusively governs any identifier-namespace migration.

## Canonical route read-back

All required routes returned HTTPS `200` with the expected content type after the custom-domain deployment:

| Representation | Routes |
| --- | --- |
| HTML | `/`, `/docs/`, `/topics/epistemedia/`, `/topics/epistemedia/evidence-first/`, representative double-encoded object route |
| Markdown | `/index.md`, `/docs/index.md`, `/topics/epistemedia/index.md`, `/topics/epistemedia/evidence-first/index.md`, representative object twin |
| Agent text | `/llms.txt`, `/llms-full.txt`, `/docs/llms.txt` |
| JSON | `/.well-known/epistemedia.json`, representative object twin |
| Discovery | `/robots.txt`, `/sitemap.xml` |

The representative object was `em:automation:sha256:3a90a6127614f1a6487a4ae37ab09608f1b6486e9b32716f9be2c7ed831b9e44`; its HTML, Markdown, and JSON routes each resolved through the required double-encoded static path.

## Remaining limitations and boundaries

- `episte.media` and `www.episte.media` still serve registrar bootstrap state; no path-preserving redirect is live.
- `api.epistemedia.org` and `mcp.epistemedia.org` have no production runtime or provider read-back. Their URLs in static discovery are planned destinations, not live-service evidence.
- Human, API, and MCP cross-interface production parity cannot be claimed until the hosted gateway passes the production smoke contract.
- Protected identifiers under `epistemedia.com` remain unchanged. EM-0009 requires governance, compatibility mapping, replay testing, and independent evaluation.
- No container, GitHub Release, GHCR, PyPI, or MCP Registry publication occurred in this activation.

