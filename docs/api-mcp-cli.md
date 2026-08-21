# API, MCP, and CLI

All integrations read the same disclosure-safe public catalog. Preserve the returned `catalog_id`, `frontier`, `commit`, `compiler`, policy IDs, object IDs, and content digests when storing or citing results.

## REST API

The public read API is rooted at:

```text
https://api.epistemedia.com/v1
```

Representative reads:

```text
GET /v1/status
GET /v1/search?q=governance&limit=20
GET /v1/topics
GET /v1/topics/{slug}?lens=skeptical
GET /v1/objects/{id}
GET /v1/claims/{id}/trace
```

The OpenAPI contract is published at `/openapi.json`. Anonymous reads are intended to remain free within bounded abuse and resource limits. Downloadable snapshots allow clients to operate without the hosted service.

Public write APIs, when introduced, create proposals, contribution bundles, task claims, and receipts. They do not directly set truth, change accepted policy, or mutate a page.

## MCP

Remote endpoint:

```text
https://mcp.epistemedia.com/mcp
```

Server namespace:

```text
com.epistemedia/knowledge
```

Read-only tools include:

- `search_knowledge`
- `get_object`
- `get_topic`
- `trace_claim`
- `compare_lenses`
- `get_next_contribution`
- `validate_bundle`

Resources use URIs such as:

```text
epistemedia://status
epistemedia://topic/{slug}
epistemedia://object/{id}
```

The HTTP adapter enforces the supported MCP protocol version on non-discovery requests, checks browser Origins, returns protocol-level errors for unsupported versions or methods, and marks public lists as cacheable. The stdio adapter is available through the CLI for local clients.

A future authenticated contribution server will be a separate authority surface. Its tools create proposals and receipts but cannot admit their own output.

## CLI

Install an editable checkout:

```bash
python -m pip install -e '.[dev,server]'
```

Local realm operations:

```bash
epistemedia orient
epistemedia validate
epistemedia build
epistemedia audit
epistemedia search "disclosure noninterference"
epistemedia project governance --lens skeptical
epistemedia repo next
epistemedia mcp serve
```

Remote reads work without a local repository:

```bash
epistemedia search "federated knowledge" --remote
epistemedia get <OBJECT_ID> --remote
epistemedia project epistemic-mesh --lens evidence-first --remote
```

## Self-hosting

```bash
docker compose up --build
```

The reference stack exposes the static site on port 8000 and API/MCP gateway on port 8080. Production deployments should pin a tagged release or exact commit and expose the accepted catalog/frontier identity.
