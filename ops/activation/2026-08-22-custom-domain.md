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

## Forensic-editorial design refresh — 2026-08-22T06:49Z

PR [#29](https://github.com/yoheinakajima/epistemedia/pull/29) was squash-merged through the protected contribution path as `081419ff0e4d28005320dc1ae7ad068b98135959`. Its pull-request validation run `32557756112` passed job `96994543150`; the resulting `main` validation run `32557840163` also concluded `success`. The source branch was deleted after merge.

Before merge, local browser inspection covered the homepage, explore index, topic, experimental lens, long-identifier object, documentation, and status page at `1440 × 900` and `390 × 844`. Every representative page had exactly one `h1`, no horizontal overflow, and a visible projection receipt. The desktop homepage placed four topic cards in the first viewport. The mobile header remained 58 pixels tall with 44-pixel navigation targets after a 17-pixel target defect found during inspection was corrected. Keyboard focus was visibly outlined, native `details` disclosure worked without JavaScript, status remained text-labelled, and the console had no warnings or errors.

The accepted commit was then deployed with `deployment_mode=custom-domain`:

- workflow run: `32557945809`, conclusion `success`;
- build job: `96995011325`, conclusion `success`;
- deploy job: `96995050209`, conclusion `success`;
- GitHub deployment: `6034179354`;
- successful deployment status: `17154918915`;
- completed: `2026-08-22T06:49:44Z`;
- provider URL: <https://epistemedia.org/>.

The build job passed validation, deterministic compilation, 63 tests, disclosure audit, custom-domain `CNAME` attachment, Pages configuration, and artifact upload. GitHub Pages API read-back continued to report build type `workflow`, custom domain `epistemedia.org`, HTTPS enforcement `true`, and public URL `https://epistemedia.org/`.

External HTTPS read-back after deployment observed the new paper, ink, forest, amber, `E/` publication shell and returned:

- `200 text/html` for `/`, `/docs/`, and `/status/`;
- `200 text/plain` for `/llms.txt`;
- `200 application/json` content for `/.well-known/epistemedia.json`;
- accepted commit `081419ff0e4d28005320dc1ae7ad068b98135959` in both the homepage receipt and discovery document.

Published artifact identity:

- release manifest: `em:release-manifest:sha256:8beaf29d2b38a606473f1bc1a9f904474b4b93f1839ae4a21cd8735cf438372d`;
- catalog: `em:catalog:sha256:0878f30018f4a18609fc53525c437f184b39cad2fe5fc2f58866dbe843a4c22f`;
- frontier: `em:frontier:sha256:768657ee40816484a512ba7a4d41f4a81e914d61ee31f14ea21fe0264e5625ad`;
- compiler: `epistemedia/0.2.0`;
- deterministic generated time: `2026-08-22T06:46:36Z`;
- files: `509`.

This deployment changes presentation and improves truthful status disclosure; it does not admit an outward-facing research dossier. The homepage still labels the 78-object, 11-topic corpus as the self-describing bootstrap corpus. Hosted API, hosted MCP, and the `episte.media` sharing redirect remain unverified and are not represented as live.

## Case 001 launch-hardening completion — 2026-08-22T23:31Z

EM-0022 and EM-0023 completed the first three launch-hardening priorities without adding a second
case, changing the accepted research packet, or activating another service.

PR [#38](https://github.com/yoheinakajima/epistemedia/pull/38) admitted the entry,
review-trust, and agent/release-parity changes as protected squash commit
`c5b307f6960514be3d71fdbed5fe41aec5d9b00d`. PR validation run `32603681837` passed
job `97105546780`; resulting-main run `32603767010` passed job `97105744337`. The source branch
was deleted. The corresponding custom-domain Pages run `32603815272` passed build job
`97105856264` and deploy job `97105921292`.

PR [#39](https://github.com/yoheinakajima/epistemedia/pull/39) admitted the living-report,
complete-ledger, terminology, practical-reading, view-divergence, and share-card changes as
protected squash commit `74fe81c26e443d39deb664fde4d17bdab8804e58`. The exact independently
reviewed candidate was `620ee2066fbef514650e6d81e0c75b1d1247c9d7`, tree
`903c267f5496f9bd82f982cf857b80f7f9af4ec4`. PR validation run `32604979068`
passed job `97108628839`; resulting-main run `32605229574` passed job `97109211579`.
The source branch was deleted. No administrative bypass was used.

The final custom-domain deployment for this implementation used `deployment_mode=custom-domain`
on exact main commit `74fe81c26e443d39deb664fde4d17bdab8804e58`:

- workflow run: `32605273577`, conclusion `success`;
- build job: `97109314769`, conclusion `success`;
- deploy job: `97109370422`, conclusion `success`;
- provider URL: <https://epistemedia.org/>.

External HTTPS read-back observed the following published identity:

- release manifest:
  `em:release-manifest:sha256:161bc9b22e67b529bd5ed96df1947a2c52a4d42477894f07179cf477352e8f7b`;
- catalog:
  `em:catalog:sha256:d5fbacd2ade655304ce5023bf8ca10dea76cc5b1db34affa58f3a2e9c5382f6c`;
- frontier:
  `em:frontier:sha256:86eb58d2a7c585ceebaa0bf33ebee98482dd4766f90ba226383a93f1daa7e54d`;
- compiler: `epistemedia/0.2.0`;
- files: `569`.

The manifest ID recomputed from its declared catalog, frontier, commit, and ordered file/hash
inventory; its file count equaled the 568 inventoried files plus the manifest itself. All 20 URLs
listed in the sitemap returned HTTPS `200` and exposed the exact deployed commit and catalog.

Agent-facing read-back returned:

- `200 text/html` for `/how-we-know/` as `ClaudeBot`;
- `200 text/markdown` for the encyclopedia dossier Markdown twin as `GPTBot`;
- `200 application/json` for the skeptical dossier JSON twin as `ChatGPT-User`;
- `200 image/svg+xml` for the encyclopedia scoreboard card as `ClaudeBot`.

The published `llms.txt` names the featured dossier JSON, scoreboard card, disclosure-safe
independent-review receipt, and Substrate index. `/how-we-know/` states “One admitted case” and
“No second case yet.” The public review route identifies `codex-independent-reviewer`, exact
reviewed head `37161f25cbc76380cce72f57f370275f22f96a77`, 29 source receipts, and 86 span
records without exposing reviewer temporary paths.

Live browser read-back at `1440 × 900` and `390 × 844` observed one `h1`, zero scripts, no
horizontal overflow, 27 complete-ledger entries, five lexicon terms, and seven native disclosure
controls. Encyclopedia and skeptical expose different first-screen findings and practical readings
from the same dossier. Every skeptical tally uses a local fragment. The homepage exposes the exact
canonical link to `#unresolved-lineage`; direct navigation lands with “What remains unresolved”
visible at the narrow viewport.

The browser automation driver did not dispatch its synthetic Tab/Enter command during the final
live session, so this read-back does not claim an independently observed keystroke activation for
the new homepage sentence link. The accepted page retains a native anchor, visible focus styling,
no-script navigation, regression coverage for the exact target, and independent exact-head mobile
route verification. A later physical-keyboard read-back can close this bounded tooling gap; it is
not represented here as completed.

The accepted dossier remained SHA-256
`7003413e286e4d310f81441db33f4a467ba2eb3e08f41ddfa3cef5abb34707ca`
(214,499 bytes); its independent review receipt remained SHA-256
`503d16396b25b1c22d7fc10ac6fb7db2e530e6ce348d63fa8b639db5a5288f0a`
(65,611 bytes). Hosted API/MCP, `episte.media`, packages, containers, and Case 002 remain outside
this activation and are not claimed live.

## Human-readable topic and object projections — 2026-08-23T04:12Z

EM-0028 replaced the undifferentiated topic-page prose and metadata stream with compact grouped
object cards, subordinate technical identity, canonical object and Markdown links, exact accepted
source links, catalog-derived topic memberships, and exact repository-reference navigation. It did
not change accepted object text, Case 001 research, topic inclusion policy, or evidence meaning.

PR [#48](https://github.com/yoheinakajima/epistemedia/pull/48) passed independent exact-head
review and was squash-merged through the protected path:

- accepted base: `e9ad62b18f21594258643694c55709f78b4f9a50`;
- reviewed candidate: `444b4af56a901778afe6a79f96b6269b827d1c58`;
- reviewed and merged tree: `c3e416456d2f3541c6ada1ddbe938a32cf49ccca`;
- squash commit: `a4ccdb9e4fc2e62018c77f6a6560666f6a69f83f`;
- PR Validate run `32616552460`, job `97138142041`, conclusion `success`;
- resulting-main Validate run `32617161851`, job `97139622644`, conclusion `success`;
- source branch deleted; no ruleset bypass used.

The one authorized custom-domain deployment was dispatched on the exact accepted main commit:

- workflow run: `32617262450`, conclusion `success`;
- build job: `97139873721`, conclusion `success`;
- deploy job: `97139967276`, conclusion `success`;
- GitHub deployment: `6044260511`;
- successful deployment status: `17181336969`;
- completed: `2026-08-23T04:12:53Z`;
- provider URL: <https://epistemedia.org/>.

The build job passed validation, deterministic compilation, tests, disclosure audit, custom-domain
attachment, Pages configuration, and artifact upload. GitHub Pages API read-back continued to
report build type `workflow`, custom domain `epistemedia.org`, account protection state `verified`,
`pending_domain_unverified_at: null`, HTTPS enforcement `true`, and approved certificate coverage
for `epistemedia.org` and `www.epistemedia.org`.

External HTTPS read-back observed the following release identity:

- release manifest:
  `em:release-manifest:sha256:c69ca3eacc2718911a58f68a6d5cc4f2c00d6ffa144046cf9653c90efb6cfc69`;
- release-manifest response: 141,538 bytes, SHA-256
  `b0839a4d9cfe3aac07748792effdb86ae62cfd40c4fc0458159d964f8ba7d07d`;
- catalog:
  `em:catalog:sha256:dfb7ef6b75d7024142ff327622e44f8b0204471734bb1661b7054e21830c8233`;
- frontier:
  `em:frontier:sha256:c37a16901d41c94ef8c10dd3dc617facd51dd6f8d01dfcfd181044ae3b110fe0`;
- commit: `a4ccdb9e4fc2e62018c77f6a6560666f6a69f83f`;
- compiler: `epistemedia/0.2.0`;
- deterministic generated time: `2026-08-23T04:09:18Z`;
- files: `687`;
- base URL: `https://epistemedia.org`.

The canonical Epistemedia topic projection returned `27` objects grouped as `24` documentation,
`2` release, and `1` repository-artifact card. Its JSON twin exposed `220` exact other-topic
memberships and `15` unique exact public-object references, all labeled as navigation rather than
semantic similarity, support, or independence. Topic HTML, Markdown, and JSON returned `200` with
`text/html`, `text/markdown`, and `application/json`; representative object HTML and Markdown also
returned `200` with their intended content types. The representative accepted-source link resolved
to `docs/README.md` at the exact deployed commit.

Live browser read-back at `1280 × 720` and `390 × 844`, supplementing exact-head local inspection
at `1440 × 900` and `390 × 844`, observed one H1, zero scripts, no horizontal overflow, closed
technical disclosures by default, visibly smaller machine metadata, grouped cards, working source
and topic navigation, and a 3px visible focus outline. Click expansion of native `details` worked.
The browser driver focused `summary` but again did not dispatch its Enter default action, so this
receipt does not infer physical-keyboard activation from that synthetic driver. Native semantics,
focusability, click behavior, and regression tests passed.

Accepted Case 001 dossier, feature manifest, independent review receipt, source spans, and policy
meanings remained byte-identical. Hosted API/MCP, `episte.media`, DNS, release/package/container
publication, credentials, spend, and Case 002 admission were not changed or represented as live.

## Case 002 multi-case library — 2026-08-26T23:17Z

EM-0030 admitted the exact independently reviewed Case 002 dossier into a deterministic two-case
How We Know library while preserving Case 001's accepted manifest, dossier, receipt, routes, and
meaning.

PR [#53](https://github.com/yoheinakajima/epistemedia/pull/53) passed independent exact-head review
and was squash-merged through the active protected path:

- accepted base: `9c6a55c4f823b90f3aa4bb052f2f27ad844599e0`;
- reviewed author head: `47a27a20995ab918475001551007af878d47378b`;
- reviewed author tree: `2f5bf431931eaa1909f206a6bbde7371d959b04a`;
- independent review receipt head: `4e392c8068b787dda3398b03252018ea45e563eb`;
- receipt tree: `7f12a103e5d700534ea39bb39a5c668ce29f7069`;
- PR Validate run/job: `33021045222` / `98351203041`, conclusion `success`;
- squash commit: `af081caa99fc08d3fabb914ff68f2e672a83bd5b`;
- resulting-main Validate run/job: `33022534484` / `98356145870`, conclusion `success`;
- source branch deleted; no ruleset bypass used.

The one authorized custom-domain deployment ran on the exact accepted merge commit:

- workflow run: `33022684967`, conclusion `success`;
- build job: `98356603238`, conclusion `success`;
- deploy job: `98356990321`, conclusion `success`;
- GitHub deployment: `6113614670`;
- successful deployment status: `17384772347`;
- completed: `2026-08-26T23:17:55Z`;
- provider URL: <https://epistemedia.org/>.

Published artifact identity:

- release manifest:
  `em:release-manifest:sha256:783ca4cb1d0701240659181a963cdf0f6db5eab4b45d07c07241415fb20f5929`;
- catalog:
  `em:catalog:sha256:092898e1fe3d355761ab4cec653576926a8f5d31621ec7ce23dd60e9d19563ef`;
- frontier:
  `em:frontier:sha256:7e4a173112ef26422acf3ed9434c8b6849c4e011797e20fed6c0a9ca58a1e4c3`;
- compiler: `epistemedia/0.2.0`;
- generated time: `2026-08-26T23:14:34Z`;
- files: `861`;
- Case 002 dossier:
  `em:dossier:sha256:cbd7a14096a956f642f5c76046d3b49ed648fbe6bf24144c992404a01415af82`;
- encyclopedia content digest:
  `048c12622d9daca7cd009a7483c58697aa0674f77b12c6eca3721954ec1f3743`;
- skeptical content digest:
  `3e25148910d8bf697cec3ed8bc17eefdbb6638d68d4b3f4b75700c8b95c1cbd7`.

External HTTPS read-back returned `200` with the intended content type for the Case 002 default,
encyclopedia, skeptical, review, Markdown, JSON, and SVG routes; discovery, `llms.txt`, and the
sitemap all expose the two-case library. The homepage retains Case 001 as lead and exposes only a
compact truthful Case 002 cue. Canonical URLs use the production origin, and every checked
projection carries the exact deployed commit, catalog, frontier, compiler, dossier identity, and
view-specific content digest.

Live Chrome/CDP read-back at `1440 x 900` and `390 x 844` observed one H1, zero scripts, materially
different first-screen policy findings, native Tab and Enter disclosure activation, a 3 px solid
focus ring, and no horizontal overflow before or after expanding a source disclosure. Provider MIME
read-back returned `text/html`, `text/markdown`, `application/json`, and `image/svg+xml` for the
corresponding Case 002 representations.

This activation does not make the seven candidate warrants independent or estimate current agent
reliability. The live page retains 34 unresolved citation occurrences, 20 no-credit claims, four
pending warrant groups, three inaccessible carriers, and zero independently confirmed warrant
roots. Hosted API/MCP, `episte.media`, DNS, package/container/release publication, credentials,
accounts, spend, and Case 003 remain out of scope and unrepresented as live.
