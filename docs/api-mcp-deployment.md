# Public API and MCP deployment contract

The API and MCP gateway is a read-only projection service. It receives an accepted repository snapshot and exposes no GitHub, contribution, deployment, package-publishing, signing, or arbitrary network-fetch authority.

Local conformance does not mean the production endpoints are live. A provider deployment becomes public state only after external HTTPS read-back records its URL, accepted commit, catalog, frontier, policies, compiler, content digest, limits, and smoke-test results.

## Application limits

The gateway enforces the following defaults. A deployment may lower them, but must not raise them without a recorded resource review.

| Environment variable | Default | Enforcement |
| --- | ---: | --- |
| `EPISTEMEDIA_MAX_BODY_BYTES` | `1048576` | Rejects an oversized declared or streamed request body with HTTP 413 |
| `EPISTEMEDIA_MAX_QUERY_BYTES` | `8192` | Rejects an oversized query string with HTTP 414 |
| `EPISTEMEDIA_MAX_RESPONSE_BYTES` | `8388608` | Fails closed before emitting a response larger than the configured bound |
| `EPISTEMEDIA_RATE_LIMIT_PER_MINUTE` | `120` | Sliding-window, per-client-address limit in the single gateway process |
| `EPISTEMEDIA_REQUEST_TIMEOUT_SECONDS` | `15` | Stops waiting for application dispatch and returns HTTP 504 |
| `EPISTEMEDIA_ALLOWED_ORIGINS` | canonical site, `www`, and local loopback origins | Comma-separated exact origins; untrusted MCP Origins receive HTTP 403 before body consumption |

The in-process rate limit is defense in depth, not a distributed quota. The deployment edge must enforce the same or a stricter anonymous limit across replicas and must pass a trustworthy client address. Provider request-body, concurrency, idle-timeout, and response-size settings must be no weaker than the application limits. Record their provider object IDs and observed response headers in the production receipt.

The container starts one unprivileged Uvicorn process with a concurrency limit of 100, backlog of 128, and a five-second keep-alive timeout. The reference Compose service also caps memory, CPU, and process count. Production may use stricter values after load testing.

## MCP 2026-07-28

`/mcp` implements the stateless 2026-07-28 Streamable HTTP binding:

- POST is the only message method; GET and DELETE return HTTP 405;
- every POST carries `Accept: application/json, text/event-stream`, JSON content type, `MCP-Protocol-Version`, and `Mcp-Method`;
- `tools/call` and `resources/read` also carry `Mcp-Name`;
- mirrored headers must match the JSON-RPC body and required `_meta` fields;
- invalid Origins are rejected before the body is read;
- version, header, method, parse, request, and parameter failures return structured JSON-RPC errors;
- every successful result carries commit, catalog, frontier, policies, compiler, and a deterministic result-content digest;
- the server is stateless and does not mint protocol sessions or accept HTTP cancellation notifications.

The local stdio adapter uses the same modern request metadata and read-only method implementation without HTTP headers.

## Deployment environment

The minimum runtime environment is:

```text
EPISTEMEDIA_ROOT=/app
EPISTEMEDIA_MAX_BODY_BYTES=1048576
EPISTEMEDIA_MAX_QUERY_BYTES=8192
EPISTEMEDIA_MAX_RESPONSE_BYTES=8388608
EPISTEMEDIA_RATE_LIMIT_PER_MINUTE=120
EPISTEMEDIA_REQUEST_TIMEOUT_SECONDS=15
EPISTEMEDIA_ALLOWED_ORIGINS=https://epistemedia.org,https://www.epistemedia.org
```

No secret is required for anonymous reads. Do not add repository tokens, publisher credentials, DNS credentials, or contribution authority to this service.

## Required external smoke checks

After deployment, run the routes in `ops/hosting/production-smoke.md` and additionally verify:

- provider limits with a bounded 413, 414, 429, and timeout probe;
- untrusted and malformed Origin rejection;
- header/body mismatch and unsupported-version error codes;
- identity parity across static status, API status, MCP discovery, resource reads, and tool calls;
- no response or log exposes provider internals, private paths, credentials, or private source content.
