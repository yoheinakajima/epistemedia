# Production Smoke Contract

Run only after a deployment claims to be live. Record exact responses and hashes in an immutable run receipt.

## Human and static

- `https://epistemedia.org/` returns HTTPS 200 and the expected canonical URL.
- `/llms.txt`, `/docs/llms.txt`, `/index.md`, `/openapi.json`, `/.well-known/epistemedia.json`, `/manifest.json`, and `/status.json` resolve.
- `www` redirects once to the accepted apex.
- `https://episte.media/<representative-path>` redirects once, preserves the path and query, and lands on `https://epistemedia.org/<representative-path>` without serving duplicate content.
- HTML pages link to deterministic Markdown twins and the governing `llms.txt`.

## Identity

Compare human status/discovery, API `/v1/status`, MCP `server/discover`, and a local build from the accepted commit. They must expose the same catalog, frontier, commit, policy pack, and compiler. Deployment-specific URLs may differ; canonical knowledge identity may not.

## API

- anonymous status, search, topics, topic lens, object, and trace reads succeed;
- unknown objects and lenses return structured errors;
- declared cache and resource limits are present;
- responses do not expose private paths, credentials, hidden source content, or provider internals.

## MCP

- `server/discover` succeeds without prior session state;
- supported protocol requests succeed and unsupported versions return the protocol-specific error;
- tools/list, resources/list, resources/read, and read-only tool calls are cacheable and carry catalog/frontier metadata;
- untrusted browser Origins are rejected;
- no tool grants mutation, integration, package, deployment, or secret access.

## Reproducibility

- download the accepted source or public-catalog bundle;
- verify release checksums;
- rebuild in a clean environment;
- compare catalog, frontier, object digests, and relevant projection manifests;
- record any expected representation differences and their causes.
