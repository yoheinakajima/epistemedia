# Render free-compute preview handoff for the read-only gateway

This is a bounded free-compute preview path for the already implemented REST and MCP gateway. It is
not a production-availability or guaranteed no-spend claim. Render's current free web services have
a shared monthly allowance, spin down after 15 minutes without traffic, and can take about one
minute to wake. Bandwidth and build allowances are separately bounded; exhaustion may suspend the
service. A free deployment is useful for protocol testing but not for an always-on agent dependency.

Use one web service for both `api.epistemedia.org` and `mcp.epistemedia.org`. The service exposes
REST below `/v1` and Streamable HTTP MCP at `/mcp`; neither hostname grants write, arbitrary-fetch,
repository, deployment, or admission authority.

## Current deployment

The v0.2.0 gateway was activated on this bounded path and passed external read-back on 2026-09-01.
The exact service, deploy, image digest, custom domains, TLS state, identities, security probes, and
limitations are recorded in the
[v0.2.0 public-gateway activation receipt](../activation/2026-09-01-v0.2.0-public-gateway.md).
The free-compute and no-SLA caveats in this handoff remain current.

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

## Pre-creation spend and quota gate

Immediately before creating anything, read back the owner-controlled workspace and current Render
terms. Record:

- selected plan and the workspace's current billing/spend state;
- remaining free instance hours, bandwidth, and build-pipeline allowance;
- current custom-domain usage and the selected workspace's included-domain limit; and
- the projected effect of adding one service and two custom domains.

Current Render documentation describes 750 free instance hours per workspace per month. Custom
domain allowances vary by workspace plan; Hobby currently includes two across the workspace and
additional domains can require payment. Stop without creating the service if the live read-back
differs, either domain would exceed the included allowance, a payment method or paid upgrade is
required, or projected usage could create a charge. Quota suspension remains an acceptable preview
outcome; automatic paid overage does not.

## Owner-controlled activation

1. Publish one accepted, tag-bound GHCR image through the protected container workflow.
2. Make only that package publicly readable and record the package URL, tag, and immutable digest.
3. Only after the pre-creation gate passes, create a web service from the exact image digest, use
   the verified Free plan, set `PORT=8080`, and add `/healthz` as the health-check path.
4. Add both custom domains to that service. Copy the exact Render DNS targets into the
   owner-controlled DNS account; do not infer them from examples.
5. Wait for Render to issue certificates and report both domains verified.
6. Run [`production-smoke.md`](production-smoke.md) externally. Record REST and MCP identity parity,
   Origin and limit behavior, TLS, response hashes, provider object IDs, image digest, and observed
   cold-start behavior before changing any public availability label.

The activation must stop if the package is not public, the image digest differs, free quotas or
included domains are insufficient, Render requests a payment method or paid plan, the DNS target is
ambiguous, or any endpoint reports an identity different from the accepted static release.

## Provider references

- [Render web services](https://render.com/docs/web-services)
- [Render custom domains and TLS](https://render.com/docs/custom-domains)
- [Render free service limitations](https://render.com/docs/free)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
