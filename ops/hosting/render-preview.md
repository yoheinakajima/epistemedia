# Render preview handoff for the read-only gateway

This is a no-spend preview path for the already implemented REST and MCP gateway. It is not a
production-availability claim. Render's free web services spin down after 15 minutes without
traffic and can take about one minute to wake, so a free deployment is useful for protocol testing
but not for an always-on agent dependency.

Use one web service for both `api.epistemedia.org` and `mcp.epistemedia.org`. The service exposes
REST below `/v1` and Streamable HTTP MCP at `/mcp`; neither hostname grants write, arbitrary-fetch,
repository, deployment, or admission authority.

## Inputs that must be exact

- image: the public GHCR image built by the protected release workflow from the accepted tag;
- image digest: the immutable `sha256:` digest returned by the registry, not only a mutable tag;
- accepted commit: the exact 40-character commit embedded by the container build;
- port: `8080` (`PORT=8080` on Render);
- health check: `/healthz`;
- plan: Free for the bounded protocol preview, with no paid upgrade implied;
- custom domains: `api.epistemedia.org` and `mcp.epistemedia.org` on the same service.

The application environment remains the public, secret-free set in
[`docs/api-mcp-deployment.md`](../../docs/api-mcp-deployment.md). Do not add GitHub, DNS,
contribution, or publisher credentials to the service.

## Owner-controlled activation

1. Publish one accepted, tag-bound GHCR image through the protected container workflow.
2. Make only that package publicly readable and record the package URL, tag, and immutable digest.
3. In an owner-controlled Render workspace, create a web service from the exact image digest, use
   the Free plan, set `PORT=8080`, and add `/healthz` as the health-check path.
4. Add both custom domains to that service. Copy the exact Render DNS targets into the
   owner-controlled DNS account; do not infer them from examples.
5. Wait for Render to issue certificates and report both domains verified.
6. Run [`production-smoke.md`](production-smoke.md) externally. Record REST and MCP identity parity,
   Origin and limit behavior, TLS, response hashes, provider object IDs, image digest, and observed
   cold-start behavior before changing any public availability label.

The activation must stop if the package is not public, the image digest differs, Render requests a
paid plan, the DNS target is ambiguous, or any endpoint reports an identity different from the
accepted static release.

## Provider references

- [Render web services](https://render.com/docs/web-services)
- [Render custom domains and TLS](https://render.com/docs/custom-domains)
- [Render free service limitations](https://render.com/docs/free)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
